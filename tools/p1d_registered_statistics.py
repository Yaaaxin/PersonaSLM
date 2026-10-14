"""Bound-policy analysis implementation; synthetic tests only until valid data exist."""
from collections import Counter, defaultdict
from math import sqrt
from statistics import NormalDist, mean, stdev
import random
from p1d_design import OUT, CELLS, read, sha
from p1d_analysis import case_contrast

POLICY_SHA = '08503570fdc4a8e6597f54efb217a1b432d1ce05d6e1fb2f833eed7e2687fc92'
CONTRAST_SHA = 'f2395c19e7c88b80ca0498335739a730e85cebba4afcdf15484995048e10e4ef'
LABELS = ('Correct', 'Incorrect', 'Unverifiable', 'Not Applicable', 'Missing')

def checked_registry():
    if sha(OUT / 'analysis_policy_proposal_v1.json') != POLICY_SHA:
        raise ValueError('Bound policy changed')
    if sha(OUT / 'contrast_specification_v1.json') != CONTRAST_SHA:
        raise ValueError('Bound weights changed')
    return read(OUT / 'contrast_specification_v1.json')['weights']

def categorical_summary(labels, eligible):
    if len(labels) != len(eligible) or not labels:
        raise ValueError('Nonempty labels and frozen eligibility must align')
    for x, e in zip(labels, eligible):
        if x not in LABELS or type(e) is not bool:
            raise ValueError('Invalid label/applicability')
        if (not e and x != 'Not Applicable') or (e and x == 'Not Applicable'):
            raise ValueError('Frozen applicability contradiction')
    counts = Counter(x for x, e in zip(labels, eligible) if e)
    n = sum(eligible); known = counts['Correct'] + counts['Incorrect']
    return {'eligible': n, 'inapplicable': len(labels)-n,
        'counts': {x: counts[x] for x in LABELS if x != 'Not Applicable'},
        'label_incidence': {x: counts[x]/n if n else None for x in LABELS if x != 'Not Applicable'},
        'assessed_only_accuracy': counts['Correct']/known if known else None,
        'assessed_only_denominator': known,
        'correct_outcome_identification_bounds': [counts['Correct']/n, (n-counts['Incorrect'])/n] if n else None,
        'interpretation': 'Label incidence, selected assessed-only accuracy, and unknown-outcome bounds are distinct estimands'}

def interval(values, family_size=1):
    if len(values) < 2:
        return None
    center = mean(values); se = stdev(values)/sqrt(len(values))
    z = NormalDist().inv_cdf(1-.05/(2*family_size))
    return {'center': center, 'se': se, 'lower': center-z*se, 'upper': center+z*se,
            'family_size': family_size, 'method': 'Normal cluster-SE approximation; no guaranteed population coverage'}

def paired_summary(rows, contrast, repeats=10000, seed=716201):
    """Each row contains one complete six-cell case, possibly explicit None values.

    Report unknown bounds on every case; complete-case summaries never substitute
    for the all-eligible estimand. Whole speaker draws retain all associated cases.
    """
    checked_registry()
    if not rows or repeats < 1:
        raise ValueError('Cases and positive bootstrap count required')
    keys = [(r['speaker_id'], r['case_id']) for r in rows]
    if len(keys) != len(set(keys)) or len({r['case_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate case or contradictory speaker mapping')
    cases = [{**{k: r[k] for k in ('speaker_id', 'case_id')}, **case_contrast(r['values'], contrast)} for r in rows]
    groups = defaultdict(list)
    for c in cases:
        groups[c['speaker_id']].append(c)
    speakers = {}
    for speaker, cs in sorted(groups.items()):
        complete = [c['complete_case_contrast'] for c in cs if c['complete_case_contrast'] is not None]
        speakers[speaker] = {'cases': len(cs), 'complete_cases': len(complete),
            'lower': mean(c['lower'] for c in cs), 'upper': mean(c['upper'] for c in cs),
            'complete_case_mean': mean(complete) if complete else None}
    values = [s['complete_case_mean'] for s in speakers.values() if s['complete_case_mean'] is not None]
    names = list(speakers); rng = random.Random(seed)
    boot, lower_boot, upper_boot = [], [], []
    for _ in range(repeats):
        draw = [speakers[rng.choice(names)] for _ in names]
        lower_boot.append(mean(s['lower'] for s in draw)); upper_boot.append(mean(s['upper'] for s in draw))
        v = [s['complete_case_mean'] for s in draw if s['complete_case_mean'] is not None]
        if v:
            boot.append(mean(v))
    def percentiles(xs):
        if not xs:
            return None
        xs = sorted(xs)
        return [xs[int(.025*(len(xs)-1))], xs[int(.975*(len(xs)-1))]]
    return {'contrast': contrast, 'case_contributions': cases, 'speakers': speakers,
        'eligible_cases': len(cases), 'eligible_speakers': len(speakers),
        'complete_cases': sum(c['complete_case_contrast'] is not None for c in cases),
        'all_eligible_identification_bounds': [mean(s['lower'] for s in speakers.values()), mean(s['upper'] for s in speakers.values())],
        'complete_case_equal_evaluable_speaker_mean': mean(values) if values else None,
        'selected_subset_cluster_interval': interval(values),
        'selected_subset_bonferroni_six_interval': interval(values, 6),
        'whole_speaker_bootstrap_selected_subset': percentiles(boot),
        'bootstrap_bound_endpoints': {'lower': percentiles(lower_boot), 'upper': percentiles(upper_boot)},
        'bootstrap_draws_without_evaluable_cases': repeats-len(boot), 'seed': seed, 'resamples': repeats,
        'leave_one_speaker_out': {name: {'bounds': [mean(s[k] for n,s in speakers.items() if n!=name) for k in ('lower','upper')],
            'selected_subset_mean': mean(v) if (v := [s['complete_case_mean'] for n,s in speakers.items() if n!=name and s['complete_case_mean'] is not None]) else None}
            for name in names} if len(names)>1 else {},
        'interpretation': 'Complete-case inference is selection-sensitive; bounds use all eligible cases with original signed weights. No cell renormalization.',
        'coverage_caveat': 'Few/dependent/purposive clusters and template reuse limit population interpretation. Boundary sensitivity remains a separate view.'}

def paired_model_rows(base, instruct):
    """Secondary model difference within the explicitly matched subset only."""
    b = {r['case_id']: r for r in base}
    if len(b) != len(base) or len({r['case_id'] for r in instruct}) != len(instruct):
        raise ValueError('Duplicate model case')
    result = []
    for i in instruct:
        if i['case_id'] not in b or b[i['case_id']]['speaker_id'] != i['speaker_id']:
            raise ValueError('Unmatched model case/speaker')
        row = b[i['case_id']]
        if set(i['values']) != set(CELLS) or set(row['values']) != set(CELLS):
            raise ValueError('Model comparison requires explicit six-cell coverage')
        result.append({'case_id': i['case_id'], 'speaker_id': i['speaker_id'],
            'base_values': row['values'], 'instruct_values': i['values'],
            'cell_differences': {c: None if row['values'][c] is None or i['values'][c] is None else i['values'][c]-row['values'][c] for c in CELLS}})
    return result

def model_contrast_bounds(row, contrast):
    b = case_contrast(row['base_values'], contrast); i = case_contrast(row['instruct_values'], contrast)
    return {'lower': i['lower']-b['upper'], 'upper': i['upper']-b['lower'],
            'complete_case_difference': None if b['complete_case_contrast'] is None or i['complete_case_contrast'] is None else i['complete_case_contrast']-b['complete_case_contrast'],
            'scope': 'Matched 24-speaker subset; no pure post-training causal interpretation'}
