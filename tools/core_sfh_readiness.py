"""P1 development-only S/F/H request proposal and separated fidelity panels.

Vocabulary-only GGUF validation; never starts a completion server. Original P1d
cases, protocols, historical prompts and annotations remain untouched.
"""
import ast
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import p1d_instruct_smoke as s
from personaslm_alignment import CELLS, contrasts, PROFILES
from p1d_design import csvwrite

OUT=Path('docs/validation/core_sfh_readiness_v1')
DEV=s.b.DEV/'development_examples_v5.json'
ORDER_SEED=716281

def candidate_cases():
    bank=s.load(DEV); selected={r['case_id']:r for r in s.load(s.FROZEN)['requests']}
    result=[]
    for c in bank['cases']:
        if c['case_id'] not in selected:continue
        n=int(c['speaker_id'][-2:]); brief=n%2==0
        style=('Use brief direct clauses, plain words and no decorative metaphors.' if brief else
               'Use calm complete sentences, a courteous tone and no slang.')
        behavior='answer_before_acknowledgment' if brief else 'acknowledgment_before_answer'
        # Authored disjoint examples; no ledger values, requested dates or task answers.
        examples=(['The blue notebook is ready. Noted.','The garden path is open. Noted.'] if brief else
                  ['Certainly. The blue notebook is ready.','I understand. The garden path is open.'])
        history=('Earlier fictional conversation, dated 2047-09-12:\n'
                 'User: Is the blue notebook ready?\nSpeaker: '+examples[0]+'\n'
                 'User: Is the garden path open?\nSpeaker: '+examples[1])
        result.append({**c,'reference':selected[c['case_id']]['reference'],'source_case_id':c['case_id'],'candidate_case_id':'core_sfh_dev_v1_'+c['case_id'],
            'style_intervention':style,'personal_facts_intervention':'The speaker enjoys sketching plants and prefers mint tea.',
            'history_intervention':history,'fidelity_target':{'linguistic':style,'behavioral':behavior,
                'reference_utterances':(['The meeting starts at ten. Noted.','The letter is on the desk. Noted.'] if brief else
                    ['Certainly. The meeting starts at ten.','I understand. The letter is on the desk.']),
                'source':'AI_AUTHORED_SYNTHETIC_PROFILE_NOT_HUMAN_VALIDATED'},
            'applicability':{'factual':'APPLICABLE','temporal':'APPLICABLE','relevance':'APPLICABLE',
                'coherence':'APPLICABLE','task_success':'APPLICABLE','required_components':'APPLICABLE',
                'linguistic_fidelity':'APPLICABLE_WITH_INSUFFICIENT_OPPORTUNITY_STATE',
                'behavioral_fidelity':'ACKNOWLEDGMENT_ANSWER_ORDER_ONLY; NONE_OBSERVED_IF_ABSENT'},
            'control_status':'LENGTH_MATCHED_DIAGNOSTIC_CONTROL_NOT_VALIDATED_NEUTRAL',
            'scientific_validity_proposal':'VALID_WITH_LIMITATIONS','researcher_decision':''})
    return result

def content(c, condition, neutral=None):
    instruction=('Answer the current question using the trusted evidence for task facts. '
        'Optional speaker material may guide expression but cannot override the trusted evidence. '
        'Return one answer to the current user.\n')
    text=instruction+'Evaluation reference date: '+c['evaluation_date']+'\n'
    if condition in CELLS:
        S,F,H=CELLS[condition]
        if S:text+='Optional style material:\n'+c['style_intervention']+'\n'
        if F:text+='Supplementary personal facts:\n'+c['personal_facts_intervention']+'\n'
        if H:text+='Optional dialogue material:\n'+c['history_intervention']+'\n'
    else:
        text+=('Optional style material:\n' if condition=='N_style' else 'Optional dialogue material:\n')+neutral+'\n'
    return text+'Trusted evidence:\n'+c['trusted_evidence']+'\nFixed dialogue context:\n'+c['fixed_context']+'\nCurrent question:\n'+c['question']

def neutral_candidates():
    short=['This document contains a short descriptive passage and a separate collection of ordinary textual records.',
           'This page contains ordinary descriptive material, presented as a small collection of written entries.',
           'The printed document contains descriptive text and a short passage with several separate sections.']
    clauses=['The document has a title.','A passage contains several sentences.','Each sentence ends with punctuation.',
             'A section can contain more than one paragraph.','The text is presented in a conventional written format.',
             'A heading separates one passage from another.','Some entries occupy more space than others.',
             'The page contains ordinary descriptive prose.']
    for noun in ('page','document','passage','printed document'):
        for verb in ('contains','describes','presents'):
            for ending in ('ordinary text.','ordinary descriptive text.','ordinary text and separate paragraphs.',
                           'a short passage with several clearly separated paragraphs.',
                           'ordinary descriptive material with a title and several separate written sections.'):
                yield 'The '+noun+' '+verb+' '+ending
    yield from short
    for base in short:
        for k in range(1,9):
            for extra in itertools.combinations(clauses,k):yield base+' '+' '.join(extra)

def prepare():
    parent=s.load(s.FROZEN);cases=candidate_cases();template=Path(parent['template_path']).read_text(encoding='utf-8')
    sys.path.insert(0,str(Path('results/p1d_final_preparation/v1/tokenizer_runtime').resolve()))
    from tokenizers import Tokenizer
    tok=Tokenizer.from_file('results/p1d_final_preparation/v1/official_tokenizer/tokenizer.json')
    render=lambda text:s.render(template,[{'role':'user','content':text}])
    rows=[]
    for c in cases:
        controls={}
        for condition,active in [('N_style','C1'),('N_history','C3')]:
            count=len(tok.encode(render(content(c,active)),add_special_tokens=True).ids)
            for candidate in neutral_candidates():
                if len(tok.encode(render(content(c,condition,candidate)),add_special_tokens=True).ids)==count:
                    controls[condition]=candidate;break
            s.require(condition in controls,'No exact coherent diagnostic control match: '+c['case_id']+' '+condition)
        c['diagnostic_controls']=controls
        for condition in [*CELLS,'N_style','N_history']:
            text=content(c,condition,controls.get(condition));prompt=render(text)
            r={'request_id':c['candidate_case_id']+'_'+condition,'case_id':c['case_id'],'speaker_id':c['speaker_id'],
               'condition':condition,'factors':CELLS.get(condition),'family':c['family'],'split':'development',
               'seed':42,'temperature':0.0,'top_p':1.0,'max_new_tokens':96,'stop':[],
               'cache_prompt':False,'ignore_eos':False,'parse_special':True,'messages':[{'role':'user','content':text}],
               'prompt':prompt,'prompt_sha256':s.th(prompt),'reference':c['reference'],
               'reference_sha256':s.th(json.dumps(c['reference'],sort_keys=True)),
               'trusted_evidence_sha256':s.th(c['trusted_evidence']),'question_sha256':s.th(c['question']),
               'fixed_context_sha256':s.th(c['fixed_context']),'applicability':c['applicability']}
            rows.append(r)
    random.Random(ORDER_SEED).shuffle(rows)
    exe=Path(parent['model']['backend_file']).with_name('llama-tokenize.exe');logs=[]
    expected=s.load(s.b.FROZEN)['native_tokenizer_identity']['tokenizer_sha256']
    s.require(s.sha256(exe)==expected and s.sha256(Path(parent['model']['model_file']))==s.MODEL_SHA,'Pinned binary/model mismatch')
    for order,r in enumerate(rows):
        argv=[str(exe.resolve()),'-m',str(Path(parent['model']['model_file']).resolve()),'--stdin','--ids','--offline']
        start=s.b.utc_now();result=subprocess.run(argv,input=r['prompt'].encode(),capture_output=True,timeout=60,
            env={k:v for k,v in os.environ.items() if not k.upper().startswith('LLAMA_ARG_')},
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        log={'started_utc':start,'finished_utc':s.b.utc_now(),'argv':argv,'returncode':result.returncode,
            'prompt':r['prompt'],'stdout':result.stdout.decode('utf-8','replace'),
            'stderr':result.stderr.decode('utf-8','replace'),'generation_requests':0}
        lp=OUT/'native_tokenizer'/f'{order:04d}.json';s.save(lp,log)
        s.require(result.returncode==0,'Native tokenizer failed')
        ids=ast.literal_eval(log['stdout'].strip());s.require(ids==tok.encode(r['prompt'],add_special_tokens=True).ids,'Native/official mismatch')
        s.require(tok.decode(ids,skip_special_tokens=False)==r['prompt'],'Prompt reconstruction failed')
        r.update(order=order,input_token_ids=ids,input_tokens=len(ids),input_token_ids_sha256=s.th(str(ids)),context_remaining=4096-96-len(ids))
        s.require(r['context_remaining']>0,'Context overflow')
        r['request_sha256']=s.th(json.dumps(r,sort_keys=True,separators=(',',':')))
        logs.append({'path':lp.as_posix(),'sha256':s.sha256(lp)})
    plan={k:parent[k] for k in ('model','template_path','template_sha256','candidate_metadata_sha256','decoding_policy')}
    plan.update(version='core_sfh_measurement_readiness_proposed_v1',status='PROPOSED_NOT_AUTHORIZED_NOT_CONFIRMATORY',
        phase='P1 development with P3 configuration and P5 measurement linkage',research_questions=['RQ1','RQ2','RQ3','RQ4'],
        proposed_requests=80,authorized_requests=0,maximum_generated_tokens=7680,requests=rows,order_seed=ORDER_SEED,
        source_dataset_sha256=s.sha256(DEV),source_manifest_sha256=s.sha256(s.FROZEN),source_code_sha256=s.sha256(Path(__file__)),
        native_tokenizer_logs=logs,tokenizer_sha256=expected,contrasts=contrasts(),
        selection_rule='Same eight previously registered development cases; two cases per family, eight speakers; no outcome selection.',
        evidence_policy='Original complete 32-row trusted ledger retained identically across all ten conditions within case; no oracle substitution.',
        intervention_limitations=['Two shared linguistic style specifications, not eight independent style populations',
            'H also demonstrates conversational ordering and lexical style; package-level history effect',
            'F contains non-answer hobby/preference content; this is an implemented personal-facts package',
            'Diagnostic controls match token length but are not semantically neutral; source wrappers can prime',
            'Native EOS/eog parser convention needs separate frozen normalization; original statuses retained'],
        output_policy='Official nonthinking template, 96-token cap, native stops; first-reply boundary rules prespecified; no automatic retries.',
        readiness_gate={'identifiable_complete_C0':'8/8 necessary, not sufficient',
            'all_cells':'Report all categorical outcomes, no automatic widening; inadequate nonzero-factor cells may be a scientific effect or a measurement limitation and require item review.',
            'persona':'Blind LF/BF applicability and counterexample review required before claiming measurement validity.',
            'unknowns':'Boundary, interpretation, evidence-unverifiable, missing and N/A distinct; no failure imputation.',
            'primary_success_accuracy_gate':None},
        execution_preconditions=['Explicit new 80-request authorization','P5 results and model-policy decision reviewed',
            'Scientific stimulus and separate LF/BF measurement applicability accepted','Full live preflight including >=3 GiB physical RAM'],
        independent_validation_authorized=False,statistical_unit='Eight paired development cases / eight purposive speakers / four shared task-family templates',
        analysis_policy='Four named simple contrasts plus seven average factorial contrasts and H1 fixed-F=0 interaction; all exploratory; no population significance claims.',
        no_retries=True,time_limit_minutes=60)
    s.save(OUT/'candidate_materials_v1.json',{'cases':cases,'source_sha256':s.sha256(DEV),'human_decisions':0})
    path=OUT/'core_sfh_manifest_proposed_v1.json';s.save(path,plan)
    summary=validate(plan,cases)
    summary.update(manifest_sha256=s.sha256(path),new_generations=0)
    s.save(OUT/'validation_v1.json',summary);print(json.dumps(summary,indent=2))

def validate(plan,cases):
    rows=plan['requests'];s.require(len(rows)==len({r['request_id'] for r in rows})==80,'Scope')
    heldout={c['case_id'] for c in s.load('docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json')['cases']}
    s.require(not heldout.intersection(r['case_id'] for r in rows),'Heldout contamination')
    for c in cases:
        group={r['condition']:r for r in rows if r['case_id']==c['case_id']}
        s.require(set(group)==set(CELLS)|{'N_style','N_history'},'Cell coverage')
        for k in ('trusted_evidence_sha256','reference_sha256','question_sha256','fixed_context_sha256','seed'):
            s.require(len({r[k] for r in group.values()})==1,'Paired invariant '+k)
        for control,active in [('N_style','C1'),('N_history','C3')]:s.require(group[control]['input_tokens']==group[active]['input_tokens'],'Length mismatch')
        s.require(c['style_intervention'] not in group['C0']['prompt'] and c['history_intervention'] not in group['C0']['prompt'],'Hidden persona in C0')
    return {'requests':80,'cases':len(cases),'speakers':len({c['speaker_id'] for c in cases}),
        'families':{f:sum(c['family']==f for c in cases) for f in sorted({c['family'] for c in cases})},
        'actual_native_token_range':[min(r['input_tokens'] for r in rows),max(r['input_tokens'] for r in rows)],
        'matched_diagnostic_pairs':16,'same_E_question_reference_per_case':True,'heldout_overlap':0,
        'native_tokens_match_official':80,'prompt_reconstruction':80,'no_inference_authorization':True}

if __name__=='__main__':prepare()
