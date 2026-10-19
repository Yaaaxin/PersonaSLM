"""Non-generation milestone verification, scoped tests, log append and sealing."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import p1d_instruct_smoke as s
import p1d_instruct_measurement as m
from escp_offline import Atom,Claim,verify

O=s.OUT
A=Path('docs/validation/research_alignment_v1')
P5=Path('docs/validation/p5/oracle_evidence_proposed_v1/oracle_evidence_manifest_proposed_v1.json')
TESTS=['tests/test_p1d_instruct_smoke.py','tests/test_p1d_instruct_preparation_v3.py',
       'tests/test_p1d_instruct_measurement.py','tests/test_escp_offline.py',
       'tests/test_personaslm_alignment.py','tests/test_p5_oracle_proposal.py',
       'tests/test_response_status.py','tests/test_p1d_format_analysis.py',
       'tests/test_p1d_fair_retrieval.py','tests/test_p1d_boundary_locality.py']

def observed_diagnostics():
    cases={c['case_id']:c for c in s.load(s.b.DEV/'development_examples_v5.json')['cases']}
    values={0:[('locker','Locker 106')],1:[('locker','Locker 106'),('pickup_window','09:00-10:00')],
            2:[('locker','Locker 107'),('pickup_window','12:00-13:00')],
            3:[('locker','Locker 102'),('pickup_window','10:00-11:00')],
            4:[('locker','Locker 111'),('pickup_window','09:00-10:00')],5:[],6:[],7:[('locker','Locker 112')]}
    rows=[]
    for c in [cases[k] for k in s.b.CASE_IDS]:
        n=int(c['case_id'].split('_')[2]);facts=c['facts'];byid={f['id']:f for f in facts}
        evidence=[Atom(f['id'],f['entity'],f['predicate'],f['value'],f['start'],f['end'],provenance='registered_development_ledger') for f in facts]
        required={k['key']:(byid[k['source_id']]['entity'],byid[k['source_id']]['predicate'],c['query_date']) for k in c['required_components']}
        claims=[Claim(key,c['target_entity'],key,val,c['query_date']) for key,val in values[n]]
        d=verify(evidence,required,claims,abstains=n in (5,6))
        rows.append({'case_id':c['case_id'],'structured_subset_diagnostic':d,
            'provenance':'AI_MANUALLY_TRANSCRIBED_CLAIMS_NOT_AUTOMATIC_EXTRACTION_OR_HUMAN_GOLD',
            'not_covered':'Evidence absence/calendar-range and volunteer-role denials are outside this ledger-attribute checker; Tessa requested hub/exit absent.',
            'complete_response_verified':False,'generated_answer_changed':False,'human_confirmation':''})
    s.save(A/'observed_development_claim_diagnostics_v1.json',rows)

def packet():
    eng=s.load(O/'engineering_summary_v1.json')
    sources=[s.FROZEN,s.AUTH,MFILE:=m.OUT/'AI_proposals_UNCONFIRMED_v1.csv',m.OUT/'AI_proposals_UNCONFIRMED_v1.json',
        m.OUT/'boundary_alias_sensitivity_v1.json',P5,
        Path('docs/PersonaSLM_research_programme_alignment_v1.md'),Path('docs/PersonaSLM_persona_fidelity_measurement_v1.md'),
        Path('docs/ESCP_candidate_specification_v1.md')]
    table='\n'.join(f'| `{p.as_posix()}` | `{s.sha256(p)}` |' for p in sources)
    text=f'''# PersonaSLM P1d core alignment and next scientific decision packet v1

Maintainer: Yaxin ZHENG. AI-assisted scientific recommendations, not human adoption. This single packet closes the already authorized Instruct feasibility scope and proposes one bounded next inference. It does not reopen approved P1d design targets or adopt v1.2.

## Verified result and recommendation

Eight Instruct requests were **newly executed exactly once** after exact manifest/model/native-token/backend preflight: 8 successful, 0 failed, 7 native EOS, 1 budget termination. Mean latency 20.808s; observed process peak working set {eng['peak_working_set_bytes']} bytes. Raw run is `{eng['run']}`. Complete engineering and scientific reports are `P1d_instruct_feasibility_engineering_report_v1.md` and `P1d_instruct_feasibility_scientific_report_v1.md`.

AI proposals: five complete requested-answer forms, two nonanswers, one partial; two correct complete tasks; 8/14 requested components present and 3/14 supported. Seven finished utterances are not seven complete task answers. The registered strict eight-case gate fails. Cleo's role-denial factual scope has an explicit Incorrect/Unverifiable alternative; either choice leaves the feasibility decision unchanged. All eight judgments remain unconfirmed. Human review can use `{m.OUT.as_posix()}/independent_review_without_scores_v1.csv` without AI scores; adopting proposals would not constitute independent second-human annotation.

Original parser labels remain seven AMBIGUOUS and one TRUNCATED. Native `eos` versus expected `eog` is a separately documented compatibility issue, not a new structural reclassification or evidence of factual failure. Eight identifiable candidate spans are not independent boundary truth.

## Exact scientific status

| Readiness dimension | Status and required resolution |
| --- | --- |
| Instruct technical feasibility | PASS for the eight development prompts; local model/backend/template/tokenizer verified. Third-party source conversion lineage still partial |
| Model/task measurement adequacy | NO-GO: strict answer-completeness criterion fails. No universal model-family failure inferred |
| Core S/F/H | Alignment and exact proposed weights restored; no new full-factorial inference. H_none includes persona/style and is not C0 |
| Candidate stimulus/control validity | Existing 288 VALID_WITH_LIMITATIONS remain AI proposals; procedural controls diagnostic only. Reuse the existing 64-case/64-control stratified review packet |
| Independence/precision | 144 names, 288 cases, 247 question strings, 16 templates and four ancestors; conditional scope or prospective diversification needed. Existing simulations retained, not empirical ICC estimates |
| Fidelity/independent measurement | Three authored profiles, 12 counterexamples and blind forms prepared; no independent human validation or behavioral ratings yet |
| Scientific model policy | Original P1d allocation unchanged. A primary-model, output-policy or core-factorial amendment requires a concrete later decision; it is not adopted by this packet |
| Main inference authorization | NO-GO for 1,728 Base + 288 Instruct; none executed. Confirmatory materials are not frozen as validated data |

## One proposed next inference decision

**Recommended: AUTHORIZE_P5_ORACLE_8_WITH_LIMITATIONS**, or **DEFER_P5_ORACLE_8**.

Manifest: `{P5.as_posix()}`

SHA-256: `{s.sha256(P5)}`

Scope: exactly eight existing development cases, H_none, one generation per case, same completed Instruct model/template/seed/order/96-token configuration, CPU4/context4096, no retries/warmup, 45-minute ceiling. Maximum 768 new output tokens. The eight new prompts replace only the trusted-ledger block with its minimal answer-sufficient source chain. Full-ledger Instruct references are reused, never regenerated. Native tokenizer arrays match the official tokenizer, with 182–303 input tokens. No validation case, training, algorithm-effect comparison or additional generation is included. Model hash remains `{s.MODEL_SHA}`; backend hash `{eng['model']['backend_sha256']}`.

Scientific purpose: RQ4/P5 oracle generation headroom before attempting a new selector. Removing distractor rows changes evidence length, positions and candidate content jointly; the result identifies an oracle evidence **package**, not a pure retrieval mechanism or persona effect. Source-line and reference equality are checked. The oracle uses known reference witnesses and is not a deployable algorithm. Partial third-party GGUF lineage must remain explicitly accepted for this bounded diagnostic only.

Prespecified strict gate: eight identifiable, complete task answers with no answer-losing cut; separately report factual/temporal support, components and fidelity opportunity. Failure retains NO-GO and motivates targeted model/task-policy reconsideration, not an automatic sweep. Success only supports a separately proposed selection/all-condition development study. It cannot authorize the full validation cohort or silently reduce evidence in the adopted Track A design.

Approval would authorize only this exact eight-request P5 manifest. Deferral leaves it unexecuted; offline measurement/baseline/manuscript work remains available. The mandatory gate follows the researcher's explicit exclusion of future-phase inference from the current eight-request authorization. No software-enum change or completed engineering stage creates a new gate.

## Bound files

| File/version | SHA-256 |
| --- | --- |
{table}

The original Instruct approval is already registered and exhausted; do not ask for it again. Broad material adoption, independent annotation and confirmatory freezing are future substantive requirements, not approvals fabricated here. A conditional 64-request S/F/H development sketch exists in the alignment report but is neither execution-ready nor requested now.

## Algorithm and publication consequences

ESCP is a typed offline scaffold with 16 authored fixtures, four ablations and a simple equal-information reference. Both full methods match 16/16 expectations; the scaffold adds diagnostics and costs more CPU per typed check. No generated reliability or persona gain, originality, independent algorithm validation or publication readiness follows. The closest prior-art overlap is explicit in novelty matrix v7. The empirical paper path remains independent S/F/H evidence with reliable fidelity measurement, transparent uncertainty and useful null/adverse findings. PLOS ONE remains the first target.

Scoped regression results, raw source hashes, historical preservation and precise changed-file inventory are bound in `validation/p1d/instruct_smoke_v1/reproducibility_manifest_v1.json`; the file intentionally does not contain its own digest.
'''
    Path('docs/P1d_core_alignment_decision_packet_v1.md').write_text(text,encoding='utf-8',newline='\n')
    s.save(A/'researcher_next_decision_UNCONFIRMED_v1.json',{'researcher':'Yaxin ZHENG',
        'packet_path':'docs/P1d_core_alignment_decision_packet_v1.md',
        'packet_sha256':s.sha256(Path('docs/P1d_core_alignment_decision_packet_v1.md')),
        'manifest_path':P5.as_posix(),'manifest_sha256':s.sha256(P5),
        'allowed_decisions':['AUTHORIZE_P5_ORACLE_8_WITH_LIMITATIONS','DEFER_P5_ORACLE_8'],
        'researcher_decision':'','researcher_timestamp':None,'authorized_new_requests':0})

def tests():
    argv=[sys.executable,'-m','pytest','-q',*TESTS]
    started=s.b.utc_now();p=subprocess.run(argv,capture_output=True,text=True)
    record={'started_utc':started,'finished_utc':s.b.utc_now(),'argv':argv,'returncode':p.returncode,
            'stdout':p.stdout,'stderr':p.stderr,'generation_requests':0}
    s.save(O/'targeted_regression_results_v1.json',record);print(p.stdout,flush=True)
    s.require(p.returncode==0,'Regression failure preserved; resolve before sealing')

def verify_and_log():
    # Independent reconstruction does not contact a model server.
    reconstructed=s.audit();s.require(reconstructed==s.load(O/'execution_integrity_v1.json'),'Inference reconstruction differs')
    for name,value in m.build().items():s.require(value==s.load(m.OUT/name),'Measurement reconstruction differs: '+name)
    before=s.load(O/'source_preservation_baseline_v1.json');log=Path('docs/research_development_log.md')
    mismatches=[p for p,h in before['tracked_sha256'].items() if not Path(p).exists() or s.sha256(Path(p))!=h]
    s.require(not mismatches,'Historical tracked files differ: '+str(mismatches))
    old=Path('docs/validation/p1d/format_calibration_v1/reproducibility_manifest_v1.json');seal=s.load(old)
    errors=[p for p,h in seal['artifact_sha256'].items() if not Path(p).exists() or s.sha256(Path(p))!=h]
    s.require(not errors,'Previous milestone artifacts differ: '+str(errors))
    # Preserve exact working-tree log bytes (Git normalized blobs can differ on Windows).
    snapshot=O/'research_development_log_before_v1.md';snapshot.write_bytes(log.read_bytes())
    validation={'recorded_utc':s.b.utc_now(),'tracked_files_verified':len(before['tracked_sha256']),
        'previous_milestone_artifacts_verified':len(seal['artifact_sha256']),'previous_manifest_sha256':s.sha256(old),
        'run_reconstruction':'PASS','measurement_reconstruction':'PASS','historical_mismatches':[],
        'old_log_sha256':s.sha256(snapshot),'no_new_inference_from_verification':True}
    s.save(O/'historical_integrity_verification_v1.json',validation)
    corrections={'generation_failures':0,'test_failures':0,'non_generation_development_errors':[
        {'error':'FileNotFoundError while inspecting presumed events.jsonl','resolution':'Read actual immutable events/*.json inventory; no source edits.'},
        {'error':'PowerShell rg glob paths rejected as invalid names','resolution':'Use rg -g filters over tools directory.'},
        {'error':'Report builder KeyError case_id in masked proposals','resolution':'Join withheld mapping for reporting, preserving masked review files.'},
        {'error':'Report builder resume refused existing immutable engineering summary','resolution':'Require equality before reusing existing summary; no overwrite.'}],
        'documentation_correction':'Added required --preflight/--output arguments to new reproduction commands before final seal.',
        'measurement_limits':['No human-adopted new semantic ratings','Native eos/eog compatibility retained as sensitivity','No behavioral applicability retrofitted']}
    s.save(O/'development_corrections_v1.json',corrections)
    test=s.load(O/'targeted_regression_results_v1.json')
    entry=f'''\n\n## {s.b.utc_now()} — Programme alignment, eight Instruct feasibility requests and ESCP offline development

Phases: P1d/P3/P5/P6; RQ1–4. Protocol v1.1 and the approved P1d E/V scope remain unchanged; v1.2 is proposed. No confirmatory freeze or full-cohort authorization is inferred.

The latest explicit researcher instruction authorized eight existing development H_none requests, exact manifest {s.SHA}, model {s.MODEL_SHA}, CPU4/context4096/96 tokens, no retries and 45 minutes. No prior exact run existed. Authorization was registered with a software UTC timestamp and null human decision timestamp. All eight completed once (0 failures), seven EOS and one limit, 341 tokens, mean request latency20.808s, observed process peak2689376256 bytes. Full raw events, sources, tokens, HTTP bodies, model/backend/template/DLL hashes, prompts and order are preserved in results/p1d_instruct_smoke/development_v1/runs/20261014T160641-ca4d1cf9e0fd433e81d9c9d2bed924b3. No main1728/288 requests, Base reruns, training or other generation occurred.

AI-only item review proposes factual2Correct/6Incorrect, temporal2Correct/5Incorrect/1Unverifiable, task2Success/6Failure; five complete requested-answer forms, two nonanswers and one partial; 8/14 components present and3/14 supported. Cleo role-denial scope and complete-utterance versus complete-answer distinctions remain explicit. Human adoption fields are blank. The strict eight-case gate fails; main P1d and all-condition S/F/H inference remain NO-GO. Original parser statuses7AMBIGUOUS/1TRUNCATED are unchanged; eos/eog alias sensitivity is separately recorded. Eight candidate spans are not independent boundary truth. Matching Base references gives descriptive AI task difference+25pp; eight-cluster bootstrap sensitivity[0,62.5]pp is neither causal post-training attribution nor population coverage.

The full work tree P0–P6, RQ/H1–H5 mapping and exact C0–C7 contrasts were restored in prospective alignment documents; H_none is not C0. Persona Fidelity now has separate linguistic/behavioral rules, three authored profiles, twelve counterexamples and score-free review materials. The existing288-case bank, controls and stratified human review route remain unchanged; names do not remove16-template/four-ancestor dependence. No old simulations or broad historical test suites were rerun.

ESCP typed evidence/admission/component rules were implemented only offline with sixteen authored fixtures. Full scaffold and simple declarative reference both match16/16; four ablations score13/12/15/15. Longer CPU batches resolve initial clock-resolution zeros and show no speed advantage. These are known engineering operations, not a new algorithm or measured generated-persona gain. Zep, Mem0, FC/PS, FPPS, LongMemEval, CoVe, RARR and fidelity studies were compared using primary methods. Novelty remains unverified. Working manuscript sections and PLOS ONE evidence requirements were updated without invented Results.

Prepared, NOT executed: eight P5 oracle-evidence requests under manifest {s.sha256(P5)}. Same development cases/model/template/decoding; only sufficient evidence subset changes. Native vocabulary-only arrays182–303tokens match the official tokenizer. This is an evidence/length/position package headroom diagnostic, not a Track A persona contrast or deployable retrieval algorithm. One consolidated next-decision packet carries the exact proposed authorization; no automatic execution.

Validation: {test['stdout'].strip()}. Inference and measurement reconstructions agree. {validation['tracked_files_verified']} tracked files and {validation['previous_milestone_artifacts_verified']} previous milestone artifacts verified unchanged before this append; exact pre-append log preserved. Non-generation inspection/reporting errors and their fixes are recorded in development_corrections_v1.json; no tests or inference failures are concealed. Git HEAD remains {before['head']}; all changes remain working-tree only. No commit/push or author identity change.

Commands: the eight-request run with preflight (once); read-only audit/measurement reconstruction; personaslm_alignment.py, escp_offline.py, p5_oracle_proposal.py (vocabulary only), alignment report/closeout scripts; focused pytest suite; git diff --check. New report/artifact/code paths are enumerated in the reproducibility manifest rather than repeating unchanged historical records.
'''
    with log.open('ab') as f:f.write(entry.encode('utf-8'))

def seal():
    source=s.load(O/'source_preservation_baseline_v1.json');head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    s.require(head==source['head'],'HEAD changed')
    oldlog=O/'research_development_log_before_v1.md';log=Path('docs/research_development_log.md')
    s.require(log.read_bytes().startswith(oldlog.read_bytes()),'Log prefix changed')
    historical=[p for p,h in source['tracked_sha256'].items() if p!='docs/research_development_log.md' and s.sha256(Path(p))!=h]
    s.require(not historical,'Historical changes')
    roots=[O,A,Path('docs/validation/p6/escp_offline_v1'),P5.parent]
    # Every new tracked-eligible working-tree artifact plus ignored raw run files.
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],text=True).splitlines()
    paths={Path(p) for p in untracked}|{log}|set((s.ROOT).rglob('*'))
    paths={p for p in paths if p.is_file() and '__pycache__' not in p.parts and p.name!='reproducibility_manifest_v1.json'}
    checked_json=0;checked_csv=0
    for root in roots:
        for p in root.rglob('*.json'):s.load(p);checked_json+=1
        for p in root.rglob('*.csv'):
            with p.open(encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f);rows=list(reader)
            s.require(reader.fieldnames and len(reader.fieldnames)==len(set(reader.fieldnames)),'CSV duplicate fields')
            s.require(all(None not in r for r in rows),'CSV ragged rows');checked_csv+=1
    check=subprocess.run(['git','diff','--check'],capture_output=True,text=True)
    s.require(check.returncode==0,'Diff check failure: '+check.stdout+check.stderr)
    record={'version':'instruct_feasibility_and_programme_alignment_reproducibility_v1','recorded_utc':s.b.utc_now(),
        'git_head':head,'git_status':subprocess.check_output(['git','status','--short'],text=True),
        'artifact_sha256':{p.as_posix():s.sha256(p) for p in sorted(paths)},
        'new_inference_attempts':8,'successful':8,'failed':0,'authorized_manifest_sha256':s.SHA,
        'next_proposal_sha256':s.sha256(P5),'next_proposal_authorized_requests':0,
        'model_sha256':s.MODEL_SHA,'backend_sha256':s.load(s.FROZEN)['model']['backend_sha256'],
        'tests':s.load(O/'targeted_regression_results_v1.json'),
        'json_files_parsed':checked_json,'csv_files_parsed':checked_csv,'git_diff_check':check.returncode,
        'historical_unchanged_except_log_append':True,'log_prefix_sha256':s.sha256(oldlog),
        'human_annotations_new':0,'source_provenance':'AI-assisted research and code; explicit scoped human inference authorization; no invented annotation adoption.',
        'self_hash_policy':'Hash this file externally; no self-referential digest.'}
    s.save(O/'reproducibility_manifest_v1.json',record)
    print(json.dumps({'artifacts':len(paths),'tests':record['tests']['stdout'].strip(),'reproducibility_sha256':s.sha256(O/'reproducibility_manifest_v1.json'),
                      'decision_packet_sha256':s.sha256(Path('docs/P1d_core_alignment_decision_packet_v1.md')),'historical':'PASS'}))

if __name__=='__main__':
    if sys.argv[1]=='prepare':observed_diagnostics();packet()
    elif sys.argv[1]=='tests':tests()
    elif sys.argv[1]=='log':verify_and_log()
    elif sys.argv[1]=='seal':seal()
    else:raise ValueError('Unknown non-generation action')
