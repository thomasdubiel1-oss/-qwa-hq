from .approval_store import Approval, ApprovalStore
from .catalog import CATALOG
from .models import ToolRequest, ToolResult

LEVEL_ORDER = {"read": 0, "development": 1, "staging": 2, "production": 3}

class QWAMCPServer:
    """Policy-first dispatcher. External adapters plug in behind dispatch()."""
    def __init__(self, approvals: ApprovalStore | None = None):
        self.approvals = approvals or ApprovalStore()

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
        """Validate and authorize; adapter execution is deliberately not implicit."""
        result = self.authorize(request)
        if result.status != "authorized":
            return result
        return ToolResult(True, "adapter_required", {
            "tool": request.tool,
            "arguments": request.arguments,
            "message": "No external adapter is wired in yet; no side effect was performed.",
        })
