"""Finite four-worker vocabulary-only checks of unapproved candidate Base prompts.

This does not launch a model server, decode tokens, or authorize any generation.
Full token IDs/logs remain in local results with per-call hashes in the public table.
"""
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from p1d_design import read, write, sha, th, CELLS
from p1c_tokenize import NativeTokenizer

DATA=Path('docs/validation/p1d/independent_candidates_v2')
LOGS=Path('results/p1d_readiness/v1/candidate_native_calls')

def run():
    target=DATA/'native_tokenizer_validation_v1.json'
    if target.exists() or LOGS.exists():raise FileExistsError('Preserve partial/completed candidate token check')
    rows=read(DATA/'base_candidate_prompts_v1.json')
    if len(rows)!=1728 or len({r['candidate_request_id'] for r in rows})!=1728:
        raise ValueError('Candidate count/identity mismatch')
    native=NativeTokenizer(); LOGS.mkdir(parents=True)
    def one(row):
        if th(row['prompt'])!=row['prompt_sha256']:raise ValueError('Prompt hash mismatch')
        start=datetime.now(timezone.utc).isoformat()
        p=subprocess.run(native.argv,input=row['prompt'].encode('utf-8'),capture_output=True,timeout=60)
        log={'candidate_request_id':row['candidate_request_id'],'prompt_sha256':row['prompt_sha256'],
            'software_started_utc':start,'software_finished_utc':datetime.now(timezone.utc).isoformat(),
            'exit_code':p.returncode,'stdout':p.stdout.decode('utf-8','replace'),'stderr':p.stderr.decode('utf-8','replace'),
            'generation':False}
        path=LOGS/(row['candidate_request_id']+'.json');write(path,log)
        if p.returncode:raise ValueError('Native tokenizer error: '+row['candidate_request_id'])
        ids=ast.literal_eval(log['stdout'].strip())
        if not isinstance(ids,list) or any(type(x) is not int for x in ids):raise ValueError('Invalid token output')
        return {'candidate_request_id':row['candidate_request_id'],'case_id':row['case_id'],'condition':row['condition'],
            'prompt_sha256':row['prompt_sha256'],'input_tokens':len(ids),'token_ids_sha256':th(str(ids)),
            'native_call_log':path.as_posix(),'native_call_sha256':sha(path),'context_fit_96':len(ids)+96<=4096,
            'context_fit_256':len(ids)+256<=4096}
    result=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(one,row) for row in rows]
        for future in as_completed(futures):
            result.append(future.result())
            if len(result)%144==0:print({'native_prompts_checked':len(result),'total':1728,'generations':0},flush=True)
    result.sort(key=lambda r:r['candidate_request_id'])
    checks=[]
    for cid in sorted({r['case_id'] for r in result}):
        counts={r['condition']:r['input_tokens'] for r in result if r['case_id']==cid}
        checks.append({'case_id':cid,'counts':counts,'active_equal':len({counts[c] for c in CELLS[:4]})==1,
            'control_equal':len({counts[c] for c in CELLS[:5]})==1,
            'control_minus_E1V1':counts['D_procedural']-counts['E1V1']})
    summary={'source_sha256':sha(DATA/'base_candidate_prompts_v1.json'),'code_sha256':sha(__file__),
        'identity':native.identity,'workers':4,'rows':result,'cases':checks,'new_generations':0,
        'context_fit_256':all(r['context_fit_256'] for r in result),'active_matches':sum(c['active_equal'] for c in checks),
        'control_matches':sum(c['control_equal'] for c in checks),
        'input_token_range':[min(r['input_tokens'] for r in result),max(r['input_tokens'] for r in result)],
        'semantic_validity':'UNREVIEWED_NOT_ESTABLISHED','independent_confirmatory_freeze':False}
    write(target,summary)
    print({k:summary[k] for k in ('new_generations','context_fit_256','active_matches','control_matches','input_token_range')},flush=True)

if __name__=='__main__':run()
