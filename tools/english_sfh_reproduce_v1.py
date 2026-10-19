"""Independent English S/F/H raw-to-results arithmetic, not human validation.

Only the generic hash-chain reader is shared. No study runner, scorer or primary
analysis is imported. No inference or participant-text printing is supported.
"""
import argparse
import ast
import base64
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re

from personaslm.journal import read_events

PUBLIC = Path('docs/validation/p1/english_real_speaker_stage_v1')
PRIVATE = Path('.local/experiments/english_sfh_v1')
BASELINE = Path('docs/validation/p1/real_persona_chat_continuation_v1/execution_receipt_v1.json')
BASELINE_SHA = '4e4d2cae32d9eaff8916ad437682fd3e97624506bc93c4d6e39c409d34439f23'
BASE_GENERATIONS, BASE_SECONDS = 688, 3973.1201058999386
METRICS = ('output_tokens', 'latency_seconds', 'native_eos', 'native_limit', 'output_words', 'source_fivegram_coverage')
CONDITIONS = tuple(f'C{i}' for i in range(8)) + ('M_STYLE', 'N_STYLE')
CONTRAST_MASKS = {'S': 1, 'F': 2, 'H': 4, 'SF': 3, 'SH': 5, 'FH': 6, 'SFH': 7}
STYLE_PAIRS = {'correct_minus_mismatched': ('C7', 'M_STYLE'),
               'correct_minus_pooled': ('C7', 'N_STYLE'), 'correct_minus_no_style_at_FH': ('C7', 'C6')}


def require(value, message):
    if not value:
        raise AssertionError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def value_hash(value):
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def compare(actual, expected, label='result'):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and actual.keys() == expected.keys(), label + ': key mismatch')
        for key in expected:
            compare(actual[key], expected[key], label + '.' + key)
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), label + ': length mismatch')
        for a, b in zip(actual, expected):
            compare(a, b, label + '[]')
    elif type(expected) is float:
        require(type(actual) in (int, float) and math.isclose(actual, expected, rel_tol=0, abs_tol=1e-10),
                label + ': arithmetic discrepancy')
    else:
        require(actual == expected, label + ': value discrepancy')


def average(values):
    return math.fsum(values) / len(values) if values else None


def summary(values, leave_out=False):
    values = [v for v in values if v is not None]
    ordered = sorted(values)
    count = len(ordered)
    result = {'n': count, 'mean': average(values),
              'median': (ordered[count // 2] if count % 2 else average(ordered[count // 2 - 1:count // 2 + 1])) if count else None,
              'range': [ordered[0], ordered[-1]] if count else None}
    if leave_out:
        deleted = [average(values[:i] + values[i + 1:]) for i in range(count)] if count > 1 else []
        result['leave_one_speaker_out_mean_range'] = [min(deleted), max(deleted)] if deleted else None
    return result


def measurements(request, response, latency):
    generated = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", response['content'].casefold())
    source = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", request['messages'][-1]['content'].casefold())
    windows = [tuple(generated[i:i + 5]) for i in range(max(0, len(generated) - 4))]
    original = {tuple(source[i:i + 5]) for i in range(max(0, len(source) - 4))}
    return {'output_tokens': response['tokens_predicted'], 'latency_seconds': latency,
            'native_eos': int(response.get('stop_type') == 'eos'), 'native_limit': int(response.get('stop_type') == 'limit'),
            'output_words': len(generated),
            'source_fivegram_coverage': sum(window in original for window in windows) / len(windows) if windows else None}


def estimates(rows):
    grid, speaker_cases = {}, defaultdict(set)
    for row in rows:
        key = row['speaker_id'], row['case_id'], row['condition']
        require(key not in grid and row['condition'] in CONDITIONS, 'Duplicate/unknown analysis cell')
        grid[key] = row['measurements']
        speaker_cases[row['speaker_id']].add(row['case_id'])
    require(all(len(cases) == 2 for cases in speaker_cases.values()), 'Two contexts per speaker required')
    require(all((speaker, case, condition) in grid for speaker, cases in speaker_cases.items()
                for case in cases for condition in CONDITIONS), 'Allocated factorial/diagnostic cells missing')
    condition_summary, effects, controls = {}, {}, {}
    for metric in METRICS:
        condition_summary[metric] = {}
        for condition in CONDITIONS:
            values = [row['measurements'][metric] for row in rows if row['condition'] == condition]
            condition_summary[metric][condition] = {**summary(values), 'allocated': len(values),
                                                   'missing_or_inapplicable': values.count(None)}
        effects[metric], controls[metric] = {}, {}
        for name, mask in CONTRAST_MASKS.items():
            complete = []
            for speaker, cases in speaker_cases.items():
                case_effects = []
                for case in sorted(cases):
                    values = [grid[speaker, case, f'C{i}'][metric] for i in range(8)]
                    if None not in values:
                        weights = [(-1) ** ((mask & (~i) & 7).bit_count()) for i in range(8)]
                        case_effects.append(math.fsum(v * w for v, w in zip(values, weights)) / 4)
                if len(case_effects) == 2:
                    complete.append(average(case_effects))
            effects[metric][name] = {**summary(complete, True), 'incomplete_speakers': len(speaker_cases) - len(complete)}
        for name, (high, low) in STYLE_PAIRS.items():
            complete = []
            for speaker, cases in speaker_cases.items():
                pairs = [(grid[speaker, case, high][metric], grid[speaker, case, low][metric]) for case in sorted(cases)]
                if all(a is not None and b is not None for a, b in pairs):
                    complete.append(average([a - b for a, b in pairs]))
            controls[metric][name] = {**summary(complete, True), 'incomplete_speakers': len(speaker_cases) - len(complete)}
    return {'condition_summary': condition_summary, 'factorial_effects': effects, 'style_controls': controls}


def verify_request(request):
    require(value_hash({k: v for k, v in request.items() if k != 'request_sha256'}) == request['request_sha256'],
            'Request SHA mismatch')
    ids = request['input_token_ids']
    require(isinstance(ids, list) and ids and all(type(i) is int and i >= 0 for i in ids), 'Invalid input IDs')
    require(value_hash(ids) == request['input_token_ids_sha256'] and len(ids) == request['input_tokens'] and
            len(ids) + 128 <= 2048, 'Input token hash/context mismatch')
    require(text_hash(request['prompt']) == request['prompt_sha256'], 'Prompt hash mismatch')


def expected_payload(row):
    return {'prompt': row['input_token_ids'], 'n_predict': 128, 'temperature': 0.0, 'top_p': 1.0,
            'seed': 42, 'cache_prompt': False, 'stop': [], 'ignore_eos': False, 'return_tokens': True, 'stream': False}


def verify_native_receipt(value, request):
    require(value['returncode'] == 0 and value['generation_requests'] == 0 and
            value['prompt_sha256'] == request['prompt_sha256'], 'Offline native tokenizer receipt')
    stdout, stderr = bytes.fromhex(value['stdout_hex']), bytes.fromhex(value['stderr_hex'])
    require(hashlib.sha256(stdout).hexdigest() == value['stdout_sha256'] and
            hashlib.sha256(stderr).hexdigest() == value['stderr_sha256'], 'Native stdout/stderr hash')
    require(ast.literal_eval(stdout.decode('utf-8').strip()) == request['input_token_ids'],
            'Offline native token IDs differ from frozen request')


def reconcile(plan, receipt, events, base_generations, base_seconds):
    for row in plan['requests']:
        verify_request(row)
    starts = [e['data'] for e in events if e['kind'] == 'english_sfh_started']
    require(starts == plan['requests'][:len(starts)] and len(starts) == receipt['attempts'], 'Attempted prefix/count mismatch')
    require(len({r['request_id'] for r in plan['requests']}) == len(plan['requests']), 'Duplicate allocated ID')
    completion_payloads = [e['data']['payload'] for e in events if e['kind'] == 'http_request' and e['data']['route'] == '/completion']
    require(completion_payloads == [expected_payload(r) for r in starts], 'Actual completion request/payload mismatch')
    token_index, pending_token, active, response_body, http_elapsed = 0, None, None, None, None
    observed, failed = {}, []
    for event in events:
        kind, data = event['kind'], event['data']
        if kind == 'http_request' and data['route'] == '/tokenize':
            require(active is None and pending_token is None and token_index < len(plan['requests']), 'Tokenizer sequence')
            pending_token = plan['requests'][token_index]
            require(data['payload'] == {'content': pending_token['prompt'], 'add_special': True,
                    'parse_special': True, 'with_pieces': False}, 'Actual tokenizer request mismatch')
        elif kind == 'http_response' and data['route'] == '/tokenize' and data.get('status') == 200:
            require(pending_token is not None, 'Unbound tokenization response')
            tokens = json.loads(base64.b64decode(data['body_base64']))['tokens']
            require(tokens == pending_token['input_token_ids'], 'Live native token IDs mismatch')
            token_index += 1
            pending_token = None
        elif kind == 'english_sfh_started':
            require(active is None and token_index == len(plan['requests']), 'Completion before full native preflight')
            active, response_body, http_elapsed = data['request_id'], None, None
        elif kind == 'http_response' and data['route'] == '/completion':
            require(active is not None, 'Unbound HTTP completion response')
            http_elapsed = data.get('elapsed_seconds')
            if data.get('status') == 200 and not data.get('incomplete'):
                try:
                    response_body = json.loads(base64.b64decode(data['body_base64']))
                except (ValueError, UnicodeDecodeError):
                    response_body = None
        elif kind == 'english_sfh_raw':
            require(active == data['request_id'] and active not in observed and response_body == data['response'],
                    'Raw response/HTTP bytes/attempt identity mismatch')
            require(type(http_elapsed) in (int, float) and 0 <= http_elapsed <= data['latency_seconds'] + 1e-6,
                    'Inner/outer elapsed mismatch')
            observed[active], active = data, None
        elif kind == 'english_sfh_failed':
            require(active == data['request_id'] and active not in observed, 'Failed attempt identity mismatch')
            failed.append(data)
            active = None
    require(active is None and len(observed) == receipt['responses'] and len(starts) == len(observed) + len(failed),
            'Unresolved attempt/response/failure accounting')
    elapsed = [r['latency_seconds'] for r in list(observed.values()) + failed]
    require(all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in elapsed), 'Invalid latency')
    seconds = math.fsum(elapsed)
    compare(seconds, receipt['completion_inference_seconds'], 'inference cost')
    compare(math.fsum(r['latency_seconds'] for r in failed), receipt['failed_seconds'], 'failed cost')
    require(receipt['cumulative_generations'] == base_generations + len(starts), 'Cumulative generation accounting')
    compare(base_seconds + seconds, receipt['cumulative_inference_seconds'], 'cumulative inference cost')
    require(receipt['unattempted'] == len(plan['requests']) - len(starts) and receipt['retries'] == 0, 'Remaining/retry accounting')
    rows = []
    for row in plan['requests']:
        raw = observed.get(row['request_id'])
        if raw:
            response = raw['response']
            require(isinstance(response['content'], str) and response.get('truncated') is False and
                    type(response.get('tokens_evaluated')) is int and response['tokens_evaluated'] == len(row['input_token_ids']),
                    'Native completion input accounting')
            if isinstance(response.get('prompt'), list):
                require(response['prompt'] == row['input_token_ids'], 'Native prompt IDs changed')
            require(type(response.get('tokens_predicted')) is int and 0 <= response['tokens_predicted'] <= 128,
                    'Native output token limit')
        rows.append({k: row[k] for k in ('request_id', 'speaker_id', 'case_id', 'condition', 'phase')} |
                    {'measurements': measurements(row, raw['response'], raw['latency_seconds']) if raw else dict.fromkeys(METRICS)})
    return rows, seconds, len(failed)


def relative(path):
    resolved = Path(path).resolve()
    require(resolved.is_relative_to(Path.cwd().resolve()), 'Evidence path escaped repository')
    return resolved.relative_to(Path.cwd().resolve())


def audit_run(batch):
    receipt_path = PUBLIC / (batch + '_execution_receipt_v1.json')
    receipt = load(receipt_path)
    folder = Path(receipt['run_directory'])
    relative(folder)
    require(folder.resolve().is_relative_to(PRIVATE.resolve()), 'Run directory outside private study')
    archive = load(folder / 'manifest.json')
    plan = archive['frozen_manifest']
    frozen = PRIVATE / batch / 'frozen_manifest_v1.json'
    registration = load(PUBLIC / (batch + '_registration_v1.json'))
    require(plan == load(frozen) and sha(frozen) == receipt['manifest_sha256'] == registration['manifest_sha256'], 'Frozen manifest binding')
    require(archive['claim'] == load(PRIVATE / batch / 'claim_v1.json'), 'Exclusive execution claim changed')
    events = read_events(folder)
    require(events[-1]['kind'] == 'run_finished' and events[-1]['event_hash'] == receipt['terminal_event_sha256'], 'Unsealed terminal')
    require(all(receipt[k] == v for k, v in events[-1]['data'].items()), 'Receipt/terminal mismatch')
    hash_only = {e['data']['path']: e['data']['sha256'] for e in events if e['kind'] == 'hash_only_input'}
    for name, digest in plan['source_hashes'].items():
        require(sha(folder / 'source_snapshot' / relative(name)) == digest, 'Source snapshot hash mismatch')
    for name, digest in plan['input_hashes'].items():
        if name in plan['source_hashes']:
            require(plan['source_hashes'][name] == digest, 'Conflicting bound input')
        elif name in hash_only:
            require(hash_only[name] == digest and sha(Path(name)) == digest, 'Hash-only retained input mismatch')
        else:
            require(sha(folder / 'input_snapshot' / relative(name)) == digest, 'Input snapshot hash mismatch')
    for request in plan['requests']:
        tokenizer_path = PRIVATE / batch / 'native_tokenizer' / (request['request_id'] + '.json')
        require(tokenizer_path.as_posix() in plan['input_hashes'], 'Native registration evidence not bound')
        verify_native_receipt(load(folder / 'input_snapshot' / tokenizer_path), request)
    require(sha(BASELINE) == BASELINE_SHA, '688 baseline receipt changed')
    historical = load(BASELINE)
    require(historical['cumulative_generations'] == BASE_GENERATIONS and
            historical['cumulative_inference_seconds'] == BASE_SECONDS, '688 historical cost mismatch')
    if batch == 'development':
        require(plan['prior_receipt'] == {'path': BASELINE.as_posix(), 'sha256': BASELINE_SHA}, 'Development predecessor')
        base_generations, base_seconds = BASE_GENERATIONS, BASE_SECONDS
    else:
        prior_plan, prior_receipt, _, _, _ = audit_run('development')
        prior_path = PUBLIC / 'development_execution_receipt_v1.json'
        require(plan['prior_receipt'] == {'path': prior_path.as_posix(), 'sha256': sha(prior_path)} and
                prior_receipt['status'] == 'PASS' and prior_receipt['responses'] == len(prior_plan['requests']),
                'Independent batch predecessor not complete')
        require({r['speaker_id'] for r in plan['requests']}.isdisjoint(r['speaker_id'] for r in prior_plan['requests']),
                'Development/validation speaker overlap')
        base_generations, base_seconds = prior_receipt['cumulative_generations'], prior_receipt['cumulative_inference_seconds']
    rows, seconds, failed = reconcile(plan, receipt, events, base_generations, base_seconds)
    return plan, receipt, rows, seconds, failed


def reproduce(batch):
    plan, receipt, rows, seconds, failed = audit_run(batch)
    primary_path = PUBLIC / (batch + '_analysis_v1.json')
    primary = load(primary_path)
    require(primary['execution'] == receipt and primary['batch'] == batch, 'Primary receipt binding')
    compare(estimates(rows), primary['estimates'])
    private_path = PRIVATE / (batch + '_analysis_private_v1.json')
    private = load(private_path)
    compare(rows, private['rows'], 'private analysis rows')
    require(value_hash(rows) == primary['private_analysis_sha256'], 'Canonical private row hash mismatch')
    frozen_source = plan['source_hashes'].get('tools/english_sfh_analysis_v1.py', plan['input_hashes'].get('tools/english_sfh_analysis_v1.py'))
    require(frozen_source == primary['source_sha256'], 'Primary analysis implementation not prospectively bound')
    return {'schema': 'english_sfh_independent_arithmetic_reproduction_v1', 'status': 'PASS', 'batch': batch,
            'checked_utc': datetime.now(timezone.utc).isoformat(), 'attempts': receipt['attempts'],
            'responses': receipt['responses'], 'failed_calls': failed, 'completion_inference_seconds': seconds,
            'cumulative_generations': receipt['cumulative_generations'],
            'cumulative_inference_seconds': receipt['cumulative_inference_seconds'],
            'estimates': estimates(rows), 'human_labels_created': 0,
            'scope': 'INDEPENDENT_ARITHMETIC_NOT_INDEPENDENT_EXPERIMENT_OR_HUMAN_VALIDATION',
            'bindings': {'manifest_sha256': receipt['manifest_sha256'], 'terminal_event_sha256': receipt['terminal_event_sha256'],
                         'receipt_sha256': sha(PUBLIC / (batch + '_execution_receipt_v1.json')),
                         'primary_analysis_sha256': sha(primary_path), 'private_rows_canonical_sha256': value_hash(rows),
                         'private_analysis_file_sha256': sha(private_path), 'reproduction_source_sha256': sha(__file__)},
            'limits': 'Native stopping, length, latency and five-word surface overlap are not semantic Persona Fidelity. '
                      'Missing/inapplicable outcomes retained; complete-speaker descriptives and leave-one-out ranges are not confidence intervals. '
                      'Shared journal reader; no model generation repeatability or independent peak-memory reproduction. Public clone-only reproduction PARTIAL.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', choices=('development', 'validation'), required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = reproduce(args.batch)
    if args.write:
        output = PUBLIC / (args.batch + '_independent_reproduction_v1.json')
        with output.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
