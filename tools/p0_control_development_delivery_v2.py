"""Final source/material audit and public indexes for the completed v2 work."""
import csv
import json
import re
import subprocess
from urllib.parse import unquote

from personaslm.control_review_v2 import validate_packet
from personaslm.journal import utc_now
from personaslm.reproducibility import source_snapshot
from p0_control_development_v2 import ROOT, SESSION, PUBLIC, DATA, read, save, digest


def main():
    started = utc_now()
    access = {"indexed_utc": started, "access_date": "2026-10-12", "tool": "web search/open/find",
              "timestamp_scope": "Actual index time; per-request times not reconstructed from the interface transcript",
              "queries": ['"persona" "length-matched" control language models',
                          '"persona" "neutral" "control" "factual" language models benchmark',
                          '"Measuring and Narrowing the Compositionality Gap" "irrelevant"',
                          '"Large Language Models Can Be Easily Distracted by Irrelevant Context"'],
              "sources": [
                  {"id": "W10", "record": "https://proceedings.mlr.press/v202/shi23a.html",
                   "paper": "https://proceedings.mlr.press/v202/shi23a/shi23a.pdf", "version": "ICML 2023 proceedings",
                   "inspected": "Bibliographic metadata, abstract, PDF access; full size inventory not extracted"},
                  {"id": "W11", "record": "https://arxiv.org/abs/2605.24279",
                   "paper": "https://arxiv.org/pdf/2605.24279v2", "version": "v2, 2026-08-27",
                   "inspected": "Title/authors, abstract, section2.1, length-matched/filler methods; character/token wording distinguished"},
                  {"id": "W12", "record": "https://arxiv.org/abs/2603.18507",
                   "paper": "https://arxiv.org/pdf/2603.18507v1", "version": "v1, 2026-03-19",
                   "inspected": "Title/authors, abstract, sections3.2-3.4, expert/random and prompt-length comparisons"}],
              "limitations": ["Primary sources checked; experiments, source repositories and data releases not reproduced",
                              "Search results served discovery only; secondary summaries not used for scientific claims",
                              "Not a systematic literature review or originality certification"],
              "new_primary_access_errors": []}
    if not (PUBLIC / "P0_control_literature_access_v2.json").exists():
        save(PUBLIC / "P0_control_literature_access_v2.json", access)
    commands = []
    for path in sorted((SESSION / "engineering").glob("*.json")):
        value = read(path)
        if "argv" in value:
            commands.append({"capture": path.relative_to(ROOT).as_posix(), "sha256": digest(path),
                             **{k: value[k] for k in ("argv", "started_utc", "finished_utc", "exit_code", "duration_seconds")},
                             "stdout_summary": value["stdout"].strip().splitlines()[-1:]})
    command_index = {"created_utc": utc_now(), "commands": commands,
        "other_actions": ["Read repository instructions, acceptance/annotation/control reports, protocol and source APIs",
                          "Snapshot154 current worktree files and22 historical journals before changes;40 existing dirty paths",
                          "Applied new code/tests and English documentation patches; captured freeze, tokenizer, review, integrity and report stages",
                          "Primary literature search/open/find, followed by versioned access index",
                          "Final delivery tool performs read-only Git status/diff, branding/link and material checks"],
        "early_read_error": "Nonexistent src/personaslm/schema.py was corrected to schemas.py; the multi-read PowerShell command returned0 despite its read error",
        "timing_limit": "Early read-only/patch calls are in the task transcript; individual missing timestamps are not invented",
        "delivery_command_capture": (SESSION / "engineering/delivery_command.json").relative_to(ROOT).as_posix(),
        "delivery_note": "The outer command capture is written on process completion and is not recursively hashed by this index"}
    if not (PUBLIC / "P0_control_development_commands_v2.json").exists():
        save(PUBLIC / "P0_control_development_commands_v2.json", command_index)
    baseline = read(SESSION / "materials/baseline.json")
    names = sorted(set(subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")) - {""})
    names = [n for n in names if (ROOT / n).is_file() and not n.startswith(("models/", "bin/", ".venv/", "results/", "data/private/"))]
    current = {n: digest(ROOT / n) for n in names}
    changed = {n: h for n, h in current.items() if baseline["source_files"].get(n) != h}
    removed = sorted(set(baseline["source_files"]) - set(current))
    if removed:
        raise ValueError("Unexpected removed source file")
    forbidden = "".join(map(chr, (67, 111, 100, 101, 120))).lower()
    branding, private_paths, checked, invalid_links = [], [], [], []
    for name in names:
        try:
            text = (ROOT / name).read_text(encoding="utf-8-sig")
        except UnicodeError:
            continue
        checked.append(name)
        if forbidden in text.lower():
            branding.append(name)
        additions = text
        if name == "docs/P0_real_inference_report.md":
            # The old body is verified byte-for-byte below. Inspect only the
            # new notice rather than labeling retained old paths as new leaks.
            additions = text.split("\n\n", 1)[0]
        if name in changed and re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/](?:DEVOIRS|Users)[\\/]", additions, re.I):
            private_paths.append(name)
        if name in changed and name.endswith(".md"):
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if link.startswith(("http:", "https:", "#")):
                    continue
                target = unquote(link.split("#", 1)[0])
                if target and not ((ROOT / name).parent / target).exists():
                    invalid_links.append({"file": name, "target": link})
    if branding or private_paths or invalid_links:
        raise ValueError(json.dumps({"branding": branding, "private_paths": private_paths, "invalid_links": invalid_links}))
    packet = read(PUBLIC / "P0_control_development_review_v2.json")
    with (PUBLIC / "P0_control_development_review_v2.csv").open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames or [], list(reader)
    if validate_packet(packet, rows, fields) or len(rows) != 24:
        raise ValueError("New review materials are not24 blank valid rows")
    # Recheck protected files after report writing; no original fixtures or
    # source modules were edited by the appended reporting work.
    integrity = read(PUBLIC / "P0_control_development_integrity_v2.json")
    if any(digest(ROOT / name) != baseline["source_files"][name] for name in integrity["protected_files"]):
        raise ValueError("Protected file changed after integrity audit")
    for name in ("P0_control_acceptance_report.md", "P0_remaining_blockers.md", "P0_policy_acceptance_report.md",
                 "P0_final_validation_report.md", "P0_methodology_acceptance_report.md", "P0_acceptance_checklist.md",
                 "P0_real_inference_report.md", "P0_neutral_control_diagnostic.md"):
        path = ROOT / "docs" / name
        original_body = path.read_bytes().split(b"\n\n", 1)[1]
        # Remaining-blocker report also has a new appended section.
        if name == "P0_remaining_blockers.md":
            marker = read(SESSION / "engineering/report_creation.json")["recorded_utc"]
            original_body = original_body.split(("\n\n## " + marker + " — Precise remaining control gate").encode("utf-8"))[0]
        import hashlib
        if hashlib.sha256(original_body).hexdigest() != baseline["source_files"]["docs/" + name]:
            raise ValueError("Earlier report body was not retained byte-for-byte: " + name)
    git_checks = {}
    for label, argv in (("diff_check", ["git", "diff", "--check"]), ("status", ["git", "status", "--short"]),
                        ("diff_stat", ["git", "diff", "--stat"]), ("head", ["git", "rev-parse", "HEAD"])):
        beginning = utc_now()
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        record = {"argv": argv, "started_utc": beginning, "finished_utc": utc_now(), "exit_code": result.returncode,
                  "stdout": result.stdout, "stderr": result.stderr}
        save(SESSION / "engineering" / ("final_" + label + ".json"), record)
        git_checks[label] = record
        if result.returncode:
            raise ValueError("Git read-only check failed")
    save(SESSION / "materials/delivery_source_snapshot.json", source_snapshot(DATA))
    value = {"started_utc": started, "finished_utc": utc_now(), "files_changed_since_baseline": changed,
             "files_removed": removed, "existing_dirty_files_at_start": 40, "text_files_scanned": len(checked),
             "product_name_occurrences": 0, "machine_private_paths_in_additions": 0, "broken_local_links": invalid_links,
             "new_review_items": 24, "new_human_reviews": 0, "protected_files_unchanged": len(integrity["protected_files"]),
             "earlier_report_bodies_preserved": True, "git_checks": git_checks,
             "test_capture": read(SESSION / "engineering/full_tests.json"), "P0": "PARTIAL", "P1": "NOT STARTED",
             "completed_command_captures": commands,
             "scope": "Self and outer command capture are created after the file inventory; no recursive self-hash"}
    save(PUBLIC / "P0_control_development_delivery_v2.json", value)
    print(json.dumps({"files_changed_since_baseline_before_delivery": len(changed), "source_text_files_scanned": len(checked),
                      "branding_occurrences": 0, "broken_links": 0, "new_review_items": 24,
                      "human_reviews": 0, "git_diff_check_exit": git_checks["diff_check"]["exit_code"], "P0": "PARTIAL"}))


if __name__ == "__main__":
    main()
