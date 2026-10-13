"""Render initial report drafts; documented editorial review follows rendering.

Final scientific prose may have separate, recorded editorial corrections. The
deterministic numerical reconstruction is tools/p1b_confirmed_analysis.py.
"""
from collections import Counter
import json
from pathlib import Path
import re
import statistics

import p1b_confirmed_analysis as m

P=m.PUBLIC/'analysis_v1'
A=m.core.load(P/'analysis_v1.json')
ROWS=m.core.load(P/'unblinded_analysis_dataset_v1.json')['rows']
REG=m.core.load(m.PUBLIC/'registration_v1.json')
ORDER=['C1-C0','C3-C0','S','F','H','SxF','SxH','FxH','SxFxH']
LINK='validation/p1b/confirmed_analysis_v1/analysis_v1/'
HEADER='Maintainer: Yaxin ZHENG. Paper: *Understanding the Effects of Persona Conditioning on Dialogue Reliability in Small Language Models*. Target: PLOS ONE. Protocol v1.1 remains formal; v1.2 Revised Proposed r1 is unadopted. Exploratory development evidence only. No new inference.\n\n'


def table(headers,rows):
    def cell(x):return str(x).replace('|',' / ').replace('\n',' ')
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(cell(v) for v in row)+' |\n' for row in rows)+'\n'


def fmt(x):return 'unavailable' if x is None else f'{x:.4f}'
def pc(n,d):return f'{n}/{d} ({100*n/d:.2f}%)'
def group(kind,key):return next(g for g in A['group_summaries'] if g['group_type']==kind and g['group']==key)
def eff(metric,contrast,policy='boundary_conservative',family='ALL'):
    return next(x for x in A['effect_summary'] if x['metric']==metric and x['contrast']==contrast and x['policy']==policy and x['family']==family)
def loso(metric,contrast,policy):
    v=[r['estimate'] for r in A['speaker_sensitivity'] if r['metric']==metric and r['contrast']==contrast and r['policy']==policy and r['estimate'] is not None]
    return f'[{fmt(min(v))}, {fmt(max(v))}]' if v else 'unavailable'
def effect_table(metrics,policy):
    return table(['Contrast']+metrics,[[c]+[fmt(eff(k,c,policy)['estimate']) for k in metrics] for c in ORDER])
def detail_table(metric,policy):
    data=[]
    for c in ORDER:
        x=eff(metric,c,policy)
        data.append([c,f"{x['evaluable_cases']}/{x['eligible_cases']}",x['speaker_clusters'],fmt(x['estimate']),
            f"[{fmt(x['lower'])}, {fmt(x['upper'])}]",f"{x['positive_cases']}/{x['negative_cases']}/{x['zero_cases']}",
            f"[{fmt(x['unknown_lower'])}, {fmt(x['unknown_upper'])}]",loso(metric,c,policy)])
    return table(['Contrast','Evaluable/eligible cases','Eligible speakers','Estimate','Empirical 95% interval','Positive/negative/zero','All-eligible unknown bounds','Leave-one-speaker-out range'],data)
def prose_spacing(text):
    # Presentation only. Protect code and link destinations (including file hashes).
    parts=re.split(r'(`[^`]*`|\]\([^)]*\))',text)
    for i in range(0,len(parts),2):
        value=parts[i]
        value=re.sub(r'(?<=[a-z])(?=\d)', ' ', value)
        value=re.sub(r'(?<=\d)(?=[a-z])', ' ', value)
        value=re.sub(r'(?<=\d)(?=Correct|Incorrect|Unverifiable|COMPLETE|CROSS_TURN|TRUNCATED|AMBIGUOUS|FULL_ANSWER|PARTIAL|NO_FINAL_ANSWER)', ' ', value)
        for old,new in {'fourare':'four are','fourerrors':'four errors','Fourerrors':'Four errors',
            'onepartial':'one partial','oneambiguous':'one ambiguous','oneunknown':'one unknown',
            'onefinal':'one final','onecase':'one case','oneBase':'one Base','oneQwen':'one Qwen',
            'fiveTRUNCATED':'five TRUNCATED','zeroCOMPLETE':'zero COMPLETE',
            'nine speakers':'nine speakers','onlythree':'only three','threepairedcases':'three paired cases',
            'one human':'one human','C0errors':'C0 errors','SxHvaries':'SxH varies',
            'FactualC':'Factual C','both0':'both 0','labels,one':'labels, one',
            'coherence5throughout':'coherence 5 throughout','BR168span':'BR168 span',
            'oneambiguousspan':'one ambiguous span','all24relevance':'all 24 relevance',
            'all34factual':'all 34 factual','all192ordinal':'all 192 ordinal',
            'TemporalSxH':'Temporal SxH','right/wrong':'right/wrong'}.items():value=value.replace(old,new)
        parts[i]=value
    return (''.join(parts).replace('P1 b','P1b').replace('p 1 b','p1b').replace('Qwen 3.5','Qwen3.5')
            .replace('response_status_v 1','response_status_v1').replace('b 11573','b11573')
            .replace('Protocol v 1.1','Protocol v1.1').replace('v 1.2 Revised Proposed r 1','v1.2 Revised Proposed r1'))
def write(name,title,text,append=False):
    text=prose_spacing(text)
    p=Path('docs')/(name+'.md')
    if append:
        old=p.read_bytes();backup=m.LOCAL/(name+'_before.bin')
        with backup.open('xb') as f:f.write(old)
        with p.open('ab') as f:f.write(('\n\n## Researcher-confirmed P1b calibration addendum\n\n'+HEADER+text).encode('utf-8'))
        assert p.read_bytes().startswith(old)
    else:
        with p.open('x',encoding='utf-8') as f:f.write('# '+title+'\n\n'+HEADER+text)


overall=group('ALL','ALL')
annotation='''## Registration and integrity

The researcher explicitly approved all 192 proposed records in the current instruction. The source retains its UNCONFIRMED filename and original bytes. A new masked [final annotation CSV](validation/p1b/researcher_confirmed_annotation_v1.csv) and [provenance register](validation/p1b/confirmed_analysis_v1/registration_v1.json) implement `p1b_confirmed_ai_adoption_v1`.

The final CSV preserves every original 48-column value, including original blank `human_*` fields, and appends authoritative `confirmed_*` decisions and `registration_*` provenance. Blank original fields mean the researcher did not originally enter scores into those fields, not that the appended decisions remain pending. The registration metadata uses reviewer_id Yaxin_ZHENG, review_status RESEARCHER_CONFIRMED, decision_source researcher_confirmation, annotation_origin AI_assisted_condition_masked_review, and final_decision_authority researcher. This non-destructive representation avoids rewriting analytical provenance or collapsing YES/PARTIAL/NO into an older binary completeness schema.

Process: condition-label-masked semantic material; AI-assisted categorical/numerical proposals; researcher verification and adoption of all 192 proposals. No per-record label was corrected during import. Source evidence quotations, explanations, uncertainties and priorities remain AI-assisted material adopted by the researcher, not independently written human notes. The instruction is the confirmation source; no review timestamp, signature, second rater or agreement statistic is invented. Registration time is an engineering timestamp. Prior knowledge and text cues limit blinding.

All 35 original master fields match in each of 192 unique responses. All 24 cases have eight cells; speaker mapping yields 12 speakers. Every supporting source quotation is verbatim in the supplied trusted evidence. Final file SHA-256: `'''+REG['final_annotation']['sha256']+'''`. Frozen dataset SHA-256: `'''+m.core.DATA_SHA+'''`. Frozen manifest SHA-256: `'''+m.core.MANIFEST_SHA+'''`.

Saved tokenizer events, prompt/token hashes, original inference sources and local model/backend files were verified without starting a server. Model SHA-256 `ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`; backend `71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`, Qwen3.5-2B-Base Q4_K_M / llama.cpp b11573. See [offline identity](validation/p1b/confirmed_analysis_v1/offline_identity_v1.json); its reused readiness labels refer to the historical preflight workflow, not withdrawal of the present authorization. All 1831 original calibration artifact hashes matched before registration.

## Adopted labels and evaluation coverage

'''+table(['Dimension','Actual labels','Frozen eligible','Missing annotations'],[
    ['Factual consistency',overall['factual_consistency'],192,0],['Temporal consistency',overall['temporal_consistency'],88,0],
    ['Response relevance',overall['response_relevance'],192,0],['Conversational coherence',overall['conversational_coherence'],192,0],
    ['Semantic completeness',overall['semantic_completeness'],192,0],['Answer delivery',overall['answer_delivery'],192,0]])+'''
The 104 temporal N/A records are outside temporal eligibility. Unverifiable is an entered semantic judgment, not missing annotation or Incorrect. Claim-level correctness here means an **output-level judgment about its delivered factual claims**; no atomic-claim enumeration/denominator was collected. Do not report 137 as a count of independently verified atomic claims.

## Boundary scope and analysis gate

BR168 remains AMBIGUOUS under response_status_v1 and retains its supplied span, including an extra generated factual question. Its adopted labels are Correct, FULL_ANSWER, YES, relevance5/coherence4. No new human structural PASS was supplied. The old two-stage importer is preserved; this separately versioned adapter registers the semantic set actually authorized, not invented Stage B entries. `boundary_conservative` retains that record but treats its numerical semantic value as unknown. `confirmed_span_sensitivity` uses all adopted labels on the exact supplied spans. The other191 units use existing identifiable-span evidence, not fabricated human structural review.

Registration and specification were written before joining treatments in this analysis. Existing earlier structural analyses were already known, so this is not first-ever blinding or prospective preregistration. The separate [unblinded analysis dataset]('''+LINK+'''unblinded_analysis_dataset_v1.json) binds the original protected mapping. Original review CSVs remain masked. Exclusive-create writes and hash checks reject replacement or tampering.

## Reproducibility and status

Commands: `python tools/p1b_confirmed_analysis.py register`, then `python tools/p1b_confirmed_analysis.py analyze --output NEW_DIRECTORY`, using the project virtual environment. Two independent reconstructions produced byte-identical numerical datasets/tables; runtime manifests naturally have separate timestamps. Full suite:712passed,0failed,0reported warnings,40.41s,exit0. [Delivery evidence](validation/p1b/confirmed_analysis_v1/delivery_v1.json) preserves exact commands, Git state and original-history verification. Semantic registration PASS; evidence does not establish independent annotation reliability or publication readiness.
'''
write('P1b_researcher_confirmed_annotation_report','P1b Researcher-Confirmed Semantic Annotation Registration',annotation)

analysis='''## Estimands and units

The analysis population is24 paired development cases in12 synthetic speakers, not192 independent observations. Conditions retain the frozen S/F/H routing. C1-C0 and C3-C0 are simple added-package contrasts at the other factors zero. S/F/H average four on-minus-off comparisons (weights +/-0.25). Pairwise interactions average difference-in-differences over the third factor (+/-0.5); SxFxH is the third-order difference (+/-1). [Exact specification](validation/p1b/confirmed_analysis_v1/factorial_specification_v2.json) was frozen after source-rating inspection but before this treatment join. No protocol amendment or neutral-adjusted contrast is made.

Categorical label-membership contrasts use the whole eligible category distribution. A zero for the Correct-label indicator means a different observed label, **not automatic factual Incorrect**. The separate Correct-versus-Incorrect sensitivity treats Unverifiable as unknown and uses an evaluable subset. All eligible cases remain in the reported denominators and signed unknown-value bounds. No C0-correct filter or outcome-based exclusion is applied.

## Main numerical inventory

The following first table is the complete **confirmed-span sensitivity**: all192 adopted labels, with the unresolved BR168 unit explicitly included. It facilitates reproduction of the confirmed set; the conservative table below accounts for boundary uncertainty. Values are proportions for label/task outcomes and descriptive score points for ordinal outcomes. Multiplying a proportion difference by100 gives percentage points.

'''+effect_table(['factual_correct_label','temporal_correct_label','task_success','response_relevance','conversational_coherence'],'confirmed_span_sensitivity')+'''
Boundary-conservative point estimates (23/24 evaluable cases for non-temporal semantics; temporal11/11, because BR168 is temporal N/A):

'''+effect_table(['factual_correct_label','temporal_correct_label','task_success','response_relevance','conversational_coherence'],'boundary_conservative')+'''
The conservative assessed-only mean is a changed coverage subset and is not silently presented as an unbiased full-population estimand. Bounds retain the24eligible units. Structural endpoints remain fully evaluable. The full machine record contains all25endpoint/sensitivity representations, both boundary policies and all nine contrasts, including every category indicator and ordinal threshold.

## Uncertainty, sign distribution and missingness

Whole-speaker bootstrap:10,000 draws,seed714005; both cases and all cells move together. The temporal subset has11cases/nine speakers. These are empirical exploratory percentile intervals, potentially unstable with12 purposive clusters, without simultaneous coverage, annotation uncertainty, repeated-model-seed uncertainty or population significance. Intervals excluding zero are not confirmatory discoveries. Degenerate intervals cannot prove absence. No p-values or post-hoc significance selection is used.

Boundary-conservative factual Correct-label incidence:

'''+detail_table('factual_correct_label','boundary_conservative')+'''
Boundary-conservative temporal Correct-label incidence:

'''+detail_table('temporal_correct_label','boundary_conservative')+'''
Factual Correct-versus-Incorrect evaluable-only sensitivity; Unverifiable stays unknown:

'''+detail_table('factual_assessable_binary','boundary_conservative')+'''
Temporal Correct-versus-Incorrect evaluable-only sensitivity:

'''+detail_table('temporal_assessable_binary','boundary_conservative')+'''
Unknown bounds use sign-aware worst/best assignments within each case before averaging; they are not confidence intervals. Changing a condition's number of Unverifiable replies can change Correct-label prevalence without demonstrating more false statements. In fact, simple factual assessed-only contrasts are both0 here, while full-label incidence decreases byone case in each. This discrepancy must remain visible.

## Heterogeneity and cancellation

Temporal SxH averages0, but contributions are C_L1:+0.5,C_L3:-0.5,G_L1:-1,H_L3:+1. Removing one speaker changes the estimate across negative and positive values. A zero marginal interaction is not evidence that every case has zero interaction. The positive triple categorical contrast likewise does not establish a stable higher-order mechanism; compare its signed bounds, small effective samples and sensitivity to how Unverifiable is represented.

The confirmed-span H task-success average is-0.1875; leave-one-speaker-out estimates range-0.2045 to-0.1364. Contributions include both signs and span multiple families; history content, length, topic relevance and date status remain bundled. The raw C0 already hasfour factual/temporal errors. Neither these errors nor a history difference proves an isolated stale-memory mechanism.

Relevance/coherence are ordinal. Full category distributions, floor/ceiling frequencies and thresholds >=2,3,4,5 are retained. Threshold contrasts provide an ordinal sensitivity without assuming equal distances between adjacent ratings; threshold-specific results must not be selected for favorable signs. Family analyses have onlythree cases and are descriptive. Persona Fidelity remains unmeasured and separate.

## Full case and speaker evidence

- [All case-level contrasts]('''+LINK+'''case_contrasts_v1.csv):10,800 rows, including explicitly inapplicable cases, cell values, analysis states and bounds.
- [Effect summaries]('''+LINK+'''effect_summary_v1.csv):4,050 rows, all contrasts/policies/families.
- [Leave-one-speaker-out diagnostics]('''+LINK+'''speaker_sensitivity_v1.csv):5,400 rows.
- [Metric coverage]('''+LINK+'''metric_coverage_v1.csv):2,050 rows.
- [Full deterministic analysis]('''+LINK+'''analysis_v1.json) and [input/output manifest]('''+LINK+'''analysis_reproducibility_manifest_v1.json).

Results are development observations under one Base/GGUF/backend/template configuration. No pure style mechanism, independent interaction law, general factual accuracy, confirmed null, natural-person generalization or novelty claim follows.
'''
write('P1b_exploratory_factorial_analysis','P1b Exploratory Factorial Analysis',analysis)

errors=m.temporal_errors(ROWS)
case_errors=Counter(r['case_id'] for r in errors)
error_text='''## Separate denominators and adopted factual judgments

Factual labels:137Correct/192 (71.35%),34Incorrect/192 (17.71%),21Unverifiable/192 (10.94%). No missing annotation or factual N/A. The assessable subset is171responses;137/171=80.12% is conditional on assessability and must not replace the eligible-denominator distribution. These are output-level claim-consistency labels, not independently atomized claim precision. Of137Correct responses,110 are full correct answers and27 are partial supported responses.

Temporal labels:40Correct/88 (45.45%),34Incorrect/88 (38.64%),14Unverifiable/88 (15.91%);104additional records are frozen N/A. The assessable temporal subset is74;40/74=54.05% is a selected-subset description. No N/A is assigned a truth value.

## Exact factual-temporal overlap

'''+table(['Factual / temporal labels','Responses'],A['factual_temporal_overlap'].items())+'''
All34factual Incorrect labels coincide with temporal Incorrect labels; this wave does not provide34additional independent temporal failures. These ratings overlap by definition and content, not evidence for independent mechanisms. Some Unverifiable outputs are promises or unfinished reasoning; none is automatically converted to Incorrect.

## Temporal contradiction inventory

Every error has a preserved full model claim, exact trusted-evidence quotations, expected components and the adopted AI-assisted explanation in [the34-row evidence table]('''+LINK+'''temporal_error_evidence_v1.csv). The following task grouping is post-review analyst description, not a new human code or causal attribution.

'''+table(['Case','Errors across eight conditions'],sorted(case_errors.items()))+'''
C-family errors select an interval-incompatible counter, including the wrong preceding-day counter at a boundary. E-family errors use an old residence or the hub/day linked to it when the question names a later date. G-family errors choose an expired pickup site for the requested historical/current date. H errors select the old delivery desk. Correct historical facts can be false answers at the requested date. All relevant old and current source entries remain in the evidence table so reviewers can check this distinction.

Crucially, C0 hasfourerrors without any S/F/H package. A stale value may originate in the trusted dated ledger itself, not necessarily added H. Current H effects cannot isolate relevance, temporal status, first-entry bias or persona salience. Those are falsifiable prospective explanations, not established causes.

## Missing final answers and annotation limits

Twenty-one Unverifiable responses comprise17prospective-check responses plusfourunfinished thinking continuations. The distinction is answer delivery, not an assumption that every literal token in a reasoning segment is false. Three promises contain the expected shelf name and have source component coverage1/1, but remain NO_FINAL_ANSWER and Unverifiable; substring occurrence is not a committed answer.

Source coding is preserved, including implicit date interpretations, partial date-window listings and supported intermediate facts. Independent reannotation should inspect these cases, the ambiguous BR168 span and possible extra unsupported pronoun/identity claims. Do not silently revise the current version. The present researcher confirmation is not evidence of independent inter-rater reliability.

## Comparison with Wave1

Wave1 had72/72eligible factual Correct and48/48temporal Correct. P1b now has observed label variation and more component/interval demands, but datasets, applicability, prompt construction and annotation workflow differ. This is descriptive evidence of measurement range, not an isolated causal effect of task difficulty or proof of superior construct validity. Neither wave is pooled with the other; no historical rating is rewritten.
'''
write('P1b_factual_temporal_error_analysis','P1b Factual and Temporal Error Analysis',error_text)

family_table=[]
for fam in 'ABCDEFGH':
    g=group('family',fam);d=g['answer_delivery'];f=g['factual_consistency'];t=g['temporal_consistency']
    family_table.append([fam,g['cases'],g['speakers'],f.get('Correct',0),f.get('Incorrect',0),f.get('Unverifiable',0),
        d.get('FULL_ANSWER',0),d.get('PARTIAL_ANSWER',0)+d.get('PARTIAL_WITH_FALSE_CLAIM',0),d.get('NO_FINAL_ANSWER',0),
        t.get('Correct',0),t.get('Incorrect',0),t.get('Unverifiable',0),t.get('Not Applicable',0)])
task='''## Definitions and observed delivery

Answer delivery is not factual consistency. The adopted five-way labels are FULL_ANSWER110, WRONG_ANSWER_DELIVERED33, PARTIAL_ANSWER27, PARTIAL_WITH_FALSE_CLAIM1, NO_FINAL_ANSWER21. Semantic completeness is YES143,PARTIAL28,NO21. The143complete responses include33wrong delivered answers; complete is not correct.

The exploratory `task_success` diagnostic requires FULL_ANSWER, factual Correct and full source component coverage. All110FULL_ANSWER records meet these joint rules:110/192=57.29%. This is a post-generation diagnostic derived from confirmed source labels, not a replacement or newly declared primary factual endpoint. BR168 contributes one success in the confirmed-span sensitivity; conservative boundary accounting retains109known successes,82known nonsuccesses andoneunknown on the192denominator. Do not report137/192 as complete-answer accuracy.

Component fractions are adopted annotations, not an independently validated automated scorer. Some partial truthful replies have0/1requested endpoints despite a correct intermediate assertion. Three uncommitted promises have1/1surface coverage yet no delivered answer. Coverage alone is not a success rule; semantic force, requested components, factual support and delivery matter separately.

## Joint categorical inventory

'''+table(['Factual consistency','Delivery','Completeness','Structure','Count'],[[r[k] for k in ('factual','delivery','completeness','structure','count')] for r in A['joint_table']])+'''
## Task-family range

Each family has24outputs fromthreepairedcases/three speakers; speakers occur again across families and are not independent between families. A=direct retrieval; B=multiple related facts; C=temporal intervals; D=relational chains; E=relevant historical/current residence chains; F=entity identification; G=question-specific past/current validity; H=fixed-context follow-up.

'''+table(['Family','Cases','Speakers','Factual C','Factual I','Factual U','Full correct','Partial','No answer','Temporal C','Temporal I','Temporal U','Temporal NA'],family_table)+'''
D is especially diagnostic:24/24supported-claim labels but only4/24full requested answers. A remains24/24full, a valid easy baseline. B's nominally more complex third case is8/8full, so designed levels do not order empirical difficulty monotonically. E/C supply28of34contradictions; H_L2 supplies8nonanswers. F explicit identity cues permit simple identification; D's unique terminal entities can allow shortcuts. A correct final value does not prove the stated reasoning path was used.

## Ordinal outcomes and coverage

'''+table(['Scale','1','2','3','4','5','Mean','Floor','Ceiling'],[[axis]+[overall[axis].get(str(k),0) for k in range(1,6)]+[
    fmt(sum(int(k)*v for k,v in overall[axis].items())/192),pc(overall[axis].get('1',0),192),pc(overall[axis].get('5',0),192)] for axis in ('response_relevance','conversational_coherence')])+'''
All192ordinal scores are registered; conservative numerical coverage is191because of BR168. Full family/condition score distributions are in [group summaries]('''+LINK+'''group_summaries_v1.csv), alongside delivery and completeness. C has14wrong replies yet all24relevance/coherence scores5; D has20partial replies yet coherence5throughout. Coherence, relevance and truth are demonstrably different measurements in these codings. Score-point means are descriptive; all four ordinal thresholds per scale are retained as sensitivity analyses.

## Paired task-success diagnostic

'''+detail_table('task_success','confirmed_span_sensitivity')+'''
This table includes the adopted ambiguous-span rating; the conservative variant remains in the main analysis. C0 through C7full-success counts are17,16,16,14,15,11,11,10, each out of24. These are paired, heterogeneous development observations, not a dose-response law. The H contrast is distributed across several tasks, not proof of an isolated historical mechanism.
'''
write('P1b_task_completion_analysis','P1b Task Completion and Ordinal Outcomes',task)

struct='''## Frozen structure versus adopted semantics

Original response_status_v1 remains COMPLETE0,TRUNCATED5,CROSS_TURN186,AMBIGUOUS1. No span or raw byte was changed. Semantic completeness is YES143,PARTIAL28,NO21. These describe different units: full continuation boundaries versus the supplied first reply. Neither categorical system replaces the other.

'''
for axis in ('semantic_completeness','answer_delivery','factual_consistency','temporal_consistency'):
    labels=sorted({x['semantic_label'] for x in A['structural_semantic_crosstabs'] if x['axis']==axis})
    data=[]
    for status in ('COMPLETE','TRUNCATED','CROSS_TURN','AMBIGUOUS'):
        data.append([status]+[sum(x['count'] for x in A['structural_semantic_crosstabs'] if x['axis']==axis and x['structural_status']==status and x['semantic_label']==label) for label in labels])
    struct+='### '+axis+'\n\n'+table(['Structure']+labels,data)
struct+='''## Observable cases and causal limits

Of186CROSS_TURN outputs,109contain full correct first replies,33contain wrong delivered answers,26partial supported replies,onepartial false reply and17nonanswers. Thus rejecting every CROSS_TURN as factually wrong would invalidate measurement. Of five TRUNCATED outputs,one is a supported partial answer andfourare Unverifiable unfinished reasoning; truncation is not equivalent to contradiction. The five remain in family G. Their native length termination is consistent with censoring but no controlled budget comparison here identifies its causal effect.

BR168 is the one AMBIGUOUS record. Its frozen span contains a complete four-component answer followed by `Factual question:`. The source explicitly flags EXTRA_GENERATED_QUESTION_IN_FIRST_REPLY and assigns coherence4. Researcher semantic adoption is retained, but no human reply-boundary PASS is invented. Conservative numerical analyses mark this single unit unknown; confirmed-span sensitivity preserves all adopted labels. Neither silently truncates the span or changes response_status_v1.

Native termination remains190length/2EOS, versus95length/1EOS in Wave1. Automatic extraction identifies191/192units here versus96/96there. Native termination, parser extraction, first-reply completeness and truth remain distinct. Subsequent generated turns are preserved for audit but not credited as answers to the first question.

## Descriptive cross-wave comparison

'''+table(['Measure','Wave1','P1b','Interpretation'],[
    ['Cases / speakers','12 / 12','24 / 12','Do not pool responses as independent'],
    ['Complete/Truncated/Cross-turn/Ambiguous','0/17/78/1','0/5/186/1','Different tasks and prompt construction'],
    ['Human complete first reply','79/96','143/192','Binary Wave1 versus explicit partial category here; preserve versions'],
    ['Factual labels','72C/0I/0U;24NA','137C/34I/21U;0NA','Different eligibility/task mix'],
    ['Temporal labels','48C/0I/0U;48NA','40C/34I/14U;104NA','Not an isolated difficulty effect'],
    ['Full task success','No directly equivalent five-way code','110/192','Do not retrofit old annotations'],
    ['Native budget stop','95/96','190/192','Both98.96%; denominator differs']])+'''
The confirmed-span C1-C0 coherence mean is0; boundary-conservative assessed-only mean is-0.0435 because removing BR168's numerical value removes a positive C0/C1difference in that case. The semantic labels remain present. This illustrates measurement-unit sensitivity, not evidence to select the more favorable analysis. Complete case and speaker tables show structural and semantic contrasts side by side.

## Next measurement action

Seek an independently scored, condition-masked subset spanning all families and delivery categories, including BR168, before concluding high annotation reliability. A new unit interpretation must be separately versioned. No reinterpretation or new generation was executed here.
'''
write('P1b_structural_semantic_analysis','P1b Structural and Semantic Measurement Comparison',struct)

novel='''## Evidence, not an originality declaration

The record now establishes mixed categorical/task/ordinal patterns in this synthetic2BBase calibration. It does not establish a universal persona-harm effect, a temporal mechanism or an original algorithm. Literature below was rechecked at official metadata/abstract scope in this task; no experiment, code or method was reproduced. The [existing matrix](related_work_novelty_matrix.md) remains intact.

'''+table(['Primary source','Verified prior coverage','Implication for current evidence'],[
    ['[Principled Personas](https://aclanthology.org/2025.emnlp-main.1364/)','Persona advantage, robustness to irrelevant attributes and fidelity across models/tasks','Unintended persona sensitivity is not new; our interactions need independent replication'],
    ['[When Personalization Misleads](https://aclanthology.org/2026.findings-acl.395/)','History-aligned factual distortion; FPPS mitigation and PFQABench','Generic persona-associated factual error is direct overlap; no representation mechanism identified here'],
    ['[One Persona, Many Cues](https://aclanthology.org/2026.acl-long.2079/)','Cue choice can change personalization conclusions','Style nested in speaker and single realizations limit generalization'],
    ['[What to Admit and How to Present](https://arxiv.org/abs/2610.11188v1)','FC/PS memory admission versus rendering; personalization trade-offs','Selection/presentation decomposition and retrieval filters are prior art'],
    ['[Decoupling Logic from Persona](https://arxiv.org/abs/2610.09772v2)','Separated logic/persona paths; structured-output failures and extra decode cost','Boundary/semantic separation and two-pass architecture are not automatically novel'],
    ['[Wiki-Talkie](https://arxiv.org/abs/2610.08513v1)','Real discussion next-turn persona behavior','Synthetic English items do not establish authentic-speaker external validity'],
    ['[TwinVoice](https://aclanthology.org/2026.findings-acl.981/)','Multiple real-world persona contexts and capability dimensions','Fidelity separation is established; no fidelity measurement here'],
    ['[Persistent Personas?](https://aclanthology.org/2026.eacl-long.246/)','Extended role-playing fidelity and instruction following','Short fixed contexts do not replicate long-dialogue mechanisms']])+'''
## Candidate empirical contributions and falsifiers

'''+table(['Candidate','Observed support / absence','Alternatives and missing evidence','Falsifiable next test / publication value'],[
    ['S/F/H interaction boundaries','Temporal SxH mean0withfouropposingcase contributions; task SxH negative but weak/sensitive','Small clusters, multiplicity, uncertainty and nested style/speaker; no general interaction','Independent counterbalanced speakers/templates. Narrow intervals nearzero or reversed patterns would weaken a stable interaction hypothesis'],
    ['Conditional reliability','A24/24full;D24Correctbut4full;C/E28contradictions','Families differ in wording, reference structure and relevance','Independently cross task operations and lexical realizations; disappearance after crossing would falsify a family mechanism'],
    ['Temporal status under sufficient evidence','34adopted temporal contradictions;H total-package task difference','Four C0errors; trusted ledger itself offers old values; no R/Tisolation','Controlled reference-date/relevance diagnostic with unchanged trusted evidence and neutral baselines'],
    ['Structural versus semantic measurement','186cross-turns include109fullcorrectfirst replies; one ambiguous span changes a paired ordinal mean','Known format-failure literature; researcher-adopted AIcodes, not independent reliability','Independent human unit/claim annotation plus frozen sensitivity rules; stable results under all defensible units would narrow the measurement-bias hypothesis'],
    ['Model/external sensitivity','No comparison yet','OnlyoneBaseGGUF, synthetic speakers; fidelity not measured','Separately versioned native-template Instruct arm and later authorized real-speaker material; failure to replicate defines scope, not a universal law']])+'''
These are potential empirical contributions if replicated with defensible measurement and useful precision. Factorial design, CPU execution, model size and increased error counts are not originality evidence. Null/mixed results are retained; no new prior-art gap is claimed proven.
'''
write('P1b_scientific_novelty_assessment','P1b Scientific Novelty Assessment',novel)

algorithm='''The original pre-calibration assessment above is preserved as historical context. This addendum uses newly registered192-response evidence. No algorithm is implemented or claimed original.

### A. Temporal-aware selection and evidence-priority routing

**Observed Failure Modes.**34adopted temporal contradictions;four occur already atC0. Selecting an old counter/residence/site/desk is observed, but retrieval versus generation responsibility is unresolved because the trusted ledger was fully supplied.

**Existing Methods and Published Prior Art.**[LongMemEval](https://arxiv.org/abs/2410.10813v2) includes temporal updates, indexing/retrieval/reading and time-aware query expansion. [What to Admit and How to Present](https://arxiv.org/abs/2610.11188v1) already separates admission/rendering and compares typed-unit versus whole-memory selection. These records/abstracts were checked; implementations were not reproduced.

**Potential Algorithmic Improvements.**A provenance- and proposition-date-aware admissibility layer is a candidate, not an original contribution. It would need to distinguish current versus requested past states and preserve beneficial old facts. A simple date filter is existing method practice.

**Validation Feasibility.**First identify a residual problem on independent ledger/reference-date material. Compare no-history/all-history, equal-budget random/relevance selection, deterministic interval lookup and established time-aware retrieval; ablate relevance, temporal eligibility and evidence priority separately. Keep trusted evidence constant. Rules cost little local computation; retrieval/extra decode cost must be measured. Removing relevant history can harm fidelity and utility.

**Publication Value.**A new failure boundary or robust negative result could be useful; a renamed filter cannot support originality. No new method is justified until simple baselines fail under an identifying design.

### B. Answer-component verification

**Observed Failure Modes.**27supported partial outputs, including20D-family outputs, show claim consistency is not full task success. Three promises contain a reference string without delivering an answer.

**Existing Methods and Published Prior Art.**[AlignScore](https://aclanthology.org/2023.acl-long.634/) learns information alignment for factual consistency. Existing exact-match/abstention, QA/NLI and component checking address parts of verification; a support metric does not automatically verify task completion.

**Potential Algorithmic Improvements.**A separate coverage-and-commitment checker might help, but the present annotation distinction is not itself a new algorithm. Current component counts sometimes reflect textual coverage, requiring semantic validation.

**Validation Feasibility.**Compare reference exact-match with abstention, human claim/required-component inventory, established alignment/NLI verification and a deterministic component checklist. Use independent prompts with paraphrases, negation, promises and true intermediate facts. Ablate support, coverage and delivery separately. Offline rules are cheap; learned scoring or regenerated answers add measured CPU cost. Do not train and evaluate on these192responses.

**Publication Value.**A validated discrepancy between claim support and task success is empirically useful; originality of a new verifier remains UNVERIFIED. Any checker that erases style must be evaluated separately for Persona Fidelity.

### C. Persona/evidence separation and interaction-aware conditioning

**Observed Failure Modes.**The H package has negative descriptive task effects; SxH varies by endpoint and cancels in temporal labels. This is not evidence of representational entanglement.

**Existing Methods and Published Prior Art.**[FPPS](https://aclanthology.org/2026.findings-acl.395/) addresses personalized factual distortion. [AO-DA](https://arxiv.org/abs/2610.09772v2) separates reasoning and persona rendering. Prompt sectioning or two stages are not new by themselves.

**Potential Algorithmic Improvements.**Condition-dependent gating is only a hypothesis. It should not be fitted to the signs in this development table. Current evidence does not justify beginning implementation.

**Validation Feasibility.**Require independent factorial replication, matched-length/compute controls, native-template baselines, established separation/steering comparators and independent fidelity annotation. Ablate sectioning, extra decode and routing decision. One additional decode roughly doubles generation-call count, not necessarily latency; actual cost is unmeasured.

**Publication Value.**Only a replicated benefit beyond existing methods with preserved fidelity could justify a method contribution. This study has not supplied that evidence.

### D. Response-boundary management and recoverable outputs

**Observed Failure Modes.**186cross-turns include109fullcorrectfirst replies, whileoneambiguousspan remains. Four truncated outputs are unfinished thinking; one is a supported partial answer.

**Existing Methods and Published Prior Art.**Native chat/EOG templates, stop sequences, role-transition extraction and existing structured-output systems already manage boundaries; AO-DA studies structural failure. These are baselines, not invented methods.

**Potential Algorithmic Improvements.**A conservative extractor with abstention could reduce ambiguous units, but choosing later correct turns would introduce selection bias. A parser change cannot create missing final-answer content.

**Validation Feasibility.**Compare frozen extraction, native template/EOG and predeclared stop rules on independent material. Human unit annotations should measure false cuts, wrong-speaker inclusion, completion retention and semantic distortion. Offline extraction costs no model calls; generation arms require new authorization and matched controls.

**Publication Value.**Measurement sensitivity may support an empirical contribution. Boundary heuristics alone do not establish an original algorithm or solve temporal errors.

### Decision

Prioritize an identifying empirical diagnostic and independent annotation before algorithm work. The above opportunities are prospective; no training, retrieval system, routing algorithm or new decoding experiment was launched. Evidence insufficient for an original algorithm claim is reported as such.
'''
write('P1b_algorithmic_opportunity_assessment','P1b Algorithmic Opportunity Assessment',algorithm,append=True)

publication='''## Current judgment: development evidence, not submission-ready validation

The new analysis is reproducible and contains meaningful measurement distinctions. It is not an independent confirmatory study, and no acceptance outcome is guaranteed. PLOS ONE requires sound methods/statistics, supported conclusions, research integrity and transparent reporting/data availability; negative and null results can be eligible. [Official criteria](https://journals.plos.org/plosone/s/criteria-for-publication).

'''+table(['Requirement','Current evidence','Remaining limitation/action'],[
    ['Scientific validity','Shared task-sufficient evidence, fixed questions/context, complete eight-cell pairing','Total packages differ in length/content;R/Tand familyconfounded;neutral controls OPEN'],
    ['Semantic annotations','192researcher-adopted records, source notes and uncertainties preserved','AI-assisted proposals withonefinal human; no independent agreement evidence; audit ambiguous/partial/promise/date cases'],
    ['Independent sample size','24developmentcases/12synthetic speakers','No representative sampling or independent confirmatory set; effective temporal9speakers'],
    ['Precision','Whole-cluster bootstrap, LOSO, unknown bounds, ordinal thresholds','Small discrete clusters, multiple endpoints, selected-subset estimates; no population significance'],
    ['Reproducibility','Original run integrity, pinned identities, immutable review snapshot and twice-rebuilt analysis','Release raw data/code/manifests in portable form; ignoredlocalresults are not yet a public archive'],
    ['Model/generalization','OneQwen2BBaseQ4_K_M backend/template arm','No cross-model/post-training replication or real-speaker external validity'],
    ['Ethics','Fictional English material; no private conversations imported','Future authorized real-speaker stage needs explicitpermissions and safeguards'],
    ['Contribution/related work','Conditional package and measurement hypotheses with direct overlap checked','No proven new mechanism or algorithm; independentfalsifiable replication needed']])+'''
## Annotation reliability and independent validation

Researcher adoption is valid provenance, not a second independent annotation. Seek a genuinely independent human review of a prospectively selected stratified subset (all families, complete/partial/no-answer, contradictions and the ambiguous unit). Keep that reviewer blind to treatment and proposed labels; retain both versions before adjudication. Only then compute appropriate actual agreement statistics, with uncertainty and the sampling scheme reported. Do not fabricate agreement now. Include additional independently selected material before population claims.

## What the calibration supports

The reviewed bank distinguishes supported claims from complete requested answers and shows actual temporal contradictions under supplied evidence. It supports case-specific exploratory contrasts and measurement planning. It does not establish that persona conditioning generally harms reliability, that the new tasks are inherently superior, or that H isolates stale-history mechanisms. Neutral comparisons and Persona Fidelity remain unavailable. A well-designed null/negative replication is acceptable; increasing call count alone does not improve readiness.

## Publication path

First resolve measurement reliability using existing outputs, then prospectively freeze an independent mechanism/replication design with clear estimands and precision targets. Maintain a public data/code inventory and truthful AI-assistance disclosure. The optional algorithm track should remain gated by reproducible unresolved errors and verified prior-art gaps.
'''
write('P1b_publication_readiness','P1b Publication Readiness',publication)

next_step='''## Primary recommendation: option C, preceded by a measurement check

Prepare a **separately authorized historical relevance/temporal-status diagnostic on independent material**. The reason is the observed34date-related contradictions and conditional H differences, not a desire for positive persona effects. Fourerrors already occuratC0; genuine history interference must be distinguished from wrong selection among trusted ledger entries. Before any new inference, independently review a stratified subset of this bank and BR168's unit; this uses existing outputs and directly tests measurement validity.

The R/T study is a prospective additional diagnostic, not silent adoption of v1.2 or replacement of S/F/H. A bounded mechanistic feasibility proposal could use12new reference-date cases from12fictional speakers, at S=F=0, with no-history plusfourcrossed relevance/temporal-content versions (60requests). Hold question, trusted evidence, requested date, history position, format and actual-token budget fixed as feasible. Define whether temporal status is valid-at-reference or expired-at-reference; past facts remain genuine rather than fabricated contradictions. Include answer-leakage controls and review each intervention before freezing. Match irrelevant/relevant facts carefully: relevance and informativeness cannot be assumed separable. This60requestillustration does not estimate S/Finteractions or provide confirmatory precision. A subsequent independent eight-cell replication would retain the original S/F/H question. Any expansion requires explicit approval.

Use selection rules based on evidence sufficiency, factor balance and linguistic diversity, not error direction in the current24cases. Do not reuse them as a confirmatory test. Negative or zero R/Tdifferences would weaken the stale-persona-interference explanation; errors equally common without added history would redirect attention to ledger reasoning or template behavior.

## Options and cost trade-offs

The original192requests summed2096.152seconds of response latency, mean10.917seconds/request, excluding setup, review and other overhead. CPU figures below are **linear illustrations at that measured Base workload**, not new measurements or guaranteed runtimes. Instruct/template changes may alter token usage and cannot inherit this rate without calibration.

'''+table(['Option','Information / novelty risk','Confounders and required independent evidence','Illustrative compute / precision','PLOS ONE relevance'],[
    ['A Independent Base expansion','Testsreplication; generic addedscale low novelty','New speakers/templates and balancedfamilies; retain all8cells; task/historyconfounds remain','48newcasesx8=384calls~70min response time; speaker count determinesprecision','Useful if testingfrozen scopedhypotheses, not merely increasingcalls'],
    ['B Instruct arm','Testsmodel/template sensitivity; not purepost-trainingcausality','Pinrelatedmodel/tokenizer/nativechat; alignsemanticcontent andbudget; comparewithin-armcontrasts','192callshas35minBase-equivalent reference only; actualInstructtime unknown','Usefulsecondaryrobustness arm aftervalid measurement'],
    ['C Relevance/temporal diagnostic','Testsstale-ledgerversusadded-historyaccounts; priorworkalreadycoversmemorygating','Independentdatecases, matchedformat/length, contentreview, noanswerleakage; holdS/Ffixedforinitialprobe','Illustrative60calls~11min;12clusters diagnostic only; no fixedconfirmatoryclaim','Highest immediateinformation aboutunresolvedtemporal mechanism'],
    ['D Boundary measurement','Quantifiesunit/score sensitivity; knownformatmethods','Independenthumanunits and frozenextractor; native-templatecomparison separatelyversioned','Offlinehuman review requires0newcalls; a192callarmBase-equivalent35min','Immediatevalidity prerequisite, notautomaticallynewalgorithm'],
    ['E Algorithmic intervention','Prematurewithoutidentifiedresidualfailurebeyondbaselines','Existingretrieval/FPPS/separation/verifierbaselines; independentablation andfidelityevaluation','Rulescheap; multipassortrainingcostunmeasured; noimplementationauthorized','Do notpursuefornoveltyalone']])+'''
## Precision gate and scope

For a future speaker-level mean paired difference, a planning approximation is half-width h≈1.96*s/sqrt(K), where K is independent speakers and s is the standard deviation of speaker-level contrasts. For h=0.10 and hypothetical s=0.25 or0.50, K≈25or97, respectively. These are sensitivity assumptions, not measured population variances or universal sample sizes. Interactions can have wider ranges/variance; semantic missingness, unequal family coverage, annotation error and multiplicity can increase requirements. Do not use12developmentclusters to justify narrow confirmatory intervals. Choose endpoints, meaningfulprecision, stratification, independent sampling and multiplicity before a confirmatory freeze.

The next experiment is not launched by this report. OptionD's independent annotation check is a prerequisite; optionC is the recommended next inference design for researcher consideration. B/Aremain secondary replication routes. No new model, algorithm, phase or inference authorization is inferred.
'''
write('P1b_next_experiment_decision','P1b Next Experiment Decision',next_step)

print(json.dumps({'reports_created':8,'historical_algorithmic_report_appended':1,'new_inference':0}))
