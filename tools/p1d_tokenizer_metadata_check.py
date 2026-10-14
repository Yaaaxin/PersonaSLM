"""Bounded official tokenizer download and GGUF metadata comparison; no weights/inference."""
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import urllib.request
from p1d_design import write, sha

REV='965dcc54bc9c0591873df0e9869c056a54d323d1'
URL=f'https://huggingface.co/Qwen/Qwen3.5-2B/resolve/{REV}/tokenizer.json'
DEST=Path('results/p1d_final_preparation/v1/official_tokenizer')
REPORT=Path('docs/validation/p1d/final_preparation_v1/instruct_tokenizer_metadata_comparison_v1.json')

def metadata(path):
    scalar={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
    with Path(path).open('rb') as f:
        def unpack(fmt):
            n=struct.calcsize('<'+fmt);raw=f.read(n)
            if len(raw)!=n:raise ValueError('Short metadata')
            return struct.unpack('<'+fmt,raw)[0]
        def string():
            n=unpack('Q')
            if n>32*1024**2:raise ValueError('Unbounded metadata string')
            return f.read(n).decode('utf-8')
        def value(kind):
            if f.tell()>64*1024**2:raise ValueError('Metadata read exceeds cap')
            if kind in scalar:return unpack(scalar[kind])
            if kind==8:return string()
            if kind==9:
                sub=unpack('I');n=unpack('Q')
                if n>1000000 or sub==9:raise ValueError('Invalid/unbounded array')
                return [value(sub) for _ in range(n)]
            raise ValueError('Unknown GGUF metadata type')
        if f.read(4)!=b'GGUF' or unpack('I') not in (2,3):raise ValueError('Not supported GGUF')
        tensors=unpack('Q');n=unpack('Q');result={}
        if n>10000:raise ValueError('Too many metadata keys')
        for _ in range(n):
            key=string();result[key]=value(unpack('I'))
        return result,{'metadata_bytes_read':f.tell(),'tensor_count':tensors,'tensor_data_read':False}

def main():
    DEST.mkdir(parents=True,exist_ok=True);target=DEST/'tokenizer.json'
    if not target.exists():
        try:
            with urllib.request.urlopen(URL,timeout=60) as r:
                data=r.read(20*1024**2+1)
                if len(data)>20*1024**2:raise ValueError('Official tokenizer exceeds 20 MiB cap')
                provenance={'url':URL,'resolved_url':r.url,'etag':r.headers.get('ETag'),'bytes':len(data),
                    'retrieved_utc':datetime.now(timezone.utc).isoformat(),'revision':REV}
            json.loads(data)
            with target.open('xb') as f:f.write(data)
            write(DEST/'download_provenance_v1.json',provenance)
        except Exception as exc:
            failure=DEST/f'failed_download_{len(list(DEST.glob("failed_download_*.json")))+1}.json'
            write(failure,{'url':URL,'error_type':type(exc).__name__,'error':str(exc),'software_utc':datetime.now(timezone.utc).isoformat(),'generation_requests':0})
            raise
    tok=json.loads(target.read_text(encoding='utf-8'));gg,read_info=metadata('models/gguf/Qwen3.5-2B-Base.Q4_K_M.gguf')
    vocab=dict(tok['model']['vocab'])
    for t in tok['added_tokens']:
        if t['content'] in vocab and vocab[t['content']]!=t['id']:raise ValueError('Conflicting official token IDs')
        vocab[t['content']]=t['id']
    byid={v:k for k,v in vocab.items()};base=gg['tokenizer.ggml.tokens']
    mismatch=[{'id':i,'base':s,'official_instruct':byid.get(i)} for i,s in enumerate(base) if byid.get(i)!=s]
    official_merges=tok['model'].get('merges',[])
    official_merges=[' '.join(m) if isinstance(m,list) else m for m in official_merges]
    report={'version':'p1d_instruct_tokenizer_metadata_comparison_v1','official_model':'Qwen/Qwen3.5-2B','revision':REV,
        'official_tokenizer_path':target.as_posix(),'official_tokenizer_sha256':sha(target),
        'base_gguf_sha256':'ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994',
        'base_token_count':len(base),'official_total_token_count':len(byid),'id_string_mismatch_count':len(mismatch),
        'id_string_mismatches':mismatch,'extra_official_ids':sorted(set(byid)-set(range(len(base)))),
        'merge_count_base':len(gg.get('tokenizer.ggml.merges',[])),'merge_count_official':len(official_merges),
        'merges_identical':gg.get('tokenizer.ggml.merges')==official_merges,
        'base_special_metadata':{k:v for k,v in gg.items() if k.startswith('tokenizer.') and not isinstance(v,list) and k!='tokenizer.chat_template'},
        'official_pre_tokenizer':tok.get('pre_tokenizer'),'official_normalizer':tok.get('normalizer'),'official_post_processor':tok.get('post_processor'),
        'read_info':read_info,'weights_downloaded':False,'generation_requests':0,'local_instruct_gguf':None,
        'conclusion':'Static vocabulary/merge comparison only. Native Instruct tokenization, special-token insertion, template runtime, quantized model loading and EOG termination remain unverified.',
        'code_sha256':sha(__file__)}
    write(REPORT,report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('id_string_mismatches','base_special_metadata','official_pre_tokenizer','official_normalizer','official_post_processor')},indent=2))

if __name__=='__main__':main()
