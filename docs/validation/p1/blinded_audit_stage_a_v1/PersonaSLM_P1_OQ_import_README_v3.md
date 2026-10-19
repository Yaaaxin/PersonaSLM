# PersonaSLM P1 O/Q — researcher audit import (preservation-first)

This package is built from the user-submitted 32-row blinded review in `csv.txt` and the frozen 32-row original blind template. All 32 reviewer labels and comments are preserved as submitted (including rows 17 and 27); identity `Yaxin ZHENG` is copied into each row. No review dates invented.

The date-binding columns are only **prescriptive audit metadata**; the original automatic scorer code has not yet been checked. `registered_evaluation_date_used_for_scoring=No` is a requirement for the NEW corrected scorer, NOT a verified historical observation. `historical_automatic_scorer_date_usage=NOT_AUDITED`.

The previously produced SIX corrections are **NOT applied**, because they differ from the user's latest explicitly submitted review. Their disputed fields (including scientific label changes at rows 17 and 27) are listed in `PersonaSLM_six_proposals_NOT_APPLIED_v3.csv`. Resolve only through explicit researcher confirmation, independently of condition identities.

Place both CSVs at `docs/validation/p1/blinded_audit_stage_a_v1/` (or a versioned subfolder) inside PersonaSLM. Preserve the original template and unblinding key. Do NOT run `PersonaSLM_P1_OQ_merge_and_fill_name_v2.py`: it assumes a full 32-row source template and forcibly overwrites the six reviewer labels from proposal files.

Files SHA256:
- blinded audit: `b0e8cff9b80bdb6055d81333fc0a42a3117e1d5a3bc043f7dcce4cd9aa8ecb84`
- proposal diff: `49d423a8f3ec10ce52c64d9cd9561173773da012ef73d223c6b48cf4eb143275`
- original blank template: `5bc9712ef9c5ad0e2a1769e55d99b72f7a4e99ab9e77a4657a605b642bfb1781`
- original submitted manual labels: `cea5090418633b2ec153becbd27600ee1d6a71645134aad536ad77908ddba8d7`

No unblinding, inference, automatic score correction, or researcher-approval inference performed.
