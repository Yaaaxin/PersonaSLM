"""One exact eight-request suffix after the sealed development RAM stop.

The original execution code, manifest, requests and partial receipt are immutable.
Only its validator is scoped to this separately authorized suffix. Extra deadline
guards tighten the original wall bound; no RAM or model setting is replaced.
"""
import argparse
import copy
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
from unittest.mock import patch

import english_sfh_execution_v1 as original
import english_sfh_reproduce_v1 as independent

BATCH = 'development_resume_v1'
MANIFEST = original.PRIVATE / BATCH / 'frozen_manifest_v1.json'
PARENT_MANIFEST = original.PRIVATE / 'development/frozen_manifest_v1.json'
PARENT_SHA = '35534588ed8f386c5831ba6db9d67a05b852721cfc56b91835d3053042c32495'
PARENT_RECEIPT = original.OUT / 'development_execution_receipt_v1.json'
RECEIPT_SHA = '0269db1739d634955484d6587ac4e9f2cd35e45506480b70c94f835321511be8'
TERMINAL_SHA = '98b08ad36fd10bdd7740b9594fc92cd527e473ee712b3bb372369862b2ad150a'
START, COUNT = 92, 8
ORIGINAL_VALIDATE = original.validate
require = original.require


def source_hashes():
    paths = [Path(__file__), Path('tools/english_sfh_combined_v1.py')]
    closure = original.shared.runtime_python_dependency_paths(paths)
    return {path.as_posix(): original.sha(path) for path in set(closure) | {
        Path('tests/test_english_sfh_resume_v1.py'), Path('tests/test_english_sfh_combined_v1.py')}}


def audit_parent():
    require(original.sha(PARENT_MANIFEST) == PARENT_SHA and original.sha(PARENT_RECEIPT) == RECEIPT_SHA,
            'Original frozen manifest/partial receipt changed')
    plan, _, _ = ORIGINAL_VALIDATE(PARENT_MANIFEST, PARENT_SHA)
    checked, receipt, rows, _, failures = independent.audit_run('development')
    require(checked == plan and len(plan['requests']) == START + COUNT, 'Parent allocation changed')
    require(receipt['status'] == 'PARTIAL' and receipt['attempts'] == receipt['responses'] == START and
            receipt['failed_seconds'] == 0 and failures == 0 and receipt['unattempted'] == COUNT and
            receipt['retries'] == 0 and receipt['terminal_event_sha256'] == TERMINAL_SHA,
            'Only the exact sealed 92-response zero-failed prefix may resume')
    events = independent.read_events(Path(receipt['run_directory']))
    stops = [event['data'] for event in events if event['kind'] == 'failure']
    require(len(stops) == 1 and stops[0] == {'type': 'ValueError',
            'message': 'Available physical RAM below frozen gate', 'request_id': None},
            'Parent did not stop between requests at the RAM gate')
    journal_manifest = independent.load(Path(receipt['run_directory']) / 'manifest.json')
    return plan, receipt, rows, journal_manifest['created_utc']


def derive(parent, receipt, created_utc, authorization_path, authorization_sha, authorization):
    require(authorization.get('decision') == 'AUTHORIZED_UNATTEMPTED_SUFFIX_ONLY' and
            authorization.get('parent_manifest_sha256') == PARENT_SHA and
            authorization.get('parent_receipt_sha256') == RECEIPT_SHA and
            authorization.get('parent_terminal_sha256') == TERMINAL_SHA and
            authorization.get('start_index') == START and authorization.get('maximum_attempts') == COUNT and
            authorization.get('ram_gates_bytes') == [original.MIN_RAM, original.READY_RAM, original.LIVE_RAM],
            'Exact prospective suffix authorization required')
    extra_sources = source_hashes()
    require(authorization.get('source_hashes') == extra_sources, 'Resume source closure changed')
    require(all(parent['source_hashes'].get(name, digest) == digest for name, digest in extra_sources.items()),
            'Historical source changed')
    require(receipt['cumulative_generations'] == 780 and receipt['cumulative_inference_seconds'] == 4449.800786499977,
            'No budget reset')
    allocation = {key: parent['allocation'][key] - receipt[used]
                  for key, used in [('maximum_inference_seconds', 'completion_inference_seconds'),
                                    ('maximum_wall_seconds', 'wall_seconds')]}
    require(all(math.isfinite(value) and value > 0 for value in allocation.values()), 'No original time remains')
    start = datetime.fromisoformat(created_utc)
    require(start.tzinfo is not None, 'Original wall-clock start requires its recorded timezone')
    deadline = (start + timedelta(seconds=parent['allocation']['maximum_wall_seconds'])).isoformat()
    plan = copy.deepcopy(parent)
    plan.update(batch=BATCH, requests=copy.deepcopy(parent['requests'][START:]), allocation=allocation,
                authorization={'decision': 'AUTHORIZED', 'maximum_attempts': COUNT},
                prior_receipt={'path': PARENT_RECEIPT.as_posix(), 'sha256': RECEIPT_SHA},
                resume={'parent_manifest_sha256': PARENT_SHA, 'parent_terminal_sha256': TERMINAL_SHA,
                        'authorization_path': Path(authorization_path).as_posix(), 'authorization_sha256': authorization_sha,
                        'start_index': START, 'original_wall_deadline': deadline,
                        'requests_sha256': original.shared.value_sha256(parent['requests'][START:]),
                        'wall_policy': 'Original absolute wall deadline includes the interruption; no reset.'})
    plan['source_hashes'].update(extra_sources)
    plan['input_hashes'].update({Path(authorization_path).as_posix(): authorization_sha,
                                PARENT_MANIFEST.as_posix(): PARENT_SHA, PARENT_RECEIPT.as_posix(): RECEIPT_SHA})
    require(receipt['cumulative_generations'] + COUNT + 160 <= 1200 and
            receipt['cumulative_inference_seconds'] + allocation['maximum_inference_seconds'] <= 72000,
            'Cumulative ceiling/validation reserve')
    return plan


def prepared(authorization_path, authorization_sha):
    path = original.local(authorization_path, original.OUT)
    require(original.sha(path) == authorization_sha, 'Authorization hash changed')
    authorization = original.load(path)
    parent, receipt, _, created = audit_parent()
    plan = derive(parent, receipt, created, Path(path).relative_to(Path.cwd()).as_posix(),
                  authorization_sha, authorization)
    return plan, receipt


def register(authorization_path, authorization_sha):
    plan, receipt = prepared(authorization_path, authorization_sha)
    original.unused(BATCH)
    require(not MANIFEST.exists(), 'Resume already registered; no overwrite')
    remaining_wall(plan)
    original.write(MANIFEST, plan)
    result = {'schema': 'english_sfh_unattempted_suffix_registration_v1', 'status': 'REGISTERED_NOT_EXECUTED',
              'batch': BATCH, 'manifest_sha256': original.sha(MANIFEST), 'original_manifest_sha256': PARENT_SHA,
              'original_partial_receipt_sha256': RECEIPT_SHA, 'parent_terminal_sha256': TERMINAL_SHA,
              'maximum_attempts': COUNT, 'start_index': START, 'new_generations': 0,
              'baseline_generations': receipt['cumulative_generations'],
              'baseline_inference_seconds': receipt['cumulative_inference_seconds'],
              'remaining_allocation': plan['allocation'], 'resume': plan['resume'], 'source_hashes': source_hashes()}
    original.write(original.OUT / (BATCH + '_registration_v1.json'), result)
    return result


def validate(manifest_path, expected_sha):
    require(original.local(manifest_path) == original.local(MANIFEST) and original.sha(MANIFEST) == expected_sha,
            'Exact continuation manifest required')
    plan = original.load(MANIFEST)
    auth = plan['resume']
    expected, receipt = prepared(auth['authorization_path'], auth['authorization_sha256'])
    require(plan == expected, 'Suffix manifest differs from the audited exact original requests')
    return plan, receipt['cumulative_generations'], receipt['cumulative_inference_seconds']


def remaining_wall(plan):
    remaining = (datetime.fromisoformat(plan['resume']['original_wall_deadline']) - datetime.now(timezone.utc)).total_seconds()
    require(remaining > 0, 'Original wall deadline expired; no automatic time reset')
    return remaining


@contextmanager
def scoped_execution(plan):
    original_memory, original_client = original.memory, original.shared.b.LlamaClient

    def bounded_memory(minimum, pid):
        remaining_wall(plan)
        return original_memory(minimum, pid)

    class DeadlineClient(original_client):
        def request(self, route, payload=None):
            self.timeout = min(self.timeout, remaining_wall(plan))
            return super().request(route, payload)

    with patch.object(original, 'validate', validate), patch.object(original, 'memory', bounded_memory), \
            patch.object(original.shared.b, 'LlamaClient', DeadlineClient):
        yield


def execute(action, manifest_sha, preflight_path=None):
    plan, _, _ = validate(MANIFEST, manifest_sha)
    remaining_wall(plan)
    with scoped_execution(plan):
        if action == 'preflight':
            return original.preflight(MANIFEST, manifest_sha)
        require(action == 'run' and preflight_path is not None, 'Fresh passing preflight required')
        return original.run(MANIFEST, manifest_sha, preflight_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('register', 'validate', 'preflight', 'run'))
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--authorization-sha256')
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--preflight', type=Path)
    args = parser.parse_args()
    if args.action == 'register':
        require(args.authorization is not None and args.authorization_sha256 is not None, 'Authorization path/hash required')
        result = register(args.authorization, args.authorization_sha256)
    elif args.action == 'validate':
        plan, generations, seconds = validate(MANIFEST, args.manifest_sha256)
        result = {'status': 'VALIDATED_NOT_EXECUTED', 'requests': len(plan['requests']),
                  'baseline_generations': generations, 'baseline_inference_seconds': seconds,
                  'remaining_wall_seconds': remaining_wall(plan)}
    elif args.action == 'preflight':
        require(args.output is not None, 'Exclusive preflight receipt required')
        original.local(args.output, original.OUT)
        try:
            result = execute('preflight', args.manifest_sha256)
        except Exception as exc:
            observation = original.shared.s.memory_observation(os.getpid())
            available = observation.get('system', {}).get('available_physical')
            result = {'status': 'FAIL', 'checked_utc': original.shared.b.utc_now(), 'error': str(exc),
                      'memory': observation, 'required_available_bytes': original.MIN_RAM,
                      'ram_deficit_bytes': max(0, original.MIN_RAM - available) if type(available) is int else None,
                      'new_generations': 0, 'retry_without_material_change': False}
        original.write(args.output, result)
    else:
        result = execute('run', args.manifest_sha256, args.preflight)
    print(json.dumps(result, indent=2))
