"""Explicit non-generation preflight, separately authorized execution, offline audit."""
import argparse
from pathlib import Path
import json
import subprocess

from personaslm import p1b_calibration as core
from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.provenance import require_local_path, sha256


def prepare(output):
    result=core.offline_preflight()
    result.update(created_utc=utc_now(),source_hashes=core.source_inventory(),
        git_sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        git_status=subprocess.check_output(['git','status','--short'],text=True))
    result['git_dirty']=bool(result['git_status'].strip())
    output=require_local_path(output)
    output.mkdir(parents=True,exist_ok=False)
    atomic_json(output/'preflight.json',result)
    atomic_json(output/'authorization_PENDING.json',{
        'version':'p1b_calibration_authorization_v1','adapter_version':core.VERSION,
        'authorized':False,'researcher_id':'','final_decision_authority':'','decision_source':'',
        'manifest_sha256':core.MANIFEST_SHA,'dataset_sha256':core.DATA_SHA,
        'preflight_sha256':sha256(output/'preflight.json'),'review_registration_sha256':None,
        'max_total_attempts':192,'allow_automatic_retries':False,
        'notes':'Template only. Researcher review confirmation and explicit execution authorization are distinct. No review date or approval is inferred.'})
    print(json.dumps(result))


def audit_runs(output):
    # This action does not rehash/load model weights or start a server.
    if sha256(require_local_path(core.MANIFEST))!=core.MANIFEST_SHA or sha256(require_local_path(core.DATA))!=core.DATA_SHA:
        raise ValueError('Frozen analysis inputs changed')
    plan=core.load(core.MANIFEST); cases={c['case_id']:c for c in core.load(core.DATA)['cases']}
    root=require_local_path(core.RUN_ROOT)
    segments=[]; provenance=[]
    directories=sorted((root/'runs').glob('*'))
    claim=core.load(root/'claim.json') if directories else None
    for p,_ in core.ordered_segments(root,claim):
        segments.append(read_events(p))
        provenance.append({'run':p.relative_to(require_local_path(Path('.'))).as_posix(),
                           'manifest_sha256':sha256(p/'manifest.json')})
    record=core.audit_segments(plan,cases,segments)
    record.update(created_utc=utc_now(),manifest_sha256=core.MANIFEST_SHA,segments=provenance,
                  algorithmic_opportunity_assessment='No P1b algorithmic conclusion without observed and reviewed failure modes; retain empirical priority and separate future method validation.')
    output=require_local_path(output); output.parent.mkdir(parents=True,exist_ok=True)
    atomic_json(output,record)
    print(json.dumps({'planned':192,'attempted':record['attempted'],'pending':record['pending'],'new_generation_requests':0}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['preflight','run','audit'])
    parser.add_argument('--output',type=Path)
    parser.add_argument('--authorization',type=Path)
    parser.add_argument('--review-registration',type=Path)
    parser.add_argument('--preflight',type=Path)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.action=='preflight':
        if not args.output: parser.error('New output directory required')
        prepare(args.output)
    elif args.action=='audit':
        if not args.output: parser.error('New output JSON required')
        audit_runs(args.output)
    else:
        if not all((args.authorization,args.review_registration,args.preflight)):
            parser.error('Separate authorization, confirmed review and preflight records are required')
        directory,result=core.run_authorized(args.authorization,args.review_registration,args.preflight,resume=args.resume)
        print(json.dumps({'run_directory':directory.as_posix(),**result}))
        if result['status']!='PASS': raise SystemExit(2)
