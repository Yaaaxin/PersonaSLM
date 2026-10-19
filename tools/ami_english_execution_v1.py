"""AMI-only reuse of the frozen English prompt, tokenizer and execution loop.

No work occurs on import. New source-qualified material, protocol and GO hashes
are required before native tokenization. Scoped module patches are single-process
only: do not call this adapter concurrently with another controller in a thread.
"""
import argparse
from contextlib import contextmanager, ExitStack
import json
import math
import os
from pathlib import Path
from unittest.mock import patch

import english_sfh_execution_v1 as original
import english_sfh_registration_v1 as registration

STUDY = 'personaslm_ami_english_sfh_v1'
OUT = Path('docs/validation/p1/english_real_speaker_stage_v2/ami')
PRIVATE = Path('.local/experiments/english_sfh_v2/ami')
MANIFEST = PRIVATE / 'development/frozen_manifest_v1.json'
BASELINE = Path('docs/validation/p1/english_real_speaker_stage_v1/development_resume_v1_execution_receipt_v1.json')
BASELINE_SHA = 'c4be870b1b0f6bb8635aa606c4a8d1d065cb289725a759731b08ba6326367dd9'
BASE_GENERATIONS, BASE_SECONDS = 788, 4485.684495999997
RESERVE = 160
DECISION = OUT.parent / 'ami_conditional_study_decision_v1.json'
POLICIES = (OUT.parent / 'ami_source_qualification_policy_v1.json',
            OUT.parent / 'metadata_qualification_policy_v1.json', DECISION)
ARCHIVE = Path('.local/datasets/ami_english_v1/ami_public_manual_1.6.2.zip')
ARCHIVE_SHA = 'b56e5babb2496b8795deeeda7e71178d7fbc9963f94276cf2a3f4b56ebbc9f9d'
RAM_GATES = [2 * 1024**3, 1024**3, 512 * 1024**2]
_VALIDATE, _WRITE, _BUILD = original.validate, original.write, registration.build_requests
require = original.require


def source_hashes():
    paths = original.shared.runtime_python_dependency_paths([Path(__file__)])
    return {p.as_posix(): original.sha(p) for p in sorted(set(paths) | {
        Path('tests/test_ami_english_execution_v1.py')})}


def relative(path, parent):
    return original.local(path, parent).relative_to(Path.cwd().resolve()).as_posix()


def inputs(bindings):
    for name, parent in (('material', PRIVATE), ('protocol', OUT), ('qualification', OUT)):
        item = bindings[name]
        require(relative(item['path'], parent) == item['path'] and
                original.sha(Path(item['path'])) == item['sha256'], 'AMI prospective input path/hash mismatch')
    material, protocol, qualification = (original.load(bindings[name]['path'])
                                         for name in ('material', 'protocol', 'qualification'))
    require(all(value.get('study_id') == STUDY and value.get('corpus') == 'AMI'
                for value in (material, protocol, qualification)), 'Distinct AMI study identity required')
    require(protocol.get('batch') == 'development', 'Only the new AMI developmental batch is authorized here')
    count = protocol.get('speaker_count')
    require(type(count) is int and count == 4, 'AMI requires exactly4 source-qualified speakers')
    require(protocol.get('reserve_generations') == RESERVE and
            BASE_GENERATIONS + count * 20 + RESERVE <= 1200, 'Independent reserve/cumulative ceiling')
    require(protocol.get('model') == original.MODEL and protocol.get('runtime') == original.RUNTIME and
            protocol.get('ram_gates_bytes') == RAM_GATES ==
            [original.MIN_RAM, original.READY_RAM, original.LIVE_RAM], 'Frozen model/runtime/RAM gates changed')
    require(protocol.get('prior_receipt') == {'path': BASELINE.as_posix(), 'sha256': BASELINE_SHA} and
            original.sha(BASELINE) == BASELINE_SHA, 'Latest cumulative budget binding required')
    prior = original.load(BASELINE)
    require(prior['cumulative_generations'] == BASE_GENERATIONS and
            prior['cumulative_inference_seconds'] == BASE_SECONDS, 'No budget reset')
    decision = original.load(DECISION)
    design = decision['finite_design']
    require(decision['schema'] == 'ami_conditional_experiment_decision_v1' and
            decision['status'] == 'CONDITIONAL_NOT_EXECUTION_GO' and
            decision['source_policy_sha256'] == original.sha(POLICIES[0]) and
            design['speakers'] == 4 and design['contexts_per_speaker'] == 2 and
            design['total_generation_attempts'] == 80 and
            design['preserved_validation_generation_reserve'] == RESERVE and
            design['remaining_after_complete_batch'] == 1200 - BASE_GENERATIONS - 80 and
            design['baseline'] == {'generations': BASE_GENERATIONS, 'inference_seconds': BASE_SECONDS} and
            design['ram_gates_bytes'] == RAM_GATES and
            design['maximum_inference_seconds'] == 3600 and design['maximum_wall_seconds'] == 5400,
            'Exact conditional AMI80 design/baseline required')
    allocation = protocol['allocation']
    require(all(type(allocation.get(k)) in (int, float) and math.isfinite(allocation[k]) and
                0 < allocation[k] <= design[k]
                for k in ('maximum_inference_seconds', 'maximum_wall_seconds')) and
            BASE_SECONDS + allocation['maximum_inference_seconds'] <= 72000, 'Conditional finite time allocation')
    require(qualification.get('decision') == 'GO_DEVELOPMENT' and
            qualification.get('material_sha256') == bindings['material']['sha256'] and
            qualification.get('protocol_sha256') == bindings['protocol']['sha256'] and
            qualification.get('privacy_audit_complete') is True and
            qualification.get('source_qualification_complete') is True and
            qualification.get('human_semantic_labels_available') is False,
            'New AMI source qualification/scientific GO required, not historical human ratings')
    require(protocol.get('source_hashes') == source_hashes(), 'AMI executable source closure changed')
    expected_inputs = {BASELINE.as_posix(): BASELINE_SHA, ARCHIVE.as_posix(): ARCHIVE_SHA}
    expected_inputs.update({p.as_posix(): original.sha(p) for p in POLICIES})
    require(all(protocol['input_hashes'].get(p) == digest for p, digest in expected_inputs.items()),
            'AMI policies/archive/budget must be prospectively bound')
    for path, digest in protocol['input_hashes'].items():
        require(original.sha(original.local(path)) == digest, 'AMI source input changed: ' + path)
    speakers = {case['speaker'] for case in material['cases']}
    require(len(speakers) == count and len(material['cases']) == 2 * count and
            all(sum(c['speaker'] == s for c in material['cases']) == 2 for s in speakers),
            'Exactly two actual contexts per qualified AMI speaker required')
    for case in material['cases']:
        registration.validate_case(case)
    return material, protocol


def build_requests(material, batch, template, tokenizer, pooled_development_style=None):
    def distinct_id(request_id):
        require(request_id.startswith('ENSFH_development_'), 'Unexpected inherited request identity')
        return 'AMI_' + request_id
    rows, pooled = _BUILD(material, batch, template,
                         lambda prompt, request_id: tokenizer(prompt, distinct_id(request_id)),
                         pooled_development_style)
    for row in rows:
        row['request_id'] = distinct_id(row['request_id'])
        row['request_sha256'] = original.shared.value_sha256({k: v for k, v in row.items()
                                                             if k != 'request_sha256'})
    return rows, pooled


def check_plan(plan, material, protocol, bindings):
    require(plan.get('study_id') == STUDY and plan.get('corpus') == 'AMI' and
            plan.get('ami_registration') == bindings and plan['cases'] == material['cases'],
            'AMI manifest identity/material binding')
    require(plan['allocation'] == protocol['allocation'] and plan['prior_receipt'] == protocol['prior_receipt'],
            'Prospective AMI allocation changed')
    require(all(plan['source_hashes'].get(path) == digest for path, digest in source_hashes().items()),
            'AMI adapter/helper closure missing from manifest')
    for item in bindings.values():
        require(plan['input_hashes'].get(item['path']) == item['sha256'], 'AMI registration input missing')
    template = original.local(plan['template_path'], PRIVATE).read_text(encoding='utf-8')
    token_ids = {row['request_id']: row['input_token_ids'] for row in plan['requests']}
    rebuilt, pooled = build_requests(material, 'development', template, lambda _, name: token_ids[name])
    require(plan['requests'] == rebuilt and plan['pooled_development_style'] == pooled,
            'AMI requests must exactly reconstruct from qualified material')


@contextmanager
def scoped(protocol, bindings, material):
    def checked_validate(path, digest):
        require(original.local(path) == original.local(MANIFEST), 'Exact new AMI manifest required')
        plan, generations, seconds = _VALIDATE(path, digest)
        check_plan(plan, material, protocol, bindings)
        return plan, generations, seconds

    def write(path, value):
        value = dict(value, study_id=STUDY, corpus='AMI')
        if Path(path) == MANIFEST:
            value['ami_registration'] = bindings
            value['source_hashes'] = {**value['source_hashes'], **source_hashes()}
        elif Path(path) == OUT / 'development_registration_v1.json':
            value['source_hashes'] = {**value['source_hashes'], **source_hashes()}
        return _WRITE(path, value)

    with ExitStack() as stack:
        for name, value in {'OUT': OUT, 'PRIVATE': PRIVATE, 'BASELINE': BASELINE,
                'BASELINE_SHA': BASELINE_SHA, 'BASE_GENERATIONS': BASE_GENERATIONS, 'BASE_SECONDS': BASE_SECONDS,
                'SIZES': {'development': (4, 80),
                          'validation': (8, RESERVE)}, 'validate': checked_validate, 'write': write}.items():
            stack.enter_context(patch.object(original, name, value))
        stack.enter_context(patch.object(registration, 'build_requests', build_requests))
        yield


def register(material_path, material_sha, protocol_path, protocol_sha, qualification_path, qualification_sha):
    bindings = {name: {'path': relative(path, parent), 'sha256': digest} for name, path, digest, parent in (
        ('material', material_path, material_sha, PRIVATE), ('protocol', protocol_path, protocol_sha, OUT),
        ('qualification', qualification_path, qualification_sha, OUT))}
    material, protocol = inputs(bindings)
    with scoped(protocol, bindings, material):
        result = registration.register(*(value for name in ('material', 'protocol', 'qualification')
                                         for value in (bindings[name]['path'], bindings[name]['sha256'])))
    return dict(result, study_id=STUDY, corpus='AMI')


def execute(action, manifest_sha, preflight_path=None):
    require(action in ('validate', 'preflight', 'run'), 'Unsupported AMI action')
    require(original.sha(MANIFEST) == manifest_sha, 'Externally supplied AMI manifest hash mismatch')
    plan = original.load(MANIFEST)
    require(plan.get('study_id') == STUDY, 'Not the new AMI study')
    bindings = plan['ami_registration']
    material, protocol = inputs(bindings)
    with scoped(protocol, bindings, material):
        if action == 'validate':
            checked, generations, seconds = original.validate(MANIFEST, manifest_sha)
            return {'status': 'VALIDATED_NOT_EXECUTED', 'study_id': STUDY, 'requests': len(checked['requests']),
                    'baseline_generations': generations, 'baseline_inference_seconds': seconds}
        if action == 'preflight':
            return dict(original.preflight(MANIFEST, manifest_sha), study_id=STUDY, corpus='AMI')
        require(preflight_path is not None, 'Fresh passing AMI preflight required')
        return dict(original.run(MANIFEST, manifest_sha, preflight_path), study_id=STUDY, corpus='AMI')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('register', 'validate', 'preflight', 'run'))
    parser.add_argument('--material', type=Path)
    parser.add_argument('--material-sha256')
    parser.add_argument('--protocol', type=Path)
    parser.add_argument('--protocol-sha256')
    parser.add_argument('--qualification', type=Path)
    parser.add_argument('--qualification-sha256')
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--preflight', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'register':
        require(all(getattr(args, name) is not None for name in ('material', 'material_sha256', 'protocol',
                'protocol_sha256', 'qualification', 'qualification_sha256')), 'Explicit prospective inputs required')
        result = register(args.material, args.material_sha256, args.protocol, args.protocol_sha256,
                          args.qualification, args.qualification_sha256)
    elif args.action == 'preflight':
        require(args.output is not None and args.manifest_sha256 is not None, 'Exclusive preflight path/hash required')
        original.local(args.output, OUT)
        try:
            result = execute('preflight', args.manifest_sha256)
        except Exception as exc:
            observation = original.shared.s.memory_observation(os.getpid())
            available = observation.get('system', {}).get('available_physical')
            result = {'status': 'FAIL', 'study_id': STUDY, 'checked_utc': original.shared.b.utc_now(),
                      'error': str(exc), 'memory': observation, 'required_available_bytes': RAM_GATES[0],
                      'ram_deficit_bytes': max(0, RAM_GATES[0] - available) if type(available) is int else None,
                      'new_generations': 0, 'retry_without_material_change': False}
        _WRITE(args.output, result)
    else:
        require(args.manifest_sha256 is not None, 'Explicit frozen AMI manifest hash required')
        result = execute(args.action, args.manifest_sha256, args.preflight)
    print(json.dumps(result, indent=2))
