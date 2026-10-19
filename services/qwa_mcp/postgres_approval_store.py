"""Managed PostgreSQL approval repository.

The repository uses a DB-API connection factory so the control plane does not
depend on a specific pool implementation. Production should inject a pooled
psycopg connection factory backed by a secret-managed DATABASE_URL.
"""
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Any

from .durable_approval_store import ApprovalRecord, TERMINAL


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PostgresApprovalStore:
    """PostgreSQL implementation with transactional decision locking."""

    def __init__(self, connection_factory: Callable[[], Any] | None = None):
        self._factory = connection_factory or self._default_factory
        self._ensure_schema()

    @staticmethod
    def _default_factory():
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg is required for PostgresApprovalStore") from exc
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL is required")
        return psycopg.connect(url)

    def _connect(self):
        return self._factory()

    def _ensure_schema(self):
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS qwa_approvals (
                        request_id TEXT PRIMARY KEY,
                        actor TEXT NOT NULL,
                        tool TEXT NOT NULL,
                        request_hash TEXT NOT NULL UNIQUE,
                        status TEXT NOT NULL,
                        approver TEXT,
                        reason TEXT,
                        created_at TIMESTAMPTZ NOT NULL,
                        decided_at TIMESTAMPTZ
                    )
                """)

    def create(self, approval: ApprovalRecord) -> ApprovalRecord:
        created = approval.created_at or _now()
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO qwa_approvals
                    (request_id, actor, tool, request_hash, status, approver,
                     reason, created_at, decided_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (request_id) DO NOTHING
                """, (
                    approval.request_id, approval.actor, approval.tool,
                    approval.request_hash, approval.status, approval.approver,
                    approval.reason, created, approval.decided_at,
                ))
                cur.execute(
                    "SELECT * FROM qwa_approvals WHERE request_id = %s",
                    (approval.request_id,),
                )
                row = cur.fetchone()
        return self._row(row)

    def get(self, request_id: str) -> ApprovalRecord | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM qwa_approvals WHERE request_id = %s",
                    (request_id,),
                )
                row = cur.fetchone()
        return self._row(row) if row else None

    def decide(self, request_id: str, status: str, approver: str,
               reason: str | None = None) -> ApprovalRecord:
        if status not in {"approved", "rejected"}:
            raise ValueError("status must be approved or rejected")
        with self._connect() as conn:
            with conn.cursor() as cur:
                # Lock the approval row so concurrent operators cannot both
                # transition the same pending request.
                cur.execute(
                    "SELECT * FROM qwa_approvals WHERE request_id = %s FOR UPDATE",
                    (request_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise KeyError(request_id)
                current = self._row(row)
                if current.status in TERMINAL:
                    raise ValueError(f"approval is already {current.status}")
                decided = _now()
                cur.execute("""
                    UPDATE qwa_approvals
                    SET status = %s, approver = %s, reason = %s, decided_at = %s
                    WHERE request_id = %s AND status = 'pending'
                """, (status, approver, reason, decided, request_id))
                cur.execute(
                    "SELECT * FROM qwa_approvals WHERE request_id = %s",
                    (request_id,),
                )
                row = cur.fetchone()
        return self._row(row)

    @staticmethod
    def _row(row) -> ApprovalRecord:
        return ApprovalRecord(
            request_id=row[0], actor=row[1], tool=row[2],
            request_hash=row[3], status=row[4], approver=row[5],
            reason=row[6], created_at=row[7].isoformat() if hasattr(row[7], "isoformat") else row[7],
            decided_at=row[8].isoformat() if row[8] is not None and hasattr(row[8], "isoformat") else row[8],
        )
