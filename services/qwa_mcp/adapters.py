"""Adapter contracts for external QWA systems.

These adapters are intentionally dry-run interfaces until credentials and
service-specific implementations are connected.
"""
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class AdapterResponse:
    ok: bool
    operation: str
    data: dict
    error: str | None = None

class GitHubAdapter(Protocol):
    def inspect_repo(self, repo: str) -> AdapterResponse: ...
    def create_branch(self, repo: str, branch: str, base: str) -> AdapterResponse: ...
    def create_pr(self, repo: str, head: str, base: str, title: str) -> AdapterResponse: ...
    def ci_status(self, repo: str, sha: str) -> AdapterResponse: ...

class StagingAdapter(Protocol):
    def deploy(self, service: str, revision: str) -> AdapterResponse: ...
    def status(self, service: str) -> AdapterResponse: ...
    def logs(self, service: str, limit: int = 100) -> AdapterResponse: ...

class KnowledgeAdapter(Protocol):
    def search(self, query: str) -> AdapterResponse: ...
    def read(self, path: str) -> AdapterResponse: ...
    def write_decision(self, path: str, content: str) -> AdapterResponse: ...
    def write_runbook(self, path: str, content: str) -> AdapterResponse: ...

class DryRunAdapter:
    """Safe placeholder that makes the absence of a real adapter explicit."""
    def __getattr__(self, operation):
        def call(**kwargs):
            return AdapterResponse(True, operation, {"dry_run": True, "arguments": kwargs})
        return call
