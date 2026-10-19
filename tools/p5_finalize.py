"""Targeted regressions, append-only development log and chained preservation seal."""
import csv
import json
from pathlib import Path
import re
import subprocess
import sys
import p5_oracle_run as p

TARGETS=['tests/test_p5_oracle_run.py','tests/test_p5_oracle_measurement.py',
    'tests/test_core_sfh_readiness.py','tests/test_escp_kill_test.py',
    'tests/test_p5_oracle_proposal.py','tests/test_p1d_instruct_smoke.py',
    'tests/test_p1d_instruct_measurement.py','tests/test_personaslm_alignment.py',
    'tests/test_escp_offline.py','tests/test_response_status.py']

def main():
    out=p.OUT;baseline=p.load(out/'preservation_baseline_v1.json')
    p.require(not (out/'reproducibility_manifest_v1.json').exists(),'Sealed milestone; do not overwrite')
    previous=Path(baseline['previous_seal']);seal=p.load(previous)
    p.require(p.sha(previous)==baseline['previous_seal_sha256'],'Previous seal changed')
    previous_changed=[x for x,h in seal['artifact_sha256'].items() if p.sha(Path(x))!=h]
    tracked_changed=[x for x,h in baseline['tracked_sha256'].items() if p.sha(Path(x))!=h]
    p.require(not previous_changed and tracked_changed==[],'Historical source changed before append')
    cmd=[sys.executable,'-m','pytest','-q',*TARGETS]
    test=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
    p.save(out/'targeted_regression_v1.json',{'command':cmd,'returncode':test.returncode,'stdout':test.stdout,
        'stderr':test.stderr,'recorded_utc':p.b.utc_now(),'scope':'New runner/measurement/core/fidelity/ESCP plus directly used historical contracts; no broad historical rerun.'})
    p.require(test.returncode==0,'Regression failed; retained result, do not seal')
    reconstruction=subprocess.run([sys.executable,'tools/p5_oracle_measurement.py','--verify'],capture_output=True,text=True)
    p.require(reconstruction.returncode==0,'Measurement reconstruction failed: '+reconstruction.stderr)
    p.save(out/'analysis_reconstruction_v1.json',{'command':[sys.executable,'tools/p5_oracle_measurement.py','--verify'],
        'returncode':reconstruction.returncode,'stdout':reconstruction.stdout,'stderr':reconstruction.stderr,'new_inference':0})
    tests=int(re.search(r'(\d+) passed',test.stdout).group(1))
    corrections=[
        {'event':'Memory gate initially failed','outcome':'Zero inference before successful preflight; preserved failure_01 and failure_02. A further same-gate failure occurred before the successful check; no invented historic timestamp.'},
        {'event':'Diagnostic memory helper named a nonexistent function','outcome':'Read-only AttributeError; corrected call to existing memory_observation; no experiment changed.'},
        {'event':'First two core control-search grammars had no exact match','outcome':'Preparation stopped before tokenizer output/manifest generation; grammar expanded before first successful candidate. No frozen candidate or response modified.'},
        {'event':'Read-only lookup of a presumed regression filename failed','outcome':'Used actual test files and existing seal; no missing validation claimed.'},
        {'event':'OS process metadata access denied in sandbox','outcome':'Explicitly approved read-only inspection identified a different application. No access to its files and no process modification; researcher released memory.'},
    ]
    p.save(out/'development_corrections_v1.json',corrections)
    log=Path('docs/research_development_log.md');before=log.read_bytes()
    with (out/'research_development_log_before_v1.md').open('xb') as f:f.write(before)
    entry=f'''\n\n## {p.b.utc_now()} — P5 oracle diagnostic / core S/F/H readiness / P6 null comparison\n\nMaintainer: Yaxin ZHENG. AI-assisted execution, analysis and development; no new human semantic ratings.\n\nRegistered the latest explicit eight-request P5 authorization against the original p5 manifest, SHA {p.SHA}; the user-supplied p1d directory was a path typo resolved by exact content hash. The earlier eight Instruct requests were verified and not repeated. Memory preflight initially blocked execution; after researcher-released memory, the unchanged >=3 GiB gate and live token/binary checks passed. Exactly eight CPU requests completed, zero failures/retries, eight native EOS,329 output tokens. Mean latency6.0918 s; observed peak server working set2,384,363,520 bytes. All raw text/token IDs, HTTP bodies, journals and original eight AMBIGUOUS structural labels preserved.\n\nItem-specific AI proposals:8 complete supported tasks,14/14 components present/supported; historical full-ledger counterparts2/8 tasks,8/14 present,3/14 supported. Whole-speaker resampling sensitivity50–100 percentage points for the descriptive+75 pp difference; not population inference. Both evidence sets sufficient, reduced ledger reference-aware and answer-bearing; length/content/position/salience jointly change. No pure retrieval, sufficiency, reasoning or persona mechanism established. Main P1d remains NO-GO.\n\nPrepared exact80-request core development candidate (8 cases×C0–C7 plus two diagnostic controls), full E/question/reference fixed within case, native tokens1626–1849,16 matched pairs. SHA0cdb9146306faeddddba85b896acbf2d49899c9a01a5d5e28751b62d787d64ae. Zero candidate generations; separate authorization required. Added8 authored LF/BF construct challenges and separate blank panels; no independent human reliability claim. Reused existing288-case audit and64-case/control consequential review rather than restarting broad validation. Original candidate bank and approved E/V plan unchanged.\n\nP6 added16 adversarial typed cases and an equal-diagnostic-output simple rule comparator.16/16 exact matches; admission groups also identical. ESCP median8.398 microseconds versus5.273 for ordinary rules; no originality or model benefit demonstrated. Prior16 fixtures and all negative results retained. Revisited primary Zep/Mem0/FC-PS methods and ACL metadata; v8 novelty/opportunity records preserve overlap and implementation limitations.\n\nNew tools:p5_oracle_run,p5_oracle_measurement,core_sfh_readiness,persona_fidelity_distinction,escp_kill_test,p5_closeout,p5_finalize. Reports:P5_oracle_engineering_report_v1,P5_oracle_scientific_report_v1,PersonaSLM_core_SFH_measurement_readiness_v1,ESCP_prior_art_kill_test_v1,related_work_novelty_matrix_monitor_v8,P1d_P5_next_scientific_decision_packet_v1. Machine evidence under docs/validation/p5/oracle_diagnostic_v1,core_sfh_readiness_v1,p6/escp_kill_test_v1; raw run linked in engineering report.\n\nValidation:{tests} targeted tests passed; exact command/output retained in targeted_regression_v1.json. Offline measurement reconstruction passed. Initial implementation/preflight failures retained in development_corrections_v1.json; no failed generation was retried. Prior milestone artifacts and tracked files were byte-checked before this append; previous log saved and new seal records append-only lineage. No model training, main cohort, additional P6 inference, protocol replacement, Git commit/push or author-identity change.\n'''
    with log.open('ab') as f:f.write(entry.encode('utf-8'))
    p.require(log.read_bytes().startswith(before),'Log is not append-only')
    historical={'previous_seal_sha256':p.sha(previous),'previous_artifact_count':len(seal['artifact_sha256']),
        'tracked_file_count':len(baseline['tracked_sha256']),'changed_historical_sources':[],
        'allowed_append_only_log':log.as_posix(),'log_before_sha256':p.sha(out/'research_development_log_before_v1.md'),
        'previous_log_bytes_preserved':True,'new_model_generations':8,'prior_Instruct_regenerated':0,
        'P1d_main_generations':0,'algorithm_generations':0,'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
    p.save(out/'historical_preservation_v1.json',historical)
    roots=[out,Path('docs/validation/core_sfh_readiness_v1'),Path('docs/validation/p6/escp_kill_test_v1'),p.ROOT]
    files={x for root in roots for x in root.rglob('*') if x.is_file() and x.name!='.writer.lock'}
    files.update(Path(x) for x in ['docs/P5_oracle_engineering_report_v1.md','docs/P5_oracle_scientific_report_v1.md',
        'docs/PersonaSLM_core_SFH_measurement_readiness_v1.md','docs/ESCP_prior_art_kill_test_v1.md',
        'docs/related_work_novelty_matrix_monitor_v8.md','docs/P1d_P5_next_scientific_decision_packet_v1.md','docs/research_development_log.md'])
    files.update(Path('tools')/x for x in ['p5_oracle_run.py','p5_oracle_measurement.py','core_sfh_readiness.py',
        'persona_fidelity_distinction.py','escp_kill_test.py','p5_closeout.py','p5_finalize.py'])
    files.update(Path(x) for x in TARGETS[:4])
    schemas={'json_files':0,'csv_files':0}
    for file in files:
        if file.suffix=='.json':p.load(file);schemas['json_files']+=1
        if file.suffix=='.csv':
            with file.open(encoding='utf-8-sig',newline='') as f:
                rows=list(csv.DictReader(f));p.require(rows and all(None not in r for r in rows),'Malformed CSV '+str(file))
            schemas['csv_files']+=1
    diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True)
    p.require(diff.returncode==0,'Whitespace diff failure: '+diff.stdout+diff.stderr)
    final={'version':'p5_oracle_core_readiness_reproducibility_v1','recorded_utc':p.b.utc_now(),
        'maintainer':'Yaxin ZHENG','provenance':'Researcher-authorized execution; AI-assisted unconfirmed semantic assessment and offline development',
        'git_head':historical['git_head'],'git_status':subprocess.check_output(['git','status','--short'],text=True),
        'historical_preservation':historical,'schema_validation':schemas,'targeted_tests_passed':tests,
        'analysis_reconstruction':'PASS','git_diff_check':'PASS','authorized_manifest_sha256':p.SHA,
        'next_manifest_sha256':p.sha(Path('docs/validation/core_sfh_readiness_v1/core_sfh_manifest_proposed_v1.json')),
        'next_decision_packet_sha256':p.sha(Path('docs/P1d_P5_next_scientific_decision_packet_v1.md')),
        'artifact_sha256':{x.as_posix():p.sha(x) for x in sorted(files)}}
    p.save(out/'reproducibility_manifest_v1.json',final)
    print(json.dumps({'tests':tests,'artifacts':len(files),'schemas':schemas,'historical':'PASS','HEAD':historical['git_head'],
        'reproducibility_manifest_sha256':p.sha(out/'reproducibility_manifest_v1.json'),
        'next_packet_sha256':final['next_decision_packet_sha256']}))

if __name__=='__main__':main()
