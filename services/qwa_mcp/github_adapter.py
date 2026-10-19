"""Provider-neutral GitHub adapter with explicit gateway boundary."""

from dataclasses import dataclass
from typing import Protocol

from .adapters import AdapterResponse


class GitHubGateway(Protocol):
    def inspect_repo(self, repo: str) -> dict: ...
    def create_branch(self, repo: str, branch: str, base: str) -> dict: ...
    def create_pr(self, repo: str, head: str, base: str, title: str) -> dict: ...
    def ci_status(self, repo: str, sha: str) -> dict: ...


@dataclass
class GitHubConnectorAdapter:
    gateway: GitHubGateway

    def inspect_repo(self, repo: str) -> AdapterResponse:
        return self._call("inspect_repo", self.gateway.inspect_repo, repo)

    def create_branch(self, repo: str, branch: str, base: str) -> AdapterResponse:
        return self._call("create_branch", self.gateway.create_branch, repo, branch, base)

    def create_pr(self, repo: str, head: str, base: str, title: str) -> AdapterResponse:
        return self._call("create_pr", self.gateway.create_pr, repo, head, base, title)

    def ci_status(self, repo: str, sha: str) -> AdapterResponse:
        return self._call("ci_status", self.gateway.ci_status, repo, sha)

    def _call(self, operation: str, fn, *args) -> AdapterResponse:
        try:
            return AdapterResponse(True, operation, fn(*args))
        except Exception as exc:
            return AdapterResponse(False, operation, {}, str(exc))
