import tempfile
from pathlib import Path

import pytest

from .durable_approval_store import ApprovalRecord, SQLiteApprovalStore, request_hash


def test_sqlite_approval_survives_reopen():
    path = Path(tempfile.mkdtemp()) / "approvals.sqlite3"
    store = SQLiteApprovalStore(str(path))
    record = ApprovalRecord("r1", "hermes", "request_change", request_hash("request_change", "hermes", {"x": 1}), "pending")
    store.create(record)

    reopened = SQLiteApprovalStore(str(path))
    assert reopened.get("r1").status == "pending"


def test_approval_can_be_decided_once():
    path = Path(tempfile.mkdtemp()) / "approvals.sqlite3"
    store = SQLiteApprovalStore(str(path))
    store.create(ApprovalRecord("r1", "hermes", "request_change", "hash1", "pending"))

    approved = store.decide("r1", "approved", "operator", "reviewed")
    assert approved.status == "approved"
    assert approved.approver == "operator"

    with pytest.raises(ValueError):
        store.decide("r1", "rejected", "operator")


def test_duplicate_request_id_does_not_create_second_record():
    path = Path(tempfile.mkdtemp()) / "approvals.sqlite3"
    store = SQLiteApprovalStore(str(path))
    record = ApprovalRecord("r1", "hermes", "request_change", "hash1", "pending")
    store.create(record)
    store.create(record)
    assert store.get("r1").request_id == "r1"
