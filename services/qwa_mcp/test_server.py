import tempfile
from pathlib import Path

from .approval_store import ApprovalStore
from .server import QWAMCPServer
from .models import ToolRequest


def test_read_tool_authorizes():
    server = QWAMCPServer(ApprovalStore(str(Path(tempfile.mkdtemp()) / "a.jsonl")))
    result = server.dispatch(ToolRequest("repo_inspect", "hermes", "read", {"repo": "qwa"}, "r1"))
    assert result.status == "adapter_required"


def test_production_requires_approval():
    path = Path(tempfile.mkdtemp()) / "a.jsonl"
    server = QWAMCPServer(ApprovalStore(str(path)))
    result = server.dispatch(ToolRequest("request_change", "hermes", "production", {}, "r2"))
    assert result.status == "approval_required"
    assert server.approvals.get("r2").status == "pending"


def test_insufficient_level_is_denied():
    server = QWAMCPServer(ApprovalStore(str(Path(tempfile.mkdtemp()) / "a.jsonl")))
    result = server.dispatch(ToolRequest("deploy_staging", "hermes", "development", {}, "r3"))
    assert result.status == "denied"
