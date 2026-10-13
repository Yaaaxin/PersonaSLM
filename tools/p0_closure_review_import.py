"""Import actual History A confirmations; never update the original decisions."""
import argparse
from collections import Counter
import json
from pathlib import Path

from personaslm.control_closure import validate_confirmations
from personaslm.control_decisions import read_csv
from personaslm.journal import atomic_json, utc_now
from personaslm.provenance import require_local_path, sha256


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--corrections", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence, corrections, output = map(require_local_path, (args.evidence, args.corrections, args.output))
    if output.exists():
        raise FileExistsError("Never overwrite confirmations")
    root = Path(__file__).resolve().parents[1] / "docs/validation"
    records = {}
    for name, path, master, key, judgment, allowed in (
        ("evidence", evidence, root / "P0_history_a_evidence_v1.csv", "evidence_id", "researcher_confirmation", {"CONFIRM", "REJECT", "UNCERTAIN"}),
        ("corrections", corrections, root / "P0_closure_correction_form_v1.csv", "candidate_id", "researcher_value", {"PASS", "FAIL", "UNCERTAIN"}),
    ):
        fields, rows = read_csv(path)
        original_fields, expected = read_csv(master)
        if fields != original_fields:
            raise ValueError("Official confirmation columns changed")
        validate_confirmations(expected, rows, key=key, judgment=judgment, allowed=allowed)
        records[name] = {"source_sha256": sha256(path), "master_sha256": sha256(master), "rows": rows,
                         "label_counts": dict(Counter(r[judgment] for r in rows))}
    result = {"version": "p0_closure_history_confirmation_v1", "imported_utc": utc_now(), **records,
              "interpretation": "Actual supplied confirmations; evidence association is not a new semantic rating; original ACCEPT_NARROW and original axis judgments remain unchanged",
              "acceptance": "Not automatic. Retain any rejected/uncertain associations or ratings and review the adopted-control scope.",
              "review_time_note": "Blank human review times stay blank; import time is distinct",
              "identity_limit": "Supplied identifier, not authenticated by software"}
    output.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(output, result)
    print(json.dumps({name: value["label_counts"] for name, value in records.items()}))


if __name__ == "__main__":
    main()
