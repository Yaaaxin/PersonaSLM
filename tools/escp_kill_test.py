"""P6 equal-output rule baseline and new adversarial specifications; no inference.

This tests structured inputs, not text extraction, generated fidelity or novelty.
The new baseline is an engineering comparator, not a published-method reproduction.
"""
from dataclasses import asdict, replace
from pathlib import Path
import json
import platform
import statistics
import time
from escp_offline import Atom, Claim, verify, admit
import p1d_budget_calibration as io

OUT=Path('docs/validation/p6/escp_kill_test_v1')

def rule_baseline(evidence, required, claims, *, abstains=False, as_of=None):
    """Elementary relational selection, with the same diagnostic output contract."""
    diagnostics=[]
    for c in claims:
        selected=[a for a in evidence if a.uncertainty=='KNOWN' and
                  (a.entity,a.attribute)==(c.entity,c.attribute) and
                  a.valid_from<=c.at<=a.valid_to and
                  (as_of is None or a.asserted_at<=as_of)]
        values=set(a.value for a in selected)
        state=('INTERPRETATION_UNCERTAIN' if c.uncertainty!='KNOWN' else
               'UNVERIFIABLE' if not values else 'CONFLICT_UNRESOLVED' if len(values)>1 else
               'SUPPORTED' if values=={c.value} else 'CONTRADICTED')
        diagnostics.append({'claim':vars(c).copy(),'state':state,
            'support_ids':[a.source for a in selected if a.value==c.value],
            'conflict_ids':[a.source for a in selected if a.value!=c.value]})
    components={}
    for key,descriptor in required.items():
        ds=[d for d in diagnostics if d['claim']['component']==key and
            (d['claim']['entity'],d['claim']['attribute'],d['claim']['at'])==tuple(descriptor)
            and d['claim']['speech_act']=='ANSWER']
        components[key]={'present':bool(ds),'supported':bool(ds) and all(d['state']=='SUPPORTED' for d in ds)}
    supported=bool(diagnostics) and all(d['state']=='SUPPORTED' for d in diagnostics)
    return {'claims':diagnostics,'components':components,
        'delivered':bool(components) and all(x['present'] for x in components.values()),
        'supported_task':bool(components) and all(x['supported'] for x in components.values()) and supported and not abstains,
        'abstention':abstains,'all_claims_supported':supported,'scalar_reliability_score':None}

def admission_baseline(evidence, history, required, style, behavior, personal_facts=()):
    groups={'answer_supporting_history':[],'dated_non_authoritative_archive':[],'quarantined_history':[]}
    for h in history:
        dates=[at for entity,attr,at in required.values() if (entity,attr)==(h.entity,h.attribute)]
        decisions=[]
        for at in dates:
            if h.uncertainty!='KNOWN':decisions.append('deny')
            elif not h.valid_from<=at<=h.valid_to:decisions.append('archive')
            else:
                matches={a.value for a in evidence if a.uncertainty=='KNOWN' and
                    (a.entity,a.attribute)==(h.entity,h.attribute) and a.valid_from<=at<=a.valid_to}
                decisions.append('answer' if matches=={h.value} else 'deny')
        group=('quarantined_history' if 'deny' in decisions else
               'answer_supporting_history' if 'answer' in decisions else 'dated_non_authoritative_archive')
        groups[group].append(h.source)
    return {'trusted_evidence_ids':[a.source for a in evidence],**groups,'style':list(style),
        'behavior':list(behavior),'personal_facts_pending_scope_check':list(personal_facts)}

def fixtures():
    a=Atom('E1','Visitor','slot','morning','2051-01-01','2051-06-30',asserted_at='2051-02-01')
    c=Claim('slot','Visitor','slot','morning','2051-04-10')
    required={'slot':('Visitor','slot','2051-04-10')}
    def row(name,ev=None,claims=None,req=None,as_of=None,abstains=False,state='SUPPORTED',success=True):
        return {'id':name,'evidence':[a] if ev is None else ev,'claims':[c] if claims is None else claims,
            'required':required if req is None else req,'as_of':as_of,'abstains':abstains,
            'expected_first_claim':state,'expected_supported_task':success}
    return [
        row('asserted_after_knowledge_cutoff',as_of='2051-01-31',state='UNVERIFIABLE',success=False),
        row('asserted_on_knowledge_cutoff',as_of='2051-02-01'),
        row('historical_validity_is_not_assertion_time',claims=[replace(c,at='2051-01-10')],
            req={'slot':('Visitor','slot','2051-01-10')}),
        row('closed_interval_end',claims=[replace(c,at='2051-06-30')],req={'slot':('Visitor','slot','2051-06-30')}),
        row('outside_interval',claims=[replace(c,at='2051-07-01')],state='UNVERIFIABLE',success=False),
        row('high_priority_cannot_resolve_trusted_conflict',ev=[a,replace(a,source='E2',value='evening',trust_priority=999)],
            state='CONFLICT_UNRESOLVED',success=False),
        row('same_surface_wrong_entity',claims=[replace(c,entity='Other')],state='UNVERIFIABLE',success=False),
        row('correct_claim_wrong_component_key',claims=[replace(c,component='other')],success=False),
        row('correct_historical_recollection_not_requested_answer',claims=[replace(c,speech_act='RECOLLECTION')],success=False),
        row('delivered_then_contradicted',claims=[c,replace(c,value='evening')],success=False),
        row('unsupported_extra_preserves_component_but_fails_task',claims=[c,Claim('extra','Visitor','color','blue',c.at)],success=False),
        row('explicit_abstention_with_correct_value',abstains=True,success=False),
        row('unresolved_semantic_scope',claims=[replace(c,uncertainty='UNRESOLVED_SCOPE')],state='INTERPRETATION_UNCERTAIN',success=False),
        row('uncertain_evidence_not_negative_fact',ev=[replace(a,uncertainty='UNKNOWN_PROVENANCE')],state='UNVERIFIABLE',success=False),
        row('duplicate_witness_not_independent_confirmation',ev=[a,replace(a,source='duplicate')]),
        row('two_requested_components_one_missing',req={**required,'gate':('Visitor','gate',c.at)},success=False),
    ]

def evaluate():
    rows=[]
    for f in fixtures():
        args=f['evidence'],f['required'],f['claims'];kw={k:f[k] for k in ('abstains','as_of')}
        a=verify(*args,**kw);b=rule_baseline(*args,**kw)
        rows.append({'id':f['id'],'escp':a,'rule_baseline':b,'identical_diagnostics':a==b,
            'matches_authored_specification':a['claims'][0]['state']==f['expected_first_claim'] and
            a['supported_task']==f['expected_supported_task']})
    f=fixtures()[0];a=f['evidence'][0]
    history=[replace(a,source='valid_history'),replace(a,source='forged_priority',value='evening',trust_priority=1000),
        replace(a,source='expired',valid_to='2051-03-31'),replace(a,source='unrelated',attribute='hobby',value='painting'),
        replace(a,source='uncertain',uncertainty='UNRESOLVED_SCOPE')]
    args=f['evidence'],history,f['required'],['calm complete sentences'],['answer before explanation'],['likes painting']
    admission=admit(*args);baseline=admission_baseline(*args)
    return rows,{'escp':admission,'simple_rules':baseline,'identical_channels':admission==baseline,
        'no_persona_baseline':{'style':[],'behavior':[],'history':[]},
        'history_removal_retaining_persona':{'style':list(args[3]),'behavior':list(args[4]),'history':[]},
        'channel_retention_is_not_generated_fidelity':True,'measured_fidelity_cost':None}

def run():
    rows,admission=evaluate();fs=fixtures();timings={}
    for name,fn in [('escp',verify),('equal_output_simple_rules',rule_baseline)]:
        samples=[]
        for _ in range(3):
            start=time.process_time_ns()
            for _ in range(5000):
                for f in fs:fn(f['evidence'],f['required'],f['claims'],as_of=f['as_of'],abstains=f['abstains'])
            samples.append((time.process_time_ns()-start)/(5000*len(fs)))
        timings[name]={'process_cpu_ns_per_case':samples,'median':statistics.median(samples)}
    summary={'phase':'P6','rq':['RQ2','RQ4'],'version':'escp_kill_test_v1','fixtures':len(rows),
        'same_diagnostic_outputs':sum(r['identical_diagnostics'] for r in rows),
        'authored_specifications_met':sum(r['matches_authored_specification'] for r in rows),
        'admission':admission,'cpu_cost':timings,'python':platform.python_version(),
        'inference_requests':0,'human_labels':0,'actual_model_answer_gain':None,'new_algorithm_claim':'REJECTED_ON_CURRENT_EVIDENCE',
        'limitations':['Authored typed inputs; no learned extraction','No generated Persona Fidelity','Not independent validation',
            'No reproduction of Zep/Mem0/FC-PS/FPPS/CoVe/RARR','Microbenchmark excludes parsing, generation and I/O'],
        'negative_finding':'Simple rules produce identical support, conflict, component and admission diagnostics; no incremental benefit.',
        'source_hashes':{str(p).replace('\\','/'):io.sha256(p) for p in (Path(__file__),Path('tools/escp_offline.py'))}}
    io.save(OUT/'authored_adversarial_fixtures_v1.json',[{**f,'evidence':[asdict(a) for a in f['evidence']],
        'claims':[asdict(c) for c in f['claims']]} for f in fs])
    io.save(OUT/'equal_output_results_v1.json',rows);io.save(OUT/'summary_v1.json',summary)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':run()
