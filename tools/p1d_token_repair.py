"""Targeted second finite alias bank for two development examples, not held-out data."""
import copy
from pathlib import Path
from p1d_design import CELLS, read, write, csvwrite, sha, th, render
from p1d_stimulus_preparation import DEST, replace_other_alias, semantic_checks
import p1c_tokenize as native_module

def main():
    if (DEST / 'development_examples_v5.json').exists():
        raise FileExistsError('Preserve completed candidate')
    bank = ('Arwen', 'Darian', 'Marlo', 'Alwin')
    write(DEST / 'targeted_alias_plan_v2.json', {'case_ids': ['p1d_dev_05_0', 'p1d_dev_05_1'], 'ordered_bank': bank,
        'max_native_calls': 40, 'selection': 'First same alias matching all five history/control lengths in both cases',
        'reason': 'Original finite bank left two documented one-token mismatches; no model outcomes inspected',
        'code_sha256': sha(__file__)})
    native_module.LOCAL = Path('results/p1d_readiness/v1/token_repair')
    native = native_module.NativeTokenizer()
    cases = read(DEST / 'development_examples_v4.json')['cases']
    old_rows = read(DEST / 'development_prompts_v4.json')
    targets = [c for c in cases if c['case_id'].startswith('p1d_dev_05_')]
    attempts, chosen, replacements = [], None, {}
    for alias in bank:
        candidate_cases = [replace_other_alias(c, alias) for c in targets]
        counts = {c['case_id']: {s: len(native.tokens(render(c,c['histories'][s]['text']))) for s in CELLS[:5]} for c in candidate_cases}
        attempts.append({'alias': alias, 'counts': counts})
        if all(len(set(ns.values())) == 1 for ns in counts.values()):
            chosen = alias; replacements = {c['case_id']: c for c in candidate_cases}; break
    rows, summaries, reviews = [], [], []
    old_by_id = {(r['case_id'], r['condition']): r for r in old_rows}
    new_cases = []
    for original in cases:
        c = replacements.get(original['case_id'], copy.deepcopy(original))
        c['version'] = 'p1d_development_examples_v5'
        checks = semantic_checks(c)
        counts = {}
        for cell in CELLS:
            prompt = render(c, c['histories'][cell]['text'])
            old = old_by_id[c['case_id'],cell]
            ids = old['input_token_ids'] if th(prompt) == old['prompt_sha256'] else native.tokens(prompt)
            row = {**old, 'prompt': prompt, 'prompt_sha256': th(prompt), 'input_token_ids': ids, 'input_tokens': len(ids),
                'trusted_evidence_sha256': th(c['trusted_evidence']), 'context_fit_256': len(ids)+256<=4096,
                'token_provenance': 'Verified identical v4 prompt bytes' if th(prompt)==old['prompt_sha256'] else 'New native vocabulary call'}
            rows.append(row); counts[cell] = len(ids)
        summaries.append({'case_id': c['case_id'], 'counts': counts,
            'active_equal': len({counts[s] for s in CELLS[:4]})==1,
            'control_equal': len({counts[s] for s in CELLS[:5]})==1, **checks})
        reviews.append({'case_id': c['case_id'], 'question': c['question'], 'fixed_context': c['fixed_context'],
            'trusted_evidence': c['trusted_evidence'], 'reference': c['required_components'], 'histories': c['histories'],
            'automated_checks': summaries[-1], 'known_risks': 'Package E/V confounding; deliberate positive-control answer support; procedural reading/checking priming and no demonstrated neutrality; authored development templates only',
            'researcher_decision': '', 'reviewer_id': '', 'human_timestamp': ''})
        new_cases.append(c)
    write(DEST / 'development_examples_v5.json', {'version': 'p1d_development_examples_v5', 'cases': new_cases, 'independent_validation': False, 'new_generations': 0})
    write(DEST / 'development_prompts_v5.json', rows)
    write(DEST / 'targeted_alias_attempts_v2.json', {'attempts': attempts, 'selected': chosen,
        'source_v4_sha256': sha(DEST / 'development_examples_v4.json'), 'old_alias': 'Quinn Kingsley',
        'new_alias': None if chosen is None else chosen+' Kingsley', 'same_speaker_case_pair_preserved': True})
    write(DEST / 'tokenizer_validation_v3.json', {'identity': native.identity, 'cases': summaries,
        'new_native_calls': len(native.calls), 'unchanged_prompt_records_reused': sum(r['token_provenance'].startswith('Verified') for r in rows),
        'inherited_token_source_sha256': sha(DEST / 'development_prompts_v4.json'),
        'source_sha256': sha(DEST / 'development_prompts_v5.json'), 'code_sha256': sha(__file__), 'new_generations': 0})
    csvwrite(DEST / 'development_semantic_review_v5.csv', reviews)
    print({'selected_alias': chosen, 'active_matches': sum(r['active_equal'] for r in summaries),
        'control_matches': sum(r['control_equal'] for r in summaries), 'new_native_calls': len(native.calls), 'new_generations': 0})

if __name__ == '__main__':
    main()
