"""Prepare a separately authorizable 16-request format/stop proposal; never execute."""
from pathlib import Path
import json
import random
import difflib
import re
import statistics
import p1d_budget_calibration as b
import p1c_tokenize as native_module

OUT=Path('docs/validation/p1d/final_preparation_v1')

def source_format_audit():
    source=Path('docs/validation/p1c/final_review_v1/calibration_manifest_candidate_v1.json')
    assert b.sha256(source)=='b0cf330d9dd5f7b59a186dc298c477a97bd86e06a29209805989a9f399fde02b'
    old=b.load(source)['requests'];current=b.load(b.FROZEN)['requests']
    for q in old+current:assert b.th(q['prompt'])==q['prompt_sha256']
    return {'version':'frozen_prompt_role_format_comparison_v1','source_p1c_sha256':b.sha256(source),'source_p1d_sha256':b.MANIFEST_SHA,
        'p1c_requests':len(old),'p1c_current_question_with_User_marker':sum(bool(re.search(r'\nUser: [^\n]+\nAssistant:$',q['prompt'])) for q in old),
        'p1d_requests':len(current),'p1d_current_question_without_User_marker':sum(bool(re.search(r'\nCURRENT QUESTION\n(?!User:)[^\n]+\nAssistant:$',q['prompt'])) for q in current),
        'p1c_input_token_range':[min(q['input_tokens'] for q in old),max(q['input_tokens'] for q in old)],
        'p1d_input_token_range':[min(q['input_tokens'] for q in current),max(q['input_tokens'] for q in current)],
        'p1c_context':'Assistant asks which assignment to check, followed by explicitly marked User question.',
        'p1d_context':'Assistant commits to use the ledger, followed by CURRENT QUESTION section and an unmarked question.',
        'interpretation':'Concrete prompt-framing difference supports a bounded diagnostic, not a causal explanation of between-wave outcomes. Evidence length, tasks, identities and fixed context also differ.',
        'historical_inputs_modified':False,'new_generations':0}

def reframe(prompt,question):
    old='\nCURRENT QUESTION\n'+question+'\nAssistant:'
    new='\nCURRENT QUESTION\nUser: '+question+'\nAssistant:'
    if not prompt.endswith(old) or prompt.count(old)!=1:raise ValueError('Unexpected original prompt tail')
    return prompt[:-len(old)]+new

def run():
    # This proposal follows a failed cap diagnostic, not a retrospectively registered hypothesis.
    qualification=b.load(b.OUT/'analysis_v1/budget_qualification_v1.json')
    b.require(len(qualification)==3 and not any(x['provisional_qualification'] for x in qualification),'No failed-budget justification')
    plan=b.load(b.FROZEN);sources=[q for q in plan['requests'] if q['condition']=='H_none' and q['max_new_tokens']==96]
    observed=b.load(b.OUT/'measurement_v1/execution_integrity_v1.json')['rows']
    reference_latency=statistics.mean(x['result']['latency_seconds'] for x in observed if x['request']['condition']=='H_none' and x['request']['max_new_tokens']==96)
    b.require(len(sources)==8 and {q['case_id'] for q in sources}==set(b.CASE_IDS),'Wrong development comparison')
    cases={c['case_id']:c for c in b.load(b.DEV/'development_examples_v5.json')['cases']}
    native_module.LOCAL=Path('results/p1d_final_preparation/v1/format_diagnostic_tokenizer')
    tokenizer=native_module.NativeTokenizer();rows=[];diffs=[];rng=random.Random(716708);rng.shuffle(sources)
    format_audit=source_format_audit()
    b.save(OUT/'frozen_prompt_format_comparison_v1.json',format_audit)
    for old in sources:
        c=cases[old['case_id']];prompt=reframe(old['prompt'],c['question']);ids=tokenizer.tokens(prompt)
        assert prompt.count(c['trusted_evidence'])==1 and c['fixed_context'] in prompt
        arms=['F_user_marker','F_user_marker_stops'];rng.shuffle(arms)
        diffs.append({'case_id':old['case_id'],'old_prompt_sha256':old['prompt_sha256'],'new_prompt_sha256':b.th(prompt),
            'diff':''.join(difflib.unified_diff(old['prompt'].splitlines(True),prompt.splitlines(True),fromfile='authorized_original',tofile='proposed_user_marker')),
            'old_input_tokens':old['input_tokens'],'new_input_tokens':len(ids),'token_count_change':len(ids)-old['input_tokens']})
        for arm in arms:
            row={**old,'request_id':f"p1d_format_dev_v1_{old['case_id']}_{arm}",'order':len(rows),
                'diagnostic_arm':arm,'prompt':prompt,'prompt_sha256':b.th(prompt),'input_token_ids':ids,
                'input_token_ids_sha256':b.th(str(ids)),'input_tokens':len(ids),'context_remaining':4096-len(ids)-96,
                'stop':[] if arm=='F_user_marker' else ['\nUser:','\nAssistant:','\nUSER:','\nASSISTANT:'],
                'historical_comparator_request_id':old['request_id'],'historical_comparator_request_sha256':old['request_sha256']}
            del row['request_sha256'];row['request_sha256']=b.th(json.dumps(row,sort_keys=True,separators=(',',':')));rows.append(row)
    manifest={'version':'p1d_format_diagnostic_proposed_v1','status':'PROPOSAL_NOT_AUTHORIZED','authorized_requests':0,'proposed_requests':16,
        'maximum_generated_tokens':1536,'development_cases':8,'conditions_per_case':'H_none only, two format/stop arms; no E/V factorial inference',
        'planning_wall_seconds':16*reference_latency,'cost_basis':'16 times observed H_none/96 mean latency, not measured new-format latency; startup excluded and workload/stops may change cost.',
        'source_budget_manifest_sha256':b.MANIFEST_SHA,'source_qualification_sha256':b.sha256(b.OUT/'analysis_v1/budget_qualification_v1.json'),
        'source_format_comparison_sha256':b.sha256(OUT/'frozen_prompt_format_comparison_v1.json'),
        'model':plan['model'],'native_tokenizer_identity':tokenizer.identity,'execution_order_seed':716708,'requests':rows,
        'controlled':'Same eight development cases, evidence, question content, references, context, persona, model, decoding seed and 96-token reference budget.',
        'intervention':'Add User: immediately before the current question; second arm adds conventional newline User/Assistant stops, explicitly listing title-case and uppercase variants. This addresses case-sensitive abstention in the offline two-string baseline, not an original algorithm.',
        'historical_baseline':'Reuse eight already generated H_none/96 outputs. No duplicate original requests. Baseline-versus-new runtime is not contemporaneous; future arm comparison is paired.',
        'limitations':['Development cases already inspected; not independent validation','Role framing changes token length and salience, not a pure latent mechanism',
            'H_none diagnostic cannot establish adequacy under every historical package','Stops can suppress quotations or produce empty answers; no automatic completion credit',
            'No official Base chat-template claim','Primary labels remain response_status_v1; alternative views separately reported'],
        'acceptance':'At least 8/8 complete identifiable first answers in an arm, no unresolved/answer-losing cut, separately report supported delivery, all style scores and factual errors. This is a diagnostic qualification, not main-study validation.',
        'selection':'No E/V effect signs. Compare all outcomes. Prefer stops only if first-answer content/completion is preserved and measured continuation/cost decreases; otherwise do not adopt them.',
        'stop_rule':'Fixed 16 attempts or integrity/runtime/OOM/45-minute ceiling; preserve all errors, no retries, no added cases.',
        'authorization_gate':'New explicit researcher authorization bound to this exact manifest required before any generation. Main study still separately gated.',
        'main_protocol_change':'None adopted. Successful format diagnostic would support a prospective configuration amendment and subsequent main-readiness review.'}
    b.save(OUT/'format_diagnostic_manifest_proposed_v1.json',manifest);b.save(OUT/'format_diagnostic_prompt_differences_v1.json',diffs)
    b.save(OUT/'format_diagnostic_tokenizer_validation_v1.json',{'identity':tokenizer.identity,'actual_native_calls':len(tokenizer.calls),
        'logs':[{'path':(native_module.LOCAL/'native_calls'/f'{i:04d}.json').as_posix(),'sha256':b.sha256(native_module.LOCAL/'native_calls'/f'{i:04d}.json')} for i in range(len(tokenizer.calls))],
        'input_token_range':[min(r['input_tokens'] for r in rows),max(r['input_tokens'] for r in rows)],'new_model_generations':0,
        'source_script_sha256':b.sha256(Path(__file__))})
    print({'proposed':16,'authorized':0,'native_tokenizer_calls':len(tokenizer.calls),'manifest_sha256':b.sha256(OUT/'format_diagnostic_manifest_proposed_v1.json')})

if __name__=='__main__':run()
