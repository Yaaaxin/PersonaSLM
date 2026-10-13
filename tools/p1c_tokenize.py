"""Offline native vocabulary tokenization only; no generation or server endpoint."""
import argparse
import ast
import json
from pathlib import Path
import subprocess

from p1c_design import DATA, PUBLIC, LOCAL, CONDITIONS, read, sha, text_hash, render, require, write_json, write_csv, now

MODEL_HASH='ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994'
BACKEND_HASH='71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846'


def select_match(counts):
    """Fixed ordered bank; never extend candidates or use model answer quality."""
    for variant in range(16):
        lengths=[counts[c][variant] for c in ('R0T0','R0T1','R1T0','R1T1')]
        if len(set(lengths))!=1:continue
        qi=variant//4
        for neutral in range(qi*8,qi*8+8):
            if counts['N_history'][neutral]==lengths[0]:return variant,neutral
    return None


class NativeTokenizer:
    def __init__(self):
        cfg=read('configs/p1_wave1_v1.json');self.model=Path(cfg['model_file']);self.server=Path(cfg['server_file'])
        self.exe=self.server.with_name('llama-tokenize.exe');self.cache={};self.calls=[]
        require(sha(self.model)==MODEL_HASH,'Model hash mismatch')
        require(sha(self.server)==BACKEND_HASH,'Server hash mismatch')
        self.argv=[str(self.exe.resolve()),'-m',str(self.model.resolve()),'--stdin','--ids','--no-parse-special','--offline']
        version=subprocess.run([str(self.exe.resolve()),'--version'],capture_output=True,timeout=60)
        self.version={'exit_code':version.returncode,'stdout':version.stdout.decode('utf-8','replace'),'stderr':version.stderr.decode('utf-8','replace')}
        require(version.returncode==0 and '11573' in self.version['stdout']+self.version['stderr'],'Native tokenizer build mismatch')
        self.identity={'model_sha256':sha(self.model),'backend_sha256':sha(self.server),'tokenizer_sha256':sha(self.exe),
            'native_version':self.version,'dll_hashes':{p.name:sha(p) for p in self.exe.parent.glob('*.dll')},
            'argv_public':[self.exe.name,'-m',self.model.name,'--stdin','--ids','--no-parse-special','--offline'],
            'parse_special':False,'add_special':'Native default; equality checked against saved backend input IDs',
            'no_generation':True,'implementation':'Pinned native llama-tokenize vocabulary-only utility; no server launched.'}

    def tokens(self,prompt):
        key=text_hash(prompt)
        if key in self.cache:return self.cache[key]
        start=now();p=subprocess.run(self.argv,input=prompt.encode('utf-8'),capture_output=True,timeout=60)
        log={'started_utc':start,'finished_utc':now(),'prompt':prompt,'prompt_sha256':key,'exit_code':p.returncode,
             'stdout':p.stdout.decode('utf-8','replace'),'stderr':p.stderr.decode('utf-8','replace')}
        # Preserve each native call even if validation below fails.
        write_json(LOCAL/'native_calls'/f'{len(self.calls):04d}.json',log);self.calls.append(log)
        require(p.returncode==0,'Native tokenizer failed')
        ids=ast.literal_eval(log['stdout'].strip())
        require(isinstance(ids,list) and all(type(t)==int for t in ids),'Unexpected native ID output')
        self.cache[key]=ids;return ids

    def verify_historical(self):
        inv=read('docs/validation/p1b/calibration_v1/analysis_v1/execution_inventory_v1.json');chosen=[]
        for path,h in inv['run_artifact_hashes'].items():
            if '/events/' not in path or not path.endswith('.json'):continue
            event=read(path)
            if event['kind']!='p1b_result':continue
            d=event['data']
            if d['family'] in {x['family'] for x in chosen}:continue
            require(sha(path)==h,'Historical tokenizer probe source changed')
            ids=self.tokens(d['prompt']);require(ids==d['input_token_ids'],'Native IDs differ from loaded backend')
            chosen.append({'source':path,'source_sha256':h,'family':d['family'],'request_id':d['request_id'],
                'prompt_sha256':d['prompt_sha256'],'tokens':len(ids),'input_token_ids_equal':True})
            if len(chosen)==3:break
        require(len(chosen)==3,'Insufficient identity probes')
        return chosen


def run():
    require(not (PUBLIC/'tokenizer_validation_v1.json').exists(),'Refusing overwrite')
    native=NativeTokenizer();probes=native.verify_historical();data=read(DATA);bank=read(PUBLIC/'candidate_bank_v1.json')
    selected=[];attempts=[];matches=[];review=[]
    for case,cb in zip(data['cases'],bank['cases']):
        require(case['case_id']==cb['case_id'],'Candidate identity mismatch')
        counts={};ids={}
        # The complete predeclared finite bank is measured to preserve best failures too.
        for condition,variants in cb['conditions'].items():
            counts[condition]=[];ids[condition]=[]
            for v in variants:
                prompt=render(case,v['text']);tokens=native.tokens(prompt)
                counts[condition].append(len(tokens));ids[condition].append(tokens)
                attempts.append({'case_id':case['case_id'],'condition':condition,'variant_id':v['variant_id'],
                    'question_variant':v['question_variant'],'prompt_sha256':text_hash(prompt),'tokens':len(tokens)})
        found=select_match(counts)
        spreads=[max(counts[c][i] for c in ('R0T0','R0T1','R1T0','R1T1'))-min(counts[c][i] for c in ('R0T0','R0T1','R1T0','R1T1')) for i in range(16)]
        best=max(0,min(max(abs(counts['N_history'][n]-counts[c][i]) for c in ('R0T0','R0T1','R1T0','R1T1'))
                       for i in range(16) for n in range((i//4)*8,(i//4)*8+8)))
        match={'case_id':case['case_id'],'status':'PASS' if found else 'FAILED','token_tolerance':0,
            'active_variant':found[0] if found else None,'neutral_variant':found[1] if found else None,
            'best_active_spread':min(spreads),'best_neutral_maximum_absolute_difference':best,'measured_candidates':sum(map(len,counts.values()))}
        matches.append(match)
        if found:
            for condition in CONDITIONS:
                vi=0 if condition=='H_none' else found[1] if condition=='N_history' else found[0]
                variant=cb['conditions'][condition][vi];prompt=render(case,variant['text'])
                row={'case_id':case['case_id'],'persona_id':case['persona_id'],'condition':condition,
                    'history':variant['text'],'variant_id':vi,'history_fact_id':variant['fact_id'],'prompt':prompt,'prompt_sha256':text_hash(prompt),
                    'input_token_ids':ids[condition][vi],'input_tokens':counts[condition][vi],'output_budget':96,
                    'context_fit':counts[condition][vi]+96<=4096,'trusted_evidence_sha256':text_hash(case['trusted_evidence']),
                    'question_sha256':text_hash(case['question']),'context_sha256':text_hash(case['fixed_context']),
                    'semantic_approval':'OPEN','generation_authorized':False}
                require(row['context_fit'],'Context limit exceeded');selected.append(row)
                if condition!='H_none':
                    review.append({'case_id':case['case_id'],'condition':condition,'intended_role':CONDITIONS[condition],
                        'history':variant['text'],'trusted_evidence':case['trusted_evidence'],'question':case['question'],
                        'requested_date':case['requested_date'],'evaluation_date':case['evaluation_date'],
                        'required_answer':case['reference']['components'],'input_tokens':row['input_tokens'],
                        'matched_difference':row['input_tokens']-counts['R1T1'][found[0]],'prompt_sha256':row['prompt_sha256'],
                        **{'review_'+k:'' for k in ['relevance','time_scope','truth','no_answer_leakage','speaker_identity','coherence','no_style_instruction','neutrality_or_intended_manipulation','decision']},
                        'evidence_quotations':'','reviewer_notes':'','reviewer_id':'','reviewed_utc':''})
        print(json.dumps(match),flush=True)
    result={'version':'p1c_native_tokenizer_v1','identity':native.identity,'historical_id_probes':probes,
        'dataset_sha256':sha(DATA),'candidate_bank_sha256':sha(PUBLIC/'candidate_bank_v1.json'),
        'matches':matches,'native_calls':len(native.calls),'selected_prompts':len(selected),'new_generations':0,
        'matching_semantics':'Four active histories and neutral matched. H_none intentionally shorter. Equality does not establish semantic validity.'}
    write_json(PUBLIC/'tokenizer_validation_v1.json',result)
    write_json(PUBLIC/'candidate_token_attempts_v1.json',{'attempts':attempts})
    write_json(PUBLIC/'selected_prompts_v1.json',{'version':data['version'],'records':selected})
    if review:write_csv(PUBLIC/'history_semantic_review_v1.csv',review)
    return {'matched_cases':sum(r['status']=='PASS' for r in matches),'cases':len(matches),'prompts':len(selected),'new_generations':0}

if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run()))
