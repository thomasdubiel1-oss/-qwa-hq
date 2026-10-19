# QWA Build Status

Completed: permission model, agent routing, audit schema/writer, production approval contract, unit tests, CI, Hermes MCP boundary, filtered-server plan, QWA MCP tool catalog, policy-first dispatcher, development approval store, and Hermes WhatsApp self-chat operator configuration.

## Current architecture

Phone / WhatsApp -> Hermes -> QWA policy router -> MCP tool boundary -> specialized QWA adapters -> GitHub / staging / knowledge / production.

The MCP dispatcher currently performs validation and authorization but deliberately does not execute external side effects until adapters are wired and tested.

## Next

1. Implement GitHub/CI adapter against the connected GitHub service.
2. Implement staging adapter with deployment/status/log contracts.
3. Implement scoped Obsidian/knowledge adapter.
4. Replace development JSONL approvals with durable storage and an operator approval surface.
5. Add metrics, cost controls, replay-safe request IDs, and agent evaluation.
6. Pair Hermes to WhatsApp on the operator machine using the self-chat flow.
