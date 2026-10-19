"""Bounded English S/F/H execution adapter; no material creation or semantic scorer.

The separate prospective material/qualification pipeline must supply an exact
manifest. Importing and validation do not tokenize, launch a server or infer.
No historical source is modified; raw participant material stays in .local.
"""
import argparse
from collections import defaultdict
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time
from unittest.mock import patch

import real_persona_chat_sfh_pilot_execution_v1 as shared

OUT = Path('docs/validation/p1/english_real_speaker_stage_v1')
PRIVATE = Path('.local/experiments/english_sfh_v1')
BASELINE = Path('docs/validation/p1/real_persona_chat_continuation_v1/execution_receipt_v1.json')
BASELINE_SHA = '4e4d2cae32d9eaff8916ad437682fd3e97624506bc93c4d6e39c409d34439f23'
BASE_GENERATIONS, BASE_SECONDS = 688, 3973.1201058999386
MODEL = {
    'model_file': 'models/gguf/instruct_candidates/qwen3-0.6b-official-23749fef/Qwen3-0.6B-Q8_0.gguf',
    'model_sha256': '9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031',
    'backend_file': 'bin/llama.cpp/llama-b11573-bin-win-cpu-x64/llama-server.exe',
    'backend_sha256': '71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846',
    'artifact_revision': '23749fefcc72300e3a2ad315e1317431b06b590a',
    'quantization': 'Q8_0',
}
RUNTIME = {'context_tokens': 2048, 'max_new_tokens': 128, 'threads': 4,
           'temperature': 0.0, 'top_p': 1.0, 'seed': 42, 'cache_prompt': False,
           'stop': [], 'ignore_eos': False, 'warmup': False, 'enable_thinking': False}
MIN_RAM, READY_RAM, LIVE_RAM = 2 * 1024**3, 1024**3, 512 * 1024**2
TEMPLATE_SHA = 'a55ee1b1660128b7098723e0abcd92caa0788061051c62d51cbe87d9cf1974d8'
SIZES = {'development': (5, 100), 'validation': (8, 160)}
DIAGNOSTICS = {'M_STYLE', 'N_STYLE'}
load, sha, th, require = shared.load, shared.sha256, shared.th, shared.require


def local(path, parent=None):
    root = Path.cwd().resolve()
    resolved = Path(path).resolve()
    require(resolved.is_relative_to(root), 'Path escaped repository')
    if parent is not None:
        require(resolved.is_relative_to(Path(parent).resolve()), 'Path escaped study area')
    return resolved


def write(path, value):
    path = local(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    shared.b.atomic_json(path, value)


def config(plan):
    return shared.s.Runtime(MODEL['model_file'], MODEL['model_sha256'], MODEL['backend_file'],
                            model_label='Qwen3-0.6B-official-Q8_0-English-SFH',
                            n_ctx=2048, max_new_tokens=128)


def payload(row):
    return {'prompt': row['input_token_ids'], 'n_predict': 128, 'temperature': 0.0,
            'top_p': 1.0, 'seed': 42, 'cache_prompt': False, 'stop': [],
            'ignore_eos': False, 'return_tokens': True, 'stream': False}


def validate_rows(plan):
    speakers_required, requests_required = SIZES[plan['batch']]
    rows, cases, speakers, ids = plan['requests'], defaultdict(dict), defaultdict(set), set()
    require(len(rows) == requests_required, 'Wrong prospective factorial allocation')
    for index, row in enumerate(rows):
        require(row['phase'] in ('MAIN', 'DIAGNOSTIC') and row['order'] == index and
                isinstance(row['request_id'], str) and row['request_id'] not in ids,
                'Unexpected phase/order/duplicate request')
        ids.add(row['request_id'])
        require(isinstance(row['speaker_id'], str) and isinstance(row['case_id'], str), 'Case identity')
        condition = row['condition']
        if condition in shared.CONDITIONS:
            require(row['phase'] == 'MAIN' and row['factors'] == shared.CONDITIONS[condition],
                    'Condition/factor mismatch')
        else:
            require(condition in DIAGNOSTICS and row['phase'] == 'DIAGNOSTIC' and
                    row['factors'] is None and row['diagnostic_factors'] == {'F': 1, 'H': 1},
                    'Diagnostics must remain outside factorial effect coding')
            if condition == 'N_STYLE':
                require(row['style_source_scope'] == 'pooled_development' and
                        row['style_source_speaker_id'] is None, 'Neutral style source')
        key = row['speaker_id'], row['case_id']
        require(condition not in cases[key], 'Duplicate factorial cell')
        cases[key][condition] = row
        speakers[row['speaker_id']].add(row['case_id'])
        tokens = row['input_token_ids']
        require(isinstance(tokens, list) and tokens and
                all(type(token) is int and token >= 0 for token in tokens), 'Native input IDs')
        require(len(tokens) == row['input_tokens'] and len(tokens) + 128 <= 2048,
                'Input/context accounting')
        require(th(row['prompt']) == row['prompt_sha256'] and
                shared.value_sha256(tokens) == row['input_token_ids_sha256'], 'Prompt/token hashes')
        require(shared.value_sha256({k: v for k, v in row.items() if k != 'request_sha256'}) ==
                row['request_sha256'], 'Exact request hash')
        require(isinstance(row['messages'], list) and row['messages'] and
                all(m.get('role') in ('system', 'user', 'assistant') and isinstance(m.get('content'), str)
                    for m in row['messages']), 'Explicit chat messages')
    require(len(speakers) == speakers_required and all(len(v) == 2 for v in speakers.values()),
            'Exactly two contexts per allocated speaker required')
    require(all(set(group) == set(shared.CONDITIONS) | DIAGNOSTICS for group in cases.values()),
            'Incomplete paired factorial or style diagnostics')
    for group in cases.values():
        mismatch = group['M_STYLE']
        require(mismatch['style_source_scope'] == 'mismatched_selected_speaker' and
                mismatch['style_source_speaker_id'] in speakers and
                mismatch['style_source_speaker_id'] != mismatch['speaker_id'],
                'Mismatched style must come from another selected speaker')
    return set(speakers)


def baseline(plan):
    require(sha(BASELINE) == BASELINE_SHA, 'Historical budget receipt changed')
    historical = load(BASELINE)
    require(historical['cumulative_generations'] == BASE_GENERATIONS and
            historical['cumulative_inference_seconds'] == BASE_SECONDS, 'Historical cumulative accounting')
    if plan['batch'] == 'development':
        require(plan['prior_receipt'] == {'path': BASELINE.as_posix(), 'sha256': BASELINE_SHA},
                'Development baseline binding')
        return BASE_GENERATIONS, BASE_SECONDS
    prior = plan['prior_receipt']
    require(local(prior['path']) == local(OUT / 'development_execution_receipt_v1.json') and
            sha(local(prior['path'])) == prior['sha256'], 'Validation predecessor binding')
    receipt = load(prior['path'])
    require(receipt['batch'] == 'development' and receipt['status'] == 'PASS' and
            receipt['attempts'] == receipt['responses'] == SIZES['development'][1], 'Complete development required')
    events = shared.b.read_events(local(receipt['run_directory'], PRIVATE))
    require(events[-1]['kind'] == 'run_finished' and
            events[-1]['event_hash'] == receipt['terminal_event_sha256'], 'Predecessor journal binding')
    terminal = events[-1]['data']
    require(all(terminal[key] == receipt[key] for key in
                ('batch', 'status', 'attempts', 'responses', 'cumulative_generations', 'cumulative_inference_seconds')),
            'Predecessor accounting mismatch')
    require(receipt['cumulative_generations'] == BASE_GENERATIONS + SIZES['development'][1] and
            receipt['cumulative_inference_seconds'] >= BASE_SECONDS, 'Validation baseline accounting')
    return receipt['cumulative_generations'], receipt['cumulative_inference_seconds']


def validate(manifest_path, expected_sha):
    manifest_path = local(manifest_path, PRIVATE)
    require(sha(manifest_path) == expected_sha, 'Externally supplied frozen manifest hash mismatch')
    plan = load(manifest_path)
    require(plan['schema'] == 'personaslm_english_sfh_execution_v1' and plan['batch'] in SIZES and
            plan['language'] == 'en', 'Study/phase/language scope')
    require(plan['model'] == MODEL and plan['runtime'] == RUNTIME, 'Frozen model/runtime scope')
    require(plan['authorization']['decision'] == 'AUTHORIZED' and
            plan['authorization']['maximum_attempts'] == SIZES[plan['batch']][1], 'Finite batch authorization')
    require(plan['scientific_prerequisites']['approved_for_execution'] is True and
            plan['scientific_prerequisites']['human_semantic_labels_available'] is False,
            'Prospective qualification required; no human-validation assertion')
    require(plan['source_head'] == subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'Source commit changed')
    closure = {p.as_posix() for p in shared.runtime_python_dependency_paths([Path(__file__)])}
    require(closure <= set(plan['source_hashes']), 'Incomplete executable source closure')
    require(all(plan['source_hashes'][name] == plan['input_hashes'][name]
                for name in set(plan['source_hashes']) & set(plan['input_hashes'])),
            'Conflicting source/input bindings')
    for name, digest in {**plan['source_hashes'], **plan['input_hashes']}.items():
        require(sha(local(name)) == digest, 'Source/input hash mismatch: ' + name)
    require(plan['scientific_prerequisites']['record_path'] in plan['input_hashes'],
            'Qualification record not hash-bound')
    template = local(plan['template_path']).read_text(encoding='utf-8')
    require(th(template) == TEMPLATE_SHA == plan['template_sha256'], 'Official nonthinking template')
    speakers = validate_rows(plan)
    for row in plan['requests']:
        require(shared.s.render(template, row['messages']) == row['prompt'] and
                row['prompt'].endswith('<|im_start|>assistant\n<think>\n\n</think>\n\n'),
                'Actual chat-template rendering')
    if plan['batch'] == 'validation':
        development_path = local(plan['development_manifest']['path'], PRIVATE)
        require(sha(development_path) == plan['development_manifest']['sha256'], 'Development manifest binding')
        require(not speakers.intersection(r['speaker_id'] for r in load(development_path)['requests']),
                'Independent speaker overlap')
        require(plan['validation_go_record'] in plan['input_hashes'], 'Independent execution decision missing')
        require(load(plan['validation_go_record'])['decision'] == 'GO', 'No frozen validation GO')
    generations, seconds = baseline(plan)
    allocation = plan['allocation']
    require(all(type(allocation[k]) in (int, float) and math.isfinite(allocation[k]) and allocation[k] > 0
                for k in ('maximum_inference_seconds', 'maximum_wall_seconds')), 'Finite positive time allocation')
    require(generations + len(plan['requests']) <= 1200 and
            seconds + allocation['maximum_inference_seconds'] <= 72000, 'Global cumulative ceiling')
    if plan['batch'] == 'development':
        require(generations + len(plan['requests']) + SIZES['validation'][1] <= 1200,
                'Independent validation reserve')
    return plan, generations, seconds


def memory(minimum, pid):
    observation = shared.s.memory_observation(pid)
    available = observation.get('system', {}).get('available_physical')
    require(type(available) is int and available >= minimum, 'Available physical RAM below frozen gate')
    require(shutil.disk_usage('.').free >= 1024**3, 'Output disk reserve')
    return observation


def unused(batch):
    require(not (PRIVATE / batch / 'claim_v1.json').exists() and
            not list((PRIVATE / batch / 'runs').glob('*')) and
            not (OUT / (batch + '_execution_receipt_v1.json')).exists(), 'Batch already claimed; no retries')


def preflight(manifest_path, expected_sha):
    plan, generations, seconds = validate(manifest_path, expected_sha)
    unused(plan['batch'])
    identity = shared.b.file_preflight(config(plan))
    require(identity['status'] == 'PASS' and identity['model']['sha256'] == MODEL['model_sha256'] and
            identity['server']['sha256'] == MODEL['backend_sha256'], 'Model/backend identity')
    require(shared._tokenizer_identity() == plan['tokenizer_identity'], 'Native tokenizer/DLL identity')
    return {'status': 'PASS', 'checked_utc': shared.b.utc_now(), 'batch': plan['batch'],
            'manifest_sha256': expected_sha, 'identity': identity,
            'baseline': {'generations': generations, 'inference_seconds': seconds},
            'memory': memory(MIN_RAM, os.getpid())}


def snapshot_inputs(journal, plan):
    """Copy source and small bound inputs privately; archive/weight bytes stay in place."""
    sources = plan['source_hashes']
    for name, digest in {**sources, **plan['input_hashes']}.items():
        source = local(name)
        large_input = source.stat().st_size > 64 * 1024**2 or source.suffix.lower() in {
            '.gguf', '.zip', '.gz', '.tgz', '.tar', '.bz2', '.xz', '.7z'}
        if name not in sources and large_input:
            require(sha(source) == digest, 'Hash-only input changed')
            journal.write('hash_only_input', {'path': name, 'sha256': digest,
                'bytes': source.stat().st_size, 'reason': 'Archive/weight or input larger than64MiB; retained at bound path'})
            continue
        kind = 'source_snapshot' if name in sources else 'input_snapshot'
        destination = journal.directory / kind / source.relative_to(Path.cwd().resolve())
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(source.read_bytes())
        require(sha(destination) == digest, 'Source/input snapshot mismatch')


def run(manifest_path, expected_sha, preflight_path):
    with shared.b.writer_lock(PRIVATE):
        fresh, saved = preflight(manifest_path, expected_sha), load(local(preflight_path, OUT))
        require(saved['status'] == 'PASS' and all(saved[k] == fresh[k]
                for k in ('batch', 'manifest_sha256', 'identity', 'baseline')), 'Passing preflight binding')
        plan, generations, baseline_seconds = validate(manifest_path, expected_sha)
        batch = plan['batch']
        claim = {'manifest_sha256': expected_sha, 'preflight_sha256': sha(preflight_path),
                 'maximum_attempts': len(plan['requests']), 'baseline': fresh['baseline']}
        write(PRIVATE / batch / 'claim_v1.json', claim)
        journal = shared.b.RunJournal(PRIVATE / batch / 'runs', {'study': 'English real-speaker S/F/H',
                    'claim': claim, 'frozen_manifest': plan, 'configuration': config(plan).as_dict()})
        started, seconds, failed_seconds, attempts, responses = time.monotonic(), 0., 0., 0, 0
        status, active, peak_ram, minimum_ram = 'BLOCKED', None, 0, None
        try:
            snapshot_inputs(journal, plan)
            journal.write('preflight', fresh)
            with patch.object(shared.s, 'config', config), shared.s.Server(plan, journal) as server:
                observation = memory(READY_RAM, server.process.pid)
                journal.write('ready_memory', observation)
                client = shared.b.LlamaClient(config(plan).endpoint, timeout=180, audit=journal.write)
                props = client.request('/props')
                journal.write('server_properties', {'props': props,
                    'validation': shared.b.validate_server_properties(props, config(plan))})
                for row in plan['requests']:
                    ids = client.request('/tokenize', {'content': row['prompt'], 'add_special': True,
                        'parse_special': True, 'with_pieces': False})['tokens']
                    require(ids == row['input_token_ids'], 'Live native token IDs differ')
                    journal.write('verified_tokenization', {'request_id': row['request_id'],
                                  'input_token_ids_sha256': shared.value_sha256(ids)})
                journal.write('after_tokenization_memory', memory(READY_RAM, server.process.pid))
                for row in plan['requests']:
                    remaining = min(plan['allocation']['maximum_inference_seconds'] - seconds,
                                    plan['allocation']['maximum_wall_seconds'] - (time.monotonic() - started))
                    require(remaining > 0, 'Finite batch time limit')
                    server.assert_running()
                    observation = memory(LIVE_RAM, server.process.pid)
                    journal.write('before_request_memory', observation)
                    available = observation['system']['available_physical']
                    minimum_ram = available if minimum_ram is None else min(minimum_ram, available)
                    peak_ram = max(peak_ram, observation.get('process', {}).get('peak_working_set', 0))
                    client.timeout = min(180, remaining)
                    active = row['request_id']
                    journal.write('english_sfh_started', row)
                    attempts += 1
                    tick = time.monotonic()
                    try:
                        response = client.request('/completion', payload(row))
                    except BaseException:
                        elapsed = time.monotonic() - tick
                        seconds += elapsed
                        failed_seconds += elapsed
                        journal.write('english_sfh_failed', {'request_id': active, 'latency_seconds': elapsed})
                        raise
                    elapsed = time.monotonic() - tick
                    seconds += elapsed
                    journal.write('english_sfh_raw', {'request_id': active, 'response': response,
                                                     'latency_seconds': elapsed})
                    responses += 1
                    shared.b.validate_completion(response, row['input_token_ids'])
                    require(type(response.get('tokens_predicted')) is int and
                            0 <= response['tokens_predicted'] <= 128, 'Output token budget')
                    after = shared.s.memory_observation(server.process.pid)
                    journal.write('after_request_memory', after)
                    peak_ram = max(peak_ram, after.get('process', {}).get('peak_working_set', 0))
                    active = None
                    print(json.dumps({'batch': batch, 'completed': responses,
                                      'allocated': len(plan['requests'])}), flush=True)
                server.assert_running()
            status = 'PASS'
        except BaseException as exc:
            status = 'PARTIAL' if attempts else 'BLOCKED'
            journal.write('failure', {'type': type(exc).__name__, 'message': str(exc), 'request_id': active})
        result = {'batch': batch, 'status': status, 'attempts': attempts, 'responses': responses,
                  'completion_inference_seconds': seconds, 'failed_seconds': failed_seconds,
                  'wall_seconds': time.monotonic() - started, 'unattempted': len(plan['requests']) - attempts,
                  'retries': 0, 'cumulative_generations': generations + attempts,
                  'cumulative_inference_seconds': baseline_seconds + seconds,
                  'peak_observed_process_lifetime_working_set': peak_ram or None,
                  'minimum_pre_request_available_ram': minimum_ram, 'human_labels_created': 0}
        journal.finish(**result)
        write(OUT / (batch + '_execution_receipt_v1.json'), {**result,
              'manifest_sha256': expected_sha, 'run_directory': journal.directory.as_posix(),
              'terminal_event_sha256': journal.previous_hash})
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('validate', 'preflight', 'run'))
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--preflight', type=Path)
    args = parser.parse_args()
    if args.action == 'validate':
        plan, generations, seconds = validate(args.manifest, args.manifest_sha256)
        result = {'status': 'VALIDATED_NOT_EXECUTED', 'batch': plan['batch'],
                  'requests': len(plan['requests']), 'baseline_generations': generations,
                  'baseline_inference_seconds': seconds}
    elif args.action == 'preflight':
        require(args.output is not None, 'Exclusive public preflight output required')
        local(args.output, OUT)
        try:
            result = preflight(args.manifest, args.manifest_sha256)
        except Exception as exc:
            observation = shared.s.memory_observation(os.getpid())
            available = observation.get('system', {}).get('available_physical')
            result = {'status': 'FAIL', 'checked_utc': shared.b.utc_now(), 'error': str(exc),
                      'memory': observation, 'required_available_bytes': MIN_RAM,
                      'ram_deficit_bytes': max(0, MIN_RAM - available) if type(available) is int else None,
                      'new_generations': 0, 'retry_without_material_change': False}
        write(args.output, result)
    else:
        require(args.preflight is not None, 'Passing preflight path required')
        result = run(args.manifest, args.manifest_sha256, args.preflight)
    print(json.dumps(result, indent=2))
