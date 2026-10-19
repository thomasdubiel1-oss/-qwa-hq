# QWA Build Status

Completed: permission model, agent routing, audit schema/writer, production approval contract, unit tests, CI, Hermes MCP boundary, filtered-server plan, QWA MCP tool catalog, policy-first dispatcher, development approval store, provider-neutral GitHub/knowledge/staging adapters, replay protection, request/trace context, metrics foundation, durable SQLite approvals, managed PostgreSQL approval repository, and authenticated operator approval surface.

## Current architecture

Phone / WhatsApp -> Hermes -> QWA policy router -> MCP tool boundary -> provider adapters -> GitHub / staging / knowledge / production.
For production mutation requests, the approval plane is: QWA MCP -> durable approval repository -> authenticated operator API -> audit event. Approval remains distinct from execution.

## Current safety guarantees

- Production mutation requests cannot execute directly.
- Approval records have immutable request identity and a request hash.
- Approval decisions are one-way: pending -> approved/rejected.
- PostgreSQL decisions use row-level locking inside a transaction.
- Replayed request IDs are served from idempotency storage.
- Provider integrations remain behind narrow gateway protocols.
- Operator decisions require a bearer token and are auditable.
- Tests use fakes/dry-run adapters and do not require production credentials.
- Local approval databases are ignored by Git.

## Next

1. Bind approved Render service aliases and add deploy-state polling.
2. Connect the production approval API to an identity-aware proxy and managed Postgres in staging.
3. Add production execution only through an approved request token and replay-safe transaction.
4. Add cost budgets, rate limits, and evaluation/observability dashboards.
