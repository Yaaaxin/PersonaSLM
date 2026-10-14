"""Official JSON tokenizer on rendered candidates; no Instruct weights or generation."""
import json
import os
from pathlib import Path
import sys
os.environ['TOKENIZERS_PARALLELISM']='false'
RUNTIME=Path('results/p1d_final_preparation/v1/tokenizer_runtime')
sys.path.insert(0,str(RUNTIME.resolve()))
from tokenizers import Tokenizer, __version__
from p1d_design import read, write, sha, th

OUT=Path('docs/validation/p1d/final_preparation_v1')
SOURCE=Path('docs/validation/p1d/scientific_validation_v1/instruct_rendered_candidates_v1.json')
TOKENIZER=Path('results/p1d_final_preparation/v1/official_tokenizer/tokenizer.json')
NATIVE=Path('docs/validation/p1d/independent_candidates_v4/native_tokenizer_validation_v1.json')

def main():
    if __version__!='0.22.2':raise ValueError('Tokenizer runtime changed')
    t=Tokenizer.from_file(str(TOKENIZER));t.no_truncation();t.no_padding()
    source=read(SOURCE);base=read('docs/validation/p1d/independent_candidates_v4/base_candidate_prompts_v1.json')
    if isinstance(base,dict):base=base['rows']
    bm={r['prompt_sha256']:r for r in base};nm={r['prompt_sha256']:r for r in read(NATIVE)['rows']};rows=[]
    for r in source['rows']:
        prompt=r['rendered_prompt']
        if th(prompt)!=r['rendered_prompt_sha256']:raise ValueError('Rendered source differs')
        encoded=t.encode(prompt,add_special_tokens=False)
        recovered=t.decode(encoded.ids,skip_special_tokens=False)
        original=bm[r['base_prompt_sha256']]
        native_equal=th(str(t.encode(original['prompt'],add_special_tokens=False).ids))==nm[r['base_prompt_sha256']]['token_ids_sha256']
        if recovered!=prompt:raise ValueError('Official tokenizer round-trip mismatch')
        rows.append({'planning_id':r['planning_id'],'case_id':r['case_id'],'condition':r['condition'],
            'rendered_prompt_sha256':r['rendered_prompt_sha256'],'official_json_input_token_ids':encoded.ids,
            'official_json_token_count':len(encoded.ids),'token_ids_sha256':th(str(encoded.ids)),
            'roundtrip_exact':True,'base_same_body_native_ids_equal':native_equal,
            'context_remaining_at_256':4096-256-len(encoded.ids),'native_instruct_gguf_verified':False,'generation_authorized':False})
    write(OUT/'instruct_official_tokenizer_records_v1.json',{'version':'p1d_official_json_tokenization_v1','rows':rows})
    report={'version':'p1d_instruct_official_tokenizer_check_v1','records':len(rows),'runtime':__version__,
        'input_token_range':[min(r['official_json_token_count'] for r in rows),max(r['official_json_token_count'] for r in rows)],
        'exact_roundtrips':sum(r['roundtrip_exact'] for r in rows),
        'base_native_equivalence_on_matched_body':sum(r['base_same_body_native_ids_equal'] for r in rows),
        'minimum_remaining_context_at_256':min(r['context_remaining_at_256'] for r in rows),
        'special_handling':'Official rendered chat markers parsed as added tokens; encode(add_special_tokens=False), no truncation/padding; decode retains special tokens.',
        'sources':{str(p):sha(p) for p in (SOURCE,TOKENIZER,NATIVE,Path(__file__))},
        'runtime_file_hashes':{p.as_posix():sha(p) for p in (RUNTIME/'tokenizers').rglob('*') if p.is_file() and p.suffix in ('.pyd','.py')},
        'shared_vocab_defined_ids_equal':248070,'base_extra_ids_without_official_definition':250,'merges_equal':247587,
        'local_instruct_model_ready':False,'new_generations':0,
        'limits':'Upstream JSON tokenizer only; final quantized Instruct tokenizer, backend/minja template equivalence, stop behavior, RAM and latency still need verification. No substitution of these IDs into an executable manifest.'}
    write(OUT/'instruct_official_tokenizer_check_v1.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('sources','runtime_file_hashes')},indent=2))

if __name__=='__main__':main()
