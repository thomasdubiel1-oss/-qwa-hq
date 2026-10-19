import tempfile
import unittest
from pathlib import Path

from .adapters import AdapterResponse
from .approval_store import ApprovalStore
from .durable_approval_store import SQLiteApprovalStore
from .server import QWAMCPServer
from .models import ToolRequest


class FakeStagingAdapter:
    def __init__(self):
        self.calls = []

    def deploy(self, service, revision, request_id=None, trace_id=None):
        self.calls.append((service, revision, request_id, trace_id))
        return AdapterResponse(True, "deploy", {"deploy_id": "dep-1"})


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

    def test_approved_staging_deploy_retries_and_executes_adapter(self):
        approvals = SQLiteApprovalStore(str(Path(tempfile.mkdtemp()) / "approvals.sqlite3"))
        adapter = FakeStagingAdapter()
        server = QWAMCPServer(approvals=approvals, adapters={"deploy_staging": adapter})
        request = ToolRequest(
            "deploy_staging", "hermes", "staging",
            {"service": "api", "revision": "a" * 40}, "deploy-r1",
        )

        pending = server.dispatch(request)
        self.assertEqual(pending.status, "approval_required")
        approved = server.approve("deploy-r1", "operator")
        self.assertEqual(approved.status, "approved")

        executed = server.dispatch(request)
        self.assertEqual(executed.status, "executed")
        self.assertEqual(adapter.calls, [("api", "a" * 40, "deploy-r1", "deploy-r1")])

    def test_staging_operation_names_map_to_adapter_methods(self):
        self.assertEqual(QWAMCPServer._operation_name("deploy_staging"), "deploy")
        self.assertEqual(QWAMCPServer._operation_name("deployment_status"), "status")
        self.assertEqual(QWAMCPServer._operation_name("logs"), "logs")


if __name__ == "__main__":
    unittest.main()
