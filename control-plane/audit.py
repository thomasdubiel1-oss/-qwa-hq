"""Append-only JSONL audit writer. Never pass secrets to it."""
import json
from datetime import datetime, timezone
from pathlib import Path

def record(path: str, *, actor: str, action: str, resource: str, decision: str, request_id: str, reason: str = "") -> None:
    event={"timestamp":datetime.now(timezone.utc).isoformat(),"actor":actor,"action":action,"resource":resource,"decision":decision,"request_id":request_id,"reason":reason}
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("a",encoding="utf-8") as f: f.write(json.dumps(event,separators=(",",":"))+"\n")
