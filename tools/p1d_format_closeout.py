"""Seal the completed diagnostic and offline preparation; never invokes inference."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/validation/p1d/format_calibration_v1'
FOLLOW = OUT / 'followup_v1'
INSTRUCT = ROOT / 'docs/validation/p1d/instruct_preparation_v3'
LOG = ROOT / 'docs/research_development_log.md'
SEAL = OUT / 'reproducibility_manifest_v1.json'
PACKET = ROOT / 'docs/P1d_next_scientific_decision_packet_v1.md'
HEAD = '4ac68b2d8ebeb9cd9b13ccdf79a081d0d4f0abf0'
FORMAT_SHA = '3f0e68b0fbe4cf5abfeab3bef9f6fbc39460b9219d118500ccc10d6fda121523'
SMOKE_SHA = 'ba63c30a9868b94b47f8f79dd774ac0627d56113810ffd4db08eb63af0374b91'


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def rel(path):
    return Path(path).relative_to(ROOT).as_posix()


def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write('\n')


def command(args):
    started = now()
    tick = time.perf_counter()
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            encoding='utf-8', errors='strict')
    record = dict(command=args, started_utc=started, finished_utc=now(),
                  elapsed_seconds=time.perf_counter()-tick, returncode=result.returncode,
                  stdout=result.stdout, stderr=result.stderr)
    return record


def binding(path):
    return {'path': rel(path), 'sha256': digest(path)}


def prepare():
    assert digest(OUT / 'frozen_manifest_v1.json') == FORMAT_SHA
    smoke = INSTRUCT / 'minimal_instruct_smoke_manifest_proposed_v1.json'
    assert digest(smoke) == SMOKE_SHA
    assert load(smoke)['authorized_requests'] == 0
    prior = ROOT / 'docs/validation/p1d/final_preparation_v1'
    methods = [
        dict(id='boundary', classification='KNOWN_ENGINEERING_APPROACH',
             observed_failure='All sixteen first replies are promises; actual stops suppress continuation without delivering requested components.',
             published_solution='Native EOG, conventional stops, role/fence parsing, official templates; generation-time grammar methods are distinct.',
             remaining_gap='Independent boundary truth and model/task adequacy, not a demonstrated need for another parser.',
             proposed_algorithm='No new parser; retain five existing extractors and actual-stop/offline-shadow comparisons.',
             computational_distinction='None established; exact stop shadows match eight actual stopped outputs.',
             fair_comparison='Same sixteen raw outputs; answer-loss and false-turn transitions; native/template alternatives need separately authorized inference.',
             falsification='If standard methods achieve independent boundary targets, reject the claimed new-parser need.',
             cpu_cost='Batch timings retained; Windows resolution causes some zero measurements; actual request latency is not isolated.',
             persona_cost='Cuts may remove useful style or quoted content; two authored fenced-role fixtures show premature cuts.',
             independent_test='Prospective human-adjudicated boundaries including quotes, headings, code fences and no-answer states.'),
        dict(id='answer_components', classification='ENGINEERING_ADAPTATION',
             observed_failure='Eight policy echoes can be factual Correct under the primary convention while all sixteen tasks fail.',
             published_solution='Structured answer checks; CoVe factored verification; RARR evidence research and editing.',
             remaining_gap='Whether a CPU-budgeted verifier improves delivered answers beyond simple component checks is untested.',
             proposed_algorithm='Candidate claim/date/component-state contract with abstention; no new generation-based implementation justified yet.',
             computational_distinction='None demonstrated beyond established structured verification.',
             fair_comparison='Exact component matching, existing metric contracts, compute-matched CoVe and fixed-ledger RARR adaptations.',
             falsification='Reject novelty or improvement if simple checks match it or answer/persona preservation worsens.',
             cpu_cost='Current objective checks are offline; future model-call and retrieval costs must be fully charged.',
             persona_cost='Editing may remove or flatten legitimate persona style.',
             independent_test='Independent complete-wrong, supported-partial, promise-only, quoted, negated and dated answers.'),
        dict(id='temporal_entity', classification='EXISTING_ESTABLISHED_METHOD',
             observed_failure='Prior entity/time errors motivate checks; this H_none diagnostic does not demonstrate stale-history selection.',
             published_solution='Time filtering, entity filtering, BM25 and LongMemEval time-aware expansion.',
             remaining_gap='Existing supplied-time+BM25 already solves sixteen curated development pools; free-text date attribution remains untested.',
             proposed_algorithm='Keep privileged metadata filtering as an oracle baseline; prospectively test uncertain temporal attribution separately.',
             computational_distinction='No original retrieval contribution established.',
             fair_comparison='Same top-one budget, extraction error counted, no oracle metadata for deployable methods.',
             falsification='No method gap if established extraction/retrieval matches the candidate on independent cases.',
             cpu_cost='Include temporal-query extraction, retrieval and reader calls, not just filtering.',
             persona_cost='Filtering current-only evidence can destroy useful historical information.',
             independent_test='Balanced current/historical questions, ambiguous dates, entity confusions and genuinely conflicting sources.'),
        dict(id='persona_evidence', classification='INCREMENTAL_CANDIDATE_UNVERIFIED',
             observed_failure='Past restricted package observations suggest a conflict question; new H_none outputs identify no unique persona-conflict mechanism.',
             published_solution='FPPS activation probing/steering, evidence-priority prompts and history removal.',
             remaining_gap='No fair local FPPS comparison or reproducible residual failure beyond those baselines.',
             proposed_algorithm='Typed evidence ownership is a hypothesis only until a surviving failure is isolated.',
             computational_distinction='None demonstrated; priority prompting must not be renamed FPPS.',
             fair_comparison='Equal cases/evidence, activation-compatible FPPS adaptation, history removal and style-preserving controls.',
             falsification='Reject if removal/priority baselines match performance or personalization is lost.',
             cpu_cost='FPPS requires detector training and activation access not provided by this completion diagnostic.',
             persona_cost='Must measure preserved useful personalization and style rather than reward deletion.',
             independent_test='Independent contradictions with separately measured factual reliability and persona fidelity.'),
        dict(id='memory_admission', classification='INCREMENTAL_CANDIDATE_UNVERIFIED',
             observed_failure='No memory-admission intervention is present in this H_none-only diagnostic.',
             published_solution='FC/PS admission, PN/CH presentation and query-relevance selection.',
             remaining_gap='CPU-efficient uncertain-source admission beyond these methods is not empirically established.',
             proposed_algorithm='Do not implement a new gate until a residual failure and exact rule distinction are specified.',
             computational_distinction='None established by recombining known filters.',
             fair_comparison='Budget-matched selection, identical admitted information where presentation varies, retained personalization.',
             falsification='Reject if published or simple admission gives the same tradeoff.',
             cpu_cost='Adjudication and selector calls must be included.',
             persona_cost='False exclusions erase valid preferences or historical persona facts.',
             independent_test='Prospective relevant/irrelevant and valid/historical information with explicit requested dates.'),
        dict(id='interaction_adaptation', classification='DEFERRED_UNSUPPORTED_HYPOTHESIS',
             observed_failure='P1c interactions were uncertain and boundary-sensitive; current design contains H_none only.',
             published_solution='Adaptive gating, steering and reranking are established families.',
             remaining_gap='No stable localized interaction has been independently demonstrated.',
             proposed_algorithm='No adaptive algorithm until the interaction and failure are replicated.',
             computational_distinction='Unspecified; do not claim novelty.',
             fair_comparison='Predeclared fixed rule versus established fixed baselines under equal computation.',
             falsification='No reproducible interaction or no benefit beyond fixed methods defeats the premise.',
             cpu_cost='Unmeasured; no additional inference authorized.',
             persona_cost='Adaptive suppression could erase legitimate persona expression.',
             independent_test='New independent cases and complete factorial coverage without using test outputs for rule tuning.')
    ]
    write(FOLLOW / 'algorithm_opportunity_registry_update_v6.json', {
        'version': 'p1d_algorithm_opportunity_update_v6', 'maintainer': 'Yaxin ZHENG',
        'provenance': 'AI-assisted scientific synthesis; not independent human adjudication',
        'parent': binding(prior / 'algorithm_opportunity_registry_update_v5.json'),
        'primary_source_review': binding(ROOT / 'docs/related_work_novelty_matrix_monitor_v6.md'),
        'new_original_algorithms': 0, 'entries': methods,
        'negative_findings_preserved': ['No first-answer gain from larger budgets in the prior 144 requests.',
             'No task-delivery gain from the current role-marker/stop diagnostic.',
             'No demonstrated retrieval gap on the existing privileged-metadata development pool.']})
    write(FOLLOW / 'related_work_monitor_delta_v7.json', {
        'version': 'related_work_monitor_delta_v7',
        'parent': binding(prior / 'related_work_monitor_delta_v6.json'),
        'methods_and_results_review': binding(ROOT / 'docs/related_work_novelty_matrix_monitor_v6.md'),
        'sources': [
            {'id':'10.18653/v1/2026.findings-acl.395','status':'PEER_REVIEWED_FINDINGS','method':'FPPS','url':'https://aclanthology.org/2026.findings-acl.395.pdf'},
            {'id':'2410.10813v2','status':'ICLR_2025','method':'LongMemEval','url':'https://arxiv.org/html/2410.10813v2'},
            {'id':'10.18653/v1/2024.findings-acl.212','status':'PEER_REVIEWED_FINDINGS','method':'Chain-of-Verification','url':'https://aclanthology.org/2024.findings-acl.212.pdf'},
            {'id':'10.18653/v1/2023.acl-long.910','status':'PEER_REVIEWED_ACL','method':'RARR','url':'https://aclanthology.org/2023.acl-long.910.pdf'},
            {'id':'2610.11188v1','status':'PREPRINT_NOT_VERIFIED_PEER_REVIEWED','method':'FC/PS admission and PN/CH presentation','url':'https://arxiv.org/html/2610.11188v1'}],
        'no_claim_of_local_published_method_replication': True,
        'unmodified_other_papers': 'Inherited prior matrices retain Persistent Personas?, TwinVoice, Wiki-Talkie and Decoupling Logic from Persona.'})
    write(OUT / 'next_decision_specification_v1.json', {
        'version':'p1d_next_decision_specification_v1', 'packet':binding(PACKET),
        'current_main_decision':'NO_GO', 'prospective_smoke':binding(smoke),
        'recommended_decision':'AUTHORIZE_8_INSTRUCT_DEVELOPMENT_REQUESTS_WITH_DOCUMENTED_LIMITATIONS',
        'alternative_decision':'DEFER_INSTRUCT_GENERATION', 'researcher_decision':None,
        'researcher_decision_timestamp':None, 'authorized_new_requests':0,
        'consequence':'At most eight listed development requests after exact preflight; no main-cohort authorization or model-policy adoption.',
        'material_risk':'Conversion lineage partially verified; tensor execution, memory and native EOG untested.',
        'current_primary_plan_unchanged':{'speakers':144,'cases':288,'base_requests':1728,'instruct_requests':288},
        'conditional_future_amendment_not_adopted':'Instruct primary six-condition design only after adequate development measurement; separate limited/deferred Base comparison; exact estimands/configuration and prospective approval required.'})


def preserve():
    base = load(OUT / 'historical_preservation_baseline_v1.json')
    assert base['head'] == HEAD
    assert command(['git','rev-parse','HEAD'])['stdout'].strip() == HEAD
    # Git normalizes text line endings; the initial baseline binds local bytes.
    # Preserve those exact bytes before the sole authorized append.
    snapshot=OUT/'source_snapshots/research_development_log.md.before'
    if not snapshot.exists():
        assert digest(LOG)==base['tracked_sha256'][rel(LOG)]
        snapshot.parent.mkdir(parents=True,exist_ok=True)
        with snapshot.open('xb') as handle:
            handle.write(LOG.read_bytes())
    old_log=snapshot.read_bytes()
    assert hashlib.sha256(old_log).hexdigest() == base['tracked_sha256'][rel(LOG)]
    assert LOG.read_bytes().startswith(old_log), 'Historical development log changed beyond append'
    changed=[]
    for path,expected in base['tracked_sha256'].items():
        if path == rel(LOG):
            continue
        if not (ROOT/path).is_file() or digest(ROOT/path) != expected:
            changed.append(path)
    old_seal = ROOT / 'docs/validation/p1d/final_preparation_v1/reproducibility_manifest_v1.json'
    prior = load(old_seal)
    old_changed=[]
    for path,expected in prior['artifact_sha256'].items():
        if path == rel(LOG):
            assert hashlib.sha256(old_log).hexdigest() == expected
            continue
        if not (ROOT/path).is_file() or digest(ROOT/path) != expected:
            old_changed.append(path)
    assert not changed and not old_changed, (changed,old_changed)
    return {'tracked_source_files':len(base['tracked_sha256']), 'changed_except_append_log':changed,
            'previous_seal':binding(old_seal), 'previous_seal_artifacts':len(prior['artifact_sha256']),
            'previous_artifact_changes_except_append_log':old_changed,
            'log_original_bytes':len(old_log), 'log_original_sha256':hashlib.sha256(old_log).hexdigest(),
            'log_original_prefix_preserved':True}


def seal():
    assert not SEAL.exists(), 'Existing seal is immutable; use --verify'
    preservation = preserve()
    tests = command([sys.executable,'-m','pytest','-q',
        'tests/test_p1d_format_calibration.py','tests/test_p1d_format_analysis.py',
        'tests/test_p1d_instruct_preparation_v3.py','tests/test_p1d_format_diagnostic.py',
        'tests/test_inference.py','tests/test_response_status.py'])
    write(OUT/'targeted_regression_results_v1.json',tests)
    assert tests['returncode']==0,tests
    reconstruction=[]
    for index in range(2):
        result=command([sys.executable,'tools/p1d_format_analysis.py','--verify'])
        reconstruction.append(result)
        assert result['returncode']==0,result
    write(OUT/'analysis_reconstruction_results_v1.json',reconstruction)
    error_history = {
        'inference_failures':0,
        'closeout_script_preflight':'An unterminated multiline f-string caused SyntaxError before any execution; corrected and py_compile passed. No source data or log was changed by the failed invocation.',
        'historical_log_byte_check':'Git-normalized line endings differ from the initial local-byte baseline. Preserve the exact pre-append working-tree log only after its baseline hash matches; verify subsequent prefix bytes. No historical-content change was detected.',
        'link_check_invocation':'An inline PowerShell/Python quoting attempt failed before execution; a literal here-string read-only check succeeded with zero broken links.',
        'initial_analysis_verification':'Python tuple versus JSON array comparison failed; canonical JSON comparison fixed verification only; original assembly code retained.',
        'initial_expanded_regression':'1 failed, 50 passed: CSV nested-object key order comparison was too strict; test now compares decoded objects and preserves legacy tuple notation in CSV bounds.',
        'network':'Initial sandbox access returned WinError 10013; public metadata/artifact requests were rerun only after tool-level approval.',
        'no_numerical_or_annotation_revision':True,
        'csv_format_note':'Nested CSV cells are JSON except legacy paired bounds rendered as Python tuple text. Canonical JSON tables are authoritative; tests compare decoded values.'}
    write(OUT/'verification_corrections_v1.json',error_history)
    stamp=now()
    entry=f'''\n\n## P1d authorized format diagnostic and offline Instruct preparation\n\nSoftware record time: {stamp}. Maintainer: Yaxin ZHENG. Human authorization time was not supplied.\n\nThe explicitly authorized format manifest ({FORMAT_SHA}) passed exact preflight. Exactly 16 Base CPU completions ran from 2026-10-14T14:52:02.926603+00:00 to 2026-10-14T14:58:52.382147+00:00; all succeeded, no retry, no extra inference. The pinned Qwen3.5-2B-Base Q4_K_M / llama.cpp b11573, CPU4, context4096, seed42, greedy settings and 96-token cap were preserved. Both new arms add the current-question User marker; only the registered stop lists differ within the pair. Raw HTTP bytes, prompts, token IDs, effective settings, ordered events and memory observations are retained.\n\nNo-stop: eight CROSS_TURN/limit outputs, 768 generated tokens. Stops: eight frozen AMBIGUOUS/word-stop outputs, 154 tokens. Every first span is identifiable; stopped AMBIGUOUS means bounded semantics are uncertified, not an unavailable boundary. First-answer content is identical after whitespace normalization in all eight pairs. All sixteen AI proposals are incomplete promises with zero required components; none is human-confirmed. Supported generic-policy echoes explain eight factual Correct proposals despite task Failure; alternative Unverifiable scope remains explicit. No metric, historical classification or approved estimand was altered.\n\nObserved mean latency was 28.336s without stops and 21.819s with stops; concurrent non-generation preparation prevents isolated performance claims. Process lifetime peak working set was 2610135040 bytes. Eight purposive case/speaker pairs, whole-speaker sensitivity, leave-one-out results, category/unknown distinctions and exact historical-ID comparisons are retained. No independent replication or pure persona mechanism is claimed. The previous 144 budget outputs/AI proposals remain unchanged.\n\nNew work: tools/p1d_format_calibration.py, tools/p1d_format_analysis.py, tools/p1d_format_followup.py, tools/p1d_format_reports.py and tools/p1d_format_closeout.py; three focused regression modules; versioned engineering/scientific/readiness/material/algorithm/novelty/decision reports; docs/validation/p1d/format_calibration_v1 and instruct_preparation_v3. Prior historical files were verified against 1190 tracked hashes and the previous 1278-artifact seal; only this log is appended.\n\nPublic Instruct metadata and one pinned 1270808032-byte GGUF were downloaded through approved tool permissions. Local hash, official shared token IDs/merges and eight b11573 vocabulary-only prompt arrays match. No Instruct server, warmup or generation ran. Conversion lineage remains partially verified: distributor build b8185 is reported, exact source revision/conversion recipe is not. The prepared eight-request H_none smoke manifest ({SMOKE_SHA}) is UNAUTHORIZED. The 1728+288 independent cohort remains NO-GO and unchanged.\n\nOffline conventional stop shadows reproduce all eight stopped texts; two authored fenced-role fixtures show false cuts. No independent boundary accuracy or original algorithm is claimed. LongMemEval, FPPS, CoVe, RARR and FC/PS admission remain required published baselines; current evidence does not justify relabeling filters, checks or stops as innovation. Candidate materials retain 288 AI VALID_WITH_LIMITATIONS judgments and diagnostic controls; 16 templates/four ancestors limit linguistic independence. Existing simulations were not rerun. The existing manuscript Methods working text remains applicable; current negative configuration findings are documented without prospective validation claims.\n\nCommands: `.venv/Scripts/python.exe tools/p1d_format_calibration.py run --preflight docs/validation/p1d/format_calibration_v1/preflight_v1.json` (executed once; do not repeat); readonly `audit`; `.venv/Scripts/python.exe tools/p1d_format_analysis.py --verify`; metadata/artifact/tokenizer preparation scripts; scoped pytest command in targeted_regression_results_v1.json; `git diff --check`. Final targeted result: {tests['stdout'].strip()}. Two independent reconstruction calls agreed. Initial verification defects (tuple/array representation and nested CSV key order) were corrected without data/rating changes; initial 1-failed/50-passed regression is disclosed in verification_corrections_v1.json. Network WinError10013 was resolved through approved escalation, not bypass.\n\nImmediate gate: one exact eight-request Instruct feasibility authorization, accepting documented partial conversion lineage or deferring. Passing it would not authorize main validation or replace the primary model. Scientific semantic adoption, material/control validity, independent measurement and any substantive model-policy amendment remain genuinely pending. No commit, push, training or other cohort execution occurred.\n'''
    with LOG.open('ab') as handle:
        handle.write(entry.encode('utf-8'))
    preservation=preserve()
    candidates=[ROOT/p for p in subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()]
    candidates += [LOG]
    run=ROOT/load(OUT/'engineering_summary_v1.json')['run_directory']
    candidates += [p for p in run.rglob('*') if p.is_file()]
    candidates += [p for p in (ROOT/'results/p1d_instruct_preparation/v3/native_tokenizer').rglob('*') if p.is_file()]
    files=sorted(set(p for p in candidates if p.is_file() and p!=SEAL),key=lambda p:rel(p))
    counts={'json':0,'jsonl':0,'csv':0}
    broken_links=[]
    for p in files:
        if p.suffix=='.json':
            load(p); counts['json']+=1
        elif p.suffix=='.jsonl':
            for line in p.read_text(encoding='utf-8').splitlines():
                if line.strip():json.loads(line)
            counts['jsonl']+=1
        elif p.suffix=='.csv':
            with p.open(encoding='utf-8',newline='') as handle:
                rows=list(csv.reader(handle))
            assert rows and all(len(r)==len(rows[0]) for r in rows),rel(p)
            counts['csv']+=1
        elif p.suffix=='.md' and p.parent==ROOT/'docs':
            for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
                if '://' in target or target.startswith('#'):continue
                destination=p.parent/target.split('#')[0]
                if destination.resolve()==SEAL.resolve():continue
                if not destination.exists():broken_links.append({'source':rel(p),'target':target})
    assert not broken_links,broken_links
    diff=command(['git','diff','--check'])
    assert diff['returncode']==0,diff
    artifact={rel(p):digest(p) for p in files}
    write(SEAL,{
        'version':'p1d_format_calibration_reproducibility_v1','sealed_utc':now(), 'head':HEAD,
        'attempted_generations':16,'successes':16,'failures':0,'retries':0,
        'new_instruct_generations':0,'new_main_validation_generations':0,'human_semantic_confirmations':0,
        'main_execution_decision':'NO_GO','format_manifest_sha256':FORMAT_SHA,
        'unauthorized_smoke_manifest_sha256':SMOKE_SHA,
        'source_preservation':preservation,'format_validation':counts,'broken_local_links':broken_links,
        'tests':binding(OUT/'targeted_regression_results_v1.json'),
        'analysis_reconstruction':binding(OUT/'analysis_reconstruction_results_v1.json'),
        'software_errors_and_corrections':binding(OUT/'verification_corrections_v1.json'),
        'model_backend_identity_source':binding(OUT/'preflight_v1.json'),
        'instruct_candidate_identity_source':binding(INSTRUCT/'candidate_download_v1.json'),
        'git_diff_check':diff,'git_status_before_seal':command(['git','status','--short'])['stdout'],
        'model_weights_ignored':command(['git','check-ignore','models/gguf/instruct_candidates/lmstudio-bb84e113/Qwen3.5-2B-Q4_K_M.gguf'])['returncode']==0,
        'artifact_sha256':artifact})
    print(json.dumps({'seal':rel(SEAL),'sha256':digest(SEAL),'artifacts':len(artifact),'tests':tests['stdout'].strip()},indent=2))


def verify():
    data=load(SEAL)
    changed=[path for path,h in data['artifact_sha256'].items() if not (ROOT/path).is_file() or digest(ROOT/path)!=h]
    assert not changed,changed
    preserve()
    assert digest(OUT/'frozen_manifest_v1.json')==FORMAT_SHA
    assert digest(INSTRUCT/'minimal_instruct_smoke_manifest_proposed_v1.json')==SMOKE_SHA
    print(json.dumps({'verified_artifacts':len(data['artifact_sha256']),'historical_integrity':'PASS','seal_sha256':digest(SEAL)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','seal','verify'])
    args=parser.parse_args()
    {'prepare':prepare,'seal':seal,'verify':verify}[args.action]()
