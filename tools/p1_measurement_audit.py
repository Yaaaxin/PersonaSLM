"""Offline scientific audit and separately registered human review. No inference calls."""
import argparse
import base64
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import secrets
import subprocess

from personaslm.inference import normalize_result
from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.measurement_audit import VERSION, REVIEW_VERSION, HUMAN_FIELDS, partition, sentence_form, coverage, make_packet, validate_annotations
from personaslm.p1 import PilotCase, evaluate_pilot
from personaslm.provenance import fingerprint
from personaslm.response_status import text_hash
from personaslm.runner import validate_completion
from personaslm.scientific_closure import reconcile_tokenizations
from p1_analyze import contrasts

PUBLIC = Path('docs/validation/p1')
LOCAL = Path('results/p1_measurement_audit/v1')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def csv_rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); rows = list(reader)
    if len(reader.fieldnames) != len(set(reader.fieldnames)) or any(None in r or None in r.values() for r in rows):
        raise ValueError('Malformed CSV schema')
    return rows


def audit():
    started = utc_now()
    outputs = [PUBLIC/'measurement_audit_v1.json', PUBLIC/'output_human_review_v1.csv',
               PUBLIC/'output_human_review_schema_v1.json', LOCAL/'admin/output_human_review_mapping_v1.json']
    if any(p.exists() for p in outputs):
        raise FileExistsError('Preserve completed audit and review masters; use a new version')
    baseline = read(LOCAL/'baseline.json')
    for name, expected in baseline['files'].items():
        if sha(name) != expected:
            raise ValueError('Preexisting workspace file changed before audit: ' + name)
    wave = read(PUBLIC/'wave1_manifest_v1.json')
    design = read(PUBLIC/'wave1_design_v1.json')
    saved = read(PUBLIC/'wave1_results_v1.json')['rows']
    cases = {r['case_id']: r for r in read('data/synthetic/p1_development_v1.json')['cases']}
    requests = {r['request_id']: r for r in wave['requests']}
    published = {r['request_id']: r for r in saved}
    if len(requests) != len(published) or len(saved) != 96 or set(requests) != set(published):
        raise ValueError('Incomplete or duplicate result inventory')
    if fingerprint({k:v for k,v in wave.items() if k!='manifest_id'}) != wave['manifest_id']:
        raise ValueError('Wave fingerprint changed')
    assert sha(PUBLIC/'wave1_design_v1.json') == wave['design_sha256']
    assert sha('data/synthetic/p1_development_v1.json') == wave['dataset_sha256']
    assert sha('docs/research_protocol_v1.1.md') == design['protocol_sha256']
    assert sha('docs/P1_experiment_plan.md') == design['experiment_plan_sha256']
    for name, h in design['source_snapshot']['source_sha256'].items():
        assert sha(Path('src/personaslm')/name) == h
    for name, value in design['source_snapshot']['p1_tool_sources'].items():
        assert sha(name) == value['sha256']
    assert sha(wave['configuration']['model_file']) == wave['model_sha256']
    assert sha(wave['configuration']['server_file']) == wave['backend_sha256']

    prepared = read(PUBLIC/'control_matching_v1.json')
    expected_tokenizations = [(r['prompt']['text'], r['input_token_ids']) for r in wave['requests']]
    expected_tokenizations += [(a['prompt']['text'], a['token_ids']) for r in prepared['results'] for a in r['attempts']]
    journals = []; generated = []; attempts = []; generation_native = 0
    for directory, inventory in baseline['journals'].items():
        folder = Path(directory)
        actual_files = {p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
        if actual_files != inventory:
            raise ValueError('Historical run files changed')
        meta = read(folder/'manifest.json'); events = read_events(folder)
        finished = [e['data'] for e in events if e['kind']=='run_finished']
        assert len(finished)==1 and finished[0]['status']=='PASS'
        info = {'directory': directory, 'manifest_sha256': sha(folder/'manifest.json'), 'events': len(events),
                'files': actual_files, 'chain_valid': True, 'run_finished': finished[0],
                'standalone_summary_present': (folder/'summary.json').exists(),
                'http_status_counts': dict(Counter(f"{e['data']['route']} {e['data']['status']}" for e in events if e['kind']=='http_response')),
                'http_errors': [e for e in events if e['kind']=='http_error'],
                'saved_backend_versions': [e['data'] for e in events if e['kind']=='engine_version'],
                'operation': meta['operation']}
        if meta['operation']=='tokenizer_preparation_only':
            info['tokenizations_reconciled'] = reconcile_tokenizations(events, expected_tokenizations)
        elif meta['operation']=='factorial_generation':
            assert meta['wave_manifest_sha256']==sha(PUBLIC/'wave1_manifest_v1.json')
            token_pending = None; native = {}; current = None; completion_pending = None; responses = {}; verified = set()
            for event in events:
                kind, data = event['kind'], event['data']
                if kind=='http_request' and data['route']=='/tokenize':
                    assert token_pending is None
                    token_pending = data['payload']
                    assert {k:v for k,v in token_pending.items() if k!='content'}=={'add_special':True,'parse_special':False,'with_pieces':False}
                if kind=='http_response' and data['route']=='/tokenize':
                    assert token_pending is not None and data['status']==200
                    native[text_hash(token_pending['content'])]=json.loads(base64.b64decode(data['body_base64']))['tokens']
                    token_pending=None; generation_native+=1
                if kind=='p1_prompt_verified':
                    assert data==requests[data['request_id']]
                    assert native[data['prompt_sha256']]==data['input_token_ids']
                    verified.add(data['request_id'])
                if kind=='p1_generation_started':
                    current=data['request_id']; attempts.append(current)
                    assert current in verified and data==requests[current]
                if kind=='http_request' and data['route']=='/completion':
                    assert completion_pending is None and data['payload']=={'prompt':requests[current]['input_token_ids'],**wave['decoding']}
                    completion_pending=current
                if kind=='http_response' and data['route']=='/completion':
                    assert completion_pending is not None and data['status']==200
                    responses[completion_pending]=json.loads(base64.b64decode(data['body_base64']));completion_pending=None
                if kind=='p1_raw_generation':
                    assert data['response']==responses[data['request_id']]
                if kind=='p1_result':
                    rid=data['request_id']; original=responses[rid]
                    assert data==published[rid]
                    for key,value in requests[rid].items():assert data[key]==value
                    assert data['token_audit']==validate_completion(original,data['input_token_ids'])
                    for key,value in normalize_result(original).items():assert data[key]==value
                    first=evaluate_pilot(PilotCase(cases[data['case_id']]),data['raw_response'],data['raw_termination'])
                    second=evaluate_pilot(PilotCase(cases[data['case_id']]),data['raw_response'],data['raw_termination'])
                    assert first==second==data['evaluation']
                    generated.append(rid)
            assert token_pending is None and completion_pending is None
            info['completed_response_reconstructions']=len(responses)
            info['native_inputs_reconciled']=len(verified)
        else:
            raise ValueError('Unexpected wave run operation')
        journals.append(info)
    assert len(generated)==len(set(generated))==len(attempts)==len(set(attempts))==96
    old_output_review=csv_rows(PUBLIC/'output_review_v1.csv'); old_controls=csv_rows(PUBLIC/'control_review_v1.csv')
    assert len(old_output_review)==96 and len(old_controls)==24

    rows=[]
    for original in sorted(saved,key=lambda r:r['request_id']):
        unit=partition(original); case=cases[original['case_id']]
        rows.append({'request_id':original['request_id'],'case_id':original['case_id'],
                     'condition':original['condition'],'family':original['family'],
                     'raw_continuation':original['raw_response'],'generated_tokens':original['generated_tokens'],
                     'original_factual_label':original['evaluation']['factual_support']['label'],
                     'applicability':original['applicability'], 'partition':unit,
                     'post_hoc_form_diagnostic':sentence_form(case,original['parsed_response']),
                     'source_prompt_sha256':original['prompt_sha256'],'raw_sha256':text_hash(original['raw_response']),
                     'source_evaluation':original['evaluation'], 'human_judgment':None})
    seed=secrets.randbits(128)
    packet,mapping=make_packet(saved,cases,seed)
    outputs[3].parent.mkdir(parents=True,exist_ok=True)
    with outputs[1].open('x',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(packet[0]));writer.writeheader();writer.writerows(packet)
    mapping.update(created_utc=utc_now(),packet_sha256=sha(outputs[1]),source_result_sha256=sha(PUBLIC/'wave1_results_v1.json'))
    atomic_json(outputs[3],mapping)
    ignored=subprocess.run(['git','check-ignore',outputs[3].as_posix()],capture_output=True,text=True)
    if ignored.returncode!=0:raise ValueError('Curator mapping is not excluded from Git')
    schema={'review_version':REVIEW_VERSION,'created_utc':utc_now(),'record_count':len(packet),'fields':list(packet[0]),
            'human_fields':list(HUMAN_FIELDS),'packet_sha256':sha(outputs[1]),'human_judgments_filled':0,
            'preserve_raw_whitespace':True,'treatment_labels_hidden':True,'automatic_factual_labels_hidden':True,
            'masking_limit':'Structural labels requested by researcher are visible. Output wording and old public artifacts permit treatment inference. Reviewers receive only CSV and instructions; no blind human evaluation yet.',
            'case_reference_material':'Full source fact ledger is identical across conditions of each case, not the treatment-specific historical prompt',
            'curator_mapping_directory':'results/p1_measurement_audit/v1/admin (ignored; not an ACL or encryption claim)',
            'independent_review_complete':False,'frozen_applicability_unchanged':True}
    atomic_json(outputs[2],schema)
    factual_u=[r for r in rows if r['original_factual_label']=='Unverifiable']
    concentration=contrasts(saved)
    result={'version':VERSION,'started_utc':started,'finished_utc':utc_now(),'post_hoc_diagnostic':True,
            'new_generation_requests':0,'originals_overwritten':False,'response_policy_changed':False,
            'git_commit':subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip(),
            'git_dirty':True,'source_wave_git':wave['git'],'rows':rows,'journal_audits':journals,
            'baseline_sha256':sha(LOCAL/'baseline.json'),'source_results_sha256':sha(PUBLIC/'wave1_results_v1.json'),
            'source_manifest_sha256':sha(PUBLIC/'wave1_manifest_v1.json'),'dataset_sha256':wave['dataset_sha256'],
            'model_sha256':wave['model_sha256'],'backend_sha256':wave['backend_sha256'],
            'source_sha256':{p:sha(p) for p in ['src/personaslm/measurement_audit.py','tools/p1_measurement_audit.py']},
            'original_first_replies_reconstructed':96,'original_evaluations_reconstructed_twice':96,
            'generation_input_tokenizations_reconciled':generation_native,
            'structure_counts':dict(Counter(r['partition']['original_status'] for r in rows)),
            'boundaries_observed':sum(r['partition']['boundary_observed'] for r in rows),
            'identifiable_spans':sum(r['partition']['first_span_identifiable'] for r in rows),
            'prefix_removed':sum(bool(r['partition']['excluded_prefix']) for r in rows),
            'raw_empty':sum(not r['raw_continuation'].strip() for r in rows),
            'additional_role_labelled_spans':sum(len(r['partition']['additional_turns']) for r in rows),
            'stop_reasons':dict(Counter(r['stop_reason'] for r in saved)),
            'unverifiable_form_counts':dict(Counter(r['post_hoc_form_diagnostic']['observed_form'] for r in factual_u)),
            'all_form_counts':dict(Counter(r['post_hoc_form_diagnostic']['observed_form'] for r in rows)),
            'reliability_coverage':coverage(saved),'coverage_by_condition':{c:coverage([r for r in saved if r['condition']==c]) for c in sorted({r['condition'] for r in saved})},
            'paired_structural_analysis':concentration,'human_response_reviews':0,
            'prior_control_reviews_present':sum(bool(r['reviewer_id'].strip()) for r in old_controls),
            'existing_review_materials_hashes':{p.name:sha(p) for p in [PUBLIC/'output_review_v1.csv',PUBLIC/'control_review_v1.csv']},
            'new_review_packet_sha256':sha(outputs[1]),'mapping_protection':schema['curator_mapping_directory'],
            'inferential_limit':'No semantic score changes, significance tests, response-based case exclusions or novel mechanism claims'}
    atomic_json(outputs[0],result)
    print(json.dumps({k:result[k] for k in ['version','new_generation_requests','original_first_replies_reconstructed','boundaries_observed','identifiable_spans','structure_counts','unverifiable_form_counts','all_form_counts','additional_role_labelled_spans']}))


def import_review(source, output):
    master_path=PUBLIC/'output_human_review_v1.csv'; schema=read(PUBLIC/'output_human_review_schema_v1.json')
    if sha(master_path)!=schema['packet_sha256']:raise ValueError('Review master hash changed')
    result=validate_annotations(csv_rows(master_path),csv_rows(source))
    if output.exists():raise FileExistsError('Do not overwrite review registration')
    output.mkdir(parents=True)
    (output/'source_review.csv').write_bytes(source.read_bytes())
    result.update(registered_utc=utc_now(),source_csv_sha256=sha(source),master_sha256=sha(master_path),
                  provenance='Supplied reviewer entries retained without filling timestamps or claiming independence')
    atomic_json(output/'registration.json',result)
    print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['audit','import-review'])
    parser.add_argument('--csv',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.operation=='audit':audit()
    else:
        if args.csv is None or args.output is None:parser.error('import-review requires --csv and --output')
        import_review(args.csv,args.output)
