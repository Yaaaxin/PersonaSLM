"""One execution-only fresh-server suffix of the unchanged 64-request study."""
import argparse
import base64
import json
from pathlib import Path
import time

import real_persona_chat_style_specificity_v1 as base

old = base.old
load, sha, require, write = base.load, base.sha, base.require, base.write
OUT = base.OUT
AMENDMENT = OUT / 'suffix_amendment_v1.json'
REGISTRATION = OUT / 'suffix_registration_v1.json'
RECEIPT = OUT / 'suffix_execution_receipt_v1.json'
ORIGINAL_RECEIPT = OUT / 'execution_receipt_v1.json'
PRIVATE = base.PRIVATE / 'suffix_v1'
RUNS = PRIVATE / 'runs'
CLAIM = PRIVATE / 'claim_v1.json'
PREFIX, N = 54, 10
BASE_GENERATIONS, BASE_SECONDS = 626, 3765.0082488998696


def reconcile():
    """Reject any uncertain, failed, repeated or non-prefix original attempt."""
    plan = base.validate()
    amendment, receipt = load(AMENDMENT), load(ORIGINAL_RECEIPT)
    require(sha(base.FROZEN) == amendment['original_manifest_sha256'] and
            sha(ORIGINAL_RECEIPT) == amendment['original_receipt_sha256'], 'Original binding changed')
    folders = list(base.RUNS.glob('*'))
    require(len(folders) == 1, 'Exactly one original run required')
    events = old.b.read_events(folders[0])
    require(events and events[-1]['kind'] == 'run_finished' and
            events[-1]['event_hash'] == receipt['terminal_event_sha256'], 'Original run not sealed')
    attempted = [e['data'] for e in events if e['kind'] == 'specificity_started']
    raw = [e['data'] for e in events if e['kind'] == 'specificity_raw']
    sent = [e['data']['payload'] for e in events if e['kind'] == 'http_request' and e['data']['route'] == '/completion']
    bodies = [json.loads(base64.b64decode(e['data']['body_base64'])) for e in events
              if e['kind'] == 'http_response' and e['data'].get('route') == '/completion' and e['data'].get('status') == 200]
    require(attempted == plan['requests'][:PREFIX] and len(attempted) == PREFIX, 'Original attempt prefix not exactly 54')
    require([r['request_id'] for r in raw] == [r['request_id'] for r in attempted] and
            sent == [old.payload(r) for r in attempted] and bodies == [r['response'] for r in raw],
            'Original requests/raw HTTP records not one-to-one')
    require(not any(e['kind'] == 'specificity_failed' for e in events), 'Original failed attempt requires separate reconciliation')
    for request, record in zip(attempted, raw):
        old.b.validate_completion(record['response'], request['input_token_ids'])
    elapsed = sum(r['latency_seconds'] for r in raw)
    require(receipt['status'] == 'PARTIAL' and receipt['attempts'] == receipt['responses'] == PREFIX and
            receipt['unattempted'] == N and receipt['failed_seconds'] == 0 and receipt['retries'] == 0,
            'Original accounting not the registered partial prefix')
    require(abs(elapsed - receipt['completion_inference_seconds']) < 1e-8 and
            receipt['cumulative_generations'] == BASE_GENERATIONS and
            abs(receipt['cumulative_inference_seconds'] - BASE_SECONDS) < 1e-8,
            'Cumulative accounting mismatch')
    require(len(plan['requests']) == PREFIX + N and BASE_GENERATIONS + N <= 1200 and
            BASE_SECONDS + 300 <= 72000, 'Finite cumulative authorization')
    return plan


def bindings():
    paths = [Path('tools/real_persona_chat_style_specificity_suffix_v1.py'),
             Path('tests/test_real_persona_chat_style_specificity_suffix_v1.py'),
             AMENDMENT, ORIGINAL_RECEIPT, base.REGISTRATION]
    return {p.as_posix(): sha(p) for p in paths}


def unused():
    require(not CLAIM.exists() and not list(RUNS.glob('*')) and not RECEIPT.exists(), 'Suffix already claimed; no retry')


def register():
    unused()
    require(not REGISTRATION.exists(), 'Suffix already registered')
    plan = reconcile()
    result = {'status': 'PROSPECTIVELY_FROZEN_NO_SUFFIX_GENERATIONS', 'registered_utc': old.b.utc_now(),
              'source_head': plan['source_head'], 'bindings': bindings(),
              'original_source_hashes': plan['source_hashes'], 'original_manifest_sha256': sha(base.FROZEN),
              'request_sha256': [r['request_sha256'] for r in plan['requests'][PREFIX:]],
              'maximum_attempts': N, 'baseline_generations': BASE_GENERATIONS, 'baseline_seconds': BASE_SECONDS,
              'amendment': load(AMENDMENT)}
    write(REGISTRATION, result)
    return {'status': result['status'], 'maximum_attempts': N}


def validate():
    plan, registration = reconcile(), load(REGISTRATION)
    require(registration['bindings'] == bindings() and registration['original_source_hashes'] == plan['source_hashes'],
            'Suffix source bindings changed')
    require(registration['original_manifest_sha256'] == sha(base.FROZEN) and
            registration['request_sha256'] == [r['request_sha256'] for r in plan['requests'][PREFIX:]],
            'Suffix request binding changed')
    return plan


def preflight(check_memory=True, check_unused=True):
    validate()
    if check_unused:
        unused()
    original = base.preflight(check_memory=check_memory, unused=False)
    return {**original, 'suffix_registration_sha256': sha(REGISTRATION),
            'suffix_bindings_sha256': old.value_sha256(bindings()),
            'baseline': {'generations_used': BASE_GENERATIONS, 'inference_seconds_used': BASE_SECONDS},
            'resources': load(AMENDMENT)['resources']}


def run(preflight_path):
    fresh, saved = preflight(), load(preflight_path)
    require(saved['status'] == 'PASS', 'Passing fresh preflight required')
    for key in ('manifest_sha256', 'registration_sha256', 'source_hashes_sha256', 'identity', 'baseline',
                'suffix_registration_sha256', 'suffix_bindings_sha256'):
        require(saved[key] == fresh[key], 'Preflight changed: ' + key)
    plan = validate()
    with old.b.writer_lock(PRIVATE):
        unused()
        claim = {'registration_sha256': sha(REGISTRATION), 'preflight_sha256': sha(preflight_path), 'maximum_attempts': N}
        write(CLAIM, claim)
        journal = old.b.RunJournal(RUNS, {'phase': 'P1 RPC unchanged request suffix v1', 'claim': claim,
                    'frozen_manifest': plan, 'suffix_registration': load(REGISTRATION),
                    'authorization': load(AMENDMENT), 'configuration': old.cfg(plan).as_dict()})
        for path, digest in {**plan['source_hashes'], **bindings()}.items():
            target = journal.directory / 'source_snapshot' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as handle:
                handle.write(Path(path).read_bytes())
            require(sha(target) == digest, 'Source snapshot mismatch')
        started, seconds, failed_seconds, attempts, responses = time.monotonic(), 0., 0., 0, 0
        status, active = 'BLOCKED', None
        try:
            journal.write('preflight', fresh)
            with old.s.Server(plan, journal) as server:
                memory = old.s.memory_observation(server.process.pid)
                journal.write('ready_memory', memory)
                require(memory['system']['available_physical'] >= old.MIN_READY_RAM, 'Ready RAM below 1 GiB')
                client = old.b.LlamaClient(old.cfg(plan).endpoint, timeout=180, audit=journal.write)
                props = client.request('/props')
                binding = old.b.validate_server_properties(props, old.cfg(plan))
                require(old.RUNTIME['backend_build'].split('-', 1)[1] in binding['build_info'], 'Backend build')
                journal.write('server_properties', {'props': props, 'validation': binding})
                for row in plan['requests'][PREFIX:]:
                    ids = client.request('/tokenize', {'content': row['prompt'], 'add_special': True,
                        'parse_special': True, 'with_pieces': False})['tokens']
                    require(ids == row['input_token_ids'], 'Live tokenizer mismatch')
                    journal.write('live_tokenizer', {'request_id': row['request_id'], 'token_ids_sha256': old.th(str(ids))})
                memory = old.s.memory_observation(server.process.pid)
                journal.write('post_tokenization_memory', memory)
                require(memory['system']['available_physical'] >= old.MIN_READY_RAM, 'Precompletion RAM below 1 GiB')
                for row in plan['requests'][PREFIX:]:
                    remaining = min(300 - seconds, 600 - (time.monotonic() - started))
                    require(remaining > 0, 'Finite suffix execution ceiling')
                    server.assert_running()
                    memory = old.s.memory_observation(server.process.pid)
                    journal.write('before_request_memory', memory)
                    require(memory['system']['available_physical'] >= old.MIN_LIVE_RAM, 'Live RAM below 512 MiB')
                    client.timeout = min(180, remaining)
                    active = row['request_id']
                    journal.write('specificity_started', row)
                    attempts += 1
                    tick = time.monotonic()
                    try:
                        response = client.request('/completion', old.payload(row))
                    except BaseException:
                        elapsed = time.monotonic() - tick
                        seconds += elapsed
                        failed_seconds += elapsed
                        journal.write('specificity_failed', {'request_id': active, 'latency_seconds': elapsed})
                        raise
                    elapsed = time.monotonic() - tick
                    seconds += elapsed
                    journal.write('specificity_raw', {'request_id': active, 'response': response, 'latency_seconds': elapsed})
                    responses += 1
                    old.b.validate_completion(response, row['input_token_ids'])
                    require(type(response.get('tokens_predicted')) is int and 0 <= response['tokens_predicted'] <= 96,
                            'Native token count outside allocation')
                    active = None
                    print(json.dumps({'suffix_completed': responses, 'suffix_planned': N, 'seconds': round(seconds, 3)}), flush=True)
                server.assert_running()
                after = preflight(check_memory=False, check_unused=False)
                require(after['identity'] == fresh['identity'], 'Postflight identity')
                journal.write('postflight', after)
            status = 'PASS'
        except BaseException as exc:
            status = 'PARTIAL' if attempts else 'BLOCKED'
            journal.write('failure', {'type': type(exc).__name__, 'message': str(exc), 'request_id': active})
        summary = {'status': status, 'attempts': attempts, 'responses': responses,
                   'completion_inference_seconds': seconds, 'failed_seconds': failed_seconds,
                   'wall_seconds': time.monotonic() - started, 'retries': 0,
                   'unattempted': N - attempts, 'run_directory': journal.directory.as_posix()}
        journal.finish(**summary)
        write(journal.directory / 'summary.json', summary)
        write(RECEIPT, {**summary, 'cumulative_generations': BASE_GENERATIONS + attempts,
                       'cumulative_inference_seconds': BASE_SECONDS + seconds,
                       'terminal_event_sha256': journal.previous_hash,
                       'original_receipt_sha256': sha(ORIGINAL_RECEIPT), 'suffix_registration_sha256': sha(REGISTRATION)})
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('register', 'validate', 'preflight', 'run'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--preflight', type=Path)
    args = parser.parse_args()
    if args.action == 'register':
        result = register()
    elif args.action == 'validate':
        result = {'status': 'PASS', 'unattempted_suffix': len(validate()['requests'][PREFIX:])}
    elif args.action == 'preflight':
        require(args.output is not None and args.output.parent == OUT, 'Immutable public preflight path required')
        try:
            result = preflight()
        except Exception as exc:
            memory = old.s.memory_observation(__import__('os').getpid())
            result = {'status': 'FAIL', 'checked_utc': old.b.utc_now(), 'error': str(exc),
                      'memory': memory, 'new_generations': 0, 'minimum_available_ram': old.MIN_PREFLIGHT_RAM}
        write(args.output, result)
    else:
        require(args.preflight is not None, 'Preflight required')
        result = run(args.preflight)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
