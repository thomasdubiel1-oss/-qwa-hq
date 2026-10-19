"""Durable deployment lifecycle storage for staging control."""
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def _now():
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class DeploymentRecord:
    request_id: str
    trace_id: str
    service: str
    provider: str
    resource_id: str
    revision: str
    deploy_id: str
    status: str
    created_at: str = ""
    updated_at: str = ""


class SQLiteDeploymentStore:
    def __init__(self, path=".qwa/deployments.sqlite3"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS deployments (
                    request_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    service TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    revision TEXT NOT NULL,
                    deploy_id TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

    def _connect(self):
        return sqlite3.connect(self.path)

    def create(self, record):
        now = _now()
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM deployments WHERE request_id = ?", (record.request_id,)).fetchone()
            if existing:
                current = self._row(existing)
                identity = (current.trace_id, current.service, current.provider, current.resource_id, current.revision, current.deploy_id)
                requested = (record.trace_id, record.service, record.provider, record.resource_id, record.revision, record.deploy_id)
                if identity != requested:
                    raise ValueError("request_id is already bound to a different deployment")
                return current
            conn.execute(
                """INSERT INTO deployments
                   (request_id, trace_id, service, provider, resource_id,
                    revision, deploy_id, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (record.request_id, record.trace_id, record.service, record.provider,
                 record.resource_id, record.revision, record.deploy_id, record.status,
                 record.created_at or now, record.updated_at or now),
            )
        return self.get(record.request_id)

    def get(self, request_id):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM deployments WHERE request_id = ?", (request_id,)).fetchone()
        return self._row(row) if row else None

    def get_by_deploy_id(self, deploy_id):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM deployments WHERE deploy_id = ?", (deploy_id,)).fetchone()
        return self._row(row) if row else None

    def update_status(self, request_id, status):
        with self._connect() as conn:
            changed = conn.execute(
                "UPDATE deployments SET status = ?, updated_at = ? WHERE request_id = ?",
                (status, _now(), request_id),
            ).rowcount
        if not changed:
            raise KeyError(request_id)
        return self.get(request_id)

    def update_status_by_deploy_id(self, deploy_id, status):
        record = self.get_by_deploy_id(deploy_id)
        if record is None:
            raise KeyError(deploy_id)
        return self.update_status(record.request_id, status)

    @staticmethod
    def _row(row):
        return DeploymentRecord(
            request_id=row[0], trace_id=row[1], service=row[2],
            provider=row[3], resource_id=row[4], revision=row[5],
            deploy_id=row[6], status=row[7], created_at=row[8], updated_at=row[9],
        )
