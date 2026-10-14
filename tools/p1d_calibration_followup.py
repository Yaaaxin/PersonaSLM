"""Non-generation P1d material triage and dependence accounting; no stimulus edits."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import random

from p1d_design import read, write, csvwrite, sha
from p1d_scientific_audit import reconstruct, question_skeleton

OUT=Path('docs/validation/p1d/final_preparation_v1')
BANK=Path('docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json')
AUDIT=Path('docs/validation/p1d/scientific_validation_v1')

def records(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def build():
    cases=read(BANK)['cases'];old={r['case_id']:r for r in records(AUDIT/'case_scientific_review_v1.csv')}
    controls={r['case_id']:r for r in records(AUDIT/'control_semantic_risks_v1.csv')}
    frequency=Counter(c['question'] for c in cases);grammars=Counter(question_skeleton(c) for c in cases)
    rng=random.Random(716704);tie={c['case_id']:rng.random() for c in cases}
    strata=defaultdict(list);all_rows=[]
    for c in cases:
        refs,trace=reconstruct(c)
        if refs!=c['required_components'] or [x['id'] for x in trace]!=c['derivation_source_ids']:raise ValueError('Ground-truth discrepancy: '+c['case_id'])
        if old[c['case_id']]['objective_errors']!='[]':raise ValueError('Unresolved objective error')
        risk=[]
        if frequency[c['question']]>1:risk.append('LITERAL_QUESTION_REUSE')
        if c['family']=='context_followup':risk.append('REFERENT_DEPENDS_ON_FIXED_CONTEXT')
        if c['family']=='single_fact':risk.append('DECLARED_FULL_ANSWER_POSITIVE_CONTROL')
        if c['family']=='relational_integration':risk.append('ADJACENT_ROW_SHORTCUT')
        if c['domain']['id']=='archive':risk.append('CONTROL_TOPIC_OVERLAP')
        if c['target_entity']!=c['persona_entity']:risk.append('PERSONA_OTHER_ENTITY_DISAMBIGUATION')
        if 'plain cover' in controls[c['case_id']]['text']:risk.append('REPAIRED_CONTROL_WORDING')
        r={'case_id':c['case_id'],'speaker_id':c['speaker_id'],'family':c['family'],'domain':c['domain']['id'],
            'date_type':c['date_type'],'template_block':c['template_block'],'grammar':question_skeleton(c),
            'question_repeat_count':frequency[c['question']],'risks':risk,'AI_disposition':old[c['case_id']]['AI_proposed_classification'],
            'control_disposition':controls[c['case_id']]['AI_proposed_classification'],'researcher_decision':'','reviewer_id':''}
        all_rows.append(r);strata[c['family'],c['domain']['id'],c['date_type']].append(r)
    selected=set()
    for key,group in sorted(strata.items()):
        group.sort(key=lambda r:(-len(r['risks']),tie[r['case_id']]))
        selected.update(r['case_id'] for r in group[:2])
    # Coverage supplements are chosen without consulting any model outcome.
    for grammar in grammars:
        if not any(r['case_id'] in selected and r['grammar']==grammar for r in all_rows):
            pool=[r for r in all_rows if r['grammar']==grammar]
            selected.add(min(pool,key=lambda r:tie[r['case_id']])['case_id'])
    cb={c['case_id']:c for c in cases};review=[];control_review=[];mapping=[]
    ordered=sorted(selected);random.Random(716705).shuffle(ordered)
    for i,cid in enumerate(ordered,1):
        c=cb[cid];a=old[cid];r=next(r for r in all_rows if r['case_id']==cid)
        review.append({**a,'review_priority_id':f'SV{i:03d}','selection_risks':json.dumps(r['risks']),
            'history_texts':json.dumps(c['histories'],ensure_ascii=False),'selection':'Two per family/domain/date stratum, risk-prioritized; template coverage supplements; no output selection.'})
        x=controls[cid];anon=f'CV{i:03d}'
        control_review.append({'review_id':anon,'question':c['question'],'requested_date':c['query_date'],
            'fixed_context':c['fixed_context'],'trusted_evidence':c['trusted_evidence'],
            'reference_components':json.dumps(c['required_components']),'candidate_text':x['text'],
            'token_equality':'Actual native full-prompt equality verified; not semantic neutrality.',
            'answer_leakage_decision':'','reference_stability_decision':'','topic_style_instruction_risks':'',
            'control_classification':'','researcher_decision':'','reviewer_id':'','actual_review_time':''})
        mapping.append({'review_id':anon,'case_id':cid,'source_text_sha256':x['text_sha256'],'AI_recommendation':x['AI_proposed_classification']})
    OUT.mkdir(parents=True,exist_ok=True)
    csvwrite(OUT/'case_risk_inventory_v1.csv',all_rows)
    csvwrite(OUT/'stratified_case_review_v1.csv',review)
    csvwrite(OUT/'stratified_control_review_masked_v1.csv',control_review)
    write(OUT/'withheld_stratified_control_mapping_v1.json',mapping)
    template_counts=Counter(c['template_block'] for c in cases)
    dependencies={'version':'p1d_template_dependence_accounting_v1','case_count':len(cases),'speaker_count':len({c['speaker_id'] for c in cases}),
        'literal_questions':len(frequency),'repeated_question_records':sum(v for v in frequency.values() if v>1),
        'abstract_grammars':len(grammars),'grammar_counts':dict(grammars),'common_paraphrase_ancestors':dict(template_counts),
        'inverse_concentration_grammar_count':len(cases)**2/sum(n*n for n in grammars.values()),
        'inverse_concentration_ancestor_count':len(cases)**2/sum(n*n for n in template_counts.values()),
        'interpretation':'Concentration descriptors, NOT effective sample size or empirical ICC. Six conditions are repeated measures, not independent samples.',
        'cross_tabs':[{'family':f,'template_block':t,'cases':sum(c['family']==f and c['template_block']==t for c in cases),
            'target_persona':sum(c['family']==f and c['template_block']==t and c['target_entity']==c['persona_entity'] for c in cases)}
            for f in sorted({c['family'] for c in cases}) for t in sorted(template_counts)],
        'recommended_scope':'Paired synthetic-speaker case distribution conditional on these authored ledger grammars. No independently authored template or real-speaker generalization.',
        'prospective_amendment_option':'Before confirmatory freeze, independently author and balance additional template families with entity/date roles; keep current version. Requires substantive scope approval; not implemented.',
        'simulations':'Existing template_precision_simulation_v1 and earlier precision/stress results preserved; no repeat simulation needed.'}
    write(OUT/'template_dependency_assessment_v1.json',dependencies)
    summary={'version':'p1d_stratified_scientific_review_v1','source_bank':BANK.as_posix(),'source_sha256':sha(BANK),
        'full_census':288,'AI_VALID_WITH_LIMITATIONS':288,'AI_diagnostic_controls':288,'selected_cases':len(selected),
        'selected_controls':len(selected),'selection_seed':716704,'mask_order_seed':716705,
        'strata':32,'minimum_per_stratum':2,'grammars_covered':len({question_skeleton(cb[cid]) for cid in selected}),
        'human_decisions':0,'new_independent_validation_claim':False,'no_new_or_modified_cases':True,
        'selection_policy':'Risk-prioritized two per family x domain x date stratum, then uncovered grammar supplement. Not a random prevalence sample. Full 288-item audit remains authoritative source.',
        'masking':'Case mapping and AI proposals separated from control review CSV, not encrypted/access-controlled; context may reveal intended treatment.',
        'approval_scope':'Review selected consequential risks and explicitly decide full-bank scoped adoption or required correction; sample review alone does not certify all 288 individually.'}
    write(OUT/'stratified_review_manifest_v1.json',summary)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':build()
