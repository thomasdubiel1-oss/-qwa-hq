# QWA Build Status

Completed: permission model, agent routing, audit schema/writer, production approval contract, unit tests, CI, Hermes MCP boundary, filtered-server plan, QWA MCP tool catalog, policy-first dispatcher, development approval store, Hermes WhatsApp self-chat operator configuration, provider-neutral GitHub adapter boundary, and scoped knowledge/Obsidian adapter.

## Current architecture

Phone / WhatsApp -> Hermes -> QWA policy router -> MCP tool boundary -> adapters -> GitHub / staging / knowledge / production.

The GitHub adapter is provider-neutral: the runtime connector is injected through a gateway protocol, keeping repository code independent of ChatGPT's connector implementation. The knowledge adapter is a local, path-scoped implementation suitable for an Obsidian vault or equivalent knowledge directory.

## Safety state

- Production mutations remain approval-gated.
- No production credentials are stored in this repository.
- Adapter tests use fakes/local temporary directories only.
- No external side effect is executed by the unit-test suite.

## Next

1. Wire adapter registry into QWAMCPServer.
2. Add replay-safe request IDs and metrics.
3. Replace development JSONL approvals with durable storage and an operator approval surface.
4. Add staging adapter implementation.
5. Pair Hermes to WhatsApp on the operator machine using the self-chat flow.
