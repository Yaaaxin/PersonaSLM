"""Construct prospective independent-candidate stimuli, never confirmed test data.

The bank has no model outputs, and must not be used to tune algorithm parameters.
All semantic validity decisions remain blank. Human review and tokenizer validation
must precede any confirmatory freeze. Shared template ancestry is explicit.
"""
from collections import Counter
import random
from pathlib import Path
from p1d_design import OUT, CELLS, read, write, csvwrite, sha, th

DEST = Path('docs/validation/p1d/independent_candidates_v1')
SEED = 716601
FIRST = ('Asha','Bryn','Dara','Emil','Faye','Galen','Hana','Ivo','Jori','Kiran','Lena','Marek')
LAST = ('Calder','Dunley','Estwick','Farnell','Gresham','Hollis','Isley','Jarrow','Keaton','Lydell','Marden','Norcross')
DOMAINS = (
    {'id':'archive','setting':'an archive retrieval service','assignment':'cabinet','middle':'wing','destination':'desk','window':'retrieval window','unit':'record'},
    {'id':'laboratory','setting':'a laboratory equipment service','assignment':'station','middle':'zone','destination':'counter','window':'equipment window','unit':'equipment'},
    {'id':'music','setting':'a rehearsal instrument service','assignment':'rack','middle':'studio','destination':'door','window':'instrument window','unit':'instrument'},
    {'id':'workshop','setting':'a workshop tool service','assignment':'bin','middle':'aisle','destination':'gate','window':'tool window','unit':'tool'},
)
PERIODS=(('2054-01-01','2054-03-31'),('2054-04-01','2054-06-30'),('2054-07-01','2054-09-30'),('2054-10-01','2054-12-31'))

def fact_sentence(f):
    return f"{f['entity']}: {f['predicate']} = {f['value']}; valid {f['start']} through {f['end']} inclusive."

def unique(facts,entity,predicate,when):
    rows=[f for f in facts if f['entity']==entity and f['predicate']==predicate and f['start']<=when<=f['end']]
    if len(rows)!=1:raise ValueError('Invalid candidate ground truth')
    return rows[0]

def construct():
    allocation=read(OUT/'allocation_selection_v1.json')['allocation']
    rng=random.Random(SEED)
    names=[f+' '+s for f in FIRST for s in LAST];rng.shuffle(names)
    cases=[]
    for row in allocation:
        si,j=row['speaker_index'],row['case_index'];cid=f'p1d_candidate_s{si:03d}_c{j}'
        persona=names[si]; other='Neri '+LAST[(si*5+j+3)%12]
        domain=DOMAINS[(si//24+j)%4]
        referent_other=(si//24)%2==1
        target=other if referent_other else persona
        distractor=persona if referent_other else other
        # Per-case independent permutations; no output-dependent or label-dependent choices.
        code_lists=[rng.sample(range(start,start+180),8) for start in (101,301,501)]
        windows=rng.sample([f'{h:02d}:{m:02d}-{h+1:02d}:{m:02d}' for h in range(8,17) for m in (0,15,30)],8)
        facts=[]
        for ei,entity in enumerate((persona,other)):
            for pi,(start,end) in enumerate(PERIODS):
                index=ei*4+pi
                a=domain['assignment'].title()+' '+str(code_lists[0][index])
                m=domain['middle'].title()+' '+str(code_lists[1][index])
                d=domain['destination'].title()+' '+str(code_lists[2][index])
                for subject,predicate,value in [(entity,domain['assignment'],a),(entity,domain['window'],windows[index]),
                    (a,domain['middle'],m),(m,domain['destination'],d)]:
                    facts.append({'id':cid+f'_f{len(facts):02d}','entity':subject,'predicate':predicate,'value':value,
                        'start':start,'end':end,'authority':'trusted','scope':domain['id']})
        requested='2054-05-15' if row['date_type']=='historical' else '2054-11-15'
        when_index=1 if row['date_type']=='historical' else 3
        first=unique(facts,target,domain['assignment'],requested)
        window=unique(facts,target,domain['window'],requested)
        middle=unique(facts,first['value'],domain['middle'],requested)
        destination=unique(facts,middle['value'],domain['destination'],requested)
        v=row['template_block']
        contexts=(
            f'User: Please prepare a note for {target}.\nAssistant: I will check that person in the ledger.',
            f'User: The next service note is for {target}.\nAssistant: I will use the dated ledger for that person.',
            f'User: Please help with the service details for {target}.\nAssistant: I will check the requested date.',
            f'User: We need to prepare the service information for {target}.\nAssistant: I will consult the ledger.')
        # Four authored paraphrase templates, NOT four independent template samples.
        if row['family']=='single_fact':
            questions=(f'Which {domain["assignment"]} was assigned to {target} on {requested}?',
                f'For {requested}, identify the {domain["assignment"]} assigned to {target}.',
                f'Give {target}\'s assigned {domain["assignment"]} for {requested}.',
                f'On {requested}, what was {target}\'s assigned {domain["assignment"]}?')
            required=[first];trace=[first]
        elif row['family']=='relational_integration':
            questions=(f'On {requested}, follow {target}\'s {domain["assignment"]} to its {domain["middle"]}, then to its {domain["destination"]}. Give the {domain["middle"]} and {domain["destination"]}.',
                f'Use {target}\'s assigned {domain["assignment"]} for {requested} to find its linked {domain["middle"]} and then {domain["destination"]}. Report both.',
                f'Which {domain["middle"]} and {domain["destination"]} follow from {target}\'s {domain["assignment"]} on {requested}? Use both ledger links.',
                f'For {target} on {requested}, give the {domain["middle"]} linked to the assigned {domain["assignment"]} and the {domain["destination"]} linked to that {domain["middle"]}.')
            required=[middle,destination];trace=[first,middle,destination]
        else:
            who='that person' if row['family']=='context_followup' else target
            questions=(f'Give both the {domain["assignment"]} and {domain["window"]} assigned to {who} on {requested}.',
                f'For {who} on {requested}, report the assigned {domain["assignment"]} together with the {domain["window"]}.',
                f'What were the {domain["assignment"]} and {domain["window"]} for {who} on {requested}? Include both details.',
                f'On {requested}, which {domain["assignment"]} and {domain["window"]} applied to {who}?')
            required=[first,window];trace=[first,window]
        histories={}
        for cell in CELLS[:4]:
            entity=target if cell[1]=='1' else distractor
            at=PERIODS[when_index if cell[3]=='1' else when_index-1][0]
            f=unique(facts,entity,domain['assignment'],at)
            histories[cell]={'text':f'Archived quotation by {persona}: "{fact_sentence(f)}"','source_id':f['id'],
                'entity_match':cell[1]=='1','query_interval_match':cell[3]=='1','answer_supporting':cell=='E1V1'}
        histories['D_procedural']={'text':f'Archived quotation by {persona}: "I read the record carefully and closed the folder. I put it on the shelf without making any further notes."',
            'source_id':None,'status':'DIAGNOSTIC_ONLY_UNMATCHED_CANDIDATE'}
        histories['H_none']={'text':'','source_id':None,'status':'SHORTER_CONTEXT'}
        cases.append({**row,'case_id':cid,'speaker_id':f'p1d_candidate_s{si:03d}','domain':domain,
            'persona_entity':persona,'other_person':other,'target_entity':target,'distractor_entity':distractor,
            'persona_profile':persona+' is a fictional service volunteer. '+('Use calm complete sentences; avoid slang.' if si%2 else 'Use brief direct clauses; avoid decorative metaphors.'),
            'query_date':requested,'evaluation_date':'2054-12-31','fixed_context':contexts[v],'question':questions[v],
            'facts':facts,'trusted_evidence':'\n'.join('['+f['id']+'] '+fact_sentence(f) for f in facts),
            'required_components':[{'key':f['predicate'],'value':f['value'],'source_id':f['id']} for f in required],
            'derivation_source_ids':[f['id'] for f in trace],'histories':histories,
            'status':'PROSPECTIVE_CANDIDATE_NOT_FROZEN_NOT_VALIDATED','algorithm_tuning_permitted':False,
            'semantic_validity_decision':'','reviewer_id':'','template_ancestry':'Four authored paraphrases per family, shared construction grammar; not independent human template authorship'})
    return cases

def validate(cases):
    if len(cases)!=288 or len({c['speaker_id'] for c in cases})!=144 or len({c['case_id'] for c in cases})!=288:
        raise ValueError('Candidate allocation mismatch')
    for c in cases:
        # Independent ledger traversal from domain rules; do not accept stored answer strings as proof.
        def get(entity,predicate):
            rows=[f for f in c['facts'] if f['entity']==entity and f['predicate']==predicate and f['start']<=c['query_date']<=f['end']]
            if len(rows)!=1:raise ValueError('Non-unique ledger ground truth')
            return rows[0]
        d=c['domain'];assigned=get(c['target_entity'],d['assignment'])
        if c['family']=='single_fact':expected=[assigned]
        elif c['family']=='relational_integration':
            middle=get(assigned['value'],d['middle']);expected=[middle,get(middle['value'],d['destination'])]
        else:expected=[assigned,get(c['target_entity'],d['window'])]
        if c['required_components']!=[{'key':f['predicate'],'value':f['value'],'source_id':f['id']} for f in expected]:
            raise ValueError('Candidate answer derivation mismatch')
        if c['family']=='context_followup' and c['target_entity'] in c['question']:
            raise ValueError('Follow-up leaks target name in question')
        for cell in CELLS[:4]:
            h=c['histories'][cell];f=next(f for f in c['facts'] if f['id']==h['source_id'])
            assert (f['entity']==c['target_entity'])==h['entity_match']
            assert (f['start']<=c['query_date']<=f['end'])==h['query_interval_match']
        assert all(r['value'] not in c['histories']['D_procedural']['text'] for r in c['required_components'])
    return {'cases':len(cases),'speakers':144,'family_counts':dict(Counter(c['family'] for c in cases)),
        'domain_counts':dict(Counter(c['domain']['id'] for c in cases)),
        'date_counts':dict(Counter(c['date_type'] for c in cases)),
        'persona_target_counts':dict(Counter(str(c['target_entity']==c['persona_entity']) for c in cases)),
        'unique_reference_reconstructions':288,'human_validity_decisions':0,'new_generations':0,
        'limits':'Structural checks only. Shared template ancestry, condition-token matching, control priming and human semantic validity remain unresolved.'}

def prompt(c,cell):
    return ('TASK RULES\nUse the trusted ledger for the requested date. Historical quotations describe their stated intervals.'
        +'\nSETTING\n'+c['domain']['setting']+'\nFICTIONAL PERSONA\n'+c['persona_profile']
        +'\nEVALUATION DATE\n'+c['evaluation_date']+'\nTRUSTED EVIDENCE\n'+c['trusted_evidence']
        +'\nARCHIVED MATERIAL\n'+c['histories'][cell]['text']+'\nFIXED CONTEXT\n'+c['fixed_context']
        +'\nCURRENT QUESTION\n'+c['question']+'\nAssistant:')

def main():
    if DEST.exists():raise FileExistsError('Preserve candidate bank')
    cases=construct();summary=validate(cases)
    write(DEST/'candidate_bank_v1.json',{'version':'p1d_independent_candidate_bank_v1','seed':SEED,'cases':cases,
        'freeze_status':'NOT_FROZEN','approval_status':'MATERIALS_UNREVIEWED','algorithm_tuning_permitted':False})
    prompts=[];review=[];applicable=[]
    for c in cases:
        for cell in CELLS:
            text=prompt(c,cell)
            prompts.append({'candidate_request_id':c['case_id']+'_'+cell,'case_id':c['case_id'],'speaker_id':c['speaker_id'],
                'condition':cell,'prompt':text,'prompt_sha256':th(text),'trusted_evidence_sha256':th(c['trusted_evidence']),
                'question_sha256':th(c['question']),'reference':c['required_components'],'fixed_context_sha256':th(c['fixed_context']),
                'native_token_ids':None,'generation_authorized':False})
            applicable.append({'case_id':c['case_id'],'condition':cell,**{m:True for m in ('relevance','factual','temporal','coherence','task_success','component_coverage','semantic_completeness','persona_fidelity','structural_status')},
                'status':'PROSPECTIVE_APPLICABILITY_CANDIDATE_NOT_FROZEN'})
        review.append({'case_id':c['case_id'],'family':c['family'],'domain':c['domain']['id'],'persona':c['persona_profile'],
            'trusted_evidence':c['trusted_evidence'],'question':c['question'],'fixed_context':c['fixed_context'],
            'requested_date':c['query_date'],'reference':c['required_components'],'source_trace':c['derivation_source_ids'],
            'histories':c['histories'],'evidence_sufficiency':'','unique_answer':'','temporal_truth':'','entity_consistency':'',
            'control_validity':'','undeclared_leakage':'','shortcut_risk':'','researcher_decision':'','reviewer_id':'','actual_timestamp':''})
    write(DEST/'base_candidate_prompts_v1.json',prompts)
    write(DEST/'metric_applicability_candidate_v1.json',applicable)
    csvwrite(DEST/'material_review_candidate_v1.csv',review)
    write(DEST/'construction_validation_v1.json',summary)
    write(DEST/'candidate_provenance_manifest_v1.json',{'seed':SEED,'code_sha256':sha(__file__),
        'allocation_source_sha256':sha(OUT/'allocation_selection_v1.json'),
        'artifact_sha256':{p.as_posix():sha(p) for p in sorted(DEST.iterdir()) if p.is_file()},
        'freeze_status':'NOT_FROZEN','execution_manifest':None,'authorized_inference_requests':0,
        'independence_claim':'New content relative to earlier waves, with shared synthetic template dependencies. Independent semantic validity is NOT established.',
        'no_tuning_rule':'Do not inspect candidate answers to tune the offline verifier or any algorithm; existing development fixtures remain separate.'})
    print(summary)

if __name__=='__main__':main()
