"""AMI stage-one source retrieval only: no target selection, curation or inference."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

import english_icsi_material_v1 as v1
import english_icsi_material_v2 as v2
import english_icsi_material_v3 as v3

POLICY = Path('docs/validation/p1/english_real_speaker_stage_v2/ami_source_qualification_policy_v1.json')
POLICY_SHA = '63b55a97517a3d581f3bb425041668dabd5edcc8142eaf504dc4e154342e3f6f'
PRIVATE = Path('.local/experiments/english_sfh_v2/ami_source_pool_v1.json')
PUBLIC = POLICY.with_name('ami_source_pool_receipt_v1.json')
NITE = '{http://nite.sourceforge.net/}'
SALT = 'PersonaSLM-AMI-source-v1:'
FROZEN_HELPERS = {
    'english_icsi_material_v1.py': '46dd226e8f4ef2614b5a4f2899fc3e4916572dba4dfab164388fee6b5706e512',
    'english_icsi_material_v2.py': 'ec7e769900cef6d9b3786cb93c01309454c0bdc1bad03cd171f3a759253b5058',
    'english_icsi_material_v3.py': 'd7c8ff997838dd50cc4a57a51ec9244e14d38803bc3b9e9cab5a9465f55b0ced',
    'icsi_english_qualification_v1.py': '9d0b6141510ab65f2178a207f2c52fa538c707022b382090da0605bc60f54c83'}


def require(value, message):
    if not value:
        raise ValueError(message)


def hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


def candidate_hash(identity):
    return hash_bytes((SALT + identity).encode('ascii'))


def metadata(raw):
    meetings, people = [], defaultdict(list)
    for item in ET.fromstring(raw):
        name = item.get('observation', '')
        if item.get('type') != 'nonscenario' or not re.fullmatch(r'(?:EN|IN)\d+[a-z]?', name):
            continue
        date_text = item.attrib['dateOnly']
        require(re.fullmatch(r'\d{1,2}-\d{1,2}-\d{4}', date_text), 'Explicit day-month-year date required')
        date = datetime.strptime(date_text, '%d-%m-%Y').date().isoformat()
        participants = {}
        for person in item.findall('speaker'):
            agent, identity = person.attrib['nxt_agent'], person.attrib['global_name']
            require(re.fullmatch(r'[A-Z]', agent) and identity and agent not in participants,
                    'Invalid or duplicate metadata channel')
            participants[agent] = identity
        require(len(set(participants.values())) == len(participants), 'Repeated global identity within meeting')
        meeting = {'meeting': name, 'date': date, 'date_label_original': date_text,
                   'participants': participants, 'type': 'nonscenario'}
        meetings.append(meeting)
        for identity in participants.values():
            people[identity].append(meeting)
    require(len({m['meeting'] for m in meetings}) == len(meetings), 'Duplicate natural meeting identity')
    eligible = sorted((p for p, ms in people.items() if len({m['date'] for m in ms}) >= 3), key=candidate_hash)[:15]
    schedules = []
    for rank, identity in enumerate(eligible, 1):
        ordered = sorted(people[identity], key=lambda m: (m['date'], m['meeting']))
        first = ordered[0]
        history = next(m for m in ordered if m['date'] > first['date'])
        target = next(m for m in ordered if m['date'] > history['date'])
        schedules.append({'candidate_rank': rank, 'global_name': identity,
                          'source': first, 'history': history, 'target': target})
    labels = {identity: f'AMI-P{index:03}' for index, identity in enumerate(sorted(people, key=candidate_hash), 1)}
    return meetings, schedules, labels


def fixed_inventory(meetings, schedules, labels):
    require((len(meetings), len(labels), len(schedules)) == (26, 51, 15),
            'Frozen metadata inventory must be26 natural meetings,51 participants,15 candidates before body access')


def times(element, start_key, end_key):
    start, end = float(element.attrib[start_key]), float(element.attrib[end_key])
    require(math.isfinite(start) and math.isfinite(end) and 0 <= start <= end, 'Invalid annotation times')
    return start, end


def render_words(words):
    # Preserve lexical forms and explicit punctuation; nonlexical events stay in the private annotation list.
    text = ''
    for word in words:
        if word['tag'] != 'w':
            continue
        separator = '' if word['attributes'].get('punc') == 'true' else (' ' if text else '')
        text += separator + word['form']
    return text


def parse_meeting(read_entry, meeting, labels, exclusion_provenance=None):
    """Assign global sequence positions BEFORE exclusions; overlaps are not removed."""
    all_segments, exclusions, barriers = [], Counter(), []
    for agent, identity in sorted(meeting['participants'].items()):
        word_entry = f"words/{meeting['meeting']}.{agent}.words.xml"
        segment_entry = f"segments/{meeting['meeting']}.{agent}.segments.xml"
        word_bytes = read_entry(word_entry)
        elements = list(ET.fromstring(word_bytes))
        ids = [element.attrib[NITE + 'id'] for element in elements]
        require(len(ids) == len(set(ids)), 'Duplicate word annotation identity')
        positions = {identity: index for index, identity in enumerate(ids)}
        unpositioned_gaps, covered_gaps = set(), set()
        for index, element in enumerate(elements):
            if element.tag == 'gap':
                try:
                    start, end = times(element, 'starttime', 'endtime')
                except (KeyError, ValueError):
                    unpositioned_gaps.add(index)
                    continue
                barriers.append({'start': start, 'end': end, 'entry': word_entry,
                                 'annotation_id': ids[index], 'barrier': True})
        used_segments = set()
        segment_bytes = read_entry(segment_entry)
        for segment in ET.fromstring(segment_bytes):
            require(segment.tag == 'segment', 'Unsupported segment annotation')
            sid = segment.attrib[NITE + 'id']
            require(sid not in used_segments, 'Duplicate segment identity')
            used_segments.add(sid)
            referenced = []
            for child in segment:
                require(child.tag == NITE + 'child', 'Unsupported segment relation')
                match = re.fullmatch(re.escape(Path(word_entry).name) + r'#id\(([^)]+)\)(?:\.\.id\(([^)]+)\))?', child.attrib['href'])
                require(match and match[1] in positions and (match[2] or match[1]) in positions,
                        'Word pointer escaped its meeting/channel or is missing')
                lo, hi = positions[match[1]], positions[match[2] or match[1]]
                require(lo <= hi, 'Reversed annotation pointer')
                referenced.extend(range(lo, hi + 1))
            require(referenced and referenced == list(range(referenced[0], referenced[-1] + 1)),
                    'Segment has missing, duplicate or noncontiguous annotation references')
            covered_gaps.update(unpositioned_gaps.intersection(referenced))
            try:
                start, end = times(segment, 'transcriber_start', 'transcriber_end')
            except (KeyError, ValueError):
                exclusions['unverifiable_mandatory_segment_time'] += 1
                if exclusion_provenance is not None:
                    exclusion_provenance.append({'reason': 'whole_meeting_excluded_for_segment_timing',
                        'segment_archive_entry': segment_entry, 'segment_archive_entry_sha256': hash_bytes(segment_bytes),
                        'segment_id': sid, 'original_segment_attributes': dict(segment.attrib),
                        'missing_time_attributes': [k for k in ('transcriber_start', 'transcriber_end') if k not in segment.attrib],
                        'timing_repaired': False})
                continue
            annotations, reject = [], None
            for index in referenced:
                element = elements[index]
                if element.tag not in ('w', 'vocalsound', 'disfmarker', 'gap'):
                    reject = 'unsupported_word_annotation'
                if element.tag == 'gap' or element.get('pron') == 'foreign':
                    reject = 'gap_or_foreign_annotation'
                try:
                    times(element, 'starttime', 'endtime')
                except (KeyError, ValueError) as exc:
                    reject = ('invalid_word_annotation_time' if element.tag == 'w' and isinstance(exc, ValueError)
                              else 'unverifiable_annotation_time_for_timed_window')
                    if exclusion_provenance is not None:
                        exclusion_provenance.append({'reason': reject, 'segment_archive_entry': segment_entry,
                            'segment_id': sid, 'word_archive_entry': word_entry,
                            'word_archive_entry_sha256': hash_bytes(word_bytes), 'annotation_tag': element.tag,
                            'word_annotation_id': ids[index], 'original_word_attributes': dict(element.attrib),
                            'missing_time_attributes': [k for k in ('starttime', 'endtime') if k not in element.attrib],
                            'timing_repaired': False})
                annotations.append({'annotation_id': ids[index], 'tag': element.tag,
                    'form': ''.join(element.itertext()), 'attributes': dict(element.attrib)})
            text = render_words(annotations)
            segment_text = ET.Element('Segment')
            segment_text.text = text
            screened = v2.screened_text(segment_text)
            if screened is None:
                reject = 'sensitive_contact_uncertain_or_empty'
            elif not v3.screen({'text': screened[0]}):
                reject = 'additional_sensitive_or_calibration'
            turn = {'speaker': labels[identity], 'start': start, 'end': end, 'text': text,
                'possible_name_tokens_for_private_audit': screened[1] if screened else [],
                'annotation_segments': [{'archive_entry': segment_entry, 'segment_id': sid,
                    'segment_attributes': dict(segment.attrib), 'word_archive_entry': word_entry,
                    'word_annotations': annotations}], 'entry': segment_entry, 'annotation_id': sid,
                'reject': reject, 'barrier': False}
            all_segments.append(turn)
        require(unpositioned_gaps <= covered_gaps, 'Unpositioned gap lacks a containing segment; no timing inferred')
    if exclusions['unverifiable_mandatory_segment_time']:
        exclusions['whole_meeting_excluded_for_segment_timing'] = 1
        return [], dict(exclusions)
    combined = sorted(all_segments + barriers, key=lambda t: (t['start'], t['end'], t['entry'], t['annotation_id']))
    retained = []
    for index, turn in enumerate(combined):
        if turn['barrier']:
            exclusions['explicit_gap_contiguity_barrier'] += 1
        elif turn['reject']:
            exclusions[turn['reject']] += 1
        else:
            retained.append({k: v for k, v in turn.items() if k not in ('reject', 'entry', 'annotation_id', 'barrier')} |
                            {'source_segment_ids': [index]})
    merged = []
    for turn in retained:
        if (merged and merged[-1]['speaker'] == turn['speaker']
                and 0 <= turn['start'] - merged[-1]['end'] <= 1
                and turn['source_segment_ids'][0] == merged[-1]['source_segment_ids'][-1] + 1):
            previous = merged[-1]
            previous['text'] += ' ' + turn['text']
            previous['end'] = turn['end']
            previous['source_segment_ids'] += turn['source_segment_ids']
            previous['annotation_segments'] += turn['annotation_segments']
            previous['possible_name_tokens_for_private_audit'] = sorted(set(
                previous['possible_name_tokens_for_private_audit'] + turn['possible_name_tokens_for_private_audit']))
        else:
            merged.append(dict(turn))
    return merged, dict(exclusions)


def source_candidate(schedule, parsed, labels, source_names, unusable_meetings=()):
    speaker = labels[schedule['global_name']]
    source = parsed[schedule['source']['meeting']]
    facts = [turn for turn in source if turn['speaker'] == speaker
             and 6 <= len(v1.WORDS.findall(turn['text'])) <= 100 and '?' not in turn['text']
             and v1.SELFREPORT.search(turn['text']) and v1.PROFESSIONAL.search(turn['text'])
             and not v1.HYPOTHETICAL.search(turn['text'])][:6]
    excluded = {sid for turn in facts for sid in turn['source_segment_ids']}
    style = v1.style_profile(source, speaker, excluded)
    examples, words = [], 0
    for turn in source:
        count = len(v1.WORDS.findall(turn['text']))
        if (turn['speaker'] == speaker and not excluded.intersection(turn['source_segment_ids'])
                and 10 <= count <= 60 and words + count <= 200):
            examples.append(turn)
            words += count
            if len(examples) == 6:
                break
    history = v3.history(parsed[schedule['history']['meeting']], speaker)
    reasons = []
    source_usable = schedule['source']['meeting'] not in unusable_meetings
    history_usable = schedule['history']['meeting'] not in unusable_meetings
    if not source_usable:
        reasons.append('fixed_source_meeting_structurally_unusable_for_timed_study')
    else:
        if not facts:
            reasons.append('no_retrieved_first_source_selfreport')
        if style is None:
            reasons.append('insufficient_separate_style_source')
        if len(examples) < 4:
            reasons.append('insufficient_bounded_style_examples')
    if not history_usable:
        reasons.append('fixed_history_meeting_structurally_unusable_for_timed_study')
    elif history is None:
        reasons.append('no_eligible_contiguous_history_window')
    return {'candidate_rank': schedule['candidate_rank'], 'speaker': speaker,
            'first_source_meeting': schedule['source']['meeting'], 'first_source_date': schedule['source']['date'],
            'history_meeting': schedule['history']['meeting'], 'history_date': schedule['history']['date'],
            'target_meeting_metadata_only': schedule['target']['meeting'], 'target_date': schedule['target']['date'],
            'target_incidentally_exposed_as_another_source': schedule['target']['meeting'] in source_names,
            'fixed_source_usable_for_timed_study': source_usable,
            'fixed_history_usable_for_timed_study': history_usable,
            'facts_source_selfreports_not_world_verified': facts, 'style': style, 'style_examples': examples,
            'history': history, 'automatic_retrieval_gaps': reasons,
            'status': 'SOURCE_RETRIEVAL_ONLY_COMPLETE_PROPOSITIONS_AND_PRIVACY_REQUIRE_ACTUAL_CURATION'}


def source_pool(expected_policy_sha256):
    require(expected_policy_sha256 == POLICY_SHA and v1.digest(POLICY) == POLICY_SHA, 'Frozen AMI policy changed')
    policy = json.loads(POLICY.read_text(encoding='utf-8'))
    sources = {}
    for name, expected in FROZEN_HELPERS.items():
        path = Path('tools') / name
        require(v1.digest(path) == expected, 'Frozen ICSI source helper changed')
        sources[path.as_posix()] = expected
    for path in (Path('tools/ami_english_material_v1.py'), Path('tests/test_ami_english_material_v1.py')):
        sources[path.as_posix()] = v1.digest(path)
    archive_path = Path(policy['archive']['path'])
    require(archive_path.resolve().is_relative_to(Path('.local/datasets/ami_english_v1').resolve())
            and archive_path.stat().st_size == policy['archive']['bytes']
            and v1.digest(archive_path) == policy['archive']['sha256'], 'AMI archive binding changed')
    entry_hashes, exclusions, exclusion_provenance = {}, Counter(), []
    with zipfile.ZipFile(archive_path) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), 'Duplicate ZIP members')
        raw_metadata = archive.read('corpusResources/meetings.xml')
        entry_hashes['corpusResources/meetings.xml'] = hash_bytes(raw_metadata)
        meetings, schedules, labels = metadata(raw_metadata)
        fixed_inventory(meetings, schedules, labels)
        source_names = {schedule[role]['meeting'] for schedule in schedules for role in ('source', 'history')}
        target_names = {schedule['target']['meeting'] for schedule in schedules}
        allowed = {f"{kind}/{meeting['meeting']}.{agent}.{kind}.xml" for meeting in meetings
                   if meeting['meeting'] in source_names for agent in meeting['participants'] for kind in ('words', 'segments')}
        def read_source(name):
            require(name in allowed, 'Stage-one target or unrelated body access blocked')
            value = archive.read(name)
            entry_hashes[name] = hash_bytes(value)
            return value
        parsed, unusable_meetings = {}, set()
        for meeting in sorted(meetings, key=lambda m: (m['date'], m['meeting'])):
            if meeting['meeting'] in source_names:
                parsed[meeting['meeting']], rejected = parse_meeting(read_source, meeting, labels, exclusion_provenance)
                exclusions.update(rejected)
                if rejected.get('whole_meeting_excluded_for_segment_timing'):
                    unusable_meetings.add(meeting['meeting'])
        candidates = [source_candidate(schedule, parsed, labels, source_names, unusable_meetings) for schedule in schedules]
    artifact = {'schema': 'ami_english_source_pool_v1', 'policy_sha256': POLICY_SHA,
        'archive_sha256': policy['archive']['sha256'], 'source_hashes': sources,
        'status': 'STAGE1_RETRIEVAL_NOT_SEMANTIC_SOURCE_APPROVAL_NOT_TARGET_ACCESS_GO',
        'global_to_pseudonymous_private': labels, 'metadata_schedules_private': schedules,
        'source_meetings_read_private': sorted(source_names),
        'target_meetings_incidentally_exposed_private': sorted(target_names & source_names),
        'annotation_entry_sha256_private': entry_hashes, 'candidates': candidates,
        'annotation_time_exclusions_private': exclusion_provenance,
        'whole_meetings_excluded_for_segment_timing_private': sorted(unusable_meetings),
        'segment_exclusions': dict(exclusions), 'new_model_generations': 0,
        'target_only_meeting_bodies_read': 0,
        'limitations': 'Machine retrieval is not semantic approval, human review, final cohort selection or inference authorization. Original word forms and punctuation retained; nonlexical events retained in private annotation provenance, not treated as words. Gap events create sequence barriers before filtering. Possible names remain private and require explicit curation. No cross-corpus identity disjointness can be inferred from different identifiers.'}
    report = {key: artifact[key] for key in ('schema', 'policy_sha256', 'archive_sha256', 'source_hashes',
              'status', 'segment_exclusions', 'new_model_generations', 'target_only_meeting_bodies_read', 'limitations')}
    report.update(natural_meetings=len(meetings), natural_global_participants=len(labels),
        fixed_metadata_candidates=len(schedules), source_meetings_read=len(source_names),
        annotation_entries_read=len(entry_hashes) - 1,
        whole_meetings_excluded_for_segment_timing=len(unusable_meetings),
        unverifiable_or_malformed_time_annotations_preserved_and_excluded=len(exclusion_provenance),
        future_target_meetings_incidentally_exposed=len(target_names & source_names),
        candidates_with_incidental_target_exposure=sum(c['target_incidentally_exposed_as_another_source'] for c in candidates),
        candidates_with_all_retrieval_components=sum(not c['automatic_retrieval_gaps'] for c in candidates),
        retrieved_fact_turns=sum(len(c['facts_source_selfreports_not_world_verified']) for c in candidates),
        candidate_gaps=dict(Counter(reason for c in candidates for reason in c['automatic_retrieval_gaps'])),
        actual_semantically_qualified_speakers=None, final_cohort_selected=False,
        source_curation_required_before_any_target_selection=True)
    return artifact, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--source-pool', action='store_true')
    modes.add_argument('--verify', action='store_true')
    parser.add_argument('--expected-policy-sha256', required=True)
    args = parser.parse_args(argv)
    if args.source_pool:
        require(not PRIVATE.exists() and not PUBLIC.exists(), 'AMI source artifacts exist; no overwrite')
    artifact, report = source_pool(args.expected_policy_sha256)
    if args.source_pool:
        created = datetime.now(timezone.utc).isoformat()
        v1.write_new(PRIVATE, dict(artifact, created_utc=created))
        v1.write_new(PUBLIC, dict(report, created_utc=created, private_pool_sha256=v1.digest(PRIVATE)))
    else:
        receipt = json.loads(PUBLIC.read_text(encoding='utf-8'))
        require(v1.digest(PRIVATE) == receipt['private_pool_sha256'], 'Private source pool hash changed')
        saved = json.loads(PRIVATE.read_text(encoding='utf-8'))
        require({k: v for k, v in saved.items() if k != 'created_utc'} == artifact
                and {k: v for k, v in receipt.items() if k not in ('created_utc', 'private_pool_sha256')} == report,
                'Source retrieval reproduction differs')
    print(json.dumps({'status': 'PASS', 'mode': 'WRITE_ONCE' if args.source_pool else 'READ_ONLY_VERIFY',
                      'public_receipt_sha256': v1.digest(PUBLIC), 'new_model_generations': 0,
                      'fixed_candidates': report['fixed_metadata_candidates'],
                      'all_components_retrieved_not_qualified': report['candidates_with_all_retrieval_components']}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
