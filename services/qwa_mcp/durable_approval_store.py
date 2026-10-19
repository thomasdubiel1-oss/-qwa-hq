"""Durable approval storage for the QWA control plane.

SQLite is the local durable implementation. It is suitable for a single
control-plane process and development/staging. Production can replace the
backend behind the same interface with managed PostgreSQL.
"""
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


TERMINAL = {"approved", "rejected", "expired"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_hash(tool: str, actor: str, arguments: dict) -> str:
    payload = json.dumps(
        {"tool": tool, "actor": actor, "arguments": arguments},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ApprovalRecord:
    request_id: str
    actor: str
    tool: str
    request_hash: str
    status: str
    approver: str | None = None
    reason: str | None = None
    created_at: str = ""
    decided_at: str | None = None


class SQLiteApprovalStore:
    """Transactional approval store with immutable request identity."""

    def __init__(self, path: str = ".qwa/approvals.sqlite3"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS approvals (
                    request_id TEXT PRIMARY KEY,
                    actor TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    approver TEXT,
                    reason TEXT,
                    created_at TEXT NOT NULL,
                    decided_at TEXT
                )
                """
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_approvals_request_hash "
                "ON approvals(request_hash)"
            )

    def _connect(self):
        return sqlite3.connect(self.path)

    def create(self, approval: ApprovalRecord) -> ApprovalRecord:
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT * FROM approvals WHERE request_id = ?", (approval.request_id,)
            ).fetchone()
            if existing:
                return self._row(existing)
            same_hash = conn.execute(
                "SELECT request_id FROM approvals WHERE request_hash = ?", (approval.request_hash,)
            ).fetchone()
            if same_hash and same_hash[0] != approval.request_id:
                raise ValueError("request hash already exists for another request_id")
            conn.execute(
                """INSERT INTO approvals
                (request_id, actor, tool, request_hash, status, approver, reason,
                 created_at, decided_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    approval.request_id, approval.actor, approval.tool,
                    approval.request_hash, approval.status, approval.approver,
                    approval.reason, approval.created_at or _now(), approval.decided_at,
                ),
            )
        return self.get(approval.request_id)

    def get(self, request_id: str) -> ApprovalRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM approvals WHERE request_id = ?", (request_id,)
            ).fetchone()
        return self._row(row) if row else None

    def decide(self, request_id: str, status: str, approver: str, reason: str | None = None) -> ApprovalRecord:
        if status not in {"approved", "rejected"}:
            raise ValueError("status must be approved or rejected")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status FROM approvals WHERE request_id = ?", (request_id,)
            ).fetchone()
            if row is None:
                raise KeyError(request_id)
            if row[0] in TERMINAL:
                raise ValueError(f"approval is already {row[0]}")
            conn.execute(
                """UPDATE approvals
                   SET status = ?, approver = ?, reason = ?, decided_at = ?
                   WHERE request_id = ? AND status = 'pending'""",
                (status, approver, reason, _now(), request_id),
            )
        return self.get(request_id)

    @staticmethod
    def _row(row) -> ApprovalRecord:
        return ApprovalRecord(
            request_id=row[0], actor=row[1], tool=row[2], request_hash=row[3],
            status=row[4], approver=row[5], reason=row[6], created_at=row[7],
            decided_at=row[8],
        )
