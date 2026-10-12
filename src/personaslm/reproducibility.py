"""Read-only Git state and exact input snapshots for new P0 runs."""
import subprocess

from .provenance import repository_root, sha256


def source_snapshot(cases_path):
    root = repository_root()
    sources = sorted((root / "src/personaslm").glob("*.py"))
    tools = sorted((root / "tools").glob("p0_*.py"))
    git = {}
    for key, command in (("commit", ["git", "rev-parse", "HEAD"]),
                         ("status_porcelain", ["git", "status", "--porcelain=v1"])):
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=15)
            git[key] = result.stdout.rstrip() if result.returncode == 0 else None
            if result.returncode:
                git[key + "_error"] = result.stderr.strip()
        except (OSError, subprocess.TimeoutExpired) as exc:
            git[key] = None
            git[key + "_error"] = str(exc)
    git["dirty"] = bool(git["status_porcelain"]) if git["status_porcelain"] is not None else None
    return {"git": git, "dataset_utf8": cases_path.read_bytes().decode("utf-8"),
            "source_utf8": {p.name: p.read_bytes().decode("utf-8") for p in sources},
            "source_sha256": {p.name: sha256(p) for p in sources},
            "tool_source_utf8": {p.relative_to(root).as_posix(): p.read_bytes().decode("utf-8") for p in tools},
            "tool_sha256": {p.relative_to(root).as_posix(): sha256(p) for p in tools},
            "evaluation_rules": "judge_current_city in saved evaluation.py; synthetic current-city only",
            "determinism_limit": "Same seed specifies input; it does not guarantee identical model output."}
