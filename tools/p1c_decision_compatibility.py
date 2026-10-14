"""Lossless scoped legacy registration and one three-item approval gate. No inference."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess

import p1c_decisions as p
import p1c_design as d

VERSION = 'p1c_legacy_scope_compatibility_v1'
BUNDLE = Path('PersonaSLM_P1c_Researcher_Confirmed_Registration_v1')
MANIFEST_REL = Path('docs/validation/p1c/final_review_v1/researcher_confirmation_manifest_v1.json')
OUTPUT = Path('docs/validation/p1c/decision_compatibility_v1')
PENDING = {'evaluation_and_statistics': 'PENDING_DOCUMENT_REVIEW',
           'protocol_addendum': 'PENDING_DOCUMENT_REVIEW',
           'execution_authorization': 'NO_GO_PENDING_EXPLICIT_AUTHORIZATION'}
ORIGINALS = {'confirmation': p.SOURCE/'researcher_confirmation_form_v1.csv',
             'cases': Path('docs/validation/p1c/scientific_review_v1/case_review_v1.csv'),
             'history': Path('docs/validation/p1c/scientific_review_v1/history_text_review_v1.csv')}


def derive(row):
    """Derive an operational category only from the explicitly restricted adoption."""
    label = row['researcher_decision']
    result = {'item_id': row['item_id'], 'original_researcher_decision': label,
              'original_confirmation_status': row['review_confirmation_status'],
              'operational_category': None, 'derivation_origin': 'software_compatibility_not_new_human_choice',
              'basis_verbatim': row['researcher_notes'], 'scope_verbatim': row['AI_scope_v1'],
              'original_record': row, 'issue': ''}
    if row['review_confirmation_status'] != 'RESEARCHER_CONFIRMED':
        result['issue'] = 'PENDING_RESEARCHER_DECISION'
        return result
    if label == 'ACCEPT_WITH_LIMITATIONS':
        supported = (row['item_type'] == 'history_text'
                     and row['item_id'].rsplit('/', 1)[-1] in ('R0T0','R0T1','R1T0','R1T1')
                     and row['AI_scope_v1'] == 'R_T_TEXT_PACKAGE_DEVELOPMENT_ONLY'
                     and 'package-level interpretation' in row['researcher_notes']
                     and 'Not an independently identified mechanism' in row['researcher_notes']
                     and 'Do not claim isolated mechanism or stale-answer competition.' in row['AI_case_specific_reason_v1'])
        if supported:
            result['operational_category'] = 'ACCEPT_WITH_RESTRICTED_ESTIMAND'
        else:
            result['issue'] = 'UNRESOLVED_SEMANTIC_MAPPING; original approval retained'
    elif label in p.DECISIONS:
        result['operational_category'] = label
    else:
        result['issue'] = 'UNSUPPORTED_ORIGINAL_LABEL; original retained'
    return result


def inspect_bundle(root, flat_snapshot=False):
    root = Path(root)
    m = p.decision_json(root/('manifest.json' if flat_snapshot else MANIFEST_REL))
    dest = m['relative_repository_destination']
    d.require(set(dest) == {'unified','confirmation','cases','history','report','manifest'}, 'Bundle inventory differs')
    paths = {}
    for key, rel in dest.items():
        path = (root/(key+Path(rel).suffix if flat_snapshot else rel)).resolve()
        d.require(path.is_relative_to(root.resolve()), 'Unsafe bundle path')
        paths[key] = path
    for key, path in ORIGINALS.items():
        d.require(d.sha(path) == m['sources_sha256'][key], 'Original source hash mismatch: '+key)
    tables = {}
    for key, sha in m['generated_csv_sha256'].items():
        d.require(key in ('unified','confirmation','cases','history'), 'Unexpected source table')
        d.require(d.sha(paths[key]) == sha, 'Supplied CSV hash mismatch: '+key)
        tables[key] = p.csv_rows(paths[key])
    d.require(set(tables) == {'unified','confirmation','cases','history'}, 'Missing supplied table')
    comparisons = 0
    for key, path in ORIGINALS.items():
        fields, old = p.csv_rows(path); newfields, new = tables[key]
        idkey = 'case_id' if key == 'cases' else 'item_id'
        refs = {r[idkey]: r for r in old}
        d.require(fields == newfields and len(new) == len(old), 'Schema/count mismatch: '+key)
        d.require(len({r[idkey] for r in new}) == len(new) and {r[idkey] for r in new} == set(refs), 'ID mismatch: '+key)
        for row in new:
            for field, value in refs[row[idkey]].items():
                if field.startswith('researcher_') or field in ('reviewer_id','review_timestamp'):
                    continue
                d.require(row[field] == value, f'Non-annotation mismatch: {key}/{row[idkey]}/{field}')
                comparisons += 1
    confirmed = tables['confirmation'][1]; unified = tables['unified'][1]
    byid = {r['item_id']: r for r in unified}
    d.require(len(unified) == len(byid) == 77, 'Expected 77 unique entries')
    expected_ids = {r['item_id'] for r in p.expected_rows()} | set(PENDING) | {'operational_scope','neutral_scope'}
    d.require(set(byid) == expected_ids, 'Bundle identities differ from frozen review')
    for row in confirmed:
        item = row['item_id']; u = byid[item]
        d.require(all(u[k] == v for k,v in row.items()), 'Unified/confirmation discrepancy: '+item)
        if item in PENDING:
            d.require(u['review_confirmation_status'] == 'RESEARCHER_ACKNOWLEDGED_PENDING'
                      and u['researcher_decision'] == PENDING[item], 'Pending decision changed: '+item)
        else:
            d.require(u['review_confirmation_status'] == 'RESEARCHER_CONFIRMED'
                      and u['reviewer_id'] == 'Yaxin_ZHENG', 'Unconfirmed decision: '+item)
            d.require(u['researcher_notes'].strip() and u['AI_case_specific_reason_v1'].strip(), 'Missing original scope: '+item)
        d.require(u['annotation_provenance'] == 'AI_ASSISTED_PROPOSAL__RESEARCHER_REVIEWED', 'Provenance mismatch')
        p.check_timestamp(u['review_timestamp'], item, errors := [])
        d.require(not errors, '; '.join(errors))
    for key in ('cases','history'):
        for row in tables[key][1]:
            item = row['case_id'] if key == 'cases' else row['case_id']+'/'+row['condition']
            for field in ('researcher_decision','researcher_notes','reviewer_id'):
                d.require(row[field] == byid[item][field], 'Cross-file decision discrepancy: '+item+'/'+field)
            if 'review_timestamp' in row:
                d.require(row['review_timestamp'] == byid[item]['review_timestamp'], 'Cross-file timestamp discrepancy: '+item)
            subfields = [k for k in row if k.startswith('researcher_') and k not in ('researcher_decision','researcher_notes')]
            d.require(all(row[k] == '' for k in subfields), 'Unexpected subcriterion rating; inspect explicitly: '+item)
    counts = dict(Counter(r['item_type']+'__'+r['researcher_decision'] for r in confirmed))
    d.require(counts == m['decision_counts'], 'Declared decision counts differ')
    d.require(m['confirmed_scoped_decisions'] == 74 and m['acknowledged_not_approved'] == 3
              and m['inference_execution_authorized'] is False, 'Declared gate counts/authorization differ')
    derived = [derive(r) for r in unified]
    unresolved = [r['item_id'] for r in derived if (r['issue'] or r['operational_category'] in ('REJECT','REVISION_REQUIRED')) and r['item_id'] not in PENDING]
    controls = [r for r in derived if r['item_id'].endswith('/N_history')]
    d.require(len(controls) == 12 and all(r['original_researcher_decision'] == 'DIAGNOSTIC_ONLY' for r in controls), 'Control scope would broaden')
    d.require(byid['neutral_scope']['researcher_decision'] == 'DIAGNOSTIC_ONLY'
              and byid['operational_scope']['researcher_decision'] == 'ACCEPT_WITH_RESTRICTED_ESTIMAND', 'Global approved scope differs')
    result = {'version': VERSION, 'entries':77, 'confirmed_scoped_decisions':74, 'pending_decisions':PENDING,
              'cases':12, 'history_texts':60, 'control_assessments_subset':12, 'global_scopes':2,
              'derived_legacy_categories':sum(r['original_researcher_decision'] == 'ACCEPT_WITH_LIMITATIONS'
                                             and bool(r['operational_category']) for r in derived),
              'unresolved_compatibility_records':unresolved, 'non_annotation_fields_compared':comparisons,
              'non_annotation_mismatches':0, 'decision_counts':counts,
              'unrated_subcriteria':'Original blanks retained; no new item-review gate or invented YES ratings.',
              'unverified_declared_sources':{k:v for k,v in m['sources_sha256'].items() if k not in ORIGINALS},
              'unverified_declaration_note':'External original proposal/report not separately supplied. Their declarations are retained, not claimed independently hash-verified.',
              'inference_authorized':False}
    return result, derived, paths


def register(root, output):
    output = Path(output)
    if output.exists(): raise FileExistsError('Preserve previous registration; choose a new version')
    technical = p.verify_sources()
    result, rows, paths = inspect_bundle(root)
    # Keep even a semantically unmappable original record; affected usage remains blocked.
    output.mkdir(parents=True, exist_ok=False)
    for key, path in paths.items():
        shutil.copyfile(path, output/(key+path.suffix))
    d.write_json(output/'registered_decisions_v1.json', {'version':VERSION,'rows':rows,'validation':result,
        'reviewer_id':'Yaxin_ZHENG','final_decision_authority':'researcher',
        'review_method':'Researcher review and adoption of AI-assisted proposals; not independent double annotation.',
        'review_timestamp':None,'timestamp_note':'No human timestamp supplied; registration time is recorded separately.'})
    d.write_csv(output/'operational_decisions_v1.csv', [{k:v for k,v in r.items() if k != 'original_record'} for r in rows])
    reg = {'version':VERSION,'registered_utc':d.now(),'validation':result,'technical':technical,
           'manifest_sha256':p.MANIFEST_SHA,'source_pins_sha256':d.sha(p.PACKAGE/'source_pins_v1.json'),
           'importer_sha256':d.sha(Path(__file__)),
           'original_source_files':{path.relative_to(p.ROOT).as_posix():d.sha(path) for path in paths.values()},
           'files':{f.name:d.sha(f) for f in output.iterdir() if f.is_file()},
           'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
           'git_status':subprocess.check_output(['git','status','--short'],text=True), 'new_generations':0}
    d.write_json(output/'registration_v1.json',reg)
    d.write_json(output/'registration_receipt_v1.json',{'registration_sha256':d.sha(output/'registration_v1.json')})
    return reg


def load_registration(path):
    path=Path(path);reg=p.decision_json(path)
    d.require(reg['version']==VERSION and reg['manifest_sha256']==p.MANIFEST_SHA,'Registration version/manifest mismatch')
    d.require(d.sha(path)==p.decision_json(path.parent/'registration_receipt_v1.json')['registration_sha256'],'Receipt mismatch')
    d.require(reg['source_pins_sha256']==d.sha(p.PACKAGE/'source_pins_v1.json'),'Source pins changed')
    expected={'unified.csv','confirmation.csv','cases.csv','history.csv','report.md','manifest.json','registered_decisions_v1.json','operational_decisions_v1.csv'}
    d.require(set(reg['files'])==expected,'Snapshot inventory mismatch')
    for name,sha in reg['files'].items():
        d.require(d.sha(path.parent/name)==sha,'Snapshot changed: '+name)
    snapshot=p.decision_json(path.parent/'registered_decisions_v1.json')
    validated,derived,_=inspect_bundle(path.parent,flat_snapshot=True)
    d.require(snapshot['rows']==derived, 'Derived/original decisions differ')
    d.require(snapshot['validation']==reg['validation']==validated,'Registration summary differs')
    for source,sha in reg['original_source_files'].items():
        d.require(d.sha(source)==sha,'Original source changed: '+source)
    return reg


def policy_audit():
    """Audit all registered formulas and applicability against actual frozen requests."""
    manifest=p.decision_json(p.MANIFEST)
    registry=p.decision_json(p.SOURCE/'estimand_registry_proposed_v1.json')
    rubric=p.decision_json(p.SOURCE/'evaluation_policy_proposed_v1.json')
    matrix=p.decision_json(p.SOURCE/'applicability_matrix_v1.json')
    addendum=p.decision_json(p.SOURCE/'protocol_addendum_proposed_v2.json')
    order=['R0T0','R0T1','R1T0','R1T1','N_history','H_none']
    d.require(registry['condition_order']==order,'Condition order changed')
    expected={'R':[-.5,-.5,.5,.5,0,0], 'T':[-.5,.5,-.5,.5,0,0], 'RxT':[1,-1,-1,1,0,0]}
    pairs=[('R1T0','R0T0'),('R1T1','R0T1'),('R0T1','R0T0'),('R1T1','R1T0')]
    pairs += [(a,b) for b in ('N_history','H_none') for a in order[:4]]+[('N_history','H_none')]
    for a,b in pairs:expected[a+'-'+b]=[int(c==a)-int(c==b) for c in order]
    d.require(set(expected)==set(registry['weights']), 'Sixteen contrast inventory differs')
    for name,weights in expected.items():
        d.require([registry['weights'][name][c] for c in order]==weights, 'Contrast formula differs: '+name)
    cases={r['case_id'] for r in manifest['requests']}
    keys={(r['case_id'],r['condition']) for r in manifest['requests']}
    d.require(len(matrix)==72 and {(r['case_id'],r['condition']) for r in matrix}==keys,'Applicability routing mismatch')
    for row in matrix:
        req=next(r for r in manifest['requests'] if r['case_id']==row['case_id'] and r['condition']==row['condition'])
        d.require(row['persona_fidelity'] is False,'Fidelity has no reference')
        d.require({k:v for k,v in row.items() if k not in ('case_id','condition','persona_fidelity')}==req['applicability'],'Applicability changed')
    entries=registry.get('registry',registry.get('contrasts',[]))
    if not entries:
        entries=next(v for v in registry.values() if isinstance(v,list) and v and isinstance(v[0],dict) and 'contrast_id' in v[0])
    d.require(len(entries)==16,'Detailed contrast inventory mismatch')
    for row in entries:
        d.require(row['weights']==registry['weights'][row['contrast_id']] and set(row['eligible_case_ids'])==cases,'Detailed contrast mismatch')
    d.require(rubric['statistics']['seed']==registry['uncertainty']['bootstrap_seed']==715004,'Bootstrap seed differs')
    d.require(rubric['statistics']['replicates']==registry['uncertainty']['replicates']==10000,'Bootstrap draws differ')
    d.require(addendum['interventions']==d.CONDITIONS and addendum['budget']==96,'Addendum intervention/config mismatch')
    d.require(Path(addendum['evaluation'])==p.SOURCE/'evaluation_policy_proposed_v1.json'
              and Path(addendum['estimands'])==p.SOURCE/'estimand_registry_proposed_v1.json','Addendum policy references differ')
    return {'status':'PASS','contrasts_checked':16,'applicability_rows':72,'cases':12,'speakers':6,
            'applicable_counts':{k:sum(r[k] for r in matrix) for k in matrix[0] if k not in ('case_id','condition')},
            'condition_ids':order,'weights':registry['weights'],'policy_change_required':False,
            'interpretation':'Package effects only; six speaker clusters; exploratory development; no composite or population significance.',
            'pending_policy_approval':True,'new_generations':0}


def approval_template(registration):
    reg=load_registration(registration)
    files=[p.SOURCE/'evaluation_policy_proposed_v1.json',p.SOURCE/'estimand_registry_proposed_v1.json',
           p.SOURCE/'applicability_matrix_v1.json',p.PACKAGE/'analysis_restrictions_v1.json']
    targets={'evaluation_and_statistics':files,
             'protocol_addendum':[p.SOURCE/'protocol_addendum_proposed_v2.json'],
             'execution_authorization':[p.MANIFEST]}
    return {'version':'p1c_consolidated_approval_v1','registration_sha256':d.sha(registration),
            'manifest_sha256':reg['manifest_sha256'],'request_count':72,
            'reviewer_id':'','decision_source':'','confirmation_statement':'','review_timestamp':None,
            'decisions':[{'item_id':key,'documents':[{'path':f.as_posix(),'sha256':d.sha(f)} for f in value],
                          'decision':'','reason':''} for key,value in targets.items()]}


def validate_approval(record, registration):
    ref=approval_template(registration); errors=[]
    if not isinstance(record,dict) or set(record)!=set(ref):raise p.DecisionError(['Consolidated approval schema differs'])
    for key in ('version','registration_sha256','manifest_sha256','request_count'):
        if record[key]!=ref[key] or type(record[key]) is not type(ref[key]): errors.append('Approval binding differs: '+key)
    if record['reviewer_id']!='Yaxin_ZHENG' or record['decision_source']!='researcher':errors.append('Explicit researcher identity/source required')
    if not isinstance(record['confirmation_statement'],str) or not record['confirmation_statement'].strip():errors.append('Explicit confirmation statement required')
    p.check_timestamp(record['review_timestamp'],'Approval timestamp',errors)
    rows=record['decisions']; expected={r['item_id']:r for r in ref['decisions']}; seen=set();blockers=[]
    if not isinstance(rows,list):raise p.DecisionError(['Decisions must be a list'])
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('item_id'),str):errors.append('Malformed approval item');continue
        key=row['item_id']
        if key not in expected or key in seen:errors.append('Duplicate/unexpected approval item: '+key);continue
        seen.add(key)
        if set(row)!=set(expected[key]) or row.get('documents')!=expected[key]['documents']:errors.append('Approved document binding differs: '+key)
        positive='AUTHORIZE_72_REQUESTS' if key=='execution_authorization' else 'APPROVE'
        if row.get('decision') not in (positive,'DECLINE','DEFER'):errors.append('Explicit decision required: '+key)
        if not isinstance(row.get('reason'),str) or not row['reason'].strip():errors.append('Scope/reason required: '+key)
        if row.get('decision')!=positive:blockers.append(key+': '+str(row.get('decision')))
    if seen!=set(expected):errors.append('Exactly three approval decisions required')
    if errors:raise p.DecisionError(errors)
    return blockers


def gate(registration, approval=None):
    reg=load_registration(registration)
    technical=p.verify_sources(); policies=policy_audit()
    blockers=['Unresolved semantic mapping: '+x for x in reg['validation']['unresolved_compatibility_records']]
    blockers += validate_approval(p.decision_json(approval),registration) if approval else list(PENDING)
    return {'version':'p1c_compatibility_gate_v1','checked_utc':d.now(),'status':'NO_GO' if blockers else 'GO',
            'registered_confirmations':74,'registered_unique_case_text_items':72,'controls_subset':12,
            'legacy_derived_categories':reg['validation']['derived_legacy_categories'],'remaining_gate_items':blockers,
            'mandatory_approval_count':len(blockers),'technical':technical,'policy_audit':policies,
            'registration_sha256':d.sha(registration),'manifest_sha256':p.MANIFEST_SHA,
            'approval_source':None if approval is None else {'path':str(approval),'sha256':d.sha(approval)},
            'control_class':p.CONTROL_CLASS,'new_generations':0,
            'scope':'Offline gate only; GO never executes inference. Runtime preflight remains required.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    q=sub.add_parser('register');q.add_argument('--bundle',type=Path,default=BUNDLE);q.add_argument('--output',type=Path,required=True)
    for name in ('prepare-approval','gate'):
        q=sub.add_parser(name);q.add_argument('--registration',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
        if name=='gate':q.add_argument('--approval',type=Path)
    args=parser.parse_args()
    try:
        if args.output.exists():raise FileExistsError('Output exists; preserve immutable versions')
        if args.action=='register':result=register(args.bundle,args.output)['validation']
        elif args.action=='prepare-approval':
            policy_audit();result=approval_template(args.registration);d.write_json(args.output,result)
        else:result=gate(args.registration,args.approval);d.write_json(args.output,result)
        print(json.dumps(result,indent=2))
        if args.action=='gate' and result['status']!='GO':raise SystemExit(2)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({'status':'REJECTED','error':str(exc),'new_generations':0}));raise SystemExit(2)


if __name__=='__main__':main()
