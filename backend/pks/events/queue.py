"""Durable job queue over the core SQLite database."""

from __future__ import annotations

import json
import sqlite3
from uuid import uuid4

from pks.core.store.db import utcnow
from pks.core.store.sqlite import SqliteStore
from pks.events.models import Job, JobStatus


def _row_to_job(row: sqlite3.Row) -> Job:
    return Job(
        id=row["id"],
        type=row["type"],
        payload=json.loads(row["payload"]),
        status=row["status"],
        attempts=row["attempts"],
        max_attempts=row["max_attempts"],
        error=row["error"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class JobQueue:
    def __init__(self, store: SqliteStore):
        self._conn = store.connection

    def enqueue(self, type: str, payload: dict | None = None, *, max_attempts: int = 3) -> Job:
        now = utcnow()
        job = Job(
            id=uuid4().hex,
            type=type,
            payload=payload or {},
            status=JobStatus.QUEUED,
            max_attempts=max_attempts,
            created_at=now,
            updated_at=now,
        )
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO jobs
                    (id, type, payload, status, attempts, max_attempts, error,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.type,
                    json.dumps(job.payload, sort_keys=True),
                    job.status,
                    job.attempts,
                    job.max_attempts,
                    job.error,
                    job.created_at,
                    job.updated_at,
                ),
            )
        return job

    def claim_next(self) -> Job | None:
        """Atomically claim the oldest queued job (marks it running, bumps attempts)."""
        while True:
            row = self._conn.execute(
                "SELECT id FROM jobs WHERE status = 'queued' ORDER BY created_at, id LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            with self._conn:
                cur = self._conn.execute(
                    """
                    UPDATE jobs
                    SET status = 'running', attempts = attempts + 1, updated_at = ?
                    WHERE id = ? AND status = 'queued'
                    """,
                    (utcnow(), row["id"]),
                )
            if cur.rowcount == 1:
                return self.get(row["id"])
            # Another worker claimed it between SELECT and UPDATE; try again.

    def mark_done(self, job_id: str) -> None:
        self._set_status(job_id, JobStatus.DONE, error=None)

    def mark_failed(self, job_id: str, error: str) -> None:
        self._set_status(job_id, JobStatus.FAILED, error=error)

    def requeue(self, job_id: str, error: str) -> None:
        """Put a failed attempt back in the queue (error retained for visibility)."""
        self._set_status(job_id, JobStatus.QUEUED, error=error)

    def _set_status(self, job_id: str, status: JobStatus, *, error: str | None) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE jobs SET status = ?, error = ?, updated_at = ? WHERE id = ?",
                (status, error, utcnow(), job_id),
            )

    def get(self, job_id: str) -> Job | None:
        row = self._conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return _row_to_job(row) if row else None

    def list(
        self,
        *,
        status: JobStatus | None = None,
        newest_first: bool = False,
        limit: int | None = None,
    ) -> list[Job]:
        order = "DESC" if newest_first else "ASC"
        sql = f"SELECT * FROM jobs ORDER BY created_at {order}, id"  # noqa: S608
        params: list[object] = []
        if status is not None:
            sql = (
                f"SELECT * FROM jobs WHERE status = ? ORDER BY created_at {order}, id"  # noqa: S608
            )
            params.append(status)
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        return [_row_to_job(row) for row in self._conn.execute(sql, params)]

    def counts(self) -> dict[str, int]:
        rows = self._conn.execute("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status")
        counts = {status.value: 0 for status in JobStatus}
        for row in rows:
            counts[row["status"]] = row["n"]
        return counts

    def list_for_resource(self, resource_id: str) -> list[Job]:
        rows = self._conn.execute(
            """
            SELECT * FROM jobs
            WHERE json_extract(payload, '$.resource_id') = ?
            ORDER BY created_at, id
            """,
            (resource_id,),
        )
        return [_row_to_job(row) for row in rows]
