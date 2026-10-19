"""Authored reviews only; no real human values or protected mappings are read."""
from pathlib import Path

import pytest

import english_sfh_review_recover_v1 as recovery


@pytest.fixture
def authored(tmp_path, monkeypatch):
    review = recovery.review
    monkeypatch.setattr(review, 'PRIVATE_ROOT', tmp_path)
    delivery, receipt, mapping = tmp_path / 'delivery', tmp_path / 'analyst/receipt.json', tmp_path / 'analyst/protected_mapping.json'
    records = [{'request_id': f'authored_{i}', 'case_id': f'authored_case_{i//10}',
                'dossier': f'An entirely authored context{i//10}.', 'response': 'An entirely authored response.'}
               for i in range(100)]
    review.build_package(records, delivery, mapping, receipt, sealed_source_sha256='a' * 64, dossiers_redacted=True)
    package = review.load_package(delivery, receipt)
    rows = []
    for index, record in enumerate(package['rows']):
        if index == 31:
            continue
        row = {'review_id': record['review_id'], **dict.fromkeys(review.EDITABLE, '')}
        row.update(annotation_status='yes', relevance=str((index + 5) % 6), coherence='4', linguistic_resemblance='3',
                   confidence='high', rationale='  Authored comment, preserved exactly.\nSecond authored line.  ',
                   claim_evidence_json='[]', history_applicability='yes', history_rating='5')
        rows.append(row)
    content = review.encode_csv(rows, recovery.INPUT_FIELDS)
    submission = tmp_path / 'received.txt'
    submission.write_bytes(content)
    return delivery, receipt, mapping, package, rows, submission, tmp_path / 'recovery'


def call(fixture):
    delivery, receipt, _, _, _, submission, output = fixture
    return recovery.recover(delivery, receipt, recovery.sha_bytes(receipt.read_bytes()),
                            submission, recovery.sha_bytes(submission.read_bytes()), output)


def test_exact_human_values_and_one_blank_record_preserved_without_mapping_io(authored, monkeypatch):
    delivery, receipt, mapping, package, human, submission, output = authored
    original_read = Path.read_bytes

    def no_mapping(path):
        if path.resolve() == mapping.resolve():
            pytest.fail('Protected mapping opened')
        return original_read(path)

    monkeypatch.setattr(Path, 'read_bytes', no_mapping)
    result = call(authored)
    assert result['submitted_rows'] == 99 and result['recovered_rows'] == 100 and result['missing_rows'] == 1
    assert result['human_labels_created_or_changed'] == 0 and result['error_count'] > 0
    assert (output / 'received_original.txt').read_bytes() == submission.read_bytes()
    recovered = recovery.review.decode_csv((output / 'RECOVERED_DRAFT.csv').read_bytes())
    assert [row['review_id'] for row in recovered] == [row['review_id'] for row in package['rows']]
    before = {row['review_id']: row for row in human}
    for row in recovered:
        if row['review_id'] in before:
            assert all(row[field] == before[row['review_id']][field] for field in recovery.review.EDITABLE)
        else:
            assert all(row[field] == '' for field in recovery.review.EDITABLE)
    assert recovered[0]['relevance'] == '5' and recovered[0]['annotation_status'] == 'yes'
    assert {row['relevance'] for row in recovered if row['review_id'] in before} == set('012345')
    assert recovered[0]['confidence'] == 'high' and recovered[0]['claim_evidence_json'] == '[]'
    assert not (output / 'protected_mapping.json').exists()
    with pytest.raises(ValueError, match='no overwrite'):
        call(authored)


@pytest.mark.parametrize('problem', ['duplicate', 'unknown', 'extra_header'])
def test_ambiguous_or_nonexact_input_rejected(authored, problem):
    _, _, _, package, rows, _, _ = authored
    fields = recovery.INPUT_FIELDS
    if problem == 'duplicate':
        rows.append(dict(rows[0]))
    elif problem == 'unknown':
        rows[0]['review_id'] = 'not-an-assigned-blinded-id'
    else:
        fields = fields + ('unexpected',)
    data = recovery.review.encode_csv(rows, fields)
    with pytest.raises(ValueError, match='Duplicate|Unknown|header'):
        recovery.parse_rows(data, {row['review_id'] for row in package['rows']})


@pytest.mark.parametrize('formula', ['=1+1', '  +SUM(A1:A2)', '\t@call()', '-1+2'])
def test_formula_like_editable_values_are_not_silently_rewritten(authored, formula):
    _, _, _, package, rows, _, _ = authored
    rows[0]['rationale'] = formula
    data = recovery.review.encode_csv(rows, recovery.INPUT_FIELDS)
    with pytest.raises(ValueError, match='Formula-like'):
        recovery.parse_rows(data, {row['review_id'] for row in package['rows']})


@pytest.mark.parametrize('which', ['submission', 'receipt'])
def test_hash_mismatch_creates_no_recovery(authored, which):
    delivery, receipt, _, _, _, submission, output = authored
    receipt_sha, submission_sha = recovery.sha_bytes(receipt.read_bytes()), recovery.sha_bytes(submission.read_bytes())
    if which == 'submission':
        submission_sha = '0' * 64
    else:
        receipt_sha = '0' * 64
    with pytest.raises(ValueError, match='SHA-256 mismatch'):
        recovery.recover(delivery, receipt, receipt_sha, submission, submission_sha, output)
    assert not output.exists()


def uncertainty_statement(submission_sha):
    return {'schema': 'english_sfh_blank_uncertainty_declaration_v1',
            'received_submission_sha256': submission_sha,
            'blank_entries_mean_uncertainty': True, 'author': 'PRINCIPAL_RESEARCHER',
            'exact_statement': 'Authored fixture declaration, not a real researcher statement.'}


def test_uncertainty_is_separate_and_changes_only_wholly_blank_record(authored):
    delivery, receipt, _, package, human, submission, output = authored
    submission_sha = recovery.sha_bytes(submission.read_bytes())
    declaration = output.parent / 'authored_declaration.json'
    declaration.write_bytes(recovery.review.json_bytes(uncertainty_statement(submission_sha)))
    result = recovery.recover(delivery, receipt, recovery.sha_bytes(receipt.read_bytes()),
                              submission, submission_sha, output, declaration,
                              recovery.sha_bytes(declaration.read_bytes()))
    lossless = recovery.review.decode_csv((output / 'RECOVERED_DRAFT.csv').read_bytes())
    derived_bytes = (output / 'UNCERTAINTY_DRAFT.csv').read_bytes()
    derived = recovery.review.decode_csv(derived_bytes)
    assert result['uncertainty_records_marked_unavailable'] == 1
    assert all(lossless[31][field] == '' for field in recovery.review.EDITABLE)
    assert derived[31]['annotation_status'] == 'UNAVAILABLE'
    assert derived[31]['missing_reason'] == recovery.UNCERTAINTY_REASON
    assert all(derived[31][field] == '' for field in recovery.review.JUDGMENTS)
    assert all(before == after for index, (before, after) in enumerate(zip(lossless, derived)) if index != 31)
    assert all(derived[index]['missing_reason'] == '' for index in range(100) if index != 31)
    assert (output / 'uncertainty_declaration_original.json').read_bytes() == declaration.read_bytes()
    feedback = recovery.review.validate_submission(package, derived_bytes, final=False)
    assert feedback['counts']['unavailable'] == 1 and feedback['counts']['completed'] == 0
    before = [dict(row) for row in lossless]
    recovery.derive_uncertainty(lossless, uncertainty_statement(submission_sha), submission_sha)
    assert lossless == before


@pytest.mark.parametrize('key,value', [('schema', 'wrong'), ('author', 'OTHER'),
                                       ('received_submission_sha256', 'wrong'),
                                       ('blank_entries_mean_uncertainty', 'true')])
def test_uncertainty_requires_matching_explicit_declaration(key, value):
    declaration = uncertainty_statement('a' * 64)
    declaration[key] = value
    with pytest.raises(ValueError, match='declaration must bind'):
        recovery.derive_uncertainty([], declaration, 'a' * 64)


def test_uncertainty_option_pair_and_hash_are_required_before_writing(authored):
    delivery, receipt, _, _, _, submission, output = authored
    arguments = (delivery, receipt, recovery.sha_bytes(receipt.read_bytes()),
                 submission, recovery.sha_bytes(submission.read_bytes()), output)
    with pytest.raises(ValueError, match='provided together'):
        recovery.recover(*arguments, uncertainty_declaration=submission)
    with pytest.raises(ValueError, match='provided together'):
        recovery.recover(*arguments, uncertainty_declaration_sha256='0' * 64)
    with pytest.raises(ValueError, match='declaration SHA-256 mismatch'):
        recovery.recover(*arguments, uncertainty_declaration=submission, uncertainty_declaration_sha256='0' * 64)
    assert not output.exists()
