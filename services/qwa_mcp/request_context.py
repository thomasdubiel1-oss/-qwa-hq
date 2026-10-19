"""Replay-safe request context and lightweight metrics primitives."""
from dataclasses import dataclass, field
from time import monotonic
from uuid import uuid4

@dataclass(frozen=True)
class RequestContext:
    request_id: str
    actor: str
    trace_id: str
    @classmethod
    def create(cls, actor: str, request_id: str | None = None, trace_id: str | None = None):
        return cls(request_id or str(uuid4()), actor, trace_id or str(uuid4()))

@dataclass
class Metrics:
    counters: dict[str, int] = field(default_factory=dict)
    durations_ms: list[float] = field(default_factory=list)
    def increment(self, name: str) -> None:
        self.counters[name] = self.counters.get(name, 0) + 1
    def observe(self, started: float) -> float:
        duration = (monotonic() - started) * 1000
        self.durations_ms.append(duration)
        return duration
