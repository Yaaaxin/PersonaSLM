"""Register explicit researcher decisions and execute one frozen tokenizer pair."""
import argparse
import csv
import json
from pathlib import Path
import shutil

from personaslm.scientific_closure import VERSION, register_reviews, tessa_plan, reconcile_tokenizations
from personaslm.control_decisions import read_csv
from personaslm.configuration import RuntimeConfig, preflight
from personaslm.inference import LlamaClient
from personaslm.journal import atomic_json, RunJournal, read_events, utc_now
from personaslm.provenance import fingerprint, sha256
from personaslm.reproducibility import source_snapshot
from personaslm.server import ManagedServer, validate_server_properties

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'docs/validation'
SESSION = ROOT / 'results/p0_scientific_closure/final_v1'
DATA = ROOT / 'results/p0_control_closure/closure_v1/materials/development_cases.jsonl'
FREEZE = PUBLIC / 'P0_tessa_minimal_freeze_v1.json'
VALIDATION = PUBLIC / 'P0_tessa_minimal_tokenizer_v1.json'
MODEL_SHA = 'ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994'
SERVER_SHA = '71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def register():
    names = ['PersonaSLM_P0_style_v1', 'PersonaSLM_P0_historyA_evidence_notes_v1']
    paths = []
    for name in names:
        matches = [p for p in PUBLIC.iterdir() if p.is_file() and p.stem == name and p.suffix.lower() == '.csv']
        if len(matches) != 1:
            raise ValueError('Missing or ambiguous source CSV')
        paths.append(matches[0])
    attestation = {'version': 'researcher_scientific_closure_attestation_v1', 'recorded_utc': utc_now(),
        'reviewer_id': 'Yaxin_ZHENG', 'decision_source': 'researcher', 'review_type': 'researcher_verified_human_review',
        'final_decision_authority': 'researcher', 'source_judgments_confirmed': True, 'history_associations_confirmed': True,
        'style_decisions': {n: ('REVISION_REQUIRED' if n == 'Tessa' else 'ACCEPT_NARROW') for n in ['Riley','Samara','Devon','Tessa','Blair','Robin']},
        'history_decision': 'ACCEPT_NARROW', 'history_comparison_suitability': 'PASS',
        'confirmation_provenance': 'Current researcher instruction Final P0 Scientific Acceptance and Closure and subsequent confirmation of agreement with blank human fields',
        'reviewed_utc': None, 'recording_time_is_not_review_time': True,
        'blind_label_request': 'Researcher requested blind-review wording in a follow-up. Source forms expose preliminary assessments; blind status is not asserted. Agreement is registered without changing procedural provenance.',
        'authority_limit': 'This attestation covers the supplied wording, not a future Tessa revision',
        'sources': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha256(p)} for p in paths]}
    sf, sr = read_csv(paths[0]); hf, hr = read_csv(paths[1])
    result = register_reviews(sf, sr, hf, hr, read(PUBLIC/'P0_style_closure_review_v1.json'), read(PUBLIC/'P0_history_a_evidence_v1.json'), attestation)
    directory = PUBLIC / 'P0_scientific_review_registration_v1'
    directory.mkdir(exist_ok=False)
    for p in paths:
        shutil.copyfile(p, directory/p.name)
    atomic_json(directory/'attestation.json', attestation)
    result.update({'registered_utc': utc_now(), 'attestation_sha256': sha256(directory/'attestation.json'), 'source_files': attestation['sources'],
        'source_human_fields': 'Blank in both original files; no CSV cell is backfilled. Explicit conversation confirmation supplies final authority.'})
    atomic_json(directory/'registration.json', result)
    print(json.dumps(result['counts']))

def freeze():
    previous = read(PUBLIC/'P0_style_closure_freeze_v1.json')
    plan = tessa_plan(previous['dataset_records'], read(PUBLIC/'P0_style_closure_review_v1.json'))
    snapshot = source_snapshot(DATA)
    value = {'version': VERSION, 'created_utc': utc_now(), 'plan': plan, 'dataset_sha256': sha256(DATA),
        'dataset_version': 'unchanged_six_control_v2_development_cases; Tessa only selected by researcher',
        'source_snapshot': snapshot, 'configuration': read(ROOT/'configs/p0_runtime.local.json'),
        'config_file_sha256': sha256(ROOT/'configs/p0_runtime.local.json'),
        'review_registration_sha256': sha256(PUBLIC/'P0_scientific_review_registration_v1/registration.json'),
        'old_style_master_sha256': sha256(PUBLIC/'P0_style_closure_review_v1.json'),
        'model_sha256': MODEL_SHA, 'backend_sha256': SERVER_SHA, 'answer_requests_authorized': 0}
    value['freeze_id'] = fingerprint(value)
    atomic_json(FREEZE, value)
    print(json.dumps({'candidate_bound': 1, 'reference_bound': 1, 'freeze_sha256': sha256(FREEZE), 'text': plan['candidate_text']}))

def tokenize():
    if VALIDATION.exists() or any((SESSION/'experiments').iterdir()):
        raise FileExistsError('Single attempt already exists; preserve it')
    frozen = read(FREEZE)
    assert fingerprint({k:v for k,v in frozen.items() if k!='freeze_id'}) == frozen['freeze_id']
    current = source_snapshot(DATA)
    assert all(current[k] == frozen['source_snapshot'][k] for k in ['source_sha256','tool_sha256'])
    assert sha256(DATA) == frozen['dataset_sha256']
    assert sha256(ROOT/'configs/p0_runtime.local.json') == frozen['config_file_sha256']
    config = RuntimeConfig.load(ROOT/'configs/p0_runtime.local.json')
    before = preflight(config)
    if before['status'] != 'PASS' or before['model']['sha256'] != MODEL_SHA or before['server']['sha256'] != SERVER_SHA:
        raise ValueError('Pinned binary verification failed')
    journal = RunJournal(SESSION/'experiments', {'scope': 'Tessa single-candidate minimal repair; tokenizer only',
        'freeze': frozen, 'freeze_sha256': sha256(FREEZE), 'configuration': config.as_dict(),
        'source_snapshot': current, 'preflight': before, 'generation_parameters': None})
    plan = frozen['plan']
    try:
        with ManagedServer(config, journal) as server:
            client = LlamaClient(config.endpoint, timeout=config.timeout, audit=journal.write)
            binding = validate_server_properties(client.request('/props'), config)
            journal.write('tokenizer_binding', binding)
            reference_ids = client.tokenize(plan['reference_prompt']['text'])
            candidate_ids = client.tokenize(plan['candidate_prompt']['text'])
            result = {'reference_token_ids': reference_ids, 'candidate_token_ids': candidate_ids,
                'reference_token_count': len(reference_ids), 'candidate_token_count': len(candidate_ids),
                'token_difference': len(candidate_ids)-len(reference_ids),
                'matching_status': 'PASS' if len(reference_ids)==len(candidate_ids) else 'FAILED',
                'researcher_approval': 'PENDING', 'plan': plan}
            journal.write('tessa_pair_result', result)
            server.assert_running()
        after = preflight(config)
        assert after == before
        journal.write('postflight', after)
        journal.finish('PASS', scope='Tokenizer execution only; no human approval inferred', completion_requests=0)
    except BaseException as exc:
        journal.write('error', {'type':type(exc).__name__, 'message':str(exc)})
        journal.finish('BLOCKED', completion_requests=0)
        raise
    events = read_events(journal.directory)
    reconcile_tokenizations(events, [(plan['reference_prompt']['text'],reference_ids),(plan['candidate_prompt']['text'],candidate_ids)])
    atomic_json(VALIDATION, {'version': VERSION, 'created_utc': utc_now(), 'run_directory': journal.directory.relative_to(ROOT).as_posix(),
        'freeze_sha256': sha256(FREEZE), 'model_sha256': MODEL_SHA, 'backend_sha256': SERVER_SHA, 'binding': binding,
        'events': len(events), 'tokenizer_requests': 2, 'completion_requests': 0, 'result': result, 'P0': 'PARTIAL'})
    print(json.dumps({k:v for k,v in result.items() if k not in {'plan','reference_token_ids','candidate_token_ids'}}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['register','freeze','tokenize'])
    args = parser.parse_args()
    {'register':register,'freeze':freeze,'tokenize':tokenize}[args.stage]()
