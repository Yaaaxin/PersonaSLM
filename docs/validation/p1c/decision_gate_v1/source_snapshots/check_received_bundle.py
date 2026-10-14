"""Read-only intake of the newly supplied legacy review bundle; no conversion."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()/'tools'))
import p1c_design as d
import p1c_decisions as p

root=Path('PersonaSLM_P1c_Researcher_Confirmed_Registration_v1')
mp=root/'docs/validation/p1c/final_review_v1/researcher_confirmation_manifest_v1.json'
m=p.decision_json(mp)
dest=m['relative_repository_destination']
original={'confirmation':p.SOURCE/'researcher_confirmation_form_v1.csv',
          'cases':Path('docs/validation/p1c/scientific_review_v1/case_review_v1.csv'),
          'history':Path('docs/validation/p1c/scientific_review_v1/history_text_review_v1.csv')}
source_checks={};generated_checks={};comparisons=0
for key,path in original.items():
    d.require(d.sha(path)==m['sources_sha256'][key],'Original input hash mismatch: '+key)
    source_checks[key]={'path':str(path),'sha256':d.sha(path),'status':'PASS'}
for key,h in m['generated_csv_sha256'].items():
    path=root/dest[key];d.require(d.sha(path)==h,'Supplied output hash mismatch: '+key)
    generated_checks[key]={'path':str(path),'sha256':h,'status':'PASS'}
for key,path in original.items():
    fields,old=p.csv_rows(path);newfields,new=p.csv_rows(root/dest[key])
    idkey='case_id' if key=='cases' else 'item_id'
    ref={r[idkey]:r for r in old}
    d.require(fields==newfields and len(new)==len(old),'Schema/count mismatch: '+key)
    d.require(len({r[idkey] for r in new})==len(new) and {r[idkey] for r in new}==set(ref),'Duplicate/unknown/missing IDs: '+key)
    for row in new:
        for field,value in ref[row[idkey]].items():
            if field.startswith('researcher_') or field in ('reviewer_id','review_timestamp'):continue
            d.require(row[field]==value,f'Non-annotation mismatch: {key}/{row[idkey]}/{field}');comparisons+=1
_,confirmed=p.csv_rows(root/dest['confirmation']);_,unified=p.csv_rows(root/dest['unified'])
byid={r['item_id']:r for r in unified};d.require(len(byid)==77,'Unified ID count')
for row in confirmed:
    d.require(all(byid[row['item_id']][k]==v for k,v in row.items()),'Unified/confirmation inconsistency')
    status=byid[row['item_id']]['review_confirmation_status']
    if status=='RESEARCHER_CONFIRMED':d.require(row['reviewer_id']=='Yaxin_ZHENG','Missing final authority')
    else:d.require(status=='RESEARCHER_ACKNOWLEDGED_PENDING','Unexpected confirmation status')
    d.require(row['review_timestamp']=='','Unexpected supplied timestamp')
for key in ('cases','history'):
    _,rows=p.csv_rows(root/dest[key])
    for row in rows:
        item=row['case_id'] if key=='cases' else row['case_id']+'/'+row['condition']
        for field in ('researcher_decision','researcher_notes','reviewer_id'):
            d.require(row[field]==byid[item][field],'Cross-file decision discrepancy: '+item)
        subfields=[k for k in row if k.startswith('researcher_') and k not in ('researcher_decision','researcher_notes')]
        d.require(all(row[k]=='' for k in subfields),'Unexpected subcriterion input')
counts=Counter(r['item_type']+'__'+r['researcher_decision'] for r in confirmed)
d.require(dict(counts)==m['decision_counts'],'Manifest decision counts mismatch')
result={'version':'p1c_received_scoped_bundle_check_v1','checked_utc':d.now(),
    'status':'SOURCE_INTEGRITY_PASS_CANONICAL_REGISTRATION_PENDING',
    'source_root':str(root),'source_files':{f.as_posix():d.sha(f) for f in root.rglob('*') if f.is_file()},
    'original_source_hash_checks':source_checks,'supplied_CSV_hash_checks':generated_checks,
    'non_annotation_fields_compared':comparisons,'non_annotation_mismatches':0,
    'supplied_records':77,'supplied_researcher_confirmed_scoped_decisions':74,
    'confirmed_unique_case_text_items':72,'confirmed_controls_subset':12,'confirmed_global_scope_items':2,
    'pending_source_global_items':{r['item_id']:r['researcher_decision'] for r in confirmed if r['item_type']=='global' and byid[r['item_id']]['review_confirmation_status']!='RESEARCHER_CONFIRMED'},
    'decision_counts':dict(counts),'canonical_new_schema_registrations':0,
    'legacy_mapping_question':'48 ACCEPT_WITH_LIMITATIONS records: explicit confirmation requested before canonical ACCEPT_WITH_RESTRICTED_ESTIMAND mapping; original labels always retained.',
    'blank_subcriteria':'No separate ratings supplied; preserve blanks. Overall adoption is not a fabricated subcriterion score.',
    'unavailable_declared_inputs':['Original external proposal and external report corresponding to the two additional source hashes are not separately supplied; their hashes are retained as unverified source declarations. The three original repository masters and all four supplied CSVs are verified.'],
    'human_review_timestamp':None,'provenance':'Supplied bundle states researcher adoption of AI-assisted proposals. Not independent human double annotation; no inference authorization.',
    'inference_authorized':False,'new_generations':0}
d.write_json(p.PACKAGE/'received_bundle_check_v1.json',result)
print(result)
