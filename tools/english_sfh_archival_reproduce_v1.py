"""Read-only two-journal analysis after a legitimate Git HEAD advance.

Frozen execution validators remain unchanged. This entrypoint cannot register,
preflight or generate; its scoped validator checks archival evidence only.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from unittest.mock import patch

import english_sfh_combined_v1 as combined

resume, independent, original = combined.resume, combined.independent, combined.original
PUBLIC = Path('docs/validation/p1/english_real_speaker_stage_v1')
PRIVATE = Path('.local/experiments/english_sfh_v1')
ANALYSIS = PUBLIC / 'development_combined_analysis_v1.json'
REPRODUCTION = PUBLIC / 'development_combined_independent_reproduction_v1.json'
ARCHIVAL_RECEIPT = PUBLIC / 'development_archival_reproduction_v1.json'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked_json(path, expected):
    require(sha(path) == expected, 'Externally bound artifact changed: ' + Path(path).name)
    return json.loads(Path(path).read_text(encoding='utf-8'))


def live_sources(plan):
    """Bytes and loaded local module paths, not current Git commit identity."""
    root = Path.cwd().resolve()
    for name, digest in plan['source_hashes'].items():
        path = (root / name).resolve()
        require(path.is_relative_to(root) and sha(path) == digest, 'Frozen live source changed: ' + name)
        module_name = None
        if name.startswith('tools/') and name.endswith('.py'):
            module_name = name[6:-3].replace('/', '.')
        elif name.startswith('src/') and name.endswith('.py'):
            module_name = name[4:-3].replace('/', '.').removesuffix('.__init__')
        if module_name in sys.modules:
            require(Path(sys.modules[module_name].__file__).resolve() == path,
                    'Loaded helper shadows frozen source: ' + name)
    required = {'tools/english_sfh_combined_v1.py': Path(combined.__file__),
                'tools/english_sfh_resume_v1.py': Path(resume.__file__),
                'tools/english_sfh_reproduce_v1.py': Path(independent.__file__),
                'tools/english_sfh_analysis_v1.py': Path(combined.primary.__file__),
                'tools/english_sfh_execution_v1.py': Path(original.__file__)}
    for name, path in required.items():
        require(plan['source_hashes'].get(name) == sha(path) and path.resolve() == (root / name).resolve(),
                'Historical analysis helper not frozen: ' + name)


def parent_evidence(bindings):
    require(bindings['original_manifest_sha256'] == resume.PARENT_SHA and
            bindings['original_partial_receipt_sha256'] == resume.RECEIPT_SHA and
            bindings['original_terminal_sha256'] == resume.TERMINAL_SHA, 'Original study anchors changed')
    checked_json(resume.PARENT_MANIFEST, bindings['original_manifest_sha256'])
    checked_json(resume.PARENT_RECEIPT, bindings['original_partial_receipt_sha256'])
    plan, receipt, rows, _, failures = independent.audit_run('development')
    require(receipt['status'] == 'PARTIAL' and receipt['attempts'] == receipt['responses'] == 92 and
            receipt['unattempted'] == 8 and failures == 0 and receipt['failed_seconds'] == 0 and
            receipt['terminal_event_sha256'] == bindings['original_terminal_sha256'], 'Original sealed prefix changed')
    events = independent.read_events(Path(receipt['run_directory']))
    stops = [event['data'] for event in events if event['kind'] == 'failure']
    require(stops == [{'type': 'ValueError', 'message': 'Available physical RAM below frozen gate',
                      'request_id': None}], 'Original RAM stop was not between requests')
    metadata = json.loads((Path(receipt['run_directory']) / 'manifest.json').read_text(encoding='utf-8'))
    return plan, receipt, rows, events, metadata['created_utc']


def archival_validate(path, expected_sha, *, parent, parent_receipt, created_utc, bindings):
    require(Path(path).resolve() == resume.MANIFEST.resolve() and
            expected_sha == bindings['suffix_manifest_sha256'], 'Unexpected archival suffix scope')
    plan = checked_json(path, expected_sha)
    info = plan['resume']
    auth_path = Path(info['authorization_path'])
    require(auth_path.resolve().is_relative_to(PUBLIC.resolve()), 'Suffix authorization escaped public study')
    authorization = checked_json(auth_path, info['authorization_sha256'])
    # Pure derivation checks the original suffix, authorizations, source closure,
    # unchanged generation settings, preserved deadline and cumulative ceilings.
    expected = resume.derive(parent, parent_receipt, created_utc, auth_path,
                             info['authorization_sha256'], authorization)
    require(plan == expected, 'Archival suffix differs from exact original allocation')
    return plan, parent_receipt['cumulative_generations'], parent_receipt['cumulative_inference_seconds']


def reproduce(analysis_sha256, reproduction_sha256):
    report = checked_json(ANALYSIS, analysis_sha256)
    prior = checked_json(REPRODUCTION, reproduction_sha256)
    require(report['schema'] == 'english_sfh_two_journal_analysis_v1' and prior['status'] == 'PASS' and
            prior['analysis_sha256'] == analysis_sha256 and prior['bindings'] == report['bindings'],
            'Sealed combined analysis/reproduction binding')
    bindings = report['bindings']
    suffix = checked_json(resume.MANIFEST, bindings['suffix_manifest_sha256'])
    live_sources(suffix)
    parent, parent_receipt, parent_rows, parent_events, created = parent_evidence(bindings)
    suffix_receipt_path = PUBLIC / (resume.BATCH + '_execution_receipt_v1.json')
    checked_json(suffix_receipt_path, bindings['suffix_receipt_sha256'])

    def read_only_validation(path, expected_sha):
        return archival_validate(path, expected_sha, parent=parent, parent_receipt=parent_receipt,
                                 created_utc=created, bindings=bindings)

    # Scoped only around the frozen read-only suffix auditor; no executor call.
    with patch.object(resume, 'validate', read_only_validation):
        suffix, suffix_receipt, suffix_events, suffix_rows, failures = combined.audit_suffix()
    require(suffix_receipt['terminal_event_sha256'] == bindings['suffix_terminal_sha256'], 'Suffix tail changed')
    rows, estimates, responses, attempts = combined.paired_rows(parent, parent_rows, suffix, suffix_rows,
                                                               parent_events, suffix_events)
    independent.compare(estimates, report['estimates'], 'sealed combined effects')
    private_path = PRIVATE / 'development_combined_analysis_private_v1.json'
    private = checked_json(private_path, prior['private_file_sha256'])
    independent.compare(rows, private['rows'], 'sealed combined rows')
    require(independent.value_hash(rows) == bindings['private_rows_canonical_sha256'], 'Canonical row hash changed')
    cost = math.fsum([parent_receipt['completion_inference_seconds'], suffix_receipt['completion_inference_seconds']])
    independent.compare(cost, report['completion_inference_seconds'], 'combined completion cost')
    independent.compare(independent.BASE_SECONDS + cost, report['cumulative_inference_seconds'], 'cumulative cost')
    independent.compare(suffix_receipt['cumulative_inference_seconds'], report['cumulative_inference_seconds'], 'suffix cumulative cost')
    require(report['run_receipts'] == [parent_receipt, suffix_receipt] and
            report['responses'] == prior['responses'] == responses == 100 and
            report['attempts'] == prior['attempts'] == attempts == 100 and
            report['allocated'] == 100 and report['missing_responses'] == 0 and
            report['failed_suffix_calls'] == failures == 0 and report['new_generation_retries'] == 0 and
            report['cumulative_generations'] == suffix_receipt['cumulative_generations'] ==
            prior['cumulative_generations'] == independent.BASE_GENERATIONS + attempts == 788,
            'Sealed complete-grid accounting changed')
    independent.compare(prior['cumulative_inference_seconds'], report['cumulative_inference_seconds'], 'prior reproduction cost')
    require(bindings['primary_definition_source_sha256'] == sha(combined.primary.__file__) and
            bindings['independent_definition_source_sha256'] == sha(independent.__file__) and
            bindings['combined_source_sha256'] == sha(combined.__file__), 'Analysis implementation bindings changed')
    return {'schema': 'english_sfh_archival_reproduction_v1', 'status': 'PASS',
            'analysis_sha256': analysis_sha256, 'prior_reproduction_sha256': reproduction_sha256,
            'archival_source_sha256': sha(__file__),
            'archival_test_sha256': sha('tests/test_english_sfh_archival_reproduce_v1.py'),
            'bindings': bindings, 'recorded_source_head': parent['source_head'],
            'current_head_gate': 'NOT_APPLICABLE_TO_READ_ONLY_ARCHIVAL_ANALYSIS',
            'execution_validators_modified': False, 'responses': responses, 'attempts': attempts,
            'cumulative_generations': report['cumulative_generations'],
            'cumulative_inference_seconds': report['cumulative_inference_seconds'],
            'comparison_absolute_tolerance': 1e-10, 'new_generations': 0, 'human_labels_created': 0,
            'limits': 'Independent arithmetic implementations, shared journal reader; not semantic or independent experimental validation. Source bytes and private archive paths must remain available. Public clone-only reproduction PARTIAL; no cross-environment generation repeatability claim.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--write', action='store_true')
    action.add_argument('--verify', action='store_true')
    parser.add_argument('--analysis-sha256', required=True)
    parser.add_argument('--reproduction-sha256', required=True)
    args = parser.parse_args(argv)
    result = reproduce(args.analysis_sha256, args.reproduction_sha256)
    if args.write:
        receipt = dict(result, created_utc=datetime.now(timezone.utc).isoformat())
        with ARCHIVAL_RECEIPT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write('\n')
    else:
        receipt = json.loads(ARCHIVAL_RECEIPT.read_text(encoding='utf-8'))
        independent.compare({key: value for key, value in receipt.items() if key != 'created_utc'}, result,
                            'existing archival receipt')
    print(json.dumps({'status': 'PASS', 'mode': 'WRITE_ONCE' if args.write else 'READ_ONLY_VERIFY',
                      'responses': result['responses'], 'new_generations': 0,
                      'receipt_sha256': sha(ARCHIVAL_RECEIPT)}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
