import tempfile
import unittest
from pathlib import Path

from .approval_store import ApprovalStore
from .server import QWAMCPServer
from .models import ToolRequest


class ServerTests(unittest.TestCase):
    def test_read_tool_authorizes(self):
        server = QWAMCPServer(ApprovalStore(str(Path(tempfile.mkdtemp()) / "a.jsonl")))
        result = server.dispatch(ToolRequest("repo_inspect", "hermes", "read", {"repo": "qwa"}, "r1"))
        self.assertEqual(result.status, "executed")

    def test_production_requires_approval(self):
        path = Path(tempfile.mkdtemp()) / "a.jsonl"
        server = QWAMCPServer(ApprovalStore(str(path)))
        result = server.dispatch(ToolRequest("request_change", "hermes", "production", {}, "r2"))
        self.assertEqual(result.status, "approval_required")
        self.assertEqual(server.approvals.get("r2").status, "pending")

    def test_insufficient_level_is_denied(self):
        server = QWAMCPServer(ApprovalStore(str(Path(tempfile.mkdtemp()) / "a.jsonl")))
        result = server.dispatch(ToolRequest("deploy_staging", "hermes", "development", {}, "r3"))
        self.assertEqual(result.status, "denied")


if __name__ == "__main__":
    unittest.main()
