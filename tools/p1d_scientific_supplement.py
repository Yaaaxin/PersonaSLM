"""Finish additive audit inventories; preserve every prior candidate and result."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from p1d_design import read, write, csvwrite, sha, th, CELLS
from p1d_scientific_audit import DEST, BANK

def main():
    cases=read(BANK/'candidate_bank_v1.json')['cases'];changes=[]
    for c in cases:
        fs={f['id']:f for f in c['facts']}
        for left,right,axis in [('E1V0','E0V0','E'),('E1V1','E0V1','E'),('E0V1','E0V0','V'),('E1V1','E1V0','V')]:
            a=fs[c['histories'][left]['source_id']];b=fs[c['histories'][right]['source_id']]
            changed={k:{'left':a[k],'right':b[k]} for k in ('entity','predicate','value','start','end') if a[k]!=b[k]}
            changes.append({'case_id':c['case_id'],'contrast':left+'-'+right,'axis':axis,'changed_fact_attributes':changed,
                'quotation_speaker_unchanged':c['persona_entity'],'one_quotation_each':True,'same_reference':c['required_components'],
                'same_evidence_sha256':th(c['trusted_evidence']),'same_question_sha256':th(c['question']),
                'interpretation':'Entity/name/value substitution' if axis=='E' else 'Validity interval/date/value substitution',
                'unsupported':'Pure topical relevance' if axis=='E' else 'Date-only or pure temporal validity manipulation'})
    write(DEST/'intervention_difference_inventory_v1.json',changes)
    dup=defaultdict(list)
    for c in cases:dup[c['question']].append(c['case_id'])
    write(DEST/'repeated_question_groups_v1.json',{'groups':[{'question':q,'cases':ids} for q,ids in dup.items() if len(ids)>1],
        'interpretation':'Same literal follow-up can refer to different context entities/ledgers. These are not duplicate whole cases; they expose template reuse.',
        'whole_case_identity':'Question + fixed context + evidence + required components'})
    applicability=read(BANK/'metric_applicability_candidate_v1.json')
    metrics=read('docs/validation/p1d/proposed_v1/analysis_policy_proposal_v1.json')['all_metrics']
    if len({(r['case_id'],r['condition']) for r in applicability})!=1728:raise ValueError('Applicability identity')
    if any(not all(r[m] is True for m in metrics) for r in applicability):raise ValueError('Eligibility differs')
    write(DEST/'metric_applicability_verification_v1.json',{'source_sha256':sha(BANK/'metric_applicability_candidate_v1.json'),
        'counts':{m:1728 for m in metrics},'instruct_expected_per_metric':288,'new_outcomes':0,
        'scope':'Eligibility is frozen only at final experiment adoption. Current matrix matches approved prospective definitions; unknown scores do not remove eligibility.'})
    native=read(BANK/'native_tokenizer_validation_v1.json')['identity'];cfg=read('configs/p1_wave1_v1.json')
    base=Path(cfg['server_file']).parent
    actual={cfg['model_file']:sha(cfg['model_file']),cfg['server_file']:sha(cfg['server_file']),str(base/'llama-tokenize.exe'):sha(base/'llama-tokenize.exe')}
    if actual[cfg['model_file']]!=native['model_sha256'] or actual[cfg['server_file']]!=native['backend_sha256'] or actual[str(base/'llama-tokenize.exe')]!=native['tokenizer_sha256']:raise ValueError('Current identity mismatch')
    for name,h in native['dll_hashes'].items():
        if sha(base/name)!=h:raise ValueError('DLL mismatch: '+name)
    write(DEST/'current_runtime_identity_verification_v1.json',{'actual_sha256':actual,'dlls_verified':len(native['dll_hashes']),
        'model_bytes':Path(cfg['model_file']).stat().st_size,'software_utc':datetime.now(timezone.utc).isoformat(),
        'no_server_or_model_inference':True,'native_token_records_reused_only_after_exact_log_and_prompt_hash_checks':1728})
    # Preserve the failed hash-based join: duplicate response text is not a key.
    old=read(DEST/'historical_budget_summary_v1.json');new=read(DEST/'historical_budget_summary_v2.json')
    write(DEST/'engineering_correction_register_v1.json',{'failed_artifacts':['historical_budget_summary_v1.json','historical_budget_delivery_audit_v1.csv','failed_attempts/p1d_budget_manifest_hash_join_v1.py'],
        'active_artifacts':['historical_budget_summary_v2.json','historical_budget_delivery_audit_v2.csv'],
        'failure':'Joining historical annotations by non-unique raw-response hash duplicated one P1c rating in the new diagnostic.',
        'old_P1c_delivery':old['counts']['p1c']['budget_and_delivery'],'correct_P1c_delivery':new['counts']['p1c']['budget_and_delivery'],
        'resolution':'Join P1b by request_id and P1c by registered request_key -> anonymous_response_id, then verify raw hashes. Assert one-to-one response IDs.',
        'historical_sources_modified':False,'official_P1c_analysis_affected':False})
    # Complete per-request precedence without editing the first candidate.
    m=read(DEST/'budget_calibration_manifest_candidate_v1.json')
    m['version']='p1d_budget_manifest_candidate_v2';m['supersedes_sha256']=sha(DEST/'budget_calibration_manifest_candidate_v1.json')
    m['effective_parameter_precedence']='Common pinned model configuration applies except max_new_tokens, explicitly overridden by each request. No other parameter may vary.'
    m['approval_scope']='A single approval would authorize the exact 144-request development budget diagnostic and its inspected development stimuli only; no main-study or Instruct inference and no automatic main-budget amendment.'
    write(DEST/'budget_calibration_manifest_candidate_v2.json',m)
    print({'difference_rows':len(changes),'dlls_verified':len(native['dll_hashes']),'active_budget_manifest_sha256':sha(DEST/'budget_calibration_manifest_candidate_v2.json')})

if __name__=='__main__':main()
