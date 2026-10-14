"""Seal the unconfirmed P1c semantic-review package, without unblinding ratings."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess

import p1c_semantic_review as a
import p1c_semantic_analysis as s
import p1c_semantic_verify as verify

DOCS = [Path('docs') / name for name in (
    'P1c_semantic_review_report_v1.md', 'P1c_structural_boundary_analysis_v1.md',
    'P1c_measurement_bias_assessment_v1.md', 'P1c_exploratory_analysis_readiness_v1.md',
    'P1c_algorithmic_opportunity_assessment_v2.md', 'P1c_next_validation_recommendation_v1.md',
    'related_work_novelty_matrix_monitor_v2.md')]


def closeout():
    destination = a.OUT / 'closeout_v1'
    a.require(not destination.exists(), 'Preserve previous closeout')
    identity = verify.verify()
    captured = a.read('results/p1c_semantic_review/v1/tests_full_02.json')
    a.require(captured['exit_code'] == 0 and '925 passed' in captured['stdout'], 'Complete suite evidence differs')
    sources = {r['anonymous_response_id']: r for r in a.rows(a.SOURCE)}
    inventories = {}
    for view, path in [('primary', s.PRIMARY), ('secondary', s.SECONDARY)]:
        proposals = a.read(path)
        a.require(len(proposals) == len({r['anonymous_response_id'] for r in proposals}) == 72, 'Proposal identities differ')
        for row in proposals:
            a.require(all(row[k] == v for k, v in sources[row['anonymous_response_id']].items()), 'Original field changed')
            a.require(a.text_sha(row['raw_first_reply']) == row['first_reply_sha256'], 'First-reply hash differs')
            a.require(all(v == '' for k, v in row.items() if k.startswith('human_')), 'Human annotation invented')
            s.validate_rating({k: row['AI_' + k] for k in a.FIELDS})
        inventories[view] = {k: dict(Counter('NULL_UNSCORABLE_OR_UNCERTAIN' if r['AI_' + k] is None else str(r['AI_' + k]) for r in proposals)) for k in a.FIELDS}
    a.require(inventories['primary']['factual_consistency'] == {'Correct': 43, 'Incorrect': 20, 'Unverifiable': 9}, 'Documentation factual summary differs')
    a.require(inventories['secondary']['factual_consistency'] == {'Correct': 47, 'Incorrect': 24, 'Unverifiable': 1}, 'Secondary factual summary differs')
    spec = a.read(s.PREP / 'analysis_specification_v1.json')
    a.require(spec['weights'] == a.read(s.REGISTRY)['weights'] and len(spec['weights']) == 16, 'Registered weights changed')
    a.require(len(a.rows(s.PREP / 'case_contrast_specifications_v1.csv')) == 192, 'Case contrast definitions differ')
    schema_counts = Counter()
    for path in a.OUT.rglob('*'):
        if path.suffix == '.json': a.read(path); schema_counts['json'] += 1
        elif path.suffix == '.csv':
            rows = a.rows(path)
            a.require(rows and all(None not in r and all(v is not None for v in r.values()) for r in rows), 'Invalid CSV: ' + str(path))
            schema_counts['csv'] += 1
    for doc in DOCS:
        for link in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if '://' not in link and not link.startswith('#'):
                a.require((doc.parent / link.split('#')[0]).exists(), 'Broken report link: ' + link)
    diff = subprocess.run(['git', 'diff', '--check'], capture_output=True, text=True)
    a.require(diff.returncode == 0, 'Git whitespace validation failed')
    code = list(Path('tools').glob('p1c_semantic_*.py')) + [Path('tools/p1c_boundary_review.py'), Path('tests/test_p1c_semantic_review.py')]
    artifacts = sorted(set([p for p in a.OUT.rglob('*') if p.is_file()] + DOCS + code))
    a.write(destination / 'verification_v1.json', {
        **identity, 'version': 'p1c_semantic_closeout_v1', 'artifact_hashes': {str(p): a.sha(p) for p in artifacts},
        'proposal_distributions': inventories, 'schema_files_verified': dict(schema_counts),
        'test_capture': 'results/p1c_semantic_review/v1/tests_full_02.json',
        'test_capture_sha256': a.sha('results/p1c_semantic_review/v1/tests_full_02.json'),
        'full_test_result': '925 passed in 38.12s', 'git_diff_check': 'PASS',
        'formal_semantic_effects_computed': False, 'actual_annotation_registration_executed': False,
        'scope': 'AI proposals and separately labeled boundary sensitivity; no human decisions or new inference.'})
    a.write(destination / 'annotation_provenance_manifest_v1.json', {
        'version': 'p1c_semantic_annotation_proposal_provenance_v1',
        'software_recorded_utc': datetime.now(timezone.utc).isoformat(),
        'maintainer': 'Yaxin ZHENG', 'annotation_origin': 'AI_assisted_condition_masked_review',
        'primary_snapshot': str(s.PRIMARY), 'primary_sha256': a.sha(s.PRIMARY),
        'secondary_snapshot': str(s.SECONDARY), 'secondary_sha256': a.sha(s.SECONDARY),
        'original_masked_source_sha256': a.sha(a.SOURCE), 'original_human_fields': 'PRESERVED_BLANK',
        'stage_a_frozen_before_stage_b': True, 'reviewer_independence': 'NOT_ESTABLISHED',
        'prior_knowledge': 'Prior participation in execution/design and aggregate observations; no perfect-blinding claim.',
        'reviewer_id': None, 'researcher_confirmation': None, 'human_review_timestamp': None,
        'analysis_implementation_sha256': a.sha('tools/p1c_semantic_analysis.py'),
        'paired_statistics_sha256': a.sha('tools/p1c_paired_statistics.py'),
        'analysis_specification_sha256': a.sha(s.PREP / 'analysis_specification_v1.json'),
        'verification_sha256': a.sha(destination / 'verification_v1.json'),
        'future_registration': 'Preserve proposals and record actual researcher adoption/corrections separately before treatment join.'})
    return {'status': 'PASS', 'records': 72, 'boundary_sensitivity_records': 8, 'tests': 925,
            'human_confirmations': 0, 'new_generations': 0, 'artifacts_bound': len(artifacts)}


if __name__ == '__main__':
    print(closeout())
