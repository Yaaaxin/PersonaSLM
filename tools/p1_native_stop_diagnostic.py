"""Additive, offline compatibility diagnostic; never rewrite a frozen score."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from personaslm.journal import atomic_json
from personaslm.response_status import classify_response

VERSION = "p1_native_stop_compatibility_diagnostic_v1"
PUBLIC = Path("docs/validation/p1")
RUN = Path("results/p1_wave1/development_v1/runs/20261013T065228-971f93c4c1434254a5298dde72dd9061")


def diagnose(raw, backend):
    """Test the native eos/eog spelling discrepancy without certifying semantics."""
    native = deepcopy(backend)
    diagnostic = deepcopy(backend)
    mapped = diagnostic.get("stop_type") == "eos"
    if mapped:
        diagnostic["stop_type"] = "eog"
    original = classify_response(raw, native)
    alternative = classify_response(raw, diagnostic)
    return {"version": VERSION, "original": original, "diagnostic": alternative,
            "native_eos_alias_mapped": mapped, "human_completeness_supplied": False,
            "replacement_score": None, "original_backend": native}


def main():
    source = PUBLIC / "wave1_results_v1.json"
    rows = json.loads(source.read_text(encoding="utf-8"))["rows"]
    log = RUN / "server.log"
    lines = log.read_text(encoding="utf-8", errors="strict").splitlines()
    evidence = [{"line": i + 1, "text": line} for i, line in enumerate(lines)
                if "248044" in line and ("EOS token" in line or "EOG token" in line)]
    assert evidence, "Saved backend EOS identity evidence missing"
    records = []
    for row in rows:
        item = diagnose(row["raw_response"], row["raw_termination"])
        assert item["original"] == row["evaluation"]["response_completeness"]
        tokens = row["generated_token_ids"]
        if item["native_eos_alias_mapped"]:
            assert tokens and tokens[-1] == 248044
        item.update(request_id=row["request_id"], generated_tokens=row["generated_tokens"],
                    terminal_output_token_id=tokens[-1] if tokens else None)
        records.append(item)
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    output = {"version": VERSION, "created_utc": datetime.now(timezone.utc).isoformat(),
              "source_sha256": digest(source), "server_log_sha256": digest(log),
              "policy_sha256": digest(Path("src/personaslm/response_status.py")),
              "diagnostic_source_sha256": digest(Path(__file__)),
              "native_eos_identity_evidence": evidence, "rows": records,
              "original_status_counts": dict(Counter(r["original"]["status"] for r in records)),
              "diagnostic_status_counts": dict(Counter(r["diagnostic"]["status"] for r in records)),
              "native_eos_aliases": sum(r["native_eos_alias_mapped"] for r in records),
              "new_generation_requests": 0, "original_scores_changed": False,
              "limitation": "EOS is a native termination boundary, not independent semantic completeness. This diagnostic does not adopt a new response policy."}
    atomic_json(PUBLIC / "native_stop_compatibility_diagnostic_v1.json", output)
    print(json.dumps({k: v for k, v in output.items() if k not in ("rows", "native_eos_identity_evidence")}))


if __name__ == "__main__":
    main()
