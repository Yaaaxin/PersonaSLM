"""Versioned researcher-decision registration and offline gate; never runs inference."""
import argparse
import ast
import csv
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess

import p1c_design as d

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('docs/validation/p1c/final_review_v1')
PACKAGE = Path('docs/validation/p1c/decision_gate_v1')
MANIFEST = SOURCE/'calibration_manifest_candidate_v1.json'
MANIFEST_SHA = 'b0cf330d9dd5f7b59a186dc298c477a97bd86e06a29209805989a9f399fde02b'
SCHEMA = 'p1c_researcher_decisions_v2'
DECISIONS = ('ACCEPT','ACCEPT_WITH_RESTRICTED_ESTIMAND','DIAGNOSTIC_ONLY','REVISION_REQUIRED','REJECT')
ACCEPTED = set(DECISIONS[:3])
CONTROL_CLASS = 'LENGTH_MATCHED_DIAGNOSTIC_CONTROL'
HUMAN_FIELDS = ('researcher_decision','restriction_reason','reference_answer_valid',
                'no_material_answer_leakage','control_assessment_decision','control_assessment_reason','researcher_notes')
LIMITS = [
    'R replaces auxiliary topic, attribute words and color values; not pure topical relevance.',
    'T replaces validity interval and factual attribute value; not pure temporal validity.',
    'No direct stale target-answer competition is manipulated.',
    'No internal model mechanism is identified by factorial contrasts.',
    'Procedural controls can prime topic/style/chronology; matching tokens does not establish neutrality.',
    'No-history comparisons include length and archive-format changes.',
    'Six speakers / twelve paired development cases are not 72 independent units.',
    'The fixed 96-token budget and first-reply extraction can censor semantic evaluation.'
]


class DecisionError(ValueError):
    def __init__(self, errors):
        self.errors=errors
        super().__init__('; '.join(errors))


def csv_rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise DecisionError(['Missing or duplicate CSV columns'])
        rows=list(reader)
        if any(None in r or any(v is None for v in r.values()) for r in rows):
            raise DecisionError(['Malformed CSV rows'])
        return reader.fieldnames,rows


def decision_json(path):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise DecisionError(['Duplicate JSON field: '+key])
            result[key]=value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique)


def expected_rows():
    cases=d.read(SOURCE/'final_case_review_proposed_v1.json')
    texts=d.read(SOURCE/'final_history_review_proposed_v1.json')
    controls=d.read(SOURCE/'final_neutral_review_proposed_v1.json')
    d.require(controls==[r for r in texts if r['condition']=='N_history'],'Control subset/source mismatch')
    rows=[]
    for kind, entries in [('case',cases),('history_text',texts)]:
        for r in entries:
            rows.append({'schema_version':SCHEMA,'item_type':kind,'item_id':r.get('item_id',r['case_id']),
                'case_id':r['case_id'],'original_condition_id':r.get('condition',''),
                'is_matched_control':'YES' if r.get('condition')=='N_history' else 'NO',
                'source_item_sha256':d.canonical(r),
                'AI_proposal_original':r.get('AI_case_decision',r.get('AI_disposition')),
                **{k:'' for k in HUMAN_FIELDS}})
    d.require(len(rows)==72 and len({r['item_id'] for r in rows})==72,'Review identity/count mismatch')
    return rows


def analysis_spec():
    registry=d.read(SOURCE/'estimand_registry_proposed_v1.json')
    return {'version':'p1c_analysis_restrictions_v1','approval_status':'PENDING_RESEARCHER',
        'manifest_sha256':MANIFEST_SHA,'original_registry_sha256':d.sha(SOURCE/'estimand_registry_proposed_v1.json'),
        'original_weights_unchanged':registry['weights'],'original_condition_ids':registry['condition_order'],
        'limitations':LIMITS,'control_class':CONTROL_CLASS,
        'control_rows':[{'item_id':r['item_id'],'original_condition_id':r['condition'],
                        'analysis_control_class':CONTROL_CLASS,'strict_semantic_neutrality':'NOT_ESTABLISHED'}
                       for r in d.read(SOURCE/'final_neutral_review_proposed_v1.json')],
        'neutral_contrast_scope':'Length/format-matched diagnostic content replacement only, never a fully controlled semantic history effect.',
        'endpoints':['Response Relevance','Factual Consistency','Temporal Consistency','Conversational Coherence',
                     'Task Success','Required-Component Coverage','Semantic Completeness','Structural Response Status','Persona Fidelity'],
        'evaluation_policy_sha256':d.sha(SOURCE/'evaluation_policy_proposed_v1.json'),
        'applicability_sha256':d.sha(SOURCE/'applicability_matrix_v1.json'),
        'categories':['Correct','Incorrect','Unverifiable','Not Applicable','Missing'],
        'statistics':{'paired_cases':12,'speaker_clusters':6,'planned_outputs':72,'scope':'Exploratory development',
                      'cluster_seed':715004,'bootstrap_draws':10000,'leave_one_speaker_out':True,
                      'unverifiable_is_incorrect':False,'incomplete_is_factual_error':False,'composite_score':False},
        'protocol_v1_1_modified':False,'v1_2_adopted':False}


def policy_targets():
    return {
        'restricted_estimands':(PACKAGE/'analysis_restrictions_v1.json').as_posix(),
        'diagnostic_control_policy':(PACKAGE/'analysis_restrictions_v1.json').as_posix(),
        'evaluation_applicability':(SOURCE/'evaluation_policy_proposed_v1.json').as_posix(),
        'statistical_analysis_policy':(SOURCE/'estimand_registry_proposed_v1.json').as_posix(),
        'protocol_addendum':(SOURCE/'protocol_addendum_proposed_v2.json').as_posix()}


def approval_template():
    return {'schema_version':'p1c_scientific_approval_v1','manifest_sha256':MANIFEST_SHA,
        'reviewer_id':'','review_status':'','decision_source':'','review_method':'',
        'review_timestamp':None,'confirmation_statement':'',
        'policy_decisions':[{'policy_id':k,'source_path':p,'source_sha256':d.sha(p),'decision':'','reason':''}
                            for k,p in policy_targets().items()]}


def authorization_template():
    return {'schema_version':'p1c_execution_authorization_v1','manifest_sha256':MANIFEST_SHA,
        'registration_sha256':'','request_count':72,'authorization_decision':'',
        'reviewer_id':'','decision_source':'','authority_statement':'','authorization_timestamp':None}


def prepare():
    if PACKAGE.exists():raise FileExistsError('Decision package exists; do not overwrite')
    d.require(d.sha(MANIFEST)==MANIFEST_SHA,'Frozen manifest hash differs')
    rows=expected_rows()
    d.write_json(PACKAGE/'analysis_restrictions_v1.json',analysis_spec())
    d.write_csv(PACKAGE/'researcher_item_decisions_v2.csv',rows)
    d.write_json(PACKAGE/'scientific_approval_template_v1.json',approval_template())
    d.write_json(PACKAGE/'execution_authorization_template_v1.json',authorization_template())
    paths=[p for p in SOURCE.rglob('*') if p.is_file()]+[Path(d.read(MANIFEST)['dataset']),
        Path('docs/validation/p1c/proposed_v2/selected_prompts_v2.json'),
        Path('docs/validation/p1c/proposed_v2/configuration_proposal_v2.json'),
        Path('docs/validation/p1c/scientific_review_v1/native_reverification_v1.json'),
        Path('docs/validation/p1c/scientific_review_v1/reproducibility_manifest_v1.json'),
        Path('tools/p1c_design.py'),Path('docs/research_protocol_v1.1.md')]
    paths += list(PACKAGE.glob('*'))
    d.write_json(PACKAGE/'source_pins_v1.json',{'version':'p1c_decision_source_pins_v1',
        'manifest_sha256':MANIFEST_SHA,'files':{p.as_posix():d.sha(p) for p in paths},
        'excluded_mutable_history_document':'docs/research_development_log.md; previous snapshot remains pinned',
        'new_generations':0})
    print(json.dumps({'unique_items':len(rows),'control_subset':12,'human_decisions':0,'execution':'NO_GO'}))


def check_timestamp(value, label, errors):
    if value in ('',None):return
    try:datetime.fromisoformat(value.replace('Z','+00:00'))
    except (ValueError,AttributeError):errors.append(label+': invalid recorded timestamp')


def validate_decisions(rows, approval):
    if not isinstance(rows,list) or any(not isinstance(r,dict) or any(not isinstance(v,str) for v in r.values()) for r in rows):
        raise DecisionError(['Decision rows must be CSV string-valued records'])
    if not isinstance(approval,dict):raise DecisionError(['Scientific approval must be an object'])
    errors=[];expected={r['item_id']:r for r in expected_rows()};seen=set();blockers=[]
    if len(rows)!=72:errors.append(f'Expected 72 unique item rows, found {len(rows)}')
    for r in rows:
        item=r.get('item_id','<missing>')
        if item in seen:errors.append(item+': duplicate ID')
        seen.add(item)
        if item not in expected:errors.append(item+': unknown ID');continue
        ref=expected[item]
        if set(r)!=set(ref):errors.append(item+': schema columns differ');continue
        for k in set(ref)-set(HUMAN_FIELDS):
            if r[k]!=ref[k]:errors.append(item+': immutable source field differs: '+k)
        decision=r['researcher_decision']
        if decision not in DECISIONS:errors.append(item+': missing/invalid mandatory decision')
        if decision in set(DECISIONS)-{'ACCEPT'} and not r['restriction_reason'].strip():
            errors.append(item+': specific restriction/revision/rejection reason required')
        for field in ('reference_answer_valid','no_material_answer_leakage'):
            if r[field] not in ('YES','NO','UNCERTAIN'):errors.append(item+': missing/invalid '+field)
            elif r[field]!='YES':
                blockers.append(item+': REVISION_REQUIRED: '+field+'='+r[field])
                if decision in ACCEPTED:errors.append(item+': acceptance contradicts '+field)
        control=r['is_matched_control']=='YES'
        if control:
            if r['control_assessment_decision'] not in ('DIAGNOSTIC_ONLY','REVISION_REQUIRED','REJECT'):
                errors.append(item+': unvalidated control must be DIAGNOSTIC_ONLY, REVISION_REQUIRED or REJECT')
            if not r['control_assessment_reason'].strip():errors.append(item+': control restriction reason required')
            if decision in ACCEPTED and r['control_assessment_decision'] in ('REVISION_REQUIRED','REJECT'):
                errors.append(item+': accepted text contradicts control assessment')
            if decision in ('REVISION_REQUIRED','REJECT') and r['control_assessment_decision']=='DIAGNOSTIC_ONLY':
                errors.append(item+': diagnostic acceptance contradicts rejected/unresolved text')
        elif r['control_assessment_decision'] or r['control_assessment_reason']:
            errors.append(item+': control fields must be empty for non-control items')
        if decision not in ACCEPTED:blockers.append(item+': '+(decision or 'MISSING'))
    if set(expected)-seen:errors.append('Missing IDs: '+', '.join(sorted(set(expected)-seen)))
    template=approval_template()
    if set(approval)!=set(template):errors.append('Scientific approval schema differs')
    for key,value in {'schema_version':'p1c_scientific_approval_v1','manifest_sha256':MANIFEST_SHA,
                      'reviewer_id':'Yaxin_ZHENG','review_status':'RESEARCHER_CONFIRMED','decision_source':'researcher',
                      'review_method':'Researcher review of AI-assisted scientific proposals'}.items():
        if approval.get(key)!=value:errors.append('Scientific approval missing/invalid '+key)
    if not isinstance(approval.get('confirmation_statement'),str) or not approval['confirmation_statement'].strip():
        errors.append('Explicit researcher confirmation statement required')
    check_timestamp(approval.get('review_timestamp'),'Scientific approval',errors)
    policies=approval.get('policy_decisions',[])
    if not isinstance(policies,list):errors.append('policy_decisions must be a list');policies=[]
    refs={r['policy_id']:r for r in template['policy_decisions']};policy_seen=set()
    for p in policies:
        if not isinstance(p,dict):errors.append('Invalid policy row');continue
        key=p.get('policy_id')
        if not isinstance(key,str):errors.append('Policy ID must be a string');continue
        if key in policy_seen:errors.append('Duplicate policy: '+str(key))
        policy_seen.add(key)
        if key not in refs or set(p)!=set(refs[key]):errors.append('Unknown/invalid policy row: '+str(key));continue
        for field in ('source_path','source_sha256'):
            if p[field]!=refs[key][field]:errors.append(key+': approved source binding differs')
        if p['decision'] not in ('APPROVE','DECLINE','DEFER'):errors.append(key+': missing/invalid policy decision')
        if not isinstance(p['reason'],str) or not p['reason'].strip():errors.append(key+': policy scope/reason required')
        if p['decision']!='APPROVE':blockers.append(key+': '+(p['decision'] or 'MISSING'))
    if set(refs)!=policy_seen:errors.append('Required policy decisions missing or unexpected')
    if errors:raise DecisionError(errors)
    return {'valid_unique_item_decisions':72,'case_decisions':12,'history_text_decisions':60,
            'control_assessments':12,'control_assessments_are_subset':True,'scientific_policy_decisions':5,
            'blockers':blockers,'scientific_gate':'PASS' if not blockers else 'NO_GO'}


def verify_sources(check_binaries=True):
    pins=d.read(PACKAGE/'source_pins_v1.json')
    for p,h in pins['files'].items():d.require(d.sha(p)==h,'Pinned source changed: '+p)
    d.require(d.sha(MANIFEST)==MANIFEST_SHA,'Frozen manifest hash mismatch')
    m=d.read(MANIFEST);data=d.read(m['dataset']);cfg=d.read(m['source_configuration'])
    d.require(d.sha(m['dataset'])==m['dataset_sha256'],'Dataset hash mismatch')
    cases={c['case_id']:c for c in data['cases']};d.validate_cases(data)
    selected=d.read('docs/validation/p1c/proposed_v2/selected_prompts_v2.json')['records']
    by_key={(r['case_id'],r['condition']):r for r in selected}
    d.require(len(m['requests'])==len(by_key)==72 and len(cases)==12,'Request/case count mismatch')
    d.require(len({c['persona_id'] for c in cases.values()})==6,'Speaker count mismatch')
    d.require([r['request_identity'] for r in m['requests']]==cfg['proposed_order'],'Order mismatch')
    for r in m['requests']:
        key=tuple(r['request_identity']);c=cases[r['case_id']]
        d.require({k:r[k] for k in by_key[key]}==by_key[key],'Selected request changed')
        d.require(r['factor_assignment']==d.CONDITIONS[r['condition']],'Factor assignment differs')
        d.require(d.render(c,r['history'])==r['prompt'],'Prompt reconstruction mismatch')
        d.require(r['reference']==c['reference'] and r['applicability']==c['applicability'],'Reference/applicability mismatch')
        d.require(r['evaluation_date']==c['evaluation_date'] and r['requested_date']==c['requested_date'],'Date mismatch')
        d.require(len(r['input_token_ids'])==r['input_tokens'] and r['input_tokens']+96<=4096,'Context/token mismatch')
    proof=d.read('docs/validation/p1c/scientific_review_v1/reproducibility_manifest_v1.json')['native_recheck_logs']
    by_hash={r['prompt_sha256']:r for r in selected}
    for p,h in proof.items():
        d.require(d.sha(p)==h,'Tokenizer raw log changed');log=d.read(p);r=by_hash[log['prompt_sha256']]
        d.require(log['prompt']==r['prompt'] and ast.literal_eval(log['stdout'].strip())==r['input_token_ids'],'Native token evidence mismatch')
    if check_binaries:
        ident=m['tokenizer_identity'];root=Path(m['backend_file']).parent
        targets=[(Path(m['model_file']),ident['model_sha256']),(Path(m['backend_file']),ident['backend_sha256']),
                 (root/'llama-tokenize.exe',ident['tokenizer_sha256'])]+[(root/k,v) for k,v in ident['dll_hashes'].items()]
        for p,h in targets:d.require(d.sha(p)==h,'Model/backend/tokenizer identity differs: '+str(p))
    return {'status':'PASS','source_files':len(pins['files']),'cases':12,'history_texts':60,'control_subset':12,
            'requests':72,'original_order':'PASS','actual_tokenizer_ID_records':72,
            'binary_identity':'PASS' if check_binaries else 'NOT_CHECKED','new_generations':0}


def register(items_path,approval_path,output):
    output=Path(output)
    if output.exists():raise FileExistsError('Registration destination exists; preserve prior versions')
    verify_sources()
    _,rows=csv_rows(items_path);approval=decision_json(approval_path)
    result=validate_decisions(rows,approval)  # All-or-nothing validation before any registration.
    output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(items_path,output/'researcher_decisions_source.csv')
    shutil.copyfile(approval_path,output/'scientific_approval_source.json')
    d.write_json(output/'registered_decisions_v1.json',{'schema_version':SCHEMA,'rows':rows,
        'scientific_approval':approval,'reviewer_id':'Yaxin_ZHENG','final_decision_authority':'researcher',
        'provenance':'Researcher review and correction/adoption of AI-assisted proposals; not independent two-annotator review.',
        'review_timestamp':approval['review_timestamp'],'validated_counts':result})
    files={p.name:d.sha(p) for p in output.iterdir() if p.is_file()}
    registration={'version':'p1c_decision_registration_v1','registered_utc':d.now(),'review_timestamp':approval['review_timestamp'],
        'manifest_sha256':MANIFEST_SHA,'analysis_restrictions_sha256':d.sha(PACKAGE/'analysis_restrictions_v1.json'),
        'source_pins_sha256':d.sha(PACKAGE/'source_pins_v1.json'),'importer_sha256':d.sha(Path(__file__)),
        'git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'git_dirty_status':subprocess.check_output(['git','status','--short'],text=True),'files':files,
        'validation':result,'inference_authorized':False,'new_generations':0}
    d.write_json(output/'registration_v1.json',registration)
    d.write_json(output/'registration_receipt_v1.json',{'registration_sha256':d.sha(output/'registration_v1.json')})
    return registration


def load_registration(path):
    path=Path(path);reg=decision_json(path);receipt=decision_json(path.parent/'registration_receipt_v1.json')
    d.require(d.sha(path)==receipt['registration_sha256'],'Registration receipt mismatch')
    d.require(reg['manifest_sha256']==MANIFEST_SHA,'Registration manifest binding mismatch')
    d.require(reg['source_pins_sha256']==d.sha(PACKAGE/'source_pins_v1.json'),'Registration source binding mismatch')
    d.require(reg['analysis_restrictions_sha256']==d.sha(PACKAGE/'analysis_restrictions_v1.json'),'Analysis restriction binding mismatch')
    d.require(reg['version']=='p1c_decision_registration_v1','Registration version mismatch')
    d.require(set(reg['files'])=={'researcher_decisions_source.csv','scientific_approval_source.json','registered_decisions_v1.json'},'Registration file inventory mismatch')
    for name,h in reg['files'].items():
        d.require(Path(name).name==name,'Unsafe registration path')
        d.require(d.sha(path.parent/name)==h,'Registered file changed: '+name)
    _,rows=csv_rows(path.parent/'researcher_decisions_source.csv');approval=decision_json(path.parent/'scientific_approval_source.json')
    result=validate_decisions(rows,approval);snapshot=decision_json(path.parent/'registered_decisions_v1.json')
    d.require(snapshot['rows']==rows and snapshot['scientific_approval']==approval,'Registered/source decisions differ')
    d.require(reg['validation']==result,'Registered decision counts/blockers differ')
    return result


def validate_authorization(auth,registration_sha):
    if not isinstance(auth,dict):raise DecisionError(['Authorization must be an object'])
    errors=[];template=authorization_template()
    if set(auth)!=set(template):errors.append('Authorization schema differs')
    exact={'schema_version':'p1c_execution_authorization_v1','manifest_sha256':MANIFEST_SHA,
           'registration_sha256':registration_sha,'reviewer_id':'Yaxin_ZHENG','decision_source':'researcher'}
    for k,v in exact.items():
        if auth.get(k)!=v:errors.append('Authorization binding/identity invalid: '+k)
    if type(auth.get('request_count')) is not int or auth['request_count']!=72:errors.append('Authorization must specify exactly 72 requests')
    if auth.get('authorization_decision') not in ('AUTHORIZE_72_REQUESTS','DECLINE','DEFER'):
        errors.append('Explicit execution authorization decision required')
    if not isinstance(auth.get('authority_statement'),str) or not auth['authority_statement'].strip():
        errors.append('Explicit researcher authority statement required')
    check_timestamp(auth.get('authorization_timestamp'),'Authorization',errors)
    if errors:raise DecisionError(errors)
    return auth['authorization_decision']=='AUTHORIZE_72_REQUESTS'


def gate(registration=None,authorization=None):
    checks={};blockers=[];valid=0;control_count=0;policies=0
    try:checks['technical']=verify_sources()
    except (ValueError,OSError,KeyError) as exc:
        checks['technical']={'status':'FAIL','error':str(exc)};blockers.append('Mandatory technical/source verification failed')
    if registration:
        try:
            review=load_registration(registration);valid=review['valid_unique_item_decisions'];control_count=review['control_assessments'];policies=5
            checks['scientific']=review;blockers.extend(review['blockers'])
        except (ValueError,OSError,KeyError) as exc:
            blockers.append('Invalid scientific registration: '+str(exc));checks['scientific']={'status':'INVALID'}
    else:
        blockers.extend(['72 unique researcher item decisions missing (12 cases, 60 texts)',
                         '12 linked diagnostic-control assessments missing; not 12 extra observations',
                         'Five scientific policy decisions missing'])
        checks['scientific']={'status':'PENDING'}
    authorized=False
    if authorization and registration and valid==72:
        try:authorized=validate_authorization(decision_json(authorization),d.sha(registration))
        except (ValueError,OSError,KeyError) as exc:blockers.append('Invalid authorization: '+str(exc))
    if not authorized:blockers.append('Separate explicit authorization for the exact 72-request manifest/registration is absent or not granted')
    checks['authorization']={'status':'AUTHORIZED' if authorized else 'PENDING_OR_NOT_GRANTED'}
    if authorization and Path(authorization).is_file():
        checks['authorization']['source_path']=str(authorization)
        checks['authorization']['source_sha256']=d.sha(authorization)
        checks['authorization']['original_source_text']=Path(authorization).read_text(encoding='utf-8-sig')
    return {'version':'p1c_execution_gate_v1','evaluated_utc':d.now(),'status':'GO' if not blockers else 'NO_GO',
        'valid_registered_unique_decisions':valid,'unregistered_unique_decisions':72-valid,
        'registered_control_assessments_subset':control_count,'unregistered_control_assessments_subset':12-control_count,
        'registered_scientific_policy_decisions':policies,'checks':checks,'blockers':blockers,
        'control_class':CONTROL_CLASS,'manifest_sha256':MANIFEST_SHA,
        'generation_requests_executed':0,'scope':'Offline gate only. GO never launches a model; runtime logging/disk/resume preflight remains required at an authorized execution.',
        'approval_is_not_inferred_from_form_presence':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('prepare')
    for action in ('validate','register'):
        p=sub.add_parser(action);p.add_argument('--items',type=Path,required=True);p.add_argument('--approval',type=Path,required=True)
        if action=='register':p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('gate');p.add_argument('--registration',type=Path);p.add_argument('--authorization',type=Path);p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.action=='prepare':prepare();return
        if args.action=='validate':verify_sources();_,rows=csv_rows(args.items);result=validate_decisions(rows,decision_json(args.approval))
        elif args.action=='register':result=register(args.items,args.approval,args.output)
        else:
            if args.output.exists():raise FileExistsError('Gate report exists; use a new destination')
            result=gate(args.registration,args.authorization);d.write_json(args.output,result)
        print(json.dumps(result,indent=2))
        if args.action=='gate' and result['status']!='GO':raise SystemExit(2)
    except (ValueError,OSError,KeyError) as exc:
        print(json.dumps({'status':'REJECTED','errors':getattr(exc,'errors',[str(exc)]),'registered':False,'new_generations':0},indent=2))
        raise SystemExit(2)


if __name__=='__main__':main()
