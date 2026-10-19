# QWA Approval Plane

The approval plane is the human-control boundary for production mutations.

## Components

- **SQLiteApprovalStore** — local durable implementation for development/staging.
- **PostgresApprovalStore** — managed PostgreSQL implementation for multi-process production use.
- **ApprovalAPI** — authenticated operator surface for inspecting and deciding approvals.
- **QWAMCPServer** — creates approval records and never treats an approval as execution.

PostgreSQL decisions lock the target row with `SELECT ... FOR UPDATE` inside the transaction so concurrent operators cannot both transition a pending request. PostgreSQL documents that row locks block conflicting writers/lockers until the transaction ends.

## Authentication

The HTTP surface requires `Authorization: Bearer <QWA_APPROVAL_TOKEN>`. The token must come from a secret manager/environment variable; never commit it.

The reference HTTP server binds to localhost by default. A production deployment should put it behind TLS, network access controls, rate limiting, and an identity-aware reverse proxy. The API intentionally exposes only:

- `GET /approvals/{request_id}`
- `POST /approvals/{request_id}/approve`
- `POST /approvals/{request_id}/reject`

An approval decision is recorded, audited, and remains separate from execution.

## Database

Set `DATABASE_URL` for the managed PostgreSQL repository. The schema is created idempotently at startup. For a production migration system, move schema creation into versioned migrations before broad rollout.

Render provides managed PostgreSQL and a REST API for infrastructure management; database credentials/API keys must remain secret and outside source control.

## Render deployment polling

Render exposes programmatic service deploys and logs. The next adapter layer should poll deploy state by approved service binding and use the provider's log pagination rather than treating a single log request as complete.
