"""Allowlisted mapping from logical staging services to provider resource IDs."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ServiceBinding:
    name: str
    provider: str
    resource_id: str
    environment: str = "staging"

class ServiceRegistry:
    def __init__(self, bindings):
        self._bindings = {b.name: b for b in bindings}

    def resolve(self, name):
        binding = self._bindings.get(name)
        if binding is None:
            raise KeyError(f"unknown service: {name}")
        if binding.environment != "staging":
            raise PermissionError("service is not a staging resource")
        return binding
