"""P1 development-wave inputs and measurement routing; P0 policies unchanged."""
from collections import Counter
from dataclasses import dataclass
from datetime import date
import random
import re
from types import SimpleNamespace

from .conditioning import FACTORIAL, build_prompt
from .evaluation_policy import evaluate_response, VERSION as POLICY
from .response_status import classify_response, text_hash
from .schemas import Fact, ENDPOINTS

VERSION = 'p1_development_v1'
ORDER_SEED = 713042
ROUTING_VERSION = 'p1_endpoint_routing_v1'


@dataclass(frozen=True)
class PilotCase:
    record: dict

    def __getattr__(self, name):
        if name == 'facts':
            return tuple(Fact.from_dict(f) for f in self.record['facts'])
        if name == 'context':
            return tuple(self.record['context'])
        return self.record[name]


def validate_dataset(dataset):
    """Fail before inference for routing, chronology or shared-input violations."""
    if dataset['version'] != VERSION or dataset['language'] != 'en' or dataset['source_type'] != 'fictional_synthetic':
        raise ValueError('P1 requires the versioned English synthetic development dataset')
    rows = dataset['cases']; profiles = {p['persona_id']: p for p in dataset['personas']}
    if len(profiles) != 12 or len(rows) != 48 or len({r['case_id'] for r in rows}) != 48:
        raise ValueError('Expected 12 unique personas and 48 unique cases')
    if len({p['style_only'] for p in profiles.values()}) != 12:
        raise ValueError('Distinct style realizations required')
    reports = []
    for pid in profiles:
        if Counter(r['family'] for r in rows if r['persona_id'] == pid) != dict.fromkeys('ABCD', 1):
            raise ValueError('Every speaker needs each of four families')
    for row in rows:
        c = PilotCase(row); profile = profiles[c.persona_id]
        if c.split != 'p1_development_only' or c.language != 'en' or not c.speaker_name.isascii():
            raise ValueError('Unexpected split or language')
        if c.speaker_name != profile['speaker_name'] or c.style_only != profile['style_only']:
            raise ValueError('Speaker or style identity mismatch')
        if set(c.applicability) != set(ENDPOINTS) or any(type(v) is not bool for v in c.applicability.values()):
            raise ValueError('Explicit boolean applicability required for all endpoints')
        if c.applicability['factual_consistency'] != (c.family != 'C') or c.applicability['temporal_consistency'] != (c.family in 'AD'):
            raise ValueError('Applicability differs from predeclared family routing')
        facts = c.facts; date.fromisoformat(c.evaluation_date)
        ids = [f.fact_id for f in facts]
        if len(ids) != len(set(ids)):raise ValueError('Duplicate fact ID')
        for a in facts:
            for b in facts:
                if a.fact_id < b.fact_id and a.attribute == b.attribute and a.value != b.value:
                    if a.valid_from <= (b.valid_until or '9999-12-31') and b.valid_from <= (a.valid_until or '9999-12-31'):
                        raise ValueError('Unplanned contradictory fact intervals')
        current = [f for f in facts if f.attribute == 'current_city' and f.active_at(c.evaluation_date)]
        old = [f for f in facts if f.attribute == 'current_city' and f.active_at(c.history_date)]
        if len(current) != 1 or len(old) != 1 or current[0].value == old[0].value:
            raise ValueError('A genuine dated residence update is required')
        if c.history_dialogue != (f'Historical dialogue ({c.history_date}):\nUser: Where were you living then?\n{c.speaker_name}: I was living in {old[0].value} at that time.'):
            raise ValueError('History identity, format or dated content changed')
        if c.speaker_name not in c.question or not c.context or current[0].value not in c.trusted_evidence:
            raise ValueError('Unclear identity/context or missing trusted evidence')
        if c.expected_answer is not None:
            expected_facts = [f for f in facts if f.value == c.expected_answer and f.active_at(c.evaluation_date)]
            if not expected_facts or c.expected_answer not in c.trusted_evidence:
                raise ValueError('Answer lacks currently valid trusted support')
            for text in [c.style_only, c.supplemental_fact, c.history_dialogue]:
                if c.expected_answer.casefold() in text.casefold():
                    raise ValueError('Answer leakage in additional persona material')
        elif c.family != 'C':raise ValueError('Missing factual answer')
        supplemental = next(f for f in facts if f.attribute == 'supplemental_possession')
        if c.supplemental_fact != f'{c.speaker_name} owns {supplemental.value}.':
            raise ValueError('Supplemental assertion is not bound to its source fact')
        evidence_positions = set(); prompts = []
        for condition, (s, f, h) in FACTORIAL.items():
            prompt = build_prompt(c, condition)
            wanted = tuple(block for enabled, block in [(s,'Speaker style profile: '+c.style_only),
                (f,'Additional fact: '+c.supplemental_fact),(h,c.history_dialogue)] if enabled)
            if prompt.additions != wanted:raise ValueError('Factorial routing error')
            if prompt.text.count(prompt.evidence_block) != 1 or prompt.evidence_block != 'TRUSTED EVIDENCE:\n'+c.trusted_evidence:
                raise ValueError('Shared evidence changed')
            if not prompt.text.endswith('RECENT CONVERSATION:\n'+'\n'.join(c.context)+'\n\nUser: '+c.question+'\nAssistant:'):
                raise ValueError('Question or fixed recent context changed')
            evidence_positions.add(prompt.text.index(prompt.evidence_block))
            prompts.append({'condition':condition,'factors':list((s,f,h)),'prompt_sha256':text_hash(prompt.text)})
        if len(evidence_positions) != 1:raise ValueError('Evidence insertion position changed')
        reports.append({'case_id':c.case_id,'persona_id':c.persona_id,'family':c.family,
            'status':'PASS','trusted_evidence_sha256':text_hash(c.trusted_evidence),'question_sha256':text_hash(c.question),
            'context_sha256':text_hash('\n'.join(c.context)),'evidence_character_offset':next(iter(evidence_positions)),
            'prompts':prompts,'applicability':c.applicability})
    return {'version':'p1_manipulation_validation_v1','status':'PASS','cases':reports,
            'prompt_count':len(reports)*8,'scope':'Scripted construction checks and author analytical inspection; not independent human validation or response quality',
            'remaining_confounds':['Style realization is nested in speaker; six categories have two realizations each',
                'Length, lexical material and positions vary in factorial cells',
                'H residence history relevance differs by task family; true old facts are not simultaneous contradictions']}


def wave_order(dataset):
    validate_dataset(dataset)
    selected = [r for r in dataset['cases'] if r['wave1_selected']]
    if len(selected) != 12 or len({r['persona_id'] for r in selected}) != 12 or Counter(r['family'] for r in selected) != dict.fromkeys('ABCD',3):
        raise ValueError('Wave needs 12 speakers, one case each, three cases per family')
    rng = random.Random(ORDER_SEED); selected = sorted(selected,key=lambda r:r['persona_id']);rng.shuffle(selected)
    order = []
    for case in selected:
        conditions = list(FACTORIAL);rng.shuffle(conditions)
        for condition in conditions:
            order.append({'request_id':f"{case['case_id']}__{condition}",'case_id':case['case_id'],
                'persona_id':case['persona_id'],'family':case['family'],'condition':condition,'factors':list(FACTORIAL[condition])})
    return order


def neutral_pool(case, condition):
    """Finite, declared before tokenization; no answer-dependent selection."""
    if condition == 'N_style':
        adjectives = ['', 'speaker-specific ', 'individual ', 'preferred ']
        nouns = ['style information', 'linguistic style information', 'information about linguistic style']
        endings = ['in this profile.', 'in this speaker profile.', 'in the available profile information.']
        return [f'No {adj}{noun} is provided {ending}' for adj in adjectives for noun in nouns for ending in endings]
    if condition == 'N_history':
        questions = ['What does a conversation involve?', 'What does an ordinary conversation involve?']
        replies = ['An exchange of questions and replies.', 'An exchange between the people taking part.',
            'An exchange of questions and replies between people.', 'People taking turns to speak and listen.',
            'People exchanging remarks and listening to one another.', 'An exchange in which people take turns speaking and listening.',
            'An exchange of remarks, with opportunities for questions and replies.', 'People sharing remarks while giving each other a chance to reply.']
        return [f'Historical dialogue ({case.history_date}):\nUser: {q}\n{case.speaker_name}: {a}' for q in questions for a in replies]
    raise ValueError('Only declared neutral families supported')


def evaluate_pilot(case, raw, backend):
    """Keep frozen policies; explicitly route unsupported tasks to human review."""
    if case.family in 'AD':
        view = SimpleNamespace(**case.record)
        view.persona_id = case.speaker_name  # Explicit named subject, not opaque database ID.
        view.facts = case.facts
        result = evaluate_response(view, raw, backend)
        result['factual_support']['assessment_source'] = 'bounded_automated_residence_audit'
        result['factual_support']['assessed'] = result['factual_support']['label'] in ('Correct','Incorrect')
    else:
        boundary = classify_response(raw, backend)
        def manual(endpoint, categorical=False):
            eligible=case.applicability[endpoint]
            return {'label':('Unverifiable' if categorical else 'PENDING') if eligible else 'Not Applicable',
                'rating':None,'reason':'Independent annotation pending' if eligible else 'Predeclared inapplicability',
                'assessment_source':'human_review_pending' if eligible else 'not_applicable','assessed':False}
        result={'policy_version':POLICY,'case_id':case.case_id,'applicability':case.applicability,
            'response_completeness':boundary,'factual_support':manual('factual_consistency',True),
            'temporal_consistency':manual('temporal_consistency',True),'response_relevance':manual('response_relevance'),
            'conversational_coherence':manual('conversational_coherence'),
            'scored_unit':'Observed first reply/prefix; no city scoring on stable facts or open-ended requests',
            'completeness_judgment_supplied':False}
    result['routing_version']=ROUTING_VERSION
    result['persona_id']=case.persona_id
    result['linguistic_fidelity']={'label':'Not Applicable','reason':'No independent reference behavior or fidelity ground truth supplied'}
    result['behavioral_fidelity']={'label':'Not Applicable','reason':'No independent reference behavior or fidelity ground truth supplied'}
    boundary=result['response_completeness']
    if boundary['removed_prefix']+boundary['first_span']['text']+boundary['excluded_tail'] != raw:
        raise ValueError('Parser cannot reconstruct original output')
    return result


def paired_factorial(values):
    """One numeric structural outcome per frozen factorial cell; no missing-cell dropping."""
    if set(values) != set(FACTORIAL):raise ValueError('Complete eight-cell observations required')
    by_factors={FACTORIAL[c]:v for c,v in values.items()}
    main={}
    for axis,name in enumerate('SFH'):
        main[name]=sum((1 if bits[axis] else -1)*v for bits,v in by_factors.items())/4
    interactions={}
    for a,b in [(0,1),(0,2),(1,2)]:
        interactions['SFH'[a]+'x'+'SFH'[b]]=sum((1 if bits[a] else -1)*(1 if bits[b] else -1)*v for bits,v in by_factors.items())/2
    interactions['SxFxH']=sum((1 if s else -1)*(1 if f else -1)*(1 if h else -1)*v for (s,f,h),v in by_factors.items())
    return {'C1-C0':values['C1']-values['C0'],'C3-C0':values['C3']-values['C0'],
        'average_main_effects':main,'difference_in_differences':interactions}
