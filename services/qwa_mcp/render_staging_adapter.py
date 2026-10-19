"""Render-backed staging adapter with allowlisted service resolution."""
import re

from .adapters import AdapterResponse
from .deployment_store import DeploymentRecord
from .service_registry import ServiceRegistry

_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


class RenderStagingAdapter:
    def __init__(self, registry: ServiceRegistry, gateway, deployment_store=None):
        self.registry = registry
        self.gateway = gateway
        self.deployment_store = deployment_store

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
        try:
            binding = self._binding(service)
            revision = self._revision(revision)
        except Exception as exc:
            return AdapterResponse(False, "deploy", {}, str(exc))

        result = self._call("deploy", self.gateway.deploy, binding.resource_id, revision)
        if result.ok:
            deploy_id = result.data.get("id")
            if not deploy_id:
                return AdapterResponse(False, "deploy", {}, "Render deploy response missing deploy id")
            result.data.update({
                "service": binding.name,
                "resource_id": binding.resource_id,
                "revision": revision,
                "request_id": request_id,
                "trace_id": trace_id,
                "deploy_id": deploy_id,
            })
            if self.deployment_store and request_id:
                self.deployment_store.create(DeploymentRecord(
                    request_id, trace_id or "", binding.name, binding.provider,
                    binding.resource_id, revision, deploy_id,
                    result.data.get("status", "created"),
                ))
        return result

    def status(self, service, deploy_id, request_id=None):
        try:
            binding = self._binding(service)
        except Exception as exc:
            return AdapterResponse(False, "status", {}, str(exc))

        result = self._call("status", self.gateway.deployment_status, binding.resource_id, deploy_id)
        if result.ok and self.deployment_store:
            status = result.data.get("status", "unknown")
            if request_id:
                self.deployment_store.update_status(request_id, status)
            elif self.deployment_store.get_by_deploy_id(deploy_id):
                self.deployment_store.update_status_by_deploy_id(deploy_id, status)
        return result

    def logs(self, service, start_time=None, end_time=None):
        try:
            binding = self._binding(service)
        except Exception as exc:
            return AdapterResponse(False, "logs", {}, str(exc))

        if not binding.owner_id:
            return AdapterResponse(False, "logs", {}, "Render owner_id is required for log queries")
        return self._call(
            "logs", self.gateway.logs, binding.owner_id, binding.resource_id,
            start_time, end_time,
        )

    def wait(self, service, deploy_id, timeout_seconds=900, poll_seconds=5):
        try:
            binding = self._binding(service)
        except Exception as exc:
            return AdapterResponse(False, "wait", {}, str(exc))

        result = self._call(
            "wait", self.gateway.wait_for_deploy, binding.resource_id,
            deploy_id, timeout_seconds, poll_seconds,
        )
        if result.ok and self.deployment_store and self.deployment_store.get_by_deploy_id(deploy_id):
            self.deployment_store.update_status_by_deploy_id(
                deploy_id, result.data.get("status", "unknown")
            )
        return result
