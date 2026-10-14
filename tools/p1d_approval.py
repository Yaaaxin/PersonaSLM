"""Register explicit P1d plan approval after checking the pre-approval seal.

No execution authorization is created. Original approval objects are never edited.
"""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from p1d_design import read, sha, write

ROOT = Path(__file__).resolve().parents[1]
AUTH = Path('docs/validation/p1d/authorization_v1')
SEAL = Path('docs/validation/p1d/proposed_v1/reproducibility_manifest_v1.json')
PACKET = 'docs/P1d_researcher_decision_packet_v1.md'
ADDENDUM = 'docs/P1d_protocol_addendum_proposed.md'
EXPECTED = {
    PACKET: '2474ad11bd37622f8dcb00034f35c4d329a38c7a07704788274f90a349a7b882',
    ADDENDUM: '1ea81f56548d6685fc0eb67bdc291283f0867e73008f8fd7e26eea432bc30319',
}

def verify(root=ROOT):
    seal = read(root / SEAL)
    objects = {**seal['approval_objects'], **EXPECTED}
    for name, expected in objects.items():
        if seal['artifact_sha256'].get(name) != expected:
            raise ValueError('Pre-approval seal binding mismatch: ' + name)
        if sha(root / name) != expected:
            raise ValueError('Reviewed content changed: ' + name)
    return objects

def register(root=ROOT):
    target = root / AUTH / 'researcher_plan_approval_corrected_v1.json'
    if target.exists():
        raise FileExistsError(target)
    objects = verify(root)
    source = root / AUTH / 'researcher_fingerprint_confirmation_source_v1.txt'
    if not source.exists():
        raise ValueError('Actual explicit confirmation source is required')
    record = {
        'version': 'p1d_plan_approval_corrected_v1',
        'researcher_id': 'Yaxin_ZHENG',
        'review_status': 'RESEARCHER_CONFIRMED',
        'decision': 'APPROVED_WITH_SCIENTIFIC_LIMITATIONS',
        'decision_source': 'Explicit researcher approval and subsequent fingerprint correction in this conversation',
        'human_review_timestamp': None,
        'software_registered_utc': datetime.now(timezone.utc).isoformat(),
        'approved_addendum_version': 'p1d_addendum_proposed_v1',
        'scope': 'Prospective design adoption only; not stimulus validity certification or inference authorization',
        'approval_objects_sha256': objects,
        'previous_unregistered_record': {
            'path': (AUTH / 'received_approval_hash_check_v1.json').as_posix(),
            'sha256': sha(root / AUTH / 'received_approval_hash_check_v1.json'),
            'disposition': 'Preserved; erroneous fingerprint references superseded, not erased',
        },
        'correction_source': {'path': source.relative_to(root).as_posix(), 'sha256': sha(source)},
        'preapproval_seal_sha256': sha(root / SEAL),
        'proposed_targets': {'synthetic_speakers': 144, 'paired_cases': 288, 'base_requests': 1728, 'instruct_requests': 288},
        'authorized_inference_requests': 0,
        'execution_manifest': None,
        'limitations': [
            'S/F/H remains the core programme; P1d is a history-package sub-study',
            'Preserve the bound E/V source-selection definitions; do not relabel them pure R/T mechanisms',
            'Procedural controls remain diagnostic, not certified semantically neutral',
            'The 24-speaker Instruct subset is not a complete 144-speaker model factorial',
            'Budget, independent stimuli, controls, measurement and model readiness require validation before execution freeze',
            'Historical protocols, raw outputs and annotations remain unchanged',
            'No inference, training, commit, push or release is authorized',
        ],
        'assessment_provenance': 'AI-assisted prospective development; explicit human researcher adoption. No independent second-human review claimed.',
        'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    }
    write(target, record)
    return record

if __name__ == '__main__':
    result = register()
    print({'status': result['decision'], 'objects_verified': len(result['approval_objects_sha256']), 'authorized_inference_requests': 0})
