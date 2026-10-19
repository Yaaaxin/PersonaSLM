"""Two sealed model runs to technical results and one mixed, blank review package.

Implemented after execution registration, before inspecting new outputs. No
semantic labels, model calls, protected-map reads or frozen helper edits.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
from unittest.mock import patch

import english_sfh_model_comparison_v1 as controller
import english_sfh_analysis_v1 as primary
import english_sfh_reproduce_v1 as independent
import english_sfh_review_delivery_v1 as delivery
import english_model_comparison_review_v1 as review

OUT, PRIVATE = controller.OUT, controller.PRIVATE
require, load, sha = controller.require, controller.load, controller.sha
METRICS = ('input_tokens', 'output_tokens', 'latency_seconds', 'native_prefill_seconds',
           'native_decode_seconds', 'native_eos', 'native_limit', 'native_stop_word')
HELPERS = {'tools/english_sfh_analysis_v1.py': '08e30da9564042d84f35d0a477aab0c43f460a491170d463ab57d75ea7a15f5a',
           'tools/english_sfh_reproduce_v1.py': '0d5402fcf578852c23910660ceaf70795d8db3dde26c44ff8625cbc544489701',
           'tools/english_sfh_review_delivery_v1.py': '08a9c443d8a03c08cf7a78e4de3d1a9cb70b1b2eeef0bc93746e93c3f427dc04',
           'tools/english_model_comparison_review_v1.py': '0bf68f15c41b12258493969b511698175501c87609956c6b3550fca496586820'}


def source_bindings():
    require(all(sha(Path(p)) == h for p, h in HELPERS.items()), 'Fixed analysis/review helper changed')
    paths = controller.old.shared.runtime_python_dependency_paths([Path(__file__)])
    paths = set(paths) | {Path('tests/test_english_model_comparison_analysis_v1.py')}
    return {p.resolve().relative_to(Path.cwd().resolve()).as_posix(): sha(p) for p in sorted(paths)}


def archival_plan(plan, variant):
    """Read-only byte-bound validation; a legitimate Git commit is not new evidence."""
    bindings = plan['bindings']
    protocol, artifacts, material, model, template = controller.inputs(
        variant, bindings['protocol_sha256'], bindings['artifact_receipt_sha256'])
    require(plan['schema'] == controller.STUDY and plan['batch'] == variant and plan['language'] == 'en' and
            plan['model'] == model and plan['runtime'] == controller.RUNTIME and plan['cases'] == material['cases'],
            'Archived study/model/material scope changed')
    require(plan['source_hashes'] == controller.source_hashes(), 'Live executable bytes differ from archived source bindings')
    require(plan['authorization'] == {'decision': 'AUTHORIZED', 'maximum_attempts': 100} and
            plan['allocation'] == {'maximum_inference_seconds': 3600, 'maximum_wall_seconds': 5400} and
            plan['scientific_prerequisites'] == {'approved_for_execution': True, 'human_semantic_labels_available': False},
            'Archived authorization/measurement scope changed')
    required = {controller.PROTOCOL.as_posix(): bindings['protocol_sha256'],
        controller.artifacts.RECEIPT.as_posix(): bindings['artifact_receipt_sha256'],
        controller.MATERIAL.as_posix(): controller.MATERIAL_SHA,
        controller.OLD_MANIFEST.as_posix(): controller.OLD_MANIFEST_SHA,
        plan['prior_receipt']['path']: plan['prior_receipt']['sha256'],
        plan['template_path']: controller.old.th(template)}
    for name in ('human_rubric', 'model_storage'):
        required[protocol[name]['path']] = protocol[name]['sha256']
    required.update({item['path']: item['sha256'] for item in artifacts['models'][variant]['metadata_files']})
    require(all(plan['input_hashes'].get(p) == h for p, h in required.items()), 'Archived required input binding missing')
    require(plan['template_sha256'] == controller.old.th(template) and
            controller.old.local(plan['template_path'], PRIVATE).read_text(encoding='utf-8') == template,
            'Archived official template changed')
    with patch.object(controller.old, 'SIZES', {variant: (5, 100)}):
        controller.old.validate_rows(plan)
    ids = {r['request_id']: r['input_token_ids'] for r in plan['requests']}
    rebuilt, pooled = controller.build(material, variant, template, lambda _, name: ids[name])
    require(rebuilt == plan['requests'] and pooled == plan['pooled_development_style'],
            'Archived exact source-to-request reconstruction changed')
    count, seconds = controller.baseline(plan)
    return {'baseline_generations': count, 'baseline_inference_seconds': seconds}


def audit_run(variant, expected_receipt):
    require(variant in ('base', 'instruct'), 'Unknown variant')
    receipt_path = OUT / (variant + '_execution_receipt_v1.json')
    require(sha(receipt_path) == expected_receipt, 'Externally anchored execution receipt changed')
    receipt = load(receipt_path)
    manifest = PRIVATE / variant / 'frozen_manifest_v1.json'
    require(sha(manifest) == receipt['manifest_sha256'], 'Archived manifest hash changed')
    plan = load(manifest)
    require(receipt['status'] == 'PASS' and receipt['attempts'] == receipt['responses'] == 100 and
            receipt['unattempted'] == receipt['retries'] == 0, 'Both complete100 runs required; partial evidence stays separate')
    baseline = archival_plan(plan, variant)
    folder = controller.old.local(receipt['run_directory'], PRIVATE / variant / 'runs')
    archive, registration = load(folder / 'manifest.json'), load(OUT / (variant + '_registration_v1.json'))
    require(archive['frozen_manifest'] == plan and archive['claim'] == load(PRIVATE / variant / 'claim_v1.json') and
            registration['manifest_sha256'] == receipt['manifest_sha256'], 'Manifest/claim/registration mismatch')
    events = independent.read_events(folder)
    require(events[-1]['kind'] == 'run_finished' and events[-1]['event_hash'] == receipt['terminal_event_sha256'] and
            all(receipt[k] == v for k, v in events[-1]['data'].items()), 'Sealed terminal binding')
    hash_only = {e['data']['path']: e['data']['sha256'] for e in events if e['kind'] == 'hash_only_input'}
    for name, digest in plan['source_hashes'].items():
        require(sha(folder / 'source_snapshot' / independent.relative(name)) == digest, 'Source snapshot mismatch')
    for name, digest in plan['input_hashes'].items():
        if name in plan['source_hashes']:
            require(plan['source_hashes'][name] == digest, 'Conflicting input/source binding')
        elif name in hash_only:
            require(hash_only[name] == digest and sha(Path(name)) == digest, 'Retained input mismatch')
        else:
            require(sha(folder / 'input_snapshot' / independent.relative(name)) == digest, 'Input snapshot mismatch')
    for request in plan['requests']:
        require(request['input_token_ids'][0] != 151643 and
                (variant == 'base' or request['input_token_ids'][0] == 151644), 'Archived native BOS/prefix changed')
        native = PRIVATE / variant / 'native_tokenizer' / (request['request_id'] + '.json')
        require(native.as_posix() in plan['input_hashes'], 'Archived native receipt lacks input hash binding')
        independent.verify_native_receipt(load(folder / 'input_snapshot' / native), request)
    with patch.object(independent, 'expected_payload', controller.payload):
        rows, cost, failures = independent.reconcile(plan, receipt, events,
            baseline['baseline_generations'], baseline['baseline_inference_seconds'])
    require(failures == 0 and receipt['failed_seconds'] == 0, 'Failed attempts may not be silently excluded')
    raw = {e['data']['request_id']: e['data'] for e in events if e['kind'] == 'english_sfh_raw'}
    require(len(raw) == 100 and set(raw) == {r['request_id'] for r in plan['requests']}, 'Exact response allocation')
    technical = technical_rows(plan['requests'], raw, rows)
    require(sha(receipt_path) == expected_receipt, 'Receipt changed while auditing')
    return plan, receipt, technical, raw


def technical_rows(requests, raw, checked_rows):
    result = []
    for request, checked in zip(requests, checked_rows, strict=True):
        require(request['request_id'] == checked['request_id'], 'Audited row order changed')
        observed = raw[request['request_id']]; response = observed['response']
        measured = primary.measure(request, response, observed['latency_seconds'])
        independent.compare(measured, checked['measurements'], 'Independent native/raw measurement')
        values = {k: measured[k] for k in ('output_tokens', 'latency_seconds', 'native_eos', 'native_limit')}
        values.update(input_tokens=request['input_tokens'], native_stop_word=int(response.get('stop_type') == 'word'))
        timing = response.get('timings') or {}
        for metric, field in (('native_prefill_seconds', 'prompt_ms'), ('native_decode_seconds', 'predicted_ms')):
            value = timing.get(field)
            require(value is None or type(value) in (int, float) and math.isfinite(value) and value >= 0,
                    'Invalid native timing; do not replace with zero')
            values[metric] = value / 1000 if value is not None else None
        result.append({k: checked[k] for k in ('request_id', 'speaker_id', 'case_id', 'condition', 'phase')} |
                      {'measurements': values})
    return result


def estimates(rows):
    with patch.object(primary, 'METRICS', METRICS), patch.object(independent, 'METRICS', METRICS):
        result = primary.estimates(rows)
        independent.compare(result, independent.estimates(rows), 'Two factorial/control implementations')
    return result


def paired_rows(base, instruct):
    key = lambda r: (r['speaker_id'], r['case_id'], r['condition'])
    a, b = {key(r): r for r in base}, {key(r): r for r in instruct}
    require(len(a) == len(base) == len(b) == len(instruct) == 100 and set(a) == set(b), 'Exact paired100 grid required')
    result = []
    for cell in sorted(a):
        require(a[cell]['phase'] == b[cell]['phase'], 'Matched phase changed')
        values = {m: b[cell]['measurements'][m] - a[cell]['measurements'][m]
                  if a[cell]['measurements'][m] is not None and b[cell]['measurements'][m] is not None else None
                  for m in METRICS}
        result.append({k: a[cell][k] for k in ('request_id', 'speaker_id', 'case_id', 'condition', 'phase')} |
                      {'measurements': values})
    return result


def summarize(rows):
    # Anonymous speaker ordinals do not expose the corpus or prompt speaker IDs.
    return {'all_speakers': estimates(rows), 'speaker_profiles': {
        'speaker_' + str(i): estimates([r for r in rows if r['speaker_id'] == speaker])
        for i, speaker in enumerate(sorted({r['speaker_id'] for r in rows}), 1)}}


def calculate(base_sha, instruct_sha):
    sources = source_bindings()
    runs = {v: audit_run(v, h) for v, h in (('base', base_sha), ('instruct', instruct_sha))}
    base, instr = runs['base'], runs['instruct']
    require(base[0]['bindings'] == instr[0]['bindings'] and base[0]['cases'] == instr[0]['cases'] and
            instr[0]['prior_receipt'] == {'path': (OUT / 'base_execution_receipt_v1.json').as_posix(), 'sha256': base_sha},
            'Paired source/protocol/budget chain differs')
    require(len({r['request_id'] for v in runs.values() for r in v[0]['requests']}) == 200, 'Duplicate model request IDs')
    for a, b in zip(base[0]['requests'], instr[0]['requests'], strict=True):
        require(all(a[k] == b[k] for k in ('speaker_id', 'case_id', 'condition', 'phase', 'messages', 'stop')),
                'Models did not receive the identical paired source/context/task allocation')
    dossiers = {k: delivery.dossier(c) for k, c in delivery.case_lookup(base[0]).items()}
    records = [{'request_id': r['request_id'], 'case_id': r['case_id'], 'dossier': dossiers[r['case_id']],
                'response': runs[v][3][r['request_id']]['response']['content']}
               for v in ('base', 'instruct') for r in runs[v][0]['requests']]
    rows = {v: runs[v][2] for v in runs}; paired = paired_rows(rows['base'], rows['instruct'])
    stops = {v: [{'request_id': request_id, **{k: raw['response'].get(k) for k in
                 ('stop_type', 'stopping_word', 'stopped_word', 'stopped_eos', 'stopped_limit')}}
                 for request_id, raw in runs[v][3].items()] for v in runs}
    private = {'technical_rows': rows, 'paired_instruct_minus_base_rows': paired,
               'native_stopping_records': stops, 'review_records': records}
    report = {'schema': 'english_model_comparison_technical_analysis_v1', 'level': 'DEVELOPMENT_EXPLORATORY',
        'status': 'COMPLETE_200_OBSERVATIONS', 'attempts': 200, 'responses': 200, 'missing_outcomes': 0,
        'new_generation_retries': 0, 'human_labels_created': 0,
        'cumulative_generations': instr[1]['cumulative_generations'],
        'cumulative_inference_seconds': instr[1]['cumulative_inference_seconds'],
        'completion_inference_seconds': math.fsum(r[1]['completion_inference_seconds'] for r in runs.values()),
        'models': {v: {'execution': runs[v][1], 'technical_estimates': summarize(rows[v]),
                       'native_stop_type_counts': dict(Counter(r['response'].get('stop_type', 'UNREPORTED') for r in runs[v][3].values()))}
                   for v in runs}, 'paired_instruct_minus_base': summarize(paired),
        'bindings': {'base_receipt_sha256': base_sha, 'instruct_receipt_sha256': instruct_sha,
                     'protocol_and_artifacts': base[0]['bindings'],
                     'manifest_sha256': {v: runs[v][1]['manifest_sha256'] for v in runs},
                     'terminal_sha256': {v: runs[v][1]['terminal_event_sha256'] for v in runs},
                     'private_evidence_canonical_sha256': independent.value_hash(private)},
        'analysis_source_hashes': sources, 'semantic_endpoints': 'PENDING_NEW_GENUINE_HUMAN_REVIEW',
        'definitions': {'latency_seconds': 'Measured completion-call wall time, not CPU process time.',
            'native_prefill_seconds': 'Native timings.prompt_ms /1000; unavailable fields stay None.',
            'native_decode_seconds': 'Native timings.predicted_ms /1000; unavailable fields stay None.',
            'native_stop_word': 'Indicator stop_type exactly equals word; EOS, limit and all other returned stop types remain distinct.',
            'native_stop_strings': 'Unchanged returned stopping_word/flags preserved privately; no text trimming.',
            'factorial_scale': '2*mean(product of selected +/-1 factor codes * outcome), within context then equal context/speaker averaging.',
            'model_difference': 'Instruct minus Base on matched cells; factor differences use the identical complete-pair speaker policy.'},
        'implementation_timing': 'Analysis adapter implemented after execution registration and before inspecting new outputs; scientific protocol and reused arithmetic already frozen.',
        'archival_validation': 'Source HEAD remains recorded provenance; current HEAD is not an analysis gate. Current executable bytes, archived source/input snapshots, exact request reconstruction, model identities, native/HTTP evidence and predecessor costs remain verified. Execution guards are unchanged.',
        'limits': 'Published checkpoint+interface/EOS configurations, not isolated instruction-tuning or size effects. Model blocks are not randomized; cross-model timing is descriptive. Tokens/native stops/timings are not Persona Fidelity or semantic reliability. Native timing fields use direct unit conversion; existing raw measurements and all factorial/control arithmetic are cross-checked by distinct frozen functions. Speaker/LOO ranges are not confidence intervals; five developmental speakers share meeting/topic/partner dependence. Peak RAM is process-lifetime, not a condition effect. No independent new-speaker validation. Public clone-only reproduction PARTIAL.'}
    require(source_bindings() == sources, 'Analysis sources changed while computing')
    return report, private


def analyze(base_sha, instruct_sha, action):
    require(action in ('write', 'verify', 'prepare-review'), 'Unknown analysis action')
    public = OUT / 'technical_analysis_v1.json'; private_path = PRIVATE / 'analysis_private_v1.json'
    reproduction = OUT / 'independent_arithmetic_receipt_v1.json'
    if action == 'write':
        require(not any(p.exists() for p in (public, private_path, reproduction)), 'No overwrite of analytical evidence')
    report, private = calculate(base_sha, instruct_sha)
    if action == 'write':
        controller.old.write(private_path, private); controller.old.write(public, report)
        controller.old.write(reproduction, {'schema': 'english_model_comparison_independent_arithmetic_v1',
            'status': 'PASS', 'scope': 'ARITHMETIC_NOT_INDEPENDENT_EXPERIMENT_OR_REVIEW',
            'analysis_sha256': sha(public), 'private_file_sha256': sha(private_path),
            'bindings': report['bindings'], 'human_labels_created': 0})
    else:
        independent.compare(load(public), report, 'Reproduced public analysis')
        independent.compare(load(private_path), private, 'Reproduced private rows and unchanged review responses')
        reproduced = load(reproduction)
        require(reproduced['status'] == 'PASS' and reproduced['analysis_sha256'] == sha(public) and
                reproduced['private_file_sha256'] == sha(private_path) and reproduced['bindings'] == report['bindings'],
                'Independent arithmetic receipt binding')
    if action == 'prepare-review':
        analyst = PRIVATE / 'review'; directory = Path('.local/reviewer-packages/english_model_comparison_v1')
        wrapper = OUT / 'review_delivery_receipt_v1.json'; helper = analyst / 'package_receipt_v1.json'
        receipt = review.build_package(private['review_records'], directory, analyst / 'protected_mapping_v1.json',
            helper, wrapper, sealed_source_sha256=sha(private_path), dossiers_redacted=True)
        package = review.load_package(directory, helper, wrapper)
        blank = review.validate_submission(package, (directory / 'REVIEW.csv').read_bytes())
        require(not blank['errors'] and blank['counts']['not_started'] == 200, 'Review package must remain blank')
        return receipt
    return {'status': 'WRITTEN' if action == 'write' else 'REPRODUCTION_PASS',
            'analysis_sha256': sha(public), 'independent_receipt_sha256': sha(reproduction),
            'responses': 200, 'human_labels_created': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('write', 'verify', 'prepare-review'))
    parser.add_argument('--base-receipt-sha256', required=True)
    parser.add_argument('--instruct-receipt-sha256', required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.base_receipt_sha256, args.instruct_receipt_sha256, args.action), indent=2, allow_nan=False))
