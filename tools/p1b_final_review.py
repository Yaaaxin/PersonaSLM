"""Inspect and tokenize the frozen P1b plan. No generation action is exposed."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess

from personaslm.configuration import RuntimeConfig, preflight
from personaslm.journal import RunJournal, read_events
from personaslm.p1b import canonical_hash
from personaslm.p1b_review_resolution import (compare_review_sources, inspect_prompts,
    context_necessity_cases, tokenized_requests, TokenizationOnlyClient)
from personaslm.scientific_closure import reconcile_tokenizations
from personaslm.server import ManagedServer, validate_server_properties
from p1b_design import read, digest, csv_rows, write_json, write_csv

PUBLIC = Path('docs/validation/p1b/final_review_v1')
LOCAL = Path('results/p1b_final_review/v1')
OLD = Path('docs/validation/p1b/final_v1')
DATA = Path('data/synthetic/p1b_development_proposed_v2.json')
REPORT_SOURCE = Path('docs/validation/p1b/PersonaSLM_P1b_independent_stimulus_audit_v1.md')
SUPPORT = Path('docs/validation/p1b/review_support')
AI = SUPPORT/'PersonaSLM_P1b_24case_independent_AI_stimulus_audit_v1.csv'
SUGGESTED = SUPPORT/'PersonaSLM_P1b_stimulus_review_v2_with_AI_suggestions.csv'
MODEL = 'ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994'
BACKEND = '71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846'


def preserve():
    baseline = read(LOCAL/'baseline.json')
    exceptions = {'docs/research_development_log.md'}
    changed = [p for p, h in baseline['files'].items() if digest(p) != h]
    if set(changed)-exceptions:
        raise ValueError('Original source or historical data changed: '+repr(changed))
    for p, h in baseline['historical_run_files'].items():
        if digest(p) != h:
            raise ValueError('Original run file changed: '+p)
    observed = {p.as_posix() for p in Path('results/p1_wave1/development_v1/runs').rglob('*') if p.is_file()}
    if observed != set(baseline['historical_run_files']):
        raise ValueError('Historical run inventory changed')
    return {'source_files_checked': len(baseline['files']), 'changed_files': changed,
            'historical_run_files_unchanged': len(observed)}


def inspect():
    if PUBLIC.exists():
        raise FileExistsError('Resolution package exists; do not overwrite')
    parent = read(OLD/'calibration_manifest_v1.json'); dataset = read(DATA)
    if digest(DATA) != parent['dataset_sha256']:
        raise ValueError('Dataset hash differs')
    for p, h in read(OLD/'hash_inventory_v1.json')['files'].items():
        if digest(p) != h:
            raise ValueError('Historical preparation artifact changed: '+p)
    for p, h in read(OLD/'hash_inventory_v1.json')['sources'].items():
        if digest(p) != h:
            raise ValueError('Pinned rendering/policy source changed: '+p)
    sources = compare_review_sources(csv_rows(OLD/'stimulus_review_v2.csv'), csv_rows(SUGGESTED), csv_rows(AI))
    advertised_hash = '810ca7e751895aaf3f50b308f1af79aa3c2c67fb9ae6032e93daa0e1cd8658f9'
    if digest(OLD/'stimulus_review_v2.csv') != advertised_hash or advertised_hash not in REPORT_SOURCE.read_text(encoding='utf-8-sig'):
        raise ValueError('Supplied report source hash mismatch')
    analysis = inspect_prompts(dataset, parent)
    preserved = preserve()
    PUBLIC.mkdir(parents=True)
    inputs = [REPORT_SOURCE, AI, SUGGESTED, DATA, OLD/'calibration_manifest_v1.json', OLD/'stimulus_review_v2.csv']
    write_json(PUBLIC/'source_registration_v1.json', {'version': 'p1b_supplied_ai_analysis_registration_v1',
        'registered_utc': datetime.now(timezone.utc).isoformat(), 'sources': {p.as_posix(): digest(p) for p in inputs},
        'provenance': 'Researcher-supplied AI suggestions; not researcher-confirmed judgments; no blind review inferred.',
        'source_report_actual_path': REPORT_SOURCE.as_posix(), 'human_review_timestamp': None,
        'source_validation': sources, 'preservation': preserved})
    write_json(PUBLIC/'prompt_audit_v1.json', analysis)
    write_json(PUBLIC/'context_necessity_v1.json', {'version': 'p1b_source_ambiguity_diagnostic_v1',
        'scope': 'Offline enumeration of possible answers without focus, not generated context ablations',
        'cases': context_necessity_cases(dataset), 'new_generations': 0})
    with (PUBLIC/'researcher_review_v2.csv').open('xb') as f:
        f.write((OLD/'stimulus_review_v2.csv').read_bytes())
    case_rows = []
    for c in dataset['cases']:
        ai = next(r for r in csv_rows(AI) if r['case_id'] == c['case_id'])
        row = {'case_id': c['case_id'], 'dataset_version': dataset['version'], 'dataset_sha256': digest(DATA),
            'ai_prior_status_preserved': ai['ai_proposed_status'], 'date_visibility_resolution': 'PASS_ALL_EIGHT_PROMPTS',
            'turn_boundary_resolution': 'EXPLICIT_SAME_USER_FOLLOWUP' if c['case_id'] == 'p1b_H_L3' else 'EXPLICIT_ALTERNATING_TURNS',
            'reference_date': c['evaluation_date'], 'answer_slot_count': len(c['expected_answer']['components']),
            'ai_scientific_risk_verbatim': ai['ai_scientific_risk'], 'ai_followup_verbatim': ai['ai_required_followup'],
            'stimulus_revision_needed': 'NO_CONCRETE_INVALIDITY_FOUND',
            'scientific_interpretation': ('Retain as an easy baseline; no context-necessity claim.' if c['case_id'] in ('p1b_H_L1','p1b_H_L2') else
                'Retain as an explicit identity-lookup baseline.' if c['case_id']=='p1b_F_L1' else
                'Retain for calibration with documented shortcuts and task-family confounds.'),
            'human_review_status': 'OPEN', 'researcher_decision': '', 'researcher_notes': ''}
        case_rows.append(row)
    write_csv(PUBLIC/'resolution_by_case_v1.csv', case_rows)
    print(json.dumps({'inspection': 'PASS', 'cases': 24, 'prompts_with_reference_date': analysis['visible_reference_dates'],
        'undated_question_cases_resolved': analysis['undated_question_cases'], 'H_L3_prompts': analysis['same_user_followup_prompts'],
        'original_review_fields_preserved': sources['original_fields_compared'], 'human_decisions_present': sources['human_decisions_present'],
        'dataset_modified': False, 'new_generations': 0}))


def runtime(parent):
    # Existing RuntimeConfig contains a legacy prompt_template field. It only
    # controls server transport here; the native tokenizer receives exact frozen
    # P1b strings, with no chat-template or prompt-builder call in this adapter.
    config = RuntimeConfig.load(Path('configs/p1_wave1_v1.json'))
    expected = {**config.as_dict(), 'prompt_template': 'p1b_transcript_proposed_v1',
                'threads_batch': 4, 'n_gpu_layers': 0}
    if parent['configuration'] != expected or parent['generation_parameters'] != {
        'cache_prompt': False, 'n_predict': 96, 'return_tokens': True, 'seed': 42, 'stop': [],
        'stream': False, 'temperature': 0.0, 'top_p': 1.0}:
        raise ValueError('Pinned transport, rendering or decoding changed')
    check = preflight(config)
    if check['status'] != 'PASS' or check['model']['sha256'] != MODEL or check['server']['sha256'] != BACKEND:
        raise ValueError('Pinned model/backend identity failed')
    return config, check


def tokenize():
    target = PUBLIC/'calibration_manifest_v2.json'
    if target.exists():
        raise FileExistsError('Successful tokenization already published; replay its journal instead')
    # Do not repeat a partially or fully tokenized attempt without explicit recovery.
    for old in (LOCAL/'runs').glob('*'):
        if any(e['kind'] == 'p1b_prompt_tokenized' for e in read_events(old)):
            raise ValueError('Prior tokenized prompts exist; preserve and recover that segment, do not rerun')
    parent = read(OLD/'calibration_manifest_v1.json'); data = read(DATA)
    if digest(DATA) != parent['dataset_sha256'] or inspect_prompts(data, parent) != read(PUBLIC/'prompt_audit_v1.json'):
        raise ValueError('Frozen prompt inspection no longer reconstructs')
    preserve()
    config, before = runtime(parent)
    source_paths = sorted(Path('src/personaslm').glob('*.py')) + [Path('tools/p1b_final_review.py'),
        Path('tests/test_p1b_review_resolution.py'), Path('configs/p1_wave1_v1.json'), Path('docs/research_protocol_v1.1.md')]
    sources = {p.as_posix(): digest(p) for p in source_paths}
    snapshot = {p.as_posix(): p.read_text(encoding='utf-8') for p in source_paths}
    git_sha = subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    git_status = subprocess.check_output(['git','status','--short'],text=True)
    journal = RunJournal(LOCAL/'runs', {'phase': 'P1b', 'operation': 'tokenizer_preflight_only',
        'parent_manifest_sha256': digest(OLD/'calibration_manifest_v1.json'), 'dataset_sha256': digest(DATA),
        'rendered_prompt_template': parent['requests'][0]['prompt_template_version'],
        'transport_configuration': config.as_dict(), 'legacy_template_field_applied_to_text': False,
        'configuration': parent['configuration'], 'git_sha': git_sha, 'git_dirty': bool(git_status.strip()),
        'git_status': git_status, 'source_hashes': sources, 'source_utf8': snapshot,
        'python': platform.python_version(), 'allowed_http_routes': ['/health','/props','/tokenize'],
        'maximum_tokenizer_requests': 192, 'generation_requests_authorized': 0})
    journal.write('preflight', before)
    try:
        with ManagedServer(config, journal) as server:
            client = TokenizationOnlyClient(config.endpoint, timeout=config.timeout, audit=journal.write)
            props = client.request('/props')
            binding = validate_server_properties(props, config)
            journal.write('tokenizer_binding', {'properties': props, 'validation': binding,
                'options': {'add_special': True, 'parse_special': False, 'with_pieces': False}})
            rows = tokenized_requests(parent['requests'], client.tokenize, journal.write)
            server.assert_running()
            after_props = client.request('/props'); validate_server_properties(after_props, config)
            if props.get('build_info') != after_props.get('build_info'):
                raise ValueError('Loaded backend changed')
            _, after = runtime(parent); journal.write('postflight', after)
            if before != after:
                raise ValueError('Pinned artifacts changed during tokenization')
        journal.finish('PASS', tokenized_prompts=len(rows), completion_requests=0, inference_responses=0)
    except BaseException as exc:
        journal.write('failure', {'type': type(exc).__name__, 'message': str(exc)})
        journal.finish('BLOCKED', completion_requests=0, inference_responses=0)
        raise
    events = read_events(journal.directory)
    count = reconcile_tokenizations(events, [(r['prompt'], r['input_token_ids']) for r in rows])
    if count != 192 or any(e['kind']=='http_request' and e['data']['route']=='/completion' for e in events):
        raise ValueError('Unexpected HTTP operation inventory')
    manifest = {**parent, 'version': 'p1b_calibration_manifest_v2', 'status': 'TOKENIZED_AWAITING_RESEARCHER_REVIEW',
        'parent_manifest': (OLD/'calibration_manifest_v1.json').as_posix(),
        'parent_manifest_sha256': digest(OLD/'calibration_manifest_v1.json'), 'created_utc': datetime.now(timezone.utc).isoformat(),
        'git_sha': git_sha, 'git_status': git_status, 'git_dirty': bool(git_status.strip()),
        'source_hashes': sources, 'source_snapshot': (journal.directory/'manifest.json').as_posix(),
        'tokenizer_run': journal.directory.as_posix(), 'requests': rows,
        'tokenizer_preflight': {'status': 'PASS', 'native_responses_reconciled': count, 'endpoint': '/tokenize',
            'options': {'add_special': True, 'parse_special': False, 'with_pieces': False}, 'context_fit': 'PASS_ALL_192',
            'model_sha256': MODEL, 'backend_sha256': BACKEND, 'binding': binding},
        'source_scope': 'Tokenization adapter snapshot, not an executed generation runner',
        'execution_authorized': False, 'executed_requests': 0, 'dataset_modified': False,
        'human_stimulus_review': 'OPEN', 'new_answer_generations': 0}
    write_json(target, manifest)
    counts = [r['input_token_count'] for r in rows]
    summary = {'version': 'p1b_actual_tokenizer_verification_v1', 'status': 'PASS', 'requests': 192,
        'token_min': min(counts), 'token_max': max(counts), 'output_budget': 96, 'context_capacity': 4096,
        'minimum_remaining_context': min(r['remaining_context_after_output_budget'] for r in rows),
        'model_sha256': MODEL, 'backend_sha256': BACKEND, 'binding': binding,
        'completion_requests': 0, 'generated_responses': 0, 'journal_events': len(events),
        'run_directory': journal.directory.as_posix(), 'server_log_sha256': digest(journal.directory/'server.log'),
        'event_hashes': {p.name: digest(p) for p in sorted((journal.directory/'events').glob('*.json'))},
        'run_manifest_sha256': digest(journal.directory/'manifest.json'), 'new_manifest_sha256': digest(target)}
    write_json(PUBLIC/'tokenizer_verification_v1.json', summary)
    write_csv(PUBLIC/'prompt_token_counts_v1.csv', [{k:r[k] for k in ('request_id','case_id','condition','prompt_sha256',
        'input_token_count','token_ids_sha256','context_fit','remaining_context_after_output_budget')} for r in rows])
    print(json.dumps({k:v for k,v in summary.items() if k not in ('event_hashes',)}))


def verify():
    parent = read(OLD/'calibration_manifest_v1.json'); dataset = read(DATA)
    if inspect_prompts(dataset, parent) != read(PUBLIC/'prompt_audit_v1.json'):
        raise ValueError('Prompt inspection differs')
    registration = read(PUBLIC/'source_registration_v1.json')
    if compare_review_sources(csv_rows(OLD/'stimulus_review_v2.csv'), csv_rows(SUGGESTED), csv_rows(AI)) != registration['source_validation']:
        raise ValueError('Source review fields differ')
    if any(digest(p) != h for p,h in registration['sources'].items()):
        raise ValueError('Supplied material or original plan changed')
    if digest(PUBLIC/'researcher_review_v2.csv') != digest(OLD/'stimulus_review_v2.csv'):
        raise ValueError('Researcher review master copy changed')
    new = read(PUBLIC/'calibration_manifest_v2.json'); summary = read(PUBLIC/'tokenizer_verification_v1.json')
    if digest(PUBLIC/'calibration_manifest_v2.json') != summary['new_manifest_sha256']:
        raise ValueError('Tokenized manifest changed')
    if new['parent_manifest_sha256'] != digest(OLD/'calibration_manifest_v1.json') or new['dataset_sha256'] != digest(DATA):
        raise ValueError('Manifest lineage changed')
    run = Path(summary['run_directory']); events = read_events(run)
    if digest(run/'manifest.json') != summary['run_manifest_sha256'] or digest(run/'server.log') != summary['server_log_sha256']:
        raise ValueError('Raw tokenizer provenance changed')
    if {p.name:digest(p) for p in (run/'events').glob('*.json')} != summary['event_hashes']:
        raise ValueError('Journal file bytes changed')
    if any(e['kind']=='http_request' and e['data']['route'] not in ('/health','/props','/tokenize') for e in events):
        raise ValueError('Unapproved HTTP operation')
    recorded = [e['data'] for e in events if e['kind']=='p1b_prompt_tokenized']
    if recorded != new['requests']:
        raise ValueError('Tokenized rows differ from journal')
    if reconcile_tokenizations(events, [(r['prompt'],r['input_token_ids']) for r in recorded]) != 192:
        raise ValueError('Tokenizer reconstruction incomplete')
    for old, row in zip(parent['requests'], recorded):
        if any(row[k] != v for k,v in old.items() if k not in ('input_token_ids','input_token_count','tokenizer_preflight','context_fit')):
            raise ValueError('Frozen input, order, or applicability changed')
        if len(row['input_token_ids']) != row['input_token_count'] or canonical_hash(row['input_token_ids']) != row['token_ids_sha256']:
            raise ValueError('Token IDs/count/hash mismatch')
    if new['generation_parameters'] != parent['generation_parameters'] or new['execution_authorized'] or new['executed_requests']:
        raise ValueError('Decoding or execution status changed')
    for p,h in new['source_hashes'].items():
        if digest(p) != h:
            raise ValueError('Tokenizer source changed: '+p)
    print(json.dumps({'status': 'PASS', 'native_tokenizations_reconstructed': 192, 'completion_requests': 0,
                      'prompt_order_and_applicability_preserved': True, 'preservation': preserve()}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['inspect','tokenize','verify'])
    args = parser.parse_args()
    {'inspect': inspect, 'tokenize': tokenize, 'verify': verify}[args.action]()
