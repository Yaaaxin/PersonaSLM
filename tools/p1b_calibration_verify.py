"""Read-only end-of-task integrity checks; creates only a new verification record."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

from personaslm import p1b_calibration as core
from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.p1b_readiness import CHECKS

ROOT=Path.cwd()
PUBLIC=Path('docs/validation/p1b/calibration_v1')
LOCAL=Path('results/p1b_execution/v1')


def h(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(output):
    baseline=core.load(LOCAL/'baseline.json')
    changed=[p for p,digest in baseline['files'].items() if not Path(p).exists() or h(p)!=digest]
    allowed={'docs/research_development_log.md'}
    if set(changed)-allowed:
        raise ValueError('Historical repository files changed: '+str(changed))
    old=(LOCAL/'development_log_before.bin').read_bytes()
    if not Path('docs/research_development_log.md').read_bytes().startswith(old):
        raise ValueError('Development log was rewritten')
    historical_changed=[p for p,digest in baseline['historical_local_files'].items() if not Path(p).exists() or h(p)!=digest]
    if historical_changed:
        raise ValueError('Historical local artifacts changed: '+str(historical_changed))
    for path,digest in core.load(PUBLIC/'analysis_v1/execution_inventory_v1.json')['run_artifact_hashes'].items():
        if h(path)!=digest:
            raise ValueError('New execution artifact changed: '+path)
    if core.source_inventory()!=baseline['previous_source_hashes']:
        raise ValueError('Frozen inference sources changed')
    journals=[]
    # Audit scientific journals, excluding unit fixtures, caches, weights and private material.
    folders=[p for p in Path('results').iterdir() if p.is_dir() and p.name.startswith(('p0','p1'))]
    for folder in folders:
        for manifest in sorted(folder.rglob('manifest.json')):
            if not (manifest.parent/'events').is_dir():
                continue
            m=core.load(manifest)
            if m.get('journal_version')!=1:
                continue
            events=read_events(manifest.parent)
            journals.append({'directory':manifest.parent.as_posix(),'events':len(events),
                             'manifest_sha256':h(manifest),'terminal_hash':events[-1]['event_hash'] if events else None,
                             'terminal_kind':events[-1]['kind'] if events else None,
                             'terminal_status':events[-1]['data'].get('status') if events else None})
    registration=core.load(PUBLIC/'researcher_review_registration_v1.json')
    rows=registration['records']
    if len(rows)!=24 or len({r['case_id'] for r in rows})!=24:
        raise ValueError('Researcher stimulus registration count differs')
    if Counter(r['check_'+k] for r in rows for k in CHECKS)!={'PASS':312}:
        raise ValueError('Researcher judgments differ')
    if any(r['reviewed_utc'] for r in rows) or registration['review_status']!='RESEARCHER_CONFIRMED':
        raise ValueError('Review provenance or missing-time representation differs')
    csv_count=json_count=0
    for p in PUBLIC.rglob('*'):
        if p.suffix=='.json':
            core.load(p);json_count+=1
        elif p.suffix=='.csv':
            core.csv_records(p);csv_count+=1
    packet=core.csv_records(PUBLIC/'analysis_v1/output_human_review_v1.csv')
    mapping=core.load(LOCAL/'protected/review_mapping_v1.json')
    if len(packet)!=192 or len({r['anonymous_response_id'] for r in packet})!=192:
        raise ValueError('Outcome review IDs differ')
    byid={r['anonymous_response_id']:r for r in mapping['responses']}
    audit=core.load(LOCAL/'offline_reconstruction_v1.json')
    outputs={r['request_id']:r['result'] for r in audit['rows']}
    for row in packet:
        if any(v for k,v in row.items() if k.startswith('human_')) or any(row[k] for k in ('reviewer_id','reviewed_utc','review_assistance')):
            raise ValueError('Invented human outcome annotation')
        result=outputs[byid[row['anonymous_response_id']]['request_id']]
        if row['raw_full_continuation']!=result['raw_response'] or row['raw_first_reply']!=result['parsed_response']:
            raise ValueError('Masked output text changed')
        if row['raw_sha256']!=result['evaluation']['response_status']['raw_sha256']:
            raise ValueError('Masked raw hash differs')
        for axis,flag in result['applicability'].items():
            if row['applicable_'+axis]!=str(flag).lower():
                raise ValueError('Masked applicability changed')
    reconstruction=core.load(LOCAL/'reconstruction_repeat_v1.json')
    if reconstruction['rows']!=audit['rows']:
        raise ValueError('Repeated offline parser/evaluation replay differs')
    docs=[p for p in Path('docs').glob('P1b_calibration_*.md')]
    missing=[]
    for p in docs:
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
            if '://' in link or link.startswith('#'):
                continue
            target=(p.parent/link.split('#')[0]).resolve()
            # This record is written atomically only after every check succeeds.
            if target != Path(output).resolve() and not target.exists():
                missing.append({'document':p.as_posix(),'link':link})
    if missing:
        raise ValueError('Missing documentation links: '+str(missing))
    forbidden=re.compile('co'+'dex',re.I)
    sources=[]
    for folder in ('src','tools','tests','docs','configs','data/synthetic'):
        sources.extend(p for p in Path(folder).rglob('*') if p.is_file() and p.suffix in ('.py','.md','.json','.jsonl','.csv','.yaml','.yml','.toml','.txt') and '__pycache__' not in p.parts)
    sources.extend([Path('README.md'),Path('AGENTS.md')])
    hits=[p.as_posix() for p in sources if forbidden.search(p.read_text(encoding='utf-8-sig'))]
    if hits:
        raise ValueError('Non-neutral product references: '+str(hits))
    result={'version':'p1b_calibration_final_integrity_v1','created_utc':utc_now(),'status':'PASS',
        'baseline_git_sha':baseline['git_sha'],'current_git_sha':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'git_status':subprocess.check_output(['git','status','--short'],text=True),
        'baseline_repository_files':len(baseline['files']),'historical_repository_changes':changed,'development_log_append_only':True,
        'historical_local_files_unchanged':len(baseline['historical_local_files']),
        'journal_chains_verified':journals,
        'historical_scope':'Byte comparison to task-start inventory for repository and selected P1 files; all scientific P0/P1 journal chains additionally revalidated, including prior failed/interrupted runs. Chain validity does not turn their terminal status into success.',
        'new_run_inventory':'PASS','inference_source_hashes':'PASS','repeated_offline_reconstruction':'IDENTICAL',
        'registered_stimuli':24,'preserved_judgments':312,'outcome_review_records':192,'human_outcome_labels':0,
        'json_files_validated':json_count,'csv_files_validated':csv_count,'new_report_links':'PASS',
        'vendor_neutral_search':{'files_searched':len(sources),'matches':0},
        'no_new_generation_requests':True}
    atomic_json(output,result)
    print(json.dumps({k:result[k] for k in ('status','baseline_repository_files','historical_local_files_unchanged','repeated_offline_reconstruction','registered_stimuli','preserved_judgments','outcome_review_records','human_outcome_labels','json_files_validated','csv_files_validated','new_report_links','vendor_neutral_search')}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.output)
