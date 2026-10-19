"""Recover an ID-keyed human review into the frozen CSV without changing labels."""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

import english_sfh_review_v1 as review

INPUT_FIELDS = ('review_id',) + review.EDITABLE
FROZEN_SOURCES = {
    'english_sfh_review_v1': '01b29ccb9686f8e9fd65408338da6d99bfc4397f9665aa402c10d9c807b615bd',
    'p1_persona_dialogue_disjoint_surface_validation_review_v4': '14883c1b5f4883339512d228c94adb05a9e7847a6951dd0d667b948bd7a0b1a2',
    'real_persona_chat_sfh_review_v1': 'fb26593c1ae9d4e6e80f30c6ec6e287b53b9b148728ffa353a294fb8443a53e5',
}
RUBRIC_SHA = '2c6331e2b076c3b0903170cc159823dcee01d28fc1848b78fa4f887a8388cb14'
UNCERTAINTY_REASON = ('The principal researcher stated that blank entries represent uncertainty about how to answer. '
                      'No judgments were supplied for this record.')


def require(value, message):
    if not value:
        raise ValueError(message)


def sha_bytes(content):
    return hashlib.sha256(content).hexdigest()


def parse_rows(content, assigned_ids):
    reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig'), newline=''), strict=True)
    require(reader.fieldnames == list(INPUT_FIELDS), 'Exact review_id plus editable-field header/order required')
    rows = list(reader)
    require(rows and all(None not in row and None not in row.values() for row in rows), 'Missing or extra CSV cells')
    ids = [row['review_id'] for row in rows]
    require(len(set(ids)) == len(ids), 'Duplicate blinded IDs; no automatic choice between judgments')
    require(set(ids) <= assigned_ids, 'Unknown blinded ID; do not guess a record match')
    for row in rows:
        require(all(not row[field].lstrip().startswith(('=', '+', '-', '@')) for field in review.EDITABLE),
                'Formula-like editable cell rejected; original bytes remain unchanged')
    return rows


def derive_uncertainty(recovered, declaration, submission_sha256):
    require(isinstance(declaration, dict)
            and declaration.get('schema') == 'english_sfh_blank_uncertainty_declaration_v1'
            and declaration.get('received_submission_sha256') == submission_sha256
            and declaration.get('blank_entries_mean_uncertainty') is True
            and declaration.get('author') == 'PRINCIPAL_RESEARCHER',
            'Uncertainty declaration must bind this submission and the principal researcher statement')
    derived, changed = [dict(row) for row in recovered], []
    for number, row in enumerate(derived, 1):
        if all(row[field] == '' for field in review.EDITABLE):
            row['annotation_status'] = 'UNAVAILABLE'
            row['missing_reason'] = UNCERTAINTY_REASON
            changed.append({'delivery_ordinal': number, 'review_id': row['review_id']})
    return derived, changed


def recover(delivery, receipt, receipt_sha256, submission, submission_sha256, output,
            uncertainty_declaration=None, uncertainty_declaration_sha256=None):
    require((uncertainty_declaration is None) == (uncertainty_declaration_sha256 is None),
            'Uncertainty declaration path and SHA-256 must be provided together')
    delivery, receipt, submission, output = map(review.private_path, (delivery, receipt, submission, output))
    require(not output.exists() and delivery != output and delivery not in output.parents,
            'New separate private recovery directory required; no overwrite or delivery edits')
    content = submission.read_bytes()
    require(sha_bytes(content) == submission_sha256, 'Received submission SHA-256 mismatch')
    require(sha_bytes(receipt.read_bytes()) == receipt_sha256, 'Package receipt SHA-256 mismatch')
    for module, expected in FROZEN_SOURCES.items():
        require(sha_bytes(Path(sys.modules[module].__file__).read_bytes()) == expected, 'Frozen review helper changed')
    require(sha_bytes(review.RUBRIC.read_bytes()) == RUBRIC_SHA, 'Frozen rubric changed')
    package = review.load_package(delivery, receipt)
    require(len(package['rows']) == 100, 'Frozen English package must retain exactly100 records')
    assigned = {row['review_id'] for row in package['rows']}
    submitted = parse_rows(content, assigned)
    by_id = {row['review_id']: row for row in submitted}
    recovered, missing = [], []
    for number, record in enumerate(package['rows'], 1):
        human = by_id.get(record['review_id'])
        recovered.append({**review.csv_display(record),
                          **{field: human[field] if human else '' for field in review.EDITABLE}})
        if human is None:
            missing.append({'delivery_ordinal': number, 'review_id': record['review_id']})
    require(all(row[field] == by_id[row['review_id']][field] for row in recovered if row['review_id'] in by_id
                for field in review.EDITABLE), 'Human value preservation failed')
    draft = review.encode_csv(recovered, review.FIELDS)
    feedback = review.validate_submission(package, draft, final=False)
    errors = Counter(item['message'] for item in feedback['errors'])
    warnings = Counter(item['message'] for item in feedback['warnings'])
    manifest = {'schema': 'english_sfh_lossless_human_review_recovery_v1',
                'status': 'RECOVERED_DRAFT_NOT_FINALIZED_NOT_UNBLINDED',
                'received_submission_sha256': submission_sha256, 'package_receipt_sha256': receipt_sha256,
                'recovery_source_sha256': sha_bytes(Path(__file__).read_bytes()),
                'frozen_sources': FROZEN_SOURCES, 'rubric_sha256': RUBRIC_SHA,
                'submitted_rows': len(submitted), 'recovered_rows': len(recovered),
                'missing_rows': missing, 'all_submitted_editable_values_preserved_exactly': True,
                'human_labels_created_or_changed': 0, 'protected_mapping_opened': False,
                'condition_unblinding_performed': False, 'provenance_attestations_created': 0,
                'error_count': len(feedback['errors']), 'warning_count': len(feedback['warnings']),
                'rows_with_errors': len({item['row'] for item in feedback['errors'] if 'row' in item}),
                'errors_by_message': dict(errors), 'warnings_by_message': dict(warnings),
                'recovered_csv_sha256': sha_bytes(draft),
                'submitted_editable_values_sha256': sha_bytes(review.json_bytes(submitted)),
                'limits': 'Structural recovery only. Invalid values remain invalid and unchanged. The researcher stated the judgments were manually blinded; this operation neither disputes that statement nor supplies additional provenance. No scores are rescaled, normalized or inferred.'}
    checklist = [
        'PRIVATE HUMAN-REVIEW CORRECTIONS — NOT A NEW RUBRIC', '',
        'The received original is archived byte-for-byte. All submitted editable values are unchanged.',
        'The three missing immutable columns and fixed100-record order were restored by blinded ID only.',
        'Copy RECOVERED_DRAFT.csv to a new local working file before making genuine human corrections.',
        'Do not edit the first four immutable columns. Do not open the protected condition mapping.',
        'Frozen rubric: ' + str(review.RUBRIC), '',
        'Required actions under the existing rubric:',
        '- For each existing rating outside0,1,2,3,NA, record the intended judgment using the frozen anchors.',
        '  There is no automatic4/5-to0–3 conversion; the original numerical values remain archived.',
        '- annotation_status must be COMPLETED or UNAVAILABLE. Only the reviewer may decide unavailability.',
        '- Applicability uses APPLICABLE, NOT_APPLICABLE or UNCERTAIN; applicable ratings use0–3, otherwise NA.',
        '- confidence uses LOW, MEDIUM or HIGH; no automatic conversion of other values.',
        '- claim_evidence_json must be an object with a claims array, exact response/reference spans and reasons.',
        '  Its counts must match the entries. Use {"claims": []} only when that is the actual human judgment.',
        '- Complete each absent record below, or personally mark UNAVAILABLE with a truthful reason.',
        '  Missing rows have been left entirely blank in editable fields, never zero or unavailable by default.',
        '- Preserve the genuine manual-blind-review statement. Supply only still-missing factual provenance',
        '  details separately; this recovery has not supplied dates, exposure, translation or independence attestations.',
        '- Run the unchanged draft validator while saving. Final validation and review lock are separate actions.', '',
        'Missing submitted records (blinded IDs only):',
    ]
    checklist += [f"- Delivery record{row['delivery_ordinal']}: {row['review_id']}" for row in missing] or ['- None.']
    checklist += ['', 'Frozen validator errors (counts; no automatic repairs):']
    checklist += [f'- {message}: {count}' for message, count in sorted(errors.items())] or ['- None.']
    checklist += ['', 'See validation_feedback.json for individual blinded records. This draft is not a final submission.']
    extra = {}
    if uncertainty_declaration is not None:
        declaration_bytes = review.private_path(uncertainty_declaration).read_bytes()
        require(sha_bytes(declaration_bytes) == uncertainty_declaration_sha256,
                'Uncertainty declaration SHA-256 mismatch')
        derived, changed = derive_uncertainty(recovered, json.loads(declaration_bytes), submission_sha256)
        uncertainty_draft = review.encode_csv(derived, review.FIELDS)
        uncertainty_feedback = review.validate_submission(package, uncertainty_draft, final=False)
        extra = {'UNCERTAINTY_DRAFT.csv': uncertainty_draft,
                 'uncertainty_validation_feedback.json': review.json_bytes(uncertainty_feedback),
                 'uncertainty_declaration_original.json': declaration_bytes}
        manifest['uncertainty_derivation'] = {
            'declaration_sha256': uncertainty_declaration_sha256,
            'csv_file': 'UNCERTAINTY_DRAFT.csv', 'csv_sha256': sha_bytes(uncertainty_draft),
            'feedback_file': 'uncertainty_validation_feedback.json',
            'feedback_sha256': sha_bytes(extra['uncertainty_validation_feedback.json']),
            'unavailability_metadata_applied_to_wholly_blank_records': changed,
            'judgment_values_created_or_changed': 0,
            'error_count': len(uncertainty_feedback['errors']),
            'warning_count': len(uncertainty_feedback['warnings'])}
        checklist += ['', 'Separate declaration-backed UNCERTAINTY_DRAFT.csv:',
                      'Only wholly blank records were marked UNAVAILABLE with the principal researcher uncertainty statement.',
                      'No scores, evidence, existing values or other provenance were filled. RECOVERED_DRAFT.csv remains lossless.',
                      'See uncertainty_validation_feedback.json; this separate draft is not finalized or unblinded.']
    output.mkdir(parents=True, exist_ok=False)
    for name, value in {'received_original.txt': content, 'RECOVERED_DRAFT.csv': draft,
                        'validation_feedback.json': review.json_bytes(feedback),
                        'recovery_manifest.json': review.json_bytes(manifest),
                        'CORRECTIONS.txt': ('\n'.join(checklist) + '\n').encode('utf-8'), **extra}.items():
        review.prior.write_exclusive(output / name, value)
    return {'status': manifest['status'], 'submitted_rows': len(submitted), 'recovered_rows': len(recovered),
            'missing_rows': len(missing), 'error_count': len(feedback['errors']),
            'warning_count': len(feedback['warnings']), 'human_labels_created_or_changed': 0,
            'uncertainty_records_marked_unavailable': len(changed) if extra else 0,
            'recovered_csv_sha256': sha_bytes(draft), 'manifest_sha256': sha_bytes((output / 'recovery_manifest.json').read_bytes())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('delivery', 'receipt', 'submission', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--receipt-sha256', required=True)
    parser.add_argument('--submission-sha256', required=True)
    parser.add_argument('--uncertainty-declaration', type=Path)
    parser.add_argument('--uncertainty-declaration-sha256')
    args = parser.parse_args()
    print(json.dumps(recover(args.delivery, args.receipt, args.receipt_sha256,
                             args.submission, args.submission_sha256, args.output,
                             args.uncertainty_declaration, args.uncertainty_declaration_sha256), sort_keys=True))
