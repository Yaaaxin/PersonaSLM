"""Versioned AI-authored review transcription, never an inference/scoring model."""
import argparse
from collections import Counter
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path('docs/validation/p1c/calibration_v1')
SOURCE=ROOT/'measurement_v1/semantic_scoring_view_v1.csv'
OUT=ROOT/'semantic_review_v1'
POLICY=Path('docs/validation/p1c/final_review_v1/evaluation_policy_proposed_v1.json')
FIELDS=('factual_consistency','temporal_consistency','response_relevance','conversational_coherence',
        'task_success','component_coverage','semantic_completeness')
# Explicit post-output AI judgments, after reading all masked evidence and replies.
# These groups are transcription conveniences, NOT rules fitted for prediction.
REVIEW={
 'supported':[1,2,3,5,7,8,13,14,15,17,18,20,21,22,24,25,26,28,32,34,36,38,41,43,45,46,47,50,51,52,55,56,57,59,60,61,62,64,66,68,69,72],
 'attribute_wording':[4], 'calendar_wording':[6],
 'later_target_state':[9,19,31,48,53,65,67,70],
 'earlier_target_state':[12,16,29,37,49,58,71],
 'other_entity_attribute':[11,27,30,35,40],
 'boundary_unresolved':[10,23,33,39,42,44,54,63]}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def text_sha(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False)
def write_csv(path,records):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader()
        for record in records:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else '' if v is None else v for k,v in record.items()})
def require(ok,message):
    if not ok:raise ValueError(message)


def supporting_quotes(row):
    ids=json.loads(row['reference_fact_ids']);lines=row['trusted_evidence'].splitlines()
    quotes=[line for line in lines if any(line.startswith('['+i+']') for i in ids)]
    require(len(quotes)==len(ids),'Missing reference fact quotations')
    return quotes


def stage_a():
    destination=OUT/'stage_a';require(not destination.exists(),'Preserve frozen Stage A')
    original=rows(SOURCE)
    require(len(original)==72 and {r['anonymous_response_id'] for r in original}=={f'PC{i:03}' for i in range(1,73)},'Review identities differ')
    forbidden={'condition','factor_assignment','frozen_structural_status','raw_full_continuation','native_termination'}
    require(not forbidden.intersection(original[0]),'Treatment/structure masking failure')
    assignments={n:g for g,items in REVIEW.items() for n in items}
    require(len(assignments)==sum(map(len,REVIEW.values()))==72,'AI decision inventory differs')
    proposal=[]
    for row in original:
        rid=row['anonymous_response_id'];number=int(rid[2:]);group=assignments[number]
        require(text_sha(row['raw_first_reply'])==row['first_reply_sha256'],'First span hash differs')
        require(all(v=='' for k,v in row.items() if k.startswith('human_')),'Source human fields changed')
        components=json.loads(row['required_answer_components']);n=len(components)
        score={'factual_consistency':'Correct','temporal_consistency':'Correct','response_relevance':5,
               'conversational_coherence':5,'task_success':1,'component_coverage':1.0,'semantic_completeness':'YES'}
        supported=components;contradicted=[];unknown=[];confidence='HIGH';extra=[]
        reason=f'{rid}: the answer asserts {components} for the named target at {row["requested_date"]}; the quoted target facts support every requested component.'
        alternative='No distinct incompatible reading identified; verify the implicit reference to the question date where the reply omits it.'
        adjudication='Confirm or correct all seven proposed ratings and their evidence.'
        if group in ('later_target_state','earlier_target_state'):
            score.update(factual_consistency='Incorrect',temporal_consistency='Incorrect',task_success=0,component_coverage=0.0)
            supported=[];contradicted=components
            period='later' if group=='later_target_state' else 'earlier'
            reason=f'{rid}: the asserted assignment in the quoted reply belongs to a {period} target interval, not {row["requested_date"]}. The requested components {components} are contradicted. This does not identify which conditioning caused the error.'
            alternative='The named value may also occur for another entity; matching a dated fact is descriptive, not proof of an internal temporal-selection process.'
        elif group=='other_entity_attribute':
            score.update(factual_consistency='Incorrect',temporal_consistency='Unverifiable',task_success=0,component_coverage=0.0)
            if number in (11,27,30):score.update(response_relevance=4,conversational_coherence=4)
            supported=[];contradicted=components;confidence='MODERATE'
            reason=f'{rid}: the response assigns Laurel to Idris Fern, but the target route 52 leads to Silver. Laurel is Archive colleague 5\'s collection desk in the same queried interval. The answer conflicts with the requested destination; selection of an incorrect time interval is not independently established.'
            alternative='Temporal Incorrect is an alternative if every false date-bound answer is coded as temporally wrong; Temporal Correct could describe the selected colleague record\'s interval but would evaluate the wrong entity. The proposed Unverifiable avoids both assumptions.'
            adjudication='Adjudicate temporal assessability separately from the demonstrable wrong target answer; retain Incorrect factual and task-failure proposals unless corrected.'
        elif group=='attribute_wording':
            score.update(response_relevance=4,conversational_coherence=4);confidence='MODERATE'
            reason=f'{rid}: Cobalt is the supported destination through route 53, and is explicitly delivered. Proposed Correct/task-success=1 reads "collection desk" as loose wording for the collection destination, not a separately supported desk assignment.'
            alternative='A strict attribute-type reading treats the desk claim as unsupported; then factual Unverifiable and unknown/failed task success may be preferable. This qualification is not concealed.'
            adjudication='Decide whether collection desk is acceptable contextual wording for the requested destination room; do not decide solely from the word Cobalt.'
        elif group=='calendar_wording':
            score.update(factual_consistency='Unverifiable',temporal_consistency='Unverifiable',response_relevance=4,
                         conversational_coherence=4,task_success=None,component_coverage=1.0)
            confidence='LOW';extra=['Calendar-date/weekday relation not supplied by the trusted ledger']
            reason=f'{rid}: Orchid and recurring service day Thursday are both supported. "on Thursday, 2042-12-15" may additionally assert the weekday of that calendar date. The ledger does not supply that proposition; no external calendar fact is silently added to the reference.'
            alternative='Reading Thursday only as the service-day attribute supports Correct on both axes and task-success=1. A literal date-weekday assertion requires explicit adjudication; unsupported is not automatically Incorrect.'
            adjudication='Resolve service-day wording versus a new calendar assertion. Preserve component coverage=1 and complete delivery separately from whole-response factual uncertainty.'
        elif group=='boundary_unresolved':
            score={k:None for k in FIELDS};score.update(factual_consistency='Unverifiable',temporal_consistency='Unverifiable',semantic_completeness='UNCERTAIN')
            supported=[];unknown=components;confidence='LOW'
            reason=f'{rid}: the frozen candidate span contains USER QUESTION or RECENT CONVERSATION after an answer-looking clause. Stage A does not certify a clean reply boundary. Primary categorical proposals are Unverifiable with reason BOUNDARY_UNSCORABLE; ordinal/delivery/coverage scores remain Missing pending the separate Stage B disposition.'
            alternative='A prefix before the visible header may be evaluable, but selecting that prefix is a separate boundary sensitivity, not a silent replacement of the frozen unit.'
            adjudication='Review the full continuation in Stage B and approve or reject the separately preserved alternative view. Do not replace primary structural status.'
        score_reason={
          'factual_consistency':reason,
          'temporal_consistency':reason+f' Requested date {row["requested_date"]}; evaluation date {row["evaluation_date"]} does not override it.',
          'response_relevance':'Missing because the reply unit is unresolved.' if group=='boundary_unresolved' else ('The response directly addresses the named assignment and all requested fields; factual falsity alone does not reduce relevance.' if score['response_relevance']==5 else 'The assignment topic is addressed, but attribute/calendar wording weakens exact alignment with the question.'),
          'conversational_coherence':'Missing because the reply unit is unresolved.' if group=='boundary_unresolved' else ('A grammatical, self-contained answer follows the fixed request to check an assignment. No missing anaphoric antecedent is evident; truth is scored separately.' if score['conversational_coherence']==5 else 'The reply follows the assignment conversation but introduces an attribute/date phrasing mismatch.'),
          'task_success':'Unknown reply unit; not a binary failure.' if group=='boundary_unresolved' else ('Unknown until calendar wording is adjudicated; both requested values were delivered.' if group=='calendar_wording' else 'All required components supported and delivered under the stated interpretation.' if score['task_success']==1 else 'A final answer was delivered but conflicts with required target components; task failure is not an inference from structure.'),
          'component_coverage':f'Required components: {components}; supported: {supported}; contradicted: {contradicted}; unknown: {unknown}.',
          'semantic_completeness':'Boundary unresolved; do not infer completeness from an answer-looking clause alone.' if group=='boundary_unresolved' else 'A finished declarative answer is delivered. Correctness and attribute/calendar uncertainty do not by themselves make the sentence unfinished.'}
        proposal.append({**row,'proposal_version':'p1c_AI_semantic_proposal_v1','annotation_origin':'AI_assisted_condition_masked_assessment',
            'proposal_status':'UNCONFIRMED','AI_review_group':group,**{'AI_'+k:v for k,v in score.items()},
            'AI_endpoint_explanations':score_reason,'AI_source_quotations':supporting_quotes(row),
            'AI_model_quotation':row['raw_first_reply'],'AI_supported_components':supported,'AI_contradicted_components':contradicted,
            'AI_unknown_components':unknown,'AI_unsupported_extra_claims':extra,'AI_confidence':confidence,
            'AI_alternative_interpretation':alternative,'AI_required_adjudication':adjudication,
            'AI_primary_unit_status':'UNRESOLVED' if group=='boundary_unresolved' else 'PROVISIONALLY_EVALUABLE',
            'researcher_proposal_decision':'','researcher_corrections':'','researcher_review_timestamp':''})
    write_csv(destination/'semantic_proposals_UNCONFIRMED_v1.csv',proposal)
    write(destination/'semantic_proposals_UNCONFIRMED_v1.json',proposal)
    manifest={'version':'p1c_stage_a_proposal_freeze_v1','created_utc':datetime.now(timezone.utc).isoformat(),
        'source':str(SOURCE),'source_sha256':sha(SOURCE),'policy_sha256':sha(POLICY),'records':72,
        'files':{p.name:sha(p) for p in destination.iterdir()},'transcription_code_sha256':sha(__file__),
        'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'source_access':'Only condition-masked semantic rows and public rubrics were read for this new initial assessment; protected mapping and Stage B were not opened before this snapshot.',
        'prior_knowledge':'The same assistant previously implemented execution and has prior conversation knowledge of aggregate structure and some assignments. This is condition-masked input, NOT independently blind assessment. No assignment was inferred from response text.',
        'method':'Item-by-item AI reading, transcribed using explicit ID groups and case-specific references; no numerical classifier or substring correctness scorer.',
        'human_confirmations':0,'reviewer_id':None,'human_review_timestamp':None,'formal_semantic_effects_computed':False}
    write(destination/'freeze_manifest_v1.json',manifest)
    return {'records':72,'primary_evaluable_proposals':64,'boundary_unresolved':8,'human_confirmations':0,
            'factual':dict(Counter(r['AI_factual_consistency'] for r in proposal)),
            'temporal':dict(Counter(r['AI_temporal_consistency'] for r in proposal))}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['stage-a'])
    parser.parse_args();print(json.dumps(stage_a(),indent=2))
