"""Offline scientific census of candidate v4. No inference or human adoption.

Checks all records against an independently reconstructed ledger lookup; attaches
explicit AI-assisted semantic judgments from the inspected finite grammar.
Schema checks alone never produce SCIENTIFICALLY_VALID.
"""
import ast
from collections import Counter, defaultdict
from datetime import date
import difflib
import json
from pathlib import Path
import random
import re
from p1d_design import read, write, csvwrite, sha, th, CELLS, WEIGHTS

DEST = Path('docs/validation/p1d/scientific_validation_v1')
BANK = Path('docs/validation/p1d/independent_candidates_v4')


def only(facts, subject, predicate, when):
    d = date.fromisoformat(when)
    rows = [f for f in facts if f['entity'] == subject and f['predicate'] == predicate
            and date.fromisoformat(f['start']) <= d <= date.fromisoformat(f['end'])]
    if len(rows) != 1:
        raise ValueError(f'Nonunique ground truth: {subject}/{predicate}/{when}')
    return rows[0]


def reconstruct(c):
    d = c['domain']; fs = c['facts']; when = c['query_date']
    a = only(fs, c['target_entity'], d['assignment'], when)
    if c['family'] == 'single_fact':
        refs, trace = [a], [a]
    elif c['family'] == 'relational_integration':
        m = only(fs, a['value'], d['middle'], when)
        z = only(fs, m['value'], d['destination'], when)
        refs, trace = [m, z], [a, m, z]
    else:
        w = only(fs, c['target_entity'], d['window'], when)
        refs, trace = [a, w], [a, w]
    return [dict(key=f['predicate'], value=f['value'], source_id=f['id']) for f in refs], trace


def words(s):
    return set(re.findall(r'[a-z]+', s.lower()))


def question_skeleton(c):
    s = c['question'].replace(c['target_entity'], 'PERSON').replace(c['query_date'], 'DATE')
    for k in ('window', 'assignment', 'middle', 'destination'):
        s = s.replace(c['domain'][k], k.upper())
    return s


def inspect_case(c):
    refs, trace = reconstruct(c)
    errors = []
    if refs != c['required_components']: errors.append('REFERENCE_MISMATCH')
    if [f['id'] for f in trace] != c['derivation_source_ids']: errors.append('TRACE_MISMATCH')
    if c['query_date'] not in c['question']: errors.append('REQUESTED_DATE_ABSENT')
    if c['target_entity'] not in c['fixed_context']: errors.append('CONTEXT_ENTITY_ABSENT')
    if c['family'] != 'context_followup' and c['target_entity'] not in c['question']: errors.append('QUESTION_ENTITY_ABSENT')
    for f in c['facts']:
        if date.fromisoformat(f['start']) > date.fromisoformat(f['end']): errors.append('REVERSED_INTERVAL')
        expected = f"[{f['id']}] {f['entity']}: {f['predicate']} = {f['value']}; valid {f['start']} through {f['end']} inclusive."
        if expected not in c['trusted_evidence']: errors.append('EVIDENCE_TEXT_MISMATCH')
        only(c['facts'], f['entity'], f['predicate'], f['start'])
        only(c['facts'], f['entity'], f['predicate'], f['end'])
    byid = {f['id']: f for f in c['facts']}; history = []
    for cell in CELLS[:4]:
        h = c['histories'][cell]; f = byid[h['source_id']]
        e = f['entity'] == c['target_entity']; v = f['start'] <= c['query_date'] <= f['end']
        if e != (cell[1] == '1') or v != (cell[3] == '1'): errors.append('ROUTING_ERROR_' + cell)
        if not v and not f['end'] < c['query_date']: errors.append('NOT_EXPIRED_' + cell)
        quote = f"{f['entity']}: {f['predicate']} = {f['value']}; valid {f['start']} through {f['end']} inclusive."
        if h['text'] != f'Archived quotation by {c["persona_entity"]}: "{quote}"': errors.append('HISTORY_TEXT_ERROR_' + cell)
        overlap = sorted(words(c['question']) & words(quote))
        supplied = [r['key'] for r in refs if r['source_id'] == f['id']]
        history.append({'case_id': c['case_id'], 'condition': cell, 'text': h['text'], 'source_fact': f,
                        'entity_match': e, 'query_interval_match': v, 'requested_date': c['query_date'],
                        'question_lexical_overlap': overlap, 'direct_required_components_supplied': supplied,
                        'chain_entry_supplied': bool(e and v and c['family'] == 'relational_integration'),
                        'historically_true': True, 'human_decision': '', 'reviewer_id': ''})
    limitation = {
        'single_fact': 'E1V1 supplies the entire requested fact: copying that quotation can succeed without using the ledger. This is the declared positive control, not hidden leakage.',
        'multi_component': 'E1V1 supplies assignment but not the requested window. A correct assignment alone can be factually correct yet incomplete; factual/task discrimination is possible, not guaranteed.',
        'context_followup': 'The fixed context identifies the referent; E1 history can also name it. Context removal is not controlled here. Assignment alone does not satisfy the two components.',
        'relational_integration': 'Assignment, middle and destination are adjacent in each ledger block. Reading the block can avoid sequential relational reasoning; correct final values do not prove multi-step computation.'
    }[c['family']]
    return {'case_id': c['case_id'], 'speaker_id': c['speaker_id'], 'family': c['family'], 'domain': c['domain']['id'],
            'AI_proposed_classification': 'REVISION_REQUIRED' if errors else 'VALID_WITH_LIMITATIONS',
            'objective_errors': errors, 'question': c['question'], 'requested_date': c['query_date'],
            'evaluation_date': c['evaluation_date'], 'unique_answer': refs, 'exact_supporting_evidence': trace,
            'trusted_evidence': c['trusted_evidence'], 'fixed_context': c['fixed_context'],
            'temporal_interpretation': f"Answer for {c['query_date']} using inclusive intervals, not the latest ledger row. '{c['date_type']}' is a design stratum; both requests precede evaluation date {c['evaluation_date']}.",
            'entity_interpretation': f"Target {c['target_entity']}; alternate {c['distractor_entity']}; quotation speaker {c['persona_entity']}; scenario {c['scenario_id']} is local, not a globally consistent biography.",
            'task_limitation': limitation, 'designed_difficulty': 'DESIGNED_ONLY_NOT_EMPIRICALLY_VALIDATED',
            'persona_leakage': 'Profile gives name/style/fictional role, no assignment/window values; target role covaries with template allocation and needs restricted heterogeneity interpretation.',
            'applicability_recommendation': 'All nine registered metrics eligible; unscorable outputs remain eligible with reason codes. No N/A inferred from failure.',
            'restricted_interpretation': 'Entity-match and requested-interval source-selection packages, conditional on shared service-ledger grammar; no pure topical/temporal mechanism or independent template generalization.',
            'provenance': 'AI-assisted finite-grammar semantic audit plus exhaustive evidence reconstruction; not independent human review',
            'researcher_decision': '', 'reviewer_id': '', 'researcher_correction': ''}, history


def token_check(prompts, native, cases):
    out = []; bycase = defaultdict(dict)
    for p, r in zip(prompts, native['rows']):
        if p['candidate_request_id'] != r['candidate_request_id']: raise ValueError('Order mismatch')
        if th(p['prompt']) != p['prompt_sha256'] or p['prompt_sha256'] != r['prompt_sha256']: raise ValueError('Prompt mismatch')
        if sha(r['native_call_log']) != r['native_call_sha256']: raise ValueError('Native log changed')
        log = read(r['native_call_log']); ids = ast.literal_eval(log['stdout'].strip())
        if log['prompt'] != p['prompt'] or log['exit_code'] != 0 or log.get('generation'): raise ValueError('Native provenance invalid')
        if len(ids) != r['input_tokens'] or th(str(ids)) != r['token_ids_sha256']: raise ValueError('Token IDs mismatch')
        c = cases[p['case_id']]
        for key, text in [('TRUSTED EVIDENCE', c['trusted_evidence']), ('FIXED CONTEXT', c['fixed_context']), ('CURRENT QUESTION', c['question']), ('EVALUATION DATE', c['evaluation_date'])]:
            if key + '\n' + text not in p['prompt']: raise ValueError('Frozen segment differs')
        if p['reference'] != c['required_components']: raise ValueError('Reference changed')
        if '\nARCHIVED MATERIAL\n' + c['histories'][p['condition']]['text'] + '\nFIXED CONTEXT' not in p['prompt']: raise ValueError('History differs')
        before = p['prompt'].split('\nARCHIVED MATERIAL\n')[0]
        bycase[p['case_id']][p['condition']] = (len(ids), th(before))
        out.append({'request_id': p['candidate_request_id'], 'prompt_sha256': p['prompt_sha256'], 'token_ids_sha256': r['token_ids_sha256'],
                    'native_log': r['native_call_log'], 'input_tokens': len(ids), 'context_remaining_at_256': 4096-len(ids)-256,
                    'evidence_prefix_sha256': th(before), 'native_bytes_verified': True, 'new_tokenization': False})
    for cells in bycase.values():
        if set(cells) != set(CELLS) or len({v[1] for v in cells.values()}) != 1: raise ValueError('Condition/evidence equality')
        if len({cells[k][0] for k in CELLS[:5]}) != 1: raise ValueError('Token match')
    return out


def control_review(c):
    text = c['histories']['D_procedural']['text']
    values = [r['value'] for r in c['required_components']]
    leakage = [v for v in values if v.lower() in text.lower()]
    assignment = c['domain']['assignment']
    return {'case_id': c['case_id'], 'text': text, 'text_sha256': th(text),
            'AI_proposed_classification': 'INVALID_CONTROL' if leakage else 'LENGTH_MATCHED_DIAGNOSTIC_CONTROL',
            'token_equivalence': 'VERIFIED_NATIVE_FULL_PROMPT',
            'format_equivalence': 'Same archive section/quotation/speaker; multi-sentence first-person narrative versus one structured dated assertion. Discourse form is not equal.',
            'answer_information': 'No literal required value detected; active E1V1 repeats answer support, so information equivalence is not claimed.',
            'instructional_neutrality': 'NOT_ESTABLISHED: read/check/no other entries can prime verification, conservative reporting or omission.',
            'stylistic_neutrality': 'NOT_ESTABLISHED: first-person procedural narrative differs from key/value/date record.',
            'topic_neutrality': ('Strong archive/folder/shelf overlap with archive retrieval setting.' if c['domain']['id'] == 'archive' else f"Record/folder discourse overlaps the common ledger task, although {c['domain']['id']} has no literal {assignment} in the control."),
            'temporal_neutrality': 'No dates or validity intervals; past tense and then/after encode sequence. Not temporally equivalent.',
            'entity_value_leakage': leakage, 'personal_information': f"Attributes reading/closing/leaving actions to {c['persona_entity']}; additional fictional behavior, not an answer value.",
            'pragmatic_risk': 'Repeated no-notes/no-entries clauses may bias response length or willingness to add information; effect unmeasured.',
            'reference_stability': 'Ledger answer unchanged; no observed contradiction or required-value leakage.',
            'human_decision': '', 'reviewer_id': '', 'correction': ''}


def dependency_audit(cases, prior):
    skeletons = Counter(question_skeleton(c) for c in cases)
    grouped = defaultdict(list)
    for c in cases: grouped[c['speaker_id']].append(c)
    old_questions = {r['current_question'] for r in prior}
    old_evidence = '\n'.join(r['trusted_evidence'] for r in prior)
    rows = []
    for c in cases:
        # Levenshtein-like sequence ratio is a reproducible lexical diagnostic, not semantic independence.
        best = max(prior, key=lambda p: difflib.SequenceMatcher(None, c['question'].lower(), p['current_question'].lower()).ratio())
        rows.append({'case_id': c['case_id'], 'exact_prior_question': c['question'] in old_questions,
                     'persona_in_prior_evidence': c['persona_entity'] in old_evidence, 'other_person_in_prior_evidence': c['other_person'] in old_evidence,
                     'closest_prior_question': best['current_question'], 'lexical_sequence_ratio': difflib.SequenceMatcher(None,c['question'].lower(),best['current_question'].lower()).ratio(),
                     'question_skeleton': question_skeleton(c), 'template_reuse_count': skeletons[question_skeleton(c)]})
    cross = []
    for t in range(4):
        group = [c for c in cases if c['template_block'] == t]
        cross.append({'template_block':t,'cases':len(group),'target_is_persona':sum(c['target_entity']==c['persona_entity'] for c in group),
                      'current':sum(c['date_type']=='current' for c in group), 'style_brief':sum('brief direct' in c['persona_profile'] for c in group)})
    return rows, {'cases':len(cases),'speakers':len(grouped),'unique_question_strings':len({c['question'] for c in cases}),
        'unique_full_evidence':len({c['trusted_evidence'] for c in cases}), 'abstract_question_grammars':len(skeletons),
        'question_grammar_frequency':dict(skeletons),'template_target_cross_tab':cross,
        'same_domain_speaker_pairs':sum(g[0]['domain']['id']==g[1]['domain']['id'] for g in grouped.values()),
        'prior_exact_questions':sum(r['exact_prior_question'] for r in rows),
        'prior_name_reuse':sum(r['persona_in_prior_evidence'] or r['other_person_in_prior_evidence'] for r in rows),
        'reference_value_reuse_within_bank':len([v for v,n in Counter(r['value'] for c in cases for r in c['required_components']).items() if n>1]),
        'warning':'Fresh IDs/values do not make 288 independent linguistic templates. Same service-ledger construction as development; publication scope must be conditional unless independently authored task families are added under an amendment.'}


def contrasts():
    out=[]
    for name,w in WEIGHTS.items():
        cells=[c for c,v in w.items() if v]
        risks=['Names, assignment values and/or validity intervals move with source selection; identical trusted ledger remains sufficient.']
        if 'D_procedural' in cells: risks.append('Procedural narrative has verification/style/topic/chronology cues; diagnostic comparison only.')
        if 'H_none' in cells: risks.append('No-history prompt is shorter; length and archive-content effects are bundled.')
        out.append({'contrast':name,'weights':w,'eligible_cases':288,'unit':'paired case, two cases per speaker',
            'identified_intervention':'Weighted contrast of the specified E(entity-match)/V(query-interval-match) source-selection packages or listed baseline packages.',
            'known_confounds':risks,'supported':'Finite-template synthetic task package effect conditional on model/template/budget and registered measurement.',
            'unsupported':'Pure topical relevance, pure temporal cognition, internal mechanism, complete S/F/H or full-cohort Base/Instruct interaction.',
            'primary_for': ['temporal_Incorrect_label_incidence','task_success'] if name in ('E','V','ExV') else [],
            'same_original_weights':True})
    return out


def main():
    cases=read(BANK/'candidate_bank_v1.json')['cases']; prompts=read(BANK/'base_candidate_prompts_v1.json'); native=read(BANK/'native_tokenizer_validation_v1.json')
    rows=[]; histories=[];controls=[]
    for c in cases:
        r,h=inspect_case(c);rows.append(r);histories.extend(h);controls.append(control_review(c))
    token=token_check(prompts,native,{c['case_id']:c for c in cases})
    oldb=read('docs/validation/p1b/confirmed_analysis_v1/analysis_v1/unblinded_analysis_dataset_v1.json')['rows']
    oldc=[r['original_AI_proposal'] for r in read('docs/validation/p1c/confirmed_semantic_v1/registration/confirmed_annotations_v1.json')['primary']]
    prior=list({(r['current_question'],r['trusted_evidence']):r for r in oldb+oldc}.values())
    overlaps,dep=dependency_audit(cases,prior)
    csvwrite(DEST/'case_scientific_review_v1.csv',rows);write(DEST/'active_history_counterfactuals_v1.json',histories)
    csvwrite(DEST/'control_semantic_risks_v1.csv',controls);write(DEST/'tokenizer_evidence_verification_v1.json',{'identity':native['identity'],'rows':token,'method':'Reverified exact native logs and unchanged prompt bytes; no repeated native calls or model inference. Tokenizer detokenization and generation-time prefill equality remain final preflight checks.'})
    csvwrite(DEST/'prior_overlap_and_template_audit_v1.csv',overlaps);write(DEST/'dependency_summary_v1.json',dep)
    write(DEST/'contrast_interpretation_inventory_v1.json',contrasts())
    # First-pass review hides treatment identity, AI suggestions, expected effects and token statistics.
    order=list(range(len(cases)));random.Random(716701).shuffle(order);review=[];mapping=[]
    for i,j in enumerate(order,1):
        c=cases[j];aid=f'CR{i:03d}'
        review.append({'review_id':aid,'candidate_text':c['histories']['D_procedural']['text'],'question':c['question'],
                       'trusted_evidence':c['trusted_evidence'],'fixed_context':c['fixed_context'],'requested_date':c['query_date'],
                       'required_components':c['required_components'],'answer_leakage':'','instructional_priming':'','style_priming':'','topic_priming':'',
                       'temporal_priming':'','naturalness':'','researcher_decision':'','evidence_and_reason':'','reviewer_id':'','actual_review_time':''})
        mapping.append({'review_id':aid,'case_id':c['case_id'],'condition':'D_procedural','text_sha256':th(c['histories']['D_procedural']['text'])})
    csvwrite(DEST/'control_review_masked_v1.csv',review);write(DEST/'withheld_control_mapping_v1.json',{'seed':716701,'rows':mapping,'masking_limit':'All items are control candidates; content reveals procedural character. Withheld file is not OS-access-controlled; distribute review CSV alone.'})
    summary={'version':'p1d_scientific_census_v1','case_decisions':dict(Counter(r['AI_proposed_classification'] for r in rows)),
        'control_decisions':dict(Counter(r['AI_proposed_classification'] for r in controls)), 'history_records':len(histories),
        'token_prompts':len(token),'token_range':[min(r['input_tokens'] for r in token),max(r['input_tokens'] for r in token)],
        'active_and_control_matches':288,'direct_full_answer_positive_controls':sum(c['family']=='single_fact' for c in cases),
        'partial_answer_positive_controls':sum(c['family'] in ('multi_component','context_followup') for c in cases),
        'chain_entry_positive_controls':sum(c['family']=='relational_integration' for c in cases),
        'human_confirmations':0,'new_inference':0,'candidate_frozen':False,'source_sha256':{(BANK/n).as_posix():sha(BANK/n) for n in ('candidate_bank_v1.json','base_candidate_prompts_v1.json','native_tokenizer_validation_v1.json','metric_applicability_candidate_v1.json')},
        'review_method':'AI-assisted inspection of all finite question/control grammars plus exhaustive case-specific ledger, text, reference and routing checks. Not 288 independent human reviews.'}
    write(DEST/'scientific_audit_summary_v1.json',summary);print(json.dumps(summary))

if __name__=='__main__':main()
