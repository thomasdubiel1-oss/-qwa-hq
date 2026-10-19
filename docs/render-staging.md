# Render staging deployment control

QWA treats Render as a provider behind an allowlisted staging adapter.

## Lifecycle

1. Resolve a logical QWA service alias through `ServiceRegistry`.
2. Require `environment=staging` and `provider=render`.
3. Require an exact 40-character Git commit SHA at the adapter boundary.
4. Trigger the Render deploy against the bound service resource.
5. Capture the Render deploy ID together with QWA request/trace context.
6. Poll the specific deploy until `live` or a terminal failure state.
7. Query logs only through the binding's Render workspace `owner_id`.

Render supports deploying a specific Git commit with `commitId`; the deploy response includes a deploy ID and lifecycle status, and a specific deploy can be retrieved by service ID and deploy ID. Log queries require the workspace owner ID and are timestamp-paginated. citeturn0search0turn0search3turn0search1

## Security boundary

- Callers provide only an approved logical service alias, never an arbitrary Render resource target.
- Production services are rejected by the registry.
- Render credentials stay outside Git and are read only by the gateway process.
- Unknown providers, services, invalid revisions, and missing log owner IDs fail closed.
- This layer does not trigger production deployments.

## Persistence

Deployment persistence is implemented in `services/qwa_mcp/deployment_store.py`.

Each staging deployment records request ID, trace ID, service alias, bound resource ID, revision, Render deploy ID, and lifecycle status. Records are idempotent by request ID and immutable across deployment identity fields, preventing a reused request ID from silently targeting a different revision or deploy.

Status reads and bounded wait operations can update the persisted lifecycle by Render deploy ID, allowing later status checks and audit tooling to reconstruct deployment state.
