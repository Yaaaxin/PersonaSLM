"""Register explicit researcher approval; no inference and no fabricated review time."""
import argparse
from collections import Counter
import csv
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import random
import shutil

from personaslm import p1b_calibration as core
from personaslm.journal import atomic_json
from personaslm.p1b_readiness import CHECKS
from personaslm.p1b_review_proposal import proposals,CONFIRM

PUBLIC=Path('docs/validation/p1b/calibration_v1')
LOCAL=Path('results/p1b_execution/v1')
PROPOSAL=Path('docs/validation/p1b/final_review_v1/stimulus_review_AI_proposed_v1.csv')
PREFLIGHT=PUBLIC/'execution_preflight_v1/preflight.json'
def h(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def csv_write(path,rows):
    with path.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def review():
    data=core.load(core.DATA); master=core.csv_records(core.MASTER); proposal=core.csv_records(PROPOSAL)
    if proposal!=proposals(data,master) or h(PROPOSAL)!='652a21aa67a4ac04f357f95653cc7c449a2982719d2c375253fd1769158bd718':
        raise ValueError('Mandatory review integrity failed')
    if h(core.DATA)!=core.DATA_SHA or h(core.MANIFEST)!=core.MANIFEST_SHA:
        raise ValueError('Mandatory frozen input check failed')
    PUBLIC.mkdir(parents=True,exist_ok=False)
    instruction={
      'version':'p1b_researcher_instruction_v1','recorded_utc':datetime.now(timezone.utc).isoformat(),
      'source_role':'user','source_message_title':'PersonaSLM — P1b Researcher Approval and Real CPU Calibration Execution',
      'researcher':'Yaxin ZHENG','message_id':None,'actual_review_timestamp':None,
      'authorization_excerpt_verbatim':"""I have personally reviewed the 24-case
stimulus assessment and its limitations.

I accept the reviewed development
stimuli for bounded P1b calibration.

This approval is limited to
development-stage experimentation.

It does not establish:

- Empirical task difficulty
- Complete causal identification
- Neutral-control validity
- Confirmatory statistical evidence
- Scientific novelty

Preserve the original AI-assisted
assessment provenance accurately.

Do not fabricate independent reviewers.

After verifying the frozen manifest,
the actual model configuration,
source integrity and mandatory checks,
I explicitly authorize exactly
192 real CPU generations.

Any substantive configuration change,
failed mandatory preflight or invalid
review record requires stopping and
requesting new authorization.""",
      'annotation_instruction_excerpt_verbatim':"""Register researcher confirmation with:

reviewer_id:
Yaxin_ZHENG

review_status:
RESEARCHER_CONFIRMED

final_decision_authority:
researcher

review_method:
Researcher confirmation of
AI-assisted case-level assessment""",
      'provenance':'Actual researcher message; rows below are tool-transcribed from explicit whole-packet confirmation, not independently hand-entered CSV or blinded outcome annotations.',
      'proposal_sha256':h(PROPOSAL),'dataset_sha256':core.DATA_SHA,'manifest_sha256':core.MANIFEST_SHA,
      'limitations_preserved':['H_L1/H_L2 do not establish context necessity','H_L3 consecutive User turns',
        'Reasoning shortcuts and untested empirical difficulty','Style partly nested in speaker',
        'Task family/history relevance confounding','96-token output may be incomplete',
        'No neutral validity, confirmatory finding or novelty approval'],
      'instruction_scope':'Exactly the frozen 192-request Base calibration after mandatory checks; stop for any mandatory failure or substantive change.'}
    atomic_json(PUBLIC/'researcher_instruction_v1.json',instruction)
    rows=[]
    for p in proposal:
        row=dict(p)
        row.update(researcher_confirmation=CONFIRM,reviewer_id='Yaxin_ZHENG',
          review_method='Researcher confirmation of AI-assisted case-level assessment',
          reviewer_notes='Explicit whole-packet researcher confirmation transcribed from the user message titled PersonaSLM — P1b Researcher Approval and Real CPU Calibration Execution; accepted only for bounded development calibration. Original limitations retained.')
        rows.append(row)
    csv_write(PUBLIC/'stimulus_researcher_confirmed_source_v1.csv',rows)
    # Freeze review-packet ordering before observing calibration output.
    plan=core.load(core.MANIFEST)
    rng=random.Random(714002); ids=[r['request_id'] for r in plan['requests']];rng.shuffle(ids)
    cases=list(plan['case_order']); rng.shuffle(cases)
    mapping={'version':'p1b_semantic_review_mapping_v1','created_utc':datetime.now(timezone.utc).isoformat(),
      'purpose':'Condition-masked review packet ordering only; does not change experimental order',
      'seed':714002,'manifest_sha256':core.MANIFEST_SHA,
      'case_aliases':{c:f'BC{i+1:03d}' for i,c in enumerate(cases)},
      'responses':[{'anonymous_response_id':f'BR{i+1:03d}',**{k:next(r for r in plan['requests'] if r['request_id']==rid)[k] for k in ('request_id','case_id','persona_id','condition','factors')}} for i,rid in enumerate(ids)]}
    (LOCAL/'protected').mkdir(parents=True,exist_ok=True)
    atomic_json(LOCAL/'protected/review_mapping_v1.json',mapping)
    print(json.dumps({'review_records':24,'proposed_judgments_validated':dict(Counter(r['ai_proposed_'+k] for r in rows for k in CHECKS)),
       'review_timestamp_invented':False,'source':(PUBLIC/'researcher_instruction_v1.json').as_posix(),'inference_started':False}))

def authorize():
    imported=core.load(PUBLIC/'review_import_v1/registration.json')
    master=core.csv_records(core.MASTER)
    if not core.validate_reviews(master,imported['records'])['all_accepted']:
        raise ValueError('Invalid mandatory researcher review')
    registration={**imported,'version':'p1b_researcher_verified_stimulus_registration_v1',
      'reviewer_id':'Yaxin_ZHENG','review_status':'RESEARCHER_CONFIRMED',
      'final_decision_authority':'researcher',
      'review_method':'Researcher confirmation of AI-assisted case-level assessment',
      'importer_review_method_preserved':imported['review_method'],
      'source_instruction':(PUBLIC/'researcher_instruction_v1.json').as_posix(),
      'source_instruction_sha256':h(PUBLIC/'researcher_instruction_v1.json'),
      'original_import_registration_sha256':h(PUBLIC/'review_import_v1/registration.json'),
      'annotation_provenance':'Whole-packet researcher confirmation via user message, transcribed by tool; not independent blind outcome annotation.',
      'actual_review_timestamp':None}
    atomic_json(PUBLIC/'researcher_review_registration_v1.json',registration)
    preflight=core.load(PREFLIGHT)
    if preflight['source_hashes']!=core.source_inventory():
        raise ValueError('Mandatory execution source check failed')
    usage=shutil.disk_usage('.')
    # Operational logging reserve, not a scientific acceptance criterion.
    required=256*1024*1024
    if usage.free<required:
        raise ValueError('Mandatory logging headroom check failed')
    probe=LOCAL/'logging_write_probe.bin'
    with probe.open('xb') as f:
        f.write(b'P1b raw logging filesystem preflight\n');f.flush();os.fsync(f.fileno())
    probe_sha=h(probe)
    if probe.read_bytes()!=b'P1b raw logging filesystem preflight\n':
        raise ValueError('Mandatory logging filesystem read-back failed')
    probe.unlink()
    auth={**core.load(PUBLIC/'execution_preflight_v1/authorization_PENDING.json'),
      'authorized':True,'researcher_id':'Yaxin_ZHENG','final_decision_authority':'researcher',
      'decision_source':(PUBLIC/'researcher_instruction_v1.json').as_posix(),
      'decision_source_sha256':h(PUBLIC/'researcher_instruction_v1.json'),
      'review_registration_sha256':h(PUBLIC/'researcher_review_registration_v1.json'),
      'authorization_registered_utc':datetime.now(timezone.utc).isoformat(),'actual_review_timestamp':None,
      'notes':'Explicit researcher authorization from the current user message; bound to unchanged experimental inputs/configuration. No retries or extra waves.',
      'mandatory_static_checks':{'disk_free_bytes':usage.free,'logging_reserve_bytes':required,'filesystem_write_read_fsync':'PASS',
        'probe_sha256':probe_sha,'source_hashes':'PASS','review_records':24,'confirmed_judgments':312},
      'stop_on_mandatory_failure':True}
    core.verify_authorization(auth,registration,master,preflight,actual_review_hash=h(PUBLIC/'researcher_review_registration_v1.json'),actual_preflight_hash=h(PREFLIGHT))
    atomic_json(PUBLIC/'researcher_authorization_v1.json',auth)
    csv_write(PUBLIC/'researcher_decisions_registered_v1.csv',[
      {'decision_id':'Q1','status':'RESEARCHER_CONFIRMED','scope':'24 cases and 312 case-level positive-criterion judgments; development only','reviewer_id':'Yaxin_ZHENG','review_timestamp':'','source':auth['decision_source']},
      {'decision_id':'Q2','status':'RESEARCHER_CONFIRMED','scope':'Limited interpretation and unchanged task-specific manual evaluation routing','reviewer_id':'Yaxin_ZHENG','review_timestamp':'','source':auth['decision_source']},
      {'decision_id':'A1','status':'AUTHORIZED_SUBJECT_TO_LIVE_PREFLIGHT','scope':'Exactly 192 frozen requests; stop on mandatory failure or interruption','reviewer_id':'Yaxin_ZHENG','review_timestamp':'','source':auth['decision_source']}])
    print(json.dumps({'researcher_review':'RESEARCHER_CONFIRMED','records':24,'judgments':312,'disk_free_bytes':usage.free,
      'mandatory_static_checks':'PASS','authorization':'REGISTERED','live_preflight':'REQUIRED_BEFORE_FIRST_GENERATION','generation_requests':0}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['review','authorize']);a=p.parse_args()
    {'review':review,'authorize':authorize}[a.action]()

