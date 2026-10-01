# coding=UTF-8
"""监听转发遇到 Telegram file_reference 过期时的刷新重试。

线上报错: [400 FILE_REFERENCE_X_EXPIRED] ... (caused by "messages.SendMedia")
来自 forward() 里的 Message.copy()/copy_message(): 内存中的 file_reference 在长时间
运行的监听转发(FloodWait 等待/深链解析/延迟评论区)之后已过期, 官方要求重新获取消息
刷新引用。这里锁定"用同一账号刷新引用后重试、失败也要可见"这条恢复路径。
"""
import asyncio
import os
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from unit_tests.pyrogram_stub import install_pyrogram_stub

install_pyrogram_stub()
sys.argv = [sys.argv[0]]

from pyrogram.errors import (  # noqa: E402
    FileReferenceEmpty,
    FileReferenceExpired,
    FileReferenceInvalid,
    FilerefUpgradeNeeded,
    FloodWait,
)

from module.persistence.system_log import SystemLogTracer  # noqa: E402
from module.transfer.live_transfer import LiveTransferService  # noqa: E402

SOURCE_CHAT_ID = -1001444244654
SOURCE_MESSAGE_ID = 2564
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _import_downloader():
    from module.downloader import TelegramRestrictedMediaDownloader
    return TelegramRestrictedMediaDownloader


FILE_REFERENCE_ERRORS = (
    FileReferenceExpired,
    FileReferenceInvalid,
    FileReferenceEmpty,
    FilerefUpgradeNeeded,
)


def _held_message(copy, client=None):
    message = SimpleNamespace(
        id=SOURCE_MESSAGE_ID,
        empty=False,
        link='https://t.me/source/2564',
        video=SimpleNamespace(file_id='stale-file', file_size=10, file_name='a.mp4'),
        text=None,
        photo=None,
        document=None,
        audio=None,
        voice=None,
        animation=None,
        video_note=None,
        sticker=None,
        copy=copy,
        chat=SimpleNamespace(id=SOURCE_CHAT_ID, username='source'),
    )
    if client is not None:
        message._client = client
    return message


def _refreshed_message(copy, message_id=SOURCE_MESSAGE_ID, chat_id=SOURCE_CHAT_ID, client=None):
    message = SimpleNamespace(
        id=message_id,
        empty=False,
        copy=copy,
        chat=SimpleNamespace(id=chat_id),
    )
    if client is not None:
        message._client = client
    return message


class _ForwardHarness:
    """装配 forward() 依赖, 记录复制/重新拉取/flood 等待调用。"""

    def __init__(
            self,
            stale_error,
            refreshed_result=None,
            refreshed_error=None,
            refreshed_failures: int = 0,
            copy_message_result=None,
            get_messages_result=None,
            get_messages_errors=None,
    ):
        self.stale_error = stale_error
        self.held_copy_calls = []
        self.refreshed_copy_calls = []
        self.fetched = []
        self.logs = []
        self._refreshed_failures = refreshed_failures
        self._get_messages_errors = list(get_messages_errors or [])

        async def stale_copy(**kwargs):
            self.held_copy_calls.append(kwargs)
            raise self.stale_error

        async def fresh_copy(**kwargs):
            self.refreshed_copy_calls.append(kwargs)
            if refreshed_error is not None:
                raise refreshed_error
            if self._refreshed_failures > 0:
                self._refreshed_failures -= 1
                raise FileReferenceExpired()
            return refreshed_result

        self.held_message = _held_message(stale_copy)

        async def get_messages(chat_id=None, message_ids=None):
            self.fetched.append((chat_id, message_ids))
            if self._get_messages_errors:
                raise self._get_messages_errors.pop(0)
            if get_messages_result is not None:
                return get_messages_result
            return _refreshed_message(fresh_copy, message_id=message_ids, chat_id=chat_id)

        copy_message_kwargs = {'return_value': copy_message_result}
        if isinstance(copy_message_result, Exception):
            copy_message_kwargs = {'side_effect': copy_message_result}
        self.client = SimpleNamespace(
            name='test-client',
            get_messages=get_messages,
            copy_message=AsyncMock(**copy_message_kwargs),
            forward_messages=AsyncMock(
                side_effect=AssertionError('should not reach forward_messages')
            ),
        )

        downloader = object.__new__(_import_downloader())
        downloader.app = SimpleNamespace(client=self.client)
        downloader.transfer_store = None
        downloader._log_system_chain = lambda **kwargs: self.logs.append(kwargs)
        downloader.wait_for_telegram_flood = AsyncMock()
        self.downloader = downloader

    def run_forward(self):
        return asyncio.run(self.downloader.forward(
            client=self.client,
            message=self.held_message,
            message_id=SOURCE_MESSAGE_ID,
            origin_chat_id=SOURCE_CHAT_ID,
            target_chat_id='target-chat',
            target_link='https://t.me/target',
            done_notice=False,
            ignore_type_filter=True,
            archive_after_success=False,
        ))


class ForwardFileReferenceRefreshCase(unittest.TestCase):
    def test_forward_refreshes_expired_file_reference_and_retries(self):
        """FILE_REFERENCE_X_EXPIRED: 重新拉取源消息后重试复制, 而不是整条转发失败。"""
        harness = _ForwardHarness(
            stale_error=FileReferenceExpired(),
            refreshed_result=SimpleNamespace(id=9001),
        )

        result = harness.run_forward()

        self.assertEqual(9001, result.id)
        self.assertEqual(1, len(harness.held_copy_calls))
        self.assertEqual(1, len(harness.refreshed_copy_calls))
        self.assertEqual([(SOURCE_CHAT_ID, SOURCE_MESSAGE_ID)], harness.fetched)
        self.assertEqual(0, harness.client.copy_message.await_count)
        self.assertEqual('target-chat', harness.refreshed_copy_calls[0]['chat_id'])
        self.assertTrue(any(
            item.get('stage') == 'file_reference_refreshed' for item in harness.logs
        ), harness.logs)

    def test_forward_refreshes_on_every_file_reference_error_class(self):
        for error_cls in FILE_REFERENCE_ERRORS:
            with self.subTest(error=error_cls.__name__):
                harness = _ForwardHarness(
                    stale_error=error_cls(),
                    refreshed_result=SimpleNamespace(id=9002),
                )
                result = harness.run_forward()
                self.assertEqual(9002, result.id)
                self.assertEqual(1, len(harness.fetched))

    def test_forward_falls_back_to_copy_message_when_refresh_unavailable(self):
        """源消息已取不到(例如深链 bot 撤回)时, 退回 copy_message 按 id 重新拉取。"""
        harness = _ForwardHarness(
            stale_error=FileReferenceExpired(),
            copy_message_result=SimpleNamespace(id=4242),
            get_messages_result=SimpleNamespace(empty=True),
        )

        result = harness.run_forward()

        self.assertEqual(4242, result.id)
        self.assertEqual(1, len(harness.held_copy_calls))
        self.assertEqual(0, len(harness.refreshed_copy_calls))
        self.assertEqual(1, harness.client.copy_message.await_count)

    def test_forward_raises_original_error_when_id_copy_returns_empty(self):
        """按 id 重新拉取返回 MessageEmpty(None) 时保留原始 file_reference 错误。

        真 pyrogram 的 Message.copy 对空消息只 warning 后返回 None, 不抛异常;
        若在此返回 None, forward() 只会 log.error 一句, 既不记 watch 事件也不报错,
        等于静默丢帖。
        """
        harness = _ForwardHarness(
            stale_error=FileReferenceExpired(),
            copy_message_result=None,
            get_messages_result=SimpleNamespace(empty=True),
        )

        with self.assertRaises(FileReferenceExpired):
            harness.run_forward()

        self.assertEqual(1, len(harness.held_copy_calls))
        self.assertEqual(1, harness.client.copy_message.await_count)

    def test_forward_gives_up_after_refresh_retry_budget(self):
        """刷新重试有上限, 超过后仍然抛出原始错误(交给外层记录监听转发异常)。"""
        harness = _ForwardHarness(
            stale_error=FileReferenceExpired(),
            refreshed_error=FileReferenceExpired(),
        )

        with self.assertRaises(FileReferenceExpired):
            harness.run_forward()

        self.assertEqual(1, len(harness.held_copy_calls))
        self.assertEqual(2, len(harness.refreshed_copy_calls))
        self.assertEqual(2, len(harness.fetched))

    def test_forward_keeps_error_when_refresh_and_fallback_both_fail(self):
        """刷新失败且按 id 重新拉取也失败时, 保留原始错误而不是静默丢消息。"""
        harness = _ForwardHarness(
            stale_error=FileReferenceExpired(),
            copy_message_result=FileReferenceExpired(),
            get_messages_result=SimpleNamespace(empty=True),
        )

        with self.assertRaises(FileReferenceExpired):
            harness.run_forward()

        self.assertEqual(1, len(harness.held_copy_calls))
        self.assertEqual(1, harness.client.copy_message.await_count)
        self.assertEqual(0, len(harness.refreshed_copy_calls))

    def test_held_path_without_identity_keeps_original_error(self):
        """刷新出来的消息复制后仍无消息体时, 保留原始 file_reference 错误而非返回 None。"""
        harness = _ForwardHarness(
            stale_error=FileReferenceExpired(),
            refreshed_result=None,
        )

        with self.assertRaises(FileReferenceExpired):
            harness.run_forward()

        self.assertEqual(1, len(harness.held_copy_calls))
        self.assertEqual(1, len(harness.fetched))
        self.assertEqual(0, harness.client.copy_message.await_count)

    def test_refresh_flood_wait_does_not_consume_refresh_budget(self):
        """刷新阶段吃到 FloodWait 只等待重试, 不消耗 file_reference 刷新预算。"""
        harness = _ForwardHarness(
            stale_error=FileReferenceExpired(),
            refreshed_result=SimpleNamespace(id=9100),
            refreshed_failures=1,
            get_messages_errors=[FloodWait(30)],
        )

        result = harness.run_forward()

        self.assertEqual(9100, result.id)
        self.assertEqual(1, harness.downloader.wait_for_telegram_flood.await_count)
        # 3 次 get_messages = 1 次限流 + 2 次成功刷新; 若限流吃掉了预算, 第二次
        # file_reference 失败后就会直接抛错。
        self.assertEqual(3, len(harness.fetched))
        self.assertEqual(2, len(harness.refreshed_copy_calls))

    def test_long_flood_refreshes_held_message_before_next_send(self):
        """长 FloodWait(引用 TTL 量级)之后主动刷新, 不等下一次发送失败。"""
        result, events, fetched, logs = self._run_flood_case(FloodWait(3600))

        self.assertEqual(9900, result.id)
        self.assertEqual(['held', 'fresh'], events)
        self.assertEqual([(SOURCE_CHAT_ID, SOURCE_MESSAGE_ID)], fetched)
        preemptive = [
            item for item in logs
            if item.get('details', {}).get('preemptive') is True
        ]
        self.assertEqual(1, len(preemptive), logs)
        self.assertEqual(3600, preemptive[0]['details']['flood_seconds'])

    def test_only_floods_at_or_above_threshold_refresh_proactively(self):
        """阈值边界: <1800s 直接重发, >=1800s(含 FloodPremiumWait) 才主动刷新。"""
        from pyrogram.errors import FloodPremiumWait

        for error, expect_refresh in (
                (FloodWait(60), False),
                (FloodWait(1799), False),
                (FloodWait(1800), True),
                (FloodPremiumWait(3600), True),
        ):
            with self.subTest(error=type(error).__name__, value=int(error.value)):
                result, events, fetched, logs = self._run_flood_case(error)
                if expect_refresh:
                    self.assertEqual(9900, result.id)
                    self.assertEqual(['held', 'fresh'], events)
                    self.assertEqual(1, len(fetched))
                    self.assertTrue(any(
                        item.get('details', {}).get('preemptive') is True
                        for item in logs
                    ), logs)
                else:
                    self.assertEqual(9901, result.id)
                    self.assertEqual(['held', 'held'], events)
                    self.assertEqual([], fetched)
                    self.assertFalse(any(
                        item.get('details', {}).get('preemptive') is True
                        for item in logs
                    ), logs)

    @staticmethod
    def _run_flood_case(error):
        """首次发送抛 FloodWait, 之后: 未刷新则重发旧消息, 已刷新则复制新消息。"""
        events = []
        fetched = []
        logs = []

        async def held_copy(**kwargs):
            events.append('held')
            if events.count('held') == 1:
                raise error
            return SimpleNamespace(id=9901)

        async def fresh_copy(**kwargs):
            events.append('fresh')
            return SimpleNamespace(id=9900)

        async def get_messages(chat_id=None, message_ids=None):
            fetched.append((chat_id, message_ids))
            return _refreshed_message(fresh_copy, message_id=message_ids, chat_id=chat_id)

        client = SimpleNamespace(
            name='test-client',
            get_messages=get_messages,
            copy_message=AsyncMock(side_effect=AssertionError('should not re-fetch by id')),
            forward_messages=AsyncMock(side_effect=AssertionError('should not forward')),
        )
        downloader = object.__new__(_import_downloader())
        downloader.app = SimpleNamespace(client=client)
        downloader.transfer_store = None
        downloader._log_system_chain = lambda **kwargs: logs.append(kwargs)
        downloader.wait_for_telegram_flood = AsyncMock()

        result = asyncio.run(downloader.forward(
            client=client,
            message=_held_message(held_copy),
            message_id=SOURCE_MESSAGE_ID,
            origin_chat_id=SOURCE_CHAT_ID,
            target_chat_id='target-chat',
            target_link='https://t.me/target',
            done_notice=False,
            ignore_type_filter=True,
            archive_after_success=False,
        ))
        return result, events, fetched, logs

    def test_held_copy_and_refresh_use_the_same_client(self):
        """复制由 message._client 执行时, 刷新也必须用同一个账号。"""
        client_a_copy_message = AsyncMock(side_effect=AssertionError('A must not copy'))
        client_a = SimpleNamespace(
            name='client-a',
            copy_message=client_a_copy_message,
            forward_messages=AsyncMock(side_effect=AssertionError('should not forward')),
        )
        refreshed_calls = []

        async def fresh_copy(**kwargs):
            refreshed_calls.append(kwargs)
            return SimpleNamespace(id=7001)

        async def stale_copy(**kwargs):
            raise FileReferenceExpired()

        async def get_messages_b(chat_id=None, message_ids=None):
            return _refreshed_message(
                fresh_copy, message_id=message_ids, chat_id=chat_id, client=client_b,
            )

        client_b = SimpleNamespace(name='client-b', get_messages=get_messages_b)
        downloader = object.__new__(_import_downloader())
        downloader.app = SimpleNamespace(client=client_a)
        downloader.transfer_store = None
        downloader._log_system_chain = lambda **kwargs: None

        result = asyncio.run(downloader.forward(
            client=client_a,
            message=_held_message(stale_copy, client=client_b),
            message_id=SOURCE_MESSAGE_ID,
            origin_chat_id=SOURCE_CHAT_ID,
            target_chat_id='target-chat',
            target_link='https://t.me/target',
            done_notice=False,
            ignore_type_filter=True,
            archive_after_success=False,
        ))

        self.assertEqual(7001, result.id)
        self.assertEqual(1, len(refreshed_calls))
        self.assertEqual(0, client_a_copy_message.await_count)

    def test_id_copy_and_refresh_use_the_same_client(self):
        """走 client.copy_message 入口时, 刷新也用这个 client, 不切到 message._client。"""
        copy_calls = []

        async def copy_message(**kwargs):
            copy_calls.append(kwargs)
            if len(copy_calls) == 1:
                raise FileReferenceExpired()
            return SimpleNamespace(id=5500)

        fetched_by_a = []
        refreshed_calls = []

        async def fresh_copy(**kwargs):
            refreshed_calls.append(kwargs)
            return SimpleNamespace(id=5500)

        async def get_messages_a(chat_id=None, message_ids=None):
            fetched_by_a.append((chat_id, message_ids))
            return _refreshed_message(fresh_copy, message_id=message_ids, chat_id=chat_id)

        client_a = SimpleNamespace(
            name='client-a',
            get_messages=get_messages_a,
            copy_message=copy_message,
        )
        client_b = SimpleNamespace(
            name='client-b',
            get_messages=AsyncMock(side_effect=AssertionError('B must not refresh')),
        )
        service = LiveTransferService(host=SimpleNamespace(
            forwarded_message_has_identity=(
                lambda message: getattr(message, 'id', None) is not None
            ),
        ))

        result = asyncio.run(service.copy_source_message(
            client=client_a,
            message=_held_message(fresh_copy, client=client_b),
            origin_chat_id=SOURCE_CHAT_ID,
            message_id=SOURCE_MESSAGE_ID,
            target_chat_id='target-chat',
            prefer_held_message=False,
        ))

        self.assertEqual(5500, result.id)
        self.assertEqual([(SOURCE_CHAT_ID, SOURCE_MESSAGE_ID)], fetched_by_a)
        self.assertEqual(0, client_b.get_messages.await_count)
        # 第一次走 client.copy_message 失败, 重试改用同一账号刷新出来的消息复制。
        self.assertEqual(1, len(copy_calls))
        self.assertEqual(1, len(refreshed_calls))


class MediaGroupFileReferenceRefreshCase(unittest.TestCase):
    def test_media_group_copy_retries_after_file_reference_expiry(self):
        calls = []
        logs = []

        async def copy_media_group(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise FileReferenceExpired()
            return [SimpleNamespace(id=777)]

        host = SimpleNamespace(
            app=SimpleNamespace(client=SimpleNamespace(copy_media_group=copy_media_group)),
            _log_system_chain=lambda **kwargs: logs.append(kwargs),
        )
        service = LiveTransferService(host=host)

        result = asyncio.run(service.copy_media_group_with_file_reference_refresh(
            chat_id='target-chat',
            from_chat_id=SOURCE_CHAT_ID,
            message_id=SOURCE_MESSAGE_ID,
            event_context={'trace_id': 'trace-1', 'watch_id': 'watch-1'},
        ))

        self.assertEqual(777, result[0].id)
        self.assertEqual(2, len(calls))
        self.assertTrue(all(call['disable_notification'] for call in calls))
        events = [
            item for item in logs
            if item.get('stage') == 'file_reference_refreshed'
        ]
        self.assertEqual(1, len(events), logs)
        self.assertEqual('trace-1', events[0]['trace_id'])
        # 媒体组没有独立刷新步骤(靠 copy_media_group 重新拉取成员), 不得声称已显式刷新。
        self.assertNotIn('refreshed', events[0]['details'])

    def test_media_group_flood_wait_retries_after_wait(self):
        calls = []

        async def copy_media_group(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise FloodWait(30)
            return [SimpleNamespace(id=778)]

        host = SimpleNamespace(
            app=SimpleNamespace(client=SimpleNamespace(copy_media_group=copy_media_group)),
            _log_system_chain=lambda **kwargs: None,
            wait_for_telegram_flood=AsyncMock(),
        )
        service = LiveTransferService(host=host)

        result = asyncio.run(service.copy_media_group_with_file_reference_refresh(
            chat_id='target-chat',
            from_chat_id=SOURCE_CHAT_ID,
            message_id=SOURCE_MESSAGE_ID,
        ))

        self.assertEqual(778, result[0].id)
        self.assertEqual(2, len(calls))
        self.assertEqual(1, host.wait_for_telegram_flood.await_count)

    def test_media_group_copy_gives_up_after_retry_budget(self):
        calls = []

        async def copy_media_group(**kwargs):
            calls.append(kwargs)
            raise FileReferenceExpired()

        host = SimpleNamespace(
            app=SimpleNamespace(client=SimpleNamespace(copy_media_group=copy_media_group)),
            _log_system_chain=lambda **kwargs: None,
        )
        service = LiveTransferService(host=host)

        with self.assertRaises(FileReferenceExpired):
            asyncio.run(service.copy_media_group_with_file_reference_refresh(
                chat_id='target-chat',
                from_chat_id=SOURCE_CHAT_ID,
                message_id=SOURCE_MESSAGE_ID,
            ))
        self.assertEqual(3, len(calls))


class FileReferenceEventContextCase(unittest.TestCase):
    def test_event_context_cannot_override_fixed_log_kwargs(self):
        """用真实 SystemLogTracer 校验: 固定 kwargs 不被 event_context 覆盖、键名合法。"""
        rows = []
        tracer = SystemLogTracer(
            store=SimpleNamespace(add_system_log=lambda **kwargs: rows.append(kwargs))
        )
        service = LiveTransferService(host=SimpleNamespace(_log_system_chain=tracer.log))

        service._log_file_reference_refresh(
            error=FileReferenceExpired(),
            outcome='已重新获取源消息并重试',
            action='copy message',
            refresh_attempt=1,
            refreshed=True,
            event_context={
                'category': 'watch',
                'stage': 'error',
                'message': 'boom',
                'trace_id': 'trace-2',
                'source_chat_id': SOURCE_CHAT_ID,
                'source_message_id': SOURCE_MESSAGE_ID,
            },
        )

        self.assertEqual(1, len(rows))
        self.assertEqual('forward', rows[0]['category'])
        self.assertEqual('file_reference_refreshed', rows[0]['stage'])
        self.assertEqual('trace-2', rows[0]['trace_id'])
        self.assertEqual(str(SOURCE_CHAT_ID), rows[0]['source_chat_id'])
        self.assertEqual(SOURCE_MESSAGE_ID, rows[0]['source_message_id'])
        self.assertTrue(rows[0]['details']['refreshed'])


class RealPyrogramFileReferenceCase(unittest.TestCase):
    """真实 pyrogram(非 stub) 下锁定错误类名与捕获覆盖。

    stub 的 pyrogram.errors 是任意造类的 DummyModule, 拼错类名也能 import 成功,
    因此必须另起一个真环境进程验证: 类名真实存在、且服务端各类错误都落进捕获元组。
    """

    def test_real_pyrogram_errors_are_caught_by_the_guard_tuple(self):
        code = (
            "from pyrogram import raw\n"
            "from pyrogram.errors.rpc_error import RPCError\n"
            "from module.transfer.live_transfer import FILE_REFERENCE_EXPIRED_ERRORS as GUARD\n"
            "cases = (\n"
            "    ('FILE_REFERENCE_EXPIRED', 400),\n"
            "    ('FILE_REFERENCE_X_EXPIRED', 400),\n"
            "    ('FILE_REFERENCE_0_EXPIRED', 400),\n"
            "    ('FILE_REFERENCE_X_INVALID', 400),\n"
            "    ('FILE_REFERENCE_EMPTY', 400),\n"
            "    ('FILEREF_UPGRADE_NEEDED', 406),\n"
            ")\n"
            "missed = []\n"
            "for raw_message, code in cases:\n"
            "    try:\n"
            "        RPCError.raise_it(\n"
            "            raw.types.RpcError(error_code=code, error_message=raw_message),\n"
            "            raw.functions.messages.SendMedia,\n"
            "        )\n"
            "    except Exception as e:\n"
            "        if not isinstance(e, GUARD):\n"
            "            missed.append((raw_message, type(e).__name__))\n"
            "print('GUARD', [c.__name__ for c in GUARD])\n"
            "print('MISSED', missed)\n"
        )
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('MISSED []', result.stdout)
        self.assertIn('FilerefUpgradeNeeded', result.stdout)


if __name__ == '__main__':
    unittest.main()
