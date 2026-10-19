"""Bounded Base/Instruct deployment comparison; no work or model loading on import.

Reuses the frozen single-writer execution loop with scoped configuration changes.
Not thread-safe: execute only one batch/controller per process. No old evidence changes.
"""
import argparse
from contextlib import contextmanager, ExitStack
import json
import os
from pathlib import Path
import struct
import subprocess
from unittest.mock import patch
from urllib.parse import urlsplit

import english_sfh_execution_v1 as old
import english_sfh_registration_v1 as registration
import english_sfh_reproduce_v1 as independent
import english_sfh_model_artifacts_v1 as artifacts
import personaslm.configuration as configuration

OUT = Path('docs/validation/p1/english_model_comparison_v1')
PRIVATE = Path('.local/experiments/english_model_comparison_v1')
PROTOCOL = OUT / 'prospective_protocol_v1.json'
BASELINE = Path('docs/validation/p1/english_real_speaker_stage_v1/development_resume_v1_execution_receipt_v1.json')
BASELINE_SHA = 'c4be870b1b0f6bb8635aa606c4a8d1d065cb289725a759731b08ba6326367dd9'
OLD_MANIFEST = Path('.local/experiments/english_sfh_v1/development/frozen_manifest_v1.json')
OLD_MANIFEST_SHA = '35534588ed8f386c5831ba6db9d67a05b852721cfc56b91835d3053042c32495'
MATERIAL = Path('.local/experiments/english_sfh_v1/icsi_curated_material_v3.json')
MATERIAL_SHA = '9d314b40bd3eaffcc53d22abf109d00529d5fdc3b48f14485e3fddc9093ed340'
BASE_GENERATIONS, BASE_SECONDS = 788, 4485.684495999997
RAM = [3 * 1024**3, 1024**3, 512 * 1024**2]
RUNTIME = dict(old.RUNTIME, stop='case_specific_native_turn_boundaries_v1')
STUDY = 'personaslm_english_model_comparison_execution_v1'
_MESSAGES, _PAYLOAD = registration.messages, old.payload
_FILE_PREFLIGHT = old.shared.b.file_preflight
require, load, sha = old.require, old.load, old.sha
STORAGE = OUT / 'model_storage_amendment_v1.json'
PHYSICAL = {variant: Path('D:/PersonaSLM-model-cache/english_qwen25_15b_v1') / variant /
            (spec['name'] + '.Q4_K_M.gguf') for variant, spec in artifacts.MODELS.items()}


def external_path(path):
    path = Path(path)
    require(path in PHYSICAL.values(), 'Only the two exact authorized external model paths are allowed')
    for part in (path, *path.parents):
        require(not part.is_symlink() and not getattr(part, 'is_junction', lambda: False)(), 'External model link/junction refused')
    require(path.resolve() == next(p for p in PHYSICAL.values() if p == path).absolute(), 'External physical path changed')
    return path.resolve()


def external_gguf(path, expected_sha):
    physical = external_path(path)
    variant = next(key for key, value in PHYSICAL.items() if value == Path(path)); spec = artifacts.MODELS[variant]
    require(expected_sha == spec['sha256'] and physical.is_file() and physical.stat().st_size == spec['bytes'] and
            sha(physical) == expected_sha, 'Pinned external weight size/SHA mismatch')
    with physical.open('rb') as stream:
        header = stream.read(24)
    require(len(header) == 24 and header[:4] == b'GGUF', 'Invalid external GGUF header')
    version, tensors, keys = struct.unpack('<IQQ', header[4:])
    require(version in (2, 3) and tensors > 0 and keys > 0, 'Invalid external GGUF metadata')
    return {'path': str(physical), 'sha256': expected_sha, 'bytes': spec['bytes'], 'gguf_version': version,
            'sha256_verified': True, 'limitation': 'Pinned external artifact; actual loading still requires owned server.'}


def file_preflight(cfg):
    with patch.object(configuration, 'verify_gguf', external_gguf):
        return _FILE_PREFLIGHT(cfg)


def server_properties(props, cfg):
    require(external_path(props.get('model_path', '')) == external_path(cfg.model_file), 'External server model_path differs')
    require(props.get('default_generation_settings', {}).get('n_ctx') == cfg.n_ctx and
            isinstance(props.get('build_info'), str) and cfg.engine_revision in props['build_info'], 'Server context/build mismatch')
    return {'model_path_matches': True, 'n_ctx': cfg.n_ctx, 'build_info': props['build_info'],
            'model_identity_limit': 'Exact authorized external path plus pinned digest and owned process.'}


def source_hashes():
    paths = set(old.shared.runtime_python_dependency_paths([Path(__file__)]))
    paths.update(Path(p) for p in ('tests/test_english_sfh_model_comparison_v1.py',
        'tests/test_english_sfh_model_artifacts_v1.py', 'tests/test_english_sfh_execution_v1.py',
        'tests/test_english_sfh_registration_v1.py', 'tests/test_english_sfh_reproduce_v1.py'))
    paths.update((registration.metadata.TEMPLATE_RUNTIME_PROVENANCE, old.shared.TOKENIZER_SOURCE))
    paths.update(Path(p) for p in load(registration.metadata.TEMPLATE_RUNTIME_PROVENANCE)['package_file_sha256'])
    return {p.as_posix(): sha(p) for p in sorted(paths)}


def messages(*args):
    result = _MESSAGES(*args)
    suffix = "\n\nContinue with the Participant's next turn."
    require(result[-1]['content'].endswith(suffix), 'Frozen continuation instruction changed')
    result[-1]['content'] = result[-1]['content'][:-len(suffix)] + '\n\nParticipant:'
    return result


def render(variant, template, chat):
    require(variant in artifacts.MODELS, 'Unknown model configuration')
    if variant == 'base':
        return chat[0]['content'] + '\n\n' + chat[1]['content']
    return registration.metadata.render_native_template(template, chat)


def build(material, variant, template, tokenize):
    def identity(old_id):
        require(old_id.startswith('ENSFH_development_'), 'Inherited request identity')
        return old_id.replace('ENSFH_development_', 'ENMC_' + variant + '_', 1)
    with patch.object(registration, 'messages', messages), patch.object(old.shared.s, 'render',
            lambda text, chat: render(variant, text, chat)):
        rows, pooled = registration.build_requests(material, 'development', template,
            lambda prompt, name: tokenize(prompt, identity(name)))
    for row in rows:
        # The union of H/context labels is invariant even when History is absent.
        case_rows = [c for c in material['cases'] if c['speaker'] == row['speaker_id']]
        case_rows.sort(key=lambda c: (c['target_date'], c['target_meeting'], c['reference_continuation_not_for_prompt']['start']))
        case = case_rows[int(row['case_id'].rsplit('context', 1)[1]) - 1]
        others = {t['speaker'] for t in case['history'] + case['context']} - {case['speaker']}
        row.update(request_id=identity(row['request_id']),
                   stop=['\nParticipant:'] + [f'\nColleague {i + 1}:' for i in range(len(others))])
        row['request_sha256'] = old.shared.value_sha256({k: v for k, v in row.items() if k != 'request_sha256'})
    return rows, pooled


def payload(row):
    return dict(_PAYLOAD(row), stop=row['stop'])


def config(plan):
    model = plan['model']
    return old.shared.s.Runtime(model['model_file'], model['model_sha256'], model['backend_file'],
        model_label='Qwen2.5-1.5B-' + plan['batch'] + '-Q4_K_M-English-SFH', n_ctx=2048, max_new_tokens=128,
        prompt_template='plain_transcript_v1' if plan['batch'] == 'base' else 'official_native_instruct_v1')


def command(plan):
    cfg = config(plan); uri = urlsplit(cfg.endpoint)
    argv = [str(old.local(cfg.server_file)), '--model', str(external_path(cfg.model_file)), '--host', uri.hostname,
        '--port', str(uri.port), '--threads', str(cfg.threads), '--threads-batch', str(cfg.threads),
        '--ctx-size', str(cfg.n_ctx), '--parallel', '1', '--n-gpu-layers', '0', '--device', 'none',
        '--no-kv-offload', '--no-op-offload', '--no-context-shift', '--offline', '--verbosity', '4',
        '--no-warmup', '--no-mmproj', '--spec-type', 'none']
    if plan['batch'] == 'instruct':
        argv += ['--chat-template-file', str(old.local(plan['template_path'])), '--chat-template-kwargs', '{"enable_thinking":false}']
    return argv


def inputs(variant, protocol_sha, artifact_sha):
    require(variant in artifacts.MODELS and sha(PROTOCOL) == protocol_sha and
            sha(artifacts.RECEIPT) == artifact_sha, 'Externally bound model/protocol/artifact inputs')
    protocol, receipt = load(PROTOCOL), load(artifacts.RECEIPT)
    storage_binding = protocol['model_storage']
    require(storage_binding['path'] == STORAGE.as_posix() and sha(old.local(STORAGE, OUT)) == storage_binding['sha256'], 'Storage amendment binding')
    storage = load(STORAGE)
    require(storage['schema'] == 'english_model_comparison_storage_amendment_v1' and
            storage['baseline_generations'] == BASE_GENERATIONS and storage['baseline_inference_seconds'] == BASE_SECONDS,
            'Storage does not change study accounting')
    rubric = protocol['human_rubric']
    require(rubric['path'] == (OUT / 'primary_review_rubric_v1.json').as_posix() and
            sha(old.local(rubric['path'], OUT)) == rubric['sha256'], 'Prospective human rubric hash binding')
    require(protocol['schema'] == 'personaslm_english_model_comparison_protocol_v1' and
            protocol['design']['models'] == ['base', 'instruct'] and
            protocol['design']['requests_per_model'] == 100 and protocol['design']['total_maximum_attempts'] == 200,
            'Only the fixed two-model200 design is authorized')
    require(protocol['runtime'] == {k: v for k, v in RUNTIME.items() if k not in ('stop', 'enable_thinking')} |
            {'parallel_model_processes': 1}, 'Frozen execution settings')
    require(protocol['safety']['ram_gates_bytes'] == RAM and
            protocol['safety']['maximum_inference_seconds_per_model'] == 3600 and
            protocol['safety']['maximum_wall_seconds_per_model'] == 5400 and
            protocol['authorization']['validation_reserve'] == 160 and
            BASE_GENERATIONS + 200 + 160 <= 1200 and BASE_SECONDS + 7200 <= 72000, 'Safety/time/reserve allocation')
    require(receipt['schema'] == 'english_qwen25_15b_artifact_receipt_v1' and
            receipt['status'] == 'ARTIFACTS_VERIFIED_NOT_EXECUTION_GO' and
            receipt['paired_tensor_name_shape_type_layout_equal'] is True and
            all(receipt['official_tokenizer_files_equal'].values()), 'Verified paired artifact receipt required')
    selected, fixed = receipt['models'][variant], artifacts.MODELS[variant]
    logical = artifacts.WEIGHTS / variant / (fixed['name'] + '.Q4_K_M.gguf')
    require(storage['models'][variant] == {'logical_path': logical.as_posix(), 'physical_path': PHYSICAL[variant].as_posix(),
            'sha256': fixed['sha256'], 'bytes': fixed['bytes']}, 'Exact logical/physical artifact migration binding')
    weight = external_path(storage['models'][variant]['physical_path'])
    require(selected['model_file'] == logical.as_posix() and selected['model_sha256'] == fixed['sha256'] and
            selected['artifact_revision'] == fixed['revision'] and selected['upstream_revision'] == fixed['official_revision'] and
            selected['quantization'] == 'Q4_K_M' and weight.stat().st_size == fixed['bytes'] and
            sha(weight) == fixed['sha256'], 'Exact published model identity')
    for item in selected['metadata_files']:
        require(sha(old.local(item['path'], artifacts.ROOT / variant)) == item['sha256'], 'Official metadata changed')
    require(artifacts.inspect(variant, weight, artifacts.ROOT / variant) == selected['comparison'], 'Native GGUF/official identity changed')
    require(selected['comparison']['official_add_bos_token'] is False and
            selected['comparison']['gguf_add_bos_token'] in (None, False), 'Unsupported BOS behavior; actual native IDs also checked')
    require(sha(MATERIAL) == MATERIAL_SHA and sha(OLD_MANIFEST) == OLD_MANIFEST_SHA, 'Original qualified source changed')
    material = load(MATERIAL)
    require(material['cases'] == load(OLD_MANIFEST)['cases'], 'Source content differs from historical qualification')
    model = {k: selected[k] for k in ('model_file', 'model_sha256', 'artifact_revision', 'upstream_revision', 'quantization')}
    model.update(logical_model_file=logical.as_posix(), model_file=PHYSICAL[variant].as_posix())
    model.update(backend_file=protocol['model_artifacts']['backend'], backend_sha256=protocol['model_artifacts']['backend_sha256'])
    require(model['backend_file'] == old.shared.MODEL['backend_file'] and sha(Path(model['backend_file'])) ==
            model['backend_sha256'] == '71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846', 'Fixed CPU backend')
    template = load(artifacts.ROOT / variant / 'tokenizer_config.json')['chat_template']
    registration.metadata.verified_template_runtime()
    return protocol, receipt, material, model, template


def baseline(plan):
    require(sha(BASELINE) == BASELINE_SHA, '788 baseline changed')
    historical = load(BASELINE)
    require(historical['cumulative_generations'] == BASE_GENERATIONS and
            historical['cumulative_inference_seconds'] == BASE_SECONDS, 'Historical cost mismatch')
    if plan['batch'] == 'base':
        require(plan['prior_receipt'] == {'path': BASELINE.as_posix(), 'sha256': BASELINE_SHA}, 'Base predecessor')
        return BASE_GENERATIONS, BASE_SECONDS
    prior = plan['prior_receipt']; path = OUT / 'base_execution_receipt_v1.json'
    require(prior['path'] == path.as_posix() and sha(path) == prior['sha256'], 'Actual Base receipt binding')
    receipt = load(path); frozen = PRIVATE / 'base/frozen_manifest_v1.json'; parent = load(frozen)
    require(receipt['status'] == 'PASS' and receipt['attempts'] == receipt['responses'] == 100 and
            receipt['failed_seconds'] == 0 and receipt['manifest_sha256'] == sha(frozen), 'Base must finish100; no repair/skip')
    require(parent['bindings'] == plan['bindings'], 'Paired protocol/artifact configuration changed')
    folder = old.local(receipt['run_directory'], PRIVATE / 'base/runs')
    archive = load(folder / 'manifest.json'); events = independent.read_events(folder)
    require(archive['frozen_manifest'] == parent and archive['claim'] == load(PRIVATE / 'base/claim_v1.json') and
            events[-1]['kind'] == 'run_finished' and events[-1]['event_hash'] == receipt['terminal_event_sha256'] and
            all(receipt[k] == v for k, v in events[-1]['data'].items()), 'Sealed Base archive/terminal/claim')
    hash_only = {e['data']['path']: e['data']['sha256'] for e in events if e['kind'] == 'hash_only_input'}
    for kind in ('source', 'input'):
        for name, digest in parent[kind + '_hashes'].items():
            source = old.local(name).relative_to(Path.cwd().resolve())
            archived = source if name in hash_only else folder / (('source' if name in parent['source_hashes'] else kind) + '_snapshot') / source
            require(sha(archived) == digest, 'Base snapshot/input changed')
    with patch.object(independent, 'expected_payload', payload):
        independent.reconcile(parent, receipt, events, BASE_GENERATIONS, BASE_SECONDS)
    require(receipt['cumulative_generations'] + 100 + 160 <= 1200 and
            receipt['cumulative_inference_seconds'] + 3600 <= 72000, 'Instruct/reserve cumulative ceiling')
    return receipt['cumulative_generations'], receipt['cumulative_inference_seconds']


@contextmanager
def scoped(model, material, template):
    def validate(path, digest):
        require(sha(old.local(path, PRIVATE)) == digest, 'Externally supplied manifest SHA')
        plan = load(path); variant = plan['batch']
        require(variant in artifacts.MODELS and old.local(path) == old.local(PRIVATE / variant / 'frozen_manifest_v1.json') and
                plan['schema'] == STUDY and plan['language'] == 'en' and plan['model'] == model and
                plan['runtime'] == RUNTIME and plan['cases'] == material['cases'], 'Frozen study/model/material scope')
        require(plan['source_head'] == subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() and
                plan['source_hashes'] == source_hashes(), 'Source version/closure changed')
        require(plan['authorization'] == {'decision': 'AUTHORIZED', 'maximum_attempts': 100} and
                plan['allocation'] == {'maximum_inference_seconds': 3600, 'maximum_wall_seconds': 5400}, 'Finite allocation changed')
        require(plan['scientific_prerequisites'] == {'approved_for_execution': True,
                'human_semantic_labels_available': False}, 'New-output semantic labels must remain unavailable')
        required = {PROTOCOL.as_posix(): plan['bindings']['protocol_sha256'], artifacts.RECEIPT.as_posix():
            plan['bindings']['artifact_receipt_sha256'], MATERIAL.as_posix(): MATERIAL_SHA,
            OLD_MANIFEST.as_posix(): OLD_MANIFEST_SHA, plan['prior_receipt']['path']: plan['prior_receipt']['sha256'],
            plan['template_path']: old.th(template)}
        rubric = load(PROTOCOL)['human_rubric']; required[rubric['path']] = rubric['sha256']
        storage = load(PROTOCOL)['model_storage']; required[storage['path']] = storage['sha256']
        required.update({item['path']: item['sha256'] for item in load(artifacts.RECEIPT)['models'][variant]['metadata_files']})
        require(all(plan['input_hashes'].get(p) == h for p, h in required.items()), 'Required snapshot inputs missing')
        require(all(sha(old.local(name)) == digest for name, digest in plan['input_hashes'].items()), 'Bound input changed')
        require(plan['template_sha256'] == old.th(template) and
                old.local(plan['template_path'], PRIVATE).read_text(encoding='utf-8') == template, 'Official template binding')
        old.validate_rows(plan)
        ids = {r['request_id']: r['input_token_ids'] for r in plan['requests']}
        rows, pooled = build(material, variant, template, lambda _, name: ids[name])
        require(rows == plan['requests'] and pooled == plan['pooled_development_style'], 'Reconstructed100 prompts/requests differ')
        for row in rows:
            require(row['input_token_ids'][0] != 151643 and
                    (variant == 'base' or row['input_token_ids'][0] == 151644), 'Native BOS/chat-prefix behavior differs')
            native = PRIVATE / variant / 'native_tokenizer' / (row['request_id'] + '.json')
            require(native.as_posix() in plan['input_hashes'], 'Native tokenizer receipt not bound')
            independent.verify_native_receipt(load(native), row)
        return plan, *baseline(plan)
    with ExitStack() as stack:
        for name, value in {'OUT': OUT, 'PRIVATE': PRIVATE, 'MODEL': model, 'RUNTIME': RUNTIME,
                'SIZES': {'development': (5, 100), 'base': (5, 100), 'instruct': (5, 100)},
                'MIN_RAM': RAM[0], 'READY_RAM': RAM[1], 'LIVE_RAM': RAM[2],
                'validate': validate, 'config': config, 'payload': payload}.items():
            stack.enter_context(patch.object(old, name, value))
        stack.enter_context(patch.object(old.shared.s, 'command', command))
        stack.enter_context(patch.object(old.shared.b, 'file_preflight', file_preflight))
        stack.enter_context(patch.object(old.shared.b, 'validate_server_properties', server_properties))
        yield


def register(variant, protocol_sha, artifact_sha, prior_sha=None):
    protocol, artifacts_receipt, material, model, template = inputs(variant, protocol_sha, artifact_sha)
    bindings = {'protocol_sha256': protocol_sha, 'artifact_receipt_sha256': artifact_sha}
    prior = {'path': BASELINE.as_posix(), 'sha256': BASELINE_SHA} if variant == 'base' else {
        'path': (OUT / 'base_execution_receipt_v1.json').as_posix(), 'sha256': prior_sha}
    baseline({'batch': variant, 'prior_receipt': prior, 'bindings': bindings})
    folder = PRIVATE / variant
    with old.shared.b.writer_lock(PRIVATE), scoped(model, material, template):
        old.unused(variant)
        require(not folder.exists(), 'Preserve prior registration; no automatic retokenization')
        observation = old.memory(RAM[0], os.getpid()); identity = old.shared._tokenizer_identity()
        old.write(folder / 'registration_claim_v1.json', {'bindings': bindings, 'prior_receipt': prior,
            'started_utc': old.shared.b.utc_now(), 'maximum_attempts': 100, 'new_generations': 0})
        try:
            rows, pooled = build(material, variant, template, lambda prompt, name:
                registration.native_tokenize(prompt, folder / 'native_tokenizer' / (name + '.json')))
        except BaseException as exc:
            old.write(folder / 'registration_failure_v1.json', {'status': 'FAILED_NO_GENERATIONS',
                'error_type': type(exc).__name__, 'error': str(exc), 'new_generations': 0,
                'preserve_native_receipts_and_claim': True, 'automatic_retry_allowed': False})
            raise
        template_path = folder / 'official_chat_template.jinja'
        with template_path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(template)
        bound = {PROTOCOL.as_posix(): protocol_sha, artifacts.RECEIPT.as_posix(): artifact_sha,
            MATERIAL.as_posix(): MATERIAL_SHA, OLD_MANIFEST.as_posix(): OLD_MANIFEST_SHA,
            prior['path']: prior['sha256'],
            template_path.as_posix(): sha(template_path)}
        bound[protocol['human_rubric']['path']] = protocol['human_rubric']['sha256']
        bound[protocol['model_storage']['path']] = protocol['model_storage']['sha256']
        bound.update({item['path']: item['sha256'] for item in artifacts_receipt['models'][variant]['metadata_files']})
        bound.update({p.as_posix(): sha(p) for p in (folder / 'native_tokenizer').glob('*.json')})
        plan = {'schema': STUDY, 'batch': variant, 'language': 'en', 'bindings': bindings, 'model': model,
            'runtime': RUNTIME, 'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'source_hashes': source_hashes(), 'input_hashes': bound, 'cases': material['cases'], 'requests': rows,
            'pooled_development_style': pooled, 'prior_receipt': prior,
            'authorization': {'decision': 'AUTHORIZED', 'maximum_attempts': 100},
            'scientific_prerequisites': {'approved_for_execution': True, 'human_semantic_labels_available': False},
            'allocation': {'maximum_inference_seconds': 3600, 'maximum_wall_seconds': 5400},
            'template_path': template_path.as_posix(), 'template_sha256': old.th(template), 'tokenizer_identity': identity}
        frozen = folder / 'frozen_manifest_v1.json'; old.write(frozen, plan); old.validate(frozen, sha(frozen))
        receipt = {'status': 'FROZEN_NOT_EXECUTED', 'batch': variant, 'bindings': bindings, 'requests': 100,
            'manifest_sha256': sha(frozen), 'model': model, 'source_head': plan['source_head'],
            'input_token_range': [min(r['input_tokens'] for r in rows), max(r['input_tokens'] for r in rows)],
            'memory_before_tokenization': observation, 'new_generations': 0, 'model_order': ['base', 'instruct'],
            'limitation': 'Development deployment configurations; model order/time confounded; no new human ratings.'}
        old.write(OUT / (variant + '_registration_v1.json'), receipt)
        return receipt


def execute(action, manifest_path, manifest_sha, preflight_path=None):
    require(action in ('validate', 'preflight', 'run') and sha(old.local(manifest_path, PRIVATE)) == manifest_sha, 'Action/manifest binding')
    plan = load(manifest_path); bindings = plan['bindings']
    _, _, material, model, template = inputs(plan['batch'], bindings['protocol_sha256'], bindings['artifact_receipt_sha256'])
    with scoped(model, material, template):
        if action == 'validate':
            _, count, seconds = old.validate(manifest_path, manifest_sha)
            return {'status': 'VALIDATED_NOT_EXECUTED', 'baseline_generations': count, 'baseline_inference_seconds': seconds}
        if action == 'preflight':
            return old.preflight(manifest_path, manifest_sha)
        require(preflight_path is not None, 'Fresh passing preflight required')
        return old.run(manifest_path, manifest_sha, preflight_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('register', 'validate', 'preflight', 'run'))
    for name in ('variant', 'protocol-sha256', 'artifact-receipt-sha256', 'prior-receipt-sha256', 'manifest-sha256'):
        parser.add_argument('--' + name)
    for name in ('manifest', 'preflight', 'output'):
        parser.add_argument('--' + name, type=Path)
    args = parser.parse_args()
    if args.action == 'register':
        result = register(args.variant, args.protocol_sha256, args.artifact_receipt_sha256, args.prior_receipt_sha256)
    elif args.action == 'preflight':
        require(args.output is not None, 'Exclusive preflight output required'); old.local(args.output, OUT)
        try:
            result = execute(args.action, args.manifest, args.manifest_sha256)
        except Exception as exc:
            observation = old.shared.s.memory_observation(os.getpid()); available = observation.get('system', {}).get('available_physical')
            result = {'status': 'FAIL', 'checked_utc': old.shared.b.utc_now(), 'error': str(exc), 'memory': observation,
                'required_available_bytes': RAM[0], 'ram_deficit_bytes': max(0, RAM[0] - available) if type(available) is int else None,
                'new_generations': 0, 'retry_without_material_change': False}
        old.write(args.output, result)
    else:
        result = execute(args.action, args.manifest, args.manifest_sha256, args.preflight)
    print(json.dumps(result, indent=2))
