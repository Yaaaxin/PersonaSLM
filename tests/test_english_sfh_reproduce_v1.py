"""Authored arithmetic/transport fixtures only, never research observations."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path

import pytest

import english_sfh_reproduce_v1 as independent


def rows():
    result = []
    coefficients = dict(zip(independent.CONTRAST_MASKS.values(), range(1, 8)))
    for speaker in range(2):
        for case in range(2):
            values = {}
            for index in range(8):
                value = 100 + speaker + case
                for mask, coefficient in coefficients.items():
                    sign = 1
                    for bit in range(3):
                        if mask & (1 << bit):
                            sign *= 1 if index & (1 << bit) else -1
                    value += coefficient * sign
                values[f'C{index}'] = value
            values.update(M_STYLE=values['C7'] - 2, N_STYLE=values['C7'] - 3)
            for condition, value in values.items():
                result.append({'speaker_id': f'AUTHORED{speaker}', 'case_id': f'CASE{case}',
                               'condition': condition, 'measurements': dict.fromkeys(independent.METRICS, value)})
    return result


def test_all_seven_contrasts_and_three_style_comparisons():
    estimates = independent.estimates(rows())
    for metric in independent.METRICS:
        for index, name in enumerate(independent.CONTRAST_MASKS, 1):
            result = estimates['factorial_effects'][metric][name]
            assert result['n'] == 2 and result['mean'] == 2 * index
            assert result['leave_one_speaker_out_mean_range'] == [2 * index, 2 * index]
        controls = estimates['style_controls'][metric]
        assert controls['correct_minus_mismatched']['mean'] == 2
        assert controls['correct_minus_pooled']['mean'] == 3
        assert controls['correct_minus_no_style_at_FH']['mean'] == 34


def test_missing_one_context_excludes_speaker_not_all_other_endpoints():
    data = rows()
    data[0]['measurements']['output_words'] = None
    estimates = independent.estimates(data)
    assert estimates['factorial_effects']['output_words']['S']['n'] == 1
    assert estimates['factorial_effects']['output_words']['S']['incomplete_speakers'] == 1
    assert estimates['style_controls']['output_words']['correct_minus_mismatched']['n'] == 2
    assert estimates['factorial_effects']['output_tokens']['S']['n'] == 2
    assert estimates['condition_summary']['output_words']['C0']['missing_or_inapplicable'] == 1


def test_short_fivegram_endpoint_inapplicable_and_full_user_overlap():
    request = {'messages': [{'content': 'The whole user message has a copied phrase here.'}]}
    response = {'content': 'a short reply', 'tokens_predicted': 3, 'stop_type': 'eos'}
    assert independent.measurements(request, response, 1)['source_fivegram_coverage'] is None
    response['content'] = 'The whole user message has a copied phrase here.'
    assert independent.measurements(request, response, 1)['source_fivegram_coverage'] == 1


def request(index):
    value = {'request_id': f'AUTHORED{index}', 'speaker_id': 'SYNTHETIC', 'case_id': 'AUTHORED',
             'condition': f'C{index}', 'phase': 'MAIN', 'prompt': 'Authored prompt.',
             'messages': [{'content': 'Authored prompt.'}], 'input_token_ids': [1, 2], 'input_tokens': 2,
             'input_token_ids_sha256': independent.value_hash([1, 2]),
             'prompt_sha256': independent.text_hash('Authored prompt.')}
    value['request_sha256'] = independent.value_hash(value)
    return value


def test_reconcile_raw_transport_and_failed_attempt_cost():
    requests = [request(0), request(1)]
    events = []
    def event(kind, value):
        events.append({'kind': kind, 'data': value})
    def http_response(route, value):
        event('http_response', {'route': route, 'status': 200, 'elapsed_seconds': .5,
                              'body_base64': base64.b64encode(json.dumps(value).encode()).decode()})
    for row in requests:
        event('http_request', {'route': '/tokenize', 'payload': {'content': row['prompt'], 'add_special': True,
              'parse_special': True, 'with_pieces': False}})
        http_response('/tokenize', {'tokens': [1, 2]})
    response = {'content': 'Authored response.', 'tokens_predicted': 4, 'tokens_evaluated': 2,
                'truncated': False, 'stop_type': 'eos'}
    event('english_sfh_started', requests[0])
    event('http_request', {'route': '/completion', 'payload': independent.expected_payload(requests[0])})
    http_response('/completion', response)
    event('english_sfh_raw', {'request_id': requests[0]['request_id'], 'response': response, 'latency_seconds': 1.0})
    event('english_sfh_started', requests[1])
    event('http_request', {'route': '/completion', 'payload': independent.expected_payload(requests[1])})
    event('english_sfh_failed', {'request_id': requests[1]['request_id'], 'latency_seconds': 2.0})
    receipt = {'attempts': 2, 'responses': 1, 'completion_inference_seconds': 3.0, 'failed_seconds': 2.0,
               'cumulative_generations': 690, 'cumulative_inference_seconds': independent.BASE_SECONDS + 3,
               'unattempted': 0, 'retries': 0}
    result, seconds, failures = independent.reconcile({'requests': requests}, receipt, events, 688, independent.BASE_SECONDS)
    assert seconds == 3 and failures == 1 and result[1]['measurements']['output_tokens'] is None
    corrupted = copy.deepcopy(events)
    next(e for e in corrupted if e['kind'] == 'english_sfh_raw')['data']['response']['content'] = 'Changed.'
    with pytest.raises(AssertionError, match='HTTP bytes'):
        independent.reconcile({'requests': requests}, receipt, corrupted, 688, independent.BASE_SECONDS)


def test_hash_and_numerical_tolerance():
    value = request(0)
    independent.verify_request(value)
    value['messages'][0]['content'] = 'Changed.'
    with pytest.raises(AssertionError, match='Request SHA'):
        independent.verify_request(value)
    independent.compare(1 + 1e-11, 1.0)
    with pytest.raises(AssertionError, match='arithmetic'):
        independent.compare(1 + 1e-8, 1.0)


def test_archived_native_stdout_must_match_registered_token_ids():
    row = request(0)
    stdout, stderr = b'[1, 2]\n', b'Authored native fixture'
    receipt = {'returncode': 0, 'generation_requests': 0, 'prompt_sha256': row['prompt_sha256'],
               'stdout_hex': stdout.hex(), 'stderr_hex': stderr.hex(),
               'stdout_sha256': hashlib.sha256(stdout).hexdigest(), 'stderr_sha256': hashlib.sha256(stderr).hexdigest()}
    independent.verify_native_receipt(receipt, row)
    changed = b'[1, 9]\n'
    receipt['stdout_hex'], receipt['stdout_sha256'] = changed.hex(), hashlib.sha256(changed).hexdigest()
    with pytest.raises(AssertionError, match='Offline native token IDs'):
        independent.verify_native_receipt(receipt, row)


def test_no_import_of_primary_study_code():
    tree = ast.parse(Path(independent.__file__).read_text(encoding='utf-8'))
    modules = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    modules += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
    assert not any(name and name.startswith('english_sfh_') for name in modules)
