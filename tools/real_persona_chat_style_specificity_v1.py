"""One bounded four-arm RPC development study; reuse existing runtime and journals.

All participant material stays in .local. No training, human labels, validation
speaker content, retries or historical evidence edits. See frozen design_v1.json.
"""
import argparse
import base64
from collections import Counter, defaultdict
import itertools
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import time

import real_persona_chat_sfh_pilot_v1 as material
import real_persona_chat_sfh_pilot_execution_v1 as old

OUT = Path('docs/validation/p1/real_persona_chat_style_specificity_v1')
PRIVATE = Path('.local/experiments/real_persona_chat_style_specificity_v1')
DESIGN = OUT / 'design_v1.json'
LICENSE_AUDIT = OUT / 'licensing_and_prior_art_review_v1.json'
REGISTRATION = OUT / 'registration_v1.json'
FROZEN = PRIVATE / 'frozen_manifest_v1.json'
BASELINE = Path('docs/validation/p1/real_persona_chat_sfh_pilot_v1/analysis_v1_1.json')
BASELINE_SHA = '2adca94fceb295e2a2d29266aaca9f60280c964a330d561b5dca12c3d59df914'
OLD_MATERIAL = Path('.local/experiments/real_persona_chat_sfh_pilot_v1/materials_v1.json')
OLD_MATERIAL_SHA = '4f2e57ba05a8784835c0c0108ec10ba18851a28c084b1dc293b4eb4359a1ff4e'
CLAIM = PRIVATE / 'claim_v1.json'
RUNS = PRIVATE / 'runs'
ARMS = ('NONE', 'CORRECT', 'MISMATCH', 'LENGTH')
FEATURES = ('hiragana_rate', 'katakana_rate', 'han_rate', 'latin_rate',
            'digit_rate', 'punctuation_rate', 'symbol_rate')
MARKERS = material.STYLE_FEATURES
SELECTION = 'PersonaSLM-RPC-specificity-development-v1'
N = 64
load, sha, require, write = old.load, old.sha256, old.require, old.write_exclusive


def vector(turns, prefix=None):
    normalized = [old.normalize_text(text) for text in turns]
    if prefix is not None:
        normalized = [text[:prefix] for text in normalized]
    return old.style_signal.style_vector([{'turns': normalized}])


def distance(left, right, features=FEATURES):
    return statistics.fmean(abs(left[key] - right[key]) for key in features)


def margin(text, case, prefix=None):
    observed = vector([text], prefix)
    return (distance(observed, vector(case['donor_reference_turns'], prefix)) -
            distance(observed, vector(case['reference_turns'], prefix)))


def native_boundary(response):
    stop = response.get('stop_type')
    require(all(response.get(key) is None or type(response[key]) is bool
                for key in ('stopped_limit', 'stopped_eos', 'stopped_word')),
            'Native stop flags must be boolean or absent')
    limit = bool(response.get('stopped_limit')) or stop == 'limit'
    eos = bool(response.get('stopped_eos')) or stop in ('eos', 'eog')
    word = bool(response.get('stopped_word')) or stop == 'word'
    return {'native_stop_type': stop, 'observed_native_boundary': eos and not limit and not word,
            'contradictory_stop_flags': sum((limit, eos, word)) > 1,
            'limit': limit, 'semantic_completeness': 'NOT_HUMAN_ASSESSED'}


def context_pairs(record, speaker):
    found = []
    turns = record['turns']
    for index in range(7, len(turns)):
        if found and index - found[-1]['reference_index'] < 8:
            continue
        response, query = turns[index], turns[index - 1]
        history = turns[index - 7:index - 1]
        texts = [turn['text'] for turn in history] + [query['text']]
        if response['interlocutor_id'] != speaker or query['interlocutor_id'] == speaker:
            continue
        if any(material.MASK.search(text) for text in texts + [response['text']]):
            continue
        if not (4 <= len(query['text']) <= 240 and 8 <= len(response['text']) <= 240):
            continue
        if not all(material.JAPANESE.search(text) for text in (query['text'], response['text'])):
            continue
        if not material._no_answer_leak(response['text'], texts):
            continue
        found.append({'history': history, 'query': query, 'reference': response,
                      'reference_index': index})
        if len(found) == 2:
            return found
    return []


def donor_assignment(profiles):
    def members(row):
        return {row['speaker'], row['target']['partner'],
                *(source['partner'] for source in row['sources'])}
    def dialogues(row):
        return {row['target']['dialogue_id'], *(s['dialogue_id'] for s in row['sources'])}
    costs = {}
    for i, own in enumerate(profiles):
        for j, donor in enumerate(profiles):
            if i == j or members(own) & members(donor) or dialogues(own) & dialogues(donor):
                continue
            if all(round(own['style'][k] * 100, 1) == round(donor['style'][k] * 100, 1)
                   for k in MARKERS):
                continue
            costs[i, j] = sum(abs(own['style'][key] - donor['style'][key])
                              for key in ('mean_turn_length', 'sd_turn_length'))
    feasible = ((sum(costs[i, j] for i, j in enumerate(order)), order)
                for order in itertools.permutations(range(len(profiles)))
                if all((i, j) in costs for i, j in enumerate(order)))
    best = min(feasible, default=None)
    require(best is not None, 'No prespecified length-matched private donor derangement')
    return best[1], best[0]


def build_cases():
    root = Path('.local/datasets/real-persona-chat')
    source = material.verify_live_source(root)
    _, dialogues, split_hash, excluded = material.load_development_view(root)
    cohort, cohort_hash = material._frozen_style_cohort(dialogues, split_hash)
    require(sha(OLD_MATERIAL) == OLD_MATERIAL_SHA, 'Historical materials changed')
    old_targets = {case['target_dialogue_id'] for case in load(OLD_MATERIAL)['cases']}
    by_speaker = defaultdict(list)
    for dialogue in dialogues:
        for speaker in dialogue['interlocutors']:
            if speaker in cohort:
                record = material._dialogue_record(dialogue, speaker)
                if record is not None:
                    by_speaker[speaker].append(record)
    selected = []
    for speaker in sorted(cohort, key=lambda value: old.th(SELECTION + '\0' + value)):
        ordered = sorted(by_speaker[speaker], key=lambda r: (r['start'], r['dialogue_id']))
        for target in reversed(ordered):
            if target['dialogue_id'] in old_targets:
                continue
            pairs = context_pairs(target, speaker)
            if len(pairs) != 2:
                continue
            sources, partners = [], {target['partner']}
            for row in ordered:
                if row['end'] >= target['start'] or row['partner'] in partners:
                    continue
                if len(row['speaker_turns']) < 10 or any(material.MASK.search(t) for t in row['speaker_turns']):
                    continue
                sources.append(row)
                partners.add(row['partner'])
                if len(sources) == 2:
                    break
            if len(sources) != 2:
                continue
            selected.append({'speaker': speaker, 'sources': sources, 'target': target,
                             'pairs': pairs, 'style': vector(sources[0]['speaker_turns'])})
            break
        if len(selected) == 8:
            break
    require(len(selected) == 8, 'Insufficient eight-speaker/two-context development material')
    donors, matching_cost = donor_assignment(selected)
    cases = []
    for index, profile in enumerate(selected):
        donor = selected[donors[index]]
        for context, pair in enumerate(profile['pairs']):
            cases.append({'case_id': f'SP{index:02d}T{context}', 'speaker_index': index,
                          'context_index': context, 'speaker_id': profile['speaker'],
                          'source_dialogue_ids': [s['dialogue_id'] for s in profile['sources']],
                          'target_dialogue_id': profile['target']['dialogue_id'],
                          'source_end': max(s['end'] for s in profile['sources']).isoformat(),
                          'target_start': profile['target']['start'].isoformat(),
                          'donor_index': donors[index], 'style': profile['style'],
                          'donor_style': donor['style'],
                          'reference_turns': profile['sources'][1]['speaker_turns'],
                          'donor_reference_turns': donor['sources'][1]['speaker_turns'], **pair})
    return cases, {'source': source, 'split_assignment_sha256': split_hash,
                   'cohort_sha256': cohort_hash, 'excluded_nondevelopment_headers': excluded,
                   'old_target_dialogue_overlap': 0, 'donor_length_matching_cost': matching_cost,
                   'reserved_validation_content_deserialized': False}


def messages(case, arm):
    length = (f"一発話の長さは平均約{case['style']['mean_turn_length'] * 50:05.1f}文字を目安にしてください。"
              if arm != 'NONE' else '長さの指定はありません。')
    names = ('疑問符', '感嘆符', '省略表現', '笑い表現', '丁寧語の語尾')
    features = case['donor_style'] if arm == 'MISMATCH' else case['style']
    rates = '\n'.join(f"{name}を使う発話の割合：約{features[key] * 100:05.1f}%。"
                      if arm in ('CORRECT', 'MISMATCH') else f"{name}：指定なし。"
                      for name, key in zip(names, MARKERS))
    history = '\n'.join(('匿名話者' if t['interlocutor_id'] == case['speaker_id'] else '相手') +
                        ': ' + t['text'] for t in case['history'])
    return [{'role': 'system', 'content':
             'あなたは匿名化された研究用対話の応答を生成します。特定の実在人物を名乗ったり特定しようとせず、説明やラベルを付けずに自然な日本語の返答だけを書いてください。'},
            {'role': 'user', 'content':
             '次の会話の最後の相手の発話に続く自然な返答を一つ書いてください。参考情報から個人情報を推測で補わないでください。話し方の割合は参考傾向であり、すべての表現を一つの返答に詰め込まないでください。\n\n'
             '[長さ]\n' + length + '\n\n[話し方]\n' + rates + '\n\n[過去の会話]\n' + history +
             '\n\n[相手の発話]\n' + case['query']['text']}]


def baseline():
    require(sha(BASELINE) == BASELINE_SHA, 'Cumulative baseline changed')
    budget = load(BASELINE)['resources']['cumulative_after']
    require(budget['generations_used'] == 572 and
            abs(budget['inference_seconds_used'] - 3514.1361039998983) < 1e-8,
            'Cumulative baseline not recovered')
    return budget


def resource_check():
    observation = old.s.memory_observation(os.getpid())
    available = observation.get('system', {}).get('available_physical')
    require(type(available) is int and available >= old.MIN_PREFLIGHT_RAM,
            f'Available RAM {available} below unchanged 3 GiB safety requirement')
    require(shutil.disk_usage('.').free >= old.MIN_DISK, 'Output disk reserve')
    return observation


def source_hashes():
    paths = list(old.runtime_python_dependency_paths([Path(__file__), Path(material.__file__)]))
    paths += [DESIGN, LICENSE_AUDIT, BASELINE, old.TOKENIZER_SOURCE,
              Path('tests/test_real_persona_chat_style_specificity_v1.py')]
    return {str(path).replace('\\', '/'): sha(path) for path in sorted(set(paths))}


def register():
    require(not FROZEN.exists() and not REGISTRATION.exists() and not CLAIM.exists(), 'Already registered')
    require(LICENSE_AUDIT.is_file(), 'Specific generation license audit required')
    require(load(LICENSE_AUDIT)['decision']['status'] == 'CONDITIONAL_GO_NO_NEW_LICENSE_BLOCKER_IDENTIFIED',
            'License/privacy audit does not permit this bounded scope')
    require(load(DESIGN)['allocation']['maximum_attempts'] == N and
            572 + N <= 1200 and 3514.1361039998983 + 1200 <= 72000,
            'Finite prospective allocation exceeds cumulative authority')
    budget = baseline()
    memory = resource_check()
    require(sha(Path(old.MODEL['model_file'])) == old.MODEL['model_sha256'], 'Model hash')
    require(sha(Path(old.MODEL['backend_file'])) == old.MODEL['backend_sha256'], 'Backend hash')
    template_path = Path(old.RUNTIME['chat_template_path'])
    require(sha(template_path) == old.RUNTIME['chat_template_sha256'], 'Template hash')
    identity = old._tokenizer_identity()
    cases, provenance = build_cases()
    template = template_path.read_text(encoding='utf-8')
    requests = []
    for case in cases:
        offset = (case['speaker_index'] + case['context_index']) % 4
        for position in range(4):
            arm = ARMS[(position + offset) % 4]
            prompt_messages = messages(case, arm)
            prompt = old.s.render(template, prompt_messages)
            ids, receipt = old._tokenize_native(Path(identity['path']), prompt)
            order = len(requests)
            write(PRIVATE / 'tokenizer' / f'{order:03d}.json', receipt)
            require(len(ids) <= old.MAX_INPUT_TOKENS and len(ids) + 96 <= 4096, 'Context safety')
            row = {'order': order, 'request_id': f'RPCSPEC{order:03d}', 'arm': arm,
                   'case_id': case['case_id'], 'messages': prompt_messages, 'prompt': prompt,
                   'prompt_sha256': old.th(prompt), 'input_token_ids': ids, 'input_tokens': len(ids)}
            row['request_sha256'] = old.value_sha256(row)
            requests.append(row)
    plan = {'schema_version': 'rpc_specificity_frozen_v1', 'registered_utc': old.b.utc_now(),
            'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'source_hashes': source_hashes(), 'model': old.MODEL, 'runtime': old.RUNTIME,
            'template_path': old.RUNTIME['chat_template_path'], 'tokenizer_identity': identity,
            'baseline': budget, 'cases': cases, 'requests': requests, 'provenance': provenance}
    write(FROZEN, plan)
    registration = {'status': 'PROSPECTIVELY_FROZEN_NO_GENERATIONS', 'registered_utc': plan['registered_utc'],
                    'source_head': plan['source_head'], 'source_hashes': plan['source_hashes'],
                    'private_manifest_sha256': sha(FROZEN), 'model': old.MODEL, 'runtime': old.RUNTIME,
                    'baseline': budget, 'allocation': load(DESIGN)['allocation'], 'provenance': provenance,
                    'memory_before_tokenization': memory, 'private_tokenizer_evidence_sha256':
                    old.value_sha256({p.name: sha(p) for p in sorted((PRIVATE / 'tokenizer').glob('*.json'))}),
                    'input_tokens_by_arm': {arm: [r['input_tokens'] for r in requests if r['arm'] == arm] for arm in ARMS},
                    'privacy': 'No speaker identities, prompts, source text, reference text or review keys public'}
    write(REGISTRATION, registration)
    return {'status': registration['status'], 'requests': len(requests), 'baseline': budget}


def validate():
    plan, registration = load(FROZEN), load(REGISTRATION)
    require(sha(FROZEN) == registration['private_manifest_sha256'], 'Frozen manifest changed')
    require(plan['source_hashes'] == source_hashes(), 'Frozen source dependency changed')
    require(plan['baseline'] == baseline(), 'Budget baseline mismatch')
    require(plan['model'] == old.MODEL and plan['runtime'] == old.RUNTIME, 'Configuration changed')
    require(len(plan['requests']) == N and len(plan['cases']) == 16, 'Allocation changed')
    template = Path(plan['template_path']).read_text(encoding='utf-8')
    for index, row in enumerate(plan['requests']):
        case = next(c for c in plan['cases'] if c['case_id'] == row['case_id'])
        require(row['order'] == index and row['request_id'] == f'RPCSPEC{index:03d}', 'Order changed')
        require(row['arm'] == ARMS[(index % 4 + case['speaker_index'] + case['context_index']) % 4], 'Arm changed')
        require(row['messages'] == messages(case, row['arm']) and
                row['prompt'] == old.s.render(template, row['messages']), 'Prompt changed')
        require(row['prompt_sha256'] == old.th(row['prompt']) and
                row['request_sha256'] == old.value_sha256({k: v for k, v in row.items() if k != 'request_sha256'}),
                'Request binding changed')
    return plan


def preflight(check_memory=True, unused=True):
    plan = validate()
    if unused:
        require(not CLAIM.exists() and not list(RUNS.glob('*')), 'No second execution/retry')
    identity = old.b.file_preflight(old.cfg(plan))
    require(identity['status'] == 'PASS' and identity['model']['sha256'] == old.MODEL['model_sha256'] and
            identity['server']['sha256'] == old.MODEL['backend_sha256'], 'Model/backend identity')
    require(old._tokenizer_identity() == plan['tokenizer_identity'], 'Tokenizer identity')
    require(sha(Path(plan['template_path'])) == old.RUNTIME['chat_template_sha256'], 'Template identity')
    memory = resource_check() if check_memory else old.s.memory_observation(os.getpid())
    return {'status': 'PASS', 'checked_utc': old.b.utc_now(), 'memory': memory,
            'manifest_sha256': sha(FROZEN), 'registration_sha256': sha(REGISTRATION),
            'source_hashes_sha256': old.value_sha256(plan['source_hashes']), 'identity': identity,
            'baseline': baseline(), 'resources': load(DESIGN)['resources']}


def preflight_receipt():
    try:
        return preflight()
    except Exception as exc:
        observation = old.s.memory_observation(os.getpid())
        available = observation.get('system', {}).get('available_physical')
        return {'status': 'FAIL', 'checked_utc': old.b.utc_now(), 'error': str(exc),
                'memory': observation, 'minimum_available_ram': old.MIN_PREFLIGHT_RAM,
                'ram_deficit_bytes': max(0, old.MIN_PREFLIGHT_RAM - available) if type(available) is int else None,
                'new_generations': 0, 'retry_unchanged_configuration': False}


def run(preflight_path):
    fresh, saved = preflight(), load(preflight_path)
    require(saved['status'] == 'PASS', 'Passing preflight required')
    for key in ('manifest_sha256', 'registration_sha256', 'source_hashes_sha256', 'identity', 'baseline'):
        require(saved[key] == fresh[key], 'Preflight changed: ' + key)
    plan = load(FROZEN)
    with old.b.writer_lock(PRIVATE):
        require(not CLAIM.exists() and not list(RUNS.glob('*')), 'No replay/retry')
        claim = {'manifest_sha256': sha(FROZEN), 'preflight_sha256': sha(preflight_path), 'maximum_attempts': N}
        write(CLAIM, claim)
        journal = old.b.RunJournal(RUNS, {'phase': 'P1 RPC four-arm style specificity development v1',
                     'claim': claim, 'frozen_manifest': plan, 'authorization': load(DESIGN),
                     'configuration': old.cfg(plan).as_dict()})
        for path, digest in plan['source_hashes'].items():
            target = journal.directory / 'source_snapshot' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as handle:
                handle.write(Path(path).read_bytes())
            require(sha(target) == digest, 'Source snapshot mismatch')
        started, seconds, failed_seconds, attempts, responses = time.monotonic(), 0., 0., 0, 0
        status, active = 'BLOCKED', None
        try:
            journal.write('preflight', fresh)
            with old.s.Server(plan, journal) as server:
                memory = old.s.memory_observation(server.process.pid)
                journal.write('ready_memory', memory)
                require(memory['system']['available_physical'] >= old.MIN_READY_RAM, 'Ready RAM below 1 GiB')
                client = old.b.LlamaClient(old.cfg(plan).endpoint, timeout=180, audit=journal.write)
                props = client.request('/props')
                binding = old.b.validate_server_properties(props, old.cfg(plan))
                require(old.RUNTIME['backend_build'].split('-', 1)[1] in binding['build_info'], 'Backend build')
                journal.write('server_properties', {'props': props, 'validation': binding})
                for row in plan['requests']:
                    ids = client.request('/tokenize', {'content': row['prompt'], 'add_special': True,
                        'parse_special': True, 'with_pieces': False})['tokens']
                    require(ids == row['input_token_ids'], 'Live tokenizer mismatch')
                    journal.write('live_tokenizer', {'request_id': row['request_id'], 'token_ids_sha256': old.th(str(ids))})
                memory = old.s.memory_observation(server.process.pid)
                journal.write('post_tokenization_memory', memory)
                require(memory['system']['available_physical'] >= old.MIN_READY_RAM, 'Precompletion RAM below 1 GiB')
                for row in plan['requests']:
                    remaining = min(1200 - seconds, 1800 - (time.monotonic() - started))
                    require(remaining > 0, 'Finite execution ceiling')
                    server.assert_running()
                    memory = old.s.memory_observation(server.process.pid)
                    journal.write('before_request_memory', memory)
                    require(memory['system']['available_physical'] >= old.MIN_LIVE_RAM, 'Live RAM below 512 MiB')
                    client.timeout = min(180, remaining)
                    active = row['request_id']
                    journal.write('specificity_started', row)
                    attempts += 1
                    tick = time.monotonic()
                    try:
                        response = client.request('/completion', old.payload(row))
                    except BaseException:
                        elapsed = time.monotonic() - tick
                        seconds += elapsed
                        failed_seconds += elapsed
                        journal.write('specificity_failed', {'request_id': active, 'latency_seconds': elapsed})
                        raise
                    elapsed = time.monotonic() - tick
                    seconds += elapsed
                    journal.write('specificity_raw', {'request_id': active, 'response': response, 'latency_seconds': elapsed})
                    responses += 1
                    old.b.validate_completion(response, row['input_token_ids'])
                    require(type(response.get('tokens_predicted')) is int and 0 <= response['tokens_predicted'] <= 96,
                            'Native token count outside allocation')
                    active = None
                    print(json.dumps({'completed': responses, 'planned': N, 'seconds': round(seconds, 3)}), flush=True)
                server.assert_running()
                after = preflight(check_memory=False, unused=False)
                require(after['identity'] == fresh['identity'], 'Postflight identity')
                journal.write('postflight', after)
            status = 'PASS'
        except BaseException as exc:
            status = 'PARTIAL' if attempts else 'BLOCKED'
            journal.write('failure', {'type': type(exc).__name__, 'message': str(exc), 'request_id': active})
        summary = {'status': status, 'attempts': attempts, 'responses': responses,
                   'completion_inference_seconds': seconds, 'failed_seconds': failed_seconds,
                   'wall_seconds': time.monotonic() - started, 'retries': 0,
                   'unattempted': N - attempts, 'run_directory': journal.directory.as_posix()}
        journal.finish(**summary)
        write(journal.directory / 'summary.json', summary)
        write(OUT / 'execution_receipt_v1.json', {**summary,
              'cumulative_generations': 572 + attempts, 'cumulative_inference_seconds': 3514.1361039998983 + seconds,
              'terminal_event_sha256': journal.previous_hash})
        return summary


def summary(values):
    return {'n': len(values), 'mean': statistics.fmean(values) if values else None,
            'range': [min(values), max(values)] if values else None,
            'leave_one_speaker_out_mean_range': [
                min(statistics.fmean(values[:i] + values[i+1:]) for i in range(len(values))),
                max(statistics.fmean(values[:i] + values[i+1:]) for i in range(len(values)))] if len(values) > 1 else None}


def analyze(write_files=True):
    plan = validate()
    folders = list(RUNS.glob('*'))
    require(len(folders) == 1, 'Exactly one run required')
    events = old.b.read_events(folders[0])
    require(events[-1]['kind'] == 'run_finished', 'Incomplete journal: reconcile before analysis')
    attempted = [e['data'] for e in events if e['kind'] == 'specificity_started']
    raw = [e['data'] for e in events if e['kind'] == 'specificity_raw']
    require(attempted == plan['requests'][:len(attempted)], 'Repeated/reordered request')
    sent = [e['data']['payload'] for e in events if e['kind'] == 'http_request' and e['data']['route'] == '/completion']
    require(sent == [old.payload(r) for r in attempted], 'HTTP payload mismatch')
    bodies = [json.loads(base64.b64decode(e['data']['body_base64'])) for e in events if
              e['kind'] == 'http_response' and e['data'].get('route') == '/completion' and e['data'].get('status') == 200]
    require(bodies == [r['response'] for r in raw], 'HTTP raw mismatch')
    require(len({r['request_id'] for r in raw}) == len(raw), 'Duplicate raw result')
    raw_by_id = {r['request_id']: r for r in raw}
    rows = []
    for request in plan['requests']:
        case = next(c for c in plan['cases'] if c['case_id'] == request['case_id'])
        record = raw_by_id.get(request['request_id'])
        row = {'request_id': request['request_id'], 'case_id': case['case_id'], 'arm': request['arm'],
               'speaker_index': case['speaker_index'], 'input_tokens': request['input_tokens']}
        if record is None:
            row.update(text=None, margin=None, output_chars=None, tokens=None, seconds=None)
        else:
            response = record['response']
            old.b.validate_completion(response, request['input_token_ids'])
            text = response['content']
            require(isinstance(text, str), 'Native content must be text')
            row.update(text=text, margin=margin(text, case) if old.normalize_text(text) else None,
                       output_chars=len(old.normalize_text(text)), tokens=response['tokens_predicted'],
                       seconds=record['latency_seconds'], **native_boundary(response),
                       marker_distance=distance(vector([text]), case['style'], MARKERS) if old.normalize_text(text) else None,
                       query_copy=old.copying_scores(text, [case['query']['text']]),
                       history_copy=old.copying_scores(text, [t['text'] for t in case['history']]),
                       reference_trigram_f1=old.character_trigram_f1(text, case['reference']['text']))
        rows.append(row)
    for case in plan['cases']:
        group = [r for r in rows if r['case_id'] == case['case_id']]
        k = min(20, *(r['output_chars'] or 0 for r in group))
        for row in group:
            row['prefix_k'] = k
            row['prefix_margin'] = margin(row['text'], case, k) if k else None
            row['eos_margin'] = row['margin'] if row.get('observed_native_boundary') else None
    contrasts = {}
    for metric in ('margin', 'prefix_margin', 'eos_margin', 'output_chars', 'tokens', 'seconds', 'marker_distance'):
        contrasts[metric] = {}
        for high, low in (('CORRECT', 'MISMATCH'), ('CORRECT', 'LENGTH'), ('LENGTH', 'NONE')):
            paired, known, missing = [], [], 0
            for speaker in range(8):
                differences = []
                for case in [c for c in plan['cases'] if c['speaker_index'] == speaker]:
                    group = {r['arm']: r for r in rows if r['case_id'] == case['case_id']}
                    a, z = group[high].get(metric), group[low].get(metric)
                    if a is None or z is None:
                        missing += 1
                    else:
                        differences.append(a - z)
                        known.append(a - z)
                if len(differences) == 2:
                    paired.append(statistics.fmean(differences))
            estimate = {**summary(paired), 'paired_contexts': len(known), 'missing_contexts': missing}
            if metric in ('margin', 'prefix_margin', 'eos_margin'):
                estimate['all_16_context_logical_bounds'] = [(sum(known) - 2 * missing) / 16,
                                                            (sum(known) + 2 * missing) / 16]
            contrasts[metric][high + '-' + low] = estimate
    memory = [e['data'] for e in events if e['kind'] in ('ready_memory', 'post_tokenization_memory', 'before_request_memory')]
    public = {'status': 'COMPLETE' if len(raw) == N else 'PARTIAL', 'evidence': 'OBSERVED_DEVELOPMENT_EXPLORATORY',
              'attempts': len(attempted), 'raw_responses': len(raw), 'conditions': {}, 'contrasts': contrasts,
              'prefix_k_distribution': dict(sorted(Counter(r['prefix_k'] for r in rows[::4]).items())),
              'native_stop_counts': dict(Counter(r.get('native_stop_type', 'MISSING') for r in rows)),
              'contradictory_stop_records': sum(r.get('contradictory_stop_flags', False) for r in rows),
              'resources': {**load(OUT / 'execution_receipt_v1.json'),
                            'peak_working_set_bytes': max((m['process']['peak_working_set'] for m in memory), default=0),
                            'minimum_available_ram_bytes': min((m['system']['available_physical'] for m in memory), default=None)},
              'bindings': {'manifest_sha256': sha(FROZEN), 'registration_sha256': sha(REGISTRATION),
                           'terminal_event_sha256': events[-1]['event_hash']},
              'human_labels': 0, 'validation_speakers_accessed': 0,
              'interpretation': load(DESIGN)['claim_boundary'], 'confirmatory_test': 'NONE'}
    for arm in ARMS:
        group = [r for r in rows if r['arm'] == arm]
        public['conditions'][arm] = {metric: {'n': sum(r.get(metric) is not None for r in group),
                    'mean': statistics.fmean(r[metric] for r in group if r.get(metric) is not None)
                    if any(r.get(metric) is not None for r in group) else None}
                    for metric in ('margin', 'prefix_margin', 'output_chars', 'tokens', 'input_tokens',
                                   'seconds', 'marker_distance', 'reference_trigram_f1')}
    if write_files:
        write(PRIVATE / 'analysis_private_v1.json', {'rows': rows})
        public['bindings']['private_analysis_sha256'] = sha(PRIVATE / 'analysis_private_v1.json')
        write(OUT / 'analysis_v1.json', public)
    return public


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('register', 'validate', 'preflight', 'run', 'analyze'))
    parser.add_argument('--preflight', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'register':
        value = register()
    elif args.action == 'validate':
        value = {'status': 'PASS', 'requests': len(validate()['requests'])}
    elif args.action == 'preflight':
        require(args.output is not None and args.output.parent == OUT, 'Public immutable preflight output required')
        value = preflight_receipt()
        write(args.output, value)
    elif args.action == 'run':
        require(args.preflight is not None, 'Preflight required')
        value = run(args.preflight)
    else:
        value = analyze()
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
