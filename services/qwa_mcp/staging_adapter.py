"""Provider-neutral staging deployment contract."""
from typing import Protocol
from .adapters import AdapterResponse
class StagingGateway(Protocol):
    def deploy(self, service: str, revision: str) -> dict: ...
    def status(self, service: str) -> dict: ...
    def logs(self, service: str, limit: int = 100) -> dict: ...
class StagingAdapter:
    def __init__(self, gateway): self.gateway = gateway
    def _call(self, op, fn, *args):
        try: return AdapterResponse(True, op, fn(*args))
        except Exception as exc: return AdapterResponse(False, op, {}, str(exc))
    def deploy(self, service, revision): return self._call("deploy", self.gateway.deploy, service, revision)
    def status(self, service): return self._call("status", self.gateway.status, service)
    def logs(self, service, limit=100): return self._call("logs", self.gateway.logs, service, min(max(int(limit),1),500))
