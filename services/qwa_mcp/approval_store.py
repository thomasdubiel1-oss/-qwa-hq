import json
from dataclasses import asdict, dataclass
from pathlib import Path

@dataclass
class Approval:
    request_id: str
    actor: str
    tool: str
    status: str = "pending"
    approver: str | None = None
    reason: str | None = None

class ApprovalStore:
    """Small JSONL store for development; production should use durable DB storage."""
    def __init__(self, path: str = ".qwa/approvals.jsonl"):
        self.path = Path(path)

    def create(self, approval: Approval) -> Approval:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(approval), sort_keys=True) + "\n")
        return approval

    def get(self, request_id: str) -> Approval | None:
        if not self.path.exists():
            return None
        found = None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = Approval(**json.loads(line))
                if item.request_id == request_id:
                    found = item
        return found
