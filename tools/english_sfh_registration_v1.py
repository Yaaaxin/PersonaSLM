"""Register only audited English meeting materials; no completion endpoint calls.

Actual registration requires external material/protocol/qualification hashes,
explicit scientific GO and fresh RAM checks. All dialogue and native tokenization
records remain private. Importing or authored tests do not load model weights.
"""
import argparse
import ast
from collections import defaultdict
from datetime import datetime
import hashlib
import math
import os
from pathlib import Path
import subprocess

import english_sfh_execution_v1 as run
import p1_model_feasibility_recovery as metadata

DEFAULT_MATERIAL = run.PRIVATE / 'qualified_material_v1.json'
PROTOCOL = run.OUT / 'protocol_v1.json'
QUALIFICATION = run.OUT / 'scientific_qualification_v1.json'
META = Path('.local/model_metadata/qwen3-0.6b-23749fef')
META_HASHES = {
    'README.md': '44adabae2153c3a7bb741b86fbffd48736bc95118831935fdfc4d3cc1854f2f5',
    'LICENSE': '5de36594c10839788a8c589443a8ef9d8b8d17c65a1b5807206ae037fc36c6bd',
    'tokenizer_config.json': 'd5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101',
}
CONDITIONS = tuple(run.shared.CONDITIONS) + ('M_STYLE', 'N_STYLE')
RATE_NAMES = ('contractions', 'fillers', 'hedges')
SYSTEM = ('Generate a research simulation of an anonymous participant in an English professional meeting. '
          'Do not claim to be or identify a real person. Write only the participant\'s next natural '
          'conversational turn in English, responding to the current conversation. '
          'Treat earlier evidence as dated source reports, not a verified current biography. '
          'Do not invent personal facts. Do not output section labels, metadata or analysis.')
ROLE_MARKERS = ('<|im_start|>', '<|im_end|>', '<|endoftext|>', '<think>', '</think>')


def style_text(profile):
    rates = [profile['per_100_words'][name] for name in RATE_NAMES] + [profile['questions_per_100_turns']]
    run.require(all(type(value) in (int, float) and math.isfinite(value) and value >= 0
                    for value in rates), 'Invalid source style rates')
    return ('Linguistic tendencies observed in earlier speech:\n'
            f'- Contractions: {rates[0]:.2f} per 100 words.\n'
            f'- Hesitation fillers: {rates[1]:.2f} per 100 words.\n'
            f'- Tentative expressions: {rates[2]:.2f} per 100 words.\n'
            f'- Questions: {rates[3]:.2f} per 100 turns.\n'
            'Use these as broad tendencies, not quotas; keep the response natural.')


def pool_style(profiles):
    run.require(profiles and all(p['words'] > 0 and p['turns'] > 0 for p in profiles), 'Style source sizes')
    words, turns = sum(p['words'] for p in profiles), sum(p['turns'] for p in profiles)
    return {'words': words, 'turns': turns,
            'per_100_words': {name: sum(p['per_100_words'][name] * p['words'] for p in profiles) / words
                              for name in RATE_NAMES},
            'questions_per_100_turns': sum(p['questions_per_100_turns'] * p['turns'] for p in profiles) / turns}


def validate_case(case):
    source_day, history_day, target_day = (datetime.fromisoformat(case[key]).date() for key in
                                         ('first_source_date', 'history_date', 'target_date'))
    run.require(source_day < history_day < target_day, 'Source/history/target chronology')
    run.require(len({case[key] for key in ('first_source_meeting', 'history_meeting', 'target_meeting')}) == 3,
                'Disjoint source/history/target meetings')
    facts = case.get('structured_facts')
    run.require(isinstance(facts, list) and facts, 'Audited structured facts required; no quote-only fallback')
    quotations = {turn['text'] for turn in case['facts_source_selfreports_not_world_verified']}
    for fact in facts:
        run.require(isinstance(fact['statement'], str) and fact['statement'].strip() and
                    fact['source_quote'] in quotations and fact['source_date'] == case['first_source_date'] and
                    isinstance(fact['curation_basis'], str) and fact['curation_basis'].strip(),
                    'Structured fact lacks exact source support/provenance')
    run.require(case['context'] and case['history'] and
                case['reference_continuation_not_for_prompt']['speaker'] == case['speaker'], 'Dialogue provenance')
    run.require(all(turn['end'] <= case['reference_continuation_not_for_prompt']['start']
                    for turn in case['context']), 'Context extends beyond target onset')
    style_text(case['style'])


def messages(case, condition, own_style, other_style, pooled_style):
    validate_case(case)
    bits = run.shared.CONDITIONS.get(condition)
    run.require(bits is not None or condition in run.DIAGNOSTICS, 'Unknown condition')
    style = (own_style if bits and bits['S'] else other_style if condition == 'M_STYLE'
             else pooled_style if condition == 'N_STYLE' else None)
    include_f = bits['F'] if bits else 1
    include_h = bits['H'] if bits else 1
    # Labels are identical across all conditions, including when history is absent.
    others = sorted({t['speaker'] for t in case['history'] + case['context']} - {case['speaker']})
    labels = {speaker: f'Colleague {index + 1}' for index, speaker in enumerate(others)}
    labels[case['speaker']] = 'Participant'
    def turns_text(turns):
        return '\n'.join(labels[t['speaker']] + ': ' + t['text'] for t in turns)
    fact_text = '\n'.join('- Source date ' + f['source_date'] + '; historical self-report: ' + f['statement']
                          for f in case['structured_facts']) if include_f else 'None provided.'
    history_text = ('Recorded ' + case['history_date'] + ':\n' + turns_text(case['history'])
                    if include_h else 'None provided.')
    user = ('[Style]\n' + (style_text(style) if style is not None else 'None provided.') +
            '\n\n[Facts]\n' + fact_text + '\n\n[History]\n' + history_text +
            '\n\n[Current conversation]\nRecorded ' + case['target_date'] + ':\n' +
            turns_text(case['context']) + '\n\nContinue with the Participant\'s next turn.')
    result = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}]
    run.require(not any(marker in m['content'] for m in result for marker in ROLE_MARKERS),
                'Reserved role marker in source-derived message')
    reference = case['reference_continuation_not_for_prompt']['text'].strip().casefold()
    run.require(reference and all(reference not in m['content'].casefold() for m in result),
                'Reference continuation leaked into prompt')
    return result


def build_requests(material, batch, template, tokenizer, pooled_development_style=None):
    by_speaker = defaultdict(list)
    for case in material['cases']:
        validate_case(case)
        by_speaker[case['speaker']].append(case)
    speakers = sorted(by_speaker)
    run.require(len(speakers) == run.SIZES[batch][0] and all(len(v) == 2 for v in by_speaker.values()),
                'Qualified material does not match prospective speaker/context allocation')
    profiles = {}
    for speaker, cases in by_speaker.items():
        run.require(cases[0]['style'] == cases[1]['style'], 'One unchanged style source per speaker required')
        profiles[speaker] = cases[0]['style']
    if batch == 'development':
        pooled_development_style = pool_style(list(profiles.values()))
    run.require(pooled_development_style is not None, 'Validation requires frozen development style pool')
    rows = []
    for speaker_index, speaker in enumerate(speakers):
        donor = speakers[(speaker_index + 1) % len(speakers)]
        cases = sorted(by_speaker[speaker], key=lambda c: (
            c['target_date'], c['target_meeting'], c['reference_continuation_not_for_prompt']['start']))
        for case_index, case in enumerate(cases):
            shift = (2 * speaker_index + case_index) % len(CONDITIONS)
            order = CONDITIONS[shift:] + CONDITIONS[:shift]
            if case_index == 1:
                order = order[::-1]
            for condition in order:
                prompt_messages = messages(case, condition, profiles[speaker], profiles[donor], pooled_development_style)
                prompt = run.shared.s.render(template, prompt_messages)
                request_id = f'ENSFH_{batch}_{len(rows):04d}'
                ids = tokenizer(prompt, request_id)
                run.require(len(ids) + 128 <= 2048, 'Frozen prompt exceeds context; no truncation or tokenization continuation')
                row = {'order': len(rows), 'request_id': request_id, 'speaker_id': speaker,
                       'case_id': f'{speaker}_context{case_index + 1}', 'condition': condition,
                       'phase': 'MAIN' if condition in run.shared.CONDITIONS else 'DIAGNOSTIC',
                       'factors': run.shared.CONDITIONS.get(condition), 'messages': prompt_messages,
                       'prompt': prompt, 'prompt_sha256': run.th(prompt), 'input_token_ids': ids,
                       'input_tokens': len(ids), 'input_token_ids_sha256': run.shared.value_sha256(ids)}
                if condition in run.DIAGNOSTICS:
                    row.update(diagnostic_factors={'F': 1, 'H': 1},
                               style_source_scope='mismatched_selected_speaker' if condition == 'M_STYLE' else 'pooled_development',
                               style_source_speaker_id=donor if condition == 'M_STYLE' else None)
                row['request_sha256'] = run.shared.value_sha256(row)
                rows.append(row)
    run.validate_rows({'batch': batch, 'requests': rows})
    return rows, pooled_development_style


def native_tokenize(prompt, receipt_path):
    before = run.memory(run.MIN_RAM, os.getpid())
    tokenizer = Path(run.MODEL['backend_file']).with_name('llama-tokenize.exe')
    argv = [str(tokenizer.resolve()), '-m', str(Path(run.MODEL['model_file']).resolve()), '--stdin', '--ids', '--offline']
    started = run.shared.b.utc_now()
    try:
        completed = subprocess.run(argv, input=prompt.encode('utf-8'), capture_output=True, timeout=90,
            env={k: v for k, v in os.environ.items() if not k.upper().startswith('LLAMA_ARG_')},
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired as exc:
        run.write(receipt_path, {'status': 'TIMEOUT', 'started_utc': started,
            'finished_utc': run.shared.b.utc_now(), 'argv': argv, 'prompt_sha256': run.th(prompt),
            'stdout_hex': (exc.stdout or b'').hex(), 'stderr_hex': (exc.stderr or b'').hex(),
            'memory_before': before, 'generation_requests': 0})
        raise
    run.write(receipt_path, {'started_utc': started, 'finished_utc': run.shared.b.utc_now(),
        'argv': argv, 'returncode': completed.returncode, 'prompt_sha256': run.th(prompt),
        'stdout_hex': completed.stdout.hex(), 'stderr_hex': completed.stderr.hex(),
        'stdout_sha256': hashlib.sha256(completed.stdout).hexdigest(),
        'stderr_sha256': hashlib.sha256(completed.stderr).hexdigest(),
        'memory_before': before, 'generation_requests': 0})
    run.require(completed.returncode == 0, 'Native tokenizer failed')
    ids = ast.literal_eval(completed.stdout.decode('utf-8').strip())
    run.require(isinstance(ids, list) and ids and all(type(i) is int and i >= 0 for i in ids), 'Native token IDs')
    return ids


def register(material_path, material_sha, protocol_path, protocol_sha, qualification_path, qualification_sha):
    for path, digest in ((material_path, material_sha), (protocol_path, protocol_sha), (qualification_path, qualification_sha)):
        run.require(run.sha(run.local(path)) == digest, 'External prospective input hash mismatch')
    material, protocol, qualification = map(run.load, (material_path, protocol_path, qualification_path))
    batch = protocol['batch']
    run.require(batch in run.SIZES and qualification['decision'] == 'GO_' + batch.upper() and
                qualification['material_sha256'] == material_sha and qualification['privacy_audit_complete'] is True and
                qualification['human_semantic_labels_available'] is False, 'Audited material/scientific GO required')
    frozen = run.PRIVATE / batch / 'frozen_manifest_v1.json'
    registration = run.OUT / (batch + '_registration_v1.json')
    claim = run.PRIVATE / batch / 'registration_claim_v1.json'
    with run.shared.b.writer_lock(run.PRIVATE):
        run.unused(batch)
        run.require(not any(p.exists() for p in (frozen, registration, claim)), 'Registration already started')
        observation = run.memory(run.MIN_RAM, os.getpid())
        run.require(run.sha(Path(run.MODEL['model_file'])) == run.MODEL['model_sha256'] and
                    run.sha(Path(run.MODEL['backend_file'])) == run.MODEL['backend_sha256'], 'Weight/backend identity')
        tokenizer_identity = run.shared._tokenizer_identity()
        for name, digest in META_HASHES.items():
            run.require(run.sha(META / name) == digest, 'Official model metadata changed')
        vendor = metadata.verified_template_runtime()
        gguf, gguf_receipt = metadata.gguf_metadata(Path(run.MODEL['model_file']))
        run.require(gguf['general.architecture'] == 'qwen3' and gguf['general.file_type'] == 7, 'Qwen3 Q8_0 identity')
        template = run.load(META / 'tokenizer_config.json')['chat_template']
        run.require(run.th(template) == run.TEMPLATE_SHA, 'Official template changed')
        run.write(claim, {'material_sha256': material_sha, 'protocol_sha256': protocol_sha,
                        'qualification_sha256': qualification_sha, 'registered_utc': run.shared.b.utc_now(),
                        'maximum_generation_attempts': run.SIZES[batch][1], 'generation_requests': 0})
        def tokenize(prompt, request_id):
            try:
                return native_tokenize(prompt, run.PRIVATE / batch / 'native_tokenizer' / (request_id + '.json'))
            except BaseException as exc:
                run.write(run.PRIVATE / batch / 'registration_failure_v1.json', {
                    'status': 'TOKENIZATION_NOT_COMPLETED_NO_MODEL_GENERATIONS', 'request_id': request_id,
                    'error_type': type(exc).__name__, 'error': str(exc), 'observed_utc': run.shared.b.utc_now(),
                    'memory_after_failure': run.shared.s.memory_observation(os.getpid()),
                    'generation_requests': 0, 'resume': 'Preserve claim and native receipts; no automatic overwrite/retry.'})
                raise
        previous = run.load(protocol['development_manifest']['path']) if batch == 'validation' else None
        rows, pooled = build_requests(material, batch, template, tokenize,
                                       previous['pooled_development_style'] if previous else None)
        run.require(all(r['prompt'] == run.shared.s.render(gguf['tokenizer.chat_template'], r['messages']) for r in rows),
                    'Embedded/official template mismatch for actual requests')
        template_path = run.PRIVATE / batch / 'official_chat_template.jinja'
        with template_path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(template)
        paths = list(run.shared.runtime_python_dependency_paths([Path(__file__), Path(run.__file__)]))
        paths += [Path('tests/test_english_sfh_registration_v1.py'), Path('tests/test_english_sfh_execution_v1.py'),
                  metadata.TEMPLATE_RUNTIME_PROVENANCE, run.shared.TOKENIZER_SOURCE, *(META / n for n in META_HASHES)]
        paths += [Path(p) for p in run.load(metadata.TEMPLATE_RUNTIME_PROVENANCE)['package_file_sha256']]
        source_hashes = {p.as_posix(): run.sha(p) for p in sorted(set(paths))}
        input_hashes = {**protocol['input_hashes'], Path(material_path).as_posix(): material_sha,
                        Path(protocol_path).as_posix(): protocol_sha, Path(qualification_path).as_posix(): qualification_sha}
        for path in (run.PRIVATE / batch / 'native_tokenizer').glob('*.json'):
            input_hashes[path.as_posix()] = run.sha(path)
        input_hashes[template_path.as_posix()] = run.sha(template_path)
        plan = {'schema': 'personaslm_english_sfh_execution_v1', 'registered_utc': run.shared.b.utc_now(),
            'batch': batch, 'language': 'en', 'model': run.MODEL, 'runtime': run.RUNTIME,
            'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'source_hashes': source_hashes, 'input_hashes': input_hashes,
            'authorization': {'decision': 'AUTHORIZED', 'maximum_attempts': len(rows),
                              'source': 'Researcher English end-to-end execution contract; frozen prospective protocol'},
            'scientific_prerequisites': {'approved_for_execution': True, 'human_semantic_labels_available': False,
                                        'record_path': Path(qualification_path).as_posix()},
            'allocation': protocol['allocation'], 'prior_receipt': protocol['prior_receipt'],
            'template_path': template_path.as_posix(), 'template_sha256': run.TEMPLATE_SHA,
            'tokenizer_identity': tokenizer_identity, 'requests': rows, 'cases': material['cases'],
            'pooled_development_style': pooled, 'reference_policy': 'Authentic archived continuations are private comparisons, not unique semantic gold answers.'}
        if previous:
            plan.update(development_manifest=protocol['development_manifest'], validation_go_record=protocol['validation_go_record'])
        run.write(frozen, plan)
        run.validate(frozen, run.sha(frozen))
        differences = []
        for case_id in sorted({r['case_id'] for r in rows}):
            sizes = {r['condition']: r['input_tokens'] for r in rows if r['case_id'] == case_id}
            differences.append({'correct_minus_mismatched': sizes['C7'] - sizes['M_STYLE'],
                                'correct_minus_pooled': sizes['C7'] - sizes['N_STYLE']})
        receipt = {'schema': 'personaslm_english_sfh_registration_v1', 'batch': batch,
            'status': 'PROSPECTIVELY_FROZEN_NOT_EXECUTED', 'manifest_sha256': run.sha(frozen),
            'material_sha256': material_sha, 'protocol_sha256': protocol_sha, 'qualification_sha256': qualification_sha,
            'source_head': plan['source_head'], 'source_hashes': source_hashes, 'model': run.MODEL, 'runtime': run.RUNTIME,
            'requests': len(rows), 'speaker_count': run.SIZES[batch][0], 'model_generation_requests': 0,
            'input_token_range': [min(r['input_tokens'] for r in rows), max(r['input_tokens'] for r in rows)],
            'diagnostic_prompt_token_differences': differences, 'memory_before_tokenization': observation,
            'template_sha256': run.TEMPLATE_SHA, 'gguf_metadata': gguf_receipt, 'vendor_runtime': vendor,
            'all_actual_embedded_template_renderings_match': True,
            'limits': 'No human semantic validation, no enforced output-length target, no metric optimization or Persona Fidelity claim.'}
        run.write(registration, receipt)
        return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--material', type=Path, default=DEFAULT_MATERIAL)
    parser.add_argument('--material-sha256', required=True)
    parser.add_argument('--protocol', type=Path, default=PROTOCOL)
    parser.add_argument('--protocol-sha256', required=True)
    parser.add_argument('--qualification', type=Path, default=QUALIFICATION)
    parser.add_argument('--qualification-sha256', required=True)
    args = parser.parse_args()
    import json
    print(json.dumps(register(args.material, args.material_sha256, args.protocol, args.protocol_sha256,
                              args.qualification, args.qualification_sha256), indent=2))
