# coding=UTF-8
from typing import Optional

from module.diagnostics import default_diagnostic
from module.language import _t
from module.transfer_store import TransferStatus
from module.util import make_forward_watch_rule, parse_forward_watch_rule


class LiveWatchManager:
    def __init__(
            self,
            listen_download_chat=None,
            listen_forward_chat=None,
            web_pending_watches=None,
            web_watch_handler_clients=None,
            transfer_store_getter=None,
            operation_submitter=None,
            user_getter=None,
            app_getter=None,
            diagnostic=None
    ):
        self.listen_download_chat = listen_download_chat if listen_download_chat is not None else {}
        self.listen_forward_chat = listen_forward_chat if listen_forward_chat is not None else {}
        self.web_pending_watches = web_pending_watches if web_pending_watches is not None else {}
        self.web_watch_handler_clients = web_watch_handler_clients if web_watch_handler_clients is not None else {}
        # chat_id → watch_id 反向映射，供 listen_download 过滤事件记录使用
        self._download_chat_watch_id: dict = {}
        self._transfer_store_getter = transfer_store_getter
        self._operation_submitter = operation_submitter
        self._user_getter = user_getter
        self._app_getter = app_getter
        self._diagnostic = diagnostic

    @property
    def diagnostic(self):
        return self._diagnostic or default_diagnostic

    @property
    def _transfer_store(self):
        if self._transfer_store_getter:
            return self._transfer_store_getter()
        return None

    @property
    def _user(self):
        if self._user_getter:
            return self._user_getter()
        return None

    @property
    def _app(self):
        if self._app_getter:
            return self._app_getter()
        return None

    @staticmethod
    def download_watch_id(source_link: str) -> str:
        return f'download:{source_link}'

    @staticmethod
    def forward_watch_id(rule: str) -> str:
        return f'forward:{rule}'

    @staticmethod
    def watch_payload_from_record(watch: dict) -> dict:
        payload = {
            'watch_type': watch.get('type'),
            'source_link': watch.get('source_link')
        }
        if watch.get('type') == 'forward':
            payload['target_link'] = watch.get('target_link')
            payload['include_comment'] = bool(watch.get('include_comment'))
            payload['resolve_deep_link'] = bool(watch.get('resolve_deep_link'))
        return payload

    def persisted_watches(self) -> list:
        store = self._transfer_store
        if not store:
            return []
        return store.list_live_transfer_watches()

    def persist_watch(self, watch: dict) -> dict:
        store = self._transfer_store
        if not store:
            return watch
        return store.upsert_live_transfer_watch(
            watch_id=watch.get('id'),
            watch_type=watch.get('type'),
            source_link=watch.get('source_link'),
            target_link=watch.get('target_link'),
            include_comment=bool(watch.get('include_comment')),
            resolve_deep_link=bool(watch.get('resolve_deep_link')),
            status=watch.get('status') or TransferStatus.PENDING,
            error_message=watch.get('error_message')
        )

    def set_live_watch_status(self, watch_id: str, status: str, error_message: str = None) -> None:
        if watch_id in self.web_pending_watches:
            self.web_pending_watches[watch_id]['status'] = status
            self.web_pending_watches[watch_id]['error_message'] = error_message
        store = self._transfer_store
        if store:
            store.update_live_transfer_watch_status(
                watch_id=watch_id,
                status=status,
                error_message=error_message
            )

    def list_watches(self, tz_offset_minutes: int | None = None) -> list:
        watches_by_id = {
            watch.get('id'): watch
            for watch in self.persisted_watches()
            if watch.get('id')
        }
        for link in sorted(self.listen_download_chat):
            watch_id = self.download_watch_id(link)
            watches_by_id[watch_id] = {
                **watches_by_id.get(watch_id, {}),
                'id': watch_id,
                'type': 'download',
                'source_link': link,
                'target_link': None,
                'include_comment': False,
                'resolve_deep_link': False,
                'status': TransferStatus.RUNNING
            }
        for rule in sorted(self.listen_forward_chat):
            parsed = parse_forward_watch_rule(rule)
            watch_id = self.forward_watch_id(rule)
            watches_by_id[watch_id] = {
                **watches_by_id.get(watch_id, {}),
                'id': watch_id,
                'type': 'forward',
                'source_link': parsed.get('source_link'),
                'target_link': parsed.get('target_link'),
                'include_comment': bool(parsed.get('include_comment')),
                'resolve_deep_link': bool(parsed.get('resolve_deep_link')),
                'status': TransferStatus.RUNNING
            }
        running_ids = set(watches_by_id)
        for watch_id, watch in sorted(self.web_pending_watches.items()):
            if watch_id not in running_ids:
                watches_by_id[watch_id] = watch
        store = self._transfer_store
        for watch_id in watches_by_id:
            count = 0
            today_count = 0
            deferred_count = 0
            if store and watches_by_id[watch_id].get('type') == 'forward':
                count = store.get_live_watch_event_count(watch_id)
                today_count = store.get_live_watch_event_count(
                    watch_id,
                    today_only=True,
                    tz_offset_minutes=tz_offset_minutes
                )
                deferred_count = len(store.list_deferred_discussion_captures(
                    watch_id=watch_id,
                    statuses=['pending', 'running'],
                    limit=500,
                ))
            watches_by_id[watch_id]['event_count'] = count
            watches_by_id[watch_id]['today_count'] = today_count
            watches_by_id[watch_id]['deferred_comment_count'] = deferred_count
        return sorted(watches_by_id.values(), key=lambda watch: str(watch.get('id') or ''))

    def pending_watch_sources(self, watch_type: str) -> set:
        return {
            watch.get('source_link')
            for watch in self.web_pending_watches.values()
            if watch.get('type') == watch_type and watch.get('source_link')
        }

    def persisted_watch_sources(self, watch_type: str) -> set:
        return {
            watch.get('source_link')
            for watch in self.persisted_watches()
            if watch.get('type') == watch_type and watch.get('source_link')
        }

    def has_download_watch_source(self, source_link: str) -> bool:
        return (
            source_link in self.listen_download_chat
            or source_link in self.pending_watch_sources('download')
            or source_link in self.persisted_watch_sources('download')
        )

    def has_forward_watch_source(self, source_link: str) -> bool:
        running_sources = {
            parse_forward_watch_rule(rule).get('source_link')
            for rule in self.listen_forward_chat
        }
        return (
            source_link in running_sources
            or source_link in self.pending_watch_sources('forward')
            or source_link in self.persisted_watch_sources('forward')
        )

    def mark_pending_watch(self, payload: dict, status: str, error_message: str = None) -> None:
        watch_type = payload.get('watch_type')
        if watch_type == 'download':
            watch_id = f'download:{payload.get("source_link")}'
        elif watch_type == 'forward':
            rule = make_forward_watch_rule(
                payload.get('source_link'),
                payload.get('target_link'),
                bool(payload.get('include_comment')),
                bool(payload.get('resolve_deep_link')),
            )
            watch_id = f'forward:{rule}'
        else:
            return
        self.set_live_watch_status(watch_id, status, error_message)

    def _create_live_watch_operation(self, watch_type: str, payload: dict) -> str:
        if self._operation_submitter:
            operation = self._operation_submitter('watch', {'watch_type': watch_type, **payload})
            return operation['id']
        return ''

    def create_watch(self, payload: dict) -> dict:
        watch_type = payload.get('type')
        if watch_type == 'download':
            created = []
            for link in payload.get('source_links') or []:
                if self.has_forward_watch_source(link):
                    raise ValueError('watch_source_conflict')
                if self.has_download_watch_source(link):
                    raise ValueError('watch_already_exists')
                watch = {
                    'id': f'download:{link}',
                    'type': 'download',
                    'source_link': link,
                    'target_link': None,
                    'include_comment': False,
                    'status': TransferStatus.PENDING
                }
                watch = self.persist_watch(watch)
                self.web_pending_watches[watch['id']] = watch
                self._create_live_watch_operation('download', {'source_link': link})
                created.append(watch)
            return {'watches': created}
        if watch_type == 'forward':
            source_link = payload.get('source_link')
            target_link = payload.get('target_link')
            include_comment = bool(payload.get('include_comment'))
            resolve_deep_link = bool(payload.get('resolve_deep_link'))
            if self.has_download_watch_source(source_link):
                raise ValueError('watch_source_conflict')
            rule = make_forward_watch_rule(
                source_link, target_link, include_comment, resolve_deep_link
            )
            same_target_exists = any(
                parse_forward_watch_rule(existing).get('source_link') == source_link and
                parse_forward_watch_rule(existing).get('target_link') == target_link
                for existing in self.listen_forward_chat
            )
            same_persisted_exists = any(
                watch.get('type') == 'forward' and
                watch.get('source_link') == source_link and
                watch.get('target_link') == target_link
                for watch in self.persisted_watches()
            )
            same_pending_exists = any(
                watch.get('type') == 'forward' and
                watch.get('source_link') == source_link and
                watch.get('target_link') == target_link
                for watch in self.web_pending_watches.values()
            )
            if same_target_exists or same_persisted_exists or same_pending_exists:
                raise ValueError('watch_already_exists')
            watch = {
                'id': f'forward:{rule}',
                'type': 'forward',
                'source_link': source_link,
                'target_link': target_link,
                'include_comment': include_comment,
                'resolve_deep_link': resolve_deep_link,
                'status': TransferStatus.PENDING
            }
            watch = self.persist_watch(watch)
            self.web_pending_watches[watch['id']] = watch
            self._create_live_watch_operation(
                'forward',
                {
                    'source_link': source_link,
                    'target_link': target_link,
                    'include_comment': include_comment,
                    'resolve_deep_link': resolve_deep_link,
                }
            )
            return {
                'watches': [watch]
            }
        raise ValueError('Unsupported watch type.')

    def delete_watch(self, watch_id: str) -> bool:
        watch_type, separator, value = watch_id.partition(':')
        if not separator:
            return False
        store = self._transfer_store
        if store:
            store.cancel_deferred_discussion_captures_for_watch(watch_id)
        if watch_type == 'download':
            handler = self.listen_download_chat.get(value)
            if not handler:
                pending_deleted = self.web_pending_watches.pop(watch_id, None) is not None
                store_deleted = store.delete_live_transfer_watch(watch_id) if store else False
                if store:
                    store.delete_live_watch_events(watch_id)
                return pending_deleted or store_deleted
            client = self.web_watch_handler_clients.pop(watch_id, None) or self._user or (self._app.client if self._app else None)
            if client:
                client.remove_handler(handler)
            self.listen_download_chat.pop(value, None)
            self.web_pending_watches.pop(watch_id, None)
            # 清理 chat_id → watch_id 反向映射
            stale_keys = [k for k, v in self._download_chat_watch_id.items() if v == watch_id]
            for k in stale_keys:
                self._download_chat_watch_id.pop(k, None)
            if store:
                store.delete_live_transfer_watch(watch_id)
                store.delete_live_watch_events(watch_id)
            self.diagnostic.info(f'已通过WebUI删除监听下载,频道链接:"{value}"。')
            return True
        if watch_type == 'forward':
            handler = self.listen_forward_chat.get(value)
            if not handler:
                pending_deleted = self.web_pending_watches.pop(watch_id, None) is not None
                store_deleted = store.delete_live_transfer_watch(watch_id) if store else False
                if store:
                    store.delete_live_watch_events(watch_id)
                return pending_deleted or store_deleted
            client = self.web_watch_handler_clients.pop(watch_id, None) or self._user or (self._app.client if self._app else None)
            if client:
                client.remove_handler(handler)
            self.listen_forward_chat.pop(value, None)
            self.web_pending_watches.pop(watch_id, None)
            if store:
                store.delete_live_transfer_watch(watch_id)
                store.delete_live_watch_events(watch_id)
            self.diagnostic.info(f'已通过WebUI删除监听转发,转发规则:"{value}"。')
            return True
        return False

    def update_watch(self, watch_id: str, payload: dict) -> dict:
        watch_type, separator, value = watch_id.partition(':')
        if not separator:
            raise ValueError('Invalid watch id.')
        if watch_type != 'forward':
            raise ValueError('Only forward watch can be updated.')
        parsed = parse_forward_watch_rule(value)
        old_source = parsed.get('source_link', '')
        new_source = str(payload.get('source_link') or '').strip()
        new_target = str(payload.get('target_link') or '').strip()
        new_include_comment = bool(payload.get('include_comment'))
        new_resolve_deep_link = bool(payload.get('resolve_deep_link'))
        if not new_source:
            new_source = old_source
        if not new_source:
            raise ValueError('Source link is required.')
        if not new_source.startswith('https://t.me/'):
            raise ValueError('Watch source must start with https://t.me/.')
        if not new_target:
            raise ValueError('Target link is required.')
        if not new_target.startswith('https://t.me/'):
            raise ValueError('Watch target must start with https://t.me/.')
        if new_source == new_target:
            raise ValueError('Source and target cannot be the same.')
        if new_source != old_source:
            if self.has_download_watch_source(new_source):
                raise ValueError('watch_source_conflict')
            if self.has_forward_watch_source(new_source):
                raise ValueError('watch_already_exists')
        self.delete_watch(watch_id)
        return self.create_watch({
            'type': 'forward',
            'source_link': new_source,
            'target_link': new_target,
            'include_comment': new_include_comment,
            'resolve_deep_link': new_resolve_deep_link,
        })

    def list_watch_events(
            self,
            watch_id: str,
            limit: int = 50,
            offset: int = 0,
            today_only: bool = False,
            tz_offset_minutes: int | None = None,
            status: str | None = None
    ) -> Optional[dict]:
        store = self._transfer_store
        if not store:
            return None
        normalized = (status or '').strip() or None
        events, total = store.list_live_watch_events(
            watch_id,
            limit=limit,
            offset=offset,
            today_only=today_only,
            tz_offset_minutes=tz_offset_minutes,
            status=normalized
        )
        return {
            'watch_id': watch_id,
            'events': events,
            'total': total,
            'limit': limit,
            'offset': offset,
            'today_only': today_only,
            'status': normalized,
            'status_counts': store.count_live_watch_events_by_status(
                watch_id,
                today_only=today_only,
                tz_offset_minutes=tz_offset_minutes
            ),
            'has_more': (offset + len(events)) < total
        }
