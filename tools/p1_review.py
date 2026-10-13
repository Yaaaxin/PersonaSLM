"""Create immutable P1 control review materials and validate genuine submissions."""
import argparse
from collections import Counter
import csv
from datetime import datetime
import json
from pathlib import Path
from personaslm.journal import atomic_json,utc_now
from personaslm.provenance import fingerprint,sha256,require_local_path

PUBLIC=Path('docs/validation/p1')
VERSION='p1_control_review_v1'
QUESTIONS={
 'answer_leakage':'Does the candidate avoid revealing the expected answer outside shared trusted evidence?',
 'additional_personal_facts':'Does the candidate avoid introducing new personal facts?',
 'contradictory_information':'Does the candidate avoid false or contradictory personal assertions?',
 'unintended_style':'Is the candidate free of an extra target linguistic-style instruction, within the declared absence-control scope?',
 'evidence_question_preservation':'Are trusted evidence, current question and recent context unchanged?',
 'speaker_identity':'Are speaker references clear and consistent?',
 'format_and_length':'Are the required wrapper, insertion position, date/role format and exact total token counts preserved?',
 'declared_scope_suitability':'Is this exact candidate acceptable for the explicitly limited comparison stated in permitted_scope?'}
EDITABLE=[*(f'check_{q}' for q in QUESTIONS),'researcher_decision','reviewer_id','review_assistance','reviewed_utc','evidence_quotations','reviewer_notes']

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;rows=list(reader)
    if not fields or len(fields)!=len(set(fields)) or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError('Malformed CSV columns')
    return fields,rows
def write_csv(path,rows):
    with path.open('x',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def create():
    data=read(Path('data/synthetic/p1_development_v1.json'));cases={r['case_id']:r for r in data['cases']}
    matches=read(PUBLIC/'control_matching_v1.json');manifest=read(PUBLIC/'wave1_manifest_v1.json')
    refs={(r['case_id'],r['condition']):r for r in manifest['requests']};rows=[]
    for pair in matches['results']:
        c=cases[pair['case_id']];candidate=pair['selected'] or pair['best_observed'];ref=refs[(pair['case_id'],pair['reference'])]
        scope=('Specific style information versus explicit absence of style information; not equivalent to C0 or complete semantic neutrality.'
            if pair['condition']=='N_style' else 'Residence history versus unrelated coherent dated dialogue under matched length/format; topic, factual content and temporal information differ.')
        row={'review_version':VERSION,'candidate_id':pair['case_id']+'__'+pair['condition']+'__'+candidate['prompt_sha256'][:12],
            'case_id':pair['case_id'],'persona_id':c['persona_id'],'speaker_name':c['speaker_name'],'scenario_family':c['family'],
            'condition_id':pair['condition'],'reference_condition':pair['reference'],
            'active_intervention':'\n\n'.join(ref['prompt']['additions']),'neutral_text':'\n\n'.join(candidate['prompt']['additions']),
            'trusted_evidence':c['trusted_evidence'],'current_question':c['question'],'fixed_context':'\n'.join(c['context']),
            'reference_date':c['evaluation_date'],'history_date':c['history_date'],'expected_answer':c['expected_answer'] or 'Not Applicable',
            'reference_prompt':ref['prompt']['text'],'candidate_prompt':candidate['prompt']['text'],
            'reference_prompt_sha256':ref['prompt_sha256'],'candidate_prompt_sha256':candidate['prompt_sha256'],
            'reference_tokens':str(pair['reference_tokens']),'candidate_tokens':str(candidate['token_count']),
            'token_difference':str(candidate['difference']),'matching_status':pair['matching_status'],'permitted_scope':scope,
            'review_questions':json.dumps(QUESTIONS,ensure_ascii=False),**{key:'' for key in EDITABLE}}
        rows.append(row)
    packet={'version':VERSION,'source_matching_sha256':sha256(PUBLIC/'control_matching_v1.json'),'items':rows,'human_review_status':'OPEN'}
    packet['packet_id']=fingerprint(packet)
    for row in rows:row['packet_id']=packet['packet_id']
    atomic_json(PUBLIC/'control_review_master_v1.json',packet)
    write_csv(PUBLIC/'control_review_v1.csv',rows)
    print(json.dumps({'control_review_items':len(rows),'human_labels_supplied':0,'version':VERSION}))

def validate(master,fields,rows):
    original={r['candidate_id']:r for r in master['items']}
    if set(fields)!=set(master['items'][0]) or len(rows)!=len(original):raise ValueError('Complete original schema and item count required')
    if len({r['candidate_id'] for r in rows})!=len(rows) or {r['candidate_id'] for r in rows}!=set(original):raise ValueError('Duplicate, missing or unknown candidate ID')
    for row in rows:
        source=original[row['candidate_id']]
        if any(row[k]!=source[k] for k in source if k not in EDITABLE):raise ValueError('Version, packet or source material changed')
        for q in QUESTIONS:
            value=row['check_'+q]
            allowed={'PASS','FAIL','UNCERTAIN'}
            if q=='unintended_style' and row['condition_id']=='N_history':allowed.add('NOT_APPLICABLE')
            if value not in allowed:raise ValueError('Missing or invalid positive-criterion judgment: '+q)
        if row['researcher_decision'] not in {'ACCEPT_NARROW','REVISION_REQUIRED','REJECT_AS_NEUTRAL','DIAGNOSTIC_ONLY','UNCERTAIN'}:
            raise ValueError('Missing or invalid decision')
        if not row['reviewer_id'].strip() or row['review_assistance'] not in {'unaided','AI-assisted','other-disclosed-in-notes'}:
            raise ValueError('Reviewer and assistance provenance required')
        if row['reviewed_utc']:datetime.fromisoformat(row['reviewed_utc'].replace('Z','+00:00'))
        if any(row['check_'+q] in {'FAIL','UNCERTAIN'} for q in QUESTIONS) and not row['evidence_quotations'].strip():
            raise ValueError('Quote the affected source for FAIL/UNCERTAIN')
        if row['researcher_decision']=='ACCEPT_NARROW':
            if row['matching_status']!='PASS' or row['token_difference']!='0':raise ValueError('Cannot adopt unmatched control')
            if any(row['check_'+q]!='PASS' for q in ['answer_leakage','additional_personal_facts','contradictory_information','evidence_question_preservation','speaker_identity','format_and_length','declared_scope_suitability']):
                raise ValueError('Narrow acceptance conflicts with required input/scope judgments; retain source and request clarification')
            if row['condition_id']=='N_style' and row['check_unintended_style']!='PASS':
                raise ValueError('Style-control acceptance conflicts with unintended-style judgment; request clarification')
    return {'version':VERSION,'annotation_count':len(rows),'decisions':dict(Counter(r['researcher_decision'] for r in rows)),
        'rows':rows,'human_review_provenance':'As explicitly supplied; no blind review or agreement inferred','generation_authorized_by_import':False}

def import_review(path,output):
    path=require_local_path(path);output=require_local_path(output)
    fields,rows=csv_rows(path);master=read(PUBLIC/'control_review_master_v1.json');result=validate(master,fields,rows)
    output.mkdir(parents=True,exist_ok=False)
    with (output/'original.csv').open('xb') as stream:stream.write(path.read_bytes())
    atomic_json(output/'registration.json',{**result,'imported_utc':utc_now(),'source_sha256':sha256(path),
        'master_sha256':sha256(PUBLIC/'control_review_master_v1.json')})
    print(json.dumps({'reviewed':len(rows),'decisions':result['decisions']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['create','import']);parser.add_argument('--csv',type=Path);parser.add_argument('--output',type=Path);args=parser.parse_args()
    if args.action=='create':create()
    elif not args.csv or not args.output:parser.error('import requires --csv and --output')
    else:import_review(args.csv,args.output)
