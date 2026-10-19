# Hermes to WhatsApp

QWA supports Hermes as the WhatsApp control channel. For the initial single-user setup, use Hermes' self-chat mode so no new business number is required.

## Pair the account

On the machine running Hermes:

    hermes whatsapp

Select self-chat, then scan the QR code from WhatsApp on the phone:

    WhatsApp -> Settings -> Linked Devices -> Link a Device

Hermes stores the paired session locally. Keep the session directory private because it contains authentication credentials.

## Recommended private configuration

Set in ~/.hermes/.env:

    WHATSAPP_ENABLED=true
    WHATSAPP_MODE=self-chat
    WHATSAPP_ALLOWED_USERS=<your WhatsApp number without +, spaces, or dashes>

Keep an explicit allowlist rather than allowing all senders.

In ~/.hermes/config.yaml:

    whatsapp:
      unauthorized_dm_behavior: ignore
      reply_prefix: ""
      send_read_receipts: false

Then start Hermes:

    hermes gateway

For a persistent user service, use hermes gateway install after verifying the pairing.

## QWA safety boundary

WhatsApp is a user interface, not a privilege escalation path. Messages from WhatsApp must still pass through the QWA policy router and MCP tool allowlists. Production mutations remain approval-gated and audited.

## Production path

For a customer-facing/business bot, migrate to the official Meta WhatsApp Cloud API instead of the personal-account bridge. That requires a Meta Business setup and public HTTPS webhook. The self-chat path is intended for your private operator workflow.
