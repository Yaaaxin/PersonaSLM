"""Run bounded regressions, append the truthful log, and seal new artifacts only."""
from pathlib import Path
import csv
import json
import re
import subprocess
import sys
import time
from datetime import datetime,timezone
import p1d_budget_calibration as b

F=Path('docs/validation/p1d/final_preparation_v1')
SEAL=F/'reproducibility_manifest_v1.json'
TESTLOG=Path('results/p1d_final_preparation/v1/regression_tests_v1.json')
LOG=Path('docs/research_development_log.md')

def now():return datetime.now(timezone.utc).isoformat()

def command(args):return subprocess.check_output(args,text=True,encoding='utf-8').strip()

def new_files():
    return [Path(p) for p in subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z']).decode().split('\0') if p]

def validate_files(paths):
    counts={'json':0,'csv':0,'markdown_local_links':0}
    for p in paths:
        if p.suffix=='.json':json.loads(p.read_text(encoding='utf-8-sig'));counts['json']+=1
        elif p.suffix=='.csv':
            with p.open(encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f);assert reader.fieldnames and len(set(reader.fieldnames))==len(reader.fieldnames),str(p)
                for row in reader:assert None not in row and all(v is not None for v in row.values()),str(p)
            counts['csv']+=1
        elif p.suffix=='.md':
            for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
                if '://' in link or link.startswith('#'):continue
                target=p.parent/link.split('#',1)[0]
                if target.resolve()==SEAL.resolve():continue # this final write follows link validation
                assert target.exists(),f'{p}: missing link {link}'
                counts['markdown_local_links']+=1
    return counts

def run():
    assert not SEAL.exists(),'Seal already exists; preserve the completed version'
    baseline=b.load(b.OUT/'historical_preservation_baseline_v1.json')
    assert command(['git','rev-parse','HEAD'])==baseline['head'],'HEAD changed during work'
    for path,h in baseline['tracked_sha256'].items():assert b.sha256(Path(path))==h,'Historical file changed before append: '+path
    original_log=LOG.read_bytes()
    engineering=b.load(b.OUT/'engineering_summary_v1.json')
    assert engineering['requests_attempted']==engineering['validated_results']==144 and engineering['failed_requests']==0
    audit=b.audit();assert audit==b.load(b.OUT/'measurement_v1/execution_integrity_v1.json')
    with Path('docs/validation/p1d/scientific_validation_v1/historical_budget_delivery_audit_v2.csv').open(encoding='utf-8-sig',newline='') as f:historical=list(csv.DictReader(f))
    assert len(historical)==264
    for row in historical:assert b.sha256(Path(row['raw_event']))==row['raw_event_sha256']
    # Only directly relevant P1d tests; no whole historical suite or generation.
    testfiles=sorted(str(p) for p in Path('tests').glob('test_p1d_*.py'))
    argv=[sys.executable,'-m','pytest','-q',*testfiles];start=now();timer=time.perf_counter()
    test=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8')
    record={'command':argv,'started_utc':start,'finished_utc':now(),'wall_seconds':time.perf_counter()-timer,
        'exit_code':test.returncode,'stdout':test.stdout,'stderr':test.stderr,'new_model_generations':0}
    testlog=TESTLOG
    if testlog.exists():
        attempt=2
        while TESTLOG.with_name(f'regression_tests_attempt_{attempt}.json').exists():attempt+=1
        testlog=TESTLOG.with_name(f'regression_tests_attempt_{attempt}.json')
    b.save(testlog,record)
    assert test.returncode==0,test.stdout+test.stderr
    count=re.search(r'(\d+) passed',test.stdout);assert count,'No passing-test summary';passed=int(count.group(1))
    numeric=subprocess.run([sys.executable,'tools/p1d_budget_analysis.py','--verify'],capture_output=True,text=True,encoding='utf-8')
    assert numeric.returncode==0,numeric.stdout+numeric.stderr
    validation=validate_files(new_files())
    diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stdout+diff.stderr
    at=now();entry=f'''

## P1d bounded CPU calibration and final preparation — recorded {at}

Maintainer: Yaxin ZHENG. This entry records actual software time, not a fabricated researcher review time. User authorization was limited to manifest `{b.MANIFEST_SHA}`, exactly eight previously inspected development cases × six cells × output caps 96/192/256. Registration retained the original proposal file and stored the explicit authorization separately. Main validation (1,728 Base plus 288 Instruct) remains unauthorized.

The complete run started at {engineering['started_utc']} and ended at {engineering['finished_utc'][-1]}. It completed 144/144 requests, no failures/retries, {engineering['generated_tokens']:,} generated tokens, {engineering['elapsed_seconds']/60:.2f} elapsed minutes. Pinned Qwen3.5-2B-Base Q4_K_M / llama.cpp b11573 CPU4/context4096/seed42/temperature0 settings were preserved. Full HTTP payloads, actual IDs, raw bytes, outputs, native stopping, latency and memory are retained. All 48 unique prompt token arrays passed live preflight; postflight and raw reconstruction passed. The lifetime server working-set peak was {engineering['peak_server_working_set_bytes']:,} bytes, not an isolated per-cap RAM measurement.

All semantic results remain 144 AI-assisted proposals with blank human decisions and explicit alternatives. They distinguish supported generic-policy claims, lack of any answer claim, speaker-attribution uncertainty, task delivery, component support, coherence and narrow style. Exact identical measurement inputs reuse documented assessments; no independent annotator or perfect blinding is claimed. None of the three budgets met the existing AI-provisional completion qualification. No main output policy was adopted. Paired budget estimates, eight-cluster sensitivity, LOSO, full distributions, unknown bounds and boundary views are reproducible; no main E/V effects selected a budget. Original raw and structural labels remain unchanged.

The 288 candidate cases and all 1,728 Base prompts remain unchanged. Exact derivations and dependency accounting were checked; 64 high-risk/stratified cases and 64 masked controls were prepared across 32 strata/all16 grammars. Human validity and neutral-control decisions remain pending, controls diagnostic, and shared templates limit new-template inference. Existing precision simulations were reused without resimulation. No test-case outputs were generated or used for tuning.

Offline official Instruct tokenizer validation covered 288 rendered prompts (1,965–2,083 tokens); shared native Base body IDs matched. Official tokenizer metadata was downloaded at its pinned revision; tokenizers 0.22.2 was isolated under ignored results. This is not a verified local Instruct GGUF/runtime: weights, quantization, native template/stop/RAM and actual latency remain open. No Instruct generation occurred.

Development-only algorithm work retained fair top-one random, lexical, BM25, time-filter and entity/time-filter baselines with uniform ties. Simple supplied-date filtering solved the curated selection target; no new algorithm gap was demonstrated. The prefix-locality adaptation added zero P1c ambiguous recoveries. Post-hoc heading cuts remain diagnostic, not human boundary truth. Published FPPS, LongMemEval temporal reordering, CoVe, RARR and constrained-generation work were compared with explicit transfer/compute limitations. A new 16-request current-user-marker/stop proposal was tokenized offline but remains separately unauthorized; it reuses existing original baselines and does not authorize the main cohort.

Executed tools: `p1d_budget_calibration.py register/preflight/run`, `p1d_budget_measurement.py historical-baseline/prepare`, `p1d_budget_review_groups.py`, `p1d_budget_analysis.py` and `--verify`, `p1d_budget_continuation_diagnostics.py`, `p1d_calibration_followup.py`, `p1d_fair_retrieval_baselines.py`, `p1d_tokenizer_metadata_check.py`, `p1d_instruct_tokenize_offline.py`, `p1d_research_updates.py`, `p1d_format_diagnostic_proposal.py`, `p1d_budget_reporting.py`, and this finalizer. Reports: `P1d_budget_calibration_engineering_report_v1.md`, `P1d_budget_calibration_scientific_report_v1.md`, `P1d_execution_readiness_packet_v3.md`; exact code/data/report files are listed in the new reproducibility manifest.

Validation: **{passed} relevant P1d tests passed** ({record['wall_seconds']:.2f} seconds wall time). Original tracked files and 264 P1b/P1c raw-event fingerprints matched; only this append changes the original log. Semantic/numerical reconstruction matched twice during analysis creation and again against saved files. No independent implementation claim is made. The final seal records JSON/CSV/link checks, source hashes, the actual command/output and Git state.

Offline failures/corrections were not model failures: Windows sandbox socket rejection for official metadata/dependency access was retried only after explicit tool approval; the first offline tokenizer body-field lookup and retrieval script path-type mismatch were corrected before successful artifacts; absent NumPy was resolved by standard-library deterministic sampling; native `limit` versus normalized `length` was corrected in the unexecuted analysis with regression coverage. An authored format fixture incorrectly assumed a trailing newline; inspection of actual frozen strings corrected the prospective-only adapter and added all144-tail coverage before any proposed prompts were written. These actions did not modify frozen scientific data. Any additional documented validation correction is retained in the corresponding report/test record.

Researcher checkpoint: adopt/correct the proposed semantic assessment and, separately if desired, authorize the exact16-request format diagnostic. Main-study execution remains NO-GO for task delivery, material/control adoption, template-scope resolution, independent measurement, local Instruct readiness and a final authorized execution manifest. PLOS ONE remains the first target; no publication readiness, independent validation or algorithmic originality is claimed. No commit, push, training or additional model inference occurred.
'''
    with LOG.open('ab') as f:f.write(entry.encode('utf-8'))
    assert LOG.read_bytes()[:len(original_log)]==original_log
    for path,h in baseline['tracked_sha256'].items():
        if path!=LOG.as_posix():assert b.sha256(Path(path))==h,path
    paths=set(new_files());paths.add(LOG)
    for root in (b.ROOT,Path('results/p1d_final_preparation/v1')):
        paths.update(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    # The installed tokenizer runtime is provenance only; no model weights are added.
    paths.discard(SEAL)
    links={p.as_posix():b.sha256(p) for p in sorted(paths) if p.is_file()}
    status=command(['git','status','--short']);diff=command(['git','diff','--check'])
    seal={'version':'p1d_bounded_calibration_and_final_preparation_v1','sealed_utc':now(),'head':baseline['head'],
        'initial_git_status':baseline['status'],'final_git_status_before_seal':status,'git_diff_check':diff,
        'authorization_manifest_sha256':b.MANIFEST_SHA,'attempted_generations':144,'successes':144,'failures':0,
        'main_validation_generations':0,'instruct_generations':0,'human_semantic_confirmations':0,
        'source_preservation':{'baseline_sha256':b.sha256(b.OUT/'historical_preservation_baseline_v1.json'),
            'unchanged_tracked_files_except_log_append':len(baseline['tracked_sha256'])-1,'historical_raw_events_verified':264,
            'log_original_bytes':len(original_log),'log_original_sha256':baseline['tracked_sha256'][LOG.as_posix()]},
        'tests':{'passed':passed,'record':testlog.as_posix(),'sha256':b.sha256(testlog),'suite':'Relevant P1d only; no full historical rerun'},
        'saved_analysis_reconstruction':numeric.stdout.strip(),'format_validation':validation,'artifact_sha256':links,
        'main_execution_decision':'NO_GO','new_format_diagnostic_authorized':False,
        'limits':'AI proposals require genuine human adoption; existing development outputs are not independent validation. No new original algorithm established.'}
    b.save(SEAL,seal);print(json.dumps({'tests_passed':passed,'sealed_files':len(links),'main_decision':'NO_GO','seal_sha256':b.sha256(SEAL)},indent=2))

if __name__=='__main__':run()
