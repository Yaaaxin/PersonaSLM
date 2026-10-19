"""One finite local recognition experiment; shared native runtime and journals.

No semantic human labels, training, validation-speaker access, retries or edits
to previous studies. Participant data and responses stay in ignored .local.
"""
import argparse
import ast
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import time
from unittest.mock import patch

import p1_model_feasibility_recovery as metadata
import real_persona_chat_sfh_pilot_execution_v1 as old
import real_persona_chat_continuation_material_v1 as material

OUT = Path('docs/validation/p1/real_persona_chat_continuation_v1')
PRIVATE = Path('.local/experiments/real_persona_chat_continuation_v1')
DESIGN, EVIDENCE = OUT / 'design_v1.json', OUT / 'primary_evidence_v1.json'
REGISTRATION, RECEIPT = OUT / 'registration_v1.json', OUT / 'execution_receipt_v1.json'
FROZEN, CLAIM, RUNS = PRIVATE / 'frozen_manifest_v1.json', PRIVATE / 'claim_v1.json', PRIVATE / 'runs'
MODEL_FILE = Path('models/gguf/instruct_candidates/qwen3-0.6b-official-23749fef/Qwen3-0.6B-Q8_0.gguf')
MODEL_SHA = '9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'
META = Path('.local/model_metadata/qwen3-0.6b-23749fef')
TEMPLATE = PRIVATE / 'official_chat_template.jinja'
BASELINE = Path('docs/validation/p1/real_persona_chat_style_specificity_v1/analysis_v1_1.json')
BASELINE_SHA = '1da84de9343c2ed1047b3f41b4cd4b0c7460f7de66b2fb98bafd59f9353bcaed'
GEN_BASE, SEC_BASE, N = 636, 3828.328792899886, 52
MIN_RAM, READY_RAM, LIVE_RAM = 2 * 1024**3, 1024**3, 512 * 1024**2
load, sha, th, require, write = old.load, old.sha256, old.th, old.require, old.write_exclusive
ARMS = material.ARMS


def config(plan):
    return old.s.Runtime(plan['model']['model_file'], MODEL_SHA, old.MODEL['backend_file'],
                         model_label='Qwen3-0.6B-official-Q8_0-development',
                         n_ctx=2048, max_new_tokens=8)


def budget():
    require(sha(BASELINE) == BASELINE_SHA, 'Cumulative baseline changed')
    resources = load(BASELINE)['resources']
    require(resources['cumulative_generations'] == GEN_BASE and
            abs(resources['cumulative_inference_seconds'] - SEC_BASE) < 1e-8, 'Budget baseline')
    require(GEN_BASE + N <= 1200 and SEC_BASE + 900 <= 72000, 'Global budget ceiling')
    return {'generations': GEN_BASE, 'inference_seconds': SEC_BASE}


def native_tokenize(text):
    tokenizer = Path(old.MODEL['backend_file']).with_name('llama-tokenize.exe')
    argv = [str(tokenizer.resolve()), '-m', str(MODEL_FILE.resolve()), '--stdin', '--ids', '--offline']
    completed = subprocess.run(argv, input=text.encode('utf-8'), capture_output=True, timeout=90,
                               env={k: v for k, v in os.environ.items() if not k.upper().startswith('LLAMA_ARG_')},
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    require(completed.returncode == 0, 'Native tokenizer failed')
    ids = ast.literal_eval(completed.stdout.decode('utf-8').strip())
    require(isinstance(ids, list) and ids and all(type(i) is int and i >= 0 for i in ids), 'Native token IDs')
    return ids


def messages(case, arm, order):
    options, correct = material.options(case, order)
    external = ('[以前の別の会話]\n資料なし。' if arm == 'NONE' else case[
        'correct_external_history' if arm == 'CORRECT' else 'mismatched_external_history'])
    local = material.labelled_history(case['history'], case['speaker_id'])
    return [
        {'role': 'system', 'content': '匿名化された日本語の会話資料を比較する研究課題です。実在人物を特定したり名乗ったりしないでください。答えは半角のAまたはB一文字だけにしてください。'},
        {'role': 'user', 'content': '会話資料と相手の最後の発話を読んで、匿名話者の実際の次の発話だった可能性が高い候補を一つ選んでください。以前の別の会話は参考資料です。理由や説明は書かず、AかBだけを答えてください。\n\n' +
         external + '\n\n[現在の会話]\n' + local + '\n相手: ' + case['query']['text'] +
         '\n\n[候補]\nA: ' + options['A'] + '\nB: ' + options['B']}], correct


def controls():
    questions = [
        ('資料には「好きな飲み物はお茶です」と書いてあります。資料に書かれた飲み物を選んでください。', ['お茶', '牛乳']),
        ('資料には「明日は図書館に行きます」と書いてあります。資料に書かれた行き先を選んでください。', ['図書館', '動物園'])]
    rows = []
    for index, (question, choices) in enumerate(questions):
        for order in (0, 1):
            displayed = choices if order == 0 else choices[::-1]
            rows.append({'case_id': f'AUTHORED{index}', 'phase': 'CONTROL', 'arm': 'CONTROL',
                         'option_order': order, 'correct_label': 'AB'[order],
                         'messages': [{'role': 'system', 'content': '日本語の資料を読んで選択してください。答えは半角のAまたはB一文字だけにしてください。'},
                                      {'role': 'user', 'content': question + '\nA: ' + displayed[0] + '\nB: ' + displayed[1]}]})
    return rows


def score(text, correct):
    choice = text.strip() if isinstance(text, str) else None
    valid = choice in ('A', 'B')
    return {'choice': choice if valid else None, 'format_valid': valid,
            'protocol_success': int(valid and choice == correct),
            'recognition_if_valid': int(choice == correct) if valid else None}


def sources():
    paths = [*old.runtime_python_dependency_paths([Path(__file__)]), DESIGN, EVIDENCE, BASELINE,
             Path('tests/test_real_persona_chat_continuation_v1.py'),
             Path('tests/test_real_persona_chat_continuation_material_v1.py'),
             META / 'README.md', META / 'LICENSE', META / 'tokenizer_config.json', old.TOKENIZER_SOURCE]
    runtime_receipt = Path('docs/validation/p1d/scientific_validation_v1/official_template_rendering_verification_v1.json')
    paths += [runtime_receipt, *(Path(p) for p in load(runtime_receipt)['package_file_sha256'])]
    return {p.as_posix(): sha(p) for p in sorted(set(paths))}


def memory_gate(minimum):
    observation = old.s.memory_observation(os.getpid())
    available = observation.get('system', {}).get('available_physical')
    require(type(available) is int and available >= minimum, f'Available physical RAM {available} < {minimum}')
    require(shutil.disk_usage('.').free >= 1024**3, 'Output disk reserve')
    return observation


def unused():
    require(not CLAIM.exists() and not RECEIPT.exists() and not list(RUNS.glob('*')), 'Already claimed; no retries')


def register():
    unused()
    require(not REGISTRATION.exists() and not FROZEN.exists(), 'Already registered')
    budget()
    memory = memory_gate(MIN_RAM)
    require(sha(MODEL_FILE) == MODEL_SHA and MODEL_FILE.stat().st_size == 639446688, 'Official weight bytes')
    require(sha(Path(old.MODEL['backend_file'])) == old.MODEL['backend_sha256'], 'Backend identity')
    tokenizer_identity = old._tokenizer_identity()
    vendor = metadata.verified_template_runtime()
    gguf, metadata_receipt = metadata.gguf_metadata(MODEL_FILE)
    require(gguf['general.architecture'] == 'qwen3' and gguf['general.file_type'] == 7, 'Model architecture/Q8_0')
    template = load(META / 'tokenizer_config.json')['chat_template']
    require(th(template) == 'a55ee1b1660128b7098723e0abcd92caa0788061051c62d51cbe87d9cf1974d8', 'Official template')
    cases, provenance = material.build_cases(native_tokenize)
    rows = controls()
    for case in cases:
        for order in (0, 1):
            arms = [ARMS[(case['speaker_index'] + p) % 3] for p in range(3)]
            if order:
                arms.reverse()
            for arm in arms:
                prompt_messages, correct = messages(case, arm, order)
                rows.append({'phase': 'MAIN', 'case_id': case['case_id'], 'pair_index': case['pair_index'],
                             'speaker_index': case['speaker_index'], 'arm': arm, 'option_order': order,
                             'correct_label': correct, 'messages': prompt_messages})
    for index, row in enumerate(rows):
        prompt = old.s.render(template, row['messages'])
        require(prompt == old.s.render(gguf['tokenizer.chat_template'], row['messages']), 'Actual template-render mismatch')
        require(prompt.endswith('<|im_start|>assistant\n<think>\n\n</think>\n\n'), 'Non-thinking prefix')
        ids = native_tokenize(prompt)
        require(len(ids) <= 1500 and len(ids) + 8 <= 2048, 'Context capacity')
        row.update(order=index, request_id=f'RPCCONT{index:03d}', prompt=prompt, prompt_sha256=th(prompt),
                   input_token_ids=ids, input_tokens=len(ids))
        row['request_sha256'] = old.value_sha256(row)
    differences = []
    for case in cases:
        for order in (0, 1):
            sizes = {r['arm']: r['input_tokens'] for r in rows if r['phase'] == 'MAIN' and
                     r['case_id'] == case['case_id'] and r['option_order'] == order}
            differences.append(abs(sizes['CORRECT'] - sizes['MISMATCH']))
    require(max(differences) <= 8 and len(rows) == N, 'Full prompt matching/allocation')
    PRIVATE.mkdir(parents=True, exist_ok=True)
    with TEMPLATE.open('x', encoding='utf-8', newline='\n') as handle:
        handle.write(template)
    model = {**old.MODEL, 'model_label': 'Qwen3-0.6B-official-Q8_0-development',
             'model_file': MODEL_FILE.as_posix(), 'model_sha256': MODEL_SHA, 'quantization': 'Q8_0',
             'artifact_revision': '23749fefcc72300e3a2ad315e1317431b06b590a',
             'intended_upstream_revision': 'NOT_INDEPENDENTLY_REBUILT', 'conversion_lineage': 'OFFICIAL_ASSET_HASH_NOT_REBUILT'}
    plan = {'registered_utc': old.b.utc_now(), 'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'model': model, 'template_path': TEMPLATE.as_posix(), 'template_sha256': sha(TEMPLATE),
            'tokenizer_identity': tokenizer_identity, 'source_hashes': sources(), 'baseline': budget(),
            'runtime': load(DESIGN)['generation'], 'cases': cases, 'requests': rows, 'provenance': provenance}
    write(FROZEN, plan)
    write(REGISTRATION, {'status': 'PROSPECTIVELY_FROZEN_NO_GENERATIONS', 'registered_utc': plan['registered_utc'],
          'source_head': plan['source_head'], 'source_hashes': plan['source_hashes'], 'manifest_sha256': sha(FROZEN),
          'model': model, 'runtime': plan['runtime'], 'template_sha256': plan['template_sha256'],
          'tokenizer_identity': tokenizer_identity, 'baseline': budget(), 'allocation': load(DESIGN)['allocation'],
          'provenance': provenance, 'memory_before_tokenization': memory, 'vendor_runtime': vendor,
          'gguf_metadata_read': metadata_receipt, 'embedded_template_sha256': th(gguf['tokenizer.chat_template']),
          'rendered_templates_equal_for_all_actual_requests': True, 'maximum_full_prompt_token_difference': max(differences),
          'input_token_range': [min(r['input_tokens'] for r in rows), max(r['input_tokens'] for r in rows)],
          'privacy': 'Participant-level materials and raw responses excluded from public records.'})
    return {'status': 'REGISTERED', 'maximum_attempts': N, 'provenance': provenance}


def validate():
    plan, registration = load(FROZEN), load(REGISTRATION)
    require(sha(FROZEN) == registration['manifest_sha256'] and sources() == plan['source_hashes'], 'Frozen bindings')
    require(plan['baseline'] == budget() and plan['runtime'] == load(DESIGN)['generation'], 'Budget/runtime binding')
    require(sha(TEMPLATE) == plan['template_sha256'] and len(plan['requests']) == N, 'Template/allocation')
    for index, row in enumerate(plan['requests']):
        require(row['order'] == index and row['request_id'] == f'RPCCONT{index:03d}', 'Unique request sequence')
        require(row['request_sha256'] == old.value_sha256({k: v for k, v in row.items() if k != 'request_sha256'}), 'Request hash')
        require(row['prompt'] == old.s.render(TEMPLATE.read_text(encoding='utf-8'), row['messages']) and
                row['prompt_sha256'] == th(row['prompt']) and len(row['input_token_ids']) == row['input_tokens'], 'Exact input binding')
    return plan


def preflight(check_memory=True, check_unused=True):
    plan = validate()
    if check_unused:
        unused()
    identity = old.b.file_preflight(config(plan))
    require(identity['status'] == 'PASS' and identity['model']['sha256'] == MODEL_SHA and
            identity['server']['sha256'] == old.MODEL['backend_sha256'], 'Model/backend identity')
    require(old._tokenizer_identity() == plan['tokenizer_identity'], 'Native tokenizer identity')
    memory = memory_gate(MIN_RAM) if check_memory else old.s.memory_observation(os.getpid())
    return {'status': 'PASS', 'checked_utc': old.b.utc_now(), 'memory': memory, 'identity': identity,
            'manifest_sha256': sha(FROZEN), 'registration_sha256': sha(REGISTRATION),
            'source_hashes_sha256': old.value_sha256(plan['source_hashes']), 'baseline': budget(),
            'resources': load(DESIGN)['resources']}


def payload(row):
    return {'prompt': row['input_token_ids'], 'n_predict': 8, 'temperature': 0.0, 'top_p': 1.0,
            'seed': 42, 'cache_prompt': False, 'stop': [], 'ignore_eos': False, 'return_tokens': True, 'stream': False}


def run(preflight_path):
    fresh, saved, plan = preflight(), load(preflight_path), validate()
    require(saved['status'] == 'PASS', 'Saved passing preflight required')
    for key in ('identity', 'manifest_sha256', 'registration_sha256', 'source_hashes_sha256', 'baseline'):
        require(saved[key] == fresh[key], 'Preflight binding: ' + key)
    with old.b.writer_lock(PRIVATE):
        unused()
        claim = {'manifest_sha256': sha(FROZEN), 'preflight_sha256': sha(preflight_path), 'maximum_attempts': N}
        write(CLAIM, claim)
        journal = old.b.RunJournal(RUNS, {'phase': 'P1 RPC continuation recognition', 'claim': claim,
                  'frozen_manifest': plan, 'authorization': load(DESIGN), 'configuration': config(plan).as_dict()})
        for path, digest in plan['source_hashes'].items():
            target = journal.directory / 'source_snapshot' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as handle:
                handle.write(Path(path).read_bytes())
            require(sha(target) == digest, 'Source snapshot')
        started, seconds, failed_seconds, attempts, responses, controls_correct = time.monotonic(), 0., 0., 0, 0, 0
        status, active = 'BLOCKED', None
        try:
            journal.write('preflight', fresh)
            # Reuse the owned-server implementation with this separately frozen config.
            with patch.object(old.s, 'config', config), old.s.Server(plan, journal) as server:
                memory = old.s.memory_observation(server.process.pid)
                journal.write('ready_memory', memory)
                require(memory['system']['available_physical'] >= READY_RAM, 'Ready RAM below1GiB')
                client = old.b.LlamaClient(config(plan).endpoint, timeout=180, audit=journal.write)
                props = client.request('/props')
                journal.write('server_properties', {'props': props, 'validation': old.b.validate_server_properties(props, config(plan))})
                for row in plan['requests']:
                    ids = client.request('/tokenize', {'content': row['prompt'], 'add_special': True,
                        'parse_special': True, 'with_pieces': False})['tokens']
                    require(ids == row['input_token_ids'], 'Live native token mismatch')
                    journal.write('live_tokenizer', {'request_id': row['request_id'], 'token_ids_sha256': th(str(ids))})
                tokenized_memory = old.s.memory_observation(server.process.pid)
                journal.write('ready_after_tokenization_memory', tokenized_memory)
                require(tokenized_memory['system']['available_physical'] >= READY_RAM,
                        'Ready RAM after tokenization below1GiB')
                for row in plan['requests']:
                    if row['phase'] == 'MAIN' and controls_correct != 4:
                        status = 'CONTROL_GATE_FAILED'
                        break
                    remaining = min(900 - seconds, 1500 - (time.monotonic() - started))
                    require(remaining > 0, 'Finite batch time ceiling')
                    server.assert_running()
                    memory = old.s.memory_observation(server.process.pid)
                    journal.write('before_request_memory', memory)
                    require(memory['system']['available_physical'] >= LIVE_RAM, 'Live RAM below512MiB')
                    client.timeout = min(180, remaining)
                    active = row['request_id']
                    journal.write('continuation_started', row)
                    attempts += 1
                    tick = time.monotonic()
                    try:
                        response = client.request('/completion', payload(row))
                    except BaseException:
                        elapsed = time.monotonic() - tick
                        seconds += elapsed
                        failed_seconds += elapsed
                        journal.write('continuation_failed', {'request_id': active, 'latency_seconds': elapsed})
                        raise
                    elapsed = time.monotonic() - tick
                    seconds += elapsed
                    journal.write('continuation_raw', {'request_id': active, 'response': response, 'latency_seconds': elapsed})
                    responses += 1
                    old.b.validate_completion(response, row['input_token_ids'])
                    require(type(response.get('tokens_predicted')) is int and 0 <= response['tokens_predicted'] <= 8, 'Output token allocation')
                    if row['phase'] == 'CONTROL':
                        controls_correct += score(response['content'], row['correct_label'])['protocol_success']
                    active = None
                    print(json.dumps({'completed': responses, 'maximum': N, 'phase': row['phase'], 'seconds': round(seconds, 3)}), flush=True)
                server.assert_running()
                journal.write('postflight', preflight(check_memory=False, check_unused=False))
            if status != 'CONTROL_GATE_FAILED':
                status = 'PASS'
        except BaseException as exc:
            status = 'PARTIAL' if attempts else 'BLOCKED'
            journal.write('failure', {'type': type(exc).__name__, 'message': str(exc), 'request_id': active})
        result = {'status': status, 'attempts': attempts, 'responses': responses, 'controls_correct': controls_correct,
                  'completion_inference_seconds': seconds, 'failed_seconds': failed_seconds,
                  'wall_seconds': time.monotonic() - started, 'unattempted': N - attempts, 'retries': 0,
                  'cumulative_generations': GEN_BASE + attempts, 'cumulative_inference_seconds': SEC_BASE + seconds}
        journal.finish(**result)
        write(RECEIPT, {**result, 'run_directory': journal.directory.as_posix(), 'terminal_event_sha256': journal.previous_hash})
        return result


def statistics_for(values):
    return {'n': len(values), 'mean': statistics.fmean(values) if values else None,
            'values': values, 'leave_one_pair_out_mean_range': [
                min(statistics.fmean(values[:i] + values[i+1:]) for i in range(len(values))),
                max(statistics.fmean(values[:i] + values[i+1:]) for i in range(len(values)))] if len(values) > 1 else None}


def analyze(write_files=False):
    plan, receipt = validate(), load(RECEIPT)
    events = old.b.read_events(Path(receipt['run_directory']))
    require(events[-1]['kind'] == 'run_finished' and events[-1]['event_hash'] == receipt['terminal_event_sha256'], 'Terminal chain')
    started = [e['data'] for e in events if e['kind'] == 'continuation_started']
    raw = [e['data'] for e in events if e['kind'] == 'continuation_raw']
    require(started == plan['requests'][:len(started)] and len(raw) == receipt['responses'], 'Exact prefix reconciliation')
    records = {r['request_id']: r for r in raw}
    require(len(records) == len(raw), 'Duplicate response')
    rows = []
    for request in plan['requests']:
        record = records.get(request['request_id'])
        scored = score(record['response']['content'], request['correct_label']) if record else {
            'choice': None, 'format_valid': None, 'protocol_success': None, 'recognition_if_valid': None}
        rows.append({**{k: request[k] for k in ('request_id', 'phase', 'case_id', 'arm', 'option_order', 'correct_label')},
                     'pair_index': request.get('pair_index'), **scored,
                     'latency_seconds': record['latency_seconds'] if record else None,
                     'output_tokens': record['response'].get('tokens_predicted') if record else None,
                     'stop_type': record['response'].get('stop_type') if record else None})
    conditions, contrasts = {}, {}
    for arm in ARMS:
        selected = [r for r in rows if r['phase'] == 'MAIN' and r['arm'] == arm]
        observed = [r for r in selected if r['protocol_success'] is not None]
        valid = [r for r in observed if r['format_valid']]
        invariant = []
        for case in plan['cases']:
            group = [r for r in selected if r['case_id'] == case['case_id']]
            if all(r['format_valid'] for r in group):
                invariant.append(int(group[0]['choice'] != group[1]['choice']))
        conditions[arm] = {'allocated': 16, 'returned': len(observed), 'format_valid': len(valid),
                           'protocol_successes': sum(r['protocol_success'] for r in observed),
                           'protocol_success_mean': statistics.fmean(r['protocol_success'] for r in observed) if observed else None,
                           'valid_selection_recognition': statistics.fmean(r['recognition_if_valid'] for r in valid) if valid else None,
                           'position_invariance_cases': len(invariant), 'position_invariant': sum(invariant),
                           'first_option_choices': sum(r['choice'] == 'A' for r in valid),
                           'lexical_baseline_mean': statistics.fmean(material.lexical_baseline(c, arm)['accuracy'] for c in plan['cases'])}
    for left, right in (('CORRECT', 'MISMATCH'), ('CORRECT', 'NONE'), ('MISMATCH', 'NONE')):
        effects, differences, missing = [], [], 0
        for pair in range(4):
            pair_differences = []
            for case in [c for c in plan['cases'] if c['pair_index'] == pair]:
                for order in (0, 1):
                    group = {r['arm']: r for r in rows if r['case_id'] == case['case_id'] and r['option_order'] == order}
                    a, b = group[left]['protocol_success'], group[right]['protocol_success']
                    if a is None or b is None:
                        missing += 1
                    else:
                        pair_differences.append(a-b)
            differences += pair_differences
            if len(pair_differences) == 4:
                effects.append(statistics.fmean(pair_differences))
        contrasts[left + '-' + right] = {**statistics_for(effects), 'missing_paired_order_cases': missing,
            'allocated_16_order_case_bounds': [(sum(differences)-missing)/16, (sum(differences)+missing)/16]}
    memory = [e['data'] for e in events if e['kind'] in ('ready_memory', 'ready_after_tokenization_memory',
                                                      'before_request_memory', 'memory_observation')]
    public = {'status': receipt['status'], 'evidence': 'OBSERVED_DEVELOPMENT_RECOGNITION_NOT_SEMANTIC_QUALITY',
              'resources': receipt, 'conditions': conditions, 'contrasts': contrasts,
              'native_stops': dict(Counter(r['stop_type'] for r in rows if r['stop_type'])),
              'peak_observed_working_set': max((m.get('process', {}).get('working_set', 0) for m in memory), default=0),
              'minimum_observed_available_ram': min((m['system']['available_physical'] for m in memory), default=None),
              'bindings': {'manifest_sha256': sha(FROZEN), 'registration_sha256': sha(REGISTRATION), 'receipt_sha256': sha(RECEIPT)},
              'human_labels': 0, 'validation_speakers_accessed': 0, 'confirmatory_test': 'NONE',
              'limits': 'Actual-reference recognition and option invariance, not semantic appropriateness, generated fidelity, true personal facts or a new algorithm. Four reciprocal dependence clusters; public clone-only reproduction PARTIAL.'}
    if write_files:
        write(PRIVATE / 'analysis_private_v1.json', {'rows': rows})
        public['bindings']['private_analysis_sha256'] = sha(PRIVATE / 'analysis_private_v1.json')
        write(OUT / 'analysis_v1.json', public)
    return public


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('register', 'preflight', 'run', 'analyze'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--preflight', type=Path)
    args = parser.parse_args()
    if args.action == 'register':
        result = register()
    elif args.action == 'preflight':
        require(args.output is not None and args.output.parent == OUT, 'Public preflight output required')
        try:
            result = preflight()
        except Exception as exc:
            observation = old.s.memory_observation(os.getpid())
            available = observation.get('system', {}).get('available_physical')
            result = {'status': 'FAIL', 'checked_utc': old.b.utc_now(), 'error': str(exc), 'memory': observation,
                      'required_available_bytes': MIN_RAM, 'ram_deficit_bytes': max(0, MIN_RAM-available) if type(available) is int else None,
                      'generations': 0, 'retry_without_material_change': False}
        write(args.output, result)
    elif args.action == 'run':
        require(args.preflight is not None, 'Preflight path required')
        result = run(args.preflight)
    else:
        result = analyze(write_files=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
