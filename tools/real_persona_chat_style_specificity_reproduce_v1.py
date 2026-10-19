"""Independent arithmetic reproduction of the frozen RPC four-arm study.

Reads only this study's private manifest/journal/analysis and public receipts.
Never imports its controller/scorer, runs inference, or prints participant rows.
Shared infrastructure: existing hash-chain reader and immutable JSON writer.
"""
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata

from personaslm.journal import atomic_json, read_events


PUBLIC = Path('docs/validation/p1/real_persona_chat_style_specificity_v1')
PRIVATE = Path('.local/experiments/real_persona_chat_style_specificity_v1')
ARMS = ('NONE', 'CORRECT', 'MISMATCH', 'LENGTH')
PAIRS = (('CORRECT', 'MISMATCH'), ('CORRECT', 'LENGTH'), ('LENGTH', 'NONE'))
METRICS = ('margin', 'prefix_margin', 'eos_margin', 'output_chars', 'tokens', 'seconds')
FEATURES = ('hiragana_rate', 'katakana_rate', 'han_rate', 'latin_rate',
            'digit_rate', 'punctuation_rate', 'symbol_rate')


def check(condition, label):
    if not condition:
        raise AssertionError(label)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def average(values):
    return math.fsum(values) / len(values) if values else None


def norm(text):
    check(isinstance(text, str), 'Response/reference must be text')
    return ''.join(unicodedata.normalize('NFKC', text).casefold().split())


def rates(turns, prefix=None):
    normalized = [norm(text) for text in turns]
    if prefix is not None:
        normalized = [text[:prefix] for text in normalized]
    # Frozen style_vector sanitizes AFTER normalization and optional truncation.
    text = ''.join(re.sub(r'<[^>]+>', '', unit).replace('＊＊', '') for unit in normalized)
    denominator = max(1, len(text))
    counts = [0] * 7
    for char in text:
        code = ord(char)
        indicators = (0x3040 <= code <= 0x309f, 0x30a0 <= code <= 0x30ff,
                      0x3400 <= code <= 0x4dbf or 0x4e00 <= code <= 0x9fff,
                      'a' <= char <= 'z' or 'A' <= char <= 'Z', char.isdigit(),
                      unicodedata.category(char).startswith('P'),
                      unicodedata.category(char).startswith('S'))
        for index, present in enumerate(indicators):
            counts[index] += int(present)
    return tuple(value / denominator for value in counts)


def distances(text, case, prefix=None):
    observed = rates([text], prefix)
    own = rates(case['reference_turns'], prefix)
    donor = rates(case['donor_reference_turns'], prefix)
    own_distance = math.fsum(abs(a - b) for a, b in zip(observed, own)) / 7
    donor_distance = math.fsum(abs(a - b) for a, b in zip(observed, donor)) / 7
    return own_distance, donor_distance, donor_distance - own_distance


def boundary(response):
    for name in ('stopped_limit', 'stopped_eos', 'stopped_word'):
        check(response.get(name) is None or type(response[name]) is bool, 'Invalid native stop flag')
    stop = response.get('stop_type')
    limit = response.get('stopped_limit', False) or stop == 'limit'
    eos = response.get('stopped_eos', False) or stop in ('eos', 'eog')
    word = response.get('stopped_word', False) or stop == 'word'
    return bool(eos and not limit and not word), sum(map(bool, (limit, eos, word))) > 1


def stats(values):
    loo = [average(values[:i] + values[i + 1:]) for i in range(len(values))] if len(values) > 1 else []
    return {'n': len(values), 'mean': average(values),
            'range': [min(values), max(values)] if values else None,
            'leave_one_speaker_out_mean_range': [min(loo), max(loo)] if loo else None}


def aggregate(rows, cases):
    by_case = {case['case_id']: {} for case in cases}
    for row in rows:
        check(row['arm'] not in by_case[row['case_id']], 'Duplicate context arm')
        by_case[row['case_id']][row['arm']] = row
    check(all(set(group) == set(ARMS) for group in by_case.values()), 'Incomplete allocated arm map')
    contrasts = {}
    for metric in METRICS:
        contrasts[metric] = {}
        for high, low in PAIRS:
            complete_speakers, known = [], []
            for speaker in range(8):
                selected = [case for case in cases if case['speaker_index'] == speaker]
                check(len(selected) == 2, 'Two contexts per speaker required')
                differences = []
                for case in selected:
                    group = by_case[case['case_id']]
                    left, right = group[high][metric], group[low][metric]
                    if left is not None and right is not None:
                        differences.append(left - right)
                known.extend(differences)
                if len(differences) == 2:
                    complete_speakers.append(average(differences))
            missing = len(cases) - len(known)
            result = {**stats(complete_speakers), 'paired_contexts': len(known), 'missing_contexts': missing}
            if metric in ('margin', 'prefix_margin', 'eos_margin'):
                result['all_16_context_logical_bounds'] = [
                    (math.fsum(known) - 2 * missing) / len(cases),
                    (math.fsum(known) + 2 * missing) / len(cases)]
            contrasts[metric][high + '-' + low] = result
    conditions = {}
    for arm in ARMS:
        group = [row for row in rows if row['arm'] == arm]
        conditions[arm] = {}
        for metric in ('margin', 'prefix_margin', 'output_chars', 'tokens', 'input_tokens', 'seconds'):
            values = [row[metric] for row in group if row[metric] is not None]
            conditions[arm][metric] = {'n': len(values), 'mean': average(values)}
    return conditions, contrasts


def same(recomputed, recorded, label):
    """Compare only independently recomputed fields; never serialize private values on failure."""
    if isinstance(recomputed, dict):
        check(isinstance(recorded, dict), label + ': object required')
        for key, value in recomputed.items():
            check(key in recorded, label + ': missing field ' + key)
            same(value, recorded[key], label + '.' + key)
    elif isinstance(recomputed, (tuple, list)):
        check(isinstance(recorded, (list, tuple)) and len(recomputed) == len(recorded), label + ': array shape')
        for left, right in zip(recomputed, recorded):
            same(left, right, label)
    elif type(recomputed) is float:
        check(type(recorded) in (int, float) and math.isfinite(recorded) and
              math.isclose(recomputed, recorded, rel_tol=1e-12, abs_tol=1e-12), label + ': numeric mismatch')
    else:
        check(recomputed == recorded, label + ': mismatch')


def reproduce():
    design = load(PUBLIC / 'design_v1.json')
    registration = load(PUBLIC / 'registration_v1.json')
    frozen_path = PRIVATE / 'frozen_manifest_v1.json'
    check(sha(frozen_path) == registration['private_manifest_sha256'], 'Frozen manifest binding')
    plan = load(frozen_path)
    cases, requests = plan['cases'], plan['requests']
    check(len(cases) == 16 and len(requests) == 64, 'Registered allocation')
    check(design['primary_proxy']['features'] == list(FEATURES), 'Primary feature specification changed')
    check(plan['source_hashes'] == registration['source_hashes'], 'Registered source bindings')
    for path, expected in plan['source_hashes'].items():
        check(sha(Path(path)) == expected, 'Frozen source hash mismatch: ' + path)
    runs = list((PRIVATE / 'runs').iterdir())
    check(len(runs) == 1 and runs[0].is_dir(), 'Exactly one run required')
    run = runs[0]
    check(load(run / 'manifest.json')['frozen_manifest'] == plan, 'Journal manifest mismatch')
    events = read_events(run)
    check(events and events[-1]['kind'] == 'run_finished', 'Terminal journal required')
    started = [e['data'] for e in events if e['kind'] == 'specificity_started']
    raw = [e['data'] for e in events if e['kind'] == 'specificity_raw']
    failed = [e['data'] for e in events if e['kind'] == 'specificity_failed']
    check(started == requests[:len(started)], 'Attempts are not a unique frozen prefix')
    sent = [e['data']['payload'] for e in events if e['kind'] == 'http_request' and e['data']['route'] == '/completion']
    expected_payloads = [{'prompt': r['input_token_ids'], 'n_predict': 96,
                         'temperature': 0.0, 'top_p': 1.0, 'seed': 42, 'cache_prompt': False,
                         'stop': [], 'ignore_eos': False, 'return_tokens': True, 'stream': False} for r in started]
    check(sent == expected_payloads, 'HTTP payload or inference configuration mismatch')
    bodies = [json.loads(base64.b64decode(e['data']['body_base64'], validate=True)) for e in events
              if e['kind'] == 'http_response' and e['data'].get('route') == '/completion' and e['data'].get('status') == 200]
    check(bodies == [row['response'] for row in raw], 'HTTP body/raw response mismatch')
    check(len({r['request_id'] for r in raw + failed}) == len(raw) + len(failed) == len(started), 'Attempt reconciliation')
    raw_by_id = {row['request_id']: row for row in raw}
    check(set(raw_by_id).issubset({row['request_id'] for row in started}), 'Unstarted response')
    cases_by_id = {case['case_id']: case for case in cases}
    rows, own_distances, donor_distances = [], [], []
    for request in requests:
        case = cases_by_id[request['case_id']]
        row = {key: request[key] for key in ('request_id', 'case_id', 'arm', 'input_tokens')}
        row.update({key: None for key in METRICS})
        row.update(speaker_index=case['speaker_index'], text=None)
        record = raw_by_id.get(request['request_id'])
        check(request['input_tokens'] == len(request['input_token_ids']), 'Frozen input token accounting')
        if record is not None:
            response = record['response']
            check(response.get('truncated') is False and response.get('tokens_evaluated') == request['input_tokens'], 'Native input token audit')
            if isinstance(response.get('prompt'), list):
                check(response['prompt'] == request['input_token_ids'], 'Returned prompt token IDs')
            tokens = response.get('tokens_predicted')
            check(type(tokens) is int and 0 <= tokens <= 96, 'Native output token count')
            seconds = record['latency_seconds']
            check(type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0, 'Latency validity')
            text = response['content']
            eos, contradictory = boundary(response)
            row.update(text=text, output_chars=len(norm(text)), tokens=tokens, seconds=seconds,
                       native_stop_type=response.get('stop_type'), observed_native_boundary=eos,
                       contradictory_stop_flags=contradictory)
            if norm(text):
                own, donor, value = distances(text, case)
                own_distances.append(own)
                donor_distances.append(donor)
                row.update(margin=value, eos_margin=value if eos else None)
        rows.append(row)
    prefix_counts = Counter()
    for case in cases:
        group = [row for row in rows if row['case_id'] == case['case_id']]
        k = min([20] + [row['output_chars'] or 0 for row in group])
        prefix_counts[str(k)] += 1
        for row in group:
            row['prefix_k'] = k
            row['prefix_margin'] = distances(row['text'], case, k)[2] if k else None
    conditions, contrasts = aggregate(rows, cases)
    public_path = PUBLIC / 'analysis_v1.json'
    private_path = PRIVATE / 'analysis_private_v1.json'
    public, private = load(public_path), load(private_path)
    check(public['bindings']['private_analysis_sha256'] == sha(private_path), 'Private analysis binding')
    check(len(private['rows']) == len(rows), 'Private result shape')
    for row, archived in zip(rows, private['rows']):
        same({key: value for key, value in row.items() if key != 'text'}, archived, 'private_row')
        check(row['text'] == archived['text'], 'Private raw text mismatch')
    same(conditions, public['conditions'], 'condition')
    same(contrasts, public['contrasts'], 'contrast')
    same(dict(prefix_counts), public['prefix_k_distribution'], 'prefix distribution')
    stop_counts = dict(Counter(row.get('native_stop_type', 'MISSING') for row in rows))
    same(stop_counts, public['native_stop_counts'], 'stop counts')
    same(sum(row.get('contradictory_stop_flags', False) for row in rows), public['contradictory_stop_records'], 'stop contradictions')
    seconds = math.fsum(row['latency_seconds'] for row in raw + failed)
    failed_seconds = math.fsum(row['latency_seconds'] for row in failed)
    baseline = design['resources']
    generations = baseline['cumulative_baseline_generations'] + len(started)
    cumulative_seconds = baseline['cumulative_baseline_inference_seconds'] + seconds
    receipt = load(PUBLIC / 'execution_receipt_v1.json')
    expected = {'attempts': len(started), 'responses': len(raw), 'unattempted': 64 - len(started),
                'completion_inference_seconds': seconds, 'failed_seconds': failed_seconds, 'retries': 0,
                'cumulative_generations': generations, 'cumulative_inference_seconds': cumulative_seconds,
                'terminal_event_sha256': events[-1]['event_hash']}
    same(expected, receipt, 'execution receipt')
    same(expected, public['resources'], 'analysis accounting')
    same({k: v for k, v in expected.items() if k not in ('cumulative_generations', 'cumulative_inference_seconds', 'terminal_event_sha256')}, events[-1]['data'], 'terminal accounting')
    check(generations <= baseline['global_generation_limit'] and cumulative_seconds <= baseline['global_inference_seconds_limit'], 'Global resource ceiling')
    check(seconds <= baseline['batch_inference_seconds_limit'], 'Batch inference ceiling')
    return {'status': 'PASS', 'recorded_utc': datetime.now(timezone.utc).isoformat(),
            'classification': 'INDEPENDENT_ARITHMETIC_REPRODUCTION_OF_DEVELOPMENT_DATA',
            'reproduction_script_sha256': sha(Path(__file__)),
            'shared_infrastructure': ['personaslm.journal.read_events', 'personaslm.journal.atomic_json'],
            'scoring_or_controller_imports': False,
            'bindings': {'manifest_sha256': sha(frozen_path), 'registration_sha256': sha(PUBLIC / 'registration_v1.json'),
                         'analysis_sha256': sha(public_path), 'private_analysis_sha256': sha(private_path),
                         'terminal_event_sha256': events[-1]['event_hash']},
            'verified_raw_responses': len(raw), 'verified_allocated_rows': len(rows),
            'primary_features': list(FEATURES), 'own_distance_mean': average(own_distances),
            'donor_distance_mean': average(donor_distances), 'conditions': conditions, 'contrasts': contrasts,
            'prefix_k_distribution': dict(prefix_counts), 'native_stop_counts': stop_counts,
            'budget': {**expected, 'observed_output_tokens': sum(r['tokens'] or 0 for r in rows),
                       'attempted_input_tokens': sum(r['input_tokens'] for r in started),
                       'remaining_generations': baseline['global_generation_limit'] - generations,
                       'remaining_inference_seconds': baseline['global_inference_seconds_limit'] - cumulative_seconds},
            'human_labels_created': 0, 'new_generations': 0, 'reserved_validation_data_accessed': False,
            'limits': 'Not independent experimental validation, human semantic evaluation or calibrated confirmatory inference. Character-feature arithmetic is reproduced; copying/marker and memory diagnostics are outside this receipt. Public clone without private frozen cases and raw journals remains PARTIAL.'}


def self_test():
    check(norm(' Ａ\nＢ\tあ ') == 'abあ', 'NFKC/casefold/whitespace')
    same(rates(['あア漢A1!★']), [1 / 7] * 7, 'Seven independent character categories')
    same(rates(['<x>あ']), [1., 0., 0., 0., 0., 0., 0.], 'Frozen tag sanitization')
    same(rates(['ああ', 'A']), [2 / 3, 0., 0., 1 / 3, 0., 0., 0.], 'Pooled characters, not mean of turn rates')
    same(rates(['ああ', 'A'], 1), [0.5, 0., 0., 0.5, 0., 0., 0.], 'Per-turn equal prefixes')
    case = {'reference_turns': ['あ'], 'donor_reference_turns': ['A']}
    same(distances('あ', case), (0., 2 / 7, 2 / 7), 'Own/donor direction')
    check(boundary({'stop_type': 'eog'}) == (True, False), 'Native eog')
    check(boundary({'stop_type': 'limit', 'stopped_eos': True}) == (False, True), 'Contradictory native flags')
    cases, rows = [], []
    for speaker in range(8):
        for context in range(2):
            identifier = f'synthetic-{speaker}-{context}'
            cases.append({'case_id': identifier, 'speaker_index': speaker})
            for arm in ARMS:
                value = {'NONE': 0., 'CORRECT': 0.3, 'MISMATCH': -0.1, 'LENGTH': 0.2}[arm]
                rows.append({'case_id': identifier, 'arm': arm, 'input_tokens': 10,
                             **{metric: value for metric in METRICS}})
    conditions, contrasts = aggregate(rows, cases)
    same(conditions['CORRECT']['margin'], {'n': 16, 'mean': 0.3}, 'Balanced mean')
    same(contrasts['margin']['CORRECT-MISMATCH']['mean'], 0.4, 'Paired contrast')
    rows[1]['margin'] = None
    _, contrasts = aggregate(rows, cases)
    result = contrasts['margin']['CORRECT-MISMATCH']
    check(result['n'] == 7 and result['paired_contexts'] == 15 and result['missing_contexts'] == 1, 'Complete paired speakers')
    same(result['all_16_context_logical_bounds'], [0.25, 0.5], 'Missing logical bounds')
    same(result['leave_one_speaker_out_mean_range'], [0.4, 0.4], 'Leave-one-speaker-out')
    try:
        same(0.1, 0.2, 'synthetic tampering')
    except AssertionError:
        pass
    else:
        raise AssertionError('Mismatch detection')
    return {'status': 'PASS', 'classification': 'SYNTHETIC_ARITHMETIC_SELF_TEST_ONLY', 'model_generations': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = self_test() if args.self_test else reproduce()
    if args.output:
        check(args.output.parent == PUBLIC, 'Public receipt must remain in study directory')
        atomic_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
