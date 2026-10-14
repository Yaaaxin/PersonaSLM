import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import p1d_format_calibration as f
from p1d_instruct_artifact_prepare import OUT,DEST,SHA,SIZE
from p1d_instruct_template_check import render,META,messages_for_base

def test_candidate_local_bytes_and_disclosed_provenance():
    assert DEST.stat().st_size==SIZE and f.sha256(DEST)==SHA
    m=f.load(OUT/'local_candidate_metadata_v1.json')
    assert m['source_upstream_revision']=='NOT_CERTIFIED_BY_DISTRIBUTOR'
    assert not m['runtime_loaded'] and m['generation_requests']==0
    assert m['merges_equal'] and m['shared_id_mismatches']==[]

def test_smoke_scope_is_exact_unapproved_development_only():
    path=OUT/'minimal_instruct_smoke_manifest_proposed_v1.json'
    assert f.sha256(path)=='ba63c30a9868b94b47f8f79dd774ac0627d56113810ffd4db08eb63af0374b91'
    p=f.load(path);assert p['authorized_requests']==0 and p['proposed_requests']==8 and p['maximum_generated_tokens']==768
    assert {r['case_id'] for r in p['requests']}==set(f.b.CASE_IDS)
    assert all(r['condition']=='H_none' and r['max_new_tokens']==96 and r['ignore_eos'] is False for r in p['requests'])
    assert p['model']['warmup'] is False and p['model']['gpu_layers']==0

def test_official_template_preserves_original_task_body():
    p=f.load(OUT/'minimal_instruct_smoke_manifest_proposed_v1.json')
    old={r['request_id']:r for r in f.load(f.b.FROZEN)['requests']}
    template=(META/'chat_template.jinja').read_text(encoding='utf-8')
    for i,r in enumerate(p['requests']):
        base=old[r['historical_base_request_id']]
        assert r['order']==i and r['historical_base_request_sha256']==base['request_sha256']
        assert r['messages']==messages_for_base(base['prompt'])
        assert r['prompt']==render(template,r['messages'])
        assert r['prompt_sha256']==f.th(r['prompt'])
        assert r['request_sha256']==f.th(json.dumps({k:v for k,v in r.items() if k!='request_sha256'},sort_keys=True,separators=(',',':')))
        assert len(r['input_token_ids'])==r['input_tokens'] and r['context_remaining']>=0

def test_native_tokenizer_records_are_real_and_no_generation():
    report=f.load(OUT/'native_development_tokenizer_v1.json')
    assert report['generation_requests']==0 and report['parse_special'] is True
    assert len(report['rows'])==8
    for r in report['rows']:
        assert f.sha256(Path(r['path']))==r['sha256'] and r['official_ids_equal']
        log=f.load(r['path']);assert log['returncode']==0 and log['generation_requests']==0
        assert 'llama-tokenize.exe' in log['argv'][0] and '--no-parse-special' not in log['argv']
