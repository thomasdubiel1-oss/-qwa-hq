# QWA Control Plane v1

This layer defines routing, permissions, approvals and audit contracts. Hermes is the orchestrator; MCP is the adapter boundary; GitHub/CI is the executable change boundary.

Hermes supports stdio and HTTP MCP servers plus per-server tool filtering, so QWA will expose the smallest useful tool surface rather than a broad unrestricted integration.
