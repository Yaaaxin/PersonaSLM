"""Additive researcher-confirmed annotation normalization and paired analysis."""
from collections import Counter, defaultdict
from copy import deepcopy
import math
import random
from statistics import mean

from .conditioning import FACTORIAL
from .measurement_audit import HUMAN_FIELDS, validate_annotations
from .response_status import text_hash

VERSION = 'p1_researcher_annotation_analysis_v1'
CONTRASTS = ('C1-C0', 'C3-C0', 'S', 'F', 'H', 'SxF', 'SxH', 'FxH', 'SxFxH')
METRICS = ('relevance', 'coherence', 'factual', 'temporal', 'semantic_complete',
           'COMPLETE', 'TRUNCATED', 'CROSS_TURN', 'AMBIGUOUS')


def inventory(rows, *, expected_count=96, cases=12):
    if len(rows) != expected_count:
        raise ValueError('Wrong annotation count')
    ids = [r['anonymous_response_id'] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate response ID')
    counts = Counter(r['anonymous_case_id'] for r in rows)
    if len(counts) != cases or set(counts.values()) != {8}:
        raise ValueError('Expected eight outputs per anonymous case')
    return {r['anonymous_response_id']: r for r in rows}


def material_differences(master, proposed):
    source, supplied = inventory(master), inventory(proposed)
    diffs = []
    if set(source) != set(supplied):
        raise ValueError('Response IDs differ from review master')
    for rid, row in supplied.items():
        ref = source[rid]
        if list(row) != list(ref):
            raise ValueError('Original 41-column schema/order changed')
        for field in ref:
            if field not in HUMAN_FIELDS and row[field] != ref[field]:
                diffs.append({'response_id': rid, 'field': field,
                              'master': ref[field], 'supplied': row[field]})
        if text_hash(ref['raw_full_continuation']) != ref['raw_sha256'] or text_hash(ref['raw_first_reply']) != ref['first_reply_sha256']:
            raise ValueError('Master raw-text hash mismatch')
    return diffs


def normalize_confirmed(master, proposed, provenance):
    """Apply only declared representation/provenance mappings, never infer scores."""
    differences = material_differences(master, proposed)
    if differences:
        raise ValueError('Frozen material mismatch: ' + repr(differences))
    ledger = inventory(provenance)
    if set(ledger) != {r['anonymous_response_id'] for r in proposed}:
        raise ValueError('Provenance ID mismatch')
    output, changes = [], []
    aliases = {'human_reply_unit_confirmed': {'true': 'YES', 'false': 'NO', 'uncertain': 'UNCERTAIN'},
               'human_semantic_completeness': {'complete': 'COMPLETE', 'incomplete': 'INCOMPLETE', 'uncertain': 'UNCERTAIN'}}
    categorical = {'correct': 'Correct', 'incorrect': 'Incorrect', 'unverifiable': 'Unverifiable'}
    paired_fields = {'proposed_reply_unit_confirmed': 'human_reply_unit_confirmed',
                     'proposed_semantic_completeness': 'human_semantic_completeness',
                     'proposed_factual_consistency': 'human_factual_consistency',
                     'proposed_temporal_consistency': 'human_temporal_consistency',
                     'proposed_response_relevance_1_to_5': 'human_response_relevance_1_to_5',
                     'proposed_conversational_coherence_1_to_5': 'human_conversational_coherence_1_to_5'}
    for row in proposed:
        rid = row['anonymous_response_id']; record = ledger[rid]
        if record['anonymous_case_id'] != row['anonymous_case_id'] or record['reviewer_original_note'] != row['reviewer_notes']:
            raise ValueError('Original researcher note/case differs from provenance')
        for old, new in paired_fields.items():
            if record[old] != row[new]:
                raise ValueError('Proposed score differs between source files: ' + rid + '/' + new)
        new = deepcopy(row)
        for key, values in aliases.items():
            if row[key] not in values:
                raise ValueError('Unknown source categorical value: ' + key)
            new[key] = values[row[key]]
        for axis, key in [('factual_consistency', 'human_factual_consistency'), ('temporal_consistency', 'human_temporal_consistency')]:
            if row['applicable_' + axis] == 'false':
                if row[key] not in ('', 'Not Applicable'):
                    raise ValueError('Rating present for inapplicable outcome')
                new[key] = 'Not Applicable'
            else:
                if row[key] not in categorical:
                    raise ValueError('Missing or unknown applicable judgment')
                new[key] = categorical[row[key]]
        if row['reviewer_id'] != 'Yaxin_ZHENG':
            raise ValueError('Unexpected researcher identity')
        new['review_assistance'] = 'AI-assisted'
        # Unknown access is an administrative disclosure, not a fabricated human answer.
        if row['prior_access_to_treatments_or_scores'] not in ('', 'YES', 'NO', 'UNCERTAIN'):
            raise ValueError('Unknown access disclosure')
        new['prior_access_to_treatments_or_scores'] = row['prior_access_to_treatments_or_scores'] or 'UNCERTAIN'
        for field in row:
            if row[field] != new[field]:
                changes.append({'response_id': rid, 'field': field, 'source': row[field], 'registered': new[field]})
        output.append(new)
    validation = validate_annotations(master, output)
    return output, changes, validation


def weights(contrast):
    if contrast in ('C1-C0', 'C3-C0'):
        return {contrast[:2]: 1.0, 'C0': -1.0}
    axes = contrast.split('x')
    if any(a not in 'SFH' or len(a) != 1 for a in axes) or len(set(axes)) != len(axes):
        raise ValueError('Unknown contrast')
    return {c: math.prod(1 if bits['SFH'.index(a)] else -1 for a in axes) / 2 ** (3 - len(axes))
            for c, bits in FACTORIAL.items()}


def metric_value(row, metric):
    h = row['annotation']
    if metric in ('factual', 'temporal'):
        axis = 'factual_consistency' if metric == 'factual' else 'temporal_consistency'
        eligible = h['applicable_' + axis] == 'true'
        label = h['human_' + axis]
        return eligible, (1.0 if label == 'Correct' else 0.0 if label == 'Incorrect' else None)
    if metric in ('relevance', 'coherence'):
        axis = 'response_relevance' if metric == 'relevance' else 'conversational_coherence'
        eligible = h['applicable_' + axis] == 'true'
        label = h['human_' + axis + '_1_to_5']
        return eligible, float(label) if label in ('1', '2', '3', '4', '5') else None
    if metric == 'semantic_complete':
        return True, {'COMPLETE': 1.0, 'INCOMPLETE': 0.0}.get(h['human_semantic_completeness'])
    if metric not in METRICS:
        raise ValueError('Unknown metric')
    return True, float(h['structural_status'] == metric)


def quantile(sorted_values, probability):
    index = (len(sorted_values) - 1) * probability
    low = int(index); high = math.ceil(index)
    return sorted_values[low] + (index - low) * (sorted_values[high] - sorted_values[low])


def uncertainty(points, seed, replicates):
    """Resample whole case units within family; no iid-response inference."""
    if not points:
        return {'range': None, 'bootstrap_percentile_95': None, 'leave_one_case_out_range': None}
    values = [p['difference'] for p in points]
    groups = defaultdict(list)
    for p in points:
        groups[p['family']].append(p['difference'])
    rng = random.Random(seed)
    simulated = sorted(mean(rng.choice(group) for group in groups.values() for _ in group)
                       for _ in range(replicates))
    loo = [mean(values[:i] + values[i+1:]) for i in range(len(values))] if len(values) > 1 else []
    interval = [quantile(simulated, .025), quantile(simulated, .975)]
    return {'range': [min(values), max(values)], 'bootstrap_percentile_95': interval,
            'leave_one_case_out_range': [min(loo), max(loo)] if loo else None,
            'bootstrap_degenerate': interval[0] == interval[1],
            'seed': seed, 'replicates': replicates,
            'scope': 'Exploratory empirical family-stratified case bootstrap; no annotation/model uncertainty or population equivalence guarantee. Degenerate intervals do not establish zero population uncertainty.'}


def analyze(rows, *, seed=713113, replicates=10000):
    by_case = defaultdict(dict)
    for row in rows:
        cid, cond = row['case_id'], row['condition']
        if cond not in FACTORIAL or cond in by_case[cid]:
            raise ValueError('Unknown or duplicate factorial cell')
        if tuple(row['factors']) != FACTORIAL[cond]:
            raise ValueError('Wrong factor assignment')
        by_case[cid][cond] = row
    if any(set(cells) != set(FACTORIAL) for cells in by_case.values()):
        raise ValueError('Missing factorial cell; preserve and diagnose before analysis')
    if len({next(iter(c.values()))['persona_id'] for c in by_case.values()}) != len(by_case):
        raise ValueError('This wave analysis requires one paired case per speaker')
    summaries, contrasts = {}, {}
    for metric in METRICS:
        per_condition = {}
        for cond in FACTORIAL:
            group = [cells[cond] for cells in by_case.values()]
            outcomes = [metric_value(r, metric) for r in group]
            eligible = sum(e for e, _ in outcomes)
            values = [v for e, v in outcomes if e and v is not None]
            per_condition[cond] = {'received': len(group), 'eligible': eligible, 'evaluated': len(values),
                                   'unscorable': eligible-len(values), 'not_applicable': len(group)-eligible,
                                   'mean': mean(values) if values else None,
                                   'distribution': dict(Counter(str(v) for v in values))}
        summaries[metric] = per_condition
        contrasts[metric] = {}
        for contrast in CONTRASTS:
            w = weights(contrast); points = []; eligible = 0; missing = []; inapplicable = []
            for cid, cells in sorted(by_case.items()):
                outcomes = {c: metric_value(r, metric) for c, r in cells.items()}
                if len({e for e, _ in outcomes.values()}) != 1:
                    raise ValueError('Within-case applicability mismatch')
                if not all(outcomes[c][0] for c in w):
                    inapplicable.append(cid); continue
                eligible += 1
                if any(outcomes[c][1] is None for c in w):
                    missing.append(cid); continue
                points.append({'case_id': cid, 'persona_id': cells['C0']['persona_id'],
                               'family': cells['C0']['family'], 'outcomes': {c: v for c, (_, v) in outcomes.items()},
                               'difference': sum(w[c] * outcomes[c][1] for c in w)})
            contrasts[metric][contrast] = {'weights': w, 'eligible_cases': eligible,
                'evaluable_cases': len(points), 'inapplicable_cases': inapplicable, 'unscorable_cases': missing,
                'case_level': points, 'estimate': mean(p['difference'] for p in points) if points else None,
                'nonzero_cases': [p['case_id'] for p in points if p['difference'] != 0],
                'uncertainty': uncertainty(points, seed, replicates)}
    return {'version': VERSION, 'conditions': summaries, 'contrasts': contrasts,
            'planned_cases': len(by_case), 'received_responses': len(rows), 'significance_test': False,
            'fidelity_scored': False, 'neutral_control_contrasts': False}
