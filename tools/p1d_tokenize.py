"""Measure developmental prompts with pinned GGUF vocabulary; no model generation."""
from pathlib import Path
from p1d_design import OUT,read,write,sha,CELLS
import p1c_tokenize as native_module

def main():
    target=OUT/'tokenizer_validation_v1.json'
    if target.exists():raise FileExistsError(target)
    native_module.LOCAL=Path('results/p1d_preparation/v1/tokenizer')
    native=native_module.NativeTokenizer()
    prompts=read(OUT/'development_prompts_v3.json');rows=[]
    for r in prompts:
        ids=native.tokens(r['prompt'])
        rows.append({'case_id':r['case_id'],'condition':r['condition'],'prompt_sha256':r['prompt_sha256'],
            'input_token_ids':ids,'input_tokens':len(ids),'context_fit_96':len(ids)+96<=4096})
    matches=[]
    for case in sorted({r['case_id'] for r in rows}):
        counts={r['condition']:r['input_tokens'] for r in rows if r['case_id']==case}
        active=[counts[c] for c in CELLS[:4]]
        matches.append({'case_id':case,'counts':counts,'active_equal':len(set(active))==1,
            'control_equal':len(set(active+[counts['D_procedural']]))==1,'active_spread':max(active)-min(active)})
    write(target,{'identity':native.identity,'rows':rows,'matches':matches,'source_sha256':sha(OUT/'development_prompts_v3.json'),
        'code_sha256':sha(__file__),'new_generations':0,'semantic_neutrality':'NOT_ESTABLISHED','context_fit_all':all(r['context_fit_96'] for r in rows)})
    print({'prompts':len(rows),'tokens_range':[min(r['input_tokens'] for r in rows),max(r['input_tokens'] for r in rows)],
        'active_equal':sum(r['active_equal'] for r in matches),'control_equal':sum(r['control_equal'] for r in matches),
        'context_fit_all':all(r['context_fit_96'] for r in rows),'new_generations':0})

if __name__=='__main__':main()
