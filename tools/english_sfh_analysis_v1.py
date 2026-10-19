"""Raw-to-technical-results analysis. No automatic semantic or fidelity labels."""
import argparse
import base64
from collections import defaultdict
import json
import math
from pathlib import Path
import re
import statistics

import english_sfh_execution_v1 as run

METRICS = ('output_tokens', 'latency_seconds', 'native_eos', 'native_limit',
           'output_words', 'source_fivegram_coverage')
FACTORS = run.shared.FACTORS


def words(text):
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text.casefold())


def fivegrams(text):
    tokens = words(text)
    return [tuple(tokens[i:i + 5]) for i in range(len(tokens) - 4)]


def measure(row, response, latency):
    text = response['content']
    # Source reuse is a descriptive surface diagnostic, never semantic fidelity.
    source = set(fivegrams(row['messages'][-1]['content']))
    generated = fivegrams(text)
    return {'output_tokens': response['tokens_predicted'],
            'latency_seconds': latency,
            'native_eos': int(response.get('stop_type') == 'eos'),
            'native_limit': int(response.get('stop_type') == 'limit'),
            'output_words': len(words(text)),
            'source_fivegram_coverage': (sum(g in source for g in generated) / len(generated)
                                          if generated else None)}


def describe(values):
    values = [v for v in values if v is not None]
    if not values:
        return {'n': 0, 'mean': None, 'median': None, 'range': None}
    return {'n': len(values), 'mean': statistics.fmean(values),
            'median': statistics.median(values), 'range': [min(values), max(values)]}


def influence(values):
    points = list(values.values())
    loo = [statistics.fmean(points[:i] + points[i + 1:]) for i in range(len(points))] if len(points) > 1 else []
    return {**describe(points), 'leave_one_speaker_out_mean_range':
            [min(loo), max(loo)] if loo else None}


def estimates(rows):
    cases = defaultdict(dict)
    speakers = defaultdict(list)
    for row in rows:
        key = row['speaker_id'], row['case_id']
        run.require(row['condition'] not in cases[key], 'Duplicate analysis cell')
        cases[key][row['condition']] = row
    for speaker, case in cases:
        speakers[speaker].append((speaker, case))
    conditions, effects, controls = {}, {}, {}
    for metric in METRICS:
        conditions[metric] = {}
        for condition in list(run.shared.CONDITIONS) + sorted(run.DIAGNOSTICS):
            group = [r['measurements'][metric] for r in rows if r['condition'] == condition]
            conditions[metric][condition] = {**describe(group), 'allocated': len(group),
                                           'missing_or_inapplicable': sum(v is None for v in group)}
        effects[metric], controls[metric] = {}, {}
        for name, factors in FACTORS.items():
            per_speaker = {}
            for speaker, keys in speakers.items():
                per_case = []
                for key in keys:
                    values = {c: cases[key][c]['measurements'][metric] for c in run.shared.CONDITIONS}
                    if all(v is not None for v in values.values()):
                        per_case.append(run.shared._factor_effect(values, factors))
                if len(per_case) == len(keys):
                    per_speaker[speaker] = statistics.fmean(per_case)
            effects[metric][name] = {**influence(per_speaker),
                'incomplete_speakers': len(speakers) - len(per_speaker)}
        for label, high, low in [('correct_minus_mismatched', 'C7', 'M_STYLE'),
                                 ('correct_minus_pooled', 'C7', 'N_STYLE'),
                                 ('correct_minus_no_style_at_FH', 'C7', 'C6')]:
            values = {}
            for speaker, keys in speakers.items():
                pairs = [(cases[k][high]['measurements'][metric], cases[k][low]['measurements'][metric]) for k in keys]
                if all(a is not None and b is not None for a, b in pairs):
                    values[speaker] = statistics.fmean(a - b for a, b in pairs)
            controls[metric][label] = {**influence(values), 'incomplete_speakers': len(speakers) - len(values)}
    return {'condition_summary': conditions, 'factorial_effects': effects, 'style_controls': controls}


def analyze(batch, write=False):
    receipt_path = run.OUT / (batch + '_execution_receipt_v1.json')
    receipt = run.load(receipt_path)
    folder = run.local(receipt['run_directory'], run.PRIVATE)
    events = run.shared.b.read_events(folder)
    run.require(events[-1]['kind'] == 'run_finished' and events[-1]['event_hash'] == receipt['terminal_event_sha256'], 'Sealed journal')
    plan = run.load(folder / 'manifest.json')['frozen_manifest']
    starts = [e['data'] for e in events if e['kind'] == 'english_sfh_started']
    raw = [e['data'] for e in events if e['kind'] == 'english_sfh_raw']
    failed = [e['data'] for e in events if e['kind'] == 'english_sfh_failed']
    http = [json.loads(base64.b64decode(e['data']['body_base64'])) for e in events
            if e['kind'] == 'http_response' and e['data'].get('route') == '/completion' and e['data'].get('status') == 200]
    run.require(http == [r['response'] for r in raw], 'Raw HTTP/completion equivalence')
    run.require(starts == plan['requests'][:len(starts)] and len(starts) == receipt['attempts'] and
                len(raw) == receipt['responses'], 'Attempt and response accounting')
    run.require(len({r['request_id'] for r in raw}) == len(raw), 'Duplicate raw response')
    elapsed = math.fsum(r['latency_seconds'] for r in raw + failed)
    run.require(math.isclose(elapsed, receipt['completion_inference_seconds'], abs_tol=1e-8), 'Inference accounting')
    by_id = {r['request_id']: r for r in raw}
    rows = []
    for row in plan['requests']:
        observed = by_id.get(row['request_id'])
        if observed:
            run.shared.b.validate_completion(observed['response'], row['input_token_ids'])
        rows.append({k: row[k] for k in ('request_id', 'speaker_id', 'case_id', 'condition', 'phase')} |
                    {'measurements': measure(row, observed['response'], observed['latency_seconds'])
                     if observed else dict.fromkeys(METRICS)})
    public = {'schema': 'english_sfh_technical_analysis_v1', 'batch': batch,
              'level': 'DEVELOPMENT_EXPLORATORY' if batch == 'development' else 'DISJOINT_COHORT_TECHNICAL_REPLICATION',
              'execution': receipt, 'estimates': estimates(rows),
              'definitions': {'factorial': '2*mean(product of selected +/-1 factor codes * outcome), first within context, then equal-weight contexts within speaker, then equal-weight speakers. Interactions use this same factorial scale, not the unscaled difference-in-differences.',
                              'latency': 'Wall elapsed per CPU-backend completion call, not CPU process time.',
                              'copying': 'Fraction of generated consecutive five-word windows present verbatim, case-insensitive, in full user message. Shorter-than-five-word responses are inapplicable, not zero.',
                              'memory': 'Execution receipt reports server lifetime peak working set; not a randomized per-condition RAM effect.'},
              'uncertainty': 'Speaker ranges and leave-one-speaker-out influence are descriptive, not confidence intervals. Shared meetings/group/topic induce dependence; no calibrated confirmatory test or population-level independence claim.',
              'semantic_endpoints': 'PENDING_GENUINE_HUMAN_REVIEW_NOT_AUTOMATICALLY_SCORED',
              'human_labels_created': 0, 'source_sha256': run.sha(__file__),
              'private_analysis_sha256': run.shared.value_sha256(rows),
              'public_clone_reproducibility': 'PARTIAL: private licensed source material, prompts and raw journals required for full analysis; weight acquisition separately documented.'}
    if write:
        run.write(run.PRIVATE / (batch + '_analysis_private_v1.json'), {'rows': rows})
        run.write(run.OUT / (batch + '_analysis_v1.json'), public)
    return public


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', choices=('development', 'validation'), required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps(analyze(args.batch, args.write), indent=2))
