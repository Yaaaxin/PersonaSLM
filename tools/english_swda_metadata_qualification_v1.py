"""Metadata-only SwDA qualification; never open utterance or transcript content.

Local pseudonymous IDs stay private. This freezes a speaker partition, not
experimental cases, semantic labels, generation authorization or qualification
of all S/F/H constructs. Source archives remain unchanged.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.local/datasets/swda_english_v1/cornell_switchboard_unprocessed.zip'
SOURCE_SHA = 'c903ef6542a9838d23fe5cf00c4cfc4727ca54cadb55c61916f090498141c817'
PRIVATE = ROOT / '.local/datasets/swda_english_v1/metadata_partition_v1.json'
PUBLIC = ROOT / 'docs/validation/p1/english_real_speaker_stage_v1/swda_metadata_qualification_v1.json'
SALT = 'PersonaSLM-English-real-speaker-stage1-partition-v1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def partition(speaker):
    return 'development' if int(digest((SALT + ':' + speaker).encode())[:2], 16) < 128 else 'reserved'


def qualify(speakers, conversations):
    assignments = {str(speaker): partition(str(speaker)) for speaker in speakers}
    counts, days, partners = defaultdict(Counter), defaultdict(lambda: defaultdict(set)), defaultdict(lambda: defaultdict(set))
    excluded, date_failures, retained = 0, 0, {}
    for key, row in sorted(conversations.items()):
        a, b = str(row['from_caller']), str(row['to_caller'])
        if a not in assignments or b not in assignments or a == b:
            raise ValueError('Invalid metadata speaker association')
        try:
            date = datetime.fromisoformat(row['talk_day']).date().isoformat()
        except (ValueError, TypeError):
            date_failures += 1
            continue
        if assignments[a] != assignments[b]:
            excluded += 1
            continue
        group = assignments[a]
        retained[key] = {'split': group, 'date': date, 'a': a, 'b': b, 'filename': row['filename']}
        for person, other in ((a, b), (b, a)):
            counts[group][person] += 1
            days[group][person].add(date)
            partners[group][person].add(other)
    group_stats = {}
    for group in ('development', 'reserved'):
        members = [s for s, g in assignments.items() if g == group]
        # Four distinct dates are a structural screen for disjoint S/F/H source
        # conversations and later targets, not evidence that factual cases exist.
        eligible = [s for s in members if len(days[group][s]) >= 4 and len(partners[group][s]) >= 3]
        group_stats[group] = {
            'assigned_speakers': len(members),
            'within_split_conversations': sum(r['split'] == group for r in retained.values()),
            'speakers_with_at_least_two_dates': sum(len(days[group][s]) >= 2 for s in members),
            'speakers_with_four_dates_and_three_partners': len(eligible),
            'max_distinct_dates_per_speaker': max((len(days[group][s]) for s in members), default=0),
        }
    private = {'salt': SALT, 'assignments': assignments, 'retained_conversation_metadata': retained}
    public = {'speakers': len(assignments), 'conversations': len(conversations),
              'invalid_dates': date_failures, 'cross_split_conversations_excluded': excluded,
              'groups': group_stats}
    return private, public


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    raw = SOURCE.read_bytes()
    if digest(raw) != SOURCE_SHA:
        raise ValueError('Source archive hash differs')
    with zipfile.ZipFile(SOURCE) as archive:
        source_members = {name: archive.read('switchboard-corpus/' + name)
                          for name in ('speakers.json', 'conversations.json')}
    private, public = qualify(*(json.loads(source_members[name])
                                for name in ('speakers.json', 'conversations.json')))
    private['source_archive_sha256'] = SOURCE_SHA
    private_bytes = encoded(private)
    public.update({
        'schema': 'personaslm_swda_metadata_qualification_v1',
        'source_archive_sha256': SOURCE_SHA,
        'source_metadata_sha256': {name: digest(data) for name, data in source_members.items()},
        'source_code_sha256': digest(Path(__file__).read_bytes()),
        'private_partition_sha256': digest(private_bytes),
        'utterance_members_opened': 0,
        'original_transcript_members_opened': 0,
        'validation_target_content_inspected': False,
        'new_model_generations': 0,
        'boundary': 'Metadata structure only. Source speaker/date correctness, factual yield, privacy and generation endpoints are not yet validated. Partition is prospective before target-content access; no target cases selected.',
        'rules': 'SHA256 salt plus speaker ID, first byte<128 development, otherwise reserved; exclude every cross-split conversation. Four dates/three partners is a structural eligibility screen only.'
    })
    if args.write:
        if PRIVATE.exists() or PUBLIC.exists():
            raise FileExistsError('Frozen qualification already exists; use read-only reproduction')
        PUBLIC.parent.mkdir(parents=True, exist_ok=True)
        with PRIVATE.open('xb') as stream:
            stream.write(private_bytes)
        with PUBLIC.open('xb') as stream:
            stream.write(encoded({**public, 'recorded_utc': datetime.now(timezone.utc).isoformat()}))
    else:
        frozen = json.loads(PUBLIC.read_text(encoding='utf-8'))
        frozen.pop('recorded_utc')
        if frozen != public or PRIVATE.read_bytes() != private_bytes:
            raise ValueError('Metadata reproduction mismatch')
    print(json.dumps(public, indent=2))


if __name__ == '__main__':
    main()
