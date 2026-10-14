"""Seal prospective preparation and targeted historical preservation; never inference."""
import csv
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import subprocess
from p1d_design import OUT,read,write,sha

def verify(seal=False):
    baseline=read('results/p1d_preparation/v1/baseline.json')
    changed=[p for p,h in baseline['files'].items() if sha(p)!=h]
    if set(changed)-{'docs/research_development_log.md'}:raise ValueError(('Historical tracked files changed',changed))
    log=Path('docs/research_development_log.md').read_bytes()
    if not log.startswith(Path('results/p1d_preparation/v1/development_log.before.md').read_bytes()):raise ValueError('Log not append-only')
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    if head!=baseline['head']:raise ValueError('Git HEAD changed')
    p1c=read('docs/validation/p1c/confirmed_semantic_v1/reproducibility_manifest_v1.json')
    for p,h in p1c['artifact_sha256'].items():
        if sha(p)!=h:raise ValueError(('P1c seal mismatch',p))
    import p1c_calibration
    actual=p1c_calibration.audit()
    if actual!=read('docs/validation/p1c/calibration_v1/measurement_v1/execution_integrity_v1.json'):raise ValueError('Original raw response reconstruction differs')
    packet=read(OUT/'researcher_decision_packet_v1.json')
    for p,h in packet['bound_documents_sha256'].items():
        if sha(p)!=h:raise ValueError(('Prospective approval object changed',p))
    paths=list(OUT.rglob('*.json'));csvs=list(OUT.rglob('*.csv'))
    for p in paths:read(p)
    for p in csvs:
        with p.open(encoding='utf-8',newline='') as f:
            for r in csv.DictReader(f):
                if None in r:raise ValueError(('Malformed CSV',p))
    docs=[Path('docs/P1c_scientific_closeout.md'),*Path('docs').glob('P1d*.md'),Path('docs/related_work_novelty_matrix_monitor_v4.md')]
    missing=[]
    for p in docs:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):continue
            resolved=p.parent/target.split('#')[0]
            if not resolved.exists() and resolved!=OUT/'reproducibility_manifest_v1.json':missing.append(str(resolved))
    if missing:raise ValueError(('Missing documentation links',missing))
    report={'version':'p1d_preparation_verification_v1','software_verified_utc':datetime.now(timezone.utc).isoformat(),
        'maintainer':'Yaxin ZHENG','technical_verification':'PASS','scientific_approval':'PENDING','execution_authorization':'NONE',
        'git_head':head,'git_status':subprocess.check_output(['git','status','--short'],text=True),
        'entry_tracked_files':len(baseline['files']),'append_only_changes':changed,'p1c_sealed_artifacts_equal':len(p1c['artifact_sha256']),
        'p1c_actual_raw_reconstruction_equal':True,'p1c_http_responses_verified':actual['http_response_bytes_verified'],
        'p1c_run_event_hashes_verified':sum(len(s['events']) for s in actual['segments']),
        'new_model_generations':0,'new_human_annotations':0,'independent_validation_cases_created':0,
        'development_examples':16,'development_prompts':96,'token_matching':'14/16 active matches; 0/16 procedural matches; NOT stimulus readiness',
        'json_files_validated':len(paths),'csv_files_validated':len(csvs),'test_result':read('results/p1d_preparation/v1/tests_final.json'),
        'source_provenance':read(OUT/'provenance_manifest_v1.json'),'approval_objects':packet['bound_documents_sha256'],
        'source_identity_note':'Historical source identities and all 72 raw HTTP/parser reconstructions checked; no broad historical test suite rerun.',
        'limitations':'Only a prospective plan. All open material, model, independent-review and identification risks remain documented.'}
    if seal:
        artifacts=[*OUT.rglob('*'),*docs,*Path('tools').glob('p1d*.py'),Path('tests/test_p1d_prospective.py')]
        report['artifact_sha256']={p.as_posix():sha(p) for p in sorted(set(artifacts)) if p.is_file() and p.name!='reproducibility_manifest_v1.json'}
        write(OUT/'reproducibility_manifest_v1.json',report)
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seal',action='store_true');args=p.parse_args()
    r=verify(args.seal);print(json.dumps({k:r[k] for k in ('technical_verification','entry_tracked_files','p1c_sealed_artifacts_equal','p1c_http_responses_verified','p1c_run_event_hashes_verified','new_model_generations')},indent=2))
