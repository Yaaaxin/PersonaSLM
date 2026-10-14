# P1c decision compatibility resolution

Maintainer: Yaxin ZHENG.

The versioned compatibility importer has registered **74 researcher-confirmed scoped decisions**, preserving all **77** supplied entries. Exactly three approvals remain pending. This supersedes the earlier software-label confirmation request in the received-bundle report; that request was unnecessary. Historical intake reports remain unchanged as an audit trail.

| Source decision | Count | Operational treatment |
|---|---:|---|
| Case: ACCEPT_WITH_RESTRICTED_ESTIMAND | 12 | Preserve restricted development use |
| Active history: ACCEPT_WITH_LIMITATIONS | 48 | Derive ACCEPT_WITH_RESTRICTED_ESTIMAND from the explicitly adopted package-level scope |
| Procedural control: DIAGNOSTIC_ONLY | 12 | LENGTH_MATCHED_DIAGNOSTIC_CONTROL; no strict-neutrality claim |
| Confirmed global scopes | 2 | Preserve package-level and diagnostic-control restrictions |
| Pending global decisions | 3 | Evaluation/statistics, addendum, execution remain unapproved |

The 12 control assessments are the same 12 records included among the 60 texts, not additional independent observations. There are 72 unique case/text items and two confirmed global scopes.

## Lossless registration

[Registration](validation/p1c/decision_compatibility_v1/registration/registration_v1.json) binds the unchanged supplied CSVs, report and source manifest, the exact frozen execution manifest, source-file hashes, importer version, actual registration time and Git state. [Registered records](validation/p1c/decision_compatibility_v1/registration/registered_decisions_v1.json) retain the complete original enriched rows. The operational category is explicitly a software compatibility derivation, not a newly selected researcher label.

All 1,772 non-annotation fields checked against the three repository masters match. The four supplied CSV digests match their supplied manifest. All 77 enriched records agree with the basic confirmation form; case/history decisions, notes and reviewer identity agree across files. The legacy `__` history identifiers and newer `/` identifiers remain intact in their respective sources, joined using their verified case and condition fields.

All 48 legacy active-text records explicitly adopt package-level interpretation and exclude isolated mechanisms. None requires a new semantic decision to normalize. Unresolvable scope would retain the original label and block only affected usage. No original label, explanation, limitation, AI suggestion or researcher note is overwritten. Blank subcriterion ratings remain blank; overall researcher adoption does not manufacture individual YES ratings.

The source manifest also declares hashes for an external original proposal and external report not separately supplied. These declarations are preserved as unverified lineage, while the three repository originals and all four supplied CSVs were verified. No independent second reviewer, inter-rater agreement or review timestamp is inferred. Actual registration timestamps are distinct from human review timestamps.

## Execution gate and interpretation

[Gate result](validation/p1c/decision_compatibility_v1/gate_status_v1.json): technical integrity PASS; execution NO-GO solely because the three genuine approvals are pending. See the [single consolidated packet](P1c_final_consolidated_approval_v1.md). The two already approved global scopes are not reopened, even though immutable original proposal files still contain their historical blank approval fields.

R/T contrasts remain history-text-package contrasts. R also changes topic/predicate/lexical cues; T also changes date intervals and values. Controls can prime procedural structure and are diagnostic only. The shorter no-history condition includes length and archive-format differences. No contrast identifies a pure relevance, temporal, stale-answer-competition or internal cognitive mechanism.

The compatibility command is a separate importer version. The previous strict new-schema importer remains available for its own format; feeding this legacy bundle to that old path is not the current workflow.

```powershell
.venv\Scripts\python.exe tools/p1c_decision_compatibility.py register --output docs/validation/p1c/decision_compatibility_v1/registration
```

This command has already executed; rerunning at that destination refuses overwrite. After actual approval, preserve the completed approval as a new file and validate it without generation:

```powershell
.venv\Scripts\python.exe tools/p1c_decision_compatibility.py gate --registration docs/validation/p1c/decision_compatibility_v1/registration/registration_v1.json --approval <completed-consolidated-approval.json> --output <new-gate-report.json>
```

GO requires three explicit bound decisions, with `AUTHORIZE_72_REQUESTS` for execution. Neither a file's existence nor approval of only the scientific documents authorizes generation. This command never launches inference; an authorized execution still performs the existing runtime preflight.
