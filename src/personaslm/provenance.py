"""Immutable-by-key, project-local JSONL results and provenance."""
import hashlib
import json
import os
from pathlib import Path


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def is_within_root(path: Path, root: Path | None = None) -> bool:
    root = (root or repository_root()).resolve()
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False


def require_local_path(path: Path, root: Path | None = None) -> Path:
    root = (root or repository_root()).resolve()
    path = Path(os.path.abspath(path if path.is_absolute() else root / path))
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
            raise ValueError(f"Symlink/junction file access refused: {part}")
    path = path.resolve()
    if not is_within_root(path, root):
        raise ValueError(f"Out-of-project file access refused: {path}")
    return path


def audit_local_paths(root: Path | None = None) -> dict:
    """Best-effort symlink/junction check; not an OS-level access guarantee."""
    root = (root or repository_root()).resolve()
    bad = []
    unreadable = []
    def on_error(error):
        unreadable.append({"path": str(error.filename), "error": str(error)})
    for current, directories, files in os.walk(root, followlinks=False, onerror=on_error):
        for name in directories + files:
            entry = Path(current) / name
            is_junction = getattr(entry, "is_junction", lambda: False)()
            if entry.is_symlink() or is_junction:
                bad.append(str(entry.relative_to(root)))
    return {"root": str(root), "links_or_junctions": bad, "unreadable_paths": unreadable,
            "passed": not bad and not unreadable,
            "status": "BLOCKED" if bad else ("PARTIAL" if unreadable else "PASS"),
            "limitation": "Path audit does not prove absence of arbitrary external file access; use OS permissions for strict isolation."}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(obj: object) -> str:
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def append_unique_atomic(path: Path, record: dict, *, record_key: str = "record_id") -> bool:
    """Safe atomic replace for small P0 runs; not a scalable concurrent logger."""
    path = require_local_path(path)
    if record_key not in record:
        raise ValueError(f"Missing {record_key}")
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    for line in lines:
        if json.loads(line).get(record_key) == record[record_key]:
            return False
    lines.append(json.dumps(record, ensure_ascii=False, sort_keys=True))
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return True
