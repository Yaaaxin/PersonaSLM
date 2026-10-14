"""Bounded development example revision and native vocabulary validation only.

No held-out material or model response is produced. Preserve every prior version.
"""
import copy
from pathlib import Path
from p1d_design import OUT, CELLS, read, write, csvwrite, sha, th, render, derive, lookup, sentence, check_case
import p1c_tokenize as native_module

DEST = Path('docs/validation/p1d/development_readiness_v1')
ALIAS_BANK = ('Quinn', 'Morgan', 'Cameron', 'Robin', 'Avery')
OPENINGS = (
    'I read the record carefully and then closed the folder after checking its cover.',
    'I read the record from beginning to end and closed the folder after checking its cover.',
    'I looked through the folder carefully and closed it after checking the cover.',
    'I checked the cover of the folder and read the record before closing it.',
)
MIDDLES = (
    'I placed it on the shelf and left the room.',
    'I put it back on the shelf and left the room without making further notes.',
    'I placed the folder on the shelf and left the room without making any further notes.',
    'I returned the folder to its usual place on the shelf before leaving the room.',
)
ENDS = ('', ' Nothing else was added.', ' I made no other entries.', ' The folder remained closed afterward.')
CONTROL_BANK = tuple(a + ' ' + b + c for a in OPENINGS for b in MIDDLES for c in ENDS)

def revise_cases():
    cases = copy.deepcopy(read(OUT / 'development_examples_v3.json')['cases'])
    changes = []
    for c in cases:
        c['version'] = 'p1d_development_examples_v4'
        c['persona_entity'] = c['target_entity']
        # Two of four follow-ups target the other person, balanced over requested date.
        if c['case_id'] in ('p1d_dev_02_1', 'p1d_dev_03_0'):
            old = c['target_entity']
            c['target_entity'], c['other_entity'] = c['other_entity'], old
            c['fixed_context'] = c['fixed_context'].replace(old, c['target_entity'])
            c['required_components'] = derive(c)
            changes.append({'case_id': c['case_id'], 'field': 'context_referent', 'before': old, 'after': c['target_entity'],
                            'reason': 'Counterbalance referent relative to persona; no outcome-based selection'})
        rebuild_histories(c)
    return cases, changes

def rebuild_histories(c):
    i = int(c['speaker_id'][-2:])
    valid = c['query_date']
    expired = '2048-01-01' if c['date_type'] == 'historical' else '2048-07-01'
    for cell in CELLS[:4]:
        e, v = int(cell[1]), int(cell[3])
        f = lookup(c['facts'], c['target_entity'] if e else c['other_entity'], 'locker', valid if v else expired)
        c['histories'][cell] = {'text': 'Archived quotation by ' + c['persona_entity'] + ': "' + sentence(f, i % 2) + '"',
            'source_id': f['id'], 'entity_match': bool(e), 'query_interval_match': bool(v),
            'answer_supporting': bool(e and v),
            'answer_competition': 'Deliberate dated value candidate; true for its stated interval'}

def replace_other_alias(c, alias):
    c = copy.deepcopy(c)
    old = c['other_entity']
    if old == c['persona_entity']:
        raise ValueError('Alias repair must not replace the persona')
    new = alias + ' ' + old.split(' ', 1)[1]
    for f in c['facts']:
        if f['entity'] == old:
            f['entity'] = new
    c['other_entity'] = new
    c['trusted_evidence'] = c['trusted_evidence'].replace(old, new)
    rebuild_histories(c)
    return c

def semantic_checks(c):
    check_case(c)
    active = [c['histories'][s] for s in CELLS[:4]]
    refs = {x['value'] for x in c['required_components']}
    control = c['histories']['D_procedural']['text']
    assert not any(value in control for value in refs)
    assert all(c['persona_entity'] in x['text'].split(': "')[0] for x in active)
    assert all('source_id' in x for x in active)
    return {'unique_reference': True, 'dated_source_lookup': True, 'literal_reference_leakage_in_control': False,
            'semantic_neutrality': 'NOT_ESTABLISHED', 'control_status': 'DIAGNOSTIC_ONLY',
            'context_referent_matches_persona': c['target_entity'] == c['persona_entity'],
            'human_review_decision': '', 'independent_validation': False}

def main():
    if (DEST / 'development_examples_v4.json').exists():
        raise FileExistsError('Preserve completed development revision')
    write(DEST / 'finite_candidate_plan_v1.json', {'alias_bank': ALIAS_BANK, 'control_bank': CONTROL_BANK,
        'selection': 'First exact native-token match in fixed bank; no generation or answer-quality criterion',
        'max_native_calls': 400, 'source_sha256': sha(OUT / 'development_examples_v3.json'), 'code_sha256': sha(__file__)})
    native_module.LOCAL = Path('results/p1d_readiness/v1/tokenizer')
    native = native_module.NativeTokenizer()
    def tokens(text):
        if len(native.calls) >= 400:
            raise RuntimeError('Bounded vocabulary-call cap reached; retain partial logs')
        return native.tokens(text)
    cases, changes = revise_cases()
    attempts = []
    # Single vocabulary-only measurement of each fixed procedural candidate.
    candidate_lengths = [len(tokens('"' + t + '"')) for t in CONTROL_BANK]
    bank_lengths = dict(zip(CONTROL_BANK, candidate_lengths))
    rows, summaries, reviews, budget_rows = [], [], [], []
    for ix, c in enumerate(cases):
        counts = {s: len(tokens(render(c, c['histories'][s]['text']))) for s in CELLS[:4]}
        if len(set(counts.values())) != 1 and c['target_entity'] == c['persona_entity']:
            for alias in ALIAS_BANK[1:]:
                candidate = replace_other_alias(c, alias)
                cc = {s: len(tokens(render(candidate, candidate['histories'][s]['text']))) for s in CELLS[:4]}
                attempts.append({'case_id': c['case_id'], 'kind': 'alias', 'candidate': alias, 'counts': cc})
                if len(set(cc.values())) == 1:
                    changes.append({'case_id': c['case_id'], 'field': 'other_entity', 'before': c['other_entity'],
                                    'after': candidate['other_entity'], 'reason': 'First native-token match in fixed alias bank'})
                    c, counts = candidate, cc
                    break
        original_control = c['histories']['D_procedural']['text']
        prefix = 'Archived quotation by ' + c['persona_entity'] + ': "'
        # Estimate candidates by token difference, then ALWAYS measure the complete prompt.
        sample = CONTROL_BANK[0]
        sample_count = len(tokens(render(c, prefix + sample + '"')))
        desired = counts['E1V1'] - sample_count + bank_lengths[sample]
        shortlist = [i for i, n in enumerate(candidate_lengths) if n == desired]
        chosen = None
        for i in shortlist:
            text = prefix + CONTROL_BANK[i] + '"'
            n = len(tokens(render(c, text)))
            attempts.append({'case_id': c['case_id'], 'kind': 'procedural_control', 'candidate_index': i,
                             'text': text, 'text_sha256': th(text), 'full_prompt_tokens': n, 'target_tokens': counts['E1V1']})
            if n == counts['E1V1']:
                chosen = i
                c['histories']['D_procedural']['text'] = text
                break
        if chosen is not None:
            changes.append({'case_id': c['case_id'], 'field': 'procedural_control', 'before': original_control,
                            'after': c['histories']['D_procedural']['text'], 'reason': 'Length matching only; semantic neutrality not certified'})
        checks = semantic_checks(c)
        for cell in CELLS:
            prompt = render(c, c['histories'][cell]['text']); ids = tokens(prompt)
            counts[cell] = len(ids)
            rows.append({'case_id': c['case_id'], 'speaker_id': c['speaker_id'], 'condition': cell,
                'prompt': prompt, 'prompt_sha256': th(prompt), 'input_token_ids': ids, 'input_tokens': len(ids),
                'trusted_evidence_sha256': th(c['trusted_evidence']), 'question_sha256': th(c['question']),
                'context_sha256': th(c['fixed_context']), 'reference_sha256': th(str(c['required_components'])),
                'reference': c['required_components'], 'context_fit_256': len(ids) + 256 <= 4096,
                'generation_authorized': False, 'split': c['split']})
        reference_text = '; '.join(x['key'] + ': ' + x['value'] for x in c['required_components']) + '.'
        budget_rows.append({'case_id': c['case_id'], 'authored_reference_answer': reference_text,
            'reference_token_ids': tokens(reference_text), 'source': 'Ledger-derived authored answer, NOT model output',
            'budget_suitability': 'Cannot establish generation completeness or termination from reference length'})
        summaries.append({'case_id': c['case_id'], 'counts': counts, 'active_equal': len({counts[s] for s in CELLS[:4]}) == 1,
            'control_equal': len({counts[s] for s in CELLS[:5]}) == 1, 'selected_control_index': chosen, **checks})
        reviews.append({'case_id': c['case_id'], 'question': c['question'], 'fixed_context': c['fixed_context'],
            'trusted_evidence': c['trusted_evidence'], 'reference': c['required_components'], 'histories': c['histories'],
            'known_risks': 'E changes entity/value cues; V changes interval/value. E1V1 is deliberately answer-supporting. Procedural reading/checking language can prime verification; no semantic neutrality claim.',
            'automated_checks': checks, 'researcher_decision': '', 'reviewer_id': '', 'human_timestamp': ''})
        cases[ix] = c
        print({'case_id': c['case_id'], 'active_equal': summaries[-1]['active_equal'], 'control_equal': summaries[-1]['control_equal']}, flush=True)
    write(DEST / 'development_examples_v4.json', {'version': 'p1d_development_examples_v4', 'cases': cases, 'independent_validation': False, 'new_generations': 0})
    write(DEST / 'development_prompts_v4.json', rows)
    write(DEST / 'revision_inventory_v4.json', changes)
    write(DEST / 'token_candidate_attempts_v1.json', attempts)
    write(DEST / 'tokenizer_validation_v2.json', {'identity': native.identity, 'cases': summaries, 'native_calls': len(native.calls),
        'source_sha256': sha(DEST / 'development_prompts_v4.json'), 'code_sha256': sha(__file__), 'new_generations': 0,
        'input_token_range': [min(x['input_tokens'] for x in rows), max(x['input_tokens'] for x in rows)]})
    write(DEST / 'authored_reference_budget_check_v1.json', budget_rows)
    csvwrite(DEST / 'development_semantic_review_v4.csv', reviews)
    print({'development_cases': len(cases), 'active_matches': sum(x['active_equal'] for x in summaries),
           'control_matches': sum(x['control_equal'] for x in summaries), 'native_calls': len(native.calls), 'new_generations': 0}, flush=True)

if __name__ == '__main__':
    main()
