from .approval_store import Approval, ApprovalStore
from .catalog import CATALOG
from .models import ToolRequest, ToolResult
from .idempotency import IdempotencyStore
from .request_context import Metrics
from .adapters import AdapterResponse, DryRunAdapter
from .durable_approval_store import ApprovalRecord, SQLiteApprovalStore, request_hash

LEVEL_ORDER = {"read": 0, "development": 1, "staging": 2, "production": 3}


class QWAMCPServer:
    """Policy-first dispatcher with explicit, injectable tool adapters."""

    def __init__(self, approvals=None, adapters: dict | None = None,
                 idempotency: IdempotencyStore | None = None,
                 metrics: Metrics | None = None):
        self.approvals = approvals or SQLiteApprovalStore()
        self.adapters = adapters or {}
        self.idempotency = idempotency or IdempotencyStore()
        self.metrics = metrics or Metrics()

    def authorize(self, request: ToolRequest) -> ToolResult:
        spec = CATALOG.get(request.tool)
        if spec is None:
            return ToolResult(False, "denied", error="unknown tool")
        if LEVEL_ORDER.get(request.level, -1) < LEVEL_ORDER.get(spec.required_level, 99):
            return ToolResult(False, "denied", error=f"requires {spec.required_level} level")
        if spec.approval_required:
            try:
                if isinstance(self.approvals, SQLiteApprovalStore) or self._durable_store(self.approvals):
                    approval = self.approvals.create(
                        ApprovalRecord(
                            request.request_id,
                            request.actor,
                            request.tool,
                            request_hash(request.tool, request.actor, request.arguments),
                            "pending",
                        )
                    )
                else:
                    approval = self.approvals.create(
                        Approval(request.request_id, request.actor, request.tool)
                    )
            except ValueError as exc:
                return ToolResult(False, "approval_error", error=str(exc))
            return ToolResult(True, "approval_required", {"request_id": approval.request_id})
        return ToolResult(True, "authorized", {"tool": spec.name})

    @staticmethod
    def _durable_store(store) -> bool:
        return all(hasattr(store, name) for name in ("create", "get", "decide"))

    def approve(self, request_id: str, approver: str, reason: str | None = None) -> ToolResult:
        """Record an explicit human approval; this does not execute the mutation."""
        if not self._durable_store(self.approvals):
            return ToolResult(False, "approval_error", error="approval decision requires durable store")
        try:
            record = self.approvals.decide(request_id, "approved", approver, reason)
        except (KeyError, ValueError) as exc:
            return ToolResult(False, "approval_error", error=str(exc))
        return ToolResult(True, "approved", {
            "request_id": record.request_id, "approver": record.approver,
            "decided_at": record.decided_at,
        })

    def reject(self, request_id: str, approver: str, reason: str | None = None) -> ToolResult:
        """Record an explicit human rejection; this does not execute anything."""
        if not self._durable_store(self.approvals):
            return ToolResult(False, "approval_error", error="approval decision requires durable store")
        try:
            record = self.approvals.decide(request_id, "rejected", approver, reason)
        except (KeyError, ValueError) as exc:
            return ToolResult(False, "approval_error", error=str(exc))
        return ToolResult(True, "rejected", {
            "request_id": record.request_id, "approver": record.approver,
            "decided_at": record.decided_at,
        })

    def dispatch(self, request: ToolRequest) -> ToolResult:
        cached = self.idempotency.get(request.request_id)
        if cached is not None:
            self.metrics.increment("tool.replays")
            return cached
        self.metrics.increment("tool.calls")
        result = self.authorize(request)
        if result.status != "authorized":
            self.idempotency.put(request.request_id, result)
            return result
        adapter = self.adapters.get(request.tool, DryRunAdapter())
        try:
            operation = getattr(adapter, self._operation_name(request.tool))
            response = operation(**request.arguments)
        except Exception as exc:
            return ToolResult(False, "adapter_error", error=str(exc))
        if not isinstance(response, AdapterResponse):
            return ToolResult(False, "adapter_error", error="adapter returned invalid response")
        result = ToolResult(
            response.ok,
            "executed" if response.ok else "adapter_error",
            {"operation": response.operation, "data": response.data},
            error=response.error,
        )
        self.idempotency.put(request.request_id, result)
        return result

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
