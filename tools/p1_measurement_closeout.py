"""Consolidated P1 closeout: no inference, no human registration, no P6 work."""
from collections import Counter
import json
from pathlib import Path
import re
import statistics
import p1_measurement_run as r
from p1_factorial_descriptive import cluster_sensitivity
from p1d_design import csvwrite


def prepare():
    out=r.OUT;ad=out/'A_C0'/'measurement_v1';cd=out/'C_DIAGNOSTIC'/'measurement_v1'
    a=r.s.load(ad/'summary_v1.json');original=r.s.load(cd/'summary_v1.json')
    aj=r.s.load(ad/'joined_AI_proposals_v1.json');cj=r.s.load(cd/'joined_AI_proposals_v1.json')
    percase=[]
    for cid in sorted({x['case_id'] for x in cj}):
        old=next(x for x in aj if x['case_id']==cid);arms={x['diagnostic_arm']:x for x in cj if x['case_id']==cid}
        percase.append({'case_id':cid,'speaker_id':old['speaker_id'],'family':old['family'],
            'original_review_id':old['review_id'],'original_task':old['task_success'],'original_complete':old['semantic_completeness'],
            'original_supported':old['supported'],'required':old['required'],
            **{arm:{'review_id':x['review_id'],'task':x['task_success'],'complete':x['semantic_completeness'],
                    'supported':x['supported'],'task_difference':int(x['task_success']=='Success')-int(old['task_success']=='Success'),
                    'complete_difference':int(x['semantic_completeness']=='YES')-int(old['semantic_completeness']=='YES'),
                    'supported_difference':x['supported']-old['supported']} for arm,x in arms.items()}})
    r.s.save(cd/'paired_case_comparison_v1.json',percase);csvwrite(cd/'paired_case_comparison_v1.csv',percase)
    c={**original,'version':'p1_C_diagnostic_summary_v2','supersedes':str(cd/'summary_v1.json'),
       'superseded_sha256':r.s.sha256(cd/'summary_v1.json'),
       'Wilson_95_descriptive_iid_approximation':None,
       'correction':'Do not report the v1 pooled 16-output iid interval: there are eight paired speakers/cases. Preserve the original summary and use whole-case resampling.',
       'paired_sensitivity':{arm:cluster_sensitivity([x[arm]['task_difference'] for x in percase]) for arm in ('concise','date_slots')},
       'actual_experimental_units':{'cases':8,'speakers':8,'paired_new_outputs_per_case':2,'shared_ancestors':4},
       'all_48_outputs_units':'32 unique calibration cases; category C repeats eight of those cases. Not 48 independent cases.'}
    r.s.save(cd/'summary_v2.json',c)
    r.s.save(out/'cumulative_authorization_ledger_v1.json',r.cumulative())
    evidence_paths=[ad/'AI_proposals_UNCONFIRMED_v1.json',cd/'AI_proposals_UNCONFIRMED_v1.json',
                    out/'C_DIAGNOSTIC'/'prospective_policy_v1.json',cd/'summary_v2.json']
    r.s.save(out/'calibration_measurement_gate_v1.json',{'decision':'NO_GO_DEVELOPMENT_PILOT',
        'recorded_utc':r.s.b.utc_now(),'decision_type':'AI-assisted scientific readiness recommendation, not a researcher rejection',
        'pilot_manifest_sha256':r.s.sha256(out/'B_FACTORIAL_manifest_v1.json'),
        'evidence_sha256':{str(p):r.s.sha256(p) for p in evidence_paths},'selected_output_instruction':None,
        'reason':'Neither predeclared diagnostic arm has a correct complete answer in each task family; BF opportunity and automatic semantic coverage remain inadequate.',
        'target_range_not_hard_gate':True,'no_case_selection_or_pilot_prompt_change':True,'additional_inference_scheduled':False,
        'authorization_remains_valid':True,'remaining_budget':r.cumulative()['remaining_authorization'],
        'not_a_new_permission_gate':'No repeated authorization is requested for ordinary P1 development; actual scientific readiness is unresolved.'})
    cases=r.s.load(out/'materials_v1.json')['cases'];valid=[]
    templates=[]
    for case in cases:
        templates.append(re.sub(r'2051-\d{2}-\d{2}','DATE',case['question'].replace(case['speaker_name'],'ENTITY')))
        valid.append({'case_id':case['case_id'],'pool':case['pool'],'family':case['family'],
            'scientific_proposal':'VALID_WITH_LIMITATIONS','reference_witnesses':case['reference'],
            'date_type':case['date_type'],'evidence_rows':len(case['facts']),
            'limits':'Four shared task ancestors; fixed source-ID roles and B/D coding shortcuts; synthetic profiles; task/template covariance; no independent validity judgment.',
            'control_status':'LENGTH_MATCHED_DIAGNOSTIC_CONTROL' if case['pool']=='factorial' else 'NOT_APPLICABLE',
            'researcher_decision':'','human_timestamp':None})
    csvwrite(out/'material_validity_proposals_v1.csv',valid)
    r.s.save(out/'dependency_inventory_v1.json',{'calibration_cases':32,'factorial_cases':8,
        'unique_exact_questions':len({c['question'] for c in cases}),'abstract_question_strings':len(set(templates)),
        'template_counts':dict(Counter(templates)),'construction_ancestors':4,'linguistic_profile_specifications':2,
        'split_key':'Full speaker identities, question strings, evidence records and task-value codes are disjoint across pools; first names and template ancestry can repeat.',
        'independent_validation_claim':False})
    # Reuse existing authored counterexamples; do not generate another example bank.
    fp=Path('docs/validation/core_sfh_readiness_v1/fidelity_v2/authored_challenges_v2.json')
    examples=r.s.load(fp);fixture_audit=[]
    for x in examples:
        fixture_audit.append({'item_id':x['item_id'],'source_path':str(fp),'source_sha256':r.s.sha256(fp),
            'response':x['response'],'intended_distinction':x['intended_distinction'],'authored_expected':x['authored_expected'],
            'new_P1_rubric_issue':('Current P1 BF ordering rule cannot score absent acknowledgment or a promise without a delivered answer. That is insufficient opportunity under the frozen P1 rule, while the older authored key treats it as a behavioral success/failure. Do not conflate the two.'
                if x['challenge'] in ('correct_wrong_style','persona_preserved_no_task','quality_improved_persona_erased') else
                'The authored example separates correctness, delivery and persona; an intended example is not an independent validation result.'),
            'human_decision':'','human_timestamp':None})
    r.s.save(out/'fidelity_construct_audit_v1.json',{'source_sha256':r.s.sha256(fp),'items':fixture_audit,
        'observed_LF_scores':{'C0':a['metrics']['linguistic_fidelity'],'diagnostic':c['metrics']['linguistic_fidelity']},
        'observed_BF_scored':0,'observed_answer_acknowledgment_pairs':0,
        'proposal_for_future_measurement':'Prespecify separate acknowledgment occurrence, response-act ordering (including promise), and advice choice. Review whether an absent required behavior is observable noncompliance or lack of opportunity. Do not retrospectively replace current BF states.',
        'independent_human_validation':False,'new_model_generations':0})
    priorities=[]
    for category,items,dest in [('A_C0',aj,ad),('C_DIAGNOSTIC',cj,cd)]:
        for x in items:
            priorities.append({'kind':'P1 semantic proposal','item':x['review_id'],'source_path':str(dest/'AI_proposals_UNCONFIRMED_v1.csv'),
                'source_sha256':r.s.sha256(dest/'AI_proposals_UNCONFIRMED_v1.csv'),
                'priority':'HIGH' if x['review_id'] in ('AM004','AM017','AM020','AM024','AM031') or x['family']=='dated_comparison' else 'STANDARD',
                'issue':'Confirm metric-specific claims, date attachment, component delivery and fidelity opportunity; no independent reviewer inferred.',
                'researcher_decision':'','researcher_correction':'','human_timestamp':None})
    p5=Path('docs/validation/p5/oracle_diagnostic_v1/measurement_v1/paired_historical_comparison_v1.csv')
    for x in r.s.load(p5.with_suffix('.json')):
        priorities.append({'kind':'Existing P5 paired evidence, no new inference','item':x['case_id'],'source_path':str(p5),'source_sha256':r.s.sha256(p5),
            'priority':'PENDING_EXISTING_CONFIRMATION','issue':'Original Instruct and oracle semantic proposals are AI-assisted; content/length/position/salience/answer exposure jointly vary.',
            'researcher_decision':'','researcher_correction':'','human_timestamp':None})
    csvwrite(out/'consolidated_researcher_review_index_v1.csv',priorities)
    r.s.save(out/'offline_development_corrections_v1.json',{'preserved_failures':[
        'Initial material validation falsely matched common Optional-speaker boilerplate as a C0 treatment; corrected to actual optional blocks before any manifest was written.',
        'Three further material build attempts found no exact 17-token diagnostic control; no inference occurred. Expanded coherent control candidates and verified all16 full-prompt length pairs with actual native tokens.',
        'First targeted test run:3 failed,33 passed. Two failures were tuple/list factor routing after JSON decoding; one test fixture violated the repository-only writer. Corrected before inference;36 passed.',
        'v1 automatic scorer shared restricted FC/TC assignment and missed typed label syntax. v1 preserved; v2 separates interval/identity checks, supports declared label syntax and defers negated success.38 tests passed.',
        'After diagnostic invariance test:39 passed. After prepared paired estimators:44 passed.',
        'Diagnostic summary v1 contained a pooled iid Wilson interval for16 paired outputs. It is retained but superseded by v2 with eight whole-case resampling. No official inference is based on the pooled interval.'
        ],'no_output_rerun_or_overwrite':True,'no_human_adoption':True})
    return a,c,percase


def report(a,c,paired,tests):
    out=r.OUT;cd=out/'C_DIAGNOSTIC'/'measurement_v1';plan=r.s.load(out/'C_DIAGNOSTIC_manifest_v1.json')
    audit=r.s.load(cd/'execution_integrity_v1.json');ledger=r.cumulative()
    lines=['# P1 measurement diagnostic and scientific decision package — consolidated v1','',
        'Maintainer: Yaxin ZHENG. Official paper: Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models. First submission target: PLOS ONE.',
        '', '**Decision: NO-GO for the 80-request S/F/H pilot and for confirmatory freezing.** The current obstacle is scientific measurement readiness, not missing development authorization. The standing 160-request authorization remains valid, with independent category caps. No additional routine batch approval is requested.',
        '', '## Actual execution and engineering evidence','',
        f"This milestone executed exactly16 category-C CPU requests on eight previously generated calibration cases, with two instruction packages. {c['successful_requests']} successful, {c['failed_requests']} failed, zero retries. Native stops {c['native_stops']}; {c['total_output_tokens']} output tokens; mean latency {c['mean_latency_seconds']:.3f}s; observed peak working set {c['peak_working_set_observed']} bytes. Available RAM exceeded3GiB during full preflight. No memory threshold or model setting was lowered.",
        f"Raw run: `{audit['run_directory']}`. Manifest `docs/validation/p1/measurement_pilot_v1/C_DIAGNOSTIC_manifest_v1.json`, SHA-256 `{r.s.sha256(out/'C_DIAGNOSTIC_manifest_v1.json')}`. Actual prompt token range {min(x['input_tokens'] for x in plan['requests'])}–{max(x['input_tokens'] for x in plan['requests'])}. Native/official/live token arrays matched for every prompt.",
        f"Qwen/Qwen3.5-2B, third-party Q4_K_M GGUF `{plan['model']['model_sha256']}`; pinned llama.cpp b11573 `{plan['model']['backend_sha256']}`; official nonthinking template `{plan['template_sha256']}`. CPU4threads,4096context,96output,seed42,temp0,top-p1,no custom stops,no cache,no warmup. Exact upstream/distributor revisions and the partial conversion-lineage limitation remain in each manifest. No model substitution or confirmatory inference occurred.",
        'The cumulative ledger is32 A_C0 +0 B_FACTORIAL +16 C_DIAGNOSTIC =48/160 attempts. Remaining caps are0/80/32, total112, with no category transfers. The initial32-case calibration is reported once in `P1_C0_measurement_calibration_report_v1.md`; this report is the one engineering/scientific record for the16-request diagnostic and the consolidated P1 checkpoint.',
        '', '## Research question, design and identification','',
        'Can shorter requested-answer instructions or explicit date/slot instructions restore measurement adequacy on the same sufficient evidence? Calibration cases00–07 were selected as the first complete four-family block, not for favorable treatment responses. The factorial bank was frozen before all calibration outputs and remains entirely unexecuted and unchanged. These repeated cases are development comparisons, not independent replication.',
        'Concise adds answer-only/no-explanation instructions. Date-slots adds field order and requested-date interval selection. Evidence, question, references, dates, model, template and decoding remain identical. The diagnostic identifies output-instruction packages, not a pure formatting mechanism, retrieval mechanism, persona effect, or post-training effect. No oracle evidence reduction or additional P5 experiment occurred.',
        '', '| Matched eight-case configuration | AI task success | Complete form | Supported components |','| --- | ---: | ---: | ---: |',
        f"| Original C0 | {sum(x['original_task']=='Success' for x in paired)}/8 | {sum(x['original_complete']=='YES' for x in paired)}/8 | {sum(x['original_supported'] for x in paired)}/16 |"]
    for arm in ('concise','date_slots'):
        lines.append(f"| {arm} | {c['arms'][arm]['success']}/8 | {c['arms'][arm]['complete']}/8 | {sum(x[arm]['supported'] for x in paired)}/16 |")
    lines+=['', 'Both instruction arms produce8/8 complete forms and identifiable first-response candidates. Neither supplies a correct complete answer in single lookup, dual-component or dated-comparison cases in this eight-case block. Both fail the prospective all-family readiness condition. No arm is selected. The original calibration target80–95% was not a hard gate; the present NO-GO follows the additional predeclared diagnostic criteria and unresolved automatic/fidelity measurement issues.',
        'Concise improves one route case; date-slots improves the same route case but loses the previously correct other route case. Thus cleaner completion is not stable factual improvement. All negative outcomes are retained. The proposed first-response identification is AI-only; original16 AMBIGUOUS parser labels remain unchanged. Native EOS/eog compatibility and separate semantic certification remain documented. No independent boundary-accuracy claim is made.',
        '', '## Paired uncertainty and failure evidence','']
    for arm,v in c['paired_sensitivity'].items():lines.append(f"{arm}: paired task-success difference {100*v['mean']:.1f} percentage points; whole-speaker/case resampling sensitivity95% [{100*v['interval'][0]:.1f}, {100*v['interval'][1]:.1f}] points. Eight purposive cases, four shared task ancestors; not guaranteed population coverage or a significance test.")
    lines+=['', 'The pooled16-output iid interval in the initial machine summary is explicitly superseded by `C_DIAGNOSTIC/measurement_v1/summary_v2.json`; the original file remains preserved. Case contributions, both instruction arms, failures and leave-one-case-out diagnostics are retained. Across both milestones there are32 unique calibration cases, not48 independent observations.',
        '', '## Metric variance and automatic evaluation','', '| Metric | Diagnostic AI distribution | Scored | Variance | Automatic v2 agreement |','| --- | --- | ---: | ---: | --- |']
    for k,v in c['metrics'].items():
        ag=c['agreement']['v2_review_text'][k]
        lines.append(f"| {k} | {json.dumps(v['distribution'])} | {v['scored']} | {v['numeric_sample_variance']} | {ag['agreement']}/{ag['paired_comparable']} |")
    lines+=['', 'All16 diagnostic relevance and coherence scores are5, and all16 complete forms areYES: these outcomes have zero observable discrimination here, not proven zero treatment effects. Factual and task-success labels still coincide in these actual data; the constructs remain separate, as shown by complete wrong answers and the pre-existing correct-history-only counterexample. LF has some narrow surface variation but its heuristic agreement is poor. BF has zero scored opportunities; it is not a measured zero score.',
        'The conservative automatic scorer is insufficient for unattended confirmatory scoring. Date-bearing prose/slot forms can remain Unverifiable automatically despite an interpretable AI judgment. Full per-category confusion matrices, unscored coverage, disagreements, canonical syntax views and original-parser sensitivities remain machine-readable. Agreement is computed on common proposed text views; shared references, deterministic keys and AI boundary assumptions preclude independent accuracy or human inter-rater reliability claims.',
        '', '## Persona Fidelity construct audit','',
        'Reuse the existing eight authored counterexamples and separate blank fidelity/quality panels. They include correct facts/wrong style, wrong facts/right persona, truthful history/wrong behavior, promise-with-persona/no answer, and improved delivery with erased persona. These intended distinctions are not independently rated outcomes. The current BF order-only rule treats absent acknowledgment or absent final answer as insufficient opportunity; older authored keys sometimes treat these as compliance/noncompliance. The mismatch is explicitly recorded, not silently rescored.',
        'Before confirmatory freezing, review separate acknowledgment occurrence, response-act ordering and unsolicited-advice opportunity. A promise can express persona while failing the task. Absence of a target feature may be observable noncompliance even when ordering is undefined. These alternatives require a prospective rubric decision; current BF values stay unscored. Short-code length heuristics are not validated fidelity thresholds.',
        '', '## Core S/F/H readiness and final checkpoint','',
        'C0 baseline:11/32 AI successes (34.4%; descriptive Wilson95%20.4–51.7), with task-family success4/8 single,2/8 dual,5/8 chain,0/8 date comparison. The eight-case C0–C7+N_style+N_history bank is intact, native-token checked and unexecuted. Trusted evidence, questions, references, dates, speaker and fixed context are identical within each pair. Sixteen active/control pairs are token-matched; the controls remain diagnostic, not semantically neutral.',
        f"Unexecuted pilot manifest: `docs/validation/p1/measurement_pilot_v1/B_FACTORIAL_manifest_v1.json`, SHA-256 `{r.s.sha256(out/'B_FACTORIAL_manifest_v1.json')}`. Principal C3−C0 outdated-answer adoption endpoint has eight prospectively eligible cases. **Observed factorial requests:0; primary estimate:NOT_ESTIMATED.** Other S/F/H main effects, interactions and diagnostic contrasts likewise have no empirical estimates. Prepared paired estimators have only synthetic software tests; no synthetic result is presented as a model finding.",
        'Scientific case proposals remain VALID_WITH_LIMITATIONS, not researcher confirmations. There are four construction ancestors, five normalized question forms and two linguistic profile specifications. Fixed source roles and target/distractor code prefixes provide shortcuts. Exact-name separation is not linguistic or template independence. No case, question, answer or prompt was replaced using its own factorial outcome.',
        '', '## Exact remaining decisions and validation requirements','',
        'One consolidated review index links48 new item-level AI proposals and the eight existing P5 paired records. Human decision/correction/time fields remain blank. Review the full metric-specific proposals, prioritizing AM004/AM031 negative-answer completeness, AM017 conflicting support, AM020/AM024 entity/temporal attribution, and date-comparison outputs. The record must remain researcher-adopted AI assistance if adopted; no independent reviewer or inter-rater agreement may be inferred.',
        'The smallest useful next step is independent condition/AI-key-masked annotation of the existing48 outputs and the authored construct challenges, with separate quality and fidelity panels. No new model request is needed for this step. If an independent reviewer is unavailable, disclose that limitation; researcher adoption alone cannot validate automatic accuracy. Do not change this scientific status merely because software tests pass.',
        'A new independent inference sample size is not yet scientifically justified by these failed readiness checks. Before selecting it, establish usable outcome/fidelity opportunity, independently authored and counterbalanced templates, a defined speaker/template sampling frame, prespecified primary estimands and practical precision, and dependence/missingness simulations. The adopted144-speaker E/V target does not automatically justify a different core S/F/H sample. Retain the previous E/V plan and all historical precision work.',
        'Remaining GO requirements: resolve the task-family floor without outcome-based case selection; settle the prospective BF rubric and automatic claim/date-scope coverage; obtain genuine independent measurement evidence where feasible; pass the registered scientific readiness check and fresh technical preflight. Confirmatory protocol/material freezing and confirmatory execution still require explicit researcher decisions. Existing development authorization is not revoked and need not be requested again, but no further batch is scheduled merely to consume the unused112 requests.',
        '', '## P5 closeout, work tree and publication','',
        'P5 is administratively/scientifically closed as a completed development diagnostic with pending semantic adoption: existing2/8 versus8/8 AI proposals remain unchanged. Eight paired source records contain exact request/output hashes and evidence. The reference-aware oracle package altered evidence content/length/position/salience/literal answer exposure; it identifies no pure retrieval/sufficiency/persona effect. No additional P5 run occurred.',
        'P0 PASS/frozen; P1 ACTIVE but factorial measurement execution NO-GO; P2 knowledge utilization PAUSED; P3 model/context PAUSED; P4 real-speaker PAUSED; P5 current diagnostic COMPLETED with human semantic review pending; P6 PAUSED. No new paused-phase designs, algorithms, training or literature expansion were undertaken. The negative ESCP baseline result remains unchanged. PLOS ONE remains the first target; no originality, confirmatory finding, equivalence or publication readiness is claimed.',
        '', '## Validation and reproduction','',
        f"Targeted regression evidence: {tests['passed']} passed, exit code{tests['exit_code']}; command and complete output in `docs/validation/p1/measurement_pilot_v1/targeted_regression_v1.json`. Original48 request/HTTP/result inventories reconstruct exactly. All earlier source observations and frozen artifacts are preserved; the research log is append-only.",
        'Generation command used: `.venv/Scripts/python.exe tools/p1_measurement_run.py run --category C_DIAGNOSTIC --preflight docs/validation/p1/measurement_pilot_v1/C_DIAGNOSTIC_preflight_v1.json`. The completed batch cannot be repeated by that command. Read-only audit: `.venv/Scripts/python.exe tools/p1_measurement_run.py audit --category C_DIAGNOSTIC --output <new-workspace-path.json>`. Original native stdout/stderr, input/output IDs, seed/order, raw HTTP, exact source snapshots and reproducibility hashes remain linked. Latencies are observed development timings; light local documentation/analysis occurred, so they are not controlled hardware comparisons.',
        '', '## Hash-bound review sources','', '| Source | SHA-256 |','| --- | --- |']
    for p in (out/'A_C0/measurement_v1/AI_proposals_UNCONFIRMED_v1.csv',out/'C_DIAGNOSTIC/measurement_v1/AI_proposals_UNCONFIRMED_v1.csv',
              out/'consolidated_researcher_review_index_v1.csv',out/'fidelity_construct_audit_v1.json',out/'calibration_measurement_gate_v1.json',
              Path('docs/validation/p5/oracle_diagnostic_v1/measurement_v1/paired_historical_comparison_v1.csv')):
        lines.append(f'| `{p.as_posix()}` | `{r.s.sha256(p)}` |')
    path=Path('docs/P1_measurement_diagnostic_and_decision_report_v1.md')
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')


if __name__=='__main__':
    a,c,paired=prepare()
    tests=r.s.load(r.OUT/'targeted_regression_v1.json')
    report(a,c,paired,tests)
