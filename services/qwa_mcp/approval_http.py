"""Authenticated operator approval HTTP surface.

This deliberately exposes only approval inspection and one-way decisions.
It is intended to sit behind TLS and network access controls in deployment.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .durable_approval_store import SQLiteApprovalStore


class ApprovalAPI:
    def __init__(self, store, *, token: str | None = None, audit=None):
        self.store = store
        self.token = token or os.environ.get("QWA_APPROVAL_TOKEN")
        if not self.token:
            raise ValueError("QWA_APPROVAL_TOKEN is required")
        self.audit = audit

    def authenticate(self, authorization: str | None) -> bool:
        return authorization == f"Bearer {self.token}"

    def get(self, request_id: str):
        record = self.store.get(request_id)
        if record is None:
            return 404, {"error": "not_found"}
        return 200, self._public(record)

    def decide(self, request_id: str, status: str, approver: str, reason: str | None = None):
        record = self.store.decide(request_id, status, approver, reason)
        if self.audit:
            self.audit(
                actor=approver,
                action=f"approval.{status}",
                resource=record.tool,
                decision=status,
                request_id=record.request_id,
                reason=reason or "",
            )
        return 200, self._public(record)

    @staticmethod
    def _public(record):
        return {
            "request_id": record.request_id,
            "actor": record.actor,
            "tool": record.tool,
            "status": record.status,
            "approver": record.approver,
            "reason": record.reason,
            "created_at": record.created_at,
            "decided_at": record.decided_at,
        }


def make_handler(api: ApprovalAPI):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status, payload):
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _auth(self):
            if not api.authenticate(self.headers.get("Authorization")):
                self._send(401, {"error": "unauthorized"})
                return False
            return True

        def do_GET(self):
            if not self._auth():
                return
            parts = [p for p in urlparse(self.path).path.split("/") if p]
            if len(parts) == 2 and parts[0] == "approvals":
                status, body = api.get(parts[1])
                self._send(status, body)
                return
            self._send(404, {"error": "not_found"})

        def do_POST(self):
            if not self._auth():
                return
            parts = [p for p in urlparse(self.path).path.split("/") if p]
            if len(parts) != 3 or parts[0] != "approvals" or parts[2] not in {"approve", "reject"}:
                self._send(404, {"error": "not_found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length) or b"{}")
                approver = payload["approver"]
                reason = payload.get("reason")
                status, body = api.decide(parts[1], "approved" if parts[2] == "approve" else "rejected",
                                          approver, reason)
                self._send(status, body)
            except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                self._send(400, {"error": str(exc)})

        def log_message(self, format, *args):
            return

    return Handler


def serve(api: ApprovalAPI, host="127.0.0.1", port=8787):
    return ThreadingHTTPServer((host, port), make_handler(api))
