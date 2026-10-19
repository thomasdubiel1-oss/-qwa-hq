import unittest
from datetime import datetime, timezone

from .durable_approval_store import ApprovalRecord
from .postgres_approval_store import PostgresApprovalStore


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.row = None

    def execute(self, sql, params=()):
        normalized = " ".join(sql.split())
        if normalized.startswith("CREATE TABLE") or normalized.startswith("CREATE TABLE IF"):
            return
        if normalized.startswith("INSERT INTO"):
            if params[0] not in self.conn.rows:
                self.conn.rows[params[0]] = list(params)
            return
        if "FOR UPDATE" in normalized:
            self.row = self.conn.rows.get(params[0])
            return
        if normalized.startswith("SELECT * FROM qwa_approvals"):
            self.row = self.conn.rows.get(params[0])
            return
        if normalized.startswith("UPDATE qwa_approvals"):
            row = self.conn.rows[params[4]]
            if row[4] == "pending":
                row[4], row[5], row[6], row[8] = params[0], params[1], params[2], params[3]
            return
        raise AssertionError(f"unexpected SQL: {normalized}")

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def cursor(self): return FakeCursor(self)


class FakeFactory:
    def __init__(self):
        self.rows = {}
    def __call__(self):
        return FakeConnection(self.rows)


class PostgresApprovalStoreTests(unittest.TestCase):
    def test_create_get_and_atomic_decide(self):
        factory = FakeFactory()
        store = PostgresApprovalStore(factory)
        record = ApprovalRecord("r1", "hermes", "request_change", "h1", "pending")
        created = store.create(record)
        self.assertEqual(created.request_id, "r1")
        self.assertEqual(store.get("r1").status, "pending")
        decided = store.decide("r1", "approved", "operator", "ok")
        self.assertEqual(decided.status, "approved")
        self.assertEqual(decided.approver, "operator")

    def test_second_decision_fails(self):
        factory = FakeFactory()
        store = PostgresApprovalStore(factory)
        store.create(ApprovalRecord("r1", "hermes", "request_change", "h1", "pending"))
        store.decide("r1", "approved", "operator")
        with self.assertRaises(ValueError):
            store.decide("r1", "rejected", "operator")
