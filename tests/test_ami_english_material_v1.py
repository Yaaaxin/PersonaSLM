"""Authored AMI-shaped XML only; no corpus, private identities or target dialogue."""
import copy
import json
import xml.etree.ElementTree as ET

import pytest

import ami_english_material_v1 as ami


def meeting_metadata():
    root = ET.Element('root')
    for name, date, kind in [('EN9001', '2-1-2005', 'nonscenario'), ('EN9002', '3-1-2005', 'nonscenario'),
                              ('EN9003', '4-1-2005', 'nonscenario'), ('EN9004', '5-1-2005', 'nonscenario'),
                              ('EN9999', '1-1-2000', 'scenario'), ('IB9000', '1-1-1999', 'nonscenario'),
                              ('ES9000a', '1-1-1998', 'scenario'), ('EN9998', '1-1-1997', 'N')]:
        item = ET.SubElement(root, 'meeting', observation=name, dateOnly=date, type=kind)
        ET.SubElement(item, 'speaker', nxt_agent='A', global_name='authored_one')
        ET.SubElement(item, 'speaker', nxt_agent='B', global_name='authored_two')
    return ET.tostring(root)


def annotation_entries(gap=False, foreign=False):
    entries = {}
    for agent in ('A', 'B'):
        words, segments = ET.Element('root'), ET.Element('root')
        for index in range(6):
            start = 4*index + (0 if agent == 'A' else 2)
            segment = ET.SubElement(segments, 'segment', {ami.NITE+'id': f's{agent}{index}',
                'transcriber_start': str(start), 'transcriber_end': str(start+1)})
            forms = ['I', 'wrote', 'software', 'for', 'the', 'shared', 'project', 'today', '.']
            identifiers = []
            for number, form in enumerate(forms):
                identity = f'w{agent}{index}_{number}'
                attrs = {ami.NITE+'id': identity, 'starttime': str(start), 'endtime': str(start+1)}
                if form == '.': attrs['punc'] = 'true'
                if foreign and index == 2 and agent == 'A': attrs['pron'] = 'foreign'
                node = ET.SubElement(words, 'w', attrs); node.text = form; identifiers.append(identity)
            ET.SubElement(segment, ami.NITE+'child', href=f'EN9001.{agent}.words.xml#id({identifiers[0]})..id({identifiers[-1]})')
            if gap and index == 2 and agent == 'A':
                ET.SubElement(words, 'gap', {ami.NITE+'id': 'authored_gap',
                    'starttime': str(start+1.5), 'endtime': str(start+1.7)})
        entries[f'words/EN9001.{agent}.words.xml'] = ET.tostring(words)
        entries[f'segments/EN9001.{agent}.segments.xml'] = ET.tostring(segments)
    return entries


def test_metadata_uses_global_identity_natural_only_and_one_fixed_triple():
    meetings, schedules, labels = ami.metadata(meeting_metadata())
    assert len(meetings) == 4 and len(schedules) == 2
    assert [s['global_name'] for s in schedules] == sorted(labels, key=ami.candidate_hash)
    assert all([s[k]['meeting'] for k in ('source', 'history', 'target')] == ['EN9001', 'EN9002', 'EN9003'] for s in schedules)
    assert all(s['source']['date'] == '2005-01-02' for s in schedules)
    assert set(labels.values()) == {'AMI-P001', 'AMI-P002'}
    with pytest.raises(ValueError, match='day-month-year'):
        ami.metadata(meeting_metadata().replace(b'2-1-2005', b'2005-01-02'))


def test_known_frozen_metadata_inventory_fails_closed_before_body_access():
    ami.fixed_inventory([None]*26, [None]*15, dict.fromkeys(range(51)))
    for counts in ((0, 0, 0), (26, 50, 15), (26, 51, 14)):
        meetings, people, candidates = counts
        with pytest.raises(ValueError, match='before body access'):
            ami.fixed_inventory([None]*meetings, [None]*candidates, dict.fromkeys(range(people)))


def test_annotation_ids_offsets_punctuation_and_overlap_are_preserved():
    entries = annotation_entries()
    meeting = ami.metadata(meeting_metadata())[0][0]
    calls = []
    def read(name):
        assert name.startswith(('words/EN9001.', 'segments/EN9001.'))
        calls.append(name)
        return entries[name]
    turns, excluded = ami.parse_meeting(read, meeting, {'authored_one': 'A', 'authored_two': 'B'})
    assert len(turns) == 12 and not excluded and len(calls) == 4
    assert turns[0]['text'] == 'I wrote software for the shared project today.'
    origin = turns[0]['annotation_segments'][0]
    assert origin['segment_id'] == 'sA0' and origin['word_annotations'][0]['annotation_id'] == 'wA0_0'
    assert origin['segment_attributes']['transcriber_start'] == '0'
    assert turns[0]['source_segment_ids'] == [0]
    overlap = copy.deepcopy(turns[:2]); overlap[1]['start'] = .5
    assert ami.v2.contiguous(overlap)


@pytest.mark.parametrize('gap,foreign', [(True, False), (False, True)])
def test_gap_or_rejected_segment_breaks_contiguity(gap, foreign):
    meeting = ami.metadata(meeting_metadata())[0][0]
    entries = annotation_entries(gap=gap, foreign=foreign)
    turns, excluded = ami.parse_meeting(entries.__getitem__, meeting, {'authored_one': 'A', 'authored_two': 'B'})
    assert excluded and not ami.v2.contiguous(turns)
    assert any(b['source_segment_ids'][0] != a['source_segment_ids'][-1]+1 for a,b in zip(turns,turns[1:]))


def test_pointer_cannot_read_other_meeting_or_skip_annotations():
    meeting = ami.metadata(meeting_metadata())[0][0]
    entries = annotation_entries()
    entries['segments/EN9001.A.segments.xml'] = entries['segments/EN9001.A.segments.xml'].replace(b'EN9001.A.words.xml#', b'EN9003.A.words.xml#', 1)
    with pytest.raises(ValueError, match='pointer escaped'):
        ami.parse_meeting(entries.__getitem__, meeting, {'authored_one': 'A', 'authored_two': 'B'})


@pytest.mark.parametrize('punctuation', [True, False])
def test_malformed_word_time_excludes_whole_segment_and_preserves_original_provenance(punctuation):
    meeting = ami.metadata(meeting_metadata())[0][0]
    entries = annotation_entries()
    path = 'words/EN9001.A.words.xml'
    root = ET.fromstring(entries[path])
    element = next(e for e in root if e.attrib[ami.NITE+'id'] == ('wA2_8' if punctuation else 'wA2_0'))
    element.set('endtime', '1')
    entries[path] = ET.tostring(root)
    provenance = []
    turns, excluded = ami.parse_meeting(entries.__getitem__, meeting,
        {'authored_one': 'A', 'authored_two': 'B'}, provenance)
    assert len(turns) == 11 and excluded['invalid_word_annotation_time'] == 1
    assert not ami.v2.contiguous(turns)
    assert len(provenance) == 1 and provenance[0]['segment_id'] == 'sA2'
    assert provenance[0]['original_word_attributes']['starttime'] == '8'
    assert provenance[0]['original_word_attributes']['endtime'] == '1'
    assert provenance[0]['word_archive_entry_sha256'] == ami.hash_bytes(entries[path])
    assert provenance[0]['timing_repaired'] is False


@pytest.mark.parametrize('tag,missing', [('disfmarker', ['starttime']), ('gap', ['starttime', 'endtime']),
                                       ('w', ['starttime'])])
def test_missing_annotation_time_is_unverifiable_not_repaired(tag, missing):
    meeting = ami.metadata(meeting_metadata())[0][0]
    entries = annotation_entries(); path = 'words/EN9001.A.words.xml'
    root = ET.fromstring(entries[path])
    element = next(e for e in root if e.attrib[ami.NITE+'id'] == 'wA2_0')
    element.tag = tag
    for key in missing:
        del element.attrib[key]
    entries[path] = ET.tostring(root)
    provenance = []
    turns, excluded = ami.parse_meeting(entries.__getitem__, meeting,
        {'authored_one': 'A', 'authored_two': 'B'}, provenance)
    assert len(turns) == 11 and not ami.v2.contiguous(turns)
    assert excluded['unverifiable_annotation_time_for_timed_window'] == 1
    assert provenance[0]['missing_time_attributes'] == missing
    assert all(key not in provenance[0]['original_word_attributes'] for key in missing)
    assert provenance[0]['timing_repaired'] is False


def test_unpositioned_gap_without_containing_segment_fails_closed():
    meeting = ami.metadata(meeting_metadata())[0][0]
    entries = annotation_entries(); path = 'words/EN9001.A.words.xml'
    root = ET.fromstring(entries[path])
    ET.SubElement(root, 'gap', {ami.NITE+'id': 'unpositioned_unreferenced_gap'})
    entries[path] = ET.tostring(root)
    with pytest.raises(ValueError, match='Unpositioned gap lacks'):
        ami.parse_meeting(entries.__getitem__, meeting, {'authored_one': 'A', 'authored_two': 'B'})


@pytest.mark.parametrize('bad_end', ['1', '-1', 'nan', 'inf', 'not-a-time', None])
def test_bad_segment_time_excludes_whole_meeting_preserves_original_and_validates_refs(bad_end):
    meeting = ami.metadata(meeting_metadata())[0][0]
    entries = annotation_entries(); path = 'segments/EN9001.A.segments.xml'
    segments = ET.fromstring(entries[path])
    segment = segments[2]
    if bad_end is None:
        del segment.attrib['transcriber_end']
    else:
        segment.set('transcriber_end', bad_end)
    entries[path] = ET.tostring(segments)
    provenance = []
    turns, excluded = ami.parse_meeting(entries.__getitem__, meeting,
        {'authored_one': 'A', 'authored_two': 'B'}, provenance)
    assert turns == []
    assert excluded['whole_meeting_excluded_for_segment_timing'] == 1
    assert excluded['unverifiable_mandatory_segment_time'] == 1
    assert provenance[0]['original_segment_attributes'] == dict(segment.attrib)
    assert provenance[0]['segment_archive_entry_sha256'] == ami.hash_bytes(entries[path])
    assert provenance[0]['timing_repaired'] is False
    # Invalid timing never suppresses structural errors in later segments/channels.
    entries['segments/EN9001.B.segments.xml'] = entries['segments/EN9001.B.segments.xml'].replace(
        b'EN9001.B.words.xml#', b'EN9003.B.words.xml#', 1)
    with pytest.raises(ValueError, match='pointer escaped'):
        ami.parse_meeting(entries.__getitem__, meeting, {'authored_one': 'A', 'authored_two': 'B'})


def test_unusable_fixed_meeting_never_selects_alternate_or_claims_missing_facts():
    _, schedules, labels = ami.metadata(meeting_metadata())
    schedule = schedules[0]
    parsed = {'EN9001': [], 'EN9002': []}
    candidate = ami.source_candidate(schedule, parsed, labels, set(parsed), {'EN9001', 'EN9002'})
    assert candidate['first_source_meeting'] == 'EN9001'
    assert candidate['history_meeting'] == 'EN9002'
    assert candidate['target_meeting_metadata_only'] == 'EN9003'
    assert candidate['automatic_retrieval_gaps'] == [
        'fixed_source_meeting_structurally_unusable_for_timed_study',
        'fixed_history_meeting_structurally_unusable_for_timed_study']
    assert not candidate['fixed_source_usable_for_timed_study']
    assert not candidate['fixed_history_usable_for_timed_study']
    assert candidate['facts_source_selfreports_not_world_verified'] == []


def test_retrieval_does_not_request_target_and_keeps_failures_not_qualified():
    meetings, schedules, labels = ami.metadata(meeting_metadata())
    schedule = schedules[0]
    source = [{'speaker': labels[schedule['global_name']], 'text': 'I wrote software for the shared project today.',
               'start': i*2., 'end': i*2.+1, 'source_segment_ids': [i]} for i in range(20)]
    # Only designated source/history exist; any target lookup would fail.
    parsed = {'EN9001': source, 'EN9002': []}
    candidate = ami.source_candidate(schedule, parsed, labels, set(parsed))
    assert len(candidate['facts_source_selfreports_not_world_verified']) == 6
    assert not set(candidate['style']['source_segment_ids']).intersection(range(6))
    assert candidate['target_incidentally_exposed_as_another_source'] is False
    assert 'no_eligible_contiguous_history_window' in candidate['automatic_retrieval_gaps']
    assert 'CURATION' in candidate['status']


def test_policy_hash_rejects_before_archive_access():
    with pytest.raises(ValueError, match='policy changed'):
        ami.source_pool('wrong')


def test_write_once_verify_readonly_and_no_private_payload_on_console(monkeypatch, tmp_path, capsys):
    artifact = {'private_fixture_identity': 'authored_private_person', 'private_quote': 'authored private quote'}
    report = {'fixed_metadata_candidates': 2, 'candidates_with_all_retrieval_components': 0}
    monkeypatch.setattr(ami, 'PRIVATE', tmp_path/'private/pool.json')
    monkeypatch.setattr(ami, 'PUBLIC', tmp_path/'public/receipt.json')
    monkeypatch.setattr(ami, 'source_pool', lambda _: (copy.deepcopy(artifact), copy.deepcopy(report)))
    assert ami.main(['--source-pool', '--expected-policy-sha256', 'fixture']) == 0
    original = [(p.read_bytes(), p.stat().st_mtime_ns) for p in (ami.PRIVATE, ami.PUBLIC)]
    assert ami.main(['--verify', '--expected-policy-sha256', 'fixture']) == 0
    assert original == [(p.read_bytes(), p.stat().st_mtime_ns) for p in (ami.PRIVATE, ami.PUBLIC)]
    assert 'authored_private' not in capsys.readouterr().out
    with pytest.raises(ValueError, match='no overwrite'):
        ami.main(['--source-pool', '--expected-policy-sha256', 'fixture'])
