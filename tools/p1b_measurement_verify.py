"""Offline preservation and measurement-delivery verification; no inference entry point."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

from personaslm.journal import atomic_json, read_events, utc_now
from p1b_measurement_audit import OUT, LOCAL, OLD, core, digest, text_digest, split_views


def verify(output):
    if output.exists():
        raise FileExistsError(output)
    baseline=core.load(LOCAL/'baseline.json')
    allowed={'docs/research_development_log.md','docs/P1b_calibration_algorithmic_opportunity.md'}
    changed=[p for p,h in baseline['tracked_hashes'].items() if not Path(p).is_file() or digest(p)!=h]
    if set(changed)-allowed:
        raise ValueError('Historical tracked material changed: '+str(changed))
    for name,old in [('docs/research_development_log.md','development_log_before.bin'),
                     ('docs/P1b_calibration_algorithmic_opportunity.md','algorithmic_report_before.bin')]:
        if not Path(name).read_bytes().startswith((LOCAL/old).read_bytes()):
            raise ValueError('Historical document rewritten: '+name)
    older=core.load(Path('results/p1b_execution/v1/baseline.json'))
    for p,h in older['historical_local_files'].items():
        if digest(p)!=h:
            raise ValueError('Earlier local experiment changed: '+p)
    inventory=core.load(OLD/'execution_inventory_v1.json')
    for p,h in inventory['run_artifact_hashes'].items():
        if digest(p)!=h:
            raise ValueError('Calibration artifact changed: '+p)
    if core.source_inventory()!=older['previous_source_hashes']:
        raise ValueError('Inference/policy sources changed')
    old_checks=core.load(Path('docs/validation/p1b/calibration_v1/final_integrity_v1.json'))
    journals=[]
    wave1_results=[]
    for original in old_checks['journal_chains_verified']:
        directory=Path(original['directory'])
        events=read_events(directory)
        if (digest(directory/'manifest.json')!=original['manifest_sha256'] or
            len(events)!=original['events'] or events[-1]['event_hash']!=original['terminal_hash']):
            raise ValueError('Historical chain/manifest differs: '+str(directory))
        journals.append({'directory':directory.as_posix(),'events':len(events),
            'terminal_hash':events[-1]['event_hash'],'original_terminal_status':original['terminal_status']})
        if directory.as_posix().startswith('results/p1_wave1/development_v1/runs/'):
            wave1_results.extend(e['data'] for e in events if e['kind']=='p1_result')
    # The original Wave 1 annotations bind the exact generated first/full text.
    reviewed=core.csv_records(Path('docs/validation/p1/output_human_review_researcher_verified_v1.csv'))
    if len(wave1_results)!=96:
        raise ValueError('Expected 96 original Wave 1 results')
    frozen_boundaries=[r['evaluation']['response_completeness'] for r in wave1_results]
    native_hashes=Counter((b['raw_sha256'],b['first_span']['sha256'],b['status']) for b in frozen_boundaries)
    if native_hashes!=Counter((r['raw_sha256'],r['first_reply_sha256'],r['structural_status']) for r in reviewed):
        raise ValueError('Wave 1 review/native content multiset differs')
    original=core.csv_records(OLD/'output_human_review_v1.csv')
    expected=split_views(original)
    for name,rows in zip(('semantic_scoring_view_v2.csv','structural_review_view_v2.csv'),expected):
        if core.csv_records(OUT/name)!=rows:
            raise ValueError('Masked view differs from source: '+name)
    summary=core.load(OUT/'audit_summary_v1.json')
    for name,h in summary['artifact_hashes'].items():
        if digest(OUT/name)!=h:
            raise ValueError('Audit artifact changed: '+name)
    mapped=LOCAL/'protected/treatment_mapping_v1.json'
    if digest(mapped)!=summary['protected_mapping_sha256']:
        raise ValueError('Protected mapping hash differs')
    if subprocess.run(['git','check-ignore','--quiet',str(mapped)]).returncode!=0:
        raise ValueError('Treatment mapping is not ignored')
    if digest(Path('tools/p1b_measurement_audit.py'))!=summary['source_sha256']:
        raise ValueError('Audit source changed after execution')
    json_files,csv_files=0,0
    for p in OUT.iterdir():
        if p.suffix=='.json':
            core.load(p); json_files+=1
        elif p.suffix=='.csv':
            core.csv_records(p); csv_files+=1
    file_list=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],text=True).split('\0')
    file_list += changed
    text_files=[Path(p) for p in set(file_list) if p and Path(p).suffix in ('.py','.md','.json','.csv')]
    prohibited=re.compile('co'+'dex',re.I)
    for p in text_files:
        if prohibited.search(p.read_text(encoding='utf-8-sig')):
            raise ValueError('Vendor-neutral policy violation: '+str(p))
    snapshots={}
    for name in ('tools/p1b_measurement_audit.py','tools/p1b_measurement_report.py',
                 'tools/p1b_measurement_verify.py','tests/test_p1b_measurement_audit.py'):
        target=LOCAL/'source_snapshot'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:
            f.write(Path(name).read_bytes())
        snapshots[name]=digest(target)
    record={'version':'p1b_measurement_integrity_v1','created_utc':utc_now(),
        'baseline_git_sha':baseline['git_sha'],'current_git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'baseline_tracked_files':len(baseline['tracked_hashes']), 'allowed_append_only_changes':changed,
        'prior_local_files_unchanged':len(older['historical_local_files']),
        'calibration_artifact_files_unchanged':len(inventory['run_artifact_hashes']),
        'historical_journals_verified':journals,
        'wave1_native_results_matched_to_review':96,
        'wave1_identifiable':sum(b['unit_identifiable'] for b in frozen_boundaries),
        'review_records':192,'blank_human_fields_verified':True,'protected_mapping_git_ignored':True,
        'json_files_validated':json_files,'csv_files_validated':csv_files,
        'vendor_neutral_text_files_checked':len(text_files),'source_snapshots':snapshots,
        'frozen_inference_sources_unchanged':True,'new_inference':0,
        'git_status':subprocess.check_output(['git','status','--short'],text=True)}
    atomic_json(output,record)
    print(json.dumps({k:record[k] for k in ('baseline_tracked_files','prior_local_files_unchanged',
        'calibration_artifact_files_unchanged','wave1_identifiable','review_records','json_files_validated','csv_files_validated')}))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    verify(p.parse_args().output)
