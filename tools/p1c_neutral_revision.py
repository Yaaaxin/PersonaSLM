"""One bounded neutral-wording repair; preserves all v1 candidates and failures."""
import argparse
import ast
from pathlib import Path
import json

import p1c_design as d
import p1c_tokenize as t

OUT=Path('docs/validation/p1c/proposed_v2')


def plan():
    old=d.NEUTRAL[7]
    new=old.replace('its two parts.','its two distinct parts.')
    d.require(new!=old,'Expected source phrase missing')
    result={'version':'p1c_neutral_minimal_revision_v2','status':'PROPOSED_NOT_HUMAN_REVIEWED',
        'recorded_utc':d.now(),'reason':'Initial v1 cases have equal four-cell lengths but nearest neutral differs by one token.',
        'source_dataset_sha256':d.sha(d.DATA),'source_bank_sha256':d.sha(d.PUBLIC/'candidate_bank_v1.json'),
        'old_neutral_reply':old,'new_neutral_reply':new,
        'rule':'Change only the final reply modifier: two parts -> two distinct parts. Four existing question variants, four candidates per case. Same active variant within all R/T cells. Select first exact match; no further expansion.',
        'max_new_candidates_per_case':4,'max_new_candidates_total':48,'token_tolerance':0,
        'changed_evidence':False,'changed_question':False,'changed_reference':False,'changed_active_history':False,
        'generation_used_for_selection':False,'researcher_approval':''}
    d.write_json(OUT/'revision_plan_v2.json',result)
    return result


def run():
    plan=d.read(OUT/'revision_plan_v2.json')
    d.require(not (OUT/'tokenizer_validation_v2.json').exists(),'Refusing overwrite')
    d.require(d.sha(d.DATA)==plan['source_dataset_sha256'],'Dataset changed')
    old=d.read(d.PUBLIC/'tokenizer_validation_v1.json')
    old_attempts=d.read(d.PUBLIC/'candidate_token_attempts_v1.json')['attempts']
    data=d.read(d.DATA);bank=d.read(d.PUBLIC/'candidate_bank_v1.json')
    # Reuse actual native IDs for identical prompts, not character approximations.
    cache={}
    for p in sorted((d.LOCAL/'native_calls').glob('*.json')):
        r=d.read(p);cache[r['prompt_sha256']]=ast.literal_eval(r['stdout'].strip())
    # Preserve the initial position-check failure and reuse its valid native counts.
    for p in sorted((d.LOCAL/'revision_v2/native_calls').glob('*.json')):
        r=d.read(p);cache[r['prompt_sha256']]=ast.literal_eval(r['stdout'].strip())
    t.LOCAL=d.LOCAL/'revision_v2_retry1';native=t.NativeTokenizer();native.cache.update(cache)
    probes=native.verify_historical();matches=[];selected=[];reviews=[];attempts=[]
    for case,cb in zip(data['cases'],bank['cases']):
        counts={cond:[r['tokens'] for r in old_attempts if r['case_id']==case['case_id'] and r['condition']==cond] for cond in d.CONDITIONS}
        neutral=[]
        for qi,q in enumerate(d.QUESTIONS):
            text=f"[Archive recorded 2042-12-01]\nArchivist: {q}\n{case['speaker_name']}: {plan['new_neutral_reply']}"
            prompt=d.render(case,text);ids=native.tokens(prompt)
            neutral.append({'text':text,'ids':ids,'qi':qi})
            attempts.append({'case_id':case['case_id'],'question_variant':qi,'history':text,'prompt_sha256':d.text_hash(prompt),'input_token_ids':ids,'tokens':len(ids)})
        match=None
        for vi in range(16):
            vals=[counts[c][vi] for c in ('R0T0','R0T1','R1T0','R1T1')]
            if len(set(vals))==1 and vals[0]==len(neutral[vi//4]['ids']):match=vi;break
        matches.append({'case_id':case['case_id'],'status':'PASS' if match is not None else 'FAILED',
            'active_variant':match,'neutral_question_variant':match//4 if match is not None else None,'token_difference':0 if match is not None else None,
            'v1_match_status':next(r['status'] for r in old['matches'] if r['case_id']==case['case_id']),
            'new_candidates_tested':4,'semantic_approval':'OPEN'})
        if match is None:continue
        for cond in d.CONDITIONS:
            v=cb['conditions'][cond][0 if cond=='H_none' else match] if cond!='N_history' else {'text':neutral[match//4]['text'],'fact_id':None}
            prompt=d.render(case,v['text']);ids=native.tokens(prompt)
            # Anchor the semantic header, not separator whitespace: H_none has
            # three adjacent newlines whose native token differs from two.
            suffix='RECENT CONVERSATION:\n'+case['fixed_context']+'\nUser: '+case['question']+'\nAssistant:'
            prefix=prompt.split('ADDITIONAL ARCHIVED DIALOGUE:\n')[0]
            # Save token positions verified from actual IDs, not inferred from text length.
            prefix_ids=native.tokens(prefix);suffix_ids=native.tokens(suffix)
            d.require(ids[:len(prefix_ids)]==prefix_ids,'Evidence prefix token boundary changed')
            d.require(ids[-len(suffix_ids):]==suffix_ids,'Final context/question suffix token boundary changed')
            row={'case_id':case['case_id'],'persona_id':case['persona_id'],'condition':cond,'prompt_template_version':d.TEMPLATE,
                'history':v['text'],'history_fact_id':v['fact_id'],'prompt':prompt,'prompt_sha256':d.text_hash(prompt),
                'input_token_ids':ids,'input_tokens':len(ids),'output_budget':96,'context_fit':len(ids)+96<=4096,
                'evidence_prefix_tokens':len(prefix_ids),'fixed_context_suffix_start_token':len(ids)-len(suffix_ids),
                'evidence_sha256':d.text_hash(case['trusted_evidence']),'question_sha256':d.text_hash(case['question']),
                'context_sha256':d.text_hash(case['fixed_context']),'reference_sha256':d.canonical(case['reference']),
                'semantic_approval':'OPEN','generation_authorized':False}
            d.require(row['context_fit'],'Context overflow');selected.append(row)
            if cond!='H_none':reviews.append({'case_id':case['case_id'],'condition':cond,'history':v['text'],
                'trusted_evidence':case['trusted_evidence'],'current_question':case['question'],'requested_date':case['requested_date'],
                'evaluation_date':case['evaluation_date'],'reference_answer':case['reference']['components'],
                'input_tokens':len(ids),'token_difference':len(ids)-counts['R1T1'][match],'prompt_sha256':row['prompt_sha256'],
                **{'review_'+s:'' for s in ['relevance','temporal_status','truth_in_interval','no_answer_leakage','speaker_identity','dialogue_coherence','no_style_instruction','narrow_comparison_validity','decision']},
                'evidence_quotations':'','reviewer_notes':'','reviewer_id':'','reviewed_utc':''})
    d.write_json(OUT/'candidate_attempts_v2.json',{'attempts':attempts})
    d.write_json(OUT/'selected_prompts_v2.json',{'version':'p1c_auxiliary_history_selected_v2','dataset_sha256':d.sha(d.DATA),'records':selected})
    if reviews:d.write_csv(OUT/'history_semantic_review_v2.csv',reviews)
    result={'version':'p1c_tokenizer_verification_v2','identity':native.identity,'historical_probes':probes,'matches':matches,
        'native_calls_new':len(native.calls),'candidate_calls':48,'selected_prompts':len(selected),'new_generations':0,
        'v1_results_sha256':d.sha(d.PUBLIC/'tokenizer_validation_v1.json'),'plan_sha256':d.sha(OUT/'revision_plan_v2.json')}
    d.write_json(OUT/'tokenizer_validation_v2.json',result)
    return {'matches':sum(m['status']=='PASS' for m in matches),'cases':12,'selected_prompts':len(selected)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','run']);a=p.parse_args()
    print(json.dumps(plan() if a.action=='plan' else run()))
