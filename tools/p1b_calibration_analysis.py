"""Offline, append-only analysis of the authorized P1b calibration; no model calls."""
import argparse
import base64
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import statistics

from personaslm import p1b_calibration as core
from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.p1b_readiness import contrast_weights
from personaslm.scientific_closure import reconcile_tokenizations

PUBLIC = Path('docs/validation/p1b/calibration_v1')
LOCAL = Path('results/p1b_execution/v1')
STATUSES = ('COMPLETE', 'TRUNCATED', 'CROSS_TURN', 'AMBIGUOUS')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def write_csv(path, rows):
    with Path(path).open('x', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def verify_transport(plan, events):
    """Reconcile native bytes, request IDs, actual settings and extracted spans."""
    starts = [e['data'] for e in events if e['kind'] == 'p1b_generation_started']
    sends = [e['data'] for e in events if e['kind'] == 'http_request' and e['data']['route'] == '/completion']
    receives = [e['data'] for e in events if e['kind'] == 'http_response' and e['data']['route'] == '/completion']
    raws = [e['data'] for e in events if e['kind'] == 'p1b_raw_generation']
    results = [e['data'] for e in events if e['kind'] == 'p1b_result']
    if not (len(starts) == len(sends) == len(receives) == len(raws) == len(results) == 192):
        raise ValueError('This complete-wave analysis requires all 192 persisted requests; preserve partial runs separately')
    if starts != plan['requests']:
        raise ValueError('Execution order or frozen request content differs')
    verified = [e for e in events if e['kind'] == 'p1b_live_prompt_verified']
    if len(verified) != 192 or max(e['sequence'] for e in verified) >= min(e['sequence'] for e in events if e['kind'] == 'p1b_generation_started'):
        raise ValueError('Live tokenizer gate did not precede generation')
    if [e['data'] for e in verified] != plan['requests']:
        raise ValueError('Live prompt/ID equality differs')
    first_attempt = min(e['sequence'] for e in events if e['kind'] == 'p1b_generation_started')
    # The existing tokenizer-only auditor deliberately rejects completion events.
    # Reconcile the complete pre-generation prefix, then audit completions below.
    native = reconcile_tokenizations([e for e in events if e['sequence'] < first_attempt],
                                    [(r['prompt'], r['input_token_ids']) for r in plan['requests']])
    outputs = []
    for row, send, receive, raw, result in zip(starts, sends, receives, raws, results):
        if send['payload'] != {'prompt': row['input_token_ids'], **core.DECODING}:
            raise ValueError('Native request differs from frozen settings/IDs')
        if receive['status'] != 200 or receive.get('incomplete'):
            raise ValueError('Incomplete or unsuccessful native response')
        body = base64.b64decode(receive['body_base64'], validate=True)
        response = json.loads(body.decode('utf-8'))
        if response != raw['response'] or raw['request_id'] != row['request_id'] or result['request_id'] != row['request_id']:
            raise ValueError('Native response/raw/result association mismatch')
        settings = response['generation_settings']
        for key, value in {'seed': 42, 'temperature': 0.0, 'n_predict': 96, 'top_p': 1.0, 'stop': [], 'ignore_eos': False}.items():
            if settings.get(key) != value:
                raise ValueError('Observed native decoding differs: ' + key)
        if response['prompt'] != row['prompt'] or response['tokens_evaluated'] != row['input_token_count'] or response['truncated']:
            raise ValueError('Native evaluated prompt differs or was context-truncated')
        if response['timings'].get('cache_n') != 0:
            raise ValueError('Observed prompt cache reuse')
        boundary = result['evaluation']['response_status']
        span = boundary['first_span']
        text = response['content']
        if text[span['start']:span['end']] != span['text'] or text_digest(text) != boundary['raw_sha256']:
            raise ValueError('First-reply offsets/raw hash differ')
        if boundary['removed_prefix'] + span['text'] + boundary['excluded_tail'] != text:
            raise ValueError('Parser does not reconstruct complete raw text')
        outputs.append({'request_id': row['request_id'], 'native_response_bytes_sha256': hashlib.sha256(body).hexdigest(),
                        'raw_text_sha256': text_digest(text), 'first_reply_sha256': text_digest(span['text']),
                        'generated_token_ids_sha256': core.canonical_hash(response['tokens']),
                        'generated_tokens': response['tokens_predicted'], 'prompt_sha256': row['prompt_sha256']})
    return {'native_tokenizations_reconciled': native, 'native_completions_reconciled': len(outputs),
            'all_live_ids_verified_before_generation': True, 'cache_n_zero': True,
            'evaluated_input_counts_match': True, 'evaluated_input_token_ids_returned': False,
            'limitation': 'The backend returns output IDs and input counts, not a separate evaluated-input-ID array.',
            'outputs': outputs}


def paired_structural(rows, cases):
    """Finite-bank contrasts, with case pairing and speaker sensitivity; no p values."""
    cells = defaultdict(dict)
    for row in rows:
        if row['case_id'] not in cases or row['condition'] in cells[row['case_id']]:
            raise ValueError('Unknown case or duplicate factorial cell')
        cells[row['case_id']][row['condition']] = row
    values, summaries = [], []
    for status in STATUSES:
        for name, weights in contrast_weights().items():
            selected = []
            for cid, case in cases.items():
                needed = [c for c, w in weights.items() if w]
                available = all(c in cells[cid] and cells[cid][c]['structural_status'] in STATUSES for c in needed)
                value = sum(weights[c] * (cells[cid][c]['structural_status'] == status) for c in needed) if available else None
                record = {'case_id': cid, 'persona_id': case['persona_id'], 'family': case['family'],
                          'contrast': name, 'outcome': status, 'evaluable': available, 'paired_value': value}
                values.append(record)
                if available:
                    selected.append(record)
            speaker = defaultdict(list)
            for row in selected:
                speaker[row['persona_id']].append(row['paired_value'])
            loo = [statistics.mean(r['paired_value'] for r in selected if r['persona_id'] != person) for person in speaker] if len(speaker) > 1 else []
            observed = [r['paired_value'] for r in selected]
            summaries.append({'contrast': name, 'outcome': status, 'eligible_cases': len(cases),
                'evaluable_cases': len(selected), 'missing_cases': len(cases) - len(selected),
                'speaker_clusters': len(speaker), 'estimate': statistics.mean(observed) if observed else None,
                'case_min': min(observed) if observed else None, 'case_max': max(observed) if observed else None,
                'nonzero_cases': sum(v != 0 for v in observed),
                'leave_one_speaker_out_min': min(loo) if loo else None,
                'leave_one_speaker_out_max': max(loo) if loo else None,
                'uncertainty_scope': 'Descriptive leave-one-speaker-out sensitivity, not a confidence interval or significance test',
                'weights': weights})
    return values, summaries


def review_packet(results, cases, mapping):
    """Keep treatment mapping outside the masked scoring CSV; leave all human fields blank."""
    old = core.csv_records(Path('docs/validation/p1/output_human_review_v1.csv'))
    fields = list(old[0])
    by_id = {r['request_id']: r for r in results}
    if len(by_id) != len(results) or set(by_id) != {r['request_id'] for r in mapping['responses']}:
        raise ValueError('Review mapping does not cover unique results')
    rows = []
    for entry in mapping['responses']:
        result = by_id[entry['request_id']]
        if any(result[k] != entry[k] for k in ('case_id', 'persona_id', 'condition', 'factors')):
            raise ValueError('Protected review mapping differs')
        case = cases[result['case_id']]
        boundary = result['evaluation']['response_status']
        span = boundary['first_span']
        row = dict.fromkeys(fields, '')
        row.update(review_version='p1b_calibration_output_human_review_v1',
            anonymous_case_id=mapping['case_aliases'][case['case_id']], anonymous_response_id=entry['anonymous_response_id'],
            current_question=case['question'], trusted_evidence=case['trusted_evidence'], evaluation_date=case['evaluation_date'],
            fixed_preceding_context='\n'.join(case['context']), reference_historical_facts=json.dumps(case['historical_source_fact'], ensure_ascii=False, sort_keys=True),
            historical_reference_scope='Case-level historical source shown in every condition; this does not disclose whether history was in the model prompt.',
            raw_first_reply=span['text'], raw_full_continuation=result['raw_response'], excluded_generated_continuation=boundary['excluded_tail'],
            structural_status=boundary['status'], native_stop_reason=json.dumps(result['raw_termination'], sort_keys=True),
            output_budget_reached=str(result['generated_tokens'] == 96).lower(), generated_tokens=result['generated_tokens'],
            first_reply_start=span['start'], first_reply_end=span['end'], removed_prefix=boundary['removed_prefix'],
            raw_sha256=boundary['raw_sha256'], first_reply_sha256=span['sha256'])
        for axis, applicable in case['applicability'].items():
            row['applicable_' + axis] = str(applicable).lower()
        # References guide evidence review; they are not scores of generated answers.
        row['reference_answer_json'] = json.dumps(case['expected_answer'], ensure_ascii=False, sort_keys=True)
        row['reference_interpretation'] = 'Use the proposition/question date and inclusive validity intervals; allow supported paraphrases and assess every delivered claim. Separate missing requested content from factual contradiction.'
        rows.append(row)
    return rows


def analyze(output):
    if Path('results/p1b_calibration/development_v1/active_writer.lock').exists():
        raise ValueError('Do not freeze analysis while the authorized writer is active')
    plan = core.load(core.MANIFEST)
    data = core.load(core.DATA)
    if digest(core.MANIFEST) != core.MANIFEST_SHA or digest(core.DATA) != core.DATA_SHA:
        raise ValueError('Frozen inputs changed')
    cases = {c['case_id']: c for c in data['cases']}
    claim = core.load(core.RUN_ROOT / 'claim.json')
    segments = core.ordered_segments(core.RUN_ROOT, claim)
    if len(segments) != 1:
        raise ValueError('This analysis version expects one uninterrupted authorized segment')
    directory, manifest = segments[0]
    events = read_events(directory)
    audit = core.audit_segments(plan, cases, [events])
    if any(r['technical_status'] != 'COMPLETED' for r in audit['rows']):
        raise ValueError('Incomplete wave; preserve and report without imputing missing outputs')
    transport = verify_transport(plan, events)
    results = [r['result'] for r in audit['rows']]
    raw_rows = []
    for result in results:
        case = cases[result['case_id']]
        boundary = result['evaluation']['response_status']
        raw_rows.append({k: result[k] for k in ('request_id','case_id','persona_id','condition','family','prompt_sha256','input_token_count','generated_tokens','stop_reason','latency_seconds')})
        raw_rows[-1].update(designed_complexity_level=case['designed_complexity_level'],
            actual_execution_status='COMPLETED', frozen_plan_executed_flag_preserved=result['executed'],
            structural_status=boundary['status'], unit_identifiable=boundary['unit_identifiable'],
            raw_empty=not bool(result['raw_response'].strip()), first_reply_empty=not bool(result['parsed_response'].strip()),
            first_reply_sha256=boundary['first_span']['sha256'], raw_sha256=boundary['raw_sha256'],
            excluded_continuation_chars=len(boundary['excluded_tail']), output_budget_reached=result['generated_tokens']==96,
            semantic_completeness='PENDING', **{axis: result['evaluation']['axes'][axis]['label'] for axis in core.AXES})
    paired, contrasts = paired_structural(raw_rows, cases)
    groups = {}
    for dimension in ('condition','family','designed_complexity_level'):
        groups[dimension] = {}
        for key in sorted({r[dimension] for r in raw_rows}):
            selected = [r for r in raw_rows if r[dimension] == key]
            groups[dimension][str(key)] = {'requests':len(selected), 'cases':len({r['case_id'] for r in selected}),
                'speaker_clusters':len({r['persona_id'] for r in selected}),
                'status_counts':{s:sum(r['structural_status']==s for r in selected) for s in STATUSES},
                'empty_first_reply':sum(r['first_reply_empty'] for r in selected),
                'semantic_eligible':{a:sum(cases[r['case_id']]['applicability'][a] for r in selected) for a in core.AXES}}
    coverage = {}
    for axis in core.AXES:
        selected = [r for r in raw_rows if cases[r['case_id']]['applicability'][axis]]
        coverage[axis] = {'eligible':len(selected),'inapplicable':192-len(selected),'automatically_scored':0,'human_scored':0,
            'pending':len(selected),'unverifiable_scored':0,'missing_response':0,
            'empty_first_reply':sum(r['first_reply_empty'] for r in selected),
            'eligible_cases':len({r['case_id'] for r in selected}), 'speaker_clusters':len({r['persona_id'] for r in selected}),
            'coverage':0.0, 'interpretation':'No semantic estimate; PENDING is workflow state, not factual Unverifiable or Incorrect'}
    mapping = core.load(LOCAL/'protected/review_mapping_v1.json')
    packet = review_packet(results,cases,mapping)
    stats = {'version':'p1b_calibration_analysis_v1','created_utc':utc_now(),
        'scope':'Exploratory development calibration; no new model calls or human outcome judgments',
        'run_directory':directory.relative_to(Path.cwd()).as_posix(),'run_id':manifest['run_id'],
        'planned':192,'attempted':audit['attempted'],'completed':len(results),'failed':0,
        'cases':len(cases),'speaker_clusters':len({c['persona_id'] for c in cases.values()}),
        'status_counts':dict(Counter(r['structural_status'] for r in raw_rows)),
        'stop_counts':dict(Counter(r['stop_reason'] for r in raw_rows)),
        'unit_identifiable':sum(r['unit_identifiable'] for r in raw_rows),
        'raw_empty':sum(r['raw_empty'] for r in raw_rows),'first_reply_empty':sum(r['first_reply_empty'] for r in raw_rows),
        'generated_tokens':{'min':min(r['generated_tokens'] for r in raw_rows),'max':max(r['generated_tokens'] for r in raw_rows),'total':sum(r['generated_tokens'] for r in raw_rows)},
        'latency_seconds':{'min':min(r['latency_seconds'] for r in raw_rows),'max':max(r['latency_seconds'] for r in raw_rows),'median':statistics.median(r['latency_seconds'] for r in raw_rows),'sum':sum(r['latency_seconds'] for r in raw_rows)},
        'coverage':coverage,'groups':groups,'contrasts':contrasts,
        'structural_analysis_version':'finite_bank_paired_structural_v1',
        'analysis_timing_disclosure':'Weights are the existing pre-generation precision-plan definitions. Offline summary code was developed during execution after initial raw responses were inspected; analyses are exploratory, not preregistered confirmatory tests.',
        'uncertainty':'Twelve purposively constructed speakers with two cases each. Leave-one-speaker-out ranges are sensitivity only; no population confidence interval, p value or significance claim.',
        'semantic_factorial_readiness':'PENDING_HUMAN_REVIEW','neutral_control_status':'OPEN; zero neutral requests; Wave 1 controls do not transfer to P1b',
        'model_sha256':core.MODEL_SHA,'backend_sha256':core.BACKEND_SHA,'dataset_sha256':core.DATA_SHA,'manifest_sha256':core.MANIFEST_SHA,
        'git_at_run_start':manifest['git'],'source_hashes_at_run_start':claim['source_hashes'],
        'plan_flags':'Frozen executed=false / authorization=false flags describe preparation-time artifacts; actual execution is established by write-ahead/raw/result events. Historical flags are not edited.',
        'algorithmic_opportunity_assessment':'Structural observations justify measurement review; no new corrective algorithm is implemented or demonstrated.'}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output/'analysis_v1.json',stats)
    atomic_json(output/'transport_integrity_v1.json',transport)
    write_csv(output/'request_measurements_v1.csv',raw_rows)
    write_csv(output/'structural_case_contrasts_v1.csv',paired)
    write_csv(output/'output_human_review_v1.csv',packet)
    # Full prompt/output records remain local; portable measurements and masked packet are public.
    atomic_json(LOCAL/'offline_reconstruction_v1.json',audit)
    artifact_hashes={p.relative_to(Path.cwd()).as_posix():digest(p) for p in directory.rglob('*') if p.is_file()}
    atomic_json(output/'execution_inventory_v1.json',{'version':'p1b_execution_inventory_v1','created_utc':utc_now(),
        'run_artifact_hashes':artifact_hashes,'dataset':{'path':core.DATA.as_posix(),'sha256':core.DATA_SHA},
        'manifest':{'path':core.MANIFEST.as_posix(),'sha256':core.MANIFEST_SHA},
        'protected_mapping_path':(LOCAL/'protected/review_mapping_v1.json').as_posix(),
        'protected_mapping_sha256':digest(LOCAL/'protected/review_mapping_v1.json'),
        'analysis_source_sha256':digest(Path(__file__)),
        'outputs':{p.name:digest(p) for p in output.iterdir() if p.is_file()}})
    print(json.dumps({k:stats[k] for k in ('planned','attempted','completed','failed','status_counts','stop_counts','unit_identifiable','raw_empty','first_reply_empty','coverage')}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    analyze(args.output)
