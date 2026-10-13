"""Offline wave-1 preservation and measurement-coverage audit; no inference."""
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path

from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.p1 import validate_dataset
from personaslm.response_status import text_hash
from personaslm.scientific_closure import reconcile_tokenizations
from p1_wave import check_sources

ROOT = Path.cwd().resolve()
PUBLIC = Path('docs/validation/p1')
SESSION = Path('results/p1_wave1/development_v1')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_inventory(directory, inventory):
    directory = Path(directory).resolve()
    if not directory.is_relative_to(ROOT):
        raise ValueError('Inventory is outside the research workspace')
    for name, expected in inventory.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid inventory member')
        actual = directory / relative
        if not actual.is_file() or digest(actual) != expected:
            raise ValueError('Historical file changed: ' + actual.relative_to(ROOT).as_posix())
    observed = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
    if observed != set(inventory):
        raise ValueError('Historical journal file inventory changed')
    return len(inventory)


def main():
    started = utc_now()
    if (PUBLIC / 'verification_v1.json').exists() or (PUBLIC / 'measurement_coverage_diagnostic_v1.json').exists():
        raise FileExistsError('Preserve the previous audit; use a new version for another audit')
    design = read(PUBLIC / 'wave1_design_v1.json')
    manifest = read(PUBLIC / 'wave1_manifest_v1.json')
    analysis = read(PUBLIC / 'wave1_analysis_v1.json')
    matching = read(PUBLIC / 'control_matching_v1.json')
    dataset = read('data/synthetic/p1_development_v1.json')
    cases = {r['case_id']: r for r in dataset['cases']}
    rows = read(PUBLIC / 'wave1_results_v1.json')['rows']
    check_sources(design)
    assert digest('docs/P1_experiment_plan.md') == design['experiment_plan_sha256']
    assert digest('docs/research_protocol_v1.1.md') == design['protocol_sha256']
    assert validate_dataset(dataset) == design['manipulation_validation']
    assert digest(design['configuration']['model_file']) == design['model_sha256']
    assert digest(design['configuration']['server_file']) == design['backend_sha256']

    # Compare byte identities against already audited P0 inventories, without editing or rerunning them.
    inventory_source = Path('results/p0_final_control_review/20261012T205559/materials/baseline.json')
    historical = read(inventory_source)['journals']
    closure = read('docs/validation/P0_control_closure_delivery_v1.json')['new_journal']
    final = read('docs/validation/P0_final_scientific_delivery_v1.json')['new_tessa_journal']
    historical[closure['path']] = closure['files']
    historical[final['run_directory']] = final['files']
    preserved = [{'directory': name, 'unchanged_files': verify_inventory(name, files)} for name, files in historical.items()]
    baseline = read(SESSION / 'materials/baseline.json')
    allowed = {'.gitignore', 'README.md', 'docs/research_development_log.md',
               'docs/related_work_novelty_matrix.md', 'docs/P1_experimental_design_proposal.md'}
    protected = {name: h for name, h in baseline['files'].items() if name not in allowed}
    assert all(digest(name) == h for name, h in protected.items()), 'Protected baseline file changed'

    tokenizer_directory = Path(matching['run_directory'])
    tokenizer_events = read_events(tokenizer_directory)
    expected = [(r['prompt']['text'], r['input_token_ids']) for r in manifest['requests']]
    expected += [(a['prompt']['text'], a['token_ids']) for r in matching['results'] for a in r['attempts']]
    native_count = reconcile_tokenizations(tokenizer_events, expected)
    assert len(matching['results']) == 24
    for match in matching['results']:
        selected = match['selected']
        assert selected and selected['difference'] == 0
        assert selected['token_count'] == match['reference_tokens'] == len(selected['token_ids'])
        assert text_hash(selected['prompt']['text']) == selected['prompt_sha256']
        assert selected == next(a for a in match['attempts'] if a['difference'] == 0)
        case = cases[match['case_id']]
        assert case['trusted_evidence'] in selected['prompt']['text']
        assert case['question'] in selected['prompt']['text']
        assert all(context in selected['prompt']['text'] for context in case['context'])
        assert case['expected_answer'] is None or case['expected_answer'].casefold() not in selected['text'].casefold()
    for audited in analysis['run_audits']:
        verify_inventory(audited['run_directory'], audited['file_hashes'])
    assert len(rows) == len({r['request_id'] for r in rows}) == 96

    # Post-output descriptive string inventory, explicitly not a new evaluator or human review.
    scope_rows = []
    for row in rows:
        if row['family'] not in 'AD':
            continue
        case = cases[row['case_id']]
        current = next(f for f in case['facts'] if f['fact_id'].endswith('_current_city'))
        prefix = f"{case['speaker_name']} currently lives in {case['expected_answer']}"
        simple = prefix + '.'
        dated = prefix + f", valid from {current['valid_from']} onward."
        actual = row['parsed_response'].strip()
        category = 'exact_current_city_sentence' if actual == simple else (
            'exact_current_city_sentence_with_source_validity_suffix' if actual == dated else 'other_text')
        scope_rows.append({'request_id': row['request_id'], 'original_factual_label': row['evaluation']['factual_support']['label'],
                           'first_reply_verbatim': row['parsed_response'], 'first_reply_sha256': text_hash(row['parsed_response']),
                           'current_source_fact': current, 'trusted_evidence': case['trusted_evidence'],
                           'expected_answer': case['expected_answer'], 'observed_string_form': category,
                           'replacement_score': None, 'human_judgment': None})
    coverage = {'version': 'p1_measurement_coverage_diagnostic_v1', 'created_utc': utc_now(),
                'source_results_sha256': digest(PUBLIC / 'wave1_results_v1.json'),
                'analysis_scope': 'Post-output lexical coverage diagnostic only; frozen scores and eligibility remain unchanged',
                'human_review': 'PENDING', 'new_evaluation_version': False,
                'counts': dict(Counter(r['observed_string_form'] for r in scope_rows)), 'rows': scope_rows,
                'visible_think_markers': [{'request_id': r['request_id'], 'family': r['family'],
                    'opening_marker_count': r['raw_response'].count('<think>'),
                    'closing_marker_count': r['raw_response'].count('</think>'),
                    'raw_sha256': text_hash(r['raw_response']), 'original_status': r['evaluation']['response_completeness']['status']}
                    for r in rows if '<think>' in r['raw_response']],
                'interpretation': 'City grammar coverage depends on suffix form. Do not interpret category transitions as semantic accuracy effects. Visible model-produced deliberation remains raw output, not a completed answer or a verified internal mechanism.'}
    atomic_json(PUBLIC / 'measurement_coverage_diagnostic_v1.json', coverage)

    csv_counts = {}
    for name in ['control_review_v1.csv', 'output_review_v1.csv']:
        with (PUBLIC / name).open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream); material = list(reader)
        assert len(reader.fieldnames) == len(set(reader.fieldnames))
        assert all(None not in r and all(v is not None for v in r.values()) for r in material)
        assert all(not r['reviewer_id'] and not r['reviewed_utc'] for r in material)
        csv_counts[name] = len(material)
    assert csv_counts == {'control_review_v1.csv': 24, 'output_review_v1.csv': 96}
    test = read(SESSION / 'engineering/final_tests.json')
    assert test['exit_code'] == 0 and '401 passed' in test['stdout']
    generation_logs = {}
    for audited in analysis['run_audits']:
        lines = (Path(audited['run_directory']) / 'server.log').read_text(encoding='utf-8', errors='replace').splitlines()
        import re
        generation_logs[audited['run_directory']] = [line for line in lines if re.search(
            r'n_threads|n_ctx\s|offload|build:|model (arch|type|size)|general\.(architecture|name)|tokenizer\.ggml\.model|available.*memory', line, re.I)]
    result = {'version': 'p1_wave1_verification_v1', 'started_utc': started, 'verified_utc': utc_now(),
              'historical_P0_journals': preserved, 'historical_P0_unchanged_files': sum(r['unchanged_files'] for r in preserved),
              'historical_chain_provenance': 'Prior chain audits remain bound by identical journal bytes; no new P0 inference',
              'protected_baseline_files': len(protected), 'frozen_source_dataset_config_plan_protocol_unchanged': True,
              'model_sha256': design['model_sha256'], 'backend_sha256': design['backend_sha256'],
              'native_tokenizer_preparation_requests_reconciled': native_count,
              'native_generation_inputs_reconciled': sum(r['native_inputs_reconstructed'] for r in analysis['run_audits']),
              'generated_responses_reconstructed_twice': analysis['completed_results'],
              'actual_output_token_ids_returned': sum(r['token_ids_status'] == 'returned' for r in rows),
              'returned_evaluated_input_ids': sum(r['token_audit']['returned_ids_match'] is not None for r in rows),
              'input_count_checks_passed': sum(r['token_audit']['count_matches'] and not r['token_audit']['truncated'] for r in rows),
              'backend_input_id_limitation': 'Native tokenizer IDs equal submitted IDs and evaluated counts. Backend does not echo evaluated input IDs; no invented array equality.',
              'all_first_spans_identifiable': all(r['evaluation']['response_completeness']['unit_identifiable'] for r in rows),
              'semantic_completeness_independently_reviewed': 0, 'exact_new_controls': len(matching['results']),
              'human_control_reviews': 0, 'csv_counts': csv_counts, 'tests': test,
              'observed_server_lines': generation_logs,
              'input_token_range': [min(r['input_tokens'] for r in rows), max(r['input_tokens'] for r in rows)],
              'public_artifact_hashes_before_verification': {p.as_posix(): digest(p) for p in PUBLIC.glob('*') if p.is_file()},
              'audit_source_sha256': digest(__file__), 'additional_generation_requests': 0}
    atomic_json(PUBLIC / 'verification_v1.json', result)
    print(json.dumps({'status': 'PASS', 'P0_journals': len(preserved), 'P0_files_unchanged': result['historical_P0_unchanged_files'],
                      'native_preparation_tokenizations': native_count, 'coverage_forms': coverage['counts'],
                      'visible_think_markers': len(coverage['visible_think_markers']), 'tests': '401 passed'}))


if __name__ == '__main__':
    main()
