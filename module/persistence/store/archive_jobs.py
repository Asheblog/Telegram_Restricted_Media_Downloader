# coding=UTF-8
import time
from typing import Optional

class ArchiveJobsMixin:
    def upsert_archive_author_job(self, job: dict) -> None:
        import json
        result = job.get('result')
        result_json = None
        if result is not None:
            result_json = json.dumps(result, ensure_ascii=False)
        with self.connect() as conn:
            conn.execute(
                '''
                INSERT INTO archive_author_jobs (
                    id, kind, channel_folder, status, phase,
                    current_count, total_count, percent, message, error,
                    result_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    kind = excluded.kind,
                    channel_folder = excluded.channel_folder,
                    status = excluded.status,
                    phase = excluded.phase,
                    current_count = excluded.current_count,
                    total_count = excluded.total_count,
                    percent = excluded.percent,
                    message = excluded.message,
                    error = excluded.error,
                    result_json = excluded.result_json,
                    updated_at = excluded.updated_at
                ''',
                (
                    job.get('id'),
                    job.get('kind'),
                    job.get('channel_folder'),
                    job.get('status'),
                    job.get('phase'),
                    int(job.get('current') or 0),
                    int(job.get('total') or 0),
                    int(job.get('percent') or 0),
                    job.get('message'),
                    job.get('error'),
                    result_json,
                    float(job.get('created_at') or time.time()),
                    float(job.get('updated_at') or time.time()),
                ),
            )

    def get_archive_author_job(self, job_id: str) -> Optional[dict]:
        import json
        with self.connect() as conn:
            row = conn.execute(
                'SELECT * FROM archive_author_jobs WHERE id = ?',
                (str(job_id),),
            ).fetchone()
        if not row:
            return None
        return self._archive_author_job_from_row(row, json)

    def list_archive_author_jobs(
            self,
            *,
            channel_folder: Optional[str] = None,
            status: Optional[str] = None,
            limit: int = 20,
    ) -> list[dict]:
        import json
        clauses = []
        params: list = []
        if channel_folder:
            clauses.append('channel_folder = ?')
            params.append(str(channel_folder))
        if status:
            clauses.append('status = ?')
            params.append(str(status))
        where = f'WHERE {" AND ".join(clauses)}' if clauses else ''
        params.append(max(int(limit or 20), 1))
        with self.connect() as conn:
            rows = conn.execute(
                f'''
                SELECT * FROM archive_author_jobs
                {where}
                ORDER BY updated_at DESC
                LIMIT ?
                ''',
                params,
            ).fetchall()
        return [self._archive_author_job_from_row(row, json) for row in rows]

    def mark_stale_archive_author_jobs(
            self,
            *,
            older_than_seconds: float = 0,
            message: str = '任务已中断（进程重启），请重新扫描。',
            kinds: Optional[tuple] = None,
    ) -> int:
        """Mark leftover running jobs as failure (e.g. after process restart).

        ``kinds`` limits which job kinds are marked stale. Reorganize jobs are
        typically excluded so they can resume from checkpoint after restart.
        """
        cutoff = time.time() - max(float(older_than_seconds or 0), 0)
        kind_list = None
        if kinds:
            kind_list = tuple(str(item) for item in kinds if str(item).strip())
        with self.connect() as conn:
            if kind_list:
                placeholders = ','.join('?' for _ in kind_list)
                cursor = conn.execute(
                    f'''
                    UPDATE archive_author_jobs
                    SET status = 'failure',
                        phase = 'error',
                        error = ?,
                        message = ?,
                        updated_at = ?
                    WHERE status = 'running'
                      AND updated_at <= ?
                      AND kind IN ({placeholders})
                    ''',
                    (message, message, time.time(), cutoff, *kind_list),
                )
            else:
                cursor = conn.execute(
                    '''
                    UPDATE archive_author_jobs
                    SET status = 'failure',
                        phase = 'error',
                        error = ?,
                        message = ?,
                        updated_at = ?
                    WHERE status = 'running'
                      AND updated_at <= ?
                    ''',
                    (message, message, time.time(), cutoff),
                )
            return int(cursor.rowcount or 0)

    @staticmethod
    def _archive_author_job_from_row(row, json_module) -> dict:
        result = None
        raw = row['result_json'] if 'result_json' in row.keys() else None
        if raw:
            try:
                result = json_module.loads(raw)
            except Exception:
                result = None
        return {
            'id': row['id'],
            'kind': row['kind'],
            'channel_folder': row['channel_folder'],
            'status': row['status'],
            'phase': row['phase'],
            'current': int(row['current_count'] or 0),
            'total': int(row['total_count'] or 0),
            'percent': int(row['percent'] or 0),
            'message': row['message'] or '',
            'error': row['error'],
            'result': result,
            'created_at': float(row['created_at'] or 0),
            'updated_at': float(row['updated_at'] or 0),
        }
