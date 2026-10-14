"""Assemble the offline integrity review; never register human decisions or infer."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess

import p1c_semantic_review as a
import p1c_semantic_analysis as old
import p1c_semantic_integrity as audit
import p1c_integrity_registration as gate

ROOT=audit.OUT
RESULT=Path('results/p1c_semantic_integrity/v1')
REPORTS={}


def doc(name,text):
    path=Path('docs')/(name+'_v1.md')
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write('# '+name.replace('_',' ')+' v1\n\nMaintainer: Yaxin ZHENG. Status: AI-assisted review; researcher confirmation pending.\n\n'+text.strip()+'\n')
    REPORTS[str(path)]=a.sha(path)


def link(path):
    path=Path(path)
    return f'[{path.name}]({path.relative_to("docs").as_posix()})'


def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(str(v).replace('|','/').replace('\n',' ') for v in row)+' |\n' for row in rows)


def schemas():
    counts={'json':0,'csv':0}
    for path in ROOT.glob('*.json'):
        a.read(path);counts['json']+=1
    for path in ROOT.glob('*.csv'):
        rows=a.rows(path);a.require(all(None not in r for r in rows),'Invalid CSV width '+str(path));counts['csv']+=1
    for path in (audit.PRIMARY,audit.SECONDARY,ROOT/'boundary_sensitivity_table_v1.json'):
        records=a.read(path);rows=a.rows(path.with_suffix('.csv'))
        a.require(len(rows)==len(records),'Active CSV count differs')
        for source,row in zip(records,rows):
            for k,v in source.items():
                expected=json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else '' if v is None else str(v)
                a.require(row[k]==expected,'CSV/JSON field differs: '+k)
    return counts


def preserve():
    baseline=a.read(RESULT/'baseline.json')
    changes=[p for p,digest in baseline['files'].items() if a.sha(p)!=digest]
    a.require(set(changes)<={'docs/research_development_log.md'},'Entry source changed '+str(changes))
    a.require(Path('docs/research_development_log.md').read_bytes().startswith((RESULT/'development_log.before.md').read_bytes()),'Log not append-only')
    seal=a.read(a.OUT/'closeout_v1/verification_v1.json')
    for path,digest in seal['artifact_hashes'].items():a.require(a.sha(path)==digest,'Previous review seal differs '+path)
    approval=a.read('docs/validation/p1c/authorization_v2/researcher_consolidated_approval_v1.json')
    for d in approval['decisions']:
        for source in d['documents']:a.require(a.sha(source['path'])==source['sha256'],'Approved document changed')
    return {'entry_files_preserved':len(baseline['files']),'prior_sealed_artifacts_preserved':len(seal['artifact_hashes']),
            'approved_policy_addendum_manifest_verified':True,'allowed_append_only_changes':changes}


def main():
    a.require(not (ROOT/'reproducibility_manifest_v1.json').exists(),'Preserve prior closeout')
    check=preserve();schema=schemas()
    tests=a.read(RESULT/'tests_full_01.json');a.require(tests['exit_code']==0,'Full test suite did not pass')
    sourcecheck=a.read(RESULT/'source_verification_01.json');a.require(sourcecheck['status']=='PASS','Source verification failed')
    primary=a.read(audit.PRIMARY);secondary=a.read(audit.SECONDARY);bounds=a.read(ROOT/'boundary_sensitivity_table_v1.json')
    diag=a.read(ROOT/'metric_independence_diagnostic_v1.json')
    now=datetime.now(timezone.utc).isoformat()
    old_primary=old.PRIMARY.with_suffix('.csv')
    approval_path='docs/validation/p1c/authorization_v2/researcher_consolidated_approval_v1.json'
    provenance={'version':'p1c_annotation_integrity_provenance_v1','software_recorded_utc':now,
        'maintainer':'Yaxin ZHENG','annotation_origin':'AI_assisted_condition_masked_proposal_and_non_independent_AI_reinspection',
        'human_review_status':'PENDING','human_review_timestamp':None,'human_confirmed_records':0,
        'source_sha256':{str(p):a.sha(p) for p in (old.PRIMARY,old_primary,old.SECONDARY,a.SOURCE,a.POLICY,old.REGISTRY,Path(approval_path))},
        'active_reviewed_primary':{'json':str(audit.PRIMARY),'sha256':a.sha(audit.PRIMARY),'records':72},
        'active_secondary':{'json':str(audit.SECONDARY),'sha256':a.sha(audit.SECONDARY),'records':72,'changed_boundary_units':8},
        'primary_reinspection_freeze_sha256':a.sha(ROOT/'primary_audit_freeze_v1.json'),
        'same_analyst':True,'independent_second_reviewer':False,'perfect_blinding_claim':False,
        'masking':'Reviewer files exclude assignments, structural status and full continuation. Prior analytical exposure and linguistic cues remain; failed schema inspection loaded mapping keys, printed no assignment records. Stage B full prompts reviewed only after primary freeze.',
        'corrections':'Six ordinal field recommendations in five primary records; additionally two PC023 secondary fields. All require actual researcher adoption.',
        'failed_export':'failed_secondary_export_v1.json records preserved incomplete v1; active secondary is v2.',
        'official_semantic_effects_computed':False,'new_inference':0}
    a.write(ROOT/'annotation_provenance_register_v1.json',provenance)
    a.write_csv(ROOT/'metric_applicability_verification_v1.csv',[
        {'anonymous_response_id':r['anonymous_response_id'],**{k:r[k] for k in r if 'applicable' in k},
         'frozen_source_fields_preserved':True,'human_confirmation':'PENDING'} for r in primary])
    # Bounds quantify unresolved outcomes, not a recoding of Unverifiable and not confidence intervals.
    descriptive={}
    for name,rows in [('primary',primary),('secondary',secondary)]:
        descriptive[name]={}
        for metric in ('factual_consistency','temporal_consistency','task_success'):
            vals=[r['reviewed_AI_ratings'][metric] for r in rows]
            success=sum(v==('Correct' if metric!='task_success' else 1) for v in vals)
            unknown=sum(v in ('Unverifiable','Missing',None) for v in vals)
            known=len(vals)-unknown
            descriptive[name][metric]={'eligible':72,'known':known,'unknown':unknown,'success_labels':success,
                'unresolved_sensitivity_bounds_counts':[success,success+unknown],
                'unresolved_sensitivity_bounds_fraction':[success/72,(success+unknown)/72],
                'evaluated_only_fraction':success/known,'warning':'Conditional on unconfirmed proposals and this boundary view. No sampling CI or official condition effect; unknown is not Incorrect.'}
    a.write(ROOT/'descriptive_sensitivity_bounds_v1.json',descriptive)

    doc('P1c_semantic_integrity_audit',f'''
## Finding and provenance correction

The 72 proposals and eight alternative boundaries are intact. The old transcription code assigned groups of endpoints together. In particular, ordinal pairs were set together and explanations were generated conditional on those scores. Therefore the earlier claim of separately assessed dimensions must be qualified: conceptual separation was intended, but **independent rating passes were not demonstrated**. There was no literal factual-label-to-task-label assignment; shared group logic still prevents a procedural-independence claim. The source report and code remain unchanged as historical evidence.

All 72 masked question/evidence/reference/reply records were re-read. The new proposal stores separate factual, requested-component, relevance and fixed-context coherence arguments, alternatives and uncertainty. This remains the same AI analytical process, not independent human annotation or a second blinded reviewer. Source quotations are AI-selected evidence references, not researcher-written notes. All researcher fields remain blank. Full Stage B prompts were inspected after the primary reinspection snapshot; the provenance manifest discloses prior analytical knowledge and the failed schema-inspection command that loaded mapping keys without displaying records. No semantic condition effects were calculated.

## Recomputed proposal distributions

{table(['Endpoint','Original frozen-boundary proposal','Reviewed recommendation'],[
['Factual','43 Correct / 20 Incorrect / 9 Unverifiable','Unchanged'],
['Temporal','43 Correct / 15 Incorrect / 14 Unverifiable','Unchanged'],
['Task success','43 success / 20 failure / 9 unknown','Unchanged'],
['Required components','44 complete / 20 zero / 8 unscorable','Unchanged'],
['Semantic completeness','64 YES / 8 UNCERTAIN','Unchanged'],
['Relevance','59 score 5 / 5 score 4 / 8 unscorable','60 score 5 / 4 score 4 / 8 unscorable'],
['Coherence','59 score 5 / 5 score 4 / 8 unscorable','64 score 5 / 8 unscorable']])}
The full denominator is 72 on all seven semantic axes; fidelity is predeclared N/A. Identifiable primary units: 64. C-versus-I factual coverage: 63; temporal coverage: 58; known task success: 63. All 72 AI assessments exist, but official human-confirmed ratings remain zero. Neither unresolved boundaries nor administrative missing confirmation is a false model claim.

## Integrity and policy

Actual model/backend bytes, 45 pinned sources, all 72 input-token records, original request order and raw HTTP bytes were verified. Execution reconstruction agrees twice; 700 run event files and 5,798 historical experiment artifacts were checked. Frozen status remains CROSS_TURN 64, AMBIGUOUS 8, COMPLETE 0, TRUNCATED 0; native budget stops 70 and EOS stops 2. No generation was performed.

The actual approved addendum is `p1c_addendum_proposed_v2`; approval is registered in {link(approval_path)}. Its SHA-256 is `51d1987e2e91e2f4e72735304380e3f4442f418b731e972828677d24b7b96f55`. The historical proposal's pending flags are not a revocation of that approval. Protocols v1.1 and the v1.2 proposal remain unchanged.

The additive measurement-state flags do not change the rubric, applicability, 16 contrast weights or primary boundary. Rating recommendations require the existing annotation confirmation, not a new protocol approval. See the [confirmation packet](P1c_final_annotation_confirmation_packet_v1.md), [boundary audit](P1c_boundary_uncertainty_analysis_v1.md), [metric independence audit](P1c_factual_task_success_comparison_v1.md) and [ordinal audit](P1c_relevance_coherence_ceiling_audit_v1.md).

## Validation and retained failures

Full test result: **{tests['stdout'].strip().splitlines()[-1]}**. The active CSV/JSON pairs agree field by field. The first secondary CSV export stopped after nine rows because eight rows introduced additional columns. The complete JSON and partial CSV are preserved as inactive v1, together with the failure log; repaired uniform-column secondary v2 is the only active import source. This was an export failure, not missing inference or changed observations. Two guessed read paths failed and were resolved to the actual analysis_preparation directory and evaluation_policy_proposed_v1 file; no source was edited. All failures remain documented.

## Algorithmic Opportunity Assessment

The immediate opportunity is better measurement provenance and boundary validation, not a demonstrated new algorithm. See the [five-part candidate assessment](P1c_algorithmic_opportunity_update_v1.md). Correcting measurement coupling is necessary for an empirical paper, but tests alone do not establish scientific validity or publication readiness.
''')

    bnotes={
        'PC010':'Correct Orchid/Thursday prefix; a generated new music question follows. EOS does not settle attribution.',
        'PC023':'Correct Orchid/Thursday service assignment under the service-day reading; repeated question/answer follows. Calendar-language alternative retained.',
        'PC033':'Silver/Tuesday instead of Maple/Tuesday: one supported component, wrong desk. Later turn truncates; primary unit remains unresolved.',
        'PC039':'Silver/Friday instead of Maple/Tuesday: contradicted desk and unsupported weekday. Later turn truncates.',
        'PC042':'Same target error as PC039, independently preserved raw text. Friday is not in the ledger; later continuation is incomplete.',
        'PC044':'Correct Maple/Tuesday before a generated recent-conversation replay ending at Assistant. Formatting attribution is unresolved.',
        'PC054':'Silver follows an earlier route; June requires Cobalt through the updated route. Generated context replay follows.',
        'PC063':'Correct December Laurel prefix, then repeated dialogue and a trailing incomplete Assistant turn.'}
    bt=[]
    for r in bounds:
        score=r['reviewed_secondary_ratings'];native=r['native_termination']
        bt.append([r['anonymous_response_id'],r['proposed_evaluation_view'],f"{score['factual_consistency']} / {score['temporal_consistency']} / {score['task_success']}",bnotes[r['anonymous_response_id']]])
    doc('P1c_boundary_uncertainty_analysis',f'''
## Primary versus sensitivity units

All eight changed factual judgments correspond exactly to the eight frozen AMBIGUOUS outputs: PC010, PC023, PC033, PC039, PC042, PC044, PC054 and PC063. Their primary F/T judgments remain Unverifiable, task success unknown and semantic completeness UNCERTAIN. This is an unavailable evaluation unit, not evidence that eight answers contain unknowable facts. The source `response_status_v1` and original candidate text remain unchanged.

Each alternative is a literal initial prefix ending before a generated section heading, never a later answer selected for correctness. Offsets, raw/prefix hashes, native stop, full continuation, excluded continuation, question, ledger and source quotations appear in {link(ROOT/'boundary_sensitivity_table_v1.csv')}. All eight prefixes are plausible, self-contained answers; none is certified as the uniquely attributable first reply. A generated document heading can be answer content or a transition. Human adjudication is still necessary. PC010 and PC023 end at EOS (85 and 93 generated tokens); the other six reach 96 tokens. Termination applies to the whole continuation, not just the proposed prefix.

{table(['ID','Exact proposed prefix','Factual / temporal / task sensitivity','Case-specific interpretation'],bt)}

All original prompts, parser traces and eight native responses were inspected. Prompt/input-token reconstruction is in the **analyst-only** protected_boundary_prompt_audit_v1.json; it is deliberately excluded from Stage A because intervention language can reveal assignments. The repeated question/context headings make a boundary interpretation plausible but not certain. A procedural text's discussion of question/reply ordering may prime format; that is a hypothesis, not a controlled finding.

## Uncertainty types

BOUNDARY_UNRESOLVED identifies the unknown unit; STRUCTURALLY_UNSCORABLE describes its scoring consequence. ANNOTATION_UNCERTAIN covers calendar/attribute/entity-versus-time readings. EVIDENCE_UNVERIFIABLE identifies a specific unsupported proposition. NOT_APPLICABLE is predeclared metric exclusion. MISSING is absent required annotation/confirmation. These are additive, potentially overlapping flags, not replacement categorical scores.

Primary factual Unverifiable = eight unresolved boundaries + PC006 calendar reading. Primary temporal Unverifiable = those eight + PC006 + PC011/027/030/035/040 entity-versus-time interpretations. PC004's accepted alias reading is also explicitly uncertain without changing its Correct proposal. In secondary PC039/042, the unsupported Friday component coexists with a demonstrably wrong desk, so an evidence-gap flag does not erase the whole-answer Incorrect rating. All human confirmation states remain MISSING; no primary semantic axis is N/A; fidelity is N/A for all 72.

## Distribution and identification sensitivity

Primary F = 43/20/9 (C/I/U); alternative F = 47/24/1. Primary T = 43/15/14; alternative T = 47/16/9. Task = 43/20/9 versus 47/24/1 (success/failure/unknown). Component coverage = 44 full, 20 zero, 8 unscorable versus 48 full, 1 half, 23 zero. Completeness = 64 YES/8 UNCERTAIN versus 72 YES under the assumed prefixes. These are proposal-conditional descriptive counts, not official effects or general accuracy.

Allowing unknown units/judgments to range over success/failure gives primary F [43,52]/72, T [43,57]/72 and task [43,52]/72; secondary F [47,48]/72, T [47,56]/72 and task [47,48]/72. These are identification bounds conditional on accepted scored labels, **not sampling confidence intervals**, and do not recode Unverifiable as Incorrect. Evaluated-only F is 43/63 versus 47/71; T is 43/58 versus 47/63. Selection may depend on condition and response form. All 72 requests remain in incidence denominators; official paired signed-weight bounds await confirmation.
''')

    doc('P1c_factual_task_success_comparison',f'''
## Independence finding

Factual and task categories coincide pointwise in all 72 original proposals, not merely in their totals. The transcription used common manually selected groups with joint defaults/updates. It did not literally copy one field into the other, but this is insufficient to claim independent assessments. Their numerical equality is not evidence of construct equivalence, inter-rater reliability or independent replication.

During this audit, task requirements and delivered components were separately re-read against the question/reference. Those arguments are recorded under metric_evidence_audit.task, independently of factual-label lookup. The transcription's `WRONG` groups are fixed records of that reinspection, **not a predictive scorer** and not a method to apply to future outputs. The resulting task recommendations happen to agree with the old values. This same-process reinspection does not remove shared-judgment bias.

## Actual data relationships

{table(['Primary factual','Task','Completeness','Components','Count'],[
['Correct','Success','YES','All supported','43'],['Incorrect','Failure','YES','Zero supported requested components','20'],
['Unverifiable','Unknown','YES','Both fields present; calendar reading uncertain','1 (PC006)'],
['Unverifiable','Unknown','UNCERTAIN','Unscorable boundary','8']])}
All 64 identifiable replies attempt a final declarative assignment. Twenty deliver an incorrect final answer; an answer can be complete and false. No identifiable primary reply was found with only intermediate reasoning or correct-but-incomplete delivery. Do not manufacture such a disagreement. PC006 attempts both requested fields but the temporal assertion is not uniquely interpretable; component coverage 1 is retained as the existing recommendation under the service-day interpretation, not a proof of task success. Adjudication may affect that interpretation and its scores together.

The alternative PC033 prefix is an important different relationship: Tuesday is supported, Silver is not the requested Maple desk; component coverage is 0.5 but factual Incorrect and task failure. A supported component is not overall success. This example stays secondary and cannot be substituted into the primary analysis.

For every row the reviewed file retains material claim quotations, all referenced evidence quotations, requested/delivered values, answer-delivery status, support fraction, uncertainty and an alternative interpretation. Incorrect entity/attribute assertions can be factual errors while temporal attribution remains unresolved. Neither a wrong fact nor an incomplete response is mechanically assigned to every metric.

## Limits and next validation

The same short assignment templates make claim correctness and task success align in these proposals. That limited task space and the coupled original coding both matter. Validate the rubric on independent examples with true partial answers, unsupported assertions, correct intermediate facts, explicit abstention, contradictions and complete false answers before claiming broad construct validity. A second actual human should review a prospectively stratified subset without seeing AI labels, with raw agreement/confusion tables and appropriate categorical/ordinal agreement only after data exist. No agreement has been fabricated.
''')

    changes=[[r['anonymous_response_id'],c['metric'],c['original'],c['recommended']] for r in primary for c in r['reviewed_AI_changes']]
    doc('P1c_relevance_coherence_ceiling_audit',f'''
## Rubrics and procedural dependence

Relevance asks whether a reply addresses the requested communicative intent. Coherence asks whether it integrates with the fixed preceding dialogue, including topic continuity and reference resolution. Neither is simply factual correctness. The original script assigned the two ordinal values together and produced generic explanations from that score. Thus 72/72 equality, including eight nulls, cannot establish independently evaluated dimensions. Historical proposals remain available verbatim.

The fixed context is generic: a user has the dated schedule ready, and the assistant asks which assignment to check. The 64 identifiable replies all continue with named assignment answers. Incorrect assignments remain factually wrong but do not necessarily create a discourse discontinuity.

## Specific pending recommendations

{table(['Response','Metric','Original','Recommended'],changes)}
PC004/011/027/030 explicitly use collection-desk wording for destination-room questions; retaining relevance 4 is a defensible attribute-alignment judgment, with 5 as a recorded alias-reading alternative. Their declarative replies nevertheless integrate with the schedule-checking dialogue, supporting coherence 5. PC006 directly attempts both requested fields: a calendar-versus-service-day ambiguity belongs to factual/temporal adjudication and does not by itself justify relevance/coherence deductions. Its two 4s are proposed as 5s. In the separate alternative-prefix view, PC023's service-day phrase similarly motivates two additional 4-to-5 recommendations.

Every row contains separate question/context/reply quotations, reasons, a plausible alternative score and qualitative confidence. These are AI explanations, not human notes. Ambiguous primary units remain unscorable. No score is changed merely to create variation, and these recommendations are not official labels.

## Measurement resolution

Original primary R/C: 59 score 5 and 5 score 4 among 64 (92.19% at the maximum). Reviewed primary R: 60/64 at 5 (93.75%); coherence: 64/64 at 5. Secondary reviewed R: 68/72 at 5; coherence: 72/72 at 5. The reinspection increases the ceiling rather than manufacturing variance. Constant observed coherence cannot sensitively measure small conditioning differences here; it does not establish a zero population effect or validate interval-scale assumptions.

Keep full ordinal distributions, missing units and threshold/sign sensitivities. Means, if later reported, are descriptive. Use independent rubric calibration examples that separate relevance, context integration and truth; do not retroactively rewrite this task bank to improve scale resolution.
''')

    files=[audit.PRIMARY.with_suffix('.csv'),audit.PRIMARY,ROOT/'boundary_sensitivity_table_v1.csv',ROOT/'boundary_sensitivity_table_v1.json',audit.SECONDARY,
           ROOT/'uncertainty_classification_v1.json',ROOT/'primary_sensitivity_specification_v1.json',ROOT/'researcher_confirmation_request_v1.json']
    doc('P1c_final_annotation_confirmation_packet',f'''
## One actual pending decision

The experiment, applicability, protocol addendum and execution were already approved; none needs reapproval. **Only adoption/correction of semantic annotation remains pending.** The researcher's earlier provisional preference for primary ratings plus boundary sensitivity is not final confirmation. No human decision or timestamp has been inferred.

Recommended adoption: the 72 reviewed primary proposals, including the six ordinal field recommendations below, retaining original boundaries; accept the eight alternative-prefix judgments exclusively as separately reported sensitivity. All original categorical/task/component/completeness proposals remain unchanged. The secondary view inherits the six ordinal changes and additionally proposes PC023 relevance/coherence 4 to 5. The choice concerns these disclosed versions, not an open-ended authorization to rescore.

{table(['Response','Metric','Original','Recommended'],changes)}

## Exact evidence packet

{table(['File relative to repository','SHA-256'],[[p.as_posix(),a.sha(p)] for p in files])}
The complete 72-row review is {link(audit.PRIMARY.with_suffix('.csv'))}; all original fields and seven original AI scores coexist with reviewed_AI_ratings, change reasons, separate evidence arguments and blank researcher fields. The eight-item view is {link(ROOT/'boundary_sensitivity_table_v1.csv')}. Its full raw continuations and structural diagnostics are Stage B material: score the primary view first. The active all-72 secondary JSON is v2; inactive v1 preserves an incomplete CSV export and must not be imported.

Read [integrity](P1c_semantic_integrity_audit_v1.md), [boundary uncertainty](P1c_boundary_uncertainty_analysis_v1.md), [factual/task comparison](P1c_factual_task_success_comparison_v1.md) and [ordinal recommendations](P1c_relevance_coherence_ceiling_audit_v1.md). PC004 alias wording, PC006 calendar wording, five entity/time ambiguities and all eight alternative spans are explicitly flagged; a researcher may correct any of them rather than adopt the recommendations. No independent second reviewer or complete blinding is claimed.

## Explicit choices and consequences

1. **Adopt reviewed recommendations; retain eight boundaries only as sensitivity (recommended).** This accepts the six primary ordinal changes and the two additional PC023 secondary changes, with all stated uncertainties. Register a new confirmed snapshot, then run the unchanged 16 contrasts in distinct primary and sensitivity outputs.
2. **Adopt original proposals; retain eight boundaries only as sensitivity.** Use the original ordinal ratings, disclose the coupled-coding and ceiling concerns, and preserve reviewed recommendations as rejected/unadopted alternatives. The importer supports this without erasing either version.
3. **Provide specific corrections or defer adoption.** Record view, anonymous ID, metric, replacement and reason. Only the dependent semantic-effect workflow waits; no new inference is implied. The researcher may also exclude secondary analysis by explicitly choosing primary-only.

The existing JSON confirmation form records the chosen rating version and sensitivity scope. A text reply identifying this packet and choice can also be faithfully registered. All human fields are currently blank. No fabricated review date is required. The additive state flags separate boundary, evidence and annotation uncertainty without changing approved scoring or denominators; they are not a new approval gate. Any genuinely different primary boundary or estimand would require a separately specified policy change and is not authorized by these choices.

## Scientific scope

The official analysis will concern 12 paired development cases within six synthetic speakers. R/T are text-package effects; procedural controls remain DIAGNOSTIC_ONLY and no-history is shorter. No pure relevance, temporal mechanism or stale-answer competition claim follows. This approval would establish researcher adoption of AI-assisted judgments, not independent human agreement, confirmatory evidence or publication readiness. The packet hash is recorded externally in reproducibility_manifest_v1.json, avoiding a circular self-hash.
''')

    doc('P1c_analysis_readiness',f'''
## Ready implementation, blocked official effects

The additive importer tools/p1c_integrity_registration.py accepts only an explicit researcher decision bound to exact source hashes. It retains original proposals, revised recommendations and actual corrections; refuses blank provenance, invalid scores, missing scope and overwriting. Registration freezes annotations before any treatment mapping is read for analysis. Current registered semantic annotations: **0**. Official semantic treatment effects: **not computed**.

After actual confirmation, use `register --approval ACTUAL_DECISION.json --output NEW_REGISTRATION_DIRECTORY`, then `analyze --registration NEW_REGISTRATION_DIRECTORY --output NEW_ANALYSIS_DIRECTORY`. These are instructions, not commands executed during this audit. Analysis rechecks the frozen registration and reconstructs numerical outputs twice. The wrapper reuses the existing paired-statistical implementation; no replacement estimator was introduced.

## Preserved specification

{link(ROOT/'primary_sensitivity_specification_v1.json')} copies all 16 weights exactly from the approved registry (SHA-256 `713a7679d5a606707f8075bae51d3fa5716a721eccf86f1f56cebc73b4bbc4e7`). With cells R0T0,R0T1,R1T0,R1T1, R weights are -1/2,-1/2,+1/2,+1/2; T weights -1/2,+1/2,-1/2,+1/2; RxT weights +1,-1,-1,+1. Four fixed-factor contrasts, eight active-history-versus-baseline contrasts and one procedural-versus-no-history contrast complete the 16. Original condition IDs and interpretation remain unchanged.

All cells remain within their case; two cases per speaker, six equally weighted speaker clusters. Bootstrap resamples whole speakers with both cases/all cells, seed 715004, 10,000 replicates. Leave-one-speaker-out, task-family summaries, category/threshold distributions, paired signs and signed-weight unknown bounds are retained. Synthetic unit fixtures verify reconstruction and unknown handling; their results are not empirical model results. No current proposal was joined to conditions for semantic-effect calculation.

## Denominators and uncertainty

All seven semantic axes are eligible on 72 outputs; per condition 12. Fidelity is N/A. Missing, Unverifiable, incorrect, unresolved boundary, incomplete and N/A remain distinct. Correct-label incidence is not C-versus-I accuracy. Assessed-only contrasts require every nonzero-weight cell to be assessable and disclose condition-dependent censoring; never reweight surviving cells or condition on baseline correctness. Alternative boundaries remain sensitivity only. Descriptive all-eligible bounds are in {link(ROOT/'descriptive_sensitivity_bounds_v1.json')}; they do not replace later sampling uncertainty.

Six clusters provide weak uncertainty estimation, particularly for interactions and sparse subgroups. Cluster bootstrap intervals may be unstable or optimistic; leave-one-out instability must be shown. Full reporting across 16 contrasts and separate endpoints is exploratory, without significance selection. Constant proposed coherence scores do not prove absence of an effect. No power, empirical ICC or independent replication is inferred from this development set.

## Validation and next evidence

Full tests: **{tests['stdout'].strip().splitlines()[-1]}**. Gate failures, original-field preservation, literal prefix hashes, ordinal edits, six-cluster routing and exact contrast weights have regression coverage. A test-only temporary approval fixture verifies software behavior; it is explicitly synthetic and never registered as a research decision.

First obtain the single annotation decision, then publish all registered exploratory contrasts internally with provenance. Independent validation should use new speakers/cases and a frozen precision target, prospective stratified independent human review, a separately controlled model/template comparison, and measurement examples that discriminate true partial completion from false complete answers. Sample size must follow cluster/interaction precision sensitivity, not the desired pilot sign. New inference still needs its own authorization. PLOS ONE submission readiness is not established by these tests or this calibration.
''')

    doc('P1c_algorithmic_opportunity_update','''
## Scope and prior-art verification

No new algorithm was implemented and no new inference was executed. This update adds the measurement-integrity findings to the preserved [source matrix](related_work_novelty_matrix_monitor_v2.md). The targeted primary-source check read method sections of [LongMemEval v2](https://arxiv.org/html/2410.10813v2), [What to Admit and How to Present v1](https://arxiv.org/html/2610.11188v1), [CoVe](https://aclanthology.org/2024.findings-acl.212.pdf), [RARR](https://aclanthology.org/2023.acl-long.910.pdf), [Efficient Guided Generation v4](https://arxiv.org/html/2307.09702v4), and [Decoupling Logic from Persona v2](https://arxiv.org/html/2610.09772v2). This is a targeted update, not an exhaustive novelty search or code replication. CoVe is Findings ACL 2024 and RARR ACL 2023; the cited admission, guided-generation and decoupling versions are treated as preprints, not assumed peer-reviewed. Other direct competitors retain the earlier verification limitations.

## Temporal evidence resolution and history gating

### 1. Observed Failure Modes

AI proposals contain wrong-period and entity/attribute answers despite the complete supplied ledger. Labels remain pending. No official R/T effect exists yet, and topical auxiliary history does not necessarily offer a competing answer.

### 2. Existing Methods and Published Prior Art

LongMemEval separates indexing, retrieval and reading, including time-aware query restriction and structured reading. The admission preprint distinguishes whole-entry FC and unit-level PS, as well as presentation with shared admitted content. These overlap directly with filtering, gating and typed evidence use. They are mandatory comparator families, not new PersonaSLM inventions.

### 3. Potential Algorithmic Improvements

A query-date/entity/attribute binding diagnostic may isolate a residual problem after ordinary interval filtering. That is currently a known engineering or incremental candidate; no novel method gap is established. Latest-only selection is an inadequate baseline for historical queries.

### 4. Validation Feasibility

Compare all-evidence, exact query-time filtering, lexical/semantic retrieval and feasible published admission under matched retained-information/compute budgets on independent current and historical questions. Include useful-history retention and negative controls. Preserve all failures. No additional inference is authorized; CPU cost for new verifier/gating models is unmeasured.

### 5. Publication Value

A replicated supplied-evidence utilization finding could support an empirical contribution. A positive pilot difference or renamed filter cannot establish original temporal reasoning or memory selection.

## Answer-component verification

### 1. Observed Failure Modes

Primary PC006 has all requested fields but uncertain interpretation. Alternative PC033 contains one correct component and one wrong component. Earlier confirmed P1b contains incomplete task delivery; P1c's 64 identifiable replies are all complete. No current primary factual/task disagreement was manufactured.

### 2. Existing Methods and Published Prior Art

CoVe plans and executes verification questions before revising a draft. RARR retrieves evidence and revises disagreements while preserving original content; attribution is not identical to truth. A component checklist or closed-ledger join alone is not an original algorithm.

### 3. Potential Algorithmic Improvements

Investigate explicit separation of claim support, target binding and answer delivery only if a typed-rule baseline leaves reproducible errors. This is a bounded measurement prototype candidate, not an established learning method.

### 4. Validation Feasibility

Prospective offline bank: 24 synthetic development snippets balanced over complete-correct, complete-wrong, correct-partial, correct-intermediate-only, unsupported and ambiguous-answer cases; freeze a separate 24-item held-out bank before tuning. These would be artificial fixtures, not new model generations. Compare literal matching, typed entity/date/component joins and answer-act checks; ablate each check. A later authorized model comparison should include CoVe/RARR-style verification with matched generation budgets. Measure false acceptance/rejection, correct-answer preservation, runtime and RAM. No gold answer is supplied as a deployable method input. Independent annotators must validate target acts before performance claims.

### 5. Publication Value

The present audit exposes a validity problem in coupled scoring, which is worth resolving regardless of algorithm success. A new algorithm requires gains beyond strong baselines on independent examples; none has been demonstrated.

## Response-boundary management

### 1. Observed Failure Modes

Reproducible engineering evidence: eight heading-boundary ambiguities, 64 cross-turn continuations and 70 output-budget stops. Sensitivity converts four ambiguous prefixes to proposed Correct and four to Incorrect; an increase in evaluability is not necessarily an increase in accuracy.

### 2. Existing Methods and Published Prior Art

Native stopping, templates and delimiter splitting are known engineering. Efficient Guided Generation uses finite-state/grammar constraints on generation. Decoupling Logic from Persona reports separate schema and raw-text behavior. Structural/semantic discrepancy and constrained output are therefore not unclaimed territory.

### 3. Potential Algorithmic Improvements

Quote/code-aware prefix attribution with explicit abstention is a measurement candidate. It must not choose a later correct answer or use condition labels. Current evidence does not show that simple splitting fails more often than a proposed state-aware method on independent data.

### 4. Validation Feasibility

Retain the prior separate 24-development/24-held-out boundary-fixture plan: genuine role/section transitions, quoted headings and ambiguous documents, balanced over correct and false answers. Compare unchanged response_status_v1, native stop, literal-header splitting and state-aware splitting, with quote/code and heading-check ablations. Report false splits, abstention, exact spans and downstream label sensitivity; failure to beat the simple baseline is a valid negative result. Offline processing requires no inference; measured CPU/RAM cost is still pending. Future controlled decoding requires separate authorization.

### 5. Publication Value

Independent evidence of measurement bias may strengthen the empirical paper. Recovery of these eight development prefixes alone is not novel generation control or validated accuracy improvement.

## Persona-evidence separation and interaction-aware conditioning

### 1. Observed Failure Modes

P1c has no fidelity reference and no confirmed semantic interaction. It cannot currently establish persona interference or a reliability/fidelity trade-off.

### 2. Existing Methods and Published Prior Art

The earlier primary-source matrix documents FPPS steering in When Personalization Misleads; the decoupling preprint separates logic and persona paths and evaluates both raw and structured behavior. Mixed/separated prompting is also a known baseline.

### 3. Potential Algorithmic Improvements

Retain interaction-aware conditioning as a falsifiable hypothesis, not a routing implementation. A concrete residual failure after steering/separation would be needed before proposing originality.

### 4. Validation Feasibility

Require independently replicated package effects, explicit fidelity targets, matched compute, mixed/separated prompts and feasible published steering/architecture baselines. Document unsupported backend access rather than substituting a weaker namesake. New model calls or training are not authorized here.

### 5. Publication Value

No candidate is an independently validated original contribution. Current structural evidence is Level 0 engineering; semantic suggestions are provisional exploratory evidence. A strong empirical path remains possible with independent annotation, model/template sensitivity, fresh paired cases and transparent null results. No PLOS ONE readiness or acceptance claim is made.
''')

    log=Path('docs/research_development_log.md')
    with log.open('a',encoding='utf-8',newline='\n') as stream:
        stream.write(f'''\n\n## {now} — P1c semantic integrity reinspection (software-recorded time)\n\nMaintainer: Yaxin ZHENG. Human annotation confirmation remains pending; this is not a review timestamp. HEAD {subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}; entry tree was already dirty.\n\nRead all 72 masked semantic records, original transcription and approved rubric, then eight full native continuations/prompts after primary audit freeze. Found joint group assignments and ordinal-pair coding, so procedural independence is not established. Reinspection retains categorical/task labels and proposes six primary ordinal changes in five records, plus PC023 two-field secondary adjustment. All original values remain intact. Additive measurement-state metadata separates boundary, evidence, interpretation and administrative uncertainty without changing the primary estimand. No official semantic effects or new inference.\n\nCommands: tools/p0_capture.py wrapped tools/p1c_semantic_integrity.py primary/secondary; tools/p1c_integrity_registration.py template; tools/p1c_semantic_verify.py; targeted pytest and full pytest. The initial schema-inspection Python command loaded protected mapping keys but failed to serialize dict_keys before any assignment record was printed; disclosure retained, no complete blinding claim. Two guessed read paths were absent and resolved to actual versions. Secondary export attempt 01 failed on nonuniform CSV fields after nine rows; failed JSON/CSV and capture preserved, fixed uniform-column export written as active v2 in attempt 02.\n\nValidation: source verification reconstructed the 72-request run twice, checked actual binary hashes, 72 tokenizer records, 700 events, 45 source pins and 5,798 historical artifacts. Targeted tests: 40 passed. Full suite: {tests['stdout'].strip().splitlines()[-1]}. Existing entry files and original proposal seals preserved; development log append-only. Tests use explicitly synthetic temporary decisions, never registered research approvals.\n\nNew files: seven P1c integrity/uncertainty/metric/confirmation/readiness/algorithm reports; tools/p1c_semantic_integrity.py, tools/p1c_integrity_registration.py, tools/p1c_integrity_closeout.py; tests/test_p1c_semantic_integrity.py; semantic_integrity_v1 CSV/JSON proposals, states, diagnostic, exact-weight specification, blank confirmation, provenance and reproducibility inventory. Prior review files, protocols, outputs, classifications and Git history unchanged.\n\nThe single remaining gate is adoption/correction of the exact semantic versions. Literature method checks cover LongMemEval, FC/PS admission, CoVe, RARR, finite-state guided generation and logic/persona separation; no algorithm originality or implementation performance is claimed. Bounded offline fixture plans remain prospective. Six-cluster development estimates cannot establish population mechanisms or publication readiness. No commit/push.\n''')
    check=preserve();schema=schemas()
    diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True)
    a.require(diff.returncode==0,'Git whitespace check failed '+diff.stdout+diff.stderr)
    inventory={str(p):a.sha(p) for p in ROOT.iterdir() if p.is_file()}
    inventory.update(REPORTS)
    for path in ('tools/p1c_semantic_integrity.py','tools/p1c_integrity_registration.py','tools/p1c_integrity_closeout.py','tests/test_p1c_semantic_integrity.py'):
        inventory[path]=a.sha(path)
    a.write(ROOT/'reproducibility_manifest_v1.json',{'version':'p1c_semantic_integrity_closeout_v1','software_verified_utc':datetime.now(timezone.utc).isoformat(),
        'status':'PASS','preservation':check,'source_verification':sourcecheck,'schema_counts':schema,
        'artifact_sha256':inventory,'active_import_sources':gate.sources(),
        'complete_test_capture':str(RESULT/'tests_full_01.json'),'complete_test_capture_sha256':a.sha(RESULT/'tests_full_01.json'),
        'test_summary':tests['stdout'].strip().splitlines()[-1],
        'original_distribution':diag['original_primary_distribution'],'reviewed_distribution':diag['reviewed_primary_distribution'],
        'registered_human_semantic_annotations':0,'official_semantic_effects_computed':False,'new_model_inference':0,
        'git_diff_check':'PASS','git_status':subprocess.check_output(['git','status','--short'],text=True),
        'failed_export_preserved':True,'active_secondary_version':'v2'})
    print(json.dumps({'reports':list(REPORTS),'artifact_count':len(inventory),'preservation':check,'tests':tests['stdout'].strip().splitlines()[-1],'gate':'PENDING_ACTUAL_RESEARCHER_ANNOTATION_CONFIRMATION'},indent=2))


if __name__=='__main__':main()
