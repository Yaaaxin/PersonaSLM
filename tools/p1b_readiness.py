"""Prepare/reconstruct P1b materials offline. There is no execute action."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess

from personaslm.p1b import canonical_hash, TEMPLATE
from personaslm.p1b_readiness import (revise, audit, requests, review_rows, precision_plan,
                                    validate_reviews, VERSION, ORDER_SEED)
from personaslm.provenance import require_local_path
from p1b_design import read, digest, csv_rows, write_json, write_csv, historical_audit

PUBLIC = Path('docs/validation/p1b/final_v1')
LOCAL = Path('results/p1b_readiness/v1')
PARENT = Path('data/synthetic/p1b_development_proposed_v1.json')
DATASET = Path('data/synthetic/p1b_development_proposed_v2.json')


def preservation():
    baseline = read(LOCAL/'baseline.json')
    allowed = {'.gitignore', 'docs/research_development_log.md'}
    changed = [p for p, h in baseline['files'].items() if digest(p) != h]
    if set(changed) - allowed:
        raise ValueError('Historical tracked material changed: ' + repr(changed))
    return {'baseline_git_sha': baseline['git_sha'], 'baseline_clean': not baseline['git_status'],
            'tracked_files_compared': len(baseline['files']), 'permitted_current_edits': changed,
            'historical_tracked_files_unchanged': len(baseline['files']) - len(changed)}


def build():
    if PUBLIC.exists() or DATASET.exists():
        raise FileExistsError('Version already exists; preserve it and use an explicitly new version')
    dataset, changes = revise(read(PARENT), digest(PARENT))
    validation = audit(dataset)
    historical, _ = historical_audit()
    historical['tracked_preservation'] = preservation()
    design = read('docs/validation/p1/wave1_design_v1.json')
    plan = requests(dataset)
    decoding = {'cache_prompt': False, 'n_predict': 96, 'return_tokens': True, 'seed': 42,
                'stop': [], 'stream': False, 'temperature': 0.0, 'top_p': 1.0}
    old_manifest = read('docs/validation/p1/wave1_manifest_v1.json')
    if decoding != old_manifest['decoding']:
        raise ValueError('Historical decoding mismatch')
    source_paths = sorted(Path('src/personaslm').glob('*.py')) + [
        Path('tools/p1b_readiness.py'), Path('tools/p1b_design.py'), Path('tests/test_p1b_readiness.py'),
        Path('configs/p1_wave1_v1.json'), Path('docs/research_protocol_v1.1.md'),
        Path('docs/PersonaSLM_Research_Protocol_v1.2_Revised_Proposed_r1.md')]
    sources = {p.as_posix(): digest(p) for p in source_paths}
    write_json(DATASET, dataset)
    PUBLIC.mkdir(parents=True)
    write_json(PUBLIC/'correction_register_v1.json', {'version': VERSION, 'parent_sha256': digest(PARENT),
        'child_sha256': digest(DATASET), 'corrected_cases': len(changes), 'corrections': changes,
        'selection_basis': 'Question/source analysis before inference; no response-dependent selection', 'human_approval': 'OPEN'})
    write_json(PUBLIC/'case_validation_v1.json', validation)
    write_json(PUBLIC/'historical_integrity_v1.json', historical)
    write_json(PUBLIC/'precision_v1.json', precision_plan(dataset))
    write_csv(PUBLIC/'stimulus_review_v2.csv', review_rows(dataset, validation, digest(DATASET)))
    control_source = Path('docs/validation/p1/control_review_v1.csv')
    with (PUBLIC/'neutral_control_review_v1.csv').open('xb') as f:
        f.write(control_source.read_bytes())
    write_json(PUBLIC/'control_scope_v1.json', {'source': control_source.as_posix(), 'source_sha256': digest(control_source),
        'copied_csv_sha256': digest(PUBLIC/'neutral_control_review_v1.csv'), 'items': 24, 'exact_recorded_matches': 24,
        'semantic_review': 'OPEN', 'dataset_scope': 'Original P1 Wave 1; not P1b',
        'p1b_controls_prepared': 0, 'transfer_of_approval_or_token_counts': False, 'new_tokenizer_requests': 0})
    applicability = [{'request_id': r['request_id'], 'case_id': r['case_id'], 'persona_id': r['persona_id'],
        'condition': r['condition'], **r['applicability'], 'structural_response_status': True,
        'semantic_completeness_diagnostic': True, 'human_annotation_status': 'NOT_GENERATED'} for r in plan]
    write_csv(PUBLIC/'evaluation_applicability_v1.csv', applicability)
    write_json(PUBLIC/'evaluation_routing_v1.json', {
        'version': 'p1b_manual_semantic_routing_proposed_v1', 'status': 'AWAITING_RESEARCHER_APPROVAL',
        'response_policy': 'response_status_v1', 'axis_policy': 'separate_axes_policy_v1',
        'scoring_unit': 'Frozen first-reply extraction with full continuation and boundary uncertainty retained',
        'factual_categories': ['Correct', 'Incorrect', 'Unverifiable', 'Not Applicable'],
        'temporal_categories': ['Correct', 'Incorrect', 'Unverifiable', 'Not Applicable'],
        'relevance_scale': [1, 2, 3, 4, 5], 'coherence_scale': [1, 2, 3, 4, 5],
        'semantic_completeness': ['COMPLETE', 'INCOMPLETE', 'UNCERTAIN'],
        'automatic_semantic_scorer': None, 'city_scorer_allowed': False,
        'oracle_role': 'Source/query stimulus validation only; never free-text scoring',
        'full_eligible_denominator_required': True, 'exclude_c0_incorrect_cases': False,
        'unknown_is_incorrect': False, 'incomplete_is_incorrect': False,
        'partial_supported_answer': 'Factual support may be Correct; answer completeness and relevance are separate.',
        'missing_or_unscorable': 'Retain eligible row, unknown score, explicit reason; report coverage and paired bounds.',
        'factual_eligible': 192, 'temporal_eligible': 88, 'relevance_eligible': 192, 'coherence_eligible': 192,
        'structural_eligible': 192, 'linguistic_fidelity_eligible': 0, 'behavioral_fidelity_eligible': 0})
    config = {**design['configuration'], 'prompt_template': TEMPLATE, 'threads_batch': 4, 'n_gpu_layers': 0}
    git_status = subprocess.check_output(['git', 'status', '--short'], text=True)
    manifest = {'version': 'p1b_calibration_manifest_v1', 'status': 'PREPARED_NOT_AUTHORIZED',
        'created_utc': datetime.now(timezone.utc).isoformat(), 'formal_protocol': 'v1.1', 'adopts_v1_2': False,
        'git_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'git_status': git_status, 'git_dirty': bool(git_status.strip()),
        'source_hashes': sources, 'source_snapshot': (LOCAL/'source_snapshot').as_posix(),
        'dataset': DATASET.as_posix(), 'dataset_sha256': digest(DATASET), 'parent_dataset_sha256': digest(PARENT),
        'development_only': True, 'confirmatory': False, 'execution_authorized': False,
        'cases': 24, 'speakers': 12, 'planned_requests': 192, 'executed_requests': 0,
        'selection_rule': 'All 24 pre-existing prototypes with three documented pre-inference corrections; no output selection.',
        'order_seed': ORDER_SEED, 'order_algorithm': 'Python random.Random; shuffle all cases, then shuffle C0-C7 within each case block.',
        'python_version': platform.python_version(), 'case_order': list(dict.fromkeys(r['case_id'] for r in plan)),
        'state_policy': 'Stateless native requests; cache_prompt=false; fresh request per cell. No previous generated text enters later prompts.',
        'resume_policy': 'Immutable run segments; retain failed attempts; resume only uncompleted request IDs from this order. No successful-output reruns or overwrite.',
        'configuration': config, 'configuration_sha256': canonical_hash(config), 'generation_parameters': decoding,
        'model_sha256': historical['model_sha256'], 'backend_sha256': historical['backend_sha256'],
        'backend_build': 'b11573', 'backend_commit': '0f701c882',
        'tokenizer_preflight': {'status': 'PENDING', 'endpoint': '/tokenize',
            'options': {'add_special': True, 'parse_special': False, 'with_pieces': False},
            'requirement': 'Pinned loaded GGUF; persist IDs, count and native response for all192; require count+96<=4096.',
            'new_requests_executed': 0},
        'response_status_version': 'response_status_v1', 'evaluation_policy_version': 'separate_axes_policy_v1',
        'evaluation_routing_version': 'p1b_manual_semantic_routing_proposed_v1',
        'runner_gate': 'Existing P1 Wave 1 runner is not a P1b execution command; consume this plan through a reviewed versioned adapter before authorization.',
        'neutral_control_requests': 0, 'requests': plan}
    write_json(PUBLIC/'calibration_manifest_v1.json', manifest)
    for p in source_paths:
        dest = LOCAL/'source_snapshot'/p
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as f:
            f.write(p.read_bytes())
    files = [DATASET] + sorted(PUBLIC.glob('*'))
    write_json(PUBLIC/'hash_inventory_v1.json', {'version': 'p1b_readiness_inventory_v1',
        'files': {p.as_posix(): digest(p) for p in files}, 'sources': sources,
        'source_snapshot': manifest['source_snapshot'], 'inventory_self_hash_excluded': True})
    print(json.dumps({'status': 'PASS', 'independent_analytic_cases': 24, 'planned_prompts': 192,
        'human_approvals': 0, 'new_tokenizations': 0, 'new_generations': 0, 'execution_ready': False,
        'historical_run_files_unchanged': historical['historical_run_files_unchanged']}))


def verify():
    inventory = read(PUBLIC/'hash_inventory_v1.json')
    for p, h in inventory['files'].items():
        if digest(p) != h:
            raise ValueError('Prepared artifact changed: ' + p)
    for p, h in inventory['sources'].items():
        if digest(p) != h or digest(Path(inventory['source_snapshot'])/p) != h:
            raise ValueError('Source or snapshot changed: ' + p)
    data, changes = revise(read(PARENT), digest(PARENT))
    validation = audit(data)
    if data != read(DATASET) or validation != read(PUBLIC/'case_validation_v1.json'):
        raise ValueError('Dataset or analytic reconstruction mismatch')
    if changes != read(PUBLIC/'correction_register_v1.json')['corrections']:
        raise ValueError('Correction reconstruction mismatch')
    manifest = read(PUBLIC/'calibration_manifest_v1.json')
    if requests(data) != manifest['requests'] or precision_plan(data) != read(PUBLIC/'precision_v1.json'):
        raise ValueError('Order or precision reconstruction mismatch')
    expected = [{k: str(v) for k, v in r.items()} for r in review_rows(data, validation, digest(DATASET))]
    if expected != csv_rows(PUBLIC/'stimulus_review_v2.csv'):
        raise ValueError('Blank stimulus master changed')
    if digest(PUBLIC/'neutral_control_review_v1.csv') != digest('docs/validation/p1/control_review_v1.csv'):
        raise ValueError('Original control master copy changed')
    historical, _ = historical_audit()
    prior = read(PUBLIC/'historical_integrity_v1.json')
    if historical != {k: v for k, v in prior.items() if k != 'tracked_preservation'}:
        raise ValueError('Historical reconstruction mismatch')
    print(json.dumps({'status': 'PASS', 'planned_requests_reconstructed': len(manifest['requests']),
        'prompt_hashes': 192, 'new_generations': 0, 'preservation': preservation(),
        'native_tokenizations_reconciled': historical['recorded_native_tokenizations_reconciled'],
        'historical_run_files_unchanged': historical['historical_run_files_unchanged'],
        'model_and_backend_file_hashes': 'PASS', 'new_prompt_tokenization': 'PENDING'}))


def import_review(source, output):
    source, output = require_local_path(source), require_local_path(output)
    result = validate_reviews(csv_rows(PUBLIC/'stimulus_review_v2.csv'), csv_rows(source))
    output.mkdir(parents=True, exist_ok=False)
    with (output/'original.csv').open('xb') as f:
        f.write(source.read_bytes())
    write_json(output/'registration.json', {**result, 'version': 'p1b_stimulus_registration_v1',
        'source_sha256': digest(source), 'master_sha256': digest(PUBLIC/'stimulus_review_v2.csv'),
        'imported_utc': datetime.now(timezone.utc).isoformat(), 'reviewed_utc': 'Only as supplied in original.csv',
        'provenance': 'As supplied; import neither implies blind annotation nor authorizes inference', 'records': csv_rows(source)})
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['build', 'verify', 'import-review'])
    parser.add_argument('--csv', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'build':
        build()
    elif args.action == 'verify':
        verify()
    elif not args.csv or not args.output:
        parser.error('import-review needs --csv and --output')
    else:
        import_review(args.csv, args.output)
