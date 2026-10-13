"""Append-only, researcher-gated P1b review integration. No model/server calls."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
import statistics
import subprocess

from personaslm.human_factorial import quantile
from personaslm.journal import atomic_json, utc_now
from personaslm.p1b_readiness import contrast_weights
from p1b_measurement_audit import (OUT as AUDIT, OLD, core, digest, text_digest,
                                  split_views, validate_submission, PROVENANCE)
from p1b_calibration_analysis import write_csv

VERSION = 'p1b_researcher_semantic_integration_v1'
ANALYSIS_VERSION = 'p1b_verified_semantic_factorial_v1'
PUBLIC = Path('docs/validation/p1b/semantic_integration_v1')
STAGE_A = AUDIT / 'semantic_scoring_view_v2.csv'
STAGE_B = AUDIT / 'structural_review_view_v2.csv'
PINS = {STAGE_A: 'e2d4c098f7fb89539dff5998aee987322a28b6483f6bffb37c75d5323d1114ca',
        STAGE_B: 'e5b9d08625927cc64a47341923c99961235b5a0bf13e7d085ecf4e49d328a788'}
METRICS = {
    'response_relevance': ('human_response_relevance_1_to_5', 1, 5),
    'factual_consistency': ('human_factual_consistency', 0, 1),
    'temporal_consistency': ('human_temporal_consistency', 0, 1),
    'conversational_coherence': ('human_conversational_coherence_1_to_5', 1, 5),
    'semantic_completeness': ('human_semantic_completeness', 0, 1)}
SOURCE_FILES = [Path('tools/p1b_semantic_integration.py'), Path('tools/p1b_measurement_audit.py'),
    Path('tools/p1b_calibration_analysis.py'), Path('src/personaslm/p1b_calibration.py'),
    Path('src/personaslm/p1b_readiness.py'), Path('src/personaslm/human_factorial.py')]


def source_hashes():
    return {p.as_posix(): digest(p) for p in SOURCE_FILES}


def git_state():
    return {'sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'dirty_status': subprocess.check_output(['git', 'status', '--short'], text=True)}


def unique(rows):
    ids = [r['anonymous_response_id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate anonymous response IDs')
    return {r['anonymous_response_id']: r for r in rows}


def audit_package():
    """Reconcile existing masters/prompt identities; never rebuild their contents."""
    for path, pin in PINS.items():
        if digest(path) != pin:
            raise ValueError('Frozen review master byte hash changed: ' + str(path))
    a, b = core.csv_records(STAGE_A), core.csv_records(STAGE_B)
    original = core.csv_records(OLD / 'output_human_review_v1.csv')
    if (a, b) != split_views(original):
        raise ValueError('Existing two-stage views do not reconstruct from original master')
    aa, bb = unique(a), unique(b)
    if set(aa) != {f'BR{i:03}' for i in range(1, 193)} or set(aa) != set(bb):
        raise ValueError('Expected exactly BR001 through BR192 in both stages')
    counts = Counter(r['anonymous_case_id'] for r in a)
    if len(counts) != 24 or set(counts.values()) != {8}:
        raise ValueError('Expected 24 cases with eight outputs each')
    hidden = {'structural_status', 'native_stop_reason', 'condition', 'factors', 'request_id',
              'raw_full_continuation', 'excluded_generated_continuation', 'generated_tokens'}
    if hidden.intersection(a[0]):
        raise ValueError('Stage A exposes structural/treatment columns')
    for rid, row in aa.items():
        other = bb[rid]
        if row['raw_first_reply'] != other['raw_first_reply'] or row['anonymous_case_id'] != other['anonymous_case_id']:
            raise ValueError('Stage A/B source association differs')
        first, raw = row['raw_first_reply'], other['raw_full_continuation']
        if text_digest(first) != row['first_reply_sha256'] or text_digest(raw) != other['raw_sha256']:
            raise ValueError('Original text hash differs')
        if (raw[int(other['first_reply_start']):int(other['first_reply_end'])] != first or
            other['removed_prefix'] + first + other['excluded_generated_continuation'] != raw):
            raise ValueError('Original parser reconstruction differs')
    plan, data = core.load(core.MANIFEST), core.load(core.DATA)
    if digest(core.MANIFEST) != core.MANIFEST_SHA or digest(core.DATA) != core.DATA_SHA:
        raise ValueError('Frozen dataset or request manifest changed')
    core.validate_plan(data, plan)
    mapping_path = Path(core.load(AUDIT / 'review_package_manifest_v2.json')['protected_mapping_path'])
    mapping = core.load(mapping_path)
    if digest(mapping_path) != core.load(AUDIT / 'review_package_manifest_v2.json')['protected_mapping_sha256']:
        raise ValueError('Protected mapping changed')
    requests = {r['request_id']: r for r in plan['requests']}
    cases = {r['case_id']: r for r in data['cases']}
    by_mapping = unique(mapping['responses'])
    if set(by_mapping) != set(aa) or len({m['request_id'] for m in by_mapping.values()}) != 192:
        raise ValueError('Mapping coverage or request uniqueness differs')
    seen = set()
    for rid, m in by_mapping.items():
        request, case = requests[m['request_id']], cases[m['case_id']]
        if any(m[k] != request[k] for k in ('case_id', 'persona_id', 'condition', 'factors')):
            raise ValueError('Treatment mapping differs from frozen manifest')
        if mapping['case_aliases'][m['case_id']] != aa[rid]['anonymous_case_id']:
            raise ValueError('Case alias differs')
        if (m['case_id'], m['condition']) in seen:
            raise ValueError('Duplicate factorial cell')
        seen.add((m['case_id'], m['condition']))
        for axis, value in case['applicability'].items():
            if aa[rid]['applicable_' + axis] != str(value).lower():
                raise ValueError('Frozen applicability differs')
        for field, value in [('current_question', case['question']), ('trusted_evidence', case['trusted_evidence']),
                             ('evaluation_date', case['evaluation_date']), ('fixed_preceding_context', '\n'.join(case['context']))]:
            if aa[rid][field] != value:
                raise ValueError('Evidence/question/reference/context differs')
    return a, b, mapping, {
        'version': VERSION, 'verified_utc': utc_now(), 'records': 192, 'cases': 24, 'speakers': 12,
        'stage_a_columns': len(a[0]), 'stage_b_columns': len(b[0]), 'text_hashes_verified': 192,
        'factorial_mappings_verified': 192, 'source_prompts_reconstructed': 192,
        'eligibility': {axis: sum(r['applicable_' + axis] == 'true' for r in a) for axis in core.AXES},
        'structural_statuses': dict(Counter(r['structural_status'] for r in b)),
        'master_hashes': {p.as_posix(): h for p, h in PINS.items()}, 'mapping_sha256': digest(mapping_path),
        'dataset_sha256': core.DATA_SHA, 'manifest_sha256': core.MANIFEST_SHA,
        'blank_human_fields': True, 'masking': 'Column masking verified; text cues/prior knowledge can reveal treatment.',
        'human_reviews_imported': 0, 'new_inference': 0}


def immutable_source(master, rows):
    """Retain incomplete/proposed coding as provenance, never treat it as confirmed."""
    source, supplied = unique(master), unique(rows)
    if set(source) != set(supplied):
        raise ValueError('Provenance source IDs differ')
    for rid, row in supplied.items():
        if list(row) != list(source[rid]):
            raise ValueError('Original review schema/order differs')
        for key, value in source[rid].items():
            if not (key.startswith('human_') or key in PROVENANCE) and row[key] != value:
                raise ValueError('Immutable source field changed: ' + rid + '/' + key)


def validate_confirmation(c, a, b, a_hash, b_hash):
    if (c.get('version') != VERSION or c.get('review_status') != 'RESEARCHER_CONFIRMED' or
        c.get('reviewer_id') != 'Yaxin_ZHENG' or c.get('final_decision_authority') != 'researcher' or
        c.get('decision_source') != 'researcher'):
        raise ValueError('Explicit researcher confirmation is absent or invalid')
    if c.get('confirmed_artifact_sha256') != {'stage_a': a_hash, 'stage_b': b_hash}:
        raise ValueError('Confirmation must bind exact completed A/B files')
    ids = c.get('confirmed_response_ids')
    if not isinstance(ids, list) or len(ids) != 192 or set(ids) != set(unique(a)) or set(ids) != set(unique(b)):
        raise ValueError('Researcher must confirm exactly 192 distinct response IDs')
    if not all(isinstance(c.get(k), str) and c[k].strip() for k in ('confirmation_statement', 'review_method', 'original_assessment_provenance')):
        raise ValueError('Explicit confirmation and accurate provenance statements required')
    if type(c.get('ai_assisted_structured_coding')) is not bool:
        raise ValueError('AI coding provenance must be explicitly true or false')
    if c.get('stage_a_condition_labels_masked') not in ('YES', 'NO', 'UNCERTAIN') or c.get('stage_b_seen_before_initial_stage_a') not in ('YES', 'NO', 'UNCERTAIN'):
        raise ValueError('Actual masking and prior structural access disclosure required')
    if c.get('prior_treatment_knowledge') not in ('YES', 'NO', 'UNCERTAIN'):
        raise ValueError('Prior treatment knowledge disclosure required')
    if c.get('stage_a_revised_after_stage_b') not in ('YES', 'NO', 'UNCERTAIN'):
        raise ValueError('Revision history disclosure required')
    for row in a + b:
        if row['reviewer_id'] != c['reviewer_id']:
            raise ValueError('Final reviewer ID differs from confirmation')
    # Optional times are copied, never substituted with import time.
    stamp = c.get('confirmation_utc')
    if stamp not in (None, ''):
        from datetime import datetime
        if not isinstance(stamp, str):
            raise ValueError('Invalid recorded confirmation timestamp')
        datetime.fromisoformat(stamp.replace('Z', '+00:00'))


def revision_diff(before, after, source_name):
    old = unique(before)
    return [{'source_version': source_name, 'anonymous_response_id': r['anonymous_response_id'],
             'field': k, 'original': old[r['anonymous_response_id']][k], 'confirmed': v}
            for r in after for k, v in r.items() if old[r['anonymous_response_id']][k] != v]


def register(stage_a, stage_b, confirmation, output, initial=None, proposed=None):
    if output.exists():
        raise FileExistsError('Never overwrite an annotation registration: ' + str(output))
    master_a, master_b, _, audit = audit_package()
    a, b = core.csv_records(stage_a), core.csv_records(stage_b)
    immutable_source(master_a, a); immutable_source(master_b, b)
    check_a, check_b = validate_submission(master_a, a), validate_submission(master_b, b)
    c = core.load(confirmation)
    validate_confirmation(c, a, b, digest(stage_a), digest(stage_b))
    if c['stage_a_revised_after_stage_b'] == 'YES' and initial is None:
        raise ValueError('Preserve initial Stage A when revisions after Stage B are declared')
    for row in b:
        if (row['human_reply_unit_confirmed'] != 'PASS' or row['structural_status'] == 'AMBIGUOUS') and not row['human_continuation_notes'].strip():
            raise ValueError('Boundary disagreement/ambiguity requires explicit researcher disposition')
    sources = {'stage_a.csv': stage_a, 'stage_b.csv': stage_b, 'confirmation.json': confirmation}
    changes = []
    for path, name in ((initial, 'stage_a_initial.csv'), (proposed, 'stage_a_proposed.csv')):
        if path is not None:
            rows = core.csv_records(path); immutable_source(master_a, rows)
            changes.extend(revision_diff(rows, a, name)); sources[name] = path
    # Validate all inputs before creating any destination. Each supplied source is copied byte-for-byte.
    output.mkdir(parents=True, exist_ok=False)
    for name, path in sources.items():
        with (output / name).open('xb') as f:
            f.write(Path(path).read_bytes())
    atomic_json(output / 'correction_history_v1.json', {'version': VERSION, 'changes': changes,
        'source_availability': {'initial_stage_a': initial is not None, 'proposed_coding': proposed is not None},
        'scope': 'Only differences between actually supplied versions; absent history is not reconstructed.'})
    record = {'version': VERSION, 'registered_utc': utc_now(), 'review_status': 'RESEARCHER_CONFIRMED',
        'annotation_count': 192, 'reviewer_id': c['reviewer_id'], 'final_decision_authority': c['final_decision_authority'],
        'confirmation_provenance': c, 'stage_a_validation': check_a, 'stage_b_validation': check_b,
        'source_availability': {'initial_stage_a': initial is not None, 'proposed_coding': proposed is not None},
        'corrected_field_count': len(changes), 'boundary_unresolved': sum(r['human_reply_unit_confirmed'] != 'PASS' for r in b),
        'packet_integrity': audit, 'git': git_state(), 'source_sha256': digest(Path(__file__)),
        'source_hashes': source_hashes(),
        'files': {p.name: digest(p) for p in output.iterdir() if p.is_file()},
        'no_independent_reviewer_or_agreement_claim': True, 'new_inference': 0}
    atomic_json(output / 'registration_v1.json', record)
    return record


def metric(row, name):
    """Keep original human category and distinct reasons for unknown numeric outcomes."""
    field, lo, hi = METRICS[name]
    h, b = row['stage_a'], row['stage_b']
    label = h[field]
    eligible = True if name == 'semantic_completeness' else h['applicable_' + name] == 'true'
    if not eligible:
        return {'eligible': False, 'label': label, 'state': 'not_applicable', 'value': None, 'lo': lo, 'hi': hi}
    if b['human_reply_unit_confirmed'] != 'PASS':
        state, value = 'boundary_unresolved', None
    elif label == '':
        state, value = 'missing_judgment', None
    elif name in ('response_relevance', 'conversational_coherence'):
        state, value = 'scored', float(label)
    elif label in ('Correct', 'COMPLETE'):
        state, value = 'scored', 1.0
    elif label in ('Incorrect', 'INCOMPLETE'):
        state, value = 'scored', 0.0
    else:
        state, value = ('unverifiable' if label == 'Unverifiable' else 'uncertain'), None
    return {'eligible': True, 'label': label, 'state': state, 'value': value, 'lo': lo, 'hi': hi}


def bounds(outcomes, weights):
    low = high = 0.0
    for condition, weight in weights.items():
        if not weight:
            continue
        r = outcomes[condition]
        lo, hi = (r['lo'], r['hi']) if r['value'] is None else (r['value'], r['value'])
        low += weight * (lo if weight > 0 else hi)
        high += weight * (hi if weight > 0 else lo)
    return low, high


def clustered_interval(points, seed, replicates):
    """Resample complete speaker bundles; estimate explicitly conditions on evaluable pairs."""
    groups = defaultdict(list)
    for row in points:
        groups[row['persona_id']].append(row['difference'])
    speakers = sorted(groups)
    evaluable_speakers = sum(any(v is not None for v in values) for values in groups.values())
    if not any(v is not None for values in groups.values() for v in values) or len(speakers) < 2:
        return {'interval': None, 'valid_resamples': 0, 'empty_resamples': 0, 'speaker_clusters': len(speakers),
                'evaluable_speaker_clusters': evaluable_speakers}
    rng = random.Random(seed); samples = []; empty = 0
    for _ in range(replicates):
        values = [v for _ in speakers for v in groups[rng.choice(speakers)] if v is not None]
        if values:
            samples.append(statistics.mean(values))
        else:
            empty += 1
    samples.sort()
    interval = [quantile(samples, .025), quantile(samples, .975)] if samples else None
    return {'interval': interval, 'valid_resamples': len(samples), 'empty_resamples': empty,
        'speaker_clusters': len(speakers), 'evaluable_speaker_clusters': evaluable_speakers,
        'seed': seed, 'replicates': replicates,
        'degenerate': interval is not None and interval[0] == interval[1],
        'scope': 'Exploratory percentile interval of evaluable-pair mean; missingness may select pairs. Small purposive clusters, no population/annotation uncertainty or simultaneous coverage guarantee.'}


def compute(rows, seed=714005, replicates=10000):
    """Pure analysis for verified records (or explicitly synthetic unit fixtures)."""
    if type(replicates) is not int or replicates < 100:
        raise ValueError('At least 100 bootstrap replicates required')
    cells = defaultdict(dict)
    for row in rows:
        cid, cond = row['case_id'], row['condition']
        if cond in cells[cid] or cond not in contrast_weights()['S']:
            raise ValueError('Unknown or duplicate factorial cell')
        cells[cid][cond] = row
    for block in cells.values():
        if set(block) != set(contrast_weights()['S']):
            raise ValueError('Missing factorial cell')
        if len({(r['persona_id'], r['family']) for r in block.values()}) != 1:
            raise ValueError('Case identity/family differs between cells')
        for axis in core.AXES:
            if len({r['stage_a']['applicable_' + axis] for r in block.values()}) != 1:
                raise ValueError('Within-case metric applicability differs')
    distributions, all_points, summaries = [], [], []
    for name in METRICS:
        for family in ['ALL'] + sorted({r['family'] for r in rows}):
            for cond in contrast_weights()['S']:
                subset = [r for r in rows if r['condition'] == cond and (family == 'ALL' or r['family'] == family)]
                outcomes = [metric(r, name) for r in subset]
                values = [o['value'] for o in outcomes if o['value'] is not None]
                distributions.append({'metric': name, 'family': family, 'condition': cond, 'received': len(subset),
                    'eligible': sum(o['eligible'] for o in outcomes), 'not_applicable': sum(not o['eligible'] for o in outcomes),
                    'judgments_entered': sum(o['eligible'] and bool(o['label']) for o in outcomes),
                    'numerically_evaluable': len(values), 'missing_judgments': sum(o['eligible'] and not o['label'] for o in outcomes),
                    'unverifiable_labels': sum(o['label'] == 'Unverifiable' for o in outcomes),
                    'boundary_unresolved': sum(o['state'] == 'boundary_unresolved' for o in outcomes),
                    'unscorable_numeric': sum(o['eligible'] and o['value'] is None for o in outcomes),
                    'label_distribution': dict(Counter(o['label'] or 'MISSING' for o in outcomes)),
                    'analysis_state_distribution': dict(Counter(o['state'] for o in outcomes)),
                    'assessed_only_mean': statistics.mean(values) if values else None})
        for contrast, weights in contrast_weights().items():
            points = []; na = 0
            for cid, block in sorted(cells.items()):
                outcomes = {c: metric(r, name) for c, r in block.items()}
                if not all(o['eligible'] for o in outcomes.values()):
                    na += 1; continue
                needed = [c for c, w in weights.items() if w]
                evaluable = all(outcomes[c]['value'] is not None for c in needed)
                lo, hi = bounds(outcomes, weights)
                points.append({'metric': name, 'contrast': contrast, 'case_id': cid,
                    'persona_id': block['C0']['persona_id'], 'family': block['C0']['family'],
                    'evaluable': evaluable,
                    'difference': sum(weights[c] * outcomes[c]['value'] for c in needed) if evaluable else None,
                    'lower_unknown_bound': lo, 'upper_unknown_bound': hi,
                    'outcomes': outcomes})
            for family in ['ALL'] + sorted({r['family'] for r in rows}):
                selected = [p for p in points if family == 'ALL' or p['family'] == family]
                values = [p['difference'] for p in selected if p['evaluable']]
                summaries.append({'metric': name, 'contrast': contrast, 'family': family, 'weights': weights,
                    'eligible_cases': len(selected), 'evaluable_cases': len(values), 'unknown_cases': len(selected)-len(values),
                    'speaker_clusters': len({p['persona_id'] for p in selected}),
                    'evaluable_speaker_clusters': len({p['persona_id'] for p in selected if p['evaluable']}),
                    'inapplicable_cases': na if family == 'ALL' else sum(block['C0']['family']==family and not metric(block['C0'],name)['eligible'] for block in cells.values()),
                    'evaluable_pair_estimate': statistics.mean(values) if values else None,
                    'all_eligible_identification_bounds': [statistics.mean(p['lower_unknown_bound'] for p in selected), statistics.mean(p['upper_unknown_bound'] for p in selected)] if selected else None,
                    'nonzero_cases': [p['case_id'] for p in selected if p['difference'] is not None and p['difference'] != 0],
                    'uncertainty': clustered_interval(selected, seed, replicates) if family == 'ALL' else None,
                    'interpretation': 'Simple/average factorial contrast of distinct endpoint; family subgroup descriptive. Bounds are unknown-value identification bounds, not confidence intervals.'})
            all_points.extend(points)
    return {'version': ANALYSIS_VERSION, 'responses': len(rows), 'paired_cases': len(cells),
        'speaker_clusters': len({r['persona_id'] for r in rows}), 'seed': seed, 'replicates': replicates,
        'distributions': distributions, 'case_level': all_points, 'contrasts': summaries,
        'structure_by_semantic_completeness': dict(Counter(r['stage_b']['structural_status']+' / '+r['stage_a']['human_semantic_completeness'] for r in rows)),
        'original_structure_preserved': True, 'significance_claim': False, 'neutral_control_adjusted': False,
        'persona_fidelity_combined': False, 'c0_correct_filter': False,
        'algorithmic_opportunity_assessment': {
            'Observed Failure Modes': 'Inspect the separate distributions, completeness and boundary-dispute counts; no structural-to-factual recoding.',
            'Existing Methods': 'Consult P1b_calibration_algorithmic_opportunity.md and related_work_novelty_matrix.md; reverify relevant published methods before any originality claim.',
            'Potential Algorithmic Improvements': 'Candidates only after researcher interpretation of reproducible errors; no method selected automatically from contrast direction.',
            'Validation Feasibility': 'Use separate development and independent evaluation with existing retrieval, temporal-filtering, native-template and verification baselines as appropriate.',
            'Publication Value': 'No automatic discovery/novelty claim; measurement validity, precision, independent replication and external validity remain necessary.'}}


def analyze_registration(registration_dir, output, seed=714005, replicates=10000):
    if output.exists():
        raise FileExistsError(output)
    reg = core.load(registration_dir / 'registration_v1.json')
    if reg.get('version') != VERSION or reg.get('review_status') != 'RESEARCHER_CONFIRMED':
        raise ValueError('A verified researcher registration is required before analysis')
    for name, pin in reg['files'].items():
        if Path(name).name != name or digest(registration_dir / name) != pin:
            raise ValueError('Registered annotation/provenance artifact changed')
    master_a, master_b, mapping, audit = audit_package()
    a, b = core.csv_records(registration_dir / 'stage_a.csv'), core.csv_records(registration_dir / 'stage_b.csv')
    validate_submission(master_a, a); validate_submission(master_b, b)
    c = core.load(registration_dir / 'confirmation.json')
    validate_confirmation(c, a, b, digest(registration_dir / 'stage_a.csv'), digest(registration_dir / 'stage_b.csv'))
    aa, bb = unique(a), unique(b)
    cases = {r['case_id']: r for r in core.load(core.DATA)['cases']}
    rows = [{**m, 'family': cases[m['case_id']]['family'], 'stage_a': aa[m['anonymous_response_id']],
             'stage_b': bb[m['anonymous_response_id']]} for m in mapping['responses']]
    result = compute(rows, seed, replicates)
    result.update(registration_sha256=digest(registration_dir/'registration_v1.json'),
        annotation_hashes={'stage_a':digest(registration_dir/'stage_a.csv'),'stage_b':digest(registration_dir/'stage_b.csv')},
        mapping_sha256=audit['mapping_sha256'], dataset_sha256=core.DATA_SHA, git=git_state(),
        source_sha256=digest(Path(__file__)), source_hashes=source_hashes(), created_utc=utc_now(),
        provenance_scope=c, analysis_timing='Exploratory post-generation analysis; implementation prepared before outcome annotations were supplied')
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / 'analysis_v1.json', result)
    atomic_json(output / 'unblinded_analysis_records_v1.json', {'version': ANALYSIS_VERSION, 'rows': rows})
    report = '# P1b Researcher-Confirmed Semantic Analysis\n\nMaintainer: Yaxin ZHENG. Protocol v1.1. Exploratory development evidence.\n\n'
    report += 'Separate endpoint distributions, case-paired values, unknown bounds and whole-speaker intervals are in `analysis_v1.json`. All eight cells and all eligible cases remain. No composite reliability score, significance claim or population-null inference is made.\n\n'
    report += f"Responses: {result['responses']}; paired cases: {result['paired_cases']}; speaker clusters: {result['speaker_clusters']}.\n\n"
    report += '## Algorithmic Opportunity Assessment\n\n'
    report += '\n\n'.join('### '+key+'\n\n'+value for key,value in result['algorithmic_opportunity_assessment'].items())
    with (output/'analysis_report_v1.md').open('x',encoding='utf-8') as f:
        f.write(report+'\n')
    atomic_json(output/'manifest_v1.json',{'version':ANALYSIS_VERSION,'created_utc':utc_now(),
        'registered_input_sha256':digest(registration_dir/'registration_v1.json'),
        'files':{p.name:digest(p) for p in output.iterdir()},'new_inference':0})
    return {'responses':192,'paired_cases':24,'speakers':12,'semantic_effects_computed':True}


def prepare(output):
    if output.exists():
        raise FileExistsError(output)
    a,b,_,audit = audit_package()
    output.mkdir(parents=True,exist_ok=False)
    atomic_json(output/'package_integrity_v1.json',audit)
    template={'version':VERSION,'review_status':'PENDING','reviewer_id':None,
        'final_decision_authority':None,'decision_source':None,'confirmation_statement':'',
        'review_method':'','original_assessment_provenance':'','ai_assisted_structured_coding':None,
        'stage_a_condition_labels_masked':None,'stage_b_seen_before_initial_stage_a':None,
        'prior_treatment_knowledge':None,'stage_a_revised_after_stage_b':None,
        'confirmed_artifact_sha256':{'stage_a':None,'stage_b':None},
        'confirmed_response_ids':[],'confirmation_utc':None,
        'instruction':'Complete only from actual researcher confirmation. Hashes bind completed files, not blank masters. No reviewer or decisions supplied by this template.'}
    atomic_json(output/'researcher_confirmation_PENDING_v1.json',template)
    atomic_json(output/'analysis_specification_v1.json',{'version':ANALYSIS_VERSION,'created_utc':utc_now(),
        'source_sha256':digest(Path(__file__)),'source_hashes':source_hashes(),'git':git_state(),'weights':contrast_weights(),
        'metrics':METRICS,'seed':714005,'bootstrap_replicates':10000,'units':{'cases':24,'speakers':12},
        'scope':'Implementation prepared after outputs existed, before researcher semantic ratings; exploratory not confirmatory.',
        'gate':'Exact-file researcher confirmation and two-stage immutable validation required; preparation computes no semantic effects.',
        'unresolved_boundary_policy':'Keep supplied labels but treat numeric primary outcomes as unknown until first unit is confirmed; never relabel the frozen structure.',
        'missingness_policy':'Keep missing, Unverifiable, unresolved boundary, Incorrect and frozen N/A separate; report label and analysis-state counts plus signed unknown bounds.',
        'sampling':'Whole-speaker bundles preserve all cases/cells; case-weighted mean. Family-specific summaries are descriptive, no per-family resampling with three cases.',
        'interval_scope':'Exploratory evaluable-pair percentile intervals; no simultaneous or population coverage guarantee. Unknown bounds are not confidence intervals.',
        'novelty':'S/F/H, conditional task effects, structural/semantic differences and future history/model/external validity questions are hypotheses; no expected effect imposed.',
        'semantic_effects_computed':False,'new_inference':0})
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('prepare');p.add_argument('--output',type=Path,default=PUBLIC)
    p=sub.add_parser('import');p.add_argument('--stage-a',type=Path,required=True);p.add_argument('--stage-b',type=Path,required=True)
    p.add_argument('--confirmation',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--initial-stage-a',type=Path);p.add_argument('--proposed-stage-a',type=Path)
    p=sub.add_parser('analyze');p.add_argument('--registration',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.action=='prepare':result=prepare(args.output)
    elif args.action=='import':result=register(args.stage_a,args.stage_b,args.confirmation,args.output,args.initial_stage_a,args.proposed_stage_a)
    else:result=analyze_registration(args.registration,args.output)
    print(json.dumps({k:v for k,v in result.items() if k in ('records','cases','speakers','annotation_count','review_status','boundary_unresolved','responses','paired_cases','semantic_effects_computed','new_inference')}))
