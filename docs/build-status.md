# QWA Build Status

Completed: permission model, agent routing, audit schema/writer, production approval contract, unit tests, CI, Hermes MCP boundary, filtered-server plan, QWA MCP tool catalog, policy-first dispatcher, development approval store, provider-neutral GitHub/knowledge/staging adapters, replay protection, request/trace context, metrics foundation, and durable SQLite approvals.

## Current architecture

Phone / WhatsApp -> Hermes -> QWA policy router -> MCP tool boundary -> provider adapters -> GitHub / staging / knowledge / production.

The dispatcher validates and authorizes requests before adapter execution. Production mutations remain approval-gated. Approval decisions are now persisted in SQLite by default for local durability; a managed PostgreSQL implementation remains the production target.

## Current safety guarantees

- Production mutation requests cannot execute directly.
- Approval records have immutable request identity and a request hash.
- Approval decisions are one-way: pending -> approved/rejected.
- Replayed request IDs are served from idempotency storage.
- Provider integrations remain behind narrow gateway protocols.
- Tests use fakes/dry-run adapters and do not require production credentials.
- Local approval databases are ignored by Git.

## Next

1. Add a managed Postgres approval repository and transaction/locking tests.
2. Bind approved Render service aliases and deploy-state polling behind the staging protocol.
3. Add an operator approval surface/API with authentication and audit events.
4. Add production execution only through an approved request token and replay-safe transaction.
5. Add cost budgets, rate limits, and evaluation/observability dashboards.
