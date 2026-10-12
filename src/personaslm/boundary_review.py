"""Supplemental case-insensitive inspection; retains frozen boundary-v1 labels."""
import re
from .response_boundary import boundary_audit

VERSION = "boundary_review_casefold_v2"


def review_boundary(raw, native, case, variant):
    original = boundary_audit(raw, native, case, variant)
    role = re.search(r"(?im)^[ \t]*(?:user|assistant)[ \t]*:", original["parsed_response"])
    extra_role = role is not None and not case["literal_role_text_allowed"]
    status = "PARTIAL" if extra_role else original["status"]
    return {"version": VERSION, "frozen_v1_status": original["status"], "reviewed_structural_status": status,
        "additional_role_material_in_v1_body": extra_role,
        "role_excerpt": role.group() if extra_role else None,
        "v1_false_structural_pass": extra_role and original["status"] == "PASS",
        "human_semantic_completeness": None,
        "note": "Offline diagnostic correction only. No stop list, experimental raw output, saved v1 classification or production parser was changed."}
