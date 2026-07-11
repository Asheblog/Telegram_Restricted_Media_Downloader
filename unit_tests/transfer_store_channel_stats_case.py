# coding=UTF-8
import datetime
import tempfile
import unittest

from module.persistence.transfer_store import TransferStatus, TransferStore


class TransferStoreChannelStatsCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = TransferStore(directory=self._tmpdir.name)
        self.task_id = self.store.create_task('https://t.me/source/1', 'https://t.me/pikpak_bot')

    def tearDown(self):
        self._tmpdir.cleanup()

    def _add(
            self,
            *,
            message_id: int,
            status: str,
            source_folder: str | None = None,
            source_chat_id: str | None = None,
            updated_at: str | None = None,
    ) -> int:
        item_id = self.store.add_item(
            task_id=self.task_id,
            source_message_id=message_id,
            source_link=f'https://t.me/source/{message_id}',
            target_link='https://t.me/pikpak_bot',
            source_chat_id=source_chat_id,
            source_folder=source_folder,
            status=status,
        )
        if updated_at is not None:
            with self.store.connect() as conn:
                conn.execute(
                    'UPDATE transfer_items SET updated_at = ? WHERE id = ?',
                    (updated_at, item_id),
                )
        return item_id

    def test_aggregate_channel_download_stats_groups_by_folder_and_status(self):
        self._add(message_id=1, status=TransferStatus.SUCCESS, source_folder='alpha')
        self._add(message_id=2, status=TransferStatus.SUCCESS, source_folder='alpha')
        self._add(message_id=3, status=TransferStatus.FAILURE, source_folder='alpha')
        self._add(message_id=4, status=TransferStatus.SKIPPED, source_folder='beta')
        self._add(
            message_id=5,
            status=TransferStatus.SUCCESS,
            source_folder=None,
            source_chat_id='-100123',
        )
        self._add(message_id=6, status=TransferStatus.PENDING, source_folder='alpha')
        self._add(message_id=7, status=TransferStatus.RUNNING, source_folder='alpha')

        rows = self.store.aggregate_channel_download_stats(days=7, tz_offset_minutes=0)

        by_channel = {row['channel']: row for row in rows}
        self.assertEqual({'alpha', 'beta', '-100123'}, set(by_channel))
        self.assertEqual(2, by_channel['alpha']['success'])
        self.assertEqual(1, by_channel['alpha']['failure'])
        self.assertEqual(0, by_channel['alpha']['skip'])
        self.assertEqual(3, by_channel['alpha']['total'])
        self.assertEqual(0, by_channel['beta']['success'])
        self.assertEqual(1, by_channel['beta']['skip'])
        self.assertEqual(1, by_channel['-100123']['success'])
        self.assertEqual(3, rows[0]['total'])

    def test_aggregate_channel_download_stats_respects_local_calendar_window(self):
        # tz_offset=0 → local == UTC. Today start UTC; window is 7 local calendar days.
        today_start, _ = TransferStore.local_today_utc_bounds(0)
        start_dt = datetime.datetime.fromisoformat(today_start).replace(tzinfo=datetime.UTC)
        inside = (start_dt - datetime.timedelta(days=6)).isoformat(timespec='seconds')
        outside = (start_dt - datetime.timedelta(days=7, seconds=1)).isoformat(timespec='seconds')

        self._add(
            message_id=1,
            status=TransferStatus.SUCCESS,
            source_folder='inside',
            updated_at=inside,
        )
        self._add(
            message_id=2,
            status=TransferStatus.SUCCESS,
            source_folder='outside',
            updated_at=outside,
        )

        rows = self.store.aggregate_channel_download_stats(days=7, tz_offset_minutes=0)

        self.assertEqual(['inside'], [row['channel'] for row in rows])


if __name__ == '__main__':
    unittest.main()
