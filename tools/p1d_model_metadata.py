"""Fetch only three small pinned official metadata files; never weights/inference."""
from datetime import datetime, timezone
from pathlib import Path
import json
import urllib.request
from p1d_design import write, sha

REVISION = '965dcc54bc9c0591873df0e9869c056a54d323d1'
FILES = ('config.json', 'tokenizer_config.json', 'chat_template.jinja')
DEST = Path('docs/validation/p1d/development_readiness_v1/official_instruct_metadata')

def main():
    if DEST.exists() and any(DEST.iterdir()):
        raise FileExistsError('Preserve previous metadata download')
    DEST.mkdir(parents=True, exist_ok=True)
    records = []
    for name in FILES:
        url = f'https://huggingface.co/Qwen/Qwen3.5-2B/resolve/{REVISION}/{name}'
        with urllib.request.urlopen(url, timeout=40) as response:
            content = response.read(131073)
            if len(content) > 131072:
                raise ValueError('Metadata exceeded 128 KiB cap')
            record = {'file': name, 'url': url, 'resolved_url': response.url,
                'etag': response.headers.get('ETag'), 'bytes': len(content),
                'software_retrieved_utc': datetime.now(timezone.utc).isoformat()}
        if name.endswith('.json'):
            json.loads(content)
        with (DEST / name).open('xb') as f:
            f.write(content)
        record['sha256'] = sha(DEST / name)
        records.append(record)
    cfg = json.loads((DEST / 'config.json').read_text(encoding='utf-8'))
    tok = json.loads((DEST / 'tokenizer_config.json').read_text(encoding='utf-8'))
    write(DEST / 'provenance_v1.json', {'official_model': 'Qwen/Qwen3.5-2B', 'revision': REVISION,
        'files': records, 'code_sha256': sha(__file__), 'model_type': cfg.get('model_type'),
        'text_config': cfg.get('text_config'), 'eos_token': tok.get('eos_token'),
        'tokenizer_class': tok.get('tokenizer_class'), 'local_gguf_sha256': None,
        'full_tokenizer_vocabulary_sha256': None, 'backend_runtime_compatibility': 'NOT_TESTED',
        'weights_downloaded': False, 'model_generations': 0,
        'limitation': 'Official metadata identity only; not local GGUF, tokenizer equivalence, RAM, latency or generation validation'})
    print({'metadata_files': len(records), 'total_bytes': sum(r['bytes'] for r in records), 'weights_downloaded': False, 'model_generations': 0})

if __name__ == '__main__':
    main()
