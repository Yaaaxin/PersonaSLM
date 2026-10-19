"""Explicit two-journal English development analysis; never merge raw journals."""
import argparse
import json
import math
from pathlib import Path

import english_sfh_analysis_v1 as primary
import english_sfh_reproduce_v1 as independent
import english_sfh_resume_v1 as resume

original = resume.original


def audit_suffix():
    receipt_path = original.OUT / (resume.BATCH + '_execution_receipt_v1.json')
    receipt = original.load(receipt_path)
    plan, generations, seconds = resume.validate(resume.MANIFEST, receipt['manifest_sha256'])
    folder = original.local(receipt['run_directory'], original.PRIVATE / resume.BATCH / 'runs')
    archive = original.load(folder / 'manifest.json')
    registration = original.load(original.OUT / (resume.BATCH + '_registration_v1.json'))
    original.require(archive['frozen_manifest'] == plan and
                     archive['claim'] == original.load(original.PRIVATE / resume.BATCH / 'claim_v1.json') and
                     registration['manifest_sha256'] == receipt['manifest_sha256'], 'Suffix manifest/claim binding')
    events = independent.read_events(folder)
    original.require(events[-1]['kind'] == 'run_finished' and events[-1]['event_hash'] == receipt['terminal_event_sha256'] and
                     all(receipt[key] == value for key, value in events[-1]['data'].items()), 'Suffix sealed terminal binding')
    hash_only = {event['data']['path']: event['data']['sha256'] for event in events if event['kind'] == 'hash_only_input'}
    for name, digest in plan['source_hashes'].items():
        original.require(original.sha(folder / 'source_snapshot' / independent.relative(name)) == digest,
                         'Suffix source snapshot changed')
    for name, digest in plan['input_hashes'].items():
        if name in plan['source_hashes']:
            original.require(plan['source_hashes'][name] == digest, 'Conflicting suffix input')
        elif name in hash_only:
            original.require(hash_only[name] == digest and original.sha(Path(name)) == digest, 'Suffix retained archive changed')
        else:
            original.require(original.sha(folder / 'input_snapshot' / independent.relative(name)) == digest,
                             'Suffix input snapshot changed')
    rows, cost, failures = independent.reconcile(plan, receipt, events, generations, seconds)
    original.require(math.isclose(cost, receipt['completion_inference_seconds'], rel_tol=0, abs_tol=1e-10), 'Suffix cost')
    return plan, receipt, events, rows, failures


def paired_rows(parent_plan, parent_rows, suffix_plan, suffix_rows, first_events, second_events):
    original.require(suffix_plan['requests'] == parent_plan['requests'][resume.START:] and
                     len(parent_rows) == resume.START + resume.COUNT and len(suffix_rows) == resume.COUNT,
                     'Only the exact original suffix may complete the grid')
    original.require(all(all(value is None for value in row['measurements'].values())
                         for row in parent_rows[resume.START:]), 'Suffix was previously observed')
    records, seen_starts = {}, set()
    for events in (first_events, second_events):
        for event in events:
            if event['kind'] == 'english_sfh_started':
                request_id = event['data']['request_id']
                original.require(request_id not in seen_starts, 'Repeated cross-journal attempt')
                seen_starts.add(request_id)
            elif event['kind'] == 'english_sfh_raw':
                raw = event['data']
                original.require(raw['request_id'] not in records, 'Repeated cross-journal response')
                records[raw['request_id']] = raw
    known = {row['request_id'] for row in parent_plan['requests']}
    original.require(set(records) <= known and seen_starts <= known, 'Unregistered combined outcome')
    rows = []
    for request in parent_plan['requests']:
        raw = records.get(request['request_id'])
        rows.append({key: request[key] for key in ('request_id', 'speaker_id', 'case_id', 'condition', 'phase')} |
                    {'measurements': primary.measure(request, raw['response'], raw['latency_seconds'])
                     if raw else dict.fromkeys(primary.METRICS)})
    recalculated = parent_rows[:resume.START] + suffix_rows
    independent.compare(rows, recalculated, 'separate raw-to-row calculations')
    estimated = primary.estimates(rows)
    independent.compare(estimated, independent.estimates(recalculated), 'independent complete-grid arithmetic')
    return rows, estimated, len(records), len(seen_starts)


def analyze(write=False):
    parent_plan, parent_receipt, parent_rows, _ = resume.audit_parent()
    suffix_plan, suffix_receipt, suffix_events, suffix_rows, failed = audit_suffix()
    parent_events = independent.read_events(Path(parent_receipt['run_directory']))
    rows, estimates, count, attempts = paired_rows(parent_plan, parent_rows, suffix_plan, suffix_rows,
                                                 parent_events, suffix_events)
    original.require(count == parent_receipt['responses'] + suffix_receipt['responses'] and
                     attempts == parent_receipt['attempts'] + suffix_receipt['attempts'], 'Combined accounting')
    cost = math.fsum([parent_receipt['completion_inference_seconds'], suffix_receipt['completion_inference_seconds']])
    independent.compare(independent.BASE_SECONDS + cost, suffix_receipt['cumulative_inference_seconds'], 'Combined cost')
    original.require(independent.BASE_GENERATIONS + attempts == suffix_receipt['cumulative_generations'], 'Combined attempts')
    bindings = {'original_manifest_sha256': resume.PARENT_SHA, 'suffix_manifest_sha256': original.sha(resume.MANIFEST),
                'original_partial_receipt_sha256': resume.RECEIPT_SHA,
                'suffix_receipt_sha256': original.sha(original.OUT / (resume.BATCH + '_execution_receipt_v1.json')),
                'original_terminal_sha256': parent_receipt['terminal_event_sha256'],
                'suffix_terminal_sha256': suffix_receipt['terminal_event_sha256'],
                'primary_definition_source_sha256': original.sha(Path(primary.__file__)),
                'independent_definition_source_sha256': original.sha(Path(independent.__file__)),
                'combined_source_sha256': original.sha(Path(__file__)),
                'private_rows_canonical_sha256': independent.value_hash(rows)}
    report = {'schema': 'english_sfh_two_journal_analysis_v1', 'batch': 'development_combined',
              'status': 'COMPLETE_OBSERVATIONS' if count == len(parent_plan['requests']) else 'PARTIAL_OBSERVATIONS',
              'level': 'DEVELOPMENT_EXPLORATORY', 'allocated': len(parent_plan['requests']),
              'attempts': attempts, 'responses': count, 'missing_responses': len(parent_plan['requests']) - count,
              'new_generation_retries': 0, 'failed_suffix_calls': failed,
              'completion_inference_seconds': cost, 'cumulative_generations': suffix_receipt['cumulative_generations'],
              'cumulative_inference_seconds': suffix_receipt['cumulative_inference_seconds'],
              'run_receipts': [parent_receipt, suffix_receipt], 'bindings': bindings, 'estimates': estimates,
              'human_labels_created': 0, 'semantic_endpoints': 'PENDING_GENUINE_HUMAN_REVIEW',
              'provenance': 'Two sealed journals remain separate. Original PARTIAL status is never rewritten; this record aggregates disjoint observations, not a synthetic merged execution.',
              'compatibility_deviation': 'Frozen primary analyze() passed str __file__ to a Path-only sha helper and stopped before writing. This adapter calls its unchanged pure measure/estimates definitions; no frozen implementation was edited.',
              'independent_reproduction': 'Distinct frozen raw-to-row and factorial implementations agree within absolute1e-10; shared hash-chain reader and current orchestration. No independent human or experimental validation.',
              'limits': 'Tokens, word count, native stops, full-user five-word overlap and completion wall latency are technical descriptions, not semantic Persona Fidelity. Complete-speaker estimates and leave-one-speaker-out ranges are not confidence intervals. The interrupted/restarted server may affect latency and memory; run boundary is preserved and confounded with order. Public clone-only reproduction is PARTIAL.'}
    if write:
        private_path = original.PRIVATE / 'development_combined_analysis_private_v1.json'
        public_path = original.OUT / 'development_combined_analysis_v1.json'
        reproduction_path = original.OUT / 'development_combined_independent_reproduction_v1.json'
        original.require(not any(path.exists() for path in (private_path, public_path, reproduction_path)),
                         'Combined evidence exists; no overwrite')
        original.write(private_path, {'rows': rows})
        original.write(public_path, report)
        original.write(reproduction_path, {'schema': 'english_sfh_two_journal_independent_arithmetic_v1',
            'status': 'PASS', 'scope': 'ARITHMETIC_NOT_INDEPENDENT_EXPERIMENT_OR_HUMAN_REVIEW',
            'bindings': bindings, 'analysis_sha256': original.sha(public_path),
            'private_file_sha256': original.sha(private_path), 'responses': count, 'attempts': attempts,
            'cumulative_generations': suffix_receipt['cumulative_generations'],
            'cumulative_inference_seconds': suffix_receipt['cumulative_inference_seconds'], 'human_labels_created': 0})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    print(json.dumps(analyze(args.write), indent=2, allow_nan=False))
