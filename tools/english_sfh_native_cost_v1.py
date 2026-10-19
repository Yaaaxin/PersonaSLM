"""Post-hoc native cost decomposition of the sealed English100; no inference."""
import argparse
import base64
from collections import defaultdict
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from unittest.mock import patch

import english_sfh_archival_reproduce_v1 as archive

primary, independent = archive.combined.primary, archive.independent
PUBLIC = Path('docs/validation/p1/english_real_speaker_stage_v2/native_cost_analysis_v1.json')
PRIVATE = Path('.local/experiments/english_sfh_v2/native_cost_analysis_private_v1.json')
METRICS = ('input_tokens', 'output_tokens', 'prefill_seconds', 'decode_seconds',
           'latency_seconds', 'residual_seconds', 'prefill_ms_per_token', 'decode_ms_per_step')
ANALYSIS_SHA = '84468a7ccf42ba9ea8d368ee9800b211c2d97d1422c1ad7fa234b163f3066a53'
REPRODUCTION_SHA = 'ce361877f9c7f47227105c3cb4db75d9575a927258c192bd33e48cddc650cb87'
ARCHIVAL_SOURCE_SHA = '6529d10700f92e547c9d39ea348bee381f12b22c09f6d2b664197a4c4d22bd5b'
require, compare = archive.require, independent.compare


def native_metrics(request, raw):
    response, latency = raw['response'], raw['latency_seconds']
    timing = response['timings']
    numeric = ('prompt_ms', 'predicted_ms', 'prompt_per_token_ms', 'predicted_per_token_ms',
               'prompt_per_second', 'predicted_per_second')
    require(all(type(timing[k]) in (int, float) and math.isfinite(timing[k]) and timing[k] >= 0
                for k in numeric), 'Invalid native timing')
    require(type(latency) in (int, float) and math.isfinite(latency) and latency >= 0, 'Invalid wall latency')
    for name in ('prompt_n', 'predicted_n', 'cache_n'):
        require(type(timing[name]) is int and timing[name] >= 0, 'Invalid native token count')
    n_input, n_output = timing['prompt_n'], timing['predicted_n']
    require(n_input == len(request['input_token_ids']) == response['tokens_evaluated'] and n_input > 0
            and n_output == response['tokens_predicted'] and 1 < n_output <= 128,
            'Native token accounting differs from observed study')
    require(timing['cache_n'] == 0 and response['tokens_cached'] == n_input + n_output - 1,
            'Prefix reuse or final slot-token accounting changed')
    compare(timing['prompt_per_token_ms'], timing['prompt_ms'] / n_input, 'prefill rate')
    compare(timing['predicted_per_token_ms'], timing['predicted_ms'] / (n_output - 1), 'decode-step rate')
    compare(timing['prompt_per_second'], n_input * 1000 / timing['prompt_ms'], 'prefill throughput')
    compare(timing['predicted_per_second'], (n_output - 1) * 1000 / timing['predicted_ms'], 'decode throughput')
    prefill, decode = timing['prompt_ms'] / 1000, timing['predicted_ms'] / 1000
    require(latency + 1e-10 >= prefill + decode, 'Native durations exceed outer wall time')
    return dict(zip(METRICS, (n_input, n_output, prefill, decode, latency,
        latency - prefill - decode, timing['prompt_per_token_ms'], timing['predicted_per_token_ms'])))


def http_metrics(response, latency):
    """Separate native-to-number recipe; not a second observer or backend clock."""
    timing = response['timings']
    return {'input_tokens': response['tokens_evaluated'], 'output_tokens': response['tokens_predicted'],
            'prefill_seconds': timing['prompt_ms'] * .001, 'decode_seconds': timing['predicted_ms'] * .001,
            'latency_seconds': latency,
            'residual_seconds': latency - math.fsum([timing['prompt_ms'], timing['predicted_ms']]) * .001,
            'prefill_ms_per_token': timing['prompt_ms'] / response['tokens_evaluated'],
            'decode_ms_per_step': timing['predicted_ms'] / (response['tokens_predicted'] - 1)}


def extract(journals):
    rows, recalculated, seen = [], [], set()
    for run_index, events in enumerate(journals):
        active, http = None, None
        for event in events:
            data = event['data']
            if event['kind'] == 'english_sfh_started':
                require(active is None and data['request_id'] not in seen, 'Duplicate or unresolved attempt')
                active, http = data, None
                seen.add(data['request_id'])
            elif event['kind'] == 'http_response' and data.get('route') == '/completion':
                require(active is not None and http is None and data.get('status') == 200
                        and not data.get('incomplete'), 'Invalid completion HTTP sequence')
                http = json.loads(base64.b64decode(data['body_base64']))
            elif event['kind'] == 'english_sfh_raw':
                require(active is not None and data['request_id'] == active['request_id'] and
                        http == data['response'], 'Raw/HTTP identity differs')
                identity = {k: active[k] for k in ('request_id', 'speaker_id', 'case_id', 'condition', 'phase')}
                identity['run_index'] = run_index
                rows.append({**identity, 'measurements': native_metrics(active, data)})
                recalculated.append({**identity, 'measurements': http_metrics(http, data['latency_seconds'])})
                active, http = None, None
        require(active is None, 'Unresolved native response')
    compare(rows, recalculated, 'Independent native row arithmetic')
    return rows, recalculated


def variable_context_estimates(rows):
    """The frozen independent recipe with actual remaining context counts, not imputed cases."""
    grid, speakers = {}, defaultdict(set)
    for row in rows:
        key = row['speaker_id'], row['case_id'], row['condition']
        require(key not in grid, 'Duplicate cost cell')
        grid[key] = row['measurements']
        speakers[row['speaker_id']].add(row['case_id'])
    require(all((s, c, k) in grid for s, cases in speakers.items() for c in cases
                for k in independent.CONDITIONS), 'Incomplete retained context')
    result = {'condition_summary': {}, 'factorial_effects': {}, 'style_controls': {}}
    vectors = {'factorial_effects': {}, 'style_controls': {}}
    for metric in METRICS:
        result['condition_summary'][metric] = {}
        for condition in independent.CONDITIONS:
            values = [row['measurements'][metric] for row in rows if row['condition'] == condition]
            result['condition_summary'][metric][condition] = {
                **independent.summary(values), 'allocated': len(values), 'missing_or_inapplicable': 0}
        for family, definitions in (('factorial_effects', independent.CONTRAST_MASKS),
                                     ('style_controls', independent.STYLE_PAIRS)):
            result[family][metric], vectors[family][metric] = {}, {}
            for name, definition in definitions.items():
                points = []
                for speaker, cases in speakers.items():
                    effects = []
                    for case in cases:
                        if family == 'factorial_effects':
                            effects.append(math.fsum(grid[speaker, case, f'C{i}'][metric] *
                                (-1) ** ((definition & (~i) & 7).bit_count()) for i in range(8)) / 4)
                        else:
                            effects.append(grid[speaker, case, definition[0]][metric] -
                                           grid[speaker, case, definition[1]][metric])
                    points.append(math.fsum(effects) / len(effects))
                result[family][metric][name] = {**independent.summary(points, True), 'incomplete_speakers': 0}
                vectors[family][metric][name] = {'sorted_values_no_identifiers': sorted(points),
                    'positive': sum(x > 0 for x in points), 'negative': sum(x < 0 for x in points),
                    'zero': sum(x == 0 for x in points)}
    return result, vectors


def summarize(rows, recalculated):
    with patch.object(primary, 'METRICS', METRICS), patch.object(independent, 'METRICS', METRICS):
        estimates = primary.estimates(rows)
        compare(estimates, independent.estimates(recalculated), 'Frozen independent native-cost contrasts')
        restart_speakers = {r['speaker_id'] for r in rows if r['run_index'] == 1}
        restart_cases = {(r['speaker_id'], r['case_id']) for r in rows if r['run_index'] == 1}
        sensitivity = {}
        for name, keep in (
            ('exclude_entire_restart_affected_speaker', lambda r: r['speaker_id'] not in restart_speakers),
            ('exclude_entire_restart_affected_context', lambda r: (r['speaker_id'], r['case_id']) not in restart_cases)):
            retained, check = [r for r in rows if keep(r)], [r for r in recalculated if keep(r)]
            computed = primary.estimates(retained)
            different, vectors = variable_context_estimates(check)
            compare(computed, different, name)
            if name.endswith('_speaker'):
                compare(computed, independent.estimates(check), name + ' frozen independent')
            counts = defaultdict(set)
            for row in retained:
                counts[row['speaker_id']].add(row['case_id'])
            sensitivity[name] = {'responses_retained': len(retained), 'speakers_retained': len(counts),
                'contexts_per_speaker_sorted': sorted(len(cases) for cases in counts.values()),
                'unequal_context_counts': len({len(cases) for cases in counts.values()}) != 1,
                'changed_estimand': 'Equal remaining contexts within each retained speaker, then equal speakers; a different finite case/speaker set, not a repair or the original estimand.',
                'estimates': computed, 'speaker_effect_vectors': vectors}
    different, vectors = variable_context_estimates(recalculated)
    compare(estimates, different, 'Independent variable-context recipe agrees on original balanced grid')
    sums = {m: math.fsum(r['measurements'][m] for r in rows) for m in METRICS}
    errors = [abs(r['measurements']['latency_seconds'] - math.fsum(r['measurements'][m]
                  for m in ('prefill_seconds', 'decode_seconds', 'residual_seconds'))) for r in rows]
    for report in [estimates] + [x['estimates'] for x in sensitivity.values()]:
        for family in ('condition_summary', 'factorial_effects', 'style_controls'):
            for key, value in report[family]['latency_seconds'].items():
                errors.append(abs(value['mean'] - math.fsum(report[family][m][key]['mean']
                              for m in ('prefill_seconds', 'decode_seconds', 'residual_seconds'))))
    require(max(errors) <= 1e-10, 'Additive timing identity failed')
    return {'responses': len(rows), 'native_timing_coverage': len(rows), 'missing_native_timings': 0,
            'mean_per_response': {m: v / len(rows) for m, v in sums.items()},
            'separate_run_descriptives': [{'run_index': index, 'responses': sum(r['run_index'] == index for r in rows),
                'mean_per_response': {m: independent.average([r['measurements'][m] for r in rows
                    if r['run_index'] == index]) for m in METRICS}} for index in sorted({r['run_index'] for r in rows})],
            'fraction_of_total_completion_wall_seconds': {m: sums[m] / sums['latency_seconds']
                for m in ('prefill_seconds', 'decode_seconds', 'residual_seconds')},
            'cache_facts': {'reported_prompt_reuse_count_zero': len(rows),
                'final_slot_tokens_equal_input_plus_output_minus_one': len(rows),
                'interpretation': 'timings.cache_n measures reused input. tokens_cached is final slot length, not a cache-hit count.'},
            'estimates': estimates, 'speaker_effect_vectors': vectors, 'restart_sensitivity': sensitivity,
            'restart_affected_speakers': len(restart_speakers), 'restart_affected_contexts': len(restart_cases),
            'maximum_additive_identity_error_seconds': max(errors)}


def analyze():
    require(archive.sha(archive.__file__) == ARCHIVAL_SOURCE_SHA, 'Archival verifier source changed')
    verified = archive.reproduce(ANALYSIS_SHA, REPRODUCTION_SHA)
    sealed = archive.checked_json(archive.ANALYSIS, ANALYSIS_SHA)
    journals = []
    for receipt in sealed['run_receipts']:
        events = independent.read_events(Path(receipt['run_directory']))
        require(events[-1]['event_hash'] == receipt['terminal_event_sha256'], 'Sealed terminal changed')
        journals.append(events)
    rows, recalculated = extract(journals)
    require(len(rows) == 100, 'Exactly the existing English100 required')
    result = summarize(rows, recalculated)
    compare(math.fsum(r['measurements']['latency_seconds'] for r in rows),
            sealed['completion_inference_seconds'], 'Preserved inference accounting')
    result.update({'schema': 'english_sfh_native_cost_posthoc_v1',
        'level': 'POST_HOC_EXPLORATORY_DEVELOPMENT_AFTER_TIMING_INSPECTION',
        'question': 'Which native elapsed-time stages account arithmetically for observed S/F/H completion costs?',
        'new_generations': 0, 'new_inference_seconds': 0, 'human_labels_read_or_created': 0,
        'definitions': {'time': 'Backend elapsed durations on CPU, not CPU process seconds or energy. Residual includes client/server/serialization/recording overhead, not a measured single component.',
            'decode_step_denominator': 'predicted_n minus one: first token comes from the final prompt batch.',
            'effects': 'Unchanged frozen source-provision factorial scaling and equal-speaker pairing. Stage decomposition is arithmetic, not causal mediation.',
            'vectors': 'Each metric/contrast vector is independently sorted by value; no speaker identifiers or cross-metric linkage are published.'},
        'backend_definition_sources': ['https://raw.githubusercontent.com/ggml-org/llama.cpp/b11573/tools/server/server-common.h',
            'https://raw.githubusercontent.com/ggml-org/llama.cpp/b11573/tools/server/server-common.cpp',
            'https://raw.githubusercontent.com/ggml-org/llama.cpp/b11573/tools/server/server-context.cpp'],
        'bindings': {'sealed_analysis_sha256': ANALYSIS_SHA, 'sealed_reproduction_sha256': REPRODUCTION_SHA,
            'archival_source_sha256': ARCHIVAL_SOURCE_SHA, 'raw_bindings': verified['bindings'],
            'source_sha256': archive.sha(__file__), 'test_sha256': archive.sha('tests/test_english_sfh_native_cost_v1.py'),
            'private_rows_canonical_sha256': independent.value_hash(rows),
            'recorded_execution_source_head': verified['recorded_source_head']},
        'cumulative_generations': verified['cumulative_generations'],
        'cumulative_inference_seconds': verified['cumulative_inference_seconds'],
        'independent_arithmetic': 'Distinct native-field and HTTP-field metric recipes; unchanged primary/independent factorial functions. A separate variable-context recipe handles context deletion. Shared raw measurements, hash-chain reader, helper imports and orchestration: not independent experimental or semantic validation.',
        'limits': 'Input size and information content change together. Order/restart/system load are not randomized independently. Five speakers share meeting/topic dependencies. Leave-one-out ranges are not confidence intervals. Shorter/faster outputs are not fidelity or reliability. No CPU process-time, energy, causal per-condition peak-memory, quality-preservation or algorithmic-novelty claim. Public clone reproduction remains PARTIAL without licensed private evidence.'})
    return result, {'rows': rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--write', action='store_true')
    modes.add_argument('--verify', action='store_true')
    args = parser.parse_args(argv)
    report, private = analyze()
    if args.write:
        require(not PUBLIC.exists() and not PRIVATE.exists(), 'Supplement already exists; no overwrite')
        archive.original.write(PRIVATE, private)
        report['private_file_sha256'] = archive.sha(PRIVATE)
        report['created_utc'] = datetime.now(timezone.utc).isoformat()
        archive.original.write(PUBLIC, report)
    else:
        existing = json.loads(PUBLIC.read_text(encoding='utf-8'))
        actual_private = archive.checked_json(PRIVATE, existing['private_file_sha256'])
        compare(private, actual_private, 'Existing private native-cost rows')
        compare(report, {k: v for k, v in existing.items() if k not in ('created_utc', 'private_file_sha256')},
                'Existing native-cost supplement')
    print(json.dumps({'status': 'PASS', 'mode': 'WRITE_ONCE' if args.write else 'READ_ONLY_VERIFY',
                      'responses': report['responses'], 'new_generations': 0,
                      'public_sha256': archive.sha(PUBLIC)}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
