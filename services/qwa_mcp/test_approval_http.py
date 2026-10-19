import tempfile
import unittest
from pathlib import Path

from .approval_http import ApprovalAPI
from .durable_approval_store import ApprovalRecord, SQLiteApprovalStore

class ApprovalHTTPTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.mkdtemp()) / "approvals.sqlite3"
        self.store = SQLiteApprovalStore(str(self.path))
        self.store.create(ApprovalRecord("r1", "hermes", "request_change", "h1", "pending"))
        self.api = ApprovalAPI(self.store, token="secret")

    def test_authentication(self):
        self.assertTrue(self.api.authenticate("Bearer secret"))
        self.assertFalse(self.api.authenticate("Bearer wrong"))

    def test_get_and_approve(self):
        status, body = self.api.get("r1")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "pending")
        status, body = self.api.decide("r1", "approved", "operator", "reviewed")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "approved")
        self.assertEqual(self.store.get("r1").status, "approved")

if __name__ == "__main__":
    unittest.main()
