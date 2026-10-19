"""Typed evidence/admission/component-checking research scaffold; no generation.

Known rule-based engineering, NOT a validated original algorithm. Structured input
is supplied, not extracted by this program. Authored fixtures are not model data.
"""
from dataclasses import dataclass, asdict, replace
from datetime import date
from pathlib import Path
import json
import statistics
import time
import p1d_budget_calibration as io

OUT=Path('docs/validation/p6/escp_offline_v1')

@dataclass(frozen=True)
class Atom:
    source: str
    entity: str
    attribute: str
    value: str
    valid_from: str
    valid_to: str
    asserted_at: str='2048-01-01'
    provenance: str='authored_fixture'
    trust_priority: int=1
    uncertainty: str='KNOWN'
    conflicts: tuple=()

    def __post_init__(self):
        if date.fromisoformat(self.valid_from)>date.fromisoformat(self.valid_to):
            raise ValueError('Reversed validity interval')
        date.fromisoformat(self.asserted_at)

@dataclass(frozen=True)
class Claim:
    component: str
    entity: str
    attribute: str
    value: str
    at: str
    speech_act: str='ANSWER'
    uncertainty: str='KNOWN'

def eligible(a, c, ablate='', as_of=None):
    return (a.uncertainty=='KNOWN' and
            (ablate=='entity' or a.entity==c.entity) and a.attribute==c.attribute and
            (ablate=='time' or a.valid_from<=c.at<=a.valid_to) and
            (as_of is None or a.asserted_at<=as_of))

def verify(evidence, required, claims, *, abstains=False, ablate='', as_of=None):
    """E is a trusted external channel. Atom trust_priority cannot elevate history.

    No closed-world inference from absence. Multiple valid values => uncertainty.
    Required descriptors: component -> (entity, attribute, requested date).
    Claim-level truth and requested component delivery are evaluated separately.
    """
    diagnostics=[]
    for c in claims:
        candidates=[a for a in evidence if eligible(a,c,ablate,as_of)]
        values={a.value for a in candidates}
        if c.uncertainty!='KNOWN':state='INTERPRETATION_UNCERTAIN'
        elif not values:state='UNVERIFIABLE'
        elif len(values)>1 and ablate!='conflict':state='CONFLICT_UNRESOLVED'
        elif c.value in values:state='SUPPORTED'
        else:state='CONTRADICTED'
        diagnostics.append({'claim':asdict(c),'state':state,
            'support_ids':[a.source for a in candidates if a.value==c.value],
            'conflict_ids':[a.source for a in candidates if a.value!=c.value]})
    components={}
    for key,(entity,attribute,at) in required.items():
        matching=[d for d in diagnostics if d['claim']['component']==key and
            d['claim']['entity']==entity and d['claim']['attribute']==attribute and
            d['claim']['at']==at and (ablate=='delivery' or d['claim']['speech_act']=='ANSWER')]
        components[key]={'present':bool(matching),'supported':bool(matching) and
            all(d['state']=='SUPPORTED' for d in matching)}
    complete=bool(components) and all(c['present'] for c in components.values())
    supported=bool(components) and all(c['supported'] for c in components.values())
    all_claims_supported=bool(diagnostics) and all(d['state']=='SUPPORTED' for d in diagnostics)
    return {'claims':diagnostics,'components':components,'delivered':complete,
        'supported_task':supported and all_claims_supported and not abstains,
        'abstention':abstains,'all_claims_supported':all_claims_supported,
        'scalar_reliability_score':None}

def admit(evidence, history, required, style, behavior, personal_facts=()):
    """Conservative typed channels. No execution of untrusted text instructions."""
    answer=[];archive=[];quarantine=[]
    for h in history:
        targets=[(key,at) for key,(entity,attr,at) in required.items()
                 if (entity,attr)==(h.entity,h.attribute)]
        if not targets:archive.append(h.source);continue
        state=[]
        for key,at in targets:
            if h.uncertainty!='KNOWN':state.append('unknown');continue
            if not h.valid_from<=at<=h.valid_to:state.append('archive');continue
            d=verify(evidence,{},[Claim(key,h.entity,h.attribute,h.value,at)])['claims'][0]
            state.append('answer' if d['state']=='SUPPORTED' else 'quarantine')
        if 'quarantine' in state or 'unknown' in state:quarantine.append(h.source)
        elif 'answer' in state:answer.append(h.source)
        else:archive.append(h.source)
    # Unstructured personal facts need their own semantic review; no automatic truth admission.
    return {'trusted_evidence_ids':[a.source for a in evidence],
        'answer_supporting_history':answer,'dated_non_authoritative_archive':archive,
        'quarantined_history':quarantine,'style':list(style),'behavior':list(behavior),
        'personal_facts_pending_scope_check':list(personal_facts)}

def simple_rule_reference(evidence, required, claims, abstains=False):
    """Independently written straightforward declarative checker, same information.

    This is the strongest fair simple comparator, not an independent annotator.
    """
    if abstains or not required or not claims:return False
    for c in claims:
        matches={a.value for a in evidence if a.entity==c.entity and a.attribute==c.attribute
                 and a.valid_from<=c.at<=a.valid_to and a.uncertainty=='KNOWN'}
        if c.uncertainty!='KNOWN' or matches!={c.value}:return False
    for key,(entity,attribute,at) in required.items():
        if not any(c.component==key and c.entity==entity and c.attribute==attribute and
                   c.at==at and c.speech_act=='ANSWER' for c in claims):return False
    return True

def fixtures():
    e=[Atom('jan','M','locker','L1','2048-01-01','2048-03-31'),
       Atom('may','M','locker','L2','2048-04-01','2048-06-30'),
       Atom('other','N','locker','L3','2048-04-01','2048-06-30'),
       Atom('window','M','window','10-11','2048-04-01','2048-06-30')]
    req={'locker':('M','locker','2048-05-15')}
    good=Claim('locker','M','locker','L2','2048-05-15')
    def row(name,claims,expected,ev=None,r=None,abstains=False):
        return {'id':name,'evidence':e if ev is None else ev,'required':req if r is None else r,
                'claims':claims,'abstains':abstains,'expected_supported_task':expected}
    return [row('correct',[good],True),row('expired_value',[replace(good,value='L1')],False),
        row('wrong_entity',[replace(good,entity='N',value='L3')],False),
        row('wrong_time',[replace(good,at='2048-01-15',value='L1')],False),
        row('valid_historical_answer',[replace(good,at='2048-01-15',value='L1')],True,
            r={'locker':('M','locker','2048-01-15')}),
        row('correct_intermediate_incomplete',[good],False,r={**req,'window':('M','window','2048-05-15')}),
        row('promise_not_delivery',[replace(good,speech_act='PROMISE')],False),
        row('trusted_conflict',[good],False,ev=e+[replace(e[1],source='conflict',value='L9')]),
        row('unknown_interval',[good],False,ev=[replace(a,uncertainty='UNKNOWN_INTERVAL') for a in e]),
        row('unsupported_extra',[good,Claim('extra','M','color','blue','2048-05-15')],False),
        row('unnecessary_abstention',[],False,abstains=True),
        row('negated_value_not_supported',[replace(good,value='NOT L2')],False),
        row('semantic_extraction_uncertain',[replace(good,uncertainty='UNCERTAIN')],False),
        row('duplicate_same_value',[good],True,ev=e+[replace(e[1],source='duplicate')]),
        row('missing_evidence', [good],False,ev=[]),
        row('correct_two_components',[good,Claim('window','M','window','10-11','2048-05-15')],True,
            r={**req,'window':('M','window','2048-05-15')})]

def run():
    fs=fixtures();rows=[]
    for f in fs:
        args=f['evidence'],f['required'],f['claims']
        for method in ('escp_rules','declarative_reference','no_entity','no_time','no_conflict','no_delivery'):
            if method=='declarative_reference':answer=simple_rule_reference(*args,abstains=f['abstains'])
            else:answer=verify(*args,abstains=f['abstains'],ablate=method.removeprefix('no_') if method.startswith('no_') else '')['supported_task']
            rows.append({'fixture':f['id'],'method':method,'supported_task':answer,
                         'expected':f['expected_supported_task'],'matches_authored_expectation':answer==f['expected_supported_task']})
    timings={}
    for method in ('escp_rules','declarative_reference'):
        samples=[]
        for _ in range(5):
            t=time.process_time_ns()
            for _ in range(100):
                for f in fs:
                    args=f['evidence'],f['required'],f['claims']
                    (verify(*args,abstains=f['abstains']) if method=='escp_rules' else simple_rule_reference(*args,abstains=f['abstains']))
            samples.append((time.process_time_ns()-t)/(100*len(fs)))
        timings[method]={'cpu_ns_per_fixture_samples':samples,'median':statistics.median(samples)}
    f=fs[0];h=[replace(f['evidence'][0],source='h_old',trust_priority=999),
              replace(f['evidence'][1],source='h_true'),replace(f['evidence'][1],source='h_false',value='L9',trust_priority=999)]
    admissions=admit(f['evidence'],h,f['required'],['brief clauses'],['answer before explanation'],['prefers tea'])
    summary={'version':'escp_offline_v1','classification':'ENGINEERING_ADAPTATION_RESEARCH_SCAFFOLD',
        'fixtures':len(fs),'new_inference':0,'independent_ground_truth':False,
        'results':{m:sum(r['matches_authored_expectation'] for r in rows if r['method']==m) for m in sorted({r['method'] for r in rows})},
        'timing':timings,'cost_excludes':['free_text_extraction','model_generation','I/O'],
        'novel_algorithm_evidence':False,'measured_model_improvement':None,'measured_persona_fidelity':None,
        'negative_result':'Full rule scaffold ties the declarative reference on authored structured fixtures; no superiority established.',
        'admission_example':admissions,'source_sha256':io.sha256(Path(__file__))}
    serial=[{**f,'evidence':[asdict(a) for a in f['evidence']],'claims':[asdict(c) for c in f['claims']]} for f in fs]
    io.save(OUT/'authored_fixtures_v1.json',serial);io.save(OUT/'results_v1.json',rows);io.save(OUT/'summary_v1.json',summary)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':run()
