"""Bounded post-hoc diagnostics of sealed English outputs; no semantic labels."""
import argparse
from collections import Counter
import json
from pathlib import Path
from unittest.mock import patch

import english_model_comparison_analysis_v1 as pair
import english_sfh_archival_reproduce_v1 as archive

PUBLIC = Path('docs/validation/p1/english_novelty_synthesis_v1')
PRIVATE = Path('.local/experiments/english_novelty_synthesis_v1')
SCOPE = PUBLIC / 'analysis_scope_v1.json'
IMPLEMENTATION = PUBLIC / 'diagnostic_implementation_v1.json'
RESULT = PUBLIC / 'response_diagnostics_v1.json'
ROWS = PRIVATE / 'response_diagnostics_private_v1.json'
METRICS = ('raw_empty', 'whitespace_empty', 'repeat5_excess', 'repeat5_any',
           'prefix20_repeat5_excess')
require, sha, load = pair.require, pair.sha, pair.load
primary, independent = pair.primary, pair.independent


def measure(text):
    require(type(text) is str, 'Native content must be text, never missing execution')
    words = primary.words(text)
    windows = primary.fivegrams(text)
    prefix = [tuple(words[i:i + 5]) for i in range(16)] if len(words) >= 20 else []
    rate = lambda items: (len(items) - len(set(items))) / len(items) if items else None
    return {'raw_empty': int(text == ''), 'whitespace_empty': int(text.strip() == ''),
            'repeat5_excess': rate(windows),
            'repeat5_any': int(len(set(windows)) < len(windows)) if windows else None,
            'prefix20_repeat5_excess': rate(prefix)}


def direct_measure(text):
    """Separate recurrence arithmetic; lexical extraction deliberately shared."""
    words = primary.words(text)
    def count(tokens):
        counts = Counter(tuple(tokens[i:i + 5]) for i in range(len(tokens) - 4))
        total = sum(counts.values())
        excess = sum(n - 1 for n in counts.values())
        return (excess / total, int(excess > 0)) if total else (None, None)
    full, any_repeat = count(words)
    return dict(zip(METRICS, (int(len(text) == 0), int(not any(not c.isspace() for c in text)),
                              full, any_repeat, count(words[:20])[0] if len(words) >= 20 else None)))


def measured_rows(requests, raw):
    require(len(requests) == len(raw) == 100 and
            {r['request_id'] for r in requests} == set(raw), 'Complete unique100 required')
    rows = []
    for request in requests:
        text = raw[request['request_id']]['response']['content']
        values = measure(text)
        independent.compare(values, direct_measure(text), 'Independent literal arithmetic')
        rows.append({k: request[k] for k in ('request_id', 'speaker_id', 'case_id', 'condition', 'phase')} |
                    {'measurements': values, 'content_sha256': independent.text_hash(text),
                     'word_count': len(primary.words(text))})
    require(len({r['speaker_id'] for r in rows}) == 5 and
            len({(r['speaker_id'], r['case_id']) for r in rows}) == 10,
            'Frozen five-speaker ten-context scope changed')
    return rows


def summarize(rows):
    with patch.object(pair, 'METRICS', METRICS):
        estimates = pair.summarize(rows)
    return {'allocation': len(rows), 'overall': {
        metric: {**primary.describe([r['measurements'][metric] for r in rows]),
                 'allocated': len(rows), 'inapplicable': sum(r['measurements'][metric] is None for r in rows)}
        for metric in METRICS}, 'estimates': estimates}


def calculate(scope_sha, implementation_sha):
    scope = archive.checked_json(SCOPE, scope_sha)
    implementation = archive.checked_json(IMPLEMENTATION, implementation_sha)
    require(implementation['scope_sha256'] == scope_sha and
            implementation['status'] == 'FROZEN_BEFORE_DIAGNOSTIC_EXTRACTION', 'Analysis scope binding')
    for name, digest in implementation['sources'].items():
        require(sha(Path(name)) == digest, 'Diagnostic implementation changed: ' + name)
    data = scope['data']
    reproduced = archive.reproduce(data['original_analysis_sha256'], data['original_reproduction_sha256'])
    old = archive.checked_json(archive.ANALYSIS, data['original_analysis_sha256'])
    requests, raw = {}, {}
    for receipt in old['run_receipts']:
        for event in independent.read_events(Path(receipt['run_directory'])):
            entry = event['data']
            if event['kind'] == 'english_sfh_started':
                require(entry['request_id'] not in requests, 'Repeated original attempt')
                requests[entry['request_id']] = entry
            elif event['kind'] == 'english_sfh_raw':
                require(entry['request_id'] not in raw, 'Repeated original response')
                raw[entry['request_id']] = entry
    rows = {'qwen3_06b_historical': measured_rows(list(requests.values()), raw)}
    runs = {v: pair.audit_run(v, data[v + '_receipt_sha256']) for v in ('base', 'instruct')}
    for variant, run in runs.items():
        rows[variant] = measured_rows(run[0]['requests'], run[3])
    key = lambda row: (row['speaker_id'], row['case_id'], row['condition'])
    require(all({key(r) for r in group} == {key(r) for r in rows['base']} for group in rows.values()),
            'Configurations no longer share the same source grid')
    with patch.object(pair, 'METRICS', METRICS):
        matched = pair.paired_rows(rows['base'], rows['instruct'])
    private = {'rows': rows, 'paired_instruct_minus_base': matched}
    report = {'schema': 'english_response_diagnostics_v1', 'status': 'COMPLETE_POSTHOC_ANALYSIS',
        'new_generations': 0, 'new_human_labels': 0, 'responses': 300, 'speakers': 5,
        'models': {name: summarize(group) for name, group in rows.items()},
        'paired_instruct_minus_base': summarize(matched),
        'bindings': {'scope_sha256': scope_sha, 'implementation_sha256': implementation_sha,
                     'source_inputs': data, 'original_reproduction': reproduced,
                     'new_terminals': {v: run[1]['terminal_event_sha256'] for v, run in runs.items()},
                     'private_canonical_sha256': independent.value_hash(private)},
        'definitions': scope['diagnostics'], 'analysis_policy': scope['analysis'],
        'resources': scope['resource'],
        'limits': 'Post-hoc literal diagnostics, not semantic repetition, fidelity or accuracy. '
                  'Short-output NA is not zero; complete-speaker subsets differ by metric. '
                  'First20words equalize opportunities only in a post-treatment-selected subset. '
                  'No human mapping opened, independent experimental validation, pure size effect or novelty claim.'}
    for name, digest in implementation['sources'].items():
        require(sha(Path(name)) == digest, 'Sources changed during extraction')
    return report, private


def run(action, scope_sha, implementation_sha):
    require(action in ('write', 'verify'), 'Unknown diagnostic action')
    if action == 'write':
        require(not RESULT.exists() and not ROWS.exists(), 'No overwrite of diagnostic evidence')
    report, private = calculate(scope_sha, implementation_sha)
    if action == 'write':
        pair.controller.old.write(ROWS, private)
        pair.controller.old.write(RESULT, report)
    else:
        independent.compare(load(RESULT), report, 'Reproduced public diagnostics')
        independent.compare(load(ROWS), private, 'Reproduced private diagnostics')
    return {'status': 'WRITTEN' if action == 'write' else 'RAW_REPRODUCTION_PASS',
            'responses': 300, 'new_generations': 0, 'human_labels_created': 0,
            'result_sha256': sha(RESULT), 'private_file_sha256': sha(ROWS)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('write', 'verify'))
    parser.add_argument('--scope-sha256', required=True)
    parser.add_argument('--implementation-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.action, args.scope_sha256, args.implementation_sha256), indent=2))
