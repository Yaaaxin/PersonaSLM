"""Prepare one disclosed community GGUF candidate; download/metadata only, never inference."""
import hashlib
import json
from pathlib import Path
import shutil
import time
from urllib.request import urlopen
import p1d_budget_calibration as b
from p1d_tokenizer_metadata_check import metadata

REPO='lmstudio-community/Qwen3.5-2B-GGUF'
REV='bb84e11355a036e28f080c7793fa6d22b7c4e344'
NAME='Qwen3.5-2B-Q4_K_M.gguf'
SHA='0bfe35afc9f05b7fac3fa04925e051ac7939a42a8a17ea11afc99701bea826cc'
SIZE=1270808032
UPSTREAM='965dcc54bc9c0591873df0e9869c056a54d323d1'
OUT=Path('docs/validation/p1d/instruct_preparation_v3')
DEST=Path('models/gguf/instruct_candidates/lmstudio-bb84e113')/NAME

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    api=b.load(OUT/'lmstudio-community__Qwen3.5-2B-GGUF_api.json')
    file=next(x for x in api['siblings'] if x['rfilename']==NAME)
    b.require(api['sha']==REV and file['lfs']['sha256']==SHA and file['size']==SIZE,'Candidate binding changed')
    pinned=OUT/'official_pinned_revision_api.json'
    if not pinned.exists():
        url=f'https://huggingface.co/api/models/Qwen/Qwen3.5-2B/revision/{UPSTREAM}?blobs=true'
        with urlopen(url,timeout=45) as r:data=r.read(2*1024**2+1)
        b.require(len(data)<=2*1024**2 and json.loads(data)['sha']==UPSTREAM,'Pinned upstream mismatch')
        pinned.write_bytes(data)
    if not DEST.exists():
        b.require(shutil.disk_usage('.').free>4*1024**3,'Insufficient disk reserve')
        DEST.parent.mkdir(parents=True,exist_ok=True);part=DEST.with_suffix('.gguf.partial')
        b.require(not part.exists(),'Partial download preserved; inspect before explicit resume')
        url=f'https://huggingface.co/{REPO}/resolve/{REV}/{NAME}'
        started=time.monotonic();h=hashlib.sha256();count=0
        try:
            with urlopen(url,timeout=60) as response,part.open('xb') as f:
                download={'url':url,'etag':response.headers.get('ETag'),'software_started_utc':b.utc_now()}
                while chunk:=response.read(1024**2):
                    count+=len(chunk);b.require(count<=SIZE and time.monotonic()-started<20*60,'Bounded download exceeded')
                    f.write(chunk);h.update(chunk)
                    if count%(128*1024**2)==0:print(json.dumps({'downloaded_bytes':count,'expected_bytes':SIZE}),flush=True)
            b.require(count==SIZE and h.hexdigest()==SHA,'Downloaded GGUF size/hash mismatch')
            part.rename(DEST)
            b.save(OUT/'candidate_download_v1.json',{**download,'file':DEST.as_posix(),'bytes':count,'sha256':SHA,
                'software_finished_utc':b.utc_now(),'elapsed_seconds':time.monotonic()-started,'model_generations':0})
        except Exception as exc:
            b.save(OUT/f'candidate_download_failure_{len(list(OUT.glob("candidate_download_failure_*.json")))+1}.json',
                {'error':str(exc),'type':type(exc).__name__,'bytes':count,'software_utc':b.utc_now(),'generations':0})
            raise
    b.require(DEST.stat().st_size==SIZE and b.sha256(DEST)==SHA,'Local candidate mismatch')
    gg,read=metadata(DEST)
    tok=b.load('results/p1d_final_preparation/v1/official_tokenizer/tokenizer.json')
    vocab=dict(tok['model']['vocab']);vocab.update({t['content']:t['id'] for t in tok['added_tokens']})
    shared=[{'id':i,'official':s,'candidate':gg['tokenizer.ggml.tokens'][i]} for s,i in vocab.items() if gg['tokenizer.ggml.tokens'][i]!=s]
    merges=[' '.join(x) if isinstance(x,list) else x for x in tok['model']['merges']]
    template=gg.get('tokenizer.chat_template','')
    official=Path('docs/validation/p1d/development_readiness_v1/official_instruct_metadata/chat_template.jinja').read_text(encoding='utf-8')
    b.save(OUT/'local_candidate_metadata_v1.json',{'version':'p1d_instruct_candidate_metadata_v1','repository':REPO,'revision':REV,
        'file':DEST.as_posix(),'sha256':SHA,'bytes':SIZE,'status':'PREPARED_CANDIDATE_NOT_ADOPTED',
        'selection_reason':'Reported b8185 quantizer, standard Q4_K_M text tensor size close to pinned Base, no MTP addition advertised; selected before inspecting any Instruct output.',
        'source_upstream_revision':'NOT_CERTIFIED_BY_DISTRIBUTOR','intended_official_revision':UPSTREAM,
        'quantizer_provenance':'Distributor reports llama.cpp b8185; full conversion command and source-weight revision are not supplied.',
        'static_metadata':{k:v for k,v in gg.items() if not isinstance(v,list)},'read':read,
        'official_shared_token_ids':len(vocab),'shared_id_mismatches':shared,'merges_equal':gg.get('tokenizer.ggml.merges')==merges,
        'embedded_template_sha256':b.th(template),'official_template_sha256':b.th(official),'embedded_template_equals_official':template==official,
        'runtime_loaded':False,'generation_requests':0,'native_stop_behavior':'NOT_MEASURED',
        'limitations':['Local byte identity is verified; conversion lineage is only partially verified.','No automatic replacement of the approved model arm.','RAM and latency require separately authorized generation; static metadata is not runtime success.']})
    print(json.dumps({'file':DEST.as_posix(),'sha256':SHA,'shared_id_mismatches':len(shared),'template_equal':template==official,'inference':0}))

if __name__=='__main__':main()
