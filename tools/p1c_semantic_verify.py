"""Offline preservation verification for the P1c semantic proposal package."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import subprocess

import p1c_calibration as calibration
import p1c_decisions as decisions
import p1c_semantic_review as review


def verify():
    identity = decisions.verify_sources()
    original = review.read(review.ROOT / 'measurement_v1/execution_integrity_v1.json')
    reconstructed = calibration.audit()
    review.require(reconstructed == original, 'Original execution reconstruction changed')
    review.require(reconstructed == calibration.audit(), 'Repeated reconstruction differs')
    frozen = review.read(review.ROOT / 'measurement_v1/review_integrity_v1.json')
    for name, digest in frozen['files'].items():
        review.require(review.sha(review.ROOT / 'measurement_v1' / name) == digest, 'Original review changed: ' + name)
    baseline = review.read('results/p1c_semantic_review/v1/baseline.json')
    changes = [p for p, digest in baseline['files'].items() if review.sha(p) != digest]
    review.require(set(changes) <= {'docs/research_development_log.md'}, 'Existing source modified: ' + str(changes))
    old_log = Path('results/p1c_semantic_review/v1/development_log.before.md').read_bytes()
    review.require(Path('docs/research_development_log.md').read_bytes().startswith(old_log), 'Development log not append-only')
    protected = review.read('results/p1c_final_review/v1/baseline.json')['historical_artifacts']
    review.require(len(protected) == 5798, 'Historical preservation inventory missing')
    for name, digest in protected.items():
        review.require(review.sha(name) == digest, 'Historical experiment changed: ' + name)
    for stage, code in [('stage_a', 'tools/p1c_semantic_review.py'), ('stage_b', 'tools/p1c_boundary_review.py')]:
        manifest = review.read(review.OUT / stage / 'freeze_manifest_v1.json')
        for name, digest in manifest['files'].items():
            review.require(review.sha(review.OUT / stage / name) == digest, 'Proposal snapshot changed: ' + name)
        key = 'transcription_code_sha256' if stage == 'stage_a' else 'code_sha256'
        review.require(review.sha(code) == manifest[key], 'Frozen proposal code changed')
    applicability = review.read('docs/validation/p1c/final_review_v1/applicability_matrix_v1.json')
    review.require(len(applicability) == 72 and len({(r['case_id'], r['condition']) for r in applicability}) == 72,
                   'Applicability identity differs')
    counts = {k: sum(row[k] for row in applicability) for k in (*review.FIELDS, 'structural_status', 'persona_fidelity')}
    review.require(all(counts[k] == 72 for k in review.FIELDS) and counts['persona_fidelity'] == 0, 'Applicability differs')
    statuses = Counter(r['result']['response_status']['status'] for r in reconstructed['rows'])
    return {'version': 'p1c_semantic_preservation_verification_v1', 'status': 'PASS',
            'verified_utc': datetime.now(timezone.utc).isoformat(), 'source_identity': identity,
            'execution_reconstructed_twice': True, 'raw_http_response_bytes_verified': reconstructed['http_response_bytes_verified'],
            'original_run_event_files': sum(len(s['events']) for s in reconstructed['segments']),
            'frozen_structure': dict(statuses), 'historical_experiment_files': len(protected),
            'entry_tracked_files': len(baseline['files']), 'allowed_append_only_changes': changes,
            'review_source_files_unchanged': len(frozen['files']), 'applicability_counts': counts,
            'frozen_manifest_sha256': decisions.MANIFEST_SHA, 'actual_binary_identity_verified': True,
            'new_inference_requests': 0, 'human_semantic_confirmations': 0,
            'formal_semantic_condition_effects': 0,
            'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'git_status': subprocess.check_output(['git', 'status', '--short'], text=True)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify()
    review.write(args.output, result)
    print({k: v for k, v in result.items() if k != 'git_status'})
