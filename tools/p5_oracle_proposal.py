"""Prepare eight UNAUTHORIZED oracle-evidence diagnostics; vocabulary only.

No server, tensor inference, answers, retries or future validation cases.
"""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import p1d_instruct_smoke as s
from p1d_instruct_template_check import render

OUT=Path('docs/validation/p5/oracle_evidence_proposed_v1')

def proof_ids(case):
    facts=case['facts'];date=case['query_date'];target=case['target_entity']
    selected=set();visiting=set()
    def link(entity):
        if entity==target:return
        s.require(entity not in visiting,'Cyclic reference chain');visiting.add(entity)
        parents=[f for f in facts if f['value']==entity and f['start']<=date<=f['end']]
        # The controlled ledger has one applicable predecessor for each required chain node.
        s.require(len(parents)==1,'Ambiguous oracle predecessor')
        selected.add(parents[0]['id']);link(parents[0]['entity']);visiting.remove(entity)
    for component in case['required_components']:
        matches=[f for f in facts if f['id']==component['source_id']]
        s.require(len(matches)==1,'Invalid reference ID');f=matches[0]
        s.require(f['value']==component['value'] and f['start']<=date<=f['end'],'Invalid reference')
        selected.add(f['id']);link(f['entity'])
    return [f['id'] for f in facts if f['id'] in selected]

def main():
    plan=s.load(s.FROZEN);s.require(s.sha256(s.FROZEN)==s.SHA,'Parent manifest changed')
    cases={c['case_id']:c for c in s.load(s.b.DEV/'development_examples_v5.json')['cases']}
    exe=Path(plan['model']['backend_file']).with_name('llama-tokenize.exe')
    native=s.load(s.b.FROZEN)['native_tokenizer_identity']
    s.require(s.sha256(exe)==native['tokenizer_sha256'],'Tokenizer binary changed')
    s.require(s.sha256(Path(plan['model']['model_file']))==s.MODEL_SHA,'Model changed')
    sys.path.insert(0,str(Path('results/p1d_final_preparation/v1/tokenizer_runtime').resolve()))
    from tokenizers import Tokenizer
    upstream=Tokenizer.from_file('results/p1d_final_preparation/v1/official_tokenizer/tokenizer.json')
    template=Path(plan['template_path']).read_text(encoding='utf-8')
    rows=[];logs=[]
    for old in plan['requests']:
        c=cases[old['case_id']];ids=proof_ids(c)
        evidence='\n'.join(line for line in c['trusted_evidence'].splitlines() if line.split(']',1)[0][1:] in ids)
        s.require(len(evidence.splitlines())==len(ids),'Source-line reconstruction')
        messages=[dict(m) for m in old['messages']]
        s.require(messages[0]['content'].count(c['trusted_evidence'])==1,'Evidence occurrence')
        messages[0]['content']=messages[0]['content'].replace(c['trusted_evidence'],evidence)
        prompt=render(template,messages)
        argv=[str(exe.resolve()),'-m',str(Path(plan['model']['model_file']).resolve()),'--stdin','--ids','--offline']
        started=s.b.utc_now()
        result=subprocess.run(argv,input=prompt.encode(),capture_output=True,timeout=60,
            env={k:v for k,v in os.environ.items() if not k.upper().startswith('LLAMA_ARG_')},
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        log={'started_utc':started,'finished_utc':s.b.utc_now(),'argv':argv,'prompt':prompt,
             'returncode':result.returncode,'stdout':result.stdout.decode('utf-8','replace'),
             'stderr':result.stderr.decode('utf-8','replace'),'generation_requests':0}
        lp=OUT/'native_tokenizer'/f'{old["order"]:04d}.json';s.save(lp,log)
        s.require(result.returncode==0,'Tokenizer failure')
        tokens=ast.literal_eval(log['stdout'].strip())
        s.require(tokens==upstream.encode(prompt,add_special_tokens=True).ids,'Native/official mismatch')
        row={k:v for k,v in old.items() if k not in ('request_sha256','request_id','prompt','prompt_sha256','messages',
             'input_token_ids','input_tokens','input_token_ids_sha256','context_remaining')}
        row.update({'request_id':'p5_oracle_dev_v1_'+c['case_id'],'parent_instruct_request_id':old['request_id'],
            'parent_request_sha256':old['request_sha256'],'intervention':'ORACLE_MINIMAL_SUFFICIENT_EVIDENCE',
            'selected_source_ids':ids,'trusted_evidence':evidence,'prompt':prompt,'messages':messages,
            'prompt_sha256':s.th(prompt),'input_token_ids':tokens,'input_tokens':len(tokens),
            'input_token_ids_sha256':s.th(str(tokens)),'context_remaining':4096-96-len(tokens)})
        row['request_sha256']=s.th(json.dumps(row,sort_keys=True,separators=(',',':')));rows.append(row)
        logs.append({'path':lp.as_posix(),'sha256':s.sha256(lp),'tokens':len(tokens)})
    proposal={k:plan[k] for k in ('model','template_path','template_sha256','candidate_metadata_sha256','order_seed','decoding_policy')}
    proposal.update({'version':'p5_oracle_evidence_proposed_v1','status':'PROPOSED_NOT_AUTHORIZED','phase':'P5',
        'research_question':'RQ4: answer-generation headroom with oracle answer-sufficient evidence',
        'parent_manifest_sha256':s.SHA,'authorized_requests':0,'proposed_requests':8,'maximum_generated_tokens':768,
        'requests':rows,'native_tokenizer_logs':logs,'tokenizer_sha256':native['tokenizer_sha256'],
        'experimental_unit':'Eight existing paired development cases; full-ledger historical reference reused without generation.',
        'changed_variables':['Trusted evidence subset','Evidence length','Evidence serial positions','Competing-entity/interval availability'],
        'unchanged_variables':['question','reference','fixed context','persona profile','H_none','model','template','seed','order','decoding','96-token limit'],
        'interpretation':'Oracle headroom package diagnostic, outside the Track A equal-evidence persona contrasts. Not deployable retrieval, causal blame allocation, independent replication or an ESCP efficacy test.',
        'acceptance':'8/8 identifiable complete task answers without answer-losing cut, with separately reported factual/temporal and component support. This stricter headroom gate is necessary, not sufficient, for a later all-condition feasibility proposal.',
        'negative_result_action':'If the strict headroom gate fails, maintain main-study NO-GO; inspect exact failures and consider a prospective model/task-policy amendment, not another automatic sweep.',
        'positive_result_action':'Prepare separately authorized evidence-selection validation and all-condition S/F/H feasibility; do not adopt reduced oracle evidence as the original Track A intervention.',
        'stop_rule':'At most eight attempts or 45 minutes; integrity/runtime/OOM failure stops; no retries or hidden warmup.',
        'required_authorization':'Explicit approval of this manifest hash, P5 evidence change and limited third-party model lineage; no main-cohort authorization.'})
    path=OUT/'oracle_evidence_manifest_proposed_v1.json';s.save(path,proposal)
    print(json.dumps({'manifest':path.as_posix(),'sha256':s.sha256(path),'proposed_requests':8,'authorized':0,
                      'native_token_range':[min(r['input_tokens'] for r in rows),max(r['input_tokens'] for r in rows)]}))

if __name__=='__main__':main()
