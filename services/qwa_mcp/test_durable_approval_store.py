import tempfile
import unittest
from pathlib import Path

from .durable_approval_store import ApprovalRecord, SQLiteApprovalStore, request_hash


class DurableApprovalStoreTests(unittest.TestCase):
    def test_sqlite_approval_survives_reopen(self):
        path = Path(tempfile.mkdtemp()) / "approvals.sqlite3"
        store = SQLiteApprovalStore(str(path))
        record = ApprovalRecord(
            "r1", "hermes", "request_change",
            request_hash("request_change", "hermes", {"x": 1}), "pending"
        )
        store.create(record)
        reopened = SQLiteApprovalStore(str(path))
        self.assertEqual(reopened.get("r1").status, "pending")

    def test_approval_can_be_decided_once(self):
        path = Path(tempfile.mkdtemp()) / "approvals.sqlite3"
        store = SQLiteApprovalStore(str(path))
        store.create(ApprovalRecord("r1", "hermes", "request_change", "hash1", "pending"))
        approved = store.decide("r1", "approved", "operator", "reviewed")
        self.assertEqual(approved.status, "approved")
        self.assertEqual(approved.approver, "operator")
        with self.assertRaises(ValueError):
            store.decide("r1", "rejected", "operator")

    def test_duplicate_request_id_does_not_create_second_record(self):
        path = Path(tempfile.mkdtemp()) / "approvals.sqlite3"
        store = SQLiteApprovalStore(str(path))
        record = ApprovalRecord("r1", "hermes", "request_change", "hash1", "pending")
        store.create(record)
        store.create(record)
        self.assertEqual(store.get("r1").request_id, "r1")


if __name__ == "__main__":
    unittest.main()
