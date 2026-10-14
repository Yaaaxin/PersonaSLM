"""Write prospective readiness bindings and focused literature/method registries."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from p1d_design import read, write, csvwrite, sha, th
from p1d_scientific_audit import DEST, BANK, only

def main():
    cases=read(BANK/'candidate_bank_v1.json')['cases'];diagnostics=[]
    for c in cases:
        if c['family']!='context_followup':continue
        possibilities=[]
        for entity in (c['persona_entity'],c['other_person']):
            fs=[only(c['facts'],entity,c['domain'][k],c['query_date']) for k in ('assignment','window')]
            possibilities.append({'entity':entity,'component_values':[f['value'] for f in fs],'source_ids':[f['id'] for f in fs]})
        diagnostics.append({'case_id':c['case_id'],'question':c['question'],'target_name_absent_from_question':c['target_entity'] not in c['question'],
            'no_context_two_ledger_consistent_answers':possibilities,'distinct_answer_pairs':len({tuple(p['component_values']) for p in possibilities})==2,
            'scope':'Offline material diagnostic only, not a new inference condition. The fixed context disambiguates; persona/history can provide correlated cues, so unique internal context use is not identified.'})
    write(DEST/'context_removal_material_diagnostic_v1.json',diagnostics)
    prior=Path('docs/validation/p1d/proposed_v1/related_work_matrix_v4.json')
    literature={
        'version':'related_work_monitor_delta_v5','parent_path':prior.as_posix(),'parent_sha256':sha(prior),
        'software_checked_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Focused primary-source recheck of implementation overlap and model provenance. Previous ten-paper methods matrix retained; no claim that all full texts were reread in this turn.',
        'queries_or_direct_sources':[
            'https://aclanthology.org/2026.findings-acl.395/',
            'https://arxiv.org/html/2410.10813v2',
            'https://arxiv.org/html/2610.11188v1',
            'https://aclanthology.org/2024.findings-acl.212/',
            'https://aclanthology.org/2023.acl-long.910/',
            'https://huggingface.co/Qwen/Qwen3.5-2B/blob/965dcc54bc9c0591873df0e9869c056a54d323d1/README.md',
            'https://huggingface.co/bartowski/Qwen_Qwen3.5-2B-GGUF/blob/main/README.md'],
        'findings':[
            {'work':'LongMemEval','status':'ICLR 2025; official venue bound in parent matrix','inspected_sections':'5.4 and D: event timestamp indexing and extracted query-range filtering','overlap':'Direct overlap with time filtering; weak time-range extraction by smaller reader is already reported','distinguishing_test':'Separate explicit query-date extraction from supplied-date entity/value checking; matched compute and persona fidelity, independently annotated text.'},
            {'work':'When Personalization Misleads / FPPS','status':'Findings of ACL 2026','canonical_id':'10.18653/v1/2026.findings-acl.395','scope':'Publication record refreshed; activation steering implementation details inherited from prior full-method matrix','overlap':'Factuality-preserving persona conditioning already targeted','distinguishing_test':'Fair steering/admission/verification baselines under CPU and fidelity constraints; no such empirical comparison yet.'},
            {'work':'What to Admit and How to Present','status':'arXiv preprint 2610.11188v1; peer review not established','overlap':'Factual/persona consistency admission and presentation controls already studied','distinguishing_test':'Measure admission errors, task completeness, style fidelity and additional judge/model cost.'},
            {'work':'Chain-of-Verification / RARR','status':'Findings ACL 2024 / ACL 2023','overlap':'Verification and revision already published','distinguishing_test':'Supplied structured claims do not replicate language extraction/search/revision; equal additional computation needed.'}],
        'novelty_status':'NO_SUPPORTED_ORIGINAL_ALGORITHM','missing_evidence':'Independent text/boundary annotations, fair complete-system baselines and held-out outcomes.'}
    write(DEST/'related_work_monitor_delta_v5.json',literature)
    parent=Path('docs/validation/p1d/development_readiness_v1/algorithm_opportunity_registry_update_v3.json')
    methods=[]
    for name,evidence,baseline,gap,plan,classification in [
        ('temporal_entity_verification','Historical errors/ambiguity; checker date-scope fixture defect','Requested-date and entity joins; LongMemEval temporal retrieval','Natural-language date/entity attribution unresolved; not a demonstrated failure of prior methods','Independently label free-text claims, compare extraction-aware checks and abstention at equal cost','ENGINEERING_ADAPTATION'),
        ('history_admission','Package manipulations supply competing source values; no new outcomes','All/remove history, lexical filtering, FC/PS admission','Fidelity/reliability tradeoff under CPU constraints unmeasured','Separate admission correctness from downstream quality and budget; no candidate outputs for tuning','INCREMENTAL_CANDIDATE_UNVALIDATED'),
        ('persona_evidence_separation','P1b/P1c patterns do not identify unique persona interference','FPPS, evidence-priority prompt, AO-DA paths','Strong published overlap; local activation baseline unavailable','Traceable same-family comparisons and persona fidelity outcomes before algorithm claim','POTENTIAL_GAP_UNVERIFIED'),
        ('component_verification','P1b correct partial answers; P1c factual/task coincidence','Structured component checks, CoVe, RARR','Free-text extraction and task-delivery adjudication remain unvalidated','Separate evidence-input contracts implemented; eight authored fixtures, then independent human-labeled text','ENGINEERING_ADAPTATION'),
        ('response_boundary','Eight P1c ambiguities; both EOS outputs ambiguous','EOS, literal stops, role/heading/fence parsers, official template','No independent span gold; parser agreement is not accuracy','Existing masked 72-item review; compare accepted spans and answer loss, then independent new outputs','KNOWN_ENGINEERING_APPROACH'),
        ('interaction_aware_conditioning','P1c package estimates uncertain and extraction-sensitive','Fixed policies plus full factorial comparisons','No replicated interaction supporting adaptation','Defer routing prototype; retain null/adverse results and require independent replication','DEFERRED_INSUFFICIENT_EVIDENCE')]:
        methods.append({'candidate':name,'observed_failure_evidence':evidence,'published_or_simple_baselines':baseline,'unresolved_gap':gap,
            'potential_improvement_and_validation':plan,'classification':classification,'new_inference':False,
            'CPU_cost':'End-to-end unmeasured; offline checker timings exclude extraction/model calls.',
            'persona_fidelity':'Must be measured separately; deleting all persona/history is a baseline, not sufficient success.',
            'publication_value':'Measurement/empirical contribution possible; no independently validated algorithmic originality.'})
    write(DEST/'algorithm_opportunity_registry_update_v4.json',{'parent_path':parent.as_posix(),'parent_sha256':sha(parent),'rows':methods})
    approved=Path('docs/validation/p1d/authorization_v1/researcher_plan_approval_corrected_v1.json')
    files=[BANK/'candidate_bank_v1.json',BANK/'candidate_provenance_manifest_v1.json',BANK/'base_candidate_prompts_v1.json',BANK/'native_tokenizer_validation_v1.json',BANK/'metric_applicability_candidate_v1.json',
        Path('docs/P1d_protocol_addendum_proposed.md'),Path('docs/P1d_researcher_decision_packet_v1.md'),approved,
        Path('docs/validation/p1d/proposed_v1/analysis_policy_proposal_v1.json'),Path('docs/validation/p1d/proposed_v1/contrast_specification_v1.json'),
        DEST/'budget_calibration_manifest_candidate_v2.json',DEST/'case_scientific_review_v1.csv',DEST/'control_review_masked_v1.csv',DEST/'control_semantic_risks_v1.csv',DEST/'instruct_rendered_candidates_v1.json']
    blockers=[
        {'id':'stimulus_scope','status':'OPEN_SCIENTIFIC','problem':'Shared development grammar does not establish independently authored template validation.','resolution':'Explicit restricted-population amendment or new independently reviewed templates; preserve existing bank.','human_confirmation_required':True},
        {'id':'material_controls','status':'HUMAN_REVIEW_PENDING','problem':'288 AI validity/control proposals are not researcher or independent-human decisions.','resolution':'Review case evidence and masked controls; diagnostic interpretation only; resolve material leakage if found.','human_confirmation_required':True},
        {'id':'measurement','status':'INDEPENDENT_REVIEW_PENDING','problem':'No independent reviewer/pilot evidence; construct and boundary uncertainty.','resolution':'Obtain actual blinded ratings and adjudication under existing plan; report infeasibility honestly.','human_confirmation_required':True},
        {'id':'instruct','status':'TECHNICALLY_INCOMPLETE','problem':'No traceable local GGUF or native runtime/template/token/RAM/stop validation.','resolution':'Select verifiable conversion/source revision and validate exact local artifact; no silent model substitution.','human_confirmation_required':'Only if substantive approved model configuration changes or new inference is requested.'},
        {'id':'budget','status':'BOUNDED_DEVELOPMENT_AUTHORIZATION_REQUIRED','problem':'96-token suitability not established.','resolution':'Exact 144-request development manifest v2, conditional preflight, then adopted semantic assessment and any required main-budget amendment.','human_confirmation_required':True},
        {'id':'full_execution','status':'NO_GO','problem':'No complete frozen validated main-study manifest or execution authorization.','resolution':'One final 2016-request readiness/authorization packet after prerequisites, retaining all targets unless amended.','human_confirmation_required':True}]
    write(DEST/'execution_readiness_packet_v2.json',{'version':'p1d_execution_readiness_v2','status':'NO_GO','approved_prospective_design':True,
        'current_candidate_version':'p1d_independent_candidate_bank_v4','candidate_frozen_for_confirmatory_use':False,
        'main_planned_base':1728,'main_planned_instruct':288,'main_total':2016,'authorized_inference':0,
        'development_budget_diagnostic_proposed':144,'development_budget_included_in_main':False,'approved_contrasts':16,
        'primary_endpoints':['temporal_Incorrect_label_incidence','task_success'],'primary_family':['E','V','ExV'],
        'restricted_estimand':'Entity-match and requested-interval package contrasts conditional on fixed templates/model; not pure R/T or full S/F/H.',
        'source_sha256':{p.as_posix():sha(p) for p in files},'blockers':blockers,
        'latest_user_hash_transcription_mismatch':'User repeated ...26eae432...; actual corrected/approved addendum is ...26eea432...; existing explicit correction preserved, no new approval gate.'})
    write(DEST/'dependency_install_record_v1.json',{'purpose':'Official template-only rendering; no weights or inference',
        'first_attempt':'Sandbox socket access failed with WinError 10013; no usable cached Jinja2 wheel.',
        'resolution':'Approved escalation of the same bounded pip install into project-local results directory.',
        'installed':{'Jinja2':'3.1.6','MarkupSafe':'3.0.4'},'project_venv_modified':False,
        'reproduce':'Install exact template_runtime_requirements_v1.txt into results/p1d_scientific_validation/v1/template_runtime, then run tools/p1d_instruct_template_check.py into a new versioned output directory.'})
    print({'followup_material_checks':len(diagnostics),'readiness':'NO_GO','algorithm_candidates':len(methods)})

if __name__=='__main__':main()
