"""Scoped knowledge adapter for an Obsidian-compatible vault.

The adapter intentionally supports only approved knowledge paths. It is a
local filesystem implementation so the core MCP service stays independent of
any particular Obsidian plugin or transport.
"""

from dataclasses import dataclass
from pathlib import Path

from .adapters import AdapterResponse

DEFAULT_ALLOWED = ("architecture/", "decisions/", "runbooks/", "research/")


@dataclass
class ScopedKnowledgeAdapter:
    root: Path
    allowed_prefixes: tuple[str, ...] = DEFAULT_ALLOWED

    def _path(self, relative: str) -> Path:
        if relative.startswith("/") or ".." in Path(relative).parts:
            raise ValueError("path escapes knowledge root")
        if not any(relative.startswith(prefix) for prefix in self.allowed_prefixes):
            raise PermissionError("knowledge path is outside the approved scope")
        candidate = (self.root / relative).resolve()
        root = self.root.resolve()
        if candidate != root and root not in candidate.parents:
            raise ValueError("resolved path escapes knowledge root")
        return candidate

    def search(self, query: str) -> AdapterResponse:
        matches = []
        for path in self.root.rglob("*.md"):
            rel = path.relative_to(self.root).as_posix()
            if any(rel.startswith(p) for p in self.allowed_prefixes):
                text = path.read_text(encoding="utf-8")
                if query.lower() in text.lower():
                    matches.append(rel)
        return AdapterResponse(True, "search", {"matches": matches})

    def read(self, path: str) -> AdapterResponse:
        target = self._path(path)
        return AdapterResponse(True, "read", {"path": path, "content": target.read_text(encoding="utf-8")})

    def write_decision(self, path: str, content: str) -> AdapterResponse:
        return self._write("write_decision", path, content)

    def write_runbook(self, path: str, content: str) -> AdapterResponse:
        return self._write("write_runbook", path, content)

    def _write(self, operation: str, path: str, content: str) -> AdapterResponse:
        target = self._path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return AdapterResponse(True, operation, {"path": path})
