"""Build AI proposals or register explicit confirmations; never authorize inference."""
import argparse
from collections import Counter
from pathlib import Path
import json

from personaslm.journal import atomic_json, utc_now
from personaslm.p1b_calibration import DATA, DATA_SHA, MANIFEST_SHA, MASTER, csv_records, load
from personaslm.p1b_readiness import CHECKS, validate_reviews
from personaslm.p1b_review_proposal import proposals, confirmed_copy, VERSION
from personaslm.provenance import require_local_path, sha256
from p1b_design import write_csv

PROPOSAL=Path('docs/validation/p1b/final_review_v1/stimulus_review_AI_proposed_v1.csv')
PUBLIC=Path('docs/validation/p1b/authorization_v1')


def build():
    rows=proposals(load(DATA),csv_records(MASTER))
    write_csv(require_local_path(PROPOSAL),rows)
    PUBLIC.mkdir(parents=True,exist_ok=True)
    record={'version':VERSION,'created_utc':utc_now(),'source_master':MASTER.as_posix(),
        'source_master_sha256':sha256(require_local_path(MASTER)), 'dataset_sha256':DATA_SHA,
        'manifest_sha256':MANIFEST_SHA,'proposal_sha256':sha256(require_local_path(PROPOSAL)),
        'cases':24,'proposed_judgments':dict(Counter(r['ai_proposed_'+k] for r in rows for k in CHECKS)),
        'proposed_case_decisions':dict(Counter(r['ai_case_decision'] for r in rows)),
        'human_decisions':0,'source_fields_preserved':24*41,
        'provenance':'AI-assisted proposal with source-specific explanations; no human approval',
        'inference_authorized':False}
    atomic_json(PUBLIC/'proposal_inventory_v1.json',record)
    print(json.dumps(record))


def register(source,output,interpretation,scoring):
    if not interpretation or not scoring:
        raise ValueError('Explicit researcher confirmation of limited interpretation and scoring routing is required')
    source=require_local_path(source); output=require_local_path(output)
    proposal=csv_records(PROPOSAL); master=csv_records(MASTER)
    if proposal!=proposals(load(DATA),master):
        raise ValueError('AI proposal no longer reconstructs')
    frozen=load(PUBLIC/'proposal_inventory_v1.json')
    if sha256(require_local_path(PROPOSAL))!=frozen['proposal_sha256']:
        raise ValueError('Proposal bytes changed')
    records=confirmed_copy(master,proposal,csv_records(source))
    result=validate_reviews(master,records)
    output.mkdir(parents=True,exist_ok=False)
    with (output/'original_confirmation.csv').open('xb') as f: f.write(source.read_bytes())
    write_csv(output/'official_review.csv',records)
    registration={**result,'version':'p1b_researcher_stimulus_confirmation_v1','registered_utc':utc_now(),
        'review_timestamp':'Only if actually supplied in individual records',
        'manifest_sha256':MANIFEST_SHA,'dataset_sha256':DATA_SHA,
        'source_proposal_sha256':frozen['proposal_sha256'],'original_confirmation_sha256':sha256(source),
        'official_review_sha256':sha256(output/'official_review.csv'),
        'interpretation_confirmed':True,'evaluation_routing_confirmed':True,
        'records':records,'final_decision_authority':'researcher',
        'review_method':'Explicit per-case confirmation of all 13 AI-proposed positive-criterion judgments; individual reviewer/method fields preserved; not blind review',
        'inference_authorized':False}
    atomic_json(output/'registration.json',registration)
    print(json.dumps({'registered':24,'inference_authorized':False}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['build','register-confirmed'])
    parser.add_argument('--csv',type=Path); parser.add_argument('--output',type=Path)
    parser.add_argument('--confirm-limited-interpretation',action='store_true')
    parser.add_argument('--confirm-evaluation-routing',action='store_true')
    args=parser.parse_args()
    if args.action=='build': build()
    else:
        if not args.csv or not args.output: parser.error('Completed CSV and new output directory required')
        register(args.csv,args.output,args.confirm_limited_interpretation,args.confirm_evaluation_routing)
