# PersonaSLM P1 O/Q date patch — v2 (reviewer-name convenience)

Extract all files together to:
`<PersonaSLM repo>/docs/validation/p1/blinded_audit_stage_a_v1/patches/scoring_date_v2/`

Only **researcher_name** is filled automatically as `Yaxin ZHENG`, as requested.
There is NO automatic scientific annotation, no fabricated independent reviewer, and no review timestamp.

Requires an actually completed 32-row CSV as `--input`; a blank blind-audit template will be rejected.
The output must be a new filename. Originals remain unchanged. No unblinding or inference.

PowerShell in repository root:
```powershell
$patch = 'docs/validation/p1/blinded_audit_stage_a_v1/patches/scoring_date_v2'
$inputCsv = 'docs/validation/p1/blinded_audit_stage_a_v1/blinded_researcher_audit_RESEARCHER_FILLED_v1.csv'
$outputCsv = 'docs/validation/p1/blinded_audit_stage_a_v1/blinded_researcher_audit_RESEARCHER_CONFIRMED_DATE_AUDITED_v2.csv'
.\.venv\Scripts\python.exe "$patch/PersonaSLM_P1_OQ_merge_and_fill_name_v2.py" --input $inputCsv --output $outputCsv --researcher-name 'Yaxin ZHENG'
```

The final scientific records are kept blind. The researcher-name column is not a reviewer-independence claim. Before any Stage B, verify actual researcher labels (32/32), the scorer-date implementation and key integrity.
