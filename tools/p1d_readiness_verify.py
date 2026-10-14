"""Additive readiness verification; never changes approved or historical artifacts."""
import ast
import csv
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
from p1d_design import read, sha, write, th
from p1d_approval import verify as verify_approval, SEAL

DEST=Path('docs/validation/p1d/development_readiness_v1')
CANDIDATE=Path('docs/validation/p1d/independent_candidates_v4')

def verify():
    verify_approval()
    preseal=read(SEAL)
    for path,h in preseal['artifact_sha256'].items():
        if sha(path)!=h:raise ValueError('Pre-approval artifact changed: '+path)
    baseline=read('results/p1d_preparation/v1/baseline.json')
    modified=[path for path,h in baseline['files'].items() if sha(path)!=h]
    if set(modified)-{'docs/research_development_log.md'}:
        raise ValueError('Historical tracked files changed: '+str(modified))
    if not Path('docs/research_development_log.md').read_bytes().startswith(Path('results/p1d_preparation/v1/development_log.before.md').read_bytes()):
        raise ValueError('Historical log prefix changed')
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    if head!=baseline['head']:raise ValueError('Git HEAD changed')
    p1c=read('docs/validation/p1c/confirmed_semantic_v1/reproducibility_manifest_v1.json')
    for path,h in p1c['artifact_sha256'].items():
        if sha(path)!=h:raise ValueError('P1c artifact changed: '+path)
    for version in ('v1','v2','v3','v4'):
        manifest=read(f'docs/validation/p1d/independent_candidates_{version}/candidate_provenance_manifest_v1.json')
        for path,h in manifest['artifact_sha256'].items():
            if sha(path)!=h:raise ValueError('Candidate provenance changed: '+path)
    native=read(CANDIDATE/'native_tokenizer_validation_v1.json')
    prompts={r['candidate_request_id']:r for r in read(CANDIDATE/'base_candidate_prompts_v1.json')}
    if len(native['rows'])!=1728 or {r['candidate_request_id'] for r in native['rows']}!=set(prompts):
        raise ValueError('Native candidate IDs mismatch')
    for r in native['rows']:
        if sha(r['native_call_log'])!=r['native_call_sha256']:raise ValueError('Native log changed')
        log=read(r['native_call_log']);ids=ast.literal_eval(log['stdout'].strip())
        if th(str(ids))!=r['token_ids_sha256'] or len(ids)!=r['input_tokens']:raise ValueError('Native IDs differ')
        prompt=prompts[r['candidate_request_id']]['prompt']
        if th(prompt)!=r['prompt_sha256'] or log['prompt_sha256']!=r['prompt_sha256']:raise ValueError('Native prompt differs')
        if log.get('generation',False) or log['exit_code']!=0:raise ValueError('Native execution record invalid')
    paths=list(Path('docs/validation/p1d').rglob('*.json'))
    for p in paths:read(p)
    csvs=list(Path('docs/validation/p1d').rglob('*.csv'))
    for p in csvs:
        with p.open(encoding='utf-8-sig',newline='') as f:
            for r in csv.DictReader(f):
                if None in r:raise ValueError('Malformed CSV: '+str(p))
    docs=[Path('docs/P1d_corrected_protocol_adoption_v1.md'),Path('docs/P1d_development_readiness_v1.md'),
          Path('docs/P1d_independent_boundary_review_guide_v1.md'),Path('docs/P1d_execution_readiness_packet_v1.md')]
    for doc in docs:
        for ref in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
            if '://' not in ref and not ref.startswith('#') and not (doc.parent/ref.split('#')[0]).exists():
                raise ValueError('Broken document link: '+ref)
    report={'version':'p1d_readiness_verification_v1','software_verified_utc':datetime.now(timezone.utc).isoformat(),
        'git_head':head,'git_status':subprocess.check_output(['git','status','--short'],text=True),
        'historical_tracked_hashes_checked':len(baseline['files']),'historical_changes':modified,
        'preapproval_artifacts_equal':len(preseal['artifact_sha256']),'p1c_sealed_artifacts_equal':len(p1c['artifact_sha256']),
        'native_candidate_prompts_verified':len(native['rows']),'candidate_active_matches':native['active_matches'],
        'candidate_control_matches':native['control_matches'],'candidate_context_fit_256':native['context_fit_256'],
        'json_files_validated':len(paths),'csv_files_validated':len(csvs),'authorized_inference_requests':0,
        'new_generations':0,'new_human_annotations':0,'prospective_protocol_adopted':True,
        'confirmatory_materials_frozen':False,'execution_ready':False,'test_results':read('results/p1d_readiness/v1/regression_tests_final.json'),
        'limitations':'Technical preservation and software checks do not certify human stimulus validity, model-arm runtime, budget adequacy or publication readiness.'}
    artifacts=[*DEST.rglob('*'),*CANDIDATE.rglob('*'),*Path('docs/validation/p1d/authorization_v1').rglob('*'),*docs,
               *Path('tools').glob('p1d*.py'),Path('tests/test_p1d_readiness.py')]
    report['artifact_sha256']={p.as_posix():sha(p) for p in sorted(set(artifacts)) if p.is_file() and p.name!='readiness_verification_v1.json'}
    write(DEST/'readiness_verification_v1.json',report)
    print({k:report[k] for k in ('historical_tracked_hashes_checked','preapproval_artifacts_equal','p1c_sealed_artifacts_equal','native_candidate_prompts_verified','execution_ready','new_generations')})

if __name__=='__main__':verify()
