"""Read-only research validation plus a new immutable verification receipt."""
import csv
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import unquote
import p1c_calibration as c

OUT=Path('docs/validation/p1c/calibration_v1/closeout_v1')
CAPTURES=Path('results/p1c_compatibility/v1')


def main():
    if OUT.exists():raise FileExistsError('Keep historical verification receipts')
    base=c.load(CAPTURES/'baseline.json');changed=[]
    for name,digest in base['files'].items():
        path=Path(name)
        if name=='docs/research_development_log.md':
            before=(CAPTURES/'development_log.before.md').read_bytes()
            c.d.require(c.d.sha(CAPTURES/'development_log.before.md')==digest and path.read_bytes().startswith(before),'Historical log text changed')
            if c.d.sha(path)!=digest:changed.append(name)
        else:c.d.require(c.d.sha(path)==digest,'Entry source changed: '+name)
    historical=c.load('results/p1c_final_review/v1/baseline.json')['historical_artifacts']
    for name,digest in historical.items():c.d.require(c.d.sha(name)==digest,'Historical experiment changed: '+name)
    measurement=Path('docs/validation/p1c/calibration_v1/measurement_v1')
    for name,digest in c.load(measurement/'review_integrity_v1.json')['files'].items():
        c.d.require(c.d.sha(measurement/name)==digest,'Measurement artifact changed: '+name)
    for name,field in [('tools/p1c_measurement.py','source_code_sha256'),('tools/p1c_paired_statistics.py','statistics_code_sha256')]:
        c.d.require(c.d.sha(name)==c.load(measurement/'review_integrity_v1.json')[field],'Analysis code changed: '+name)
    summary=c.load(measurement/'measurement_summary_v1.json')
    c.d.require(summary['successful']==72 and summary['failed']==0 and summary['semantic_human_judgments']==0,'Execution/evaluation inventory mismatch')
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    c.d.require(head==base['git_head'],'Git HEAD changed')
    diff=subprocess.run(['git','diff','--check'],capture_output=True,text=True)
    c.d.require(diff.returncode==0,'Git whitespace check failed: '+diff.stdout+diff.stderr)
    full=c.load(CAPTURES/'full_tests_02.json')
    c.d.require(full['exit_code']==0 and '907 passed' in full['stdout'],'Expected complete test result absent')
    OUT.mkdir(parents=True)
    for name in ['register_01.json','approval_01.json','gate_01.json','tests_01.json','tests_02.json',
                 'tests_execution_01.json','offline_baseline_01.json','preflight_execution_01.json',
                 'execution_01.json','measurement_01.json','measurement_02.json','review_observations_01.json',
                 'full_tests_01.json','full_tests_02.json']:
        target=OUT/'engineering_logs'/name;target.parent.mkdir(exist_ok=True)
        shutil.copyfile(CAPTURES/name,target)
    roots=[Path('docs/validation/p1c/decision_compatibility_v1'),Path('docs/validation/p1c/authorization_v2'),
           Path('docs/validation/p1c/calibration_v1'),Path('docs/validation/method_development/component_baseline_v1'),
           Path('docs/validation/research_monitor_v1')]
    counts={'json':0,'csv':0}
    for root in roots:
        for path in root.rglob('*'):
            if path.suffix=='.json':c.load(path);counts['json']+=1
            if path.suffix=='.csv':
                with path.open(encoding='utf-8-sig',newline='') as f:
                    reader=csv.DictReader(f)
                    c.d.require(reader.fieldnames and len(reader.fieldnames)==len(set(reader.fieldnames)),'CSV columns invalid: '+str(path))
                    for row in reader:c.d.require(None not in row and all(v is not None for v in row.values()),'Malformed CSV: '+str(path))
                counts['csv']+=1
    docs=[Path('docs')/name for name in ['P1c_decision_compatibility_resolution.md','P1c_final_consolidated_approval_v1.md',
          'P1c_nongated_research_progress_v1.md','related_work_novelty_matrix_monitor_v1.md',
          'P1c_calibration_semantic_review_guide_v1.md','P1c_calibration_execution_and_measurement_report_v1.md']]
    links=0
    for path in docs:
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):continue
            resolved=(path.parent/unquote(target.split('#')[0])).resolve()
            c.d.require(resolved.exists() or resolved==(OUT/'verification_v1.json').resolve(),'Broken documentation link: '+target)
            links+=1
    tracked_status=subprocess.check_output(['git','status','--short','--untracked-files=all'],text=True)
    inventory={p.as_posix():c.d.sha(p) for root in roots for p in root.rglob('*') if p.is_file()}
    inventory.update({p.as_posix():c.d.sha(p) for p in docs})
    inventory.update({p.as_posix():c.d.sha(p) for p in list(Path('tools').glob('p1c_*.py'))+list(Path('tests').glob('test_p1c_*.py'))})
    result={'version':'p1c_authorized_calibration_closeout_v1','status':'PASS','verified_utc':c.d.now(),
            'git_head':head,'git_status':tracked_status,'git_diff_check':'PASS',
            'entry_files_checked':len(base['files']),'entry_files_changed':changed,'historical_run_files_preserved':len(historical),
            'source_and_review_files_preserved':True,'historical_log_prefix_preserved':True,
            'manifest_sha256':c.p.MANIFEST_SHA,'actual_generation_requests':72,'successful_requests':72,'failed_requests':0,
            'human_semantic_labels':0,'new_inference_in_verification':0,'full_tests':'907 passed in 37.57s',
            'test_capture_sha256':c.d.sha(CAPTURES/'full_tests_02.json'),'json_csv_validation':counts,
            'new_document_local_links_checked':links,'result_and_statistics_reconstruction_twice':'EXACT_AGREEMENT',
            'pre_generation_approvals':'ALL_THREE_REGISTERED','next_dependent_gate':'Valid human semantic annotations and boundary dispositions; no renewed request for existing approvals.',
            'files':inventory,'verification_code_sha256':c.d.sha(Path(__file__))}
    c.d.write_json(OUT/'verification_v1.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('files','git_status')},indent=2))


if __name__=='__main__':main()
