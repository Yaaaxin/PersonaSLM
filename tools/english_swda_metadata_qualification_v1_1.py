"""Correct unpadded calendar dates; preserve v1's parser failure and partition.

This correction precedes all target-content access. No cohorts are selected
from generation outcomes, and the deterministic speaker assignment is unchanged.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile

import english_swda_metadata_qualification_v1 as prior

PRIVATE = prior.PRIVATE.with_name('metadata_partition_v1_1.json')
PUBLIC = prior.PUBLIC.with_name('swda_metadata_qualification_v1_1.json')


def normalized_dates(conversations):
    result = {}
    for key, row in conversations.items():
        copied = dict(row)
        try:
            copied['talk_day'] = datetime.strptime(row['talk_day'], '%Y-%m-%d').date().isoformat()
        except (ValueError, TypeError):
            pass  # Unknown dates remain invalid, never inferred from record IDs.
        result[key] = copied
    return result


def main(write=False):
    if prior.digest(prior.SOURCE.read_bytes()) != prior.SOURCE_SHA:
        raise ValueError('Archive changed')
    with zipfile.ZipFile(prior.SOURCE) as archive:
        speakers = json.loads(archive.read('switchboard-corpus/speakers.json'))
        conversations = json.loads(archive.read('switchboard-corpus/conversations.json'))
    private, public = prior.qualify(speakers, normalized_dates(conversations))
    old_private = json.loads(prior.PRIVATE.read_text(encoding='utf-8'))
    assert old_private['assignments'] == private['assignments'], 'Speaker partition changed'
    private['source_archive_sha256'] = prior.SOURCE_SHA
    private_bytes = prior.encoded(private)
    public.update({
        'schema': 'personaslm_swda_metadata_qualification_v1_1',
        'correction': 'v1 incorrectly rejected992 valid unpadded YYYY-M-D dates; now uses explicit calendar strptime. Frozen v1 is preserved as software-error evidence, not missing-date evidence. No target content or generation was accessed before correction.',
        'source_archive_sha256': prior.SOURCE_SHA,
        'source_code_sha256': {p.name: prior.digest(p.read_bytes()) for p in (Path(__file__), Path(prior.__file__))},
        'prior_receipt_sha256': prior.digest(prior.PUBLIC.read_bytes()),
        'private_partition_sha256': prior.digest(private_bytes),
        'speaker_assignments_unchanged': True,
        'utterance_members_opened': 0,
        'original_transcript_members_opened': 0,
        'validation_target_content_inspected': False,
        'new_model_generations': 0,
        'boundary': 'Structural metadata eligibility only, not factual/semantic/ethical qualification or experiment registration.'
    })
    if write:
        if PRIVATE.exists() or PUBLIC.exists():
            raise FileExistsError('Correction already frozen')
        with PRIVATE.open('xb') as stream:
            stream.write(private_bytes)
        with PUBLIC.open('xb') as stream:
            stream.write(prior.encoded({**public, 'recorded_utc': datetime.now(timezone.utc).isoformat()}))
    else:
        frozen = json.loads(PUBLIC.read_text(encoding='utf-8'))
        frozen.pop('recorded_utc')
        assert frozen == public and PRIVATE.read_bytes() == private_bytes, 'Correction reproduction mismatch'
    print(json.dumps(public, indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    main(parser.parse_args().write)
