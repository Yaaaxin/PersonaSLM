import hashlib
import io
from pathlib import Path
import struct

import pytest

import english_sfh_model_artifacts_v1 as artifacts


class Response(io.BytesIO):
    status = 200

    def read(self, size=-1):
        assert 0 < size <= 1024 * 1024
        return super().read(size)


def test_download_streams_and_verifies_before_promotion(tmp_path, monkeypatch):
    content = b'authored fixture' * 100000
    monkeypatch.setattr(artifacts.urllib.request, 'urlopen', lambda *a, **k: Response(content))
    path = tmp_path / 'fixture.gguf'
    result = artifacts.download('https://example.invalid/fixed', path, len(content),
                                hashlib.sha256(content).hexdigest(), len(content))
    assert path.read_bytes() == content and result['bytes'] == len(content)
    assert not path.with_name(path.name + '.partial').exists()
    with pytest.raises(ValueError, match='Existing artifact'):
        artifacts.download('https://example.invalid/fixed', path, len(content))


@pytest.mark.parametrize('failure', ['hash', 'size', 'cap', 'network'])
def test_failed_download_preserves_partial_and_never_retries(tmp_path, monkeypatch, failure):
    calls = []
    def open_url(*args, **kwargs):
        calls.append(args)
        if failure == 'network':
            raise OSError('authored network failure')
        return Response(b'fixture')
    monkeypatch.setattr(artifacts.urllib.request, 'urlopen', open_url)
    path = tmp_path / 'fixture.gguf'
    with pytest.raises((ValueError, OSError)):
        artifacts.download('https://example.invalid/fixed', path, 3 if failure == 'cap' else 20,
                           '0' * 64 if failure == 'hash' else None, 9 if failure == 'size' else None)
    assert len(calls) == 1 and not path.exists()
    assert path.with_name(path.name + '.partial').exists()
    with pytest.raises(FileExistsError):
        artifacts.download('https://example.invalid/fixed', path, 20)
    assert len(calls) == 1


def test_prior_attempt_blocks_network(tmp_path, monkeypatch):
    root = tmp_path / 'private'; root.mkdir()
    monkeypatch.setattr(artifacts, 'ROOT', root)
    monkeypatch.setattr(artifacts, 'RECEIPT', tmp_path / 'receipt.json')
    monkeypatch.setattr(artifacts, 'WEIGHTS', tmp_path / 'models')
    monkeypatch.setattr(artifacts.urllib.request, 'urlopen', lambda *a, **k: pytest.fail('network forbidden'))
    with pytest.raises(ValueError, match='Preserve prior attempt'):
        artifacts.acquire()


def test_only_two_pinned_non_bf16_artifacts_are_defined():
    assert set(artifacts.MODELS) == {'base', 'instruct'}
    assert all(s['bytes'] < 1024**3 and len(s['sha256']) == 64 and len(s['revision']) == 40
               for s in artifacts.MODELS.values())
    assert not any('safetensors' in name or name.endswith('.gguf') for name in artifacts.FILES)


@pytest.mark.parametrize('corruption', [None, 'architecture', 'quantization', 'eos', 'token', 'merge'])
def test_metadata_identity_uses_official_ids_not_just_model_name(tmp_path, monkeypatch, corruption):
    gguf = {'general.architecture': 'qwen2', 'general.file_type': 15,
            'qwen2.block_count': 28, 'qwen2.embedding_length': 1536,
            'qwen2.feed_forward_length': 8960, 'qwen2.attention.head_count': 12,
            'qwen2.attention.head_count_kv': 2, 'qwen2.context_length': 32768,
            'tokenizer.ggml.model': 'gpt2', 'tokenizer.ggml.eos_token_id': 151643,
            'tokenizer.ggml.tokens': ['a', 'b'], 'tokenizer.ggml.merges': ['a b'],
            'tokenizer.chat_template': 'authored fixture'}
    changes = {'architecture': ('general.architecture', 'qwen3'),
               'quantization': ('general.file_type', 7), 'eos': ('tokenizer.ggml.eos_token_id', 151645),
               'token': ('tokenizer.ggml.tokens', ['b', 'a']), 'merge': ('tokenizer.ggml.merges', [])}
    if corruption:
        key, value = changes[corruption]; gguf[key] = value
    def load(path):
        return {'tokenizer.json': {'model': {'vocab': {'a': 0}, 'merges': [['a', 'b']]},
                                  'added_tokens': [{'content': 'b', 'id': 1}]},
                'tokenizer_config.json': {'chat_template': 'authored fixture', 'add_bos_token': False},
                'config.json': {'vocab_size': 2}}[path.name]
    monkeypatch.setattr(artifacts.metadata, 'gguf_metadata', lambda p: (gguf, {'tensor_count': 1}))
    monkeypatch.setattr(artifacts, 'tensor_directory', lambda *args: {'tensor_data_read': False})
    monkeypatch.setattr(artifacts.metadata, 'load', load)
    monkeypatch.setattr(artifacts, 'sha', lambda p: '832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e')
    if corruption:
        with pytest.raises(ValueError):
            artifacts.inspect('base', tmp_path / 'model.gguf', tmp_path)
    else:
        result = artifacts.inspect('base', tmp_path / 'model.gguf', tmp_path)
        assert result['official_token_ids_matched'] == 2 and result['embedded_template_equals_official']


def tensor(name, shape, kind=12, offset=0):
    name = name.encode()
    return (struct.pack('<Q', len(name)) + name + struct.pack('<I', len(shape)) +
            struct.pack('<' + 'Q' * len(shape), *shape) + struct.pack('<IQ', kind, offset))


def test_tensor_directory_checks_sorted_layout_without_tensor_data(tmp_path):
    first = tensor('b', [32, 64]) + tensor('a', [64], 0, 256)
    second = tensor('a', [64], 0, 1024) + tensor('b', [32, 64], 12, 2048)
    results = []
    for i, directory in enumerate((first, second)):
        path = tmp_path / str(i)
        path.write_bytes(b'header' + directory + b'NEVER READ TENSOR PAYLOAD')
        results.append(artifacts.tensor_directory(path, {'metadata_bytes_read': 6, 'tensor_count': 2}))
    assert results[0]['name_shape_type_sha256'] == results[1]['name_shape_type_sha256']
    assert results[0]['directory_bytes_read'] == len(first)
    assert results[0]['type_counts'] == {'0': 1, '12': 1} and not results[0]['tensor_data_read']


@pytest.mark.parametrize('body', [b'bad', struct.pack('<Q', 1025), tensor('a', [0]),
                                 tensor('a', [2], 65), tensor('a', [2]) + tensor('a', [2])])
def test_invalid_tensor_directory_fails_closed(tmp_path, body):
    path = tmp_path / 'directory'; path.write_bytes(body)
    with pytest.raises(ValueError):
        artifacts.tensor_directory(path, {'metadata_bytes_read': 0,
                                          'tensor_count': 2 if body == tensor('a', [2]) * 2 else 1})
