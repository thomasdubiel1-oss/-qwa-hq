# Render staging adapter

QWA now has a provider-neutral staging contract plus a concrete Render HTTP gateway.
The gateway uses Render's REST API and requires RENDER_API_KEY; the key must never
be committed to Git.

## Safety boundary

- deploy_staging remains governed by the QWA MCP catalog and staging level.
- The Render gateway is not automatically instantiated by the dispatcher.
- Tests mock HTTP and never contact Render.
- Production credentials are not stored in the repository.
- A real Render workspace/service must be selected before deployment is enabled.

## Planned wiring

QWAMCPServer -> StagingAdapter -> RenderGateway -> Render API

The next deployment layer should bind service aliases to approved Render service
IDs, record request ID and revision, wait for deploy state, and fail closed on
unknown services.
