"""Read-only historical verification and additive delivery records; no inference."""
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

import p1b_confirmed_analysis as a
from personaslm.journal import read_events, utc_now

REPORT_NAMES = [
    'researcher_confirmed_annotation_report', 'exploratory_factorial_analysis',
    'factual_temporal_error_analysis', 'task_completion_analysis',
    'structural_semantic_analysis', 'scientific_novelty_assessment',
    'algorithmic_opportunity_assessment', 'publication_readiness',
    'next_experiment_decision']
REPORTS = [Path('docs/P1b_'+name+'.md') for name in REPORT_NAMES]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def verify():
    baseline=a.core.load(a.LOCAL/'baseline.json')
    changed=[p for p,h in baseline['files'].items() if not Path(p).is_file() or a.digest(p)!=h]
    allowed={'docs/research_development_log.md','docs/P1b_algorithmic_opportunity_assessment.md'}
    check(not set(changed)-allowed, 'Historical source changed: '+str(changed))
    for path,snapshot in [('docs/research_development_log.md','development_log_before.bin'),
                          ('docs/P1b_algorithmic_opportunity_assessment.md','P1b_algorithmic_opportunity_assessment_before.bin')]:
        check(Path(path).read_bytes().startswith((a.LOCAL/snapshot).read_bytes()),'History rewritten: '+path)
    check(a.prior.git_state()['sha']==baseline['git_sha'],'Git HEAD changed')
    older=a.core.load(Path('results/p1b_execution/v1/baseline.json'))
    for p,h in older['historical_local_files'].items():
        check(a.digest(p)==h, 'Prior local artifact changed: '+p)
    inventory=a.core.load(a.prior.OLD/'execution_inventory_v1.json')
    for p,h in inventory['run_artifact_hashes'].items():
        check(a.digest(p)==h,'Original calibration artifact changed: '+p)
    check(a.core.source_inventory()==older['previous_source_hashes'],'Inference sources changed')
    frozen=a.core.load(Path('docs/validation/p1b/calibration_v1/final_integrity_v1.json'))
    journals=[]; wave1=[]
    for item in frozen['journal_chains_verified']:
        path=Path(item['directory']);events=read_events(path)
        check(a.digest(path/'manifest.json')==item['manifest_sha256'] and len(events)==item['events']
              and events[-1]['event_hash']==item['terminal_hash'],'Historical journal differs: '+str(path))
        journals.append({'directory':path.as_posix(),'events':len(events),
                         'terminal_hash':events[-1]['event_hash'],'original_terminal_status':item['terminal_status']})
        if path.as_posix().startswith('results/p1_wave1/development_v1/runs/'):
            wave1.extend(e['data']['evaluation']['response_completeness'] for e in events if e['kind']=='p1_result')
    reviewed=a.core.csv_records(Path('docs/validation/p1/output_human_review_researcher_verified_v1.csv'))
    check(len(wave1)==96 and Counter((b['raw_sha256'],b['first_span']['sha256'],b['status']) for b in wave1)
          ==Counter((r['raw_sha256'],r['first_reply_sha256'],r['structural_status']) for r in reviewed),
          'Wave 1 native/annotation mapping changed')
    rows,spec=a.load_registered()
    check(len(rows)==192 and len({r['anonymous_response_id'] for r in rows})==192,'Response IDs differ')
    check(set(Counter(r['case_id'] for r in rows).values())=={8},'Eight-cell case count differs')
    check(len({r['case_id'] for r in rows})==24 and len({r['persona_id'] for r in rows})==12,'Units differ')
    check(set(Counter(r['persona_id'] for r in rows).values())=={16},'Speaker clustering differs')
    for case in {r['case_id'] for r in rows}:
        check({r['condition'] for r in rows if r['case_id']==case}=={'C'+str(i) for i in range(8)},'Factorial cells differ')
    check(Counter(r['structural_status'] for r in rows)=={'CROSS_TURN':186,'TRUNCATED':5,'AMBIGUOUS':1},'Frozen structure differs')
    check(sum(r['applicable_temporal_consistency']=='true' for r in rows)==88,'Temporal denominator differs')
    first=a.PUBLIC/'analysis_v1';second=a.LOCAL/'replay_v1'
    replay={}
    for folder in (first,second):
        manifest=a.core.load(folder/'analysis_reproducibility_manifest_v1.json')
        for name,h in manifest['files'].items():
            check(a.digest(folder/name)==h,'Analysis artifact changed: '+str(folder/name))
    for name,h in a.core.load(first/'analysis_reproducibility_manifest_v1.json')['files'].items():
        check(a.digest(second/name)==h,'Numerical replay mismatch: '+name)
        replay[name]=h
    result=a.core.load(first/'analysis_v1.json')
    group=next(g for g in result['group_summaries'] if g['group_type']=='ALL')
    check(group['factual_consistency']==dict(Counter(r['confirmed_factual_consistency'] for r in rows)),'Factual summary differs')
    check(group['temporal_consistency']==dict(Counter(r['confirmed_temporal_consistency'] for r in rows)),'Temporal summary differs')
    check(group['task_success']==110,'Task success count differs')
    check(spec['weights']==a.prior.contrast_weights() and spec['bootstrap_seed']==714005,'Statistical specification differs')
    check(sum(x['count'] for x in result['joint_table'])==192,'Joint denominator differs')
    for field in ('semantic_completeness','answer_delivery','factual_consistency','temporal_consistency'):
        check(sum(x['count'] for x in result['structural_semantic_crosstabs'] if x['axis']==field)==192,'Cross-table denominator differs')
    check(subprocess.run(['git','check-ignore','--quiet','results/p1b_measurement_audit/v1/protected/treatment_mapping_v1.json']).returncode==0,
          'Original treatment mapping is no longer ignored')
    return {'version':'p1b_confirmed_delivery_integrity_v1','verified_utc':utc_now(),
            'baseline_git_sha':baseline['git_sha'],'baseline_files':len(baseline['files']),
            'allowed_append_only_changes':changed,'prior_local_files_preserved':len(older['historical_local_files']),
            'calibration_files_preserved':len(inventory['run_artifact_hashes']),
            'historical_journals':journals,'wave1_native_review_records_verified':96,
            'registered_annotations':192,'cases':24,'speakers':12,'frozen_prompts_verified':192,
            'frozen_structure':dict(Counter(r['structural_status'] for r in rows)),
            'metric_applicability':{axis:sum(r['applicable_'+axis]=='true' for r in rows) for axis in a.core.AXES},
            'two_reconstructions_byte_identical':replay,'bootstrap_seed':714005,'bootstrap_replicates':10000,
            'analysis_source_hash':a.digest(Path(a.__file__)),'no_new_inference':True,
            'no_annotation_or_historical_output_overwrite':True,'status':'PASS'}


def main():
    check(not (a.PUBLIC/'delivery_v1.json').exists(),'Refuse to overwrite delivery')
    integrity=verify()
    # Clarify a misleading metadata field without changing frozen registration inputs.
    a.atomic_json(a.PUBLIC/'annotation_provenance_clarification_v2.json',{
        'version':'p1b_annotation_provenance_clarification_v2','recorded_utc':utc_now(),
        'original_record':'researcher_confirmation_v1.json',
        'original_sha256':a.digest(a.PUBLIC/'researcher_confirmation_v1.json'),
        'superseded_field':'independent_human_annotators','original_value':1,
        'independent_human_annotators':None,'number_of_distinct_named_human_reviewers':1,
        'independent_annotation_reliability':'Not established',
        'explanation':'The original field counted the named confirming researcher but its name could imply independent annotation. Independence from AI proposals or prior knowledge is not established. No independent second reviewer or agreement measurement exists.',
        **a.PROVENANCE,'human_review_timestamp':None,'inter_annotator_agreement':None,
        'rating_changes':0,'source_or_registration_overwritten':False,
        'confirmation_scope':'All 192 supplied semantic proposals; no fabricated Stage B boundary judgments'})
    literature=[
        ('Principled Personas','https://aclanthology.org/2025.emnlp-main.1364/'),
        ('When Personalization Misleads','https://aclanthology.org/2026.findings-acl.395/'),
        ('One Persona, Many Cues','https://aclanthology.org/2026.acl-long.2079/'),
        ('What to Admit and How to Present','https://arxiv.org/abs/2610.11188v1'),
        ('Decoupling Logic from Persona','https://arxiv.org/abs/2610.09772v2'),
        ('Wiki-Talkie','https://arxiv.org/abs/2610.08513v1'),
        ('TwinVoice','https://aclanthology.org/2026.findings-acl.981/'),
        ('Persistent Personas?','https://aclanthology.org/2026.eacl-long.246/'),
        ('LongMemEval','https://arxiv.org/abs/2410.10813v2'),
        ('AlignScore','https://aclanthology.org/2023.acl-long.634/'),
        ('PLOS ONE publication criteria','https://journals.plos.org/plosone/s/criteria-for-publication')]
    a.atomic_json(a.PUBLIC/'literature_access_v1.json',{'recorded_utc':utc_now(),
        'access_scope':'Primary metadata/abstract pages and official journal criteria were browsed in this task. No method/code was reproduced; no exhaustive novelty review claimed.',
        'exact_per_page_access_timestamp':None,
        'sources':[{'title_key':title,'url':url} for title,url in literature],
        'new_algorithm_originality':'UNVERIFIED; none claimed'})
    captures={p.name:a.core.load(p) for p in sorted((a.LOCAL/'engineering').glob('*.json'))}
    a.atomic_json(a.PUBLIC/'command_register_v1.json',{'version':'p1b_confirmed_commands_v1',
        'recorded_utc':utc_now(),'captures':captures,
        'additional_actual_read_only_commands':['git status --short','git rev-parse HEAD',
            'Get-Content -LiteralPath AGENTS.md','Get-Content -LiteralPath tools/p1b_measurement_verify.py -TotalCount 240'],
        'read_only_inspections':'Repository documents, source, inventories and case-level JSON/CSV were inspected with Get-Content, rg and project Python; no unrecorded inference is implied.',
        'editorial_corrections':a.core.load(a.LOCAL/'editorial_finalize_record_v1.json'),
        'previous_editorial_record':a.core.load(a.LOCAL/'editorial_record_v1.json'),
        'delivery_command':['.\\.venv\\Scripts\\python.exe','tools/p1b_confirmed_delivery.py'],
        'delivery_capture':'results/p1b_confirmed_analysis/v1/engineering/delivery_01.json',
        'timestamp_limit':'Recorded engine times are actual; unavailable historical error/review times are null, not inferred.'})
    test=captures['full_tests_01.json']
    check(test['exit_code']==0 and '712 passed in 40.41s' in test['stdout'],'Unexpected full test result')
    log=Path('docs/research_development_log.md')
    entry=f'''

## P1b researcher-confirmed semantic registration and exploratory factorial analysis

Recorded UTC: {utc_now()}. Research maintainer: Yaxin ZHENG. Formal Protocol v1.1 and prospective v1.2 remain unchanged. Task-entry HEAD `{integrity['baseline_git_sha']}` was clean. No new generation, server launch, tokenizer call, training, further wave, commit or push occurred.

### Scope, implementation and truthful review provenance

The researcher explicitly confirmed the complete 192-row AI-assisted proposal set. Preserved its UNCONFIRMED filename and every source field; registered a separate masked CSV with appended confirmed values and researcher-authority provenance. All 35 master fields match across 192 aliases, 24 eight-cell cases and 12 synthetic speakers. Source explanations, uncertainties and quotations retain AI-assisted origin. No review time, second reviewer, independent blind annotation or agreement is invented. The source's original blank human fields remain blank, while authoritative appended decisions are complete.

The existing two-stage importer remains unchanged. A separately versioned semantic-adoption adapter handles the actual approved 48-column proposals without fabricating missing structural judgments or reducing PARTIAL to a binary code. BR168 remains AMBIGUOUS: conservative numerical analysis treats it as unknown; confirmed-span sensitivity uses the adopted labels on the original span. No parser or old policy was changed. A provenance clarification corrects the interpretation of the newly written `independent_human_annotators: 1` metadata: one named confirming human does not establish independent annotation. Original registration bytes and ratings are retained; the additive clarification supersedes only that field interpretation.

### Actual measurements and analysis specification

Factual labels: 137 Correct, 34 Incorrect, 21 Unverifiable out of 192. Temporal: 40 Correct, 34 Incorrect, 14 Unverifiable out of 88, with 104 frozen N/A. All 34 factual and temporal errors overlap. Delivery: 110 FULL_ANSWER, 33 WRONG_ANSWER_DELIVERED, 27 PARTIAL_ANSWER, one PARTIAL_WITH_FALSE_CLAIM, 21 NO_FINAL_ANSWER. Completeness: 143 YES, 28 PARTIAL, 21 NO. All labels were adopted unchanged, not fitted to the expected summary. Relevance scores 1-5: 4/14/31/0/143; coherence: 0/4/1/18/169. No missing confirmed semantic labels.

Annotation/specification snapshots preceded the new treatment join. Version `p1b_confirmed_factorial_v2` is explicitly post-output exploratory analysis, not preregistration. It retains C1-C0, C3-C0, average S/F/H, averaged pairwise difference-in-differences and SxFxH with exact weights. Whole-speaker bootstrap uses seed714005 and10000 draws; 24 paired cases/12 speakers, temporal11 cases/nine eligible speakers. It preserves all categories, eligible denominators, case-level values, unknown bounds, leave-one-speaker-out diagnostics and ordinal thresholds. No C0-correct filter, missing-to-wrong conversion, pooled reliability score or neutral-adjusted contrast is used.

The full adopted-span task-success simple contrasts are -1/24 and -3/24; the average H contrast is -0.1875. Conservative counterparts use 23 evaluable cases, with all24 retained for bounds. Temporal SxH averages zero but four opposing case contributions remain visible. These are small purposive-sample development observations, not population significance or an isolated mechanism. D has24 supported-claim judgments but only4 full answers; A remains24/24 full. Thirty-four contradictions are concentrated in seven cases; four already occur at C0.

### Commands, tests, failures and corrections

Executed `.\\.venv\\Scripts\\python.exe tools/p1b_confirmed_analysis.py register`, then `analyze --output docs/validation/p1b/confirmed_analysis_v1/analysis_v1`, followed by `analyze --output results/p1b_confirmed_analysis/v1/replay_v1`. All exited0. The ten numerical/data artifacts are byte-identical across both reconstructions; actual runtime manifests preserve their separate engineering timestamps. `tools/p1b_confirmed_report.py` generated the report drafts. The saved editorial helper corrected spacing and identified H_L2, not H_L3, as the case with eight nonanswers by checking the frozen case table; data/labels were unchanged.

Targeted `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_p1b_confirmed_analysis.py`:24 passed. Full `.\\.venv\\Scripts\\python.exe -m pytest -q`:712 passed,0 failed,0 reported warnings,40.41s pytest time,exit0; captured process duration {test['duration_seconds']} seconds. Tests cover immutable fields, categorical applicability, exact adoption, component/delivery distinctions, boundary uncertainty, contrast weights, clustering, overwrite rejection and ordinal sensitivity. No tests were weakened.

A documentation patch containing delete/add operations on the same path was rejected before mutation; it was corrected with an explicit update. A read-only rg command used a literal Windows wildcard path and exited1/os error123; explicit file lists corrected the inspection. Initial generated prose had spacing artifacts and one wrong H-family prose case label; corrected against the immutable analysis, with draft hashes preserved. Original error times were not captured and are not invented. These engineering errors did not alter experimental data. [Command register](validation/p1b/confirmed_analysis_v1/command_register_v1.json) preserves actual captured argv, UTC, exit status, output and corrections.

### Preservation, scientific limits and deliverables

Verified458 task-entry repository files with only append-only historical report/log updates,3967 older local artifact hashes,1831 calibration artifact hashes,29 journal chains and96 Wave1 native/review records. Current local model/backend file hashes and saved native tokenizer IDs reconcile; no new live inference observation is claimed. All192 prompts and masked text/applicability mappings reconstruct. Original protocols, outputs, reviews, source snapshots and failed/interrupted run statuses remain intact.

New tools: `tools/p1b_confirmed_analysis.py`, `tools/p1b_confirmed_report.py`, `tools/p1b_confirmed_delivery.py`; tests: `tests/test_p1b_confirmed_analysis.py`. Eight new methodological reports cover registration, factorial/error/task/structural analyses, novelty, publication readiness and next steps. The existing algorithmic opportunity report receives only an addendum. [Delivery inventory](validation/p1b/confirmed_analysis_v1/delivery_v1.json) indexes exact files, final hashes and validation results.

Neutral controls remain OPEN and absent from these contrasts. An independent annotation subset and BR168 unit review are recommended before broad inference. The next inference proposal is a separately authorized relevance/temporal-status diagnostic on independent material; no algorithm is implemented. Existing personalization, memory selection and separation methods overlap the prospective ideas. Primary literature was checked at metadata/abstract scope, with no originality guarantee. Twelve purposive clusters, AI-assisted single-authority labels, unmeasured fidelity, style/speaker nesting, task/history confounding, output censoring and no independent/model/external validation limit PLOS ONE readiness. Reports do not claim the development study is submission-ready or that publication is assured.
'''
    with log.open('ab') as f:f.write(entry.encode('utf-8'))
    # Preserve this task's final source bytes separately from experiment journals.
    snapshots={}
    for name in ['tools/p1b_confirmed_analysis.py','tools/p1b_confirmed_report.py',
                 'tools/p1b_confirmed_delivery.py','tests/test_p1b_confirmed_analysis.py']:
        target=a.LOCAL/'source_snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(Path(name).read_bytes())
        snapshots[name]=a.digest(target)
    integrity['source_snapshots']=snapshots
    check(log.read_bytes().startswith((a.LOCAL/'development_log_before.bin').read_bytes()),'Log prefix changed')
    integrity['development_log_append_only']=True
    newfiles=[p for p in subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],text=True).split('\0') if p]
    changedfiles=[p for p,h in a.core.load(a.LOCAL/'baseline.json')['files'].items() if a.digest(p)!=h]
    prohibited=re.compile('co'+'dex',re.I)
    checked=0
    for name in newfiles+changedfiles:
        p=Path(name)
        if p.suffix in ('.md','.py','.csv','.json'):
            check(not prohibited.search(p.read_text(encoding='utf-8-sig')),'Vendor-neutral policy violation: '+name)
            checked+=1
    integrity['vendor_neutral_files_checked']=checked
    valid_json=0;valid_csv=0
    for p in a.PUBLIC.rglob('*'):
        if p.suffix=='.json':a.core.load(p);valid_json+=1
        elif p.suffix=='.csv':a.core.csv_records(p);valid_csv+=1
    a.core.csv_records(a.FINAL);valid_csv+=1
    integrity['json_files_validated']=valid_json;integrity['csv_files_validated']=valid_csv
    links=[]
    for p in REPORTS:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if target.startswith(('https://','http://','#')):continue
            link=p.parent/unquote(target.split('#')[0])
            check(link.is_file() or link==a.PUBLIC/'delivery_v1.json','Broken report link: '+str(link))
            links.append({'report':p.as_posix(),'target':target})
    integrity['report_links_verified']=links
    diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True)
    check(diff.returncode==0,'git diff --check failed: '+diff.stdout+diff.stderr)
    integrity['git_diff_check']={'exit_code':diff.returncode,'stdout':diff.stdout,'stderr':diff.stderr}
    integrity['final_git']=a.prior.git_state()
    a.atomic_json(a.PUBLIC/'final_integrity_v1.json',integrity)
    inventory={p:a.digest(Path(p)) for p in newfiles+changedfiles if Path(p).is_file()}
    # Include integrity created after the inventory query.
    inventory[(a.PUBLIC/'final_integrity_v1.json').as_posix()]=a.digest(a.PUBLIC/'final_integrity_v1.json')
    delivery={'version':'p1b_confirmed_delivery_v1','created_utc':utc_now(),'files':inventory,
        'git':a.prior.git_state(),'tests':{'passed':712,'failed':0,'warnings_reported':0,'pytest_seconds':40.41,'exit_code':0},
        'annotation_sha256':a.digest(a.FINAL),'registration_sha256':a.digest(a.PUBLIC/'registration_v1.json'),
        'provenance_clarification':'annotation_provenance_clarification_v2.json',
        'integrity':'final_integrity_v1.json','source_snapshots':snapshots,
        'new_inference':0,'numerical_replays_identical':10,
        'decision':'Researcher-confirmed semantic registration and exploratory analysis completed; no confirmatory/general/algorithmic claim',
        'remaining_scientific_limits':['Independent annotation reliability unestablished','BR168 boundary unresolved',
            'Neutral controls OPEN','12 purposive speakers; development data only','Task/history and style/speaker confounding',
            'One model/template; no external validation or persona-fidelity measurement']}
    a.atomic_json(a.PUBLIC/'delivery_v1.json',delivery)
    print(json.dumps({'status':'PASS','annotations':192,'historical_journals':len(integrity['historical_journals']),
        'prior_files':integrity['prior_local_files_preserved'],'calibration_files':integrity['calibration_files_preserved'],
        'identical_replay_files':10,'tests_passed':712,'new_inference':0}))


if __name__=='__main__':main()
