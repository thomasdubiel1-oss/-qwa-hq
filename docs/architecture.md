# QWA Control-Plane Architecture

Phone/laptop -> authenticated remote access -> Hermes -> agent router -> Claude Code/Opus, Codex, QWA MCP and scheduled subagents -> GitHub -> staging -> production.

Hermes coordinates work and active agent state. Engineering agents implement bounded tasks. Obsidian stores durable knowledge. GitHub stores executable code/configuration and audit history.

Security: no unrestricted production credentials, no production customer data in development, least-privilege MCP tools, explicit human approval for production changes, secrets outside Git and Obsidian.
