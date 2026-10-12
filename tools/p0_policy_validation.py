"""Immutable policy freeze, single holdout evaluation and P0 inference sidecars."""
import argparse
from collections import Counter
from dataclasses import asdict
import csv
import json
from pathlib import Path

from personaslm.conditioning import build_prompt
from personaslm.configuration import RuntimeConfig
from personaslm.evaluation_policy import evaluate_response, category_accounting, VERSION as EVAL_VERSION
from personaslm.fixtures import load_cases
from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.neutral_review import EDITABLE, make_packet
from personaslm.provenance import fingerprint, require_local_path, sha256
from personaslm.reproducibility import source_snapshot
from personaslm.response_status import classify_response, text_hash, VERSION, STATUSES
from personaslm.run_audit import audit_run
from personaslm.runner import run_local

PUBLIC = Path('docs/validation')
HOLDOUT = Path('tests/fixtures/p0_response_status_holdout_v1.json')
REAL = Path('tests/fixtures/p0_policy_inference_holdout_v1.jsonl')
FROZEN = [Path(p) for p in (
    'src/personaslm/response_status.py','src/personaslm/evaluation_policy.py',
    'src/personaslm/evaluation_v3.py','src/personaslm/evaluation_v2.py',
    'docs/P0_response_status_policy_v1.md','docs/P0_evaluation_policy_v1.md',
    'tests/fixtures/p0_response_status_development_v1.json')]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def inventory(directory):
    return {p.relative_to(directory).as_posix():sha256(p) for p in sorted(directory.rglob('*')) if p.is_file()}


def freeze(session):
    if HOLDOUT.exists() or REAL.exists():
        raise ValueError('Freeze policy before authoring this holdout; use a new version if already exposed')
    prior=[]
    for manifest in sorted(Path('results').rglob('manifest.json')):
        if (manifest.parent/'events').is_dir():
            prior.append({'directory':manifest.parent.as_posix(),'file_inventory':inventory(manifest.parent)})
    result={'created_utc':utc_now(),'boundary_version':VERSION,'evaluation_version':EVAL_VERSION,
            'frozen_files':{p.as_posix():{'sha256':sha256(p),'utf8':p.read_bytes().decode('utf-8')} for p in FROZEN},
            'configuration':RuntimeConfig.load(Path('configs/p0_runtime.local.json')).as_dict(),
            'configuration_file_sha256':sha256(Path('configs/p0_runtime.local.json')),
            'reconstruction':source_snapshot(FROZEN[-1]),'prior_journals':prior,
            'holdout_design':{'software_cases':24,'real_cases':6,'selection':'All newly authored holdout items; no output-based selection',
                              'real_generation':'C0 transcript_base_v1, 96 tokens, seed 42, temperature 0, top_p 1, stop=[], CPU 4/4, context 4096',
                              'accuracy_scope':'Authored software expectations, not independent human semantic ground truth'},
            'change_policy':'No rule edits after holdout access; a changed policy needs a new version and holdout'}
    atomic_json(session/'materials/policy_freeze.json',result)
    public={k:v for k,v in result.items() if k not in ('reconstruction','prior_journals','frozen_files')}
    public['frozen_files']={k:v['sha256'] for k,v in result['frozen_files'].items()}
    public['git']=result['reconstruction']['git']
    public['original_freeze_sha256']=sha256(session/'materials/policy_freeze.json')
    public['historical_journals_frozen']=len(prior)
    atomic_json(PUBLIC/'P0_response_policy_freeze_v1.json',public)
    print(json.dumps({'frozen_utc':result['created_utc'],'historical_journals':len(prior),'frozen_files':public['frozen_files']}))


def check_frozen(session, sealed=True):
    frozen=read(session/'materials/policy_freeze.json')
    for name, data in frozen['frozen_files'].items():
        if sha256(Path(name)) != data['sha256']:
            raise ValueError('Frozen policy changed: '+name)
    if sealed:
        seal=read(session/'materials/holdout_seal.json')
        for name,digest in seal['files'].items():
            if sha256(Path(name))!=digest:
                raise ValueError('Sealed holdout/config changed: '+name)
    return frozen


def seal(session):
    frozen=check_frozen(session,False)
    software=read(HOLDOUT)
    cases=load_cases(REAL)
    assert len(software['cases'])==24 and len(cases)==6
    assert len({r['id'] for r in software['cases']})==24
    assert not set(r['id'] for r in software['cases']) & set(r['id'] for r in read(FROZEN[-1])['cases'])
    prompts={c.case_id:asdict(build_prompt(c,'C0')) for c in cases}
    value={'created_utc':utc_now(),'policy_freeze_sha256':sha256(session/'materials/policy_freeze.json'),
           'files':{p.as_posix():sha256(p) for p in (HOLDOUT,REAL,Path('configs/p0_runtime.local.json'))},
           'prompts':prompts,'prompt_sha256':{k:text_hash(v['text']) for k,v in prompts.items()},
           'software_fixture':software,'real_fixture_utf8':REAL.read_bytes().decode('utf-8'),
           'config':frozen['configuration'],'config_sha256':fingerprint(frozen['configuration']),
           'semantic_reviews_available':0,'new_real_case_literal_risk':['policy_real_006']}
    atomic_json(session/'materials/holdout_seal.json',value)
    atomic_json(PUBLIC/'P0_response_holdout_seal_v1.json',value)
    print(json.dumps({'sealed_utc':value['created_utc'],'software_cases':24,'real_cases':6,'prompt_hashes':value['prompt_sha256']}))


def holdout(session):
    check_frozen(session)
    atomic_json(session/'experiments/holdout_started.json',{'created_utc':utc_now(),'policy_version':VERSION})
    rows=[]
    for row in read(HOLDOUT)['cases']:
        semantic=None
        if row.get('semantic'):
            semantic={'label':row['semantic'],'basis':'Authored software contract, not human annotation',
                      'review_id':row['id'],'raw_sha256':text_hash(row['raw'])}
        backend={'stop_type':row['stop'],'stopping_word':row.get('stopping_word'),**row.get('backend_extra',{})}
        result=classify_response(row['raw'],backend,declared_stops=row.get('stops',[]),
                                 literal_delimiters=row.get('literal',False),semantic_review=semantic)
        joined=result['removed_prefix']+result['first_span']['text']+result['excluded_tail']
        rows.append({'id':row['id'],'expected_status':row['expected'],'result':result,
                     'status_matches':result['status']==row['expected'],'span_matches':result['first_span']['text']==row['first'],
                     'raw_reconstruction_matches':joined==row['raw']})
    correct=sum(r['status_matches'] for r in rows)
    uncertain=[r['id'] for r in rows if r['result']['status']=='AMBIGUOUS']
    decided=[r for r in rows if r['result']['status']!='AMBIGUOUS']
    matrix={truth:{pred:sum(r['expected_status']==truth and r['result']['status']==pred for r in rows) for pred in STATUSES} for truth in STATUSES}
    result={'created_utc':utc_now(),'version':VERSION,'policy_unchanged_since_freeze':True,
            'holdout_sha256':sha256(HOLDOUT),'correct':correct,'total':len(rows),'accuracy':correct/len(rows),
            'decided_coverage':len(decided)/len(rows),'decided_correct':sum(r['status_matches'] for r in decided),
            'ambiguous_case_ids':uncertain,'confusion_matrix':matrix,
            'span_matches':sum(r['span_matches'] for r in rows),'rows':rows,
            'ground_truth_provenance':'Author-specified synthetic software expectations; not independent human ground truth or model-response accuracy',
            'status':'PASS' if correct==len(rows) and all(r['span_matches'] and r['raw_reconstruction_matches'] for r in rows) else 'PARTIAL'}
    atomic_json(session/'experiments/software_holdout_result.json',result)
    atomic_json(PUBLIC/'P0_response_status_holdout_v1.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','confusion_matrix')}))


def infer(session):
    frozen=check_frozen(session)
    atomic_json(session/'experiments/inference_started.json',{'created_utc':utc_now(),'reason':'Fresh fixed holdout validates frozen measurement end to end, not prompt optimization'})
    summary,directory=run_local(RuntimeConfig(**frozen['configuration']),'C0',REAL,session/'experiments/runs',
                               run_metadata={'policy_version':VERSION,'evaluation_policy':EVAL_VERSION,
                                             'seal_sha256':sha256(session/'materials/holdout_seal.json'),
                                             'selection':'All six frozen new holdout cases; no adaptive rerun'})
    result={'summary':summary,'run_directory':directory.as_posix()}
    atomic_json(session/'experiments/inference_result.json',result)
    print(json.dumps(result))
    if summary['status']!='PASS':
        raise SystemExit(2)


def forms(session):
    template=PUBLIC/'P0_neutral_annotation_form_v3.json'
    csv_path=PUBLIC/'P0_neutral_annotation_form_v3.csv'
    frozen_path=Path('results/p0_validation/20261012T164648/prompts_frozen_v3.json')
    expected=make_packet(read(frozen_path),sha256(frozen_path))
    assert read(template)==expected
    with csv_path.open(encoding='utf-8-sig',newline='') as handle:
        rows=list(csv.DictReader(handle))
    assert rows==[{k:str(v) for k,v in r.items()} for r in expected['items']]
    assert all(not row[k] for row in rows for k in EDITABLE)
    submissions=list(Path('results/human_review').glob('**/*')) if Path('results/human_review').exists() else []
    result={'created_utc':utc_now(),'form_items':len(rows),'material_reconstruction_matches':True,
            'case_condition_keys_unique':len({(r['case_id'],r['condition_id']) for r in rows})==40,
            'all_token_differences_zero':all(r['token_difference']=='0' for r in rows),
            'form_sha256':sha256(csv_path),'template_sha256':sha256(template),'packet_id':expected['packet_id'],
            'human_reviews_completed':0,'remaining':40,'human_review_status':'OPEN',
            'submission_files_present':sum(p.is_file() for p in submissions),
            'scope':'Blank master verified against actual frozen prompts; no new human annotations supplied or imported'}
    atomic_json(PUBLIC/'P0_neutral_review_readiness_v1.json',result)
    atomic_json(session/'materials/neutral_review_readiness.json',result)
    print(json.dumps(result))


def analyze(session):
    frozen=check_frozen(session)
    directory=Path(read(session/'experiments/inference_result.json')['run_directory'])
    a,b=audit_run(directory),audit_run(directory)
    assert a==b and a['status']=='PASS'
    events=read_events(directory)
    raws={e['data']['case_id']:e['data']['response'] for e in events if e['kind']=='raw_generation'}
    cases={c.case_id:c for c in load_cases(REAL)}
    sealed=read(session/'materials/holdout_seal.json')
    rows=[]
    for row in a['cases']:
        cid=row['case_id']
        assert row['prompt_sha256']==sealed['prompt_sha256'][cid]
        policy=evaluate_response(cases[cid],raws[cid]['content'],
                                 {k:v for k,v in raws[cid].items() if k in ('stop_type','stopping_word','stopped_eos','stopped_word','stopped_limit')},
                                 literal_delimiters=cid in sealed['new_real_case_literal_risk'])
        rows.append({'case_id':cid,'original_reconstruction':row,'policy':policy})
    prior=[]
    for old in frozen['prior_journals']:
        same=inventory(Path(old['directory']))==old['file_inventory']
        assert same,old['directory']
        prior.append({'directory':old['directory'],'unchanged':same,'inventory_sha256':fingerprint(old['file_inventory'])})
    manifest=read(directory/'manifest.json')
    summary={'created_utc':utc_now(),'boundary_version':VERSION,'evaluation_version':EVAL_VERSION,
             'new_run_id':directory.name,'new_responses':len(rows),'historical_responses_preserved':134,
             'total_recorded_responses':134+len(rows),'new_offline_replays_identical':a==b,
             'boundary_counts':dict(Counter(r['policy']['response_completeness']['status'] for r in rows)),
             'factual_accounting':category_accounting([r['policy'] for r in rows]),
             'real_boundary_accuracy':None,'accuracy_unavailable_reason':'No independent annotated real-output ground truth',
             'human_completeness_judgments':0,'old_journals':prior,'rows':rows,
             'generation_git':manifest['reconstruction']['git'],'config':manifest['configuration'],
             'manifest_sha256':sha256(directory/'manifest.json'),'terminal_event_hash':events[-1]['event_hash'],
             'server_log_sha256':sha256(directory/'server.log'),'policy_freeze_sha256':sha256(session/'materials/policy_freeze.json'),
             'legacy_evaluation_preserved':True,'policy_unchanged_after_holdout':True}
    atomic_json(session/'experiments/real_holdout_analysis.json',summary)
    # Native model paths occur in some backend settings: redact only the public copy.
    from p0_final_methodology import redact
    atomic_json(PUBLIC/'P0_response_policy_real_holdout_v1.json',redact(summary))
    print(json.dumps({k:v for k,v in summary.items() if k not in ('rows','old_journals','config','generation_git')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=('freeze','seal','holdout','infer','forms','analyze'))
    parser.add_argument('--session',type=Path,required=True)
    args=parser.parse_args()
    globals()[args.stage](require_local_path(args.session))
