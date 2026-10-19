"""Acquire only the two pinned English Qwen2.5 artifacts; never load or infer."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import urllib.request

import p1_model_feasibility_recovery as metadata

ROOT = Path('.local/model_metadata/english_qwen25_15b_v1')
WEIGHTS = Path('models/gguf/english_qwen25_15b_v1')
RECEIPT = Path('docs/validation/p1/english_model_comparison_v1/artifact_receipt_v1.json')
FILES = ('README.md', 'LICENSE', 'config.json', 'generation_config.json',
         'tokenizer_config.json', 'tokenizer.json', 'vocab.json', 'merges.txt')
MODELS = {
    'base': {'name': 'Qwen2.5-1.5B', 'official_revision': '8faed761d45a263340a0528343f099c05c9a4323',
             'revision': '4d8150eba159047c0ad5f72a8473e4ad60419c4a', 'bytes': 986048544,
             'sha256': 'ea47cef917fa77a3458206d0848f81dd033dfb859bbb3b176bf6006d3b620814', 'eos': 151643},
    'instruct': {'name': 'Qwen2.5-1.5B-Instruct', 'official_revision': '989aa7980e4cf806f80c7fef2b1adb7bc71aa306',
                 'revision': '531cb7a27c3ad23c7d9c69d2d7a9de562ce55bcd', 'bytes': 986048960,
                 'sha256': 'f86985a0e8b549680da4cf43a037bb185c4ec8d1ee07cce52c1720f848b7c972', 'eos': 151645}}
require, sha = metadata.require, metadata.sha256


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), 'Existing evidence must not be overwritten')
    partial = path.with_name(path.name + '.partial')
    with partial.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    require(not path.exists(), 'Destination appeared during write')
    partial.rename(path)


def download(url, path, limit, expected_sha=None, expected_bytes=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), 'Existing artifact requires separate inspection')
    partial = path.with_name(path.name + '.partial')
    digest, count = hashlib.sha256(), 0
    with partial.open('xb') as stream:
        with urllib.request.urlopen(url, timeout=90) as response:
            require(response.status == 200, 'Unexpected HTTP response')
            while block := response.read(1024 * 1024):
                count += len(block)
                require(count <= limit, 'Download exceeded fixed byte limit')
                stream.write(block); digest.update(block)
        stream.flush(); os.fsync(stream.fileno())
    require(expected_bytes is None or count == expected_bytes, 'Artifact size mismatch')
    require(expected_sha is None or digest.hexdigest() == expected_sha, 'Artifact hash mismatch')
    require(not path.exists(), 'Destination appeared during download')
    partial.rename(path)
    return {'path': path.as_posix(), 'url': url, 'bytes': count, 'sha256': digest.hexdigest()}


def tensor_directory(path, header):
    require(0 < header['tensor_count'] <= 10000, 'Tensor count bounds')
    layout = []
    with path.open('rb') as stream:
        stream.seek(header['metadata_bytes_read'])
        def read(size):
            value = stream.read(size)
            require(len(value) == size, 'Short tensor directory')
            return value
        for _ in range(header['tensor_count']):
            length = struct.unpack('<Q', read(8))[0]
            require(0 < length <= 1024, 'Tensor name bounds')
            name = read(length).decode('utf-8')
            dimensions = struct.unpack('<I', read(4))[0]
            require(1 <= dimensions <= 4, 'Tensor dimension bounds')
            shape = list(struct.unpack('<' + 'Q' * dimensions, read(8 * dimensions)))
            kind, _offset = struct.unpack('<IQ', read(12))
            require(all(0 < d <= 1000000 for d in shape) and kind < 64, 'Tensor shape/type bounds')
            layout.append({'name': name, 'shape': shape, 'type': kind})
        directory_bytes = stream.tell() - header['metadata_bytes_read']
    require(len({x['name'] for x in layout}) == len(layout), 'Duplicate tensor names')
    encoded = json.dumps(sorted(layout, key=lambda x: x['name']), sort_keys=True, separators=(',', ':')).encode()
    return {'name_shape_type_sha256': hashlib.sha256(encoded).hexdigest(),
            'type_counts': dict(sorted(Counter(str(x['type']) for x in layout).items())),
            'directory_bytes_read': directory_bytes, 'tensor_data_read': False}


def inspect(variant, weight, directory):
    spec = MODELS[variant]
    gguf, header = metadata.gguf_metadata(weight)
    expected = {'general.architecture': 'qwen2', 'general.file_type': 15,
                'qwen2.block_count': 28, 'qwen2.embedding_length': 1536,
                'qwen2.feed_forward_length': 8960, 'tokenizer.ggml.model': 'gpt2',
                'qwen2.attention.head_count': 12, 'qwen2.attention.head_count_kv': 2,
                'tokenizer.ggml.eos_token_id': spec['eos']}
    require(all(gguf.get(k) == v for k, v in expected.items()), 'GGUF architecture/quantization/EOS mismatch')
    require(header['tensor_count'] > 0, 'Missing tensor declarations')
    token = metadata.load(directory / 'tokenizer.json')
    official = metadata.load(directory / 'tokenizer_config.json')
    vocab = dict(token['model']['vocab'])
    vocab.update({entry['content']: entry['id'] for entry in token['added_tokens']})
    actual = gguf['tokenizer.ggml.tokens']
    require(len(actual) == metadata.load(directory / 'config.json')['vocab_size'] and
            gguf.get('qwen2.context_length', 0) >= 2048, 'Vocabulary/context bounds mismatch')
    require(all(0 <= i < len(actual) and actual[i] == text for text, i in vocab.items()), 'Official token IDs differ')
    merges = [' '.join(m) if isinstance(m, list) else m for m in token['model']['merges']]
    require(merges == gguf['tokenizer.ggml.merges'], 'Official merges differ')
    require(sha(directory / 'LICENSE') == '832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e', 'License changed')
    return {'header': header, 'verified_fields': expected, 'official_token_ids_matched': len(vocab),
            'gguf_token_count': len(actual), 'merge_count': len(merges),
            'gguf_add_bos_token': gguf.get('tokenizer.ggml.add_bos_token'),
            'official_add_bos_token': official.get('add_bos_token'),
            'gguf_context_length': gguf.get('qwen2.context_length'),
            'official_template_sha256': hashlib.sha256(official['chat_template'].encode()).hexdigest(),
            'embedded_template_sha256': hashlib.sha256(gguf.get('tokenizer.chat_template', '').encode()).hexdigest(),
            'embedded_template_equals_official': gguf.get('tokenizer.chat_template') == official['chat_template'],
            'tensor_layout': tensor_directory(weight, header)}


def acquire():
    require(not RECEIPT.exists() and not ROOT.exists() and not WEIGHTS.exists(), 'Preserve prior attempt; no automatic retry')
    write(ROOT / 'acquisition_claim_v1.json', {'started_utc': metadata.utc_now(), 'maximum_download_operations': 22,
          'automatic_retries': 0, 'parallel_downloads': 1, 'models': MODELS, 'new_model_generations': 0})
    results, phase = {}, 'metadata'
    try:
        for variant, spec in MODELS.items():
            phase = variant + '_official_metadata'
            directory = ROOT / variant; records = []
            for name in FILES:
                url = f"https://huggingface.co/Qwen/{spec['name']}/resolve/{spec['official_revision']}/{name}"
                records.append(download(url, directory / name, 8 * 1024**2))
            repo = f"mradermacher/{spec['name']}-GGUF"
            api = f"https://huggingface.co/api/models/{repo}/revision/{spec['revision']}?blobs=true"
            records.append(download(api, directory / 'quantization_api.json', 2 * 1024**2))
            info = metadata.load(directory / 'quantization_api.json')
            require(info['sha'] == spec['revision'], 'Remote repository revision mismatch')
            filename = spec['name'] + '.Q4_K_M.gguf'
            remote = next(f for f in info['siblings'] if f['rfilename'] == filename)
            require(remote['size'] == spec['bytes'] and remote['lfs']['sha256'] == spec['sha256'], 'Pinned remote file mismatch')
            prefix = f"https://huggingface.co/{repo}/resolve/{spec['revision']}/"
            records.append(download(prefix + 'README.md', directory / 'quantization_README.md', 2 * 1024**2))
            phase = variant + '_weight'
            weight = WEIGHTS / variant / filename
            artifact = download(prefix + filename, weight, spec['bytes'], spec['sha256'], spec['bytes'])
            phase = variant + '_metadata_verification'
            comparison = inspect(variant, weight, directory)
            write(directory / 'gguf_metadata_comparison_v1.json', comparison)
            results[variant] = {'model_file': weight.as_posix(), 'model_sha256': spec['sha256'], 'artifact': artifact,
                                'upstream_revision': spec['official_revision'], 'artifact_revision': spec['revision'],
                                'quantization': 'Q4_K_M', 'license': 'Apache-2.0', 'metadata_files': records,
                                'comparison': comparison}
        equal = {name: sha(ROOT / 'base' / name) == sha(ROOT / 'instruct' / name)
                 for name in ('tokenizer.json', 'vocab.json', 'merges.txt')}
        require(all(equal.values()), 'Official Base/Instruct tokenization differs')
        require(results['base']['comparison']['header']['tensor_count'] ==
                results['instruct']['comparison']['header']['tensor_count'], 'Paired tensor counts differ')
        require(results['base']['comparison']['tensor_layout']['name_shape_type_sha256'] ==
                results['instruct']['comparison']['tensor_layout']['name_shape_type_sha256'], 'Paired tensor layouts differ')
        receipt = {'schema': 'english_qwen25_15b_artifact_receipt_v1', 'status': 'ARTIFACTS_VERIFIED_NOT_EXECUTION_GO',
                   'completed_utc': metadata.utc_now(), 'models': results, 'official_tokenizer_files_equal': equal,
                   'paired_tensor_name_shape_type_layout_equal': True,
                   'conversion_provenance': 'PARTIAL: published static artifacts; exact upstream conversion revision/command unverified',
                   'source_hashes': {p.as_posix(): sha(p) for p in (Path('tools') / Path(__file__).name,
                                     Path('tools') / Path(metadata.__file__).name,
                                     Path('tests/test_english_sfh_model_artifacts_v1.py'))},
                   'ram_preflight_performed': False, 'new_model_generations': 0}
        write(RECEIPT, receipt)
        return receipt
    except BaseException as exc:
        write(ROOT / 'acquisition_failure_v1.json', {'failed_utc': metadata.utc_now(), 'phase': phase,
              'error_type': type(exc).__name__, 'completed_variants': list(results),
              'error_message': re.sub(r'https?://\S+', '[URL omitted]', str(exc))[:500],
              'partial_files_preserved': True, 'automatic_retry_allowed': False, 'new_model_generations': 0})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', required=True)
    parser.parse_args()
    print(json.dumps(acquire(), indent=2, sort_keys=True))
