"""Bounded public model metadata only; no tensors, inference or selection by outcomes."""
import json
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
import p1d_budget_calibration as b

OUT=Path('docs/validation/p1d/instruct_preparation_v3')
REPOS=['Qwen/Qwen3.5-2B','bartowski/Qwen_Qwen3.5-2B-GGUF','unsloth/Qwen3.5-2B-GGUF','lmstudio-community/Qwen3.5-2B-GGUF']

def fetch(url):
    with urlopen(url,timeout=45) as response:
        data=response.read(2*1024*1024+1)
        if len(data)>2*1024*1024:raise ValueError('Metadata limit exceeded')
        return data,{'url':url,'resolved_url':response.url,'etag':response.headers.get('ETag'),'retrieved_utc':b.utc_now(),'bytes':len(data)}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for repo in REPOS:
        tag=repo.replace('/','__');path=OUT/(tag+'_api.json')
        if path.exists():continue
        try:
            data,meta=fetch('https://huggingface.co/api/models/'+repo+'?blobs=true')
            value=json.loads(data);rev=value['sha']
            path.write_bytes(data);meta['sha256']=b.sha256(path)
            b.save(OUT/(tag+'_provenance.json'),{**meta,'repository':repo,'revision':rev,'inference':0})
            card,cardmeta=fetch(f'https://huggingface.co/{repo}/raw/{rev}/README.md')
            cardpath=OUT/(tag+'_README.md');cardpath.write_bytes(card)
            b.save(OUT/(tag+'_card_provenance.json'),{**cardmeta,'sha256':b.sha256(cardpath)})
            print(json.dumps({'repo':repo,'revision':rev,'q4_files':[x for x in value.get('siblings',[]) if 'Q4_K_M' in x['rfilename']],'source_revision_mentions':[line for line in card.decode().splitlines() if any(k in line.lower() for k in ('revision','commit','quantiz','imatrix','llama.cpp','original model'))][:22]}),flush=True)
        except Exception as exc:
            print(json.dumps({'repo':repo,'error':type(exc).__name__,'message':str(exc)}),flush=True)
            raise

if __name__=='__main__':main()
