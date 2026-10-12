"""Single-writer P0 journal: immutable manifest and atomic, fsynced event files."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid

from .provenance import fingerprint, require_local_path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: dict) -> None:
    path = require_local_path(path)
    if path.exists():
        raise FileExistsError(f"Immutable artifact already exists: {path}")
    temp = path.with_name(path.name + ".tmp")
    with temp.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


class RunJournal:
    def __init__(self, output_root: Path, manifest: dict):
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex
        self.directory = require_local_path(output_root) / self.run_id
        self.directory.mkdir(parents=True, exist_ok=False)
        (self.directory / "events").mkdir()
        self.sequence = 0
        frozen = {**manifest, "run_id": self.run_id, "created_utc": utc_now(), "journal_version": 1}
        self.previous_hash = fingerprint(frozen)
        atomic_json(self.directory / "manifest.json", frozen)

    def write(self, kind: str, data: dict):
        sequence = self.sequence + 1
        event = {"sequence": sequence, "kind": kind, "created_utc": utc_now(),
                 "previous_hash": self.previous_hash, "data": data}
        event_hash = fingerprint(event)
        atomic_json(self.directory / "events" / f"{sequence:06d}.json", {**event, "event_hash": event_hash})
        self.sequence = sequence
        self.previous_hash = event_hash

    def finish(self, status: str, **details):
        self.write("run_finished", {"status": status, **details})


def read_events(directory: Path) -> list[dict]:
    """Read completed files; detect tampering/gaps. A missing finish means interrupted."""
    directory = require_local_path(directory)
    manifest_path = require_local_path(directory / "manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("journal_version") != 1 or not (directory / "events").is_dir():
        raise ValueError("Unsupported or incomplete run journal")
    previous = fingerprint(manifest)
    events = []
    for index, path in enumerate(sorted((directory / "events").glob("*.json")), 1):
        path = require_local_path(path)
        event = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(event, dict):
            raise ValueError(f"Malformed journal event: {path.name}")
        digest = event.pop("event_hash", None)
        if event.get("sequence") != index or event.get("previous_hash") != previous or fingerprint(event) != digest:
            raise ValueError(f"Journal integrity failure: {path.name}")
        event["event_hash"] = digest
        events.append(event)
        previous = digest
    return events
