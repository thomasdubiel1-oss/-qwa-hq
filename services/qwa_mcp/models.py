from dataclasses import dataclass, field
from typing import Any, Literal

Risk = Literal["low", "medium", "high", "production"]

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    risk: Risk
    required_level: str
    mutating: bool = False
    approval_required: bool = False

@dataclass(frozen=True)
class ToolRequest:
    tool: str
    actor: str
    level: str
    arguments: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""

@dataclass(frozen=True)
class ToolResult:
    ok: bool
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
