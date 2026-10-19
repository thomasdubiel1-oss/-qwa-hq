"""QWA MCP service layer: validated, policy-gated tool contracts."""

from .server import QWAMCPServer
from .adapters import DryRunAdapter, AdapterResponse
from .github_adapter import GitHubConnectorAdapter
from .knowledge_adapter import ScopedKnowledgeAdapter

__all__ = ["QWAMCPServer", "DryRunAdapter", "AdapterResponse", "GitHubConnectorAdapter", "ScopedKnowledgeAdapter"]
