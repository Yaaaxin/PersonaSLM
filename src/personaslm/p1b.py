"""Offline, proposed P1b stimulus design. No model client or response evaluator.

The symbolic oracle validates supplied fact-ledger queries, not arbitrary English
responses. Human verification of the question/oracle correspondence stays OPEN.
"""
from collections import Counter
from copy import deepcopy
from datetime import date
import hashlib
import json
import math
from statistics import NormalDist

from .conditioning import FACTORIAL

VERSION = 'p1b_development_proposed_v1'
TEMPLATE = 'p1b_transcript_proposed_v1'
REFERENCE = '2027-04-15'  # Fictional evaluation date, never an execution date.
FAMILIES = dict(zip('ABCDEFGH', [
    'factual_retrieval', 'related_facts', 'validity_intervals', 'relational_reasoning',
    'relevant_history', 'entity_disambiguation', 'historical_vs_current', 'context_followup']))
NAMES = ['Arden Vale', 'Briar Moss', 'Cleo Reed', 'Dara Wells', 'Emery Lake', 'Finley Ash',
         'Gale Rowan', 'Hollis Fern', 'Indigo Shaw', 'Jules Finch', 'Kit Sorrel', 'Linden West']
STYLES = [
    ('brevity', 'Uses compact sentences while retaining requested details.'),
    ('formality', 'Uses a formal register and avoids contractions.'),
    ('lexical_preference', 'Prefers everyday vocabulary to specialist synonyms.'),
    ('rhythm', 'Usually presents related clauses as separate sentences.'),
    ('pragmatics', 'Usually acknowledges the request briefly before answering.'),
    ('lexical_preference', 'Prefers precise nouns rather than informal substitutes.'),
    ('brevity', 'Usually answers in short sentences without redundant restatement.'),
    ('formality', 'Uses a conversational register with ordinary contractions.'),
    ('rhythm', 'Usually connects related clauses within a sentence.'),
    ('pragmatics', 'Usually begins directly with the requested information.'),
    ('formality', 'Uses polite, matter-of-fact phrasing.'),
    ('rhythm', 'Usually alternates a short opening clause with a fuller sentence.'),
]


def hash_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def canonical_hash(value):
    return hash_text(json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')))


def active(fact, at):
    date.fromisoformat(at)
    return fact['valid_from'] <= at <= (fact['valid_until'] or '9999-12-31')


def render_evidence(facts):
    return ('Verified fictional records. Dates use inclusive validity intervals; an absent end means ongoing.\n'
            + '\n'.join(f"{f['fact_id']}: {f['subject']} — {f['relation'].replace('_', ' ')}: {f['value']}. "
                        f"Valid {f['valid_from']} through {f['valid_until'] or 'ongoing'}." for f in facts))


def solve(case):
    """Resolve explicit unique joins/date filters; refuse missing/ambiguous facts."""
    values, proof, terminal = {}, [], []
    for step in case['query']['steps']:
        at = step.get('at', REFERENCE)
        if 'find_subject' in step:
            selector = step['find_subject']
            candidates = [f for f in case['facts'] if f['relation'] == selector['relation']
                          and f['value'] == selector['value'] and active(f, at)]
            field = 'subject'
        else:
            subject = step['subject']
            if isinstance(subject, dict):
                if 'ref' in subject:
                    subject = values[subject['ref']]
                else:
                    binding = case['context_bindings'][subject['context_key']]
                    if binding['source_quote'] not in '\n'.join(case['context']) or binding['value'] not in binding['source_quote']:
                        raise ValueError('Context binding lacks a verbatim source')
                    subject = binding['value']
            candidates = [f for f in case['facts'] if f['subject'] == subject
                          and f['relation'] == step['relation'] and active(f, at)]
            field = 'value'
        if len(candidates) != 1:
            raise ValueError('Query requires exactly one supported fact per step')
        fact = candidates[0]
        values[step['key']] = fact[field]
        proof.append(fact['fact_id'])
        if step['key'] in case['query']['answer_keys']:
            terminal.append(fact['fact_id'])
    return {'components': {key: values[key] for key in case['query']['answer_keys']},
            'proof_fact_ids': list(dict.fromkeys(proof)), 'answer_fact_ids': terminal}


def build_case(index, family, level):
    # Twelve speakers, two cases each; shift the second block to avoid a single
    # difficulty level being constant within speaker. No response-dependent choice.
    p = index if index < 12 else (index - 12 + 1) % 12
    name, pid = NAMES[p], f'p1b_persona_{p+1:02d}'
    cid = f'p1b_{family}_L{level}'
    facts, steps, answers = [], [], []
    context = [f'User: We are checking the supplied records with {name}.',
               'Assistant: Which record should I check?']
    bindings = {}

    def add(subject, relation, value, start='2027-01-01', end=None):
        fid = f'{cid}_f{len(facts)+1:02d}'
        facts.append(dict(fact_id=fid, subject=subject, relation=relation, value=value,
                          valid_from=start, valid_until=end))
        return fid

    def lookup(key, subject, relation, at=REFERENCE, answer=True):
        steps.append(dict(key=key, subject=subject, relation=relation, at=at))
        if answer:
            answers.append(key)

    old_city, current_city = f'Alderwick {p+1}', f'Mereford {p+1}'
    history_date = '2026-11-15'
    history_fact = dict(fact_id=f'{pid}_past_residence', subject=name, relation='residence', value=old_city,
                        valid_from='2026-01-01', valid_until='2026-12-31')
    history = (f'Historical dialogue ({history_date}):\nUser: Where are you living?\n'
               f'{name}: I live in {old_city}.')
    if family == 'A':
        target = f'{name} archive box'
        add(target, 'storage_room', f'Juniper Room {p+1}')
        for k in range(level - 1):
            add(f'{name} supply box {k+1}', 'storage_room', f'Willow Room {k+1}')
        lookup('room', target, 'storage_room')
        question = f'Which room stores the archive box assigned to {name}?'
    elif family == 'B':
        add(name, 'workshop', f'Bookbinding Group {p+1}')
        add(name, 'workshop_role', 'materials coordinator')
        lookup('workshop', name, 'workshop', answer=True)
        lookup('role', name, 'workshop_role')
        if level >= 2:
            add(f'Bookbinding Group {p+1}', 'meeting_place', f'Cedar Hall {p+1}')
            lookup('place', {'ref': 'workshop'}, 'meeting_place')
        if level == 3:
            add(f'Cedar Hall {p+1}', 'entrance', 'east entrance')
            lookup('entrance', {'ref': 'place'}, 'entrance')
        question = f'Name {name}\'s workshop and role' + (', its meeting place' if level >= 2 else '') + (', and that place\'s entrance' if level == 3 else '') + '.'
    elif family == 'C':
        add(name, 'collection_counter', 'Maple Counter', '2027-01-01', '2027-03-31')
        add(name, 'collection_counter', 'Birch Counter', '2027-04-01', '2027-04-09')
        add(name, 'collection_counter', 'Cedar Counter', '2027-04-10')
        at = '2027-04-05' if level == 1 else '2027-04-10'
        lookup('counter', name, 'collection_counter', at)
        question = f'Which collection counter applies to {name} on {at}?'
        if level == 3:
            lookup('previous_counter', name, 'collection_counter', '2027-04-09')
            question = f'Which counter applies to {name} on 2027-04-10, and which applied on the preceding day?'
    elif family == 'D':
        add(name, 'assigned_crate', f'Crate {p+31}')
        add(f'Crate {p+31}', 'stored_in', f'Locker {p+51}')
        lookup('crate', name, 'assigned_crate', answer=False)
        lookup('locker', {'ref': 'crate'}, 'stored_in', answer=(level == 1))
        if level >= 2:
            add(f'Locker {p+51}', 'located_in', f'Fern Room {p+1}')
            lookup('room', {'ref': 'locker'}, 'located_in', answer=(level == 2))
        if level == 3:
            add(f'Fern Room {p+1}', 'building', f'West Annex {p+1}')
            lookup('building', {'ref': 'room'}, 'building')
        question = f'Which { {1:"locker",2:"room",3:"building"}[level]} contains the crate assigned to {name}?'
    elif family == 'E':
        add(name, 'residence', old_city, '2026-01-01', '2026-12-31')
        add(name, 'residence', current_city, '2027-01-01')
        lookup('city', name, 'residence', answer=(level == 1))
        if level >= 2:
            add(current_city, 'collection_hub', f'Heron Hub {p+1}')
            add(old_city, 'collection_hub', f'Plover Hub {p+1}')
            lookup('hub', {'ref': 'city'}, 'collection_hub', answer=(level == 2))
        if level == 3:
            add(f'Heron Hub {p+1}', 'opening_day', 'Thursday')
            add(f'Plover Hub {p+1}', 'opening_day', 'Monday')
            lookup('day', {'ref': 'hub'}, 'opening_day')
        question = {1:f'Where does {name} live on {REFERENCE}?',
                    2:f'Which collection hub serves {name}\'s residence on {REFERENCE}?',
                    3:f'On which day does the hub serving {name}\'s residence on {REFERENCE} open?'}[level]
    elif family == 'F':
        a, b = f'Morgan North ({cid}-N)', f'Morgan South ({cid}-S)'
        add(a, 'project_role', 'archivist'); add(b, 'project_role', 'treasurer')
        if level == 1:
            add(a, 'shelf', 'Amber Shelf'); add(b, 'shelf', 'Violet Shelf')
            lookup('shelf', a, 'shelf')
            question = f'{name} is checking the project: which shelf is assigned to {a}?'
        else:
            steps.append({'key':'person', 'find_subject':{'relation':'project_role','value':'archivist'}})
            add(a, 'folder', f'Folder {p+71}'); add(b, 'folder', f'Folder {p+91}')
            lookup('folder', {'ref':'person'}, 'folder', answer=(level == 2))
            if level == 3:
                add(f'Folder {p+71}', 'shelf', 'Amber Shelf'); add(f'Folder {p+91}', 'shelf', 'Violet Shelf')
                lookup('shelf', {'ref':'folder'}, 'shelf')
            question = f'{name} needs the {"folder assigned to" if level==2 else "shelf holding the folder assigned to"} the archivist. Which is it?'
    elif family == 'G':
        add(name, 'pickup_site', 'Orchard Lodge', '2027-01-01', '2027-02-28')
        add(name, 'pickup_site', 'Meadow Lodge', '2027-03-01', '2027-03-31')
        add(name, 'pickup_site', 'Harbor Lodge', '2027-04-01')
        at = REFERENCE if level == 1 else '2027-03-20'
        lookup('site', name, 'pickup_site', at)
        question = f'Which pickup site was valid for {name} on {at}?'
        if level == 3:
            lookup('current_site', name, 'pickup_site')
            question = f'Name {name}\'s pickup site on 2027-03-20 and the different site valid on {REFERENCE}.'
    else:
        parcel = f'Parcel {p+111}'
        quote = f'Please focus on {parcel}.'
        context = [f'User: {name} is arranging delivery. {quote}', 'Assistant: I will check that parcel.']
        bindings['selected_parcel'] = {'value':parcel, 'source_quote':quote}
        if level == 1:
            add(parcel, 'delivery_desk', 'Elm Desk')
            lookup('desk', {'context_key':'selected_parcel'}, 'delivery_desk')
            question = 'Which desk should it go to?'
        else:
            add(parcel, 'recipient', f'Recipient {p+131}')
            add(f'Recipient {p+131}', 'delivery_desk', 'Elm Desk', '2027-01-01', '2027-04-09')
            add(f'Recipient {p+131}', 'delivery_desk', 'Ash Desk', '2027-04-10')
            lookup('recipient', {'context_key':'selected_parcel'}, 'recipient', answer=False)
            at = REFERENCE if level == 2 else '2027-04-10'
            lookup('desk', {'ref':'recipient'}, 'delivery_desk', at)
            question = f'Which desk should it go to on {at}?'
            if level == 3:
                other = f'Parcel {p+151}'
                add(other, 'recipient', f'Recipient {p+171}')
                add(f'Recipient {p+171}', 'delivery_desk', 'Oak Desk')
                context = [f'User: {name} has {other} and {parcel}.',
                           f'Assistant: Which one are we arranging?', f'User: {quote}']
    case = dict(case_id=cid, persona_id=pid, speaker_name=name, family=family, task_family=FAMILIES[family],
                designed_complexity_level=level, empirical_difficulty=None, language='en',
                split='development_only', template_version=TEMPLATE, evaluation_date=REFERENCE,
                facts=facts, trusted_evidence=render_evidence(facts), question=question,
                context=context, context_bindings=bindings, query={'steps':steps,'answer_keys':answers},
                style_axis=STYLES[p][0], style_only=STYLES[p][1],
                supplemental_fact=f'{name} owns a woven bookmark.', history_dialogue=history,
                history_date=history_date, historical_source_fact=history_fact,
                history_relevance='same_residence_attribute' if family == 'E' else 'unrelated_residence',
                applicability={'factual_consistency':True,'temporal_consistency':family in 'CEG' or (family=='H' and level>1),
                               'response_relevance':True,'conversational_coherence':True,
                               'linguistic_fidelity':False,'behavioral_fidelity':False},
                semantic_review_status='OPEN', inference_authorized=False,
                actual_prompt_token_counts=None, matched_controls_status='NOT_PREPARED')
    case['expected_answer'] = solve(case)
    return case


def build_dataset():
    cases = [build_case(3*f+l-1, family, l) for f,family in enumerate(FAMILIES) for l in (1,2,3)]
    return {'version':VERSION, 'status':'PROPOSED_DEVELOPMENT_ONLY', 'language':'en',
            'source_type':'fictional_synthetic', 'formal_protocol':'v1.1', 'adopts_v1_2':False,
            'confirmatory_test':False, 'generation_requests':0,
            'selection_rule':'All 24 family-by-complexity prototypes; no outcome-based inclusion or exclusion.',
            'cases':cases}


def prompt(case, condition):
    s,f,h = FACTORIAL[condition]
    additions = [text for on,text in [(s,'Speaker style profile: '+case['style_only']),
                 (f,'Additional fact: '+case['supplemental_fact']), (h,case['history_dialogue'])] if on]
    # The common prefix/evidence position is identical across all eight cells.
    return (f'CONTINUE THE DIALOGUE. Use the verified records to answer the factual question.\n'
            f'Evaluation reference: {case["evaluation_date"]}.\n\nTRUSTED EVIDENCE:\n{case["trusted_evidence"]}'
            '\n\nADDITIONAL CONTEXT:\n'+'\n'.join(additions)+'\n\nRECENT CONVERSATION:\n'
            +'\n'.join(case['context'])+'\n\nUser: '+case['question']+'\nAssistant:')


def validate_dataset(dataset):
    if dataset['version'] != VERSION or dataset['confirmatory_test'] or dataset['generation_requests'] != 0:
        raise ValueError('Only unexecuted development proposals are accepted')
    cases = dataset['cases']
    if len(cases) != 24 or len({r['case_id'] for r in cases}) != 24:
        raise ValueError('Expected 24 unique prototypes')
    if Counter((r['family'],r['designed_complexity_level']) for r in cases) != Counter((f,l) for f in FAMILIES for l in (1,2,3)):
        raise ValueError('Family/complexity allocation changed')
    if sorted(Counter(r['persona_id'] for r in cases).values()) != [2]*12:
        raise ValueError('Expected twelve two-case speaker clusters')
    rows = []
    for c in cases:
        if c['split'] != 'development_only' or c['language'] != 'en' or c['inference_authorized']:
            raise ValueError('Invalid experimental scope')
        if c['trusted_evidence'] != render_evidence(c['facts']):
            raise ValueError('Evidence text differs from source ledger')
        ids = [f['fact_id'] for f in c['facts']]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate fact IDs')
        for a in c['facts']:
            date.fromisoformat(a['valid_from'])
            if a['valid_until'] and date.fromisoformat(a['valid_until']) < date.fromisoformat(a['valid_from']):
                raise ValueError('Reversed interval')
            for b in c['facts']:
                if a['fact_id'] < b['fact_id'] and (a['subject'],a['relation']) == (b['subject'],b['relation']):
                    if max(a['valid_from'],b['valid_from']) <= min(a['valid_until'] or '9999-12-31',b['valid_until'] or '9999-12-31'):
                        raise ValueError('Overlapping unique-attribute facts')
        answer = solve(c)
        if answer != c['expected_answer']:
            raise ValueError('Unsupported ground truth')
        if not active(c['historical_source_fact'],c['history_date']):
            raise ValueError('False dated historical assertion')
        for value in answer['components'].values():
            if any(value.casefold() in c[k].casefold() for k in ['style_only','supplemental_fact','history_dialogue']):
                raise ValueError('Expected answer leaked through intervention')
        removal_checks = 0
        for fid in answer['proof_fact_ids']:
            deleted = deepcopy(c); deleted['facts'] = [f for f in deleted['facts'] if f['fact_id'] != fid]
            try:
                solve(deleted)
            except ValueError:
                removal_checks += 1
            else:
                raise ValueError('Declared supporting fact was unnecessary')
        changed = deepcopy(c)
        next(f for f in changed['facts'] if f['fact_id'] == answer['answer_fact_ids'][-1])['value'] = 'Alternative verified value'
        if solve(changed)['components'] == answer['components']:
            raise ValueError('Oracle did not respond to changed evidence')
        strings = {condition:prompt(c,condition) for condition in FACTORIAL}
        prefix = next(iter(strings.values())).split('\n\nADDITIONAL CONTEXT:')[0]
        if any(not s.startswith(prefix) or not s.endswith('User: '+c['question']+'\nAssistant:') for s in strings.values()):
            raise ValueError('Shared input changed')
        rows.append({'case_id':c['case_id'],'persona_id':c['persona_id'],'family':c['family'],
                     'level':c['designed_complexity_level'],'supporting_facts':len(answer['proof_fact_ids']),
                     'evidence_removal_checks':removal_checks,'evidence_change_checks':1,
                     'fact_count':len(c['facts']),'temporal_applicable':c['applicability']['temporal_consistency'],
                     'evidence_sha256':hash_text(c['trusted_evidence']),'question_sha256':hash_text(c['question']),
                     'context_sha256':canonical_hash(c['context']), 'answer_sha256':canonical_hash(answer),
                     'prompt_sha256':{k:hash_text(v) for k,v in strings.items()},
                     'tokenizer_validation':'NOT_EXECUTED', 'human_semantic_review':'OPEN'})
    return {'version':'p1b_offline_validation_v1','status':'PASS','scope':'Symbolic source/query and construction validation only',
            'cases':rows,'prompt_count':len(cases)*8,'empirical_discrimination':'UNTESTED',
            'human_review':'OPEN','actual_tokenization':'NOT_EXECUTED','new_generation_requests':0}


def precision(speakers, cases_per_speaker, discordance, icc, difference=0.0, comparisons=1):
    """Normal planning approximation for paired binary differences, not a power claim."""
    if speakers < 2 or cases_per_speaker < 1 or not 0 <= icc <= 1 or comparisons < 1:
        raise ValueError('Invalid allocation')
    if not abs(difference) <= discordance <= 1:
        raise ValueError('Discordance must be at least absolute paired difference')
    n = speakers*cases_per_speaker
    de = 1+(cases_per_speaker-1)*icc
    z = NormalDist().inv_cdf(1-.05/(2*comparisons))
    return {'speakers':speakers,'cases_per_speaker':cases_per_speaker,'cases':n,
            'discordance_assumption':discordance,'paired_difference_assumption':difference,
            'icc_of_case_differences':icc,'comparisons':comparisons,'design_effect':de,
            'effective_case_count':n/de,'half_width':z*math.sqrt((discordance-difference**2)*de/n)}
