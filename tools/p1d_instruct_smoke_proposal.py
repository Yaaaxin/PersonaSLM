"""Vocabulary-only validation and a separately authorizable eight-request Instruct proposal."""
import ast
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import p1d_budget_calibration as b
from p1d_instruct_artifact_prepare import OUT,DEST,SHA,REV,REPO,UPSTREAM
from p1d_instruct_template_check import render,messages_for_base,META

LOCAL=Path('results/p1d_instruct_preparation/v3')

def main():
    b.require(b.sha256(DEST)==SHA,'Candidate checksum differs')
    candidate=b.load(OUT/'local_candidate_metadata_v1.json')
    source=b.load(b.FROZEN);exe=Path(source['model']['backend_file']).with_name('llama-tokenize.exe')
    b.require(b.sha256(exe)==source['native_tokenizer_identity']['tokenizer_sha256'],'Tokenizer changed')
    sys.path.insert(0,str(Path('results/p1d_final_preparation/v1/tokenizer_runtime').resolve()))
    from tokenizers import Tokenizer
    upstream=Tokenizer.from_file('results/p1d_final_preparation/v1/official_tokenizer/tokenizer.json')
    official=(META/'chat_template.jinja').read_text(encoding='utf-8')
    rows=[r for r in source['requests'] if r['condition']=='H_none' and r['max_new_tokens']==96]
    random.Random(716709).shuffle(rows);proposed=[];logs=[]
    argv=[str(exe.resolve()),'-m',str(DEST.resolve()),'--stdin','--ids','--offline']
    env={k:v for k,v in os.environ.items() if not k.upper().startswith('LLAMA_ARG_')}
    for i,old in enumerate(rows):
        messages=messages_for_base(old['prompt']);prompt=render(official,messages)
        b.require(prompt.endswith('<|im_start|>assistant\n<think>\n\n</think>\n\n'),'Nonthinking prefix changed')
        expected=upstream.encode(prompt,add_special_tokens=True).ids
        started=b.utc_now();r=subprocess.run(argv,input=prompt.encode(),capture_output=True,timeout=60,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        log={'started_utc':started,'finished_utc':b.utc_now(),'argv':argv,'prompt':prompt,'prompt_sha256':b.th(prompt),
            'stdout':r.stdout.decode('utf-8','replace'),'stderr':r.stderr.decode('utf-8','replace'),'returncode':r.returncode,'generation_requests':0}
        path=LOCAL/'native_tokenizer'/f'{i:04d}.json';b.save(path,log)
        b.require(r.returncode==0,'Native tokenizer failed')
        ids=ast.literal_eval(log['stdout'].strip());b.require(ids==expected,'Native/upstream tokenizer mismatch')
        logs.append({'path':path.as_posix(),'sha256':b.sha256(path),'tokens':len(ids),'official_ids_equal':True,
            'embedded_template_same_for_this_mapping':render(candidate['static_metadata']['tokenizer.chat_template'],messages)==prompt})
        row={'order':i,'request_id':'p1d_instruct_smoke_v1_'+old['case_id'],'case_id':old['case_id'],'speaker_id':old['speaker_id'],
            'condition':'H_none','split':'DEVELOPMENT_ONLY_EXCLUDED_FROM_VALIDATION','historical_base_request_id':old['request_id'],
            'historical_base_request_sha256':old['request_sha256'],'prompt':prompt,'messages':messages,'prompt_sha256':b.th(prompt),
            'input_token_ids':ids,'input_tokens':len(ids),'input_token_ids_sha256':b.th(str(ids)),'parse_special':True,
            'seed':42,'temperature':0,'top_p':1,'cache_prompt':False,'stop':[],'ignore_eos':False,'max_new_tokens':96,
            'reference':old['reference'],'reference_sha256':old['reference_sha256'],'context_remaining':4096-len(ids)-96}
        row['request_sha256']=b.th(json.dumps(row,sort_keys=True,separators=(',',':')));proposed.append(row)
    b.save(OUT/'native_development_tokenizer_v1.json',{'rows':logs,'model_sha256':SHA,'tokenizer_sha256':b.sha256(exe),
        'generation_requests':0,'parse_special':True,'add_special':'Native default; exact upstream array equality checked',
        'scope':'Eight development prompts only; no tensor computation or model server. Not native certification of all 288 candidate prompts.'})
    manifest={'version':'p1d_instruct_smoke_proposed_v1','status':'PROPOSAL_NOT_AUTHORIZED','authorized_requests':0,'proposed_requests':8,
        'scope':'Eight existing development cases, H_none, official non-thinking template, one fixed 96-token budget, no retries.',
        'model':{'upstream':'Qwen/Qwen3.5-2B','intended_upstream_revision':UPSTREAM,'artifact_repository':REPO,'artifact_revision':REV,
            'model_file':DEST.as_posix(),'model_sha256':SHA,'quantization':'Q4_K_M','quantizer_reported_build':'b8185',
            'source_weight_conversion_lineage':'PARTIALLY_VERIFIED; distributor supplies model name/build, not exact weight revision or command',
            'backend_file':source['model']['backend_file'],'backend_sha256':source['model']['backend_sha256'],
            'threads':4,'threads_batch':4,'ctx':4096,'gpu_layers':0,'mtp':False,'vision':False,'warmup':False},
        'template_path':(META/'chat_template.jinja').as_posix(),'template_sha256':b.sha256(META/'chat_template.jinja'),
        'template_policy':'Explicit official revision template, enable_thinking=False; do not silently use different embedded GGUF template.',
        'decoding_policy':'Greedy comparability diagnostic, not upstream recommended sampled benchmark decoding.',
        'output_budget_reason':'Same 96-token capacity as Base format diagnostic; short 1-3 component answers. Adequacy is tested, not assumed; no new budget sweep.',
        'maximum_generated_tokens':768,'order_seed':716709,'requests':proposed,
        'native_tokenizer_evidence_sha256':b.sha256(OUT/'native_development_tokenizer_v1.json'),
        'candidate_metadata_sha256':b.sha256(OUT/'local_candidate_metadata_v1.json'),
        'preflight':['Explicit authorization of this exact hash and partial conversion-lineage limitation','Exact local model/backend/DLL/template/source checks','Disable server warmup; zero unlisted completion requests','Native special-token arrays and CPU4/ctx4096 verified','No validation case contamination'],
        'stop_rule':'Eight attempts or integrity/runtime/OOM/45-minute ceiling. No retries, no additional samples.',
        'acceptance':'8/8 identifiable and semantically complete task answers, no answer-losing boundary cut; separately assess supported components, factual/temporal errors and persona fidelity. No automatic main-study qualification.',
        'consequences':'Failure keeps both validation arms NO-GO; success supports separately authorized all-condition development measurement validation, not immediate 2016-request execution.',
        'confounders':['Model weights, quantizer build, template, special-token interpretation and native EOG policy differ from Base','No pure post-training or full-cohort model interaction','Development cases already inspected','No independent human boundary truth'],
        'required_researcher_decision':'AUTHORIZE_8_WITH_DISCLOSED_LIMITATIONS or DEFER; no automatic adoption of a new primary P1d model/output policy.'}
    b.save(OUT/'minimal_instruct_smoke_manifest_proposed_v1.json',manifest)
    print(json.dumps({'native_tokenizer_prompts':8,'range':[min(r['input_tokens'] for r in proposed),max(r['input_tokens'] for r in proposed)],
        'embedded_render_equals_official':sum(x['embedded_template_same_for_this_mapping'] for x in logs),'inference':0,
        'proposed_manifest_sha256':b.sha256(OUT/'minimal_instruct_smoke_manifest_proposed_v1.json')}))

if __name__=='__main__':main()
