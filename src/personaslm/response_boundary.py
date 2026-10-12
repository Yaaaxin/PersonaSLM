"""Versioned single-turn diagnostics; never changes the historical parser."""
import re
from types import SimpleNamespace

from .conditioning import build_prompt
from .run_audit import text_hash

VERSION = "single_turn_boundary_v1"
SENTINEL = "<END_OF_REPLY>"
VARIANTS = {
    "T0": {"prompt_version": "transcript_base_v1", "stop": []},
    "T1": {"prompt_version": "transcript_base_v1", "stop": ["\nUser:", "\nAssistant:"]},
    "T2": {"prompt_version": "explicit_end_reply_v1", "stop": []},
    "T3": {"prompt_version": "explicit_end_reply_v1", "stop": ["\n<END_OF_REPLY>"]},
}


def prompt_for(case, variant):
    item = SimpleNamespace(**case, style_only="", supplemental_fact="", history_dialogue="")
    original = build_prompt(item, "C0").text
    if VARIANTS[variant]["prompt_version"] == "transcript_base_v1":
        return original
    return ("Write exactly one assistant reply to the last user question. Preserve any requested line breaks. "
            "After the complete reply, write <END_OF_REPLY> on a new line. "
            "Do not invent another conversation turn. The end marker is a formatting delimiter, not part of the answer.\n\n"
            + original)


def boundary_audit(raw, native, case, variant):
    """Return body plus exact offsets/tail; uncertainty never silently becomes success."""
    settings = VARIANTS[variant]
    explicit = settings["prompt_version"] == "explicit_end_reply_v1"
    markers = ["\n"+SENTINEL] if explicit else ["\nUser:", "\nAssistant:"]
    candidates = [(raw.find(marker), marker) for marker in markers if marker in raw]
    visible = min(candidates) if candidates else None
    material = case["trusted_evidence"] + "\n" + case["question"]
    collision = any(marker in material for marker in markers)
    stop_type = native.get("stop_type")
    stopping_word = native.get("stopping_word")
    acknowledged = stop_type == "word" and stopping_word in settings["stop"]
    eos = stop_type in ("eos", "eog") or native.get("stopped_eos") is True
    offset = visible[0] if visible else len(raw)
    body = raw[:offset].strip()
    role_labels = re.findall(r"(?m)^(?:User|Assistant):", body)
    unexpected_roles = bool(role_labels) and not case["literal_role_text_allowed"]
    established = bool(visible or acknowledged or eos)
    issues = []
    if collision:
        issues.append("reserved_delimiter_occurs_in_requested_content")
    if not established:
        issues.append("no_turn_end_observed_before_budget_or_unknown_stop")
    if not body:
        issues.append("empty_reply")
    if unexpected_roles:
        issues.append("additional_role_turn_inside_reply")
    if stop_type == "word" and not acknowledged:
        issues.append("backend_stop_word_not_in_declared_list")
    return {"version": VERSION, "status": "PASS" if not issues else "PARTIAL",
        "scope": "structural single-turn boundary only; not semantic correctness/completeness",
        "raw_response": raw, "raw_sha256": text_hash(raw), "parsed_response": body,
        "parsed_sha256": text_hash(body), "slice_end": offset,
        "excluded_tail": raw[offset:], "visible_delimiter": visible[1] if visible else None,
        "backend_boundary_acknowledged": acknowledged, "backend_stopping_word": stopping_word,
        "eos_reported": eos, "input_delimiter_collision": collision,
        "terminal_punctuation": bool(re.search(r"[.!?][\"']?$", body)),
        "nonempty_lines": len([line for line in body.splitlines() if line.strip()]),
        "issues": issues, "human_semantic_completeness": None,
        "note": "A backend stop may withhold the delimiter. Saved raw means the complete returned payload; no unseen continuation is invented."}
