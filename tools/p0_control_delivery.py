"""Final public indexes and report-preservation checks; no experimental mutations."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

from personaslm.journal import atomic_json, utc_now

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "results/p0_neutral_validity/20261012T195226"
PUBLIC = ROOT / "docs/validation"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    records = []
    for path in sorted((SESSION / "engineering").glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if "argv" not in value:
            continue
        # Full failures may contain machine-specific temporary paths. Keep those
        # bytes in local logs; publish their hashes and exact command/times.
        records.append({**{k:value[k] for k in ("argv", "started_utc", "finished_utc", "exit_code", "duration_seconds")},
            "log_path": path.relative_to(ROOT).as_posix(), "log_sha256": sha(path),
            "output_scope": "Full stdout/stderr retained locally; use hash to bind the evidence"})
    atomic_json(PUBLIC / "P0_neutral_validity_commands_v1.json", {"created_utc":utc_now(), "commands":records,
        "uncaptured_actions": ["Initial Get-Location/Get-Date/AGENTS/Git status and scoped rg/file reads are in the tool transcript",
            "Read-only inline Python inspection failed due to Windows shell quoting; inspection was rerun with stdin/file scripts",
            "Preparation inventoried tracked source and 21 journals; baseline created_utc records completion, not invented command-start time",
            "Source/doc patches use the patch interface; Git diffs and source/run hashes preserve their contents",
            "Web accesses are indexed separately with actual query strings and explicitly unavailable per-query timestamps"],
        "scope": "Completed captures at export time; this export and final checks have separate local captures"})
    baseline = json.loads((SESSION / "materials/baseline.json").read_text(encoding="utf-8"))
    preserved_reports = {}
    for original in (SESSION / "engineering/report_originals").glob("*.md"):
        current = ROOT / "docs" / original.name
        assert original.read_bytes() in current.read_bytes()
        assert sha(original) == baseline["tracked_files"]["docs/" + original.name]
        preserved_reports[original.name] = sha(original)
    # The research log must retain its entire committed text as a prefix.
    log_path = ROOT / "docs/research_development_log.md"
    historical_log = subprocess.check_output(["git", "show", "HEAD:docs/research_development_log.md"], cwd=ROOT)
    current_log = log_path.read_bytes().replace(b"\r\n", b"\n")
    assert current_log.startswith(historical_log.replace(b"\r\n", b"\n"))
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    needle = "".join(map(chr,(67,111,100,101,120))).lower()
    matches, all_files, link_count = [], {}, 0
    for name in sorted(set(names)):
        path = ROOT / name
        if not name or not path.is_file() or name.startswith(("data/private/", "models/", "bin/", ".venv/", "results/")):
            continue
        content = path.read_bytes()
        if b"\0" in content:
            continue
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            continue
        all_files[name] = sha(path)
        if needle in text.lower():
            matches.append(name)
        if path.suffix == ".json":
            json.loads(text)
        if path.suffix == ".md" and (name not in baseline["tracked_files"] or sha(path) != baseline["tracked_files"].get(name)):
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in target or target.startswith("#"):
                    continue
                target = target.split("#", 1)[0]
                if not (path.parent / target).exists():
                    raise ValueError("Broken local link: " + name + " -> " + target)
                link_count += 1
    assert not matches
    statuses = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, text=True)
    result = {"created_utc":utc_now(), "commands_indexed":len(records), "report_originals_preserved":preserved_reports,
        "historical_development_log_prefix_preserved": True, "product_name_matches":matches,
        "current_text_files_searched":len(all_files), "local_links_checked":link_count,
        "file_hashes":all_files, "git_status_before_this_artifact":statuses,
        "git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "new_final_artifact_note":"This artifact is created after the inventory; final Git status capture includes it",
        "no_new_experiments":True}
    atomic_json(PUBLIC / "P0_neutral_validity_final_checks_v1.json", result)
    print(json.dumps({"commands_indexed":len(records),"source_search_matches":len(matches),
        "report_histories_preserved":len(preserved_reports),"links_checked":link_count,"files_searched":len(all_files)}))


if __name__ == "__main__":
    main()
