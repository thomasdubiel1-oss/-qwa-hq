from .approval_store import Approval, ApprovalStore
from .catalog import CATALOG
from .models import ToolRequest, ToolResult
from .adapters import AdapterResponse, DryRunAdapter

LEVEL_ORDER = {"read": 0, "development": 1, "staging": 2, "production": 3}


class QWAMCPServer:
    """Policy-first dispatcher with explicit, injectable tool adapters."""

    def __init__(self, approvals: ApprovalStore | None = None, adapters: dict | None = None):
        self.approvals = approvals or ApprovalStore()
        self.adapters = adapters or {}

    def authorize(self, request: ToolRequest) -> ToolResult:
        spec = CATALOG.get(request.tool)
        if spec is None:
            return ToolResult(False, "denied", error="unknown tool")
        if LEVEL_ORDER.get(request.level, -1) < LEVEL_ORDER.get(spec.required_level, 99):
            return ToolResult(False, "denied", error=f"requires {spec.required_level} level")
        if spec.approval_required:
            approval = self.approvals.create(Approval(request.request_id, request.actor, request.tool))
            return ToolResult(True, "approval_required", {"request_id": approval.request_id})
        return ToolResult(True, "authorized", {"tool": spec.name})

    def dispatch(self, request: ToolRequest) -> ToolResult:
        result = self.authorize(request)
        if result.status != "authorized":
            return result
        adapter = self.adapters.get(request.tool, DryRunAdapter())
        try:
            operation = getattr(adapter, self._operation_name(request.tool))
            response = operation(**request.arguments)
        except Exception as exc:
            return ToolResult(False, "adapter_error", error=str(exc))
        if not isinstance(response, AdapterResponse):
            return ToolResult(False, "adapter_error", error="adapter returned invalid response")
        return ToolResult(response.ok, "executed" if response.ok else "adapter_error",
                          {"operation": response.operation, "data": response.data},
                          error=response.error)

    @staticmethod
    def _operation_name(tool: str) -> str:
        return {
            "repo_inspect": "inspect_repo",
            "branch_create": "create_branch",
            "pr_create": "create_pr",
            "ci_status": "ci_status",
            "knowledge_search": "search",
            "knowledge_read": "read",
            "knowledge_write_decision": "write_decision",
            "knowledge_write_runbook": "write_runbook",
        }.get(tool, tool)
