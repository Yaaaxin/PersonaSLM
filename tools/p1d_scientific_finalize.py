"""Seal new offline work and verify preservation against this turn's baseline."""
from collections import Counter
import csv
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
from p1d_design import read, write, csvwrite, sha
from p1d_scientific_audit import DEST

LOCAL=Path('results/p1d_scientific_validation/v1')
DOCS=[Path('docs')/name for name in (
    'P1d_stimulus_validity_audit_v1.md','P1d_control_neutrality_assessment_v1.md','P1d_identification_assessment_v1.md',
    'P1d_actual_tokenizer_validation_v1.md','P1d_independent_validation_integrity_v1.md','P1d_output_budget_calibration_plan_v1.md',
    'P1d_instruct_arm_readiness_v1.md','P1d_statistical_precision_assessment_v1.md','P1d_measurement_readiness_v1.md',
    'P1d_algorithmic_development_update_v1.md','P1d_execution_readiness_packet_v2.md')]

def main():
    baseline=read(LOCAL/'baseline.json');tests=read(LOCAL/'regression_tests_v1.json')
    if tests['exit_code']!=0:raise ValueError('Tests failed')
    a=list(csv.DictReader((DEST/'historical_budget_delivery_audit_v1.csv').open(encoding='utf-8')))
    b=list(csv.DictReader((DEST/'historical_budget_delivery_audit_v2.csv').open(encoding='utf-8')))
    corrections=[{'wave':x['wave'],'raw_event':x['raw_event'],'incorrect_joined_id':x['response_id'],'correct_id':y['response_id'],
        'old_delivery':x['answer_delivery'],'correct_delivery':y['answer_delivery'],'delivery_changed':x['answer_delivery']!=y['answer_delivery']} for x,y in zip(a,b) if x['response_id']!=y['response_id']]
    csvwrite(DEST/'rejected_hash_join_corrections_v1.csv',corrections)
    fix=read(DEST/'engineering_correction_register_v1.json')
    fix['identity_misassociations_in_rejected_attempt']=dict(Counter(r['wave'] for r in corrections))
    fix['delivery_label_changes_in_rejected_attempt']=sum(r['delivery_changed'] for r in corrections)
    fix['item_level_corrections']='rejected_hash_join_corrections_v1.csv'
    fix['current_diagnostic_version']='v2';write(DEST/'engineering_correction_register_v2.json',fix)
    for row in b:
        if sha(row['raw_event'])!=row['raw_event_sha256']:raise ValueError('Historical raw event changed')
    now=datetime.now(timezone.utc).isoformat()
    entry=f'''\n\n## {now} — P1d scientific validation and bounded execution preparation\n\nMaintainer: Yaxin ZHENG. AI-assisted development and semantic material proposals; no human decisions fabricated. HEAD at start: `{baseline['head']}`; working tree was clean. The researcher had committed earlier work between sessions; no Git commit/push was performed here.\n\nVerified the already corrected plan approval and original document hashes. The latest user message repeated an older addendum hash transcription variant; retained the actual registered unchanged hash without reopening approval. Audited all 288 candidate cases and 1,152 active histories, reconstructed evidence/answers, checked 1,728 saved native token logs/IDs, and verified current Base/server/tokenizer plus 29 DLLs. AI proposals: 288 VALID_WITH_LIMITATIONS and 288 LENGTH_MATCHED_DIAGNOSTIC_CONTROL; zero human approvals. No main-study stimuli changed or froze. New template audit: 247 question strings, 16 abstract grammars, shared development ancestry and template/target-role imbalance. All 72 follow-ups have two ledger-consistent alternatives without fixed context; this is an offline material diagnostic, not a new arm.\n\nImplemented `p1d_scientific_audit.py`, `p1d_scientific_supplement.py`, `p1d_budget_manifest.py`, `p1d_template_precision.py`, `p1d_metric_contracts.py`, `p1d_instruct_template_check.py`, `p1d_scientific_packet.py` and this finalizer. Created eleven focused English reports, case/control review files, contrast/confound inventory, applicability checks, exact 144-request development-only budget manifest v2, measurement contracts and literature/algorithm registry deltas in `docs/validation/p1d/scientific_validation_v1`. The 2,016 main-study requests and 144 diagnostic requests remain unauthorized.\n\nHistorical budget review read all 192 P1b and 72 P1c saved result events. A first new diagnostic joined by nonunique raw-text hashes, misassociating IDs ({fix['identity_misassociations_in_rejected_attempt']}) and changing one P1c delivery count. Rejected outputs and source code are preserved; corrected v2 uses request identity and verifies text, restoring P1c 43 Success/20 Failure/9 Uncertain. No historical source or official analysis was changed. Initial read-only inspection helpers also encountered a list/dict mismatch and Windows rg glob/path errors; corrected bounded queries succeeded.\n\nPrecision: 108 synthetic configurations × 128 replications, 324 summaries; full second reconstruction exactly equal. Explicit cross-template slopes expose conditional-template versus new-template coverage differences; no empirical ICC estimated. No cohort expansion adopted. Eight authored metric-contract fixtures exercise independent evidence inputs and uncertainty, without invented model responses or human labels. Existing algorithm prototype and failed/negative findings preserved; no supported original algorithm claimed.\n\nOfficial Instruct template rendering: Jinja2 3.1.6 / MarkupSafe 3.0.4 installed into a project-local results target. Initial sandbox network call failed with WinError 10013; the approved escalation of the same bounded pip command succeeded (small dependencies only, no weights). Rendered all 288 candidate strings from official pinned bytes; both official variants agree for the chosen single-user mapping but differ in an assistant-turn probe. No local Instruct GGUF/native tokenization/runtime/latency/RAM result exists. Main study remains NO-GO for scientific scope, material/independent review, budget, model and final authorization prerequisites.\n\nValidation commands: offline tools listed above; `.venv/Scripts/python.exe -m pytest -q tests/test_p1d_scientific_validation.py tests/test_p1d_readiness.py tests/test_p1d_prospective.py` — {tests['stdout'].strip().splitlines()[-1]}. Initial relevant run before the template/context tests: 94 passed in 12.58s. No broad historical test-suite rerun. Final preservation/CSV/JSON/link/diff checks are recorded in the new reproducibility manifest. No new model inference, training, historical protocol adoption/change, independent annotation, public release or Git commit/push.\n'''
    log=Path('docs/research_development_log.md')
    if not log.read_bytes().startswith((LOCAL/'development_log.before.md').read_bytes()):raise ValueError('Historical log prefix changed')
    with log.open('ab') as f:f.write(entry.encode('utf-8'))
    changed=[p for p,h in baseline['files'].items() if sha(p)!=h]
    if set(changed)!={'docs/research_development_log.md'}:raise ValueError('Unexpected original tracked modifications: '+str(changed))
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    if head!=baseline['head']:raise ValueError('HEAD changed during work')
    for p in DEST.rglob('*.json'):read(p)
    csvs=list(DEST.rglob('*.csv'))
    for p in csvs:
        with p.open(encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                if None in row:raise ValueError('Malformed CSV: '+str(p))
    for p in DOCS:
        for ref in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' in ref or ref.startswith('#'):continue
            target=(p.parent/ref.split('#')[0])
            if target==DEST/'reproducibility_manifest_v1.json':continue
            if not target.exists():raise ValueError('Broken link: '+str(target))
    for p,h in read(DEST/'execution_readiness_packet_v2.json')['source_sha256'].items():
        if sha(p)!=h:raise ValueError('Readiness binding changed: '+p)
    diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True)
    if diff.returncode:raise ValueError(diff.stdout+diff.stderr)
    files=[*DEST.rglob('*'),*DOCS,Path('tests/test_p1d_scientific_validation.py'),
        *[Path('tools')/n for n in ('p1d_scientific_audit.py','p1d_scientific_supplement.py','p1d_budget_manifest.py','p1d_template_precision.py','p1d_metric_contracts.py','p1d_instruct_template_check.py','p1d_scientific_packet.py','p1d_scientific_finalize.py')],LOCAL/'regression_tests_v1.json',log]
    report={'version':'p1d_scientific_reproducibility_v1','software_verified_utc':now,'git_head':head,
        'git_status':subprocess.check_output(['git','status','--short'],text=True),'original_tracked_files_checked':len(baseline['files']),
        'original_tracked_changes':changed,'original_log_prefix_preserved':True,'historical_raw_result_events_unchanged':len(b),
        'test_results':tests,'git_diff_check':{'exit_code':diff.returncode,'stdout':diff.stdout,'stderr':diff.stderr},
        'precision_reconstruction':read(DEST/'precision_reconstruction_check_v1.json'),
        'new_model_inference':0,'new_human_ratings':0,'new_independent_validation_results':0,'main_study_ready':False,
        'candidate_dataset_frozen':False,'authorized_inference':0,
        'inactive_failed_diagnostics':['historical_budget_summary_v1.json','historical_budget_delivery_audit_v1.csv'],
        'active_budget_manifest':'budget_calibration_manifest_candidate_v2.json','active_historical_budget_audit':'historical_budget_delivery_audit_v2.csv',
        'artifact_sha256':{p.as_posix():sha(p) for p in sorted(set(files)) if p.is_file() and p.name!='reproducibility_manifest_v1.json'}}
    write(DEST/'reproducibility_manifest_v1.json',report)
    print({'tracked_unchanged_except_append_log':len(baseline['files']),'raw_result_events_unchanged':len(b),
        'artifacts_sealed':len(report['artifact_sha256']),'tests':tests['stdout'].strip().splitlines()[-1],
        'readiness':'NO_GO','new_inference':0})

if __name__=='__main__':main()
