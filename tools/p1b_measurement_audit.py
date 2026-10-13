"""Offline measurement audit and split review views. Never launches a model."""
import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import random
import re
import statistics
import subprocess

from personaslm import p1b_calibration as core
from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.p1b_readiness import contrast_weights
from p1b_calibration_analysis import digest, text_digest, write_csv, verify_transport, paired_structural, review_packet

VERSION = 'p1b_measurement_audit_v1'
OUT = Path('docs/validation/p1b/measurement_audit_v1')
LOCAL = Path('results/p1b_measurement_audit/v1')
OLD = Path('docs/validation/p1b/calibration_v1/analysis_v1')
REVIEW_SEED = 714003  # Independent of execution 714001 and original alias assignment 714002.
BOOTSTRAP_SEED = 714004
BOOTSTRAP_REPLICATES = 10000
HUMAN_EXTRA = ('human_answer_delivery', 'human_required_components_notes', 'human_missing_metric_reason')
PROVENANCE = ('reviewer_notes', 'reviewer_id', 'review_assistance', 'prior_access_to_treatments_or_scores', 'reviewed_utc')
HIDE = {'raw_full_continuation', 'excluded_generated_continuation', 'structural_status',
        'native_stop_reason', 'output_budget_reached', 'generated_tokens', 'first_reply_start',
        'first_reply_end', 'removed_prefix', 'raw_sha256', 'human_reply_unit_confirmed', 'human_continuation_notes'}
RISKS = {
    'A': 'Direct lookup baseline; extra distractor records do not establish greater difficulty.',
    'B': 'Two to four requested components; response burden and integration are not separated.',
    'C': 'Inclusive date boundaries and prior-day lookup; explicit intervals may permit direct retrieval.',
    'D': 'Relational proof chains have unique terminal entities; correct output does not prove multi-step reasoning.',
    'E': 'Relevant old residence contrasts with current evidence; task family and history relevance are confounded.',
    'F': 'Explicit identity or unique role cues can resolve the target without difficult ambiguity.',
    'G': 'Past/current site selection; two-date demand and fixed output budget may interact; no causal budget test.',
    'H': 'H_L1/H_L2 do not establish context necessity; H_L3 retains consecutive User turns.'}


def split_views(master, seed=REVIEW_SEED):
    """Retain immutable source strings and aliases; do not copy structural anchors into stage 1."""
    ids = [r['anonymous_response_id'] for r in master]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate anonymous response ID')
    ordered = list(master)
    random.Random(seed).shuffle(ordered)
    semantic, structural = [], []
    for position, row in enumerate(ordered, 1):
        if any(v for k, v in row.items() if k.startswith('human_') or k in PROVENANCE):
            raise ValueError('Source is not a blank review master; preserve annotations separately')
        first = {k: v for k, v in row.items() if k not in HIDE}
        first.update(review_version='p1b_semantic_scoring_view_v2', presentation_index=str(position))
        first.update(dict.fromkeys(HUMAN_EXTRA, ''))
        semantic.append(first)
        second = {k: row[k] for k in ('anonymous_case_id', 'anonymous_response_id', 'raw_first_reply',
            'raw_full_continuation', 'excluded_generated_continuation', 'structural_status', 'native_stop_reason',
            'output_budget_reached', 'generated_tokens', 'first_reply_start', 'first_reply_end', 'removed_prefix',
            'raw_sha256', 'first_reply_sha256')}
        second.update(review_version='p1b_structural_review_view_v2', presentation_index=str(position),
            human_reply_unit_confirmed='', human_continuation_notes='', reviewer_id='', review_assistance='',
            prior_access_to_treatments_or_scores='', reviewed_utc='')
        structural.append(second)
    return semantic, structural


def validate_submission(master, submitted):
    """Validate immutable fields and explicitly explained missingness; never infer a human label."""
    expected = {r['anonymous_response_id']: r for r in master}
    ids = [r['anonymous_response_id'] for r in submitted]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError('Missing, duplicate or unknown response IDs')
    missing, assessed = Counter(), Counter()
    for row in submitted:
        original = expected[row['anonymous_response_id']]
        if set(row) != set(original):
            raise ValueError('Review schema differs')
        for key, value in original.items():
            if not (key.startswith('human_') or key in PROVENANCE) and row[key] != value:
                raise ValueError('Immutable field differs: ' + row['anonymous_response_id'] + ':' + key)
        if not all(row[k].strip() for k in ('reviewer_id', 'review_assistance', 'prior_access_to_treatments_or_scores')):
            raise ValueError('Actual reviewer identity/access/assistance required')
        for key, allowed in {
            'human_semantic_completeness': {'COMPLETE', 'INCOMPLETE', 'UNCERTAIN'},
            'human_answer_delivery': {'DELIVERED', 'PARTIAL', 'NOT_DELIVERED', 'UNCERTAIN'},
            'human_reply_unit_confirmed': {'PASS', 'FAIL', 'UNCERTAIN'},
        }.items():
            if key in row and row[key] not in allowed:
                raise ValueError('Invalid or missing label: ' + key)
        for axis in core.AXES:
            if 'applicable_' + axis not in row:
                continue  # Stage 2 boundary verification has no semantic ratings.
            categorical = axis in ('factual_consistency', 'temporal_consistency')
            key = 'human_' + axis + ('' if categorical else '_1_to_5')
            value = row[key]
            applicable = row['applicable_' + axis] == 'true'
            if not applicable:
                if value != 'Not Applicable':
                    raise ValueError('Frozen inapplicability requires Not Applicable')
            elif value == '':
                if not row.get('human_missing_metric_reason', '').strip():
                    raise ValueError('Missing eligible judgment without explicit reason')
                missing[axis] += 1
            elif value not in ({'Correct', 'Incorrect', 'Unverifiable'} if categorical else set('12345')):
                raise ValueError('Invalid rating or retrospective N/A: ' + key)
            else:
                if value == 'Unverifiable' and not row['human_unverifiable_reason'].strip():
                    raise ValueError('Unverifiable requires a reason')
                assessed[axis] += 1
        if 'human_evidence_quotations' in row and not row['human_evidence_quotations'].strip():
            raise ValueError('Case-specific evidence required')
    return {'valid_records': len(ids), 'assessed': dict(assessed), 'explicitly_missing': dict(missing),
            'scope': 'Schema and immutable-data validation only; no automated certification of human judgment quality'}


def cluster_intervals(case_values, repeats=BOOTSTRAP_REPLICATES, seed=BOOTSTRAP_SEED):
    """Separately versioned, post-output exploratory cluster percentile intervals."""
    groups = defaultdict(list)
    for row in case_values:
        if not row['evaluable']:
            raise ValueError('Structural bootstrap requires complete case coverage')
        groups[(row['outcome'], row['contrast'])].append(row)
    summaries = []
    for (outcome, contrast), rows in groups.items():
        by_speaker = defaultdict(list)
        for row in rows:
            by_speaker[row['persona_id']].append(row['paired_value'])
        speakers = sorted(by_speaker)
        rng = random.Random(seed)
        samples = []
        for _ in range(repeats):
            values = [v for _ in speakers for v in by_speaker[rng.choice(speakers)]]
            samples.append(statistics.mean(values))
        samples.sort()
        summaries.append({'outcome': outcome, 'contrast': contrast, 'eligible_cases': len(rows),
            'evaluable_cases': len(rows), 'speaker_clusters': len(speakers),
            'estimate': statistics.mean(r['paired_value'] for r in rows),
            'lower_percentile_95': samples[int(.025 * (repeats - 1))],
            'upper_percentile_95': samples[int(.975 * (repeats - 1))],
            'seed': seed, 'replicates': repeats,
            'scope': 'Post-output exploratory cluster bootstrap; 12 purposive speakers, not population or simultaneous coverage. Degenerate intervals do not establish absence.'})
    return summaries


def boundary_record(result):
    boundary = result['evaluation']['response_status']
    raw, first, tail = result['raw_response'], boundary['first_span']['text'], boundary['excluded_tail']
    if boundary['removed_prefix'] + first + tail != raw:
        raise ValueError('Raw reconstruction differs')
    markers = re.findall(r'(?im)^\s*(user|assistant|system|human|bot)\s*:', tail)
    return {k: result[k] for k in ('request_id', 'case_id', 'persona_id', 'condition', 'family', 'prompt_sha256',
        'input_token_count', 'generated_tokens', 'stop_reason', 'latency_seconds')} | {
        'structural_status': boundary['status'], 'unit_identifiable': boundary['unit_identifiable'],
        'boundary_reason': json.dumps(boundary['reasons']), 'raw_full_continuation': raw, 'first_reply': first,
        'excluded_continuation': tail, 'removed_prefix': boundary['removed_prefix'],
        'first_reply_start': boundary['first_span']['start'], 'first_reply_end': boundary['first_span']['end'],
        'raw_sha256': text_digest(raw), 'first_reply_sha256': text_digest(first),
        'native_termination_json': json.dumps(result['raw_termination'], sort_keys=True),
        'budget_termination': result['stop_reason'] == 'length',
        'explicit_think_open_unclosed': '<think>' in first and '</think>' not in first,
        'additional_role_markers': len(markers), 'additional_role_sequence': ','.join(markers),
        'raw_reconstruction': 'PASS', 'semantic_completeness': 'PENDING',
        'review_disposition': ('REQUIRED_BOUNDARY_ADJUDICATION; retain original ambiguous span; no invented first reply'
            if not boundary['unit_identifiable'] else 'REQUIRED_SEMANTIC_REVIEW; extraction alone is not semantic validity')}


def wave1_check():
    path = Path('docs/validation/p1/output_human_review_researcher_verified_v1.csv')
    rows = core.csv_records(path)
    if len(rows) != 96 or len({r['anonymous_response_id'] for r in rows}) != 96:
        raise ValueError('Wave 1 review identities differ')
    report = core.load(Path('docs/validation/p1/researcher_factorial_analysis_v1.json'))
    if digest(path) != report['annotation_sha256']:
        raise ValueError('Wave 1 confirmed annotation hash differs')
    old = {r['anonymous_response_id']: r for r in core.csv_records(Path('docs/validation/p1/output_human_review_v1.csv'))}
    for row in rows:
        for key, value in old[row['anonymous_response_id']].items():
            if not (key.startswith('human_') or key in PROVENANCE) and row[key] != value:
                raise ValueError('Wave 1 immutable review field changed: ' + key)
        if text_digest(row['raw_full_continuation']) != row['raw_sha256'] or text_digest(row['raw_first_reply']) != row['first_reply_sha256']:
            raise ValueError('Wave 1 text hash differs')
    return {'records': len(rows), 'cases': len({r['anonymous_case_id'] for r in rows}),
        'structural_status': dict(Counter(r['structural_status'] for r in rows)),
        'human_semantic_completeness': dict(Counter(r['human_semantic_completeness'] for r in rows)),
        'human_unit_confirmation': dict(Counter(r['human_reply_unit_confirmed'] for r in rows)),
        'budget_reached': sum(r['output_budget_reached'] == 'true' for r in rows),
        'native_stops': dict(Counter(r['native_stop_reason'] for r in rows)),
        'factual': dict(Counter(r['human_factual_consistency'] for r in rows)),
        'temporal': dict(Counter(r['human_temporal_consistency'] for r in rows)),
        'annotation_sha256': digest(path), 'unchanged_immutable_records': 96}


def build(output):
    if output.exists():
        raise FileExistsError(output)
    preflight = core.offline_preflight()
    plan, data = core.load(core.MANIFEST), core.load(core.DATA)
    cases = {c['case_id']: c for c in data['cases']}
    segments = core.ordered_segments(core.RUN_ROOT, core.load(core.RUN_ROOT / 'claim.json'))
    if len(segments) != 1:
        raise ValueError('Expected one preserved calibration segment')
    directory, manifest = segments[0]
    events = read_events(directory)
    audit = core.audit_segments(plan, cases, [events])
    transport = verify_transport(plan, events)
    results = [row['result'] for row in audit['rows']]
    mapping_path = Path('results/p1b_execution/v1/protected/review_mapping_v1.json')
    mapping = core.load(mapping_path)
    expected = review_packet(results, cases, mapping)
    master = core.csv_records(OLD / 'output_human_review_v1.csv')
    if [{k: str(v) for k, v in r.items()} for r in expected] != master:
        raise ValueError('Original review master differs from reconstructed raw data')
    rows = [boundary_record(r) for r in results]
    case_values, contrasts = paired_structural(rows, cases)
    previous = core.load(OLD / 'analysis_v1.json')
    if contrasts != previous['contrasts']:
        raise ValueError('Frozen descriptive structural results differ')
    intervals = cluster_intervals(case_values)
    first, second = split_views(master)
    protected = LOCAL / 'protected'
    protected.mkdir(exist_ok=False)
    (protected / 'treatment_mapping_v1.json').write_bytes(mapping_path.read_bytes())
    atomic_json(protected / 'presentation_order_v2.json', {'version': VERSION, 'created_utc': utc_now(),
        'seed': REVIEW_SEED, 'source_mapping_sha256': digest(mapping_path),
        'response_ids': [r['anonymous_response_id'] for r in first],
        'timing': 'Chosen during post-generation audit, independently of outcomes; aliases remain unchanged'})
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / 'semantic_scoring_view_v2.csv', first)
    write_csv(output / 'structural_review_view_v2.csv', second)
    # Analyst files intentionally omit anonymous aliases; do not send them with the initial scoring view.
    write_csv(output / 'response_boundary_audit_v1.csv', rows)
    write_csv(output / 'structural_case_contrasts_v1.csv', case_values)
    atomic_json(output / 'structural_uncertainty_v1.json', {'version': 'post_output_cluster_bootstrap_v1',
        'specification_timing': 'After seeing structural outputs; exploratory sensitivity only', 'results': intervals})
    task_rows = []
    for cid, case in cases.items():
        selected = [r for r in rows if r['case_id'] == cid]
        task_rows.append({'case_id': cid, 'persona_id': case['persona_id'], 'family': case['family'],
            'task_family': case['task_family'], 'designed_level': case['designed_complexity_level'],
            'required_components': len(case['expected_answer']['components']),
            'source_facts': len(case['facts']), 'query_steps': len(case['query']['steps']),
            'proof_facts': len(case['expected_answer']['proof_fact_ids']),
            'reference_components_json': json.dumps(case['expected_answer']['components'], sort_keys=True),
            'trusted_evidence_sha256': text_digest(case['trusted_evidence']), 'question_sha256': text_digest(case['question']),
            'context_sha256': core.canonical_hash(case['context']), 'temporal_eligible': case['applicability']['temporal_consistency'],
            'history_relevance': case['history_relevance'], 'requests': len(selected),
            'identifiable': sum(r['unit_identifiable'] for r in selected),
            'truncated': sum(r['structural_status'] == 'TRUNCATED' for r in selected),
            'budget_terminations': sum(r['budget_termination'] for r in selected),
            'interpretation_limit': RISKS[case['family']], 'empirical_difficulty': 'UNESTABLISHED',
            'semantic_judgments': 0})
    write_csv(output / 'task_discrimination_inventory_v1.csv', task_rows)
    atomic_json(output / 'native_transport_reaudit_v1.json', transport)
    atomic_json(output / 'offline_identity_reaudit_v1.json', preflight)
    atomic_json(output / 'wave1_verified_comparison_inputs_v1.json', wave1_check())
    stats = {'version': VERSION, 'created_utc': utc_now(), 'git_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        'git_dirty_status': subprocess.check_output(['git', 'status', '--short'], text=True),
        'run_id': manifest['run_id'], 'run_manifest_sha256': digest(directory / 'manifest.json'),
        'journal_events': len(events), 'journal_terminal_hash': events[-1]['event_hash'],
        'attempted': audit['attempted'], 'completed': len(results), 'failed': sum(r['error'] is not None for r in results),
        'status_counts': dict(Counter(r['structural_status'] for r in rows)),
        'stop_counts': dict(Counter(r['stop_reason'] for r in rows)),
        'identifiable': sum(r['unit_identifiable'] for r in rows),
        'raw_empty': sum(not r['raw_full_continuation'].strip() for r in rows),
        'first_reply_empty': sum(not r['first_reply'].strip() for r in rows),
        'unclosed_think_blocks': sum(r['explicit_think_open_unclosed'] for r in rows),
        'additional_role_marker_distribution': dict(Counter(r['additional_role_markers'] for r in rows)),
        'semantic_coverage': previous['coverage'], 'human_outcome_judgments': 0,
        'semantic_condition_effects': 'NOT_ESTIMATED', 'review_seed': REVIEW_SEED,
        'protected_mapping_sha256': digest(mapping_path), 'original_review_master_sha256': digest(OLD / 'output_human_review_v1.csv'),
        'new_model_requests': 0, 'new_tokenizer_requests': 0, 'new_server_launches': 0,
        'structural_contrasts_unchanged': True,
        'per_request_raw_parser_transport_reconciled': 192,
        'semantic_review_status': 'OPEN', 'secondary_review_status': 'OPEN',
        'uncertainty_is_not_preregistered': True,
        'source_sha256': digest(Path(__file__)),
        'artifact_hashes': {p.name: digest(p) for p in output.iterdir() if p.is_file()}}
    atomic_json(output / 'audit_summary_v1.json', stats)
    print(json.dumps({k: stats[k] for k in ('attempted', 'completed', 'failed', 'status_counts', 'stop_counts',
        'identifiable', 'unclosed_think_blocks', 'additional_role_marker_distribution', 'human_outcome_judgments', 'new_model_requests')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='action', required=True)
    b = sub.add_parser('build')
    b.add_argument('--output', type=Path, default=OUT)
    v = sub.add_parser('validate-review')
    v.add_argument('--master', type=Path, required=True)
    v.add_argument('--completed', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'build':
        build(args.output)
    else:
        print(json.dumps(validate_submission(core.csv_records(args.master), core.csv_records(args.completed))))
