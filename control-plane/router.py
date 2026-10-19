"""Small, dependency-free policy router prototype for QWA."""
from dataclasses import dataclass
from typing import Literal

Decision = Literal['allow', 'deny', 'approval_required']

@dataclass(frozen=True)
class Request:
    actor: str
    level: str
    action: str
    resource: str
    production: bool = False

@dataclass(frozen=True)
class Result:
    decision: Decision
    reason: str

def authorize(req: Request) -> Result:
    if req.production:
        if req.level != 'production':
            return Result('deny', 'production access requires production level')
        return Result('approval_required', 'production mutation requires human approval')
    if req.action in {'read', 'inspect', 'test'}:
        return Result('allow', 'read-only or validation action')
    if req.level in {'development', 'staging', 'production'}:
        return Result('allow', 'non-production action within assigned level')
    return Result('deny', 'insufficient permission level')
