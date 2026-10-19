"""Render-backed staging adapter with allowlisted service resolution."""
import re

from .adapters import AdapterResponse
from .service_registry import ServiceRegistry

_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


class RenderStagingAdapter:
    def __init__(self, registry: ServiceRegistry, gateway):
        self.registry = registry
        self.gateway = gateway

    def _binding(self, service):
        binding = self.registry.resolve(service)
        if binding.provider != "render":
            raise PermissionError("service is not bound to Render")
        return binding

    @staticmethod
    def _revision(revision):
        if not isinstance(revision, str) or not _SHA_RE.fullmatch(revision):
            raise ValueError("revision must be a 40-character Git commit SHA")
        return revision.lower()

    def _call(self, operation, fn, *args):
        try:
            return AdapterResponse(True, operation, fn(*args))
        except Exception as exc:
            return AdapterResponse(False, operation, {}, str(exc))

    def deploy(self, service, revision, request_id=None, trace_id=None):
        binding = self._binding(service)
        result = self._call("deploy", self.gateway.deploy, binding.resource_id, self._revision(revision))
        if result.ok:
            result.data.update({
                "service": binding.name,
                "resource_id": binding.resource_id,
                "revision": revision.lower(),
                "request_id": request_id,
                "trace_id": trace_id,
                "deploy_id": result.data.get("id"),
            })
        return result

    def status(self, service, deploy_id):
        binding = self._binding(service)
        return self._call("status", self.gateway.deployment_status, binding.resource_id, deploy_id)

    def logs(self, service, start_time=None, end_time=None):
        binding = self._binding(service)
        if not binding.owner_id:
            return AdapterResponse(False, "logs", {}, "Render owner_id is required for log queries")
        return self._call(
            "logs",
            self.gateway.logs,
            binding.owner_id,
            binding.resource_id,
            start_time,
            end_time,
        )

    def wait(self, service, deploy_id, timeout_seconds=900, poll_seconds=5):
        binding = self._binding(service)
        return self._call(
            "wait",
            self.gateway.wait_for_deploy,
            binding.resource_id,
            deploy_id,
            timeout_seconds,
            poll_seconds,
        )
