"""Post hoc P1 measurement diagnostics and blank review packaging, never rescoring."""
from collections import Counter
import json
import random

from .response_status import ROLE, classify_response, text_hash

VERSION = 'p1_measurement_audit_v1'
REVIEW_VERSION = 'p1_output_human_review_v1'
HUMAN_FIELDS = (
    'human_reply_unit_confirmed', 'human_semantic_completeness', 'human_factual_consistency',
    'human_temporal_consistency', 'human_response_relevance_1_to_5', 'human_conversational_coherence_1_to_5',
    'human_unverifiable_reason', 'human_evidence_quotations', 'human_continuation_notes', 'reviewer_notes',
    'reviewer_id', 'review_assistance', 'prior_access_to_treatments_or_scores', 'reviewed_utc',
)


def partition(row):
    """Verify exact frozen offsets, including whitespace, without reparsing a new unit."""
    boundary = row['evaluation']['response_completeness']
    raw = row['raw_response']
    span = boundary['first_span']
    if not 0 <= span['start'] <= span['end'] <= len(raw):
        raise ValueError('Invalid first-reply offsets')
    if (raw[span['start']:span['end']] != span['text'] or
        raw[:span['start']] != boundary['removed_prefix'] or
        raw[span['end']:] != boundary['excluded_tail'] or
        text_hash(raw) != boundary['raw_sha256'] or text_hash(span['text']) != span['sha256'] or
        row['parsed_response'] != span['text']):
        raise ValueError('Frozen parser partition does not reconstruct raw output')
    expected_operations = {'first_span': span, 'removed_prefix': boundary['removed_prefix'],
                           'excluded_continuation': boundary['excluded_tail']}
    if row['parser_operations'] != expected_operations:
        raise ValueError('Parser-operation trace differs from frozen partition')
    reconstructed = classify_response(raw, row['raw_termination'])
    if reconstructed != boundary:
        raise ValueError('Frozen response classification no longer reconstructs')
    tail = boundary['excluded_tail']
    transitions = list(ROLE.finditer(tail))
    turns = []
    for i, hit in enumerate(transitions):
        end = transitions[i+1].start() if i+1 < len(transitions) else len(tail)
        start = span['end'] + hit.start()
        finish = span['end'] + end
        turns.append({'role_label': hit.group(1), 'raw_start': start, 'raw_end': finish,
                      'raw_text': raw[start:finish],
                      'meaning_complete': None})
    return {'first_reply': span, 'excluded_prefix': boundary['removed_prefix'], 'additional_turns': turns,
            'excluded_continuation': tail, 'original_status': boundary['status'],
            'first_span_identifiable': boundary['unit_identifiable'],
            'observed_reply_boundary': boundary['observed_boundary'],
            'boundary_observed': boundary['observed_boundary'] is not None,
            'native_termination': row['raw_termination'], 'normalized_stop_reason': row['stop_reason'],
            'output_budget_reached': row['generated_tokens'] == 96,
            'first_reply_budget_censored': boundary['status'] == 'TRUNCATED',
            'semantic_completeness': 'UNREVIEWED',
            'parser_operations': row['parser_operations'], 'raw_reconstruction_exact': True}


def sentence_form(case, first):
    """Whole-span/source-bound form inventory; not a correctness/completeness classifier.

    Exact named subject, predicate, object and (if present) interval are required.
    Negation, another candidate, extra claims or unresolved attributions do not
    match. Unsupported text is left unresolved, never scored by substring.
    """
    text = first.strip()
    kind, fact = 'UNSUPPORTED_FORM', None
    name = case['speaker_name']
    if not text:
        kind = 'EMPTY_FIRST_REPLY'
    elif text.startswith('<think>') and '</think>' not in text:
        kind = 'OPEN_DELIBERATION_PREFIX'
    else:
        applicable = [f for f in case['facts'] if f['valid_from'] <= case['evaluation_date']
                      and (f['valid_until'] is None or case['evaluation_date'] <= f['valid_until'])]
        for item in applicable:
            if case['family'] in 'AD' and item['attribute'] == 'current_city':
                if item['value'] != case['expected_answer']:
                    continue
                stem = f"{name} currently lives in {item['value']}"
                forms = {stem + '.': 'CURRENT_CITY_SENTENCE',
                         stem + f", valid from {item['valid_from']} onward.": 'DATED_CURRENT_CITY_SENTENCE'}
            elif case['family'] == 'B' and item['attribute'] == 'reading_group':
                if item['value'] != case['expected_answer']:
                    continue
                stem = f"{name} is a member of the {item['value']}."
                forms = {stem: 'MEMBERSHIP_SENTENCE',
                         'The verified record shows that ' + stem: 'ATTRIBUTED_MEMBERSHIP_SENTENCE'}
            else:
                continue
            if text in forms:
                kind, fact = forms[text], item
                break
    recognized = fact is not None
    return {'version': VERSION, 'observed_form': kind, 'bound_source_fact': fact,
            'whole_span_source_form_match': recognized,
            'human_factual_label': None, 'replacement_score': None,
            'semantic_completeness': None,
            'scope': 'Post-output strict surface-form diagnosis, not independent semantic validation',
            'possible_causes': {
                'unsupported_answer_syntax': kind in ('DATED_CURRENT_CITY_SENTENCE', 'UNSUPPORTED_FORM'),
                'date_bearing_answer': kind == 'DATED_CURRENT_CITY_SENTENCE',
                'missing_answer': True if kind == 'EMPTY_FIRST_REPLY' else (False if recognized else None),
                'contradictory_answer': False if recognized else None,
                'multiple_answer_candidates': False if recognized else None,
                'speaker_attribution_ambiguity': False if recognized else None,
                'other_unsupported_task_type': case['family'] == 'B',
                'semantic_incompleteness': None}}


def coverage(rows):
    endpoints = {'response_relevance': 'response_relevance', 'factual_consistency': 'factual_support',
                 'temporal_consistency': 'temporal_consistency', 'conversational_coherence': 'conversational_coherence'}
    result = {}
    for endpoint, key in endpoints.items():
        eligible = [r for r in rows if r['applicability'][endpoint]]
        labels = Counter(r['evaluation'][key]['label'] for r in eligible)
        attempts = sum(r['family'] in 'AD' for r in eligible) if endpoint == 'factual_consistency' else 0
        decisive = labels['Correct'] + labels['Incorrect']
        result[endpoint] = {'eligible': len(eligible), 'received': len(eligible),
                           'automatically_assessed_attempts': attempts, 'conclusive_automatic_labels': decisive,
                           'minimum_unresolved_human_reviews': len(eligible) - decisive,
                           'independent_packet_review_items': len(eligible),
                           'unverifiable_labels': labels['Unverifiable'],
                           'unverifiable_after_automatic_attempt': sum(r['family'] in 'AD' and r['evaluation'][key]['label'] == 'Unverifiable' for r in eligible) if endpoint == 'factual_consistency' else 0,
                           'pending_human_placeholders': len(eligible) - attempts,
                           'human_evaluated': 0, 'missing_response_records': 0,
                           'empty_first_replies': sum(not r['parsed_response'].strip() for r in eligible),
                           'first_reply_budget_censored': sum(r['evaluation']['response_completeness']['status'] == 'TRUNCATED' for r in eligible),
                           'independently_confirmed_semantic_incomplete': None,
                           'semantic_completeness_unreviewed': len(eligible),
                           'automatic_coverage_fraction': decisive / len(eligible) if eligible else None,
                           'observed_labels': dict(labels)}
    return result


def make_packet(rows, cases, private_seed):
    """No treatment or automatic factual label enters the reviewer-facing view."""
    rng = random.Random(private_seed)
    case_ids = sorted({r['case_id'] for r in rows}); rng.shuffle(case_ids)
    anonymous = {cid: f'MC{i:03d}' for i, cid in enumerate(case_ids, 1)}
    ordered = sorted(rows, key=lambda r: r['request_id']); rng.shuffle(ordered)
    packet, mapping = [], []
    for i, row in enumerate(ordered, 1):
        case = cases[row['case_id']]; boundary = row['evaluation']['response_completeness']
        item = {'review_version': REVIEW_VERSION, 'anonymous_case_id': anonymous[row['case_id']],
                'anonymous_response_id': f'MR{i:03d}', 'current_question': case['question'],
                'trusted_evidence': case['trusted_evidence'], 'evaluation_date': case['evaluation_date'],
                'fixed_preceding_context': '\n'.join(case['context']),
                'reference_historical_facts': json.dumps(case['facts'], ensure_ascii=False),
                'historical_reference_scope': 'Same full source ledger for all responses to this case; does not reveal which history was in the prompt',
                'raw_first_reply': row['parsed_response'], 'raw_full_continuation': row['raw_response'],
                'excluded_generated_continuation': boundary['excluded_tail'], 'structural_status': boundary['status'],
                'native_stop_reason': row['stop_reason'], 'output_budget_reached': str(row['generated_tokens'] == 96).lower(),
                'generated_tokens': str(row['generated_tokens']), 'first_reply_start': str(boundary['first_span']['start']),
                'first_reply_end': str(boundary['first_span']['end']), 'removed_prefix': boundary['removed_prefix'],
                'raw_sha256': text_hash(row['raw_response']), 'first_reply_sha256': text_hash(row['parsed_response'])}
        item.update({f'applicable_{name}': str(value).lower() for name, value in case['applicability'].items()})
        item.update({name: '' for name in HUMAN_FIELDS}); packet.append(item)
        mapping.append({'anonymous_case_id': item['anonymous_case_id'], 'anonymous_response_id': item['anonymous_response_id'],
                        'request_id': row['request_id'], 'case_id': row['case_id'], 'persona_id': row['persona_id'],
                        'condition': row['condition'], 'factors': row['factors'], 'raw_sha256': item['raw_sha256']})
    return packet, {'review_version': REVIEW_VERSION, 'curator_only': True, 'private_shuffle_seed': private_seed,
                    'protection_scope': 'Ignored administration directory; distribute only CSV/guide. No encryption/ACL or successful blinding claimed.',
                    'rows': mapping}


def validate_annotations(master, received):
    """Validate supplied human records without supplying or revising judgments."""
    if not master or len(received) != len(master):
        raise ValueError('Missing or extra review records')
    expected = {r['anonymous_response_id']: r for r in master}
    if len(expected) != len(master):
        raise ValueError('Duplicate master ID')
    seen = set()
    for row in received:
        rid = row.get('anonymous_response_id')
        if rid not in expected or rid in seen:
            raise ValueError('Unknown or duplicate response ID')
        seen.add(rid); source = expected[rid]
        if set(row) != set(source):
            raise ValueError('Review schema changed')
        if any(row[k] != v for k, v in source.items() if k not in HUMAN_FIELDS):
            raise ValueError('Frozen review material or version changed')
        if row['human_reply_unit_confirmed'] not in {'YES', 'NO', 'UNCERTAIN'}:
            raise ValueError('Missing or invalid unit judgment')
        if row['human_semantic_completeness'] not in {'COMPLETE', 'INCOMPLETE', 'UNCERTAIN'}:
            raise ValueError('Missing or invalid completeness judgment')
        for endpoint, field in [('factual_consistency', 'human_factual_consistency'), ('temporal_consistency', 'human_temporal_consistency')]:
            allowed = {'Correct', 'Incorrect', 'Unverifiable'} if source['applicable_' + endpoint] == 'true' else {'Not Applicable'}
            if row[field] not in allowed:
                raise ValueError('Invalid categorical label or frozen applicability conflict')
        for endpoint, field in [('response_relevance', 'human_response_relevance_1_to_5'), ('conversational_coherence', 'human_conversational_coherence_1_to_5')]:
            allowed = {'1', '2', '3', '4', '5', 'Unscorable'} if source['applicable_' + endpoint] == 'true' else {'Not Applicable'}
            if row[field] not in allowed:
                raise ValueError('Invalid rating')
        if not row['reviewer_id'].strip() or row['review_assistance'] not in {'unaided', 'AI-assisted', 'other-disclosed-in-notes'}:
            raise ValueError('Missing reviewer provenance')
        if row['prior_access_to_treatments_or_scores'] not in {'YES', 'NO', 'UNCERTAIN'}:
            raise ValueError('Missing masking disclosure')
        if not row['human_evidence_quotations'].strip():
            raise ValueError('Evidence quotations required')
        if any(row[k] in {'Unverifiable', 'Unscorable'} for k in ('human_factual_consistency', 'human_temporal_consistency', 'human_response_relevance_1_to_5', 'human_conversational_coherence_1_to_5')) and not row['human_unverifiable_reason'].strip():
            raise ValueError('Unresolved judgment requires a reason')
        if row['review_assistance'] == 'other-disclosed-in-notes' and not row['reviewer_notes'].strip():
            raise ValueError('Other assistance requires disclosure')
    return {'review_version': REVIEW_VERSION, 'validated_records': len(received),
            'reviewer_ids': sorted({r['reviewer_id'] for r in received}),
            'unavailable_review_times': sum(not r['reviewed_utc'].strip() for r in received),
            'review_status': 'COMPLETE', 'blind_review_asserted': False,
            'frozen_scores_overwritten': False}
