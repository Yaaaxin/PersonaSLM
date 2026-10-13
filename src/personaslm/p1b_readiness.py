"""Offline P1b revision, independent ledger audit and prospective planning.

No inference client. Analytic checks are not human approval or empirical
difficulty measurements. The v1 generator, policies and artifacts stay frozen.
"""
from collections import Counter
from copy import deepcopy
from datetime import date, datetime
import math
import random
import re
from statistics import NormalDist

from .conditioning import FACTORIAL
from .p1b import (VERSION as PARENT_VERSION, TEMPLATE, REFERENCE, canonical_hash,
                  hash_text, prompt, render_evidence, validate_dataset)

VERSION = 'p1b_development_proposed_v2'
ORDER_SEED = 714001
CHECKS = (
    'evidence_sufficient', 'answers_unique', 'reference_answer_correct',
    'temporal_interpretation_correct', 'entities_clear', 'question_clear',
    'context_valid', 'speaker_consistent', 'reference_stable_across_cells',
    'no_accidental_answer_leakage', 'no_unplanned_contradictions',
    'applicability_correct', 'demand_description_appropriate')

# Independently specified after reading every English question and source ledger.
# These are analytic reference checks, NOT human judgments or response scores.
EXPECTED = {
    'A_L1': {'room': 'Juniper Room 1'}, 'A_L2': {'room': 'Juniper Room 2'},
    'A_L3': {'room': 'Juniper Room 3'},
    'B_L1': {'workshop': 'Bookbinding Group 4', 'role': 'materials coordinator'},
    'B_L2': {'workshop': 'Bookbinding Group 5', 'role': 'materials coordinator', 'place': 'Cedar Hall 5'},
    'B_L3': {'workshop': 'Bookbinding Group 6', 'role': 'materials coordinator', 'place': 'Cedar Hall 6', 'entrance': 'east entrance'},
    'C_L1': {'counter': 'Birch Counter'}, 'C_L2': {'counter': 'Cedar Counter'},
    'C_L3': {'counter': 'Cedar Counter', 'previous_counter': 'Birch Counter'},
    'D_L1': {'locker': 'Locker 60'}, 'D_L2': {'room': 'Fern Room 11'}, 'D_L3': {'building': 'West Annex 12'},
    'E_L1': {'city': 'Mereford 2'}, 'E_L2': {'hub': 'Heron Hub 3'}, 'E_L3': {'day': 'Tuesday'},
    'F_L1': {'shelf': 'Amber Shelf'}, 'F_L2': {'folder': 'Folder 76'}, 'F_L3': {'shelf': 'Amber Shelf'},
    'G_L1': {'site': 'Harbor Lodge'}, 'G_L2': {'site': 'Meadow Lodge'},
    'G_L3': {'site': 'Meadow Lodge', 'current_site': 'Harbor Lodge'},
    'H_L1': {'desk': 'Elm Desk'}, 'H_L2': {'desk': 'Ash Desk'}, 'H_L3': {'desk': 'Ash Desk'},
}
DEMANDS = {
    'A': 'Direct retrieval; levels add competing boxes, not additional logical steps.',
    'B': 'Multi-component retrieval/integration; answer length and number of joins also change.',
    'C': 'Inclusive validity-interval selection; L2 tests an update boundary and L3 the preceding day.',
    'D': 'Relational evidence chain; unique terminal entity may permit a shortcut.',
    'E': 'Current residence selection with relevant, true past history; later levels follow hub links.',
    'F': 'Entity/role disambiguation; recurring archivist and shelf templates may permit shortcuts.',
    'G': 'Question-time versus evaluation-time selection; L3 requests both historical and current sites.',
    'H': 'Context-bound parcel reference; only L3 contains a competing parcel.',
}


def revise(parent, parent_file_sha256):
    """Three pre-inference content corrections; never mutate the parent."""
    validate_dataset(parent)
    revised = deepcopy(parent)
    revised['version'] = VERSION
    revised['parent'] = {'version': PARENT_VERSION, 'file_sha256': parent_file_sha256}
    revisions = []
    questions = {
        'p1b_B_L2': "Name Emery Lake's workshop and role in it. Also name the workshop's meeting place.",
        'p1b_B_L3': "Name Finley Ash's workshop and role in it. Also name the workshop's meeting place and the entrance to that place.",
    }
    for c in revised['cases']:
        before = deepcopy(c)
        reason = None
        if c['case_id'] in questions:
            c['question'] = questions[c['case_id']]
            reason = 'Resolve the ambiguous attachment of its; retain the same requested answer components.'
        elif c['case_id'] == 'p1b_E_L3':
            assert date.fromisoformat(REFERENCE).strftime('%A') == 'Thursday'
            next(f for f in c['facts'] if f['fact_id'].endswith('_f05'))['value'] = 'Tuesday'
            c['trusted_evidence'] = render_evidence(c['facts'])
            c['expected_answer']['components']['day'] = 'Tuesday'
            reason = 'Remove an accidental match between the hub opening day and the weekday of the reference date.'
        if reason:
            changes = {k: {'before': before[k], 'after': c[k]} for k in before if before[k] != c[k]}
            revisions.append({'case_id': c['case_id'], 'reason': reason, 'changes': changes,
                              'before_case_sha256': canonical_hash(before), 'after_case_sha256': canonical_hash(c)})
    return revised, revisions


def parse_evidence(text):
    """Read the rendered English ledger independently of the query/oracle code."""
    lines = text.splitlines()
    if not lines or lines[0] != 'Verified fictional records. Dates use inclusive validity intervals; an absent end means ongoing.':
        raise ValueError('Unexpected evidence header')
    records = []
    for line in lines[1:]:
        match = re.fullmatch(r'(p1b_[A-H]_L[123]_f\d+): (.+) — ([a-z ]+): (.+)\. Valid (\d{4}-\d{2}-\d{2}) through (ongoing|\d{4}-\d{2}-\d{2})\.', line)
        if not match:
            raise ValueError('Unparseable evidence line')
        fid, subject, relation, value, start, end = match.groups()
        records.append({'fact_id': fid, 'subject': subject, 'relation': relation.replace(' ', '_'),
                        'value': value, 'valid_from': start, 'valid_until': None if end == 'ongoing' else end})
    return records


def independent_reference(c):
    """Separate family-specific derivation; never consume query or expected_answer."""
    facts = parse_evidence(c['trusted_evidence'])
    proof = []

    def lookup(subject, relation, at=REFERENCE):
        at_date = date.fromisoformat(at)
        rows = [f for f in facts if f['subject'] == subject and f['relation'] == relation
                and date.fromisoformat(f['valid_from']) <= at_date
                and (f['valid_until'] is None or at_date <= date.fromisoformat(f['valid_until']))]
        if len(rows) != 1:
            raise ValueError('Independent reference is missing or ambiguous')
        f = rows[0]
        proof.append({'fact_id': f['fact_id'], 'at': at, 'source_quote': next(
            line for line in c['trusted_evidence'].splitlines() if line.startswith(f['fact_id'] + ':'))})
        return f['value']

    family, level, name = c['family'], c['designed_complexity_level'], c['speaker_name']
    if family == 'A':
        answer = {'room': lookup(name + ' archive box', 'storage_room')}
    elif family == 'B':
        answer = {'workshop': lookup(name, 'workshop'), 'role': lookup(name, 'workshop_role')}
        if level >= 2:
            answer['place'] = lookup(answer['workshop'], 'meeting_place')
        if level == 3:
            answer['entrance'] = lookup(answer['place'], 'entrance')
    elif family == 'C':
        answer = {'counter': lookup(name, 'collection_counter', '2027-04-05' if level == 1 else '2027-04-10')}
        if level == 3:
            answer['previous_counter'] = lookup(name, 'collection_counter', '2027-04-09')
    elif family == 'D':
        value = lookup(lookup(name, 'assigned_crate'), 'stored_in')
        key = 'locker'
        if level >= 2:
            value, key = lookup(value, 'located_in'), 'room'
        if level == 3:
            value, key = lookup(value, 'building'), 'building'
        answer = {key: value}
    elif family == 'E':
        value, key = lookup(name, 'residence'), 'city'
        if level >= 2:
            value, key = lookup(value, 'collection_hub'), 'hub'
        if level == 3:
            value, key = lookup(value, 'opening_day'), 'day'
        answer = {key: value}
    elif family == 'F':
        if level == 1:
            person = f'Morgan North ({c["case_id"]}-N)'
        else:
            people = [f['subject'] for f in facts if f['relation'] == 'project_role' and f['value'] == 'archivist'
                      and f['valid_from'] <= REFERENCE <= (f['valid_until'] or '9999-12-31')]
            if len(people) != 1:
                raise ValueError('Ambiguous archivist')
            person = people[0]
            lookup(person, 'project_role')
        if level == 1:
            answer = {'shelf': lookup(person, 'shelf')}
        else:
            folder = lookup(person, 'folder')
            answer = {'folder': folder} if level == 2 else {'shelf': lookup(folder, 'shelf')}
    elif family == 'G':
        answer = {'site': lookup(name, 'pickup_site', REFERENCE if level == 1 else '2027-03-20')}
        if level == 3:
            answer['current_site'] = lookup(name, 'pickup_site')
    elif family == 'H':
        matches = re.findall(r'Please focus on (Parcel \d+)\.', '\n'.join(c['context']))
        if len(matches) != 1:
            raise ValueError('Context lacks a unique focus')
        entity = matches[0]
        if level >= 2:
            entity = lookup(entity, 'recipient')
        answer = {'desk': lookup(entity, 'delivery_desk', '2027-04-10' if level == 3 else REFERENCE)}
    else:
        raise ValueError('Unknown family')
    return answer, proof


def audit(dataset):
    if dataset['version'] != VERSION:
        raise ValueError('Wrong revision')
    # Secondary reuse of original engineering invariants; the persisted version
    # is never relabelled or overwritten. Independent derivation follows below.
    legacy_view = deepcopy(dataset)
    legacy_view['version'] = PARENT_VERSION
    secondary = validate_dataset(legacy_view)
    rows = []
    for c in dataset['cases']:
        short = c['case_id'].removeprefix('p1b_')
        answer, proof = independent_reference(c)
        if answer != EXPECTED[short] or answer != c['expected_answer']['components']:
            raise ValueError('Independent answer disagreement: ' + c['case_id'])
        if parse_evidence(c['trusted_evidence']) != c['facts']:
            raise ValueError('Rendered evidence/ledger disagreement')
        if [p['fact_id'] for p in proof] != c['expected_answer']['proof_fact_ids']:
            raise ValueError('Independent support path disagreement')
        temporal = c['family'] in 'CEG' or (c['family'] == 'H' and c['designed_complexity_level'] > 1)
        expected_app = dict(factual_consistency=True, temporal_consistency=temporal,
                            response_relevance=True, conversational_coherence=True,
                            linguistic_fidelity=False, behavioral_fidelity=False)
        if c['applicability'] != expected_app:
            raise ValueError('Applicability disagreement')
        hist = c['historical_source_fact']
        if hist['subject'] != c['speaker_name'] or f"{c['speaker_name']}: I live in {hist['value']}." not in c['history_dialogue']:
            raise ValueError('Historical speaker/source disagreement')
        if c['speaker_name'] not in '\n'.join(c['context']) or c['supplemental_fact'] != c['speaker_name'] + ' owns a woven bookmark.':
            raise ValueError('Speaker identity mismatch')
        if f"Historical dialogue ({c['history_date']}):" not in c['history_dialogue']:
            raise ValueError('Historical timestamp mismatch')
        if c['family'] == 'E':
            past = next(f for f in c['facts'] if f['relation'] == 'residence' and f['valid_from'] == '2026-01-01')
            if any(past[k] != hist[k] for k in ('subject', 'relation', 'value', 'valid_from', 'valid_until')):
                raise ValueError('Past residence contradiction')
        prompts = {k: prompt(c, k) for k in FACTORIAL}
        for condition, bits in FACTORIAL.items():
            text = prompts[condition]
            expected_additions = '\n'.join(t for on, t in zip(bits, [
                'Speaker style profile: ' + c['style_only'], 'Additional fact: ' + c['supplemental_fact'], c['history_dialogue']]) if on)
            actual_additions = text.split('\n\nADDITIONAL CONTEXT:\n', 1)[1].split('\n\nRECENT CONVERSATION:\n', 1)[0]
            if expected_additions != actual_additions or text.count(c['trusted_evidence']) != 1:
                raise ValueError('Factor routing/evidence mismatch')
            suffix = '\n\nRECENT CONVERSATION:\n' + '\n'.join(c['context']) + '\n\nUser: ' + c['question'] + '\nAssistant:'
            if not text.endswith(suffix):
                raise ValueError('Question or context changed')
        risks = [DEMANDS[c['family']],
                 'Human question/reference and semantic leakage review remains OPEN.',
                 'Style is nested within speaker; supplementary bookmark fact is uniform; no fidelity ground truth.']
        if c['case_id'] in ('p1b_H_L1', 'p1b_H_L2'):
            risks.append('Only one parcel: context binding is explicit but context necessity is not empirically established.')
        if c['case_id'] == 'p1b_H_L3':
            risks.append('Recent context ends with a User turn followed by the final User question; preserve and review this format.')
        rows.append({'case_id': c['case_id'], 'persona_id': c['persona_id'], 'family': c['family'],
                     'analytic_status': 'PASS', 'semantic_acceptance': 'OPEN',
                     'review_type': 'tool_assisted_analytic_validation_not_human_review',
                     'answer_components': answer, 'dated_support': proof,
                     'temporal_interpretation': 'Use each proposition date below; the global reference does not invalidate explicitly past questions.',
                     'applicability': expected_app, 'construction_checks': {k: 'PASS' for k in CHECKS if k not in ('question_clear', 'demand_description_appropriate')},
                     'human_checks_remaining': list(CHECKS), 'risks': risks,
                     'evidence_sha256': hash_text(c['trusted_evidence']), 'question_sha256': hash_text(c['question']),
                     'context_sha256': canonical_hash(c['context']), 'answer_sha256': canonical_hash(c['expected_answer']),
                     'prompt_sha256': {k: hash_text(v) for k, v in prompts.items()}})
    return {'version': 'p1b_independent_analytic_audit_v1', 'status': 'PASS', 'case_count': len(rows),
            'scope': 'Offline source, answer and routing checks; not independent human review or model discrimination.',
            'cases': rows, 'secondary_engineering_validation': secondary,
            'human_review': 'OPEN', 'empirical_discrimination': 'UNTESTED', 'new_generations': 0}


def review_rows(dataset, validation, dataset_sha256):
    rows = []
    for c, a in zip(dataset['cases'], validation['cases']):
        row = {'review_version': 'p1b_stimulus_review_v2', 'dataset_version': VERSION, 'dataset_sha256': dataset_sha256,
               'case_id': c['case_id'], 'persona_id': c['persona_id'], 'speaker': c['speaker_name'],
               'task_family': c['task_family'], 'designed_level': c['designed_complexity_level'],
               'empirical_difficulty': 'UNTESTED', 'trusted_evidence': c['trusted_evidence'],
               'current_question': c['question'], 'fixed_context': '\n'.join(c['context']),
               'evaluation_reference': c['evaluation_date'], 'expected_answer': canonical_text(a['answer_components']),
               'dated_evidence_chain': canonical_text(a['dated_support']), 'temporal_interpretation': a['temporal_interpretation'],
               'active_style': c['style_only'], 'supplemental_fact': c['supplemental_fact'], 'dated_history': c['history_dialogue'],
               'applicability': canonical_text(c['applicability']), 'demand_and_risks': '\n'.join(a['risks']),
               'validation_questions': '; '.join(CHECKS)}
        row.update({'check_' + k: '' for k in CHECKS})
        row.update({k: '' for k in ('researcher_decision', 'reviewer_id', 'review_method', 'reviewed_utc', 'evidence_quotations', 'reviewer_notes')})
        rows.append(row)
    return rows


def canonical_text(value):
    import json
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def validate_reviews(master, submitted):
    """Reject partial, duplicate or changed stimuli; never manufacture approval."""
    by_id = {r['case_id']: r for r in master}
    if len(by_id) != 24 or len(submitted) != 24 or len({r['case_id'] for r in submitted}) != 24:
        raise ValueError('Expected 24 unique reviewed case IDs')
    mutable = {'check_' + k for k in CHECKS} | {'researcher_decision', 'reviewer_id', 'review_method', 'reviewed_utc', 'evidence_quotations', 'reviewer_notes'}
    accepted = 0
    for r in submitted:
        original = by_id.get(r['case_id'])
        if original is None or r.keys() != original.keys():
            raise ValueError('Unknown ID or schema mismatch')
        if any(r[k] != original[k] for k in r.keys() - mutable):
            raise ValueError('Non-annotation field changed')
        if any(r['check_' + k] not in ('PASS', 'FAIL', 'UNCERTAIN', 'NOT_APPLICABLE') for k in CHECKS):
            raise ValueError('Missing or invalid judgment')
        if not r['reviewer_id'].strip() or not r['review_method'].strip():
            raise ValueError('Reviewer identity and method required')
        if r['reviewed_utc']:
            datetime.fromisoformat(r['reviewed_utc'].replace('Z', '+00:00'))
        if r['researcher_decision'] not in ('ACCEPT', 'REVISION_REQUIRED', 'UNCERTAIN'):
            raise ValueError('Invalid researcher decision')
        if r['researcher_decision'] == 'ACCEPT':
            if any(r['check_' + k] != 'PASS' for k in CHECKS):
                raise ValueError('ACCEPT conflicts with an unresolved or inapplicable core check')
            accepted += 1
        if any(r['check_' + k] != 'PASS' for k in CHECKS) and not r['reviewer_notes'].strip():
            raise ValueError('Unresolved judgments require explanatory notes')
    return {'reviewed_records': 24, 'accepted': accepted, 'all_accepted': accepted == 24,
            'timestamp_requirement': 'Optional; no date inferred', 'inference_authorized': False}


def requests(dataset, seed=ORDER_SEED):
    rng = random.Random(seed)
    cases = list(dataset['cases'])
    rng.shuffle(cases)
    rows = []
    for c in cases:
        cells = list(FACTORIAL)
        rng.shuffle(cells)
        for condition in cells:
            text = prompt(c, condition)
            rows.append({'request_id': f'P1B-CAL1-{len(rows)+1:03d}', 'order': len(rows)+1,
                         'case_id': c['case_id'], 'persona_id': c['persona_id'], 'family': c['family'],
                         'condition': condition, 'factors': dict(zip('SFH', FACTORIAL[condition])),
                         'prompt_template_version': TEMPLATE, 'prompt': text, 'prompt_sha256': hash_text(text),
                         'trusted_evidence_sha256': hash_text(c['trusted_evidence']),
                         'question_sha256': hash_text(c['question']), 'context_sha256': canonical_hash(c['context']),
                         'evaluation_reference_sha256': canonical_hash(c['expected_answer']),
                         'applicability': c['applicability'], 'input_token_ids': None, 'input_token_count': None,
                         'tokenizer_preflight': 'PENDING', 'context_fit': 'PENDING', 'executed': False})
    return rows


def contrast_weights():
    out = {'C1-C0': {c: float(c == 'C1') - float(c == 'C0') for c in FACTORIAL},
           'C3-C0': {c: float(c == 'C3') - float(c == 'C0') for c in FACTORIAL}}
    for label in ('S', 'F', 'H', 'SxF', 'SxH', 'FxH', 'SxFxH'):
        axes = [list('SFH').index(a) for a in label.split('x')]
        # Average main effect; average difference-in-differences; third difference.
        out[label] = {c: math.prod(2*bits[a]-1 for a in axes) / 2**(3-len(axes)) for c, bits in FACTORIAL.items()}
    return out


def precision_plan(dataset):
    rows = []
    for metric in ('factual_consistency', 'temporal_consistency'):
        counts = Counter(c['persona_id'] for c in dataset['cases'] if c['applicability'][metric])
        n, sum_m2 = sum(counts.values()), sum(m*m for m in counts.values())
        for contrast, weights in contrast_weights().items():
            for response_correlation in (.2, .5, .8):
                for contrast_icc in (0., .2, .5):
                    for comparisons in (1, 9):
                        variance = .25*(1-response_correlation)*sum(w*w for w in weights.values())
                        effective_n = n*n/((1-contrast_icc)*n + contrast_icc*sum_m2)
                        z = NormalDist().inv_cdf(1-.05/(2*comparisons))
                        rows.append({'metric': metric, 'contrast': contrast, 'cases': n, 'speakers': len(counts),
                                     'cluster_sizes': dict(counts), 'response_correlation_assumption': response_correlation,
                                     'contrast_icc_assumption': contrast_icc, 'comparisons': comparisons,
                                     'variance_assumption': variance, 'effective_n': effective_n,
                                     'normal_approximation_half_width': z*math.sqrt(variance/effective_n)})
    return {'version': 'p1b_calibration_precision_v1', 'status': 'ASSUMPTION_BASED_NOT_OBSERVED',
            'formula': 'Var(case contrast)=0.25*(1-r)*sum(w^2); n_eff=N^2/[(1-rho)*N+rho*sum(m_i^2)]',
            'assumptions': 'Exchangeable within-case binary covariance; equal marginal variance 0.25; exchangeable speaker contrast ICC; complete scoring.',
            'limitations': 'Normal approximation is optimistic with 12 or 9 speakers; not an achieved CI or power estimate. Missing ratings require separate bounds.',
            'contrast_weights': contrast_weights(), 'rows': rows}
