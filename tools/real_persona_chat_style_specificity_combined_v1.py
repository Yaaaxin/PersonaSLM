"""Additive analysis of the original 54-attempt journal and its unused suffix.

No inference, retries, source edits or historical artifact replacement. Each real
journal is checked before an explicit in-memory concatenation for frozen scoring;
that concatenation is not represented as a new hash chain. Independent arithmetic
is supplied by the separate reproduction implementation, not the scorer.
"""
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from unittest.mock import patch

from personaslm.journal import atomic_json, read_events
import real_persona_chat_style_specificity_v1 as study
import real_persona_chat_style_specificity_reproduce_v1 as independent


OUT, PRIVATE = study.OUT, study.PRIVATE
SUFFIX = PRIVATE / 'suffix_v1'
NEW_PUBLIC = OUT / 'analysis_v1_1.json'
NEW_PRIVATE = PRIVATE / 'analysis_private_v1_1.json'
NEW_REPRODUCTION = OUT / 'independent_analysis_reproduction_v1_1.json'
load, sha, check, same = independent.load, independent.sha, independent.check, independent.same


def serialized_sha(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def run_evidence(root, requests, plan):
    directories = list((root / 'runs').iterdir())
    check(len(directories) == 1 and directories[0].is_dir(), 'Exactly one journal per session required')
    directory = directories[0]
    manifest = load(directory / 'manifest.json')
    check(manifest['frozen_manifest'] == plan, 'Session frozen manifest differs')
    events = read_events(directory)
    check(events and events[-1]['kind'] == 'run_finished', 'Unfinished journal cannot be combined')
    started = [e['data'] for e in events if e['kind'] == 'specificity_started']
    raw = [e['data'] for e in events if e['kind'] == 'specificity_raw']
    failed = [e['data'] for e in events if e['kind'] == 'specificity_failed']
    check(started == requests[:len(started)], 'Session not exact unique allocated prefix')
    check(len({r['request_id'] for r in raw + failed}) == len(raw) + len(failed) == len(started), 'Session attempt reconciliation')
    check({r['request_id'] for r in raw + failed} == {r['request_id'] for r in started}, 'Session request membership')
    sent = [e['data']['payload'] for e in events if e['kind'] == 'http_request' and e['data']['route'] == '/completion']
    expected = [{'prompt': r['input_token_ids'], 'n_predict': 96, 'temperature': 0.0,
                 'top_p': 1.0, 'seed': 42, 'cache_prompt': False, 'stop': [],
                 'ignore_eos': False, 'return_tokens': True, 'stream': False} for r in started]
    check(sent == expected, 'Session HTTP payload differs from frozen configuration')
    bodies = [json.loads(base64.b64decode(e['data']['body_base64'], validate=True)) for e in events
              if e['kind'] == 'http_response' and e['data'].get('route') == '/completion' and e['data'].get('status') == 200]
    check(bodies == [record['response'] for record in raw], 'Session HTTP/raw body mismatch')
    seconds = math.fsum(record['latency_seconds'] for record in raw + failed)
    check(all(type(record['latency_seconds']) in (float, int) and math.isfinite(record['latency_seconds']) and
              record['latency_seconds'] >= 0 for record in raw + failed), 'Invalid observed latency')
    return {'directory': directory, 'manifest': manifest, 'events': events, 'started': started,
            'raw': raw, 'failed': failed, 'seconds': seconds,
            'terminal_sha256': events[-1]['event_hash']}


def merge_events(first, second, requests):
    started = first['started'] + second['started']
    check(started == requests[:len(started)], 'Combined attempts are not exact frozen prefix')
    ids = [row['request_id'] for row in started]
    check(len(ids) == len(set(ids)), 'Cross-session duplicate attempt')
    raw = first['raw'] + second['raw']
    check(len({row['request_id'] for row in raw}) == len(raw), 'Cross-session duplicate response')
    return first['events'] + second['events']


def frozen_analysis(events, resource_receipt):
    """Narrow read adapters; capture existing scorer writes instead of touching files."""
    original_load, original_sha = study.load, study.sha
    captured = {}
    old_private = PRIVATE / 'analysis_private_v1.json'
    old_public = OUT / 'analysis_v1.json'

    def redirected_load(path):
        return resource_receipt if Path(path) == OUT / 'execution_receipt_v1.json' else original_load(path)

    def captured_write(path, value):
        check(Path(path) in (old_private, old_public), 'Unexpected frozen analysis output')
        check(Path(path) not in captured, 'Repeated analysis output')
        captured[Path(path)] = json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))

    def redirected_sha(path):
        return serialized_sha(captured[old_private]) if Path(path) == old_private else original_sha(path)

    with patch.object(study.old.b, 'read_events', return_value=events), \
            patch.object(study, 'load', side_effect=redirected_load), \
            patch.object(study, 'write', side_effect=captured_write), \
            patch.object(study, 'sha', side_effect=redirected_sha):
        study.analyze(write_files=True)
    check(set(captured) == {old_private, old_public}, 'Missing captured analysis')
    return captured[old_private], captured[old_public]


def independent_rows(plan, raw):
    records = {record['request_id']: record for record in raw}
    cases = {case['case_id']: case for case in plan['cases']}
    rows = []
    for request in plan['requests']:
        case = cases[request['case_id']]
        row = {key: request[key] for key in ('request_id', 'case_id', 'arm', 'input_tokens')}
        row.update({key: None for key in independent.METRICS})
        row.update(speaker_index=case['speaker_index'], text=None)
        check(request['input_tokens'] == len(request['input_token_ids']), 'Input token count')
        record = records.get(request['request_id'])
        if record is not None:
            response = record['response']
            check(response.get('truncated') is False and response.get('tokens_evaluated') == request['input_tokens'], 'Native token verification')
            if isinstance(response.get('prompt'), list):
                check(response['prompt'] == request['input_token_ids'], 'Native prompt mismatch')
            tokens = response.get('tokens_predicted')
            check(type(tokens) is int and 0 <= tokens <= 96, 'Output token allocation')
            text = response['content']
            eos, contradictory = independent.boundary(response)
            row.update(text=text, output_chars=len(independent.norm(text)), tokens=tokens,
                       seconds=record['latency_seconds'], native_stop_type=response.get('stop_type'),
                       observed_native_boundary=eos, contradictory_stop_flags=contradictory)
            if independent.norm(text):
                margin = independent.distances(text, case)[2]
                row.update(margin=margin, eos_margin=margin if eos else None)
        rows.append(row)
    counts = Counter()
    for case in plan['cases']:
        group = [row for row in rows if row['case_id'] == case['case_id']]
        k = min([20] + [row['output_chars'] or 0 for row in group])
        counts[str(k)] += 1
        for row in group:
            row['prefix_k'] = k
            row['prefix_margin'] = independent.distances(row['text'], case, k)[2] if k else None
    return rows, dict(counts)


def posthoc_diagnostics(plan, rows):
    human_margins = []
    for speaker in range(8):
        cases = [case for case in plan['cases'] if case['speaker_index'] == speaker]
        check(len(cases) == 2 and cases[0]['style'] == cases[1]['style'], 'Speaker source profile consistency')
        case = cases[0]
        source = [case['style'][key] for key in independent.FEATURES]
        own = independent.rates(case['reference_turns'])
        donor = independent.rates(case['donor_reference_turns'])
        human_margins.append(math.fsum(abs(a - d) - abs(a - o) for a, d, o in zip(source, donor, own)) / 7)
    equality = {'complete_nonempty_contexts': 0, 'CORRECT_MISMATCH_identical': 0,
                'CORRECT_LENGTH_identical': 0, 'all_four_identical': 0}
    for case in plan['cases']:
        group = {row['arm']: row for row in rows if row['case_id'] == case['case_id']}
        if not all(row['text'] is not None and independent.norm(row['text']) for row in group.values()):
            continue
        texts = {arm: independent.norm(row['text']) for arm, row in group.items()}
        equality['complete_nonempty_contexts'] += 1
        equality['CORRECT_MISMATCH_identical'] += texts['CORRECT'] == texts['MISMATCH']
        equality['CORRECT_LENGTH_identical'] += texts['CORRECT'] == texts['LENGTH']
        equality['all_four_identical'] += len(set(texts.values())) == 1
    return {'classification': 'POST_HOC_NOT_PREREGISTERED_MEASUREMENT_DIAGNOSTIC',
            'timing': 'Requested after the original 54-response partial result, before suffix analysis; no primary endpoint or selection rule changed.',
            'human_source1_to_source2_margin': {**independent.stats(human_margins),
                                                'positive_speakers': sum(value > 0 for value in human_margins)},
            'normalized_output_equality': equality,
            'boundary': 'Weak human-human discrimination limits interpretation of model-margin nulls. Neither this check nor normalized equality establishes semantic fidelity, human judgment or independent validation.'}


def verify_session_receipt(evidence, receipt, allocation, baseline_generations, baseline_seconds):
    expected = {'attempts': len(evidence['started']), 'responses': len(evidence['raw']),
                'unattempted': allocation - len(evidence['started']), 'retries': 0,
                'completion_inference_seconds': evidence['seconds'],
                'failed_seconds': math.fsum(row['latency_seconds'] for row in evidence['failed'])}
    same(expected, receipt, 'Session receipt accounting')
    same(expected, evidence['events'][-1]['data'], 'Session terminal accounting')
    same({**expected, 'cumulative_generations': baseline_generations + len(evidence['started']),
          'cumulative_inference_seconds': baseline_seconds + evidence['seconds'],
          'terminal_event_sha256': evidence['terminal_sha256']}, receipt, 'Cumulative session accounting')
    check(receipt['status'] == evidence['events'][-1]['data']['status'], 'Session status binding')
    same(receipt['wall_seconds'], evidence['events'][-1]['data']['wall_seconds'], 'Session wall time')


def combine(write_files=False):
    if not (OUT / 'suffix_execution_receipt_v1.json').exists():
        return {'status': 'BLOCKED_NO_TERMINAL_SUFFIX_RECEIPT', 'new_files_written': 0,
                'boundary': 'Original partial evidence preserved; no synthetic completion or new inference.'}
    check(not write_files or not any(path.exists() for path in (NEW_PRIVATE, NEW_PUBLIC, NEW_REPRODUCTION)),
          'Immutable combined artifact already exists; no replacement')
    plan = study.validate()
    design = load(OUT / 'design_v1.json')
    limits = design['resources']
    preserved_paths = (OUT / 'execution_receipt_v1.json', OUT / 'analysis_v1.json',
                       PRIVATE / 'analysis_private_v1.json', OUT / 'independent_analysis_reproduction_v1.json')
    preserved = {path.as_posix(): sha(path) for path in preserved_paths}
    first_receipt = load(OUT / 'execution_receipt_v1.json')
    second_receipt = load(OUT / 'suffix_execution_receipt_v1.json')
    first = run_evidence(PRIVATE, plan['requests'], plan)
    second = run_evidence(SUFFIX, plan['requests'][54:], plan)
    prior_reproduction = load(OUT / 'independent_analysis_reproduction_v1.json')
    check(prior_reproduction['status'] == 'PASS', 'Original independent reproduction not passing')
    same({'analysis_sha256': sha(OUT / 'analysis_v1.json'),
          'private_analysis_sha256': sha(PRIVATE / 'analysis_private_v1.json'),
          'manifest_sha256': sha(study.FROZEN), 'registration_sha256': sha(study.REGISTRATION),
          'terminal_event_sha256': first['terminal_sha256']},
         prior_reproduction['bindings'], 'Preserved partial reproduction bindings')
    check(len(first['started']) == len(first['raw']) == 54 and not first['failed'], 'Original preserved prefix must be 54 completed attempts')
    check(len(second['started']) <= 10, 'Suffix allocation exceeded')
    verify_session_receipt(first, first_receipt, 64, limits['cumulative_baseline_generations'],
                           limits['cumulative_baseline_inference_seconds'])
    verify_session_receipt(second, second_receipt, 10, first_receipt['cumulative_generations'],
                           first_receipt['cumulative_inference_seconds'])
    if not second['started']:
        return {'status': 'BLOCKED_SUFFIX_ZERO_ATTEMPTS_ORIGINAL_PARTIAL_PRESERVED', 'new_files_written': 0}
    amendment_path = OUT / 'suffix_amendment_v1.json'
    registration_path = OUT / 'suffix_registration_v1.json'
    amendment, registration = load(amendment_path), load(registration_path)
    check(registration['amendment'] == amendment == second['manifest']['authorization'], 'Suffix authorization binding')
    check(registration == second['manifest']['suffix_registration'], 'Journal suffix registration binding')
    check(registration['original_source_hashes'] == plan['source_hashes'], 'Original source dependency binding')
    same({'original_manifest_sha256': sha(study.FROZEN), 'maximum_attempts': 10,
          'request_sha256': [row['request_sha256'] for row in plan['requests'][54:]],
          'baseline_generations': first_receipt['cumulative_generations'],
          'baseline_seconds': first_receipt['cumulative_inference_seconds']}, registration, 'Suffix registration')
    same({'original_manifest_sha256': sha(study.FROZEN),
          'original_receipt_sha256': sha(OUT / 'execution_receipt_v1.json'),
          'original_terminal_event_sha256': first['terminal_sha256']}, amendment, 'Amendment original evidence')
    same({'original_receipt_sha256': sha(OUT / 'execution_receipt_v1.json'),
          'suffix_registration_sha256': sha(registration_path)}, second_receipt, 'Suffix receipt bindings')
    check(second['seconds'] <= amendment['resources']['suffix_inference_seconds_limit'] and
          second_receipt['wall_seconds'] <= amendment['resources']['suffix_wall_seconds_limit'], 'Suffix time allocation')
    for root, evidence, extra in ((PRIVATE, first, {}), (SUFFIX, second, registration['bindings'])):
        claim = load(root / 'claim_v1.json')
        check(claim == evidence['manifest']['claim'], 'Journal claim binding')
        check(claim['maximum_attempts'] == (64 if root == PRIVATE else 10), 'Claim allocation')
        if root == PRIVATE:
            check(claim['manifest_sha256'] == sha(study.FROZEN), 'Original claim manifest')
        else:
            check(claim['registration_sha256'] == sha(registration_path), 'Suffix claim registration')
        matching_preflights = [path for path in OUT.glob('*preflight*.json') if sha(path) == claim['preflight_sha256']]
        check(len(matching_preflights) == 1 and load(matching_preflights[0])['status'] == 'PASS', 'Claim passing preflight binding')
        preflights = [event['data'] for event in evidence['events'] if event['kind'] == 'preflight']
        check(len(preflights) == 1 and preflights[0]['status'] == 'PASS' and
              preflights[0]['manifest_sha256'] == sha(study.FROZEN) and
              preflights[0]['registration_sha256'] == sha(study.REGISTRATION), 'Live journal preflight binding')
        if root == SUFFIX:
            check(preflights[0]['suffix_registration_sha256'] == sha(registration_path), 'Live suffix preflight binding')
        for path, expected in {**plan['source_hashes'], **extra}.items():
            check(sha(Path(path)) == expected and sha(evidence['directory'] / 'source_snapshot' / path) == expected,
                  'Live/snapshot source binding: ' + path)
    events = merge_events(first, second, plan['requests'])
    attempts, raw = first['started'] + second['started'], first['raw'] + second['raw']
    elapsed = first['seconds'] + second['seconds']
    cumulative_generations = first_receipt['cumulative_generations'] + len(second['started'])
    cumulative_seconds = first_receipt['cumulative_inference_seconds'] + second['seconds']
    check(cumulative_generations == limits['cumulative_baseline_generations'] + len(attempts), 'Combined generation baseline')
    check(cumulative_generations <= limits['global_generation_limit'] and cumulative_seconds <= limits['global_inference_seconds_limit'], 'Cumulative ceiling')
    resources = {'status': 'COMPLETE' if len(raw) == 64 else 'PARTIAL', 'attempts': len(attempts),
                 'responses': len(raw), 'unattempted': 64 - len(attempts), 'retries': 0,
                 'completion_inference_seconds': elapsed,
                 'failed_seconds': first_receipt['failed_seconds'] + second_receipt['failed_seconds'],
                 'active_session_wall_seconds': first_receipt['wall_seconds'] + second_receipt['wall_seconds'],
                 'cumulative_generations': cumulative_generations, 'cumulative_inference_seconds': cumulative_seconds,
                 'session_count': 2, 'terminal_event_sha256': second['terminal_sha256'],
                 'terminal_event_sha256_by_session': [first['terminal_sha256'], second['terminal_sha256']],
                 'session_attempts': [len(first['started']), len(second['started'])],
                 'session_inference_seconds': [first['seconds'], second['seconds']],
                 'receipt_sha256_by_session': [sha(OUT / 'execution_receipt_v1.json'), sha(OUT / 'suffix_execution_receipt_v1.json')],
                 'latency_and_memory_limitation': 'The final suffix uses a fresh owned server after a live-RAM safety stop. Session, order, cache/process state and speaker/context allocation can confound latency and memory contrasts. No assertion of externally repaired hardware or bit-identical cross-session inference.'}
    private, public = frozen_analysis(events, resources)
    rows, prefix_counts = independent_rows(plan, raw)
    check(len(rows) == len(private['rows']) == 64, 'Combined result row count')
    for row, recorded in zip(rows, private['rows']):
        same({key: value for key, value in row.items() if key != 'text'}, recorded, 'Independent combined row')
        check(row['text'] == recorded['text'], 'Combined archived text mismatch')
    conditions, contrasts = independent.aggregate(rows, plan['cases'])
    same(conditions, public['conditions'], 'Independent combined arm means')
    same(contrasts, public['contrasts'], 'Independent paired contrasts/bounds/LOO')
    same(prefix_counts, public['prefix_k_distribution'], 'Independent equal-prefix counts')
    stops = dict(Counter(row.get('native_stop_type', 'MISSING') for row in rows))
    same(stops, public['native_stop_counts'], 'Independent native stops')
    same(sum(row.get('contradictory_stop_flags', False) for row in rows), public['contradictory_stop_records'], 'Native contradictions')
    same(resources, public['resources'], 'Combined accounting')
    bindings = {'original_claim_sha256': sha(PRIVATE / 'claim_v1.json'),
                'suffix_claim_sha256': sha(SUFFIX / 'claim_v1.json'),
                'original_journal_manifest_sha256': sha(first['directory'] / 'manifest.json'),
                'suffix_journal_manifest_sha256': sha(second['directory'] / 'manifest.json'),
                'suffix_registration_sha256': sha(registration_path),
                'suffix_amendment_sha256': sha(amendment_path),
                'terminal_event_sha256_by_session': resources['terminal_event_sha256_by_session'],
                'combined_controller_sha256': sha(Path(__file__)),
                'independent_arithmetic_sha256': sha(Path(independent.__file__)),
                'preserved_partial_artifact_hashes': preserved}
    public['bindings'].update(bindings)
    public['analysis_version'] = 'v1.1_ADD_ONLY_TWO_VERIFIED_JOURNALS'
    public['execution_deviation'] = resources['latency_and_memory_limitation']
    public['event_view'] = 'Original frozen scorer receives ordered concatenation of two separately verified real event lists. No synthetic merged hash chain is claimed; both terminal hashes are bound.'
    public['posthoc_measurement_diagnostics'] = posthoc_diagnostics(plan, rows)
    receipt = {'status': 'PASS', 'recorded_utc': datetime.now(timezone.utc).isoformat(),
               'classification': 'INDEPENDENT_ARITHMETIC_REPRODUCTION_NOT_INDEPENDENT_EXPERIMENT',
               'analysis_sha256': serialized_sha(public), 'private_analysis_sha256': serialized_sha(private),
               'bindings': bindings, 'verified_raw_responses': len(raw), 'verified_allocated_rows': 64,
               'conditions': conditions, 'contrasts': contrasts, 'prefix_k_distribution': prefix_counts,
               'native_stop_counts': stops, 'budget': {**resources,
                   'observed_output_tokens': sum(row['tokens'] or 0 for row in rows),
                   'attempted_input_tokens': sum(row['input_tokens'] for row in attempts),
                   'remaining_generations': limits['global_generation_limit'] - cumulative_generations,
                   'remaining_inference_seconds': limits['global_inference_seconds_limit'] - cumulative_seconds},
               'posthoc_measurement_diagnostics': public['posthoc_measurement_diagnostics'],
               'shared_infrastructure': ['Hash-chain reader', 'Immutable writer', 'Explicit event/receipt view adapter'],
               'independent_arithmetic': 'Seven Unicode feature rates, own/donor distances, equal prefixes, native boundaries, per-row margins, paired aggregation, missing bounds and leave-one-speaker-out ranges are recalculated by a separate scoring implementation.',
               'limits': 'No independent experiment or human semantic review. Marker/copying and memory diagnostics use the frozen original scorer and are not independently recomputed here. Post-hoc human-human check does not validate the metric. Private artifacts required: public clone-only reproduction remains PARTIAL.',
               'new_generations': 0, 'human_labels_created': 0, 'reserved_validation_content_accessed': False}
    check({path.as_posix(): sha(path) for path in preserved_paths} == preserved, 'Historical artifact changed during analysis')
    if write_files:
        atomic_json(NEW_PRIVATE, private)
        atomic_json(NEW_PUBLIC, public)
        check(sha(NEW_PRIVATE) == receipt['private_analysis_sha256'] and sha(NEW_PUBLIC) == receipt['analysis_sha256'], 'New analysis write hash')
        atomic_json(NEW_REPRODUCTION, receipt)
    return receipt


def self_test():
    independent.self_test()
    requests = [{'request_id': f'SYNTHETIC{i}'} for i in range(4)]
    first = {'started': requests[:2], 'raw': requests[:2], 'events': [{'kind': 'one'}]}
    second = {'started': requests[2:], 'raw': requests[2:], 'events': [{'kind': 'two'}]}
    check(len(merge_events(first, second, requests)) == 2, 'Exact suffix concatenation')
    bad = {**second, 'started': requests[1:3]}
    try:
        merge_events(first, bad, requests)
    except AssertionError:
        pass
    else:
        raise AssertionError('Duplicate/reordered suffix was accepted')
    return {'status': 'PASS', 'classification': 'SYNTHETIC_COMBINED_ARITHMETIC_SELF_TEST', 'new_generations': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--write', action='store_true', help='Write additive v1.1 artifacts only; refuse existing paths')
    args = parser.parse_args()
    print(json.dumps(self_test() if args.self_test else combine(args.write), indent=2, allow_nan=False))
