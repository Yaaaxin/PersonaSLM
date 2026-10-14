"""Concrete consolidated readiness packet, not an inference authorization request."""
from pathlib import Path
from p1d_design import read,write,sha

ROOT=Path('docs/validation/p1d/development_readiness_v1')
CANDIDATE=Path('docs/validation/p1d/independent_candidates_v4')

def main():
    token=read(CANDIDATE/'native_tokenizer_validation_v1.json')
    approval=Path('docs/validation/p1d/authorization_v1/researcher_plan_approval_corrected_v1.json')
    objects=[approval,CANDIDATE/'candidate_provenance_manifest_v1.json',CANDIDATE/'candidate_bank_v1.json',
        CANDIDATE/'base_candidate_prompts_v1.json',CANDIDATE/'native_tokenizer_validation_v1.json',
        CANDIDATE/'material_review_candidate_v1.csv',CANDIDATE/'metric_applicability_candidate_v1.json',
        ROOT/'model_comparison_estimands_v1.json',ROOT/'output_budget_diagnostic_proposal_v1.json',
        ROOT/'statistical_implementation_binding_v2.json',ROOT/'official_instruct_metadata/provenance_v1.json',
        ROOT/'independent_measurement/boundary_review_blinded_v1.csv',
        Path('docs/validation/p1d/proposed_v1/analysis_policy_proposal_v1.json'),
        Path('docs/validation/p1d/proposed_v1/contrast_specification_v1.json')]
    old_inventory=read(ROOT/'full_allocation_planning_inventory_v1.json')
    old_inventory['source_candidate_sha256']=sha(CANDIDATE/'candidate_bank_v1.json')
    old_inventory['supersedes']=str(ROOT/'full_allocation_planning_inventory_v1.json')
    write(ROOT/'full_allocation_planning_inventory_v2.json',old_inventory)
    objects.append(ROOT/'full_allocation_planning_inventory_v2.json')
    packet={'version':'p1d_execution_readiness_packet_v1','researcher':'Yaxin ZHENG',
        'prospective_protocol':'APPROVED_WITH_SCIENTIFIC_LIMITATIONS','inference_go_no_go':'NO_GO',
        'authorized_inference_requests':0,'proposed_base_requests':1728,'proposed_instruct_requests':288,
        'proposed_main_total':2016,'separate_budget_diagnostic_base_proposal':144,'budget_diagnostic_authorized':False,
        'objects_sha256':{str(p).replace('\\','/'):sha(p) for p in objects},
        'candidate_not_confirmatory_freeze':True,'frozen_execution_manifest':None,
        'material_checks':{'cases':288,'speakers':144,'conditions':6,'base_candidate_prompts':1728,
            'active_length_matches':token['active_matches'],'procedural_length_matches':token['control_matches'],
            'context_fit_256':token['context_fit_256'],'native_token_range':token['input_token_range'],
            'human_case_validity_confirmations':0,'independent_measurement_ratings':0,'control_semantics':'DIAGNOSTIC_ONLY_REVIEW_PENDING'},
        'base_identity':token['identity'],
        'instruct_runtime':'UNVERIFIED: source metadata available, no selected local GGUF or rendered backend validation',
        'budget':'Approved 96-token reference preserved; empirical adequacy not established. Any change requires prospective amendment.',
        'next_required_decisions':['Actual material/scientific validity review of this candidate bank, with documented corrections if needed',
            'Actual independent measurement evidence or explicit scientifically justified limitations; no fictional reviewer',
            'A separately bounded authorized development budget diagnostic, after its exact manifest is ready',
            'Final verified model/material/budget freeze and explicit exact-manifest execution authorization'],
        'not_requested':'No reapproval of the corrected prospective plan. No blanket authorization of absent/unvalidated execution manifests.',
        'scientific_limitations':['E/V package effects, not pure R/T or latent mechanisms','S/F/H programme retained',
            'Procedural controls are not certified semantically neutral','Shared synthetic template ancestry and hypothetical case worlds',
            'Model comparison limited to 24 paired speaker clusters','Precision assumptions are not empirical ICC estimates',
            'No independently validated original algorithm or publication-readiness claim']}
    write(ROOT/'execution_readiness_packet_v1.json',packet)
    bindings='\n'.join(f'| `{p}` | `{h}` |' for p,h in packet['objects_sha256'].items())
    text=f'''# P1d execution readiness and next authorization checkpoint — v1

Maintainer: Yaxin ZHENG. Prospective protocol adoption: APPROVED WITH SCIENTIFIC LIMITATIONS. **Real inference: NO-GO; authorized requests: zero.** No approval is being requested for an absent executable manifest.

## Concrete current materials

The current independent-validation candidate is v4: 144 new synthetic persona identities, 144 distinct paired other-person identities, 288 case-scoped hypothetical scenarios, four balanced families/domains and 144 current/144 historical queries. Its 1,728 Base candidate prompts have actual pinned vocabulary records. Active-cell matches: {token['active_matches']}/288; procedural matches: {token['control_matches']}/288. Input range: {token['input_token_range'][0]}–{token['input_token_range'][1]}; context fits at 256 tokens: {token['context_fit_256']}. These are technical results, not human semantic validity or a confirmatory freeze.

The [current candidate manifest](validation/p1d/independent_candidates_v4/candidate_provenance_manifest_v1.json) records content hashes for review. **It is not a frozen execution manifest.** The [288-case review file](validation/p1d/independent_candidates_v4/material_review_candidate_v1.csv) includes all six histories/baselines, evidence, references and source traces; human decisions remain blank. The [72-record independent boundary package](P1d_independent_boundary_review_guide_v1.md) is ready for a real reviewer; zero independent ratings exist.

The main prospective inventory remains 1,728 Base plus 288 Instruct = 2,016. Instruct covers the same six conditions on 48 cases/24 speakers; its corresponding Base observations already belong to the main Base arm. No full-cohort model interaction or pure post-training effect is identified. The planning inventory has no executable order or runtime authorization. Instruct prompts require verified official rendering and the actual local tokenizer before they can be counted as executable requests.

## Gates and scope

| Requirement | Actual status |
| --- | --- |
| Exact reviewed protocol and corrected fingerprint | Registered; originals unchanged |
| Candidate ground truth, allocation and native Base tokens | Mechanically checked; source versions and failures retained |
| Independent stimulus/control semantic validity | Pending actual review; procedural controls diagnostic only |
| Independent measurement | Ready to collect; no independent human ratings or agreement |
| Base model/backend | Original pinned identity verified; no new inference |
| Instruct model | Official metadata hashed; local GGUF/source revision/quantizer/runtime/template equivalence unresolved |
| Output budget | 96-token reference retained; adequacy requires separately authorized development evidence |
| Endpoints/statistics | Approved primary temporal Incorrect incidence and complete task success; six primary comparisons, all 16 registered contrasts, original signed weights and speaker clustering |
| Precision | 144-speaker choice retains original simulation assumptions and uncertainty limits |
| Final execution manifest and exact authorization | Absent / not granted |

The separate development budget proposal concerns eight inspected development cases × six cells × three budgets = 144 Base requests, not extra independent-validation cases and not authorized here. It would establish whether the 96-token reference can support measurement before an independent freeze; changing that reference needs a prospective amendment. Do not authorize the main cohort by treating these missing checks as passed.

Complete the material review and independent measurement, resolve the exact local Instruct source/template, and prepare any required bounded development diagnostic as a concrete separate manifest. Then combine final material, budget/model configuration, statistical specification and exact execution scope in one authorization decision. The already adopted prospective design is not reopened merely because its old documents retain historical PENDING text.

## Exact current bindings

| File | SHA-256 |
| --- | --- |
{bindings}

Machine-readable packet: [execution_readiness_packet_v1.json](validation/p1d/development_readiness_v1/execution_readiness_packet_v1.json), SHA-256 `{sha(ROOT/'execution_readiness_packet_v1.json')}`. The [development report](P1d_development_readiness_v1.md) records scientific limitations, preserved failures, model metadata discrepancies and the mandatory Algorithmic Opportunity Assessment. None of the current engineering baselines is an independently supported original algorithm. PLOS ONE readiness is not established by these checks.
'''
    path=Path('docs/P1d_execution_readiness_packet_v1.md')
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    print({'packet':str(path),'status':'NO_GO','authorized_requests':0})

if __name__=='__main__':main()
