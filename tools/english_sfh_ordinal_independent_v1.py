"""Pure exact arithmetic for the frozen five-speaker alternate ordinal analysis.

No file, mapping, corpus, model or human-review IO. Completion scenarios describe
logical sensitivity only; they are not observations or imputed human ratings.
"""
from collections import Counter, defaultdict
from fractions import Fraction
import math


DOMAINS = ('relevance', 'coherence', 'linguistic_resemblance')
CONDITIONS = tuple(f'C{i}' for i in range(8)) + ('M_STYLE', 'N_STYLE')
MASKS = {'S': 1, 'F': 2, 'H': 4, 'SF': 3, 'SH': 5, 'FH': 6, 'SFH': 7}
CONTROLS = {'correct_minus_mismatched': 'M_STYLE',
            'correct_minus_pooled': 'N_STYLE',
            'correct_minus_no_style_at_FH': 'C6'}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def ordinal_relation(left, right):
    """Ordered comparison only; invariant to a common strictly increasing relabeling."""
    return 'win' if left > right else 'loss' if left < right else 'tie'


def _validate(rows):
    _require(isinstance(rows, list) and len(rows) == 100, 'Exactly100 allocated rows required')
    grid = defaultdict(lambda: defaultdict(dict))
    missing = 0
    for row in rows:
        _require(isinstance(row, dict) and set(row) == {
            'speaker_id', 'case_id', 'condition', 'ratings', 'latency_seconds'}, 'Exact arithmetic row fields required')
        _require(all(isinstance(row[k], str) and row[k].strip() for k in ('speaker_id', 'case_id')),
                 'Nonempty opaque speaker/context identifiers required')
        _require(row['condition'] in CONDITIONS, 'Unknown condition')
        ratings = row['ratings']
        _require(isinstance(ratings, dict) and set(ratings) == set(DOMAINS), 'Exactly three primary domains required')
        values = list(ratings.values())
        unavailable = all(value is None for value in values)
        _require(unavailable or all(type(value) is int and 0 <= value <= 5 for value in values),
                 'Whole unavailable row or three strict0..5 integers required; structural NA is not a score')
        missing += unavailable
        latency = row['latency_seconds']
        _require(type(latency) in (int, float) and math.isfinite(latency) and latency >= 0,
                 'Finite nonnegative observed latency required')
        case = grid[row['speaker_id']][row['case_id']]
        _require(row['condition'] not in case, 'Duplicate speaker/context/condition cell')
        case[row['condition']] = row
    _require(missing <= 1, 'At most one wholly unavailable review is in this fixed analysis')
    _require(len(grid) == 5 and all(len(cases) == 2 for cases in grid.values()),
             'Exactly five speakers and two contexts each required')
    _require(all(set(case) == set(CONDITIONS) for cases in grid.values() for case in cases.values()),
             'Every context requires all ten conditions')
    return {speaker: {case: grid[speaker][case] for case in sorted(grid[speaker])}
            for speaker in sorted(grid)}, ([0, 1, 2, 3, 4, 5] if missing else [None])


def _rating(row, domain, completion):
    score = row['ratings'][domain]
    return completion if score is None else score


def _average(values):
    return sum(values, Fraction()) / len(values)


def _summary(groups, domain, evaluate, scenarios):
    """Equal fixed units within each speaker, then equal speakers, using rationals."""
    available = lambda unit: all(row['ratings'][domain] is not None for row in unit)
    speaker_values = []
    for units in groups.values():
        if all(available(unit) for unit in units):
            speaker_values.append(_average([Fraction(evaluate(unit, None)) for unit in units]))
    speaker_values.sort()
    completions = []
    for completion in scenarios:
        completions.append(_average([
            _average([Fraction(evaluate(unit, completion)) for unit in units])
            for units in groups.values()]))
    loo = [(sum(speaker_values, Fraction()) - omitted) / (len(speaker_values) - 1)
           for omitted in speaker_values] if len(speaker_values) > 1 else []
    return {
        'allocated_units': sum(len(units) for units in groups.values()),
        'observed_units': sum(available(unit) for units in groups.values() for unit in units),
        'complete_speakers': len(speaker_values),
        'speaker_values_sorted': [float(value) for value in speaker_values],
        'positive': sum(value > 0 for value in speaker_values),
        'zero': sum(value == 0 for value in speaker_values),
        'negative': sum(value < 0 for value in speaker_values),
        'mean_complete_speakers': float(_average(speaker_values)) if speaker_values else None,
        'leave_one_speaker_out_mean_range': [float(min(loo)), float(max(loo))] if loo else None,
        'full_design_bounds': [float(min(completions)), float(max(completions))],
        'full_design_completion_values': [float(value) for value in completions],
    }


def _sign(index, mask):
    sign = 1
    for bit in (1, 2, 4):
        if mask & bit and not index & bit:
            sign = -sign
    return sign


def _thresholds(groups, domain, sign, scenarios):
    return {str(cut): _summary(groups, domain,
        lambda unit, completion, cut=cut: 2 * sign(unit[0]) *
            int(_rating(unit[0], domain, completion) >= cut), scenarios)
        for cut in range(1, 6)}


def _paired(groups, domain, scenarios):
    def relation(unit, completion):
        return ordinal_relation(_rating(unit[0], domain, completion),
                                _rating(unit[1], domain, completion))

    result = {label: _summary(groups, domain,
        lambda unit, completion, label=label: int(relation(unit, completion) == label), scenarios)
        for label in ('win', 'tie', 'loss')}
    result['net'] = _summary(groups, domain,
        lambda unit, completion: int(relation(unit, completion) == 'win') -
                                 int(relation(unit, completion) == 'loss'), scenarios)
    result['quality_latency'] = {}
    for quality in ('win', 'tie', 'loss'):
        for speed in ('faster', 'equal', 'slower'):
            def joint(unit, completion, quality=quality, speed=speed):
                left, right = (row['latency_seconds'] for row in unit)
                observed_speed = 'faster' if left < right else 'slower' if left > right else 'equal'
                return int(relation(unit, completion) == quality and observed_speed == speed)
            result['quality_latency'][quality + '_' + speed] = _summary(groups, domain, joint, scenarios)
    return result


def _distribution(rows, domain):
    values = sorted(row['ratings'][domain] for row in rows if row['ratings'][domain] is not None)
    counts = Counter(values)
    central = None if not values else ([values[len(values) // 2]] if len(values) % 2 else
                                      values[len(values) // 2 - 1:len(values) // 2 + 1])
    return {'counts': [counts[category] for category in range(6)], 'observed': len(values),
            'missing': len(rows) - len(values), 'central_categories': central}


def compute(rows):
    """Return ordinal distribution/pair profiles; never average ordinal categories.

    Complete-speaker means describe a changed subset if a speaker is incomplete.
    Full-design bounds instead retain all five speakers. Scenario array indices
    match completion_category_scenarios throughout each outcome domain, preserving
    nested category cuts and correlated missingness effects. LOO ranges are not CIs.
    """
    grid, scenarios = _validate(rows)
    factorial = {speaker: [(case[f'C{index}'],) for case in cases.values() for index in range(8)]
                 for speaker, cases in grid.items()}
    paired = {factor: {speaker: [(case[f'C{index | bit}'], case[f'C{index}'])
                  for case in cases.values() for index in range(8) if not index & bit]
                  for speaker, cases in grid.items()} for factor, bit in (('S', 1), ('F', 2), ('H', 4))}
    control_pairs = {name: {speaker: [(case['C7'], case[comparator]) for case in cases.values()]
                           for speaker, cases in grid.items()} for name, comparator in CONTROLS.items()}
    result = {'schema': 'english_sfh_ordinal_arithmetic_v1', 'speakers': 5, 'contexts': 10,
              'responses': 100, 'domains': {}}
    for domain in DOMAINS:
        report = {'completion_category_scenarios': list(scenarios),
            'condition_distributions': {condition: _distribution(
                [case[condition] for cases in grid.values() for case in cases.values()], domain)
                for condition in CONDITIONS},
            'threshold_factorial': {name: _thresholds(factorial, domain,
                lambda row, mask=mask: _sign(int(row['condition'][1:]), mask), scenarios)
                for name, mask in MASKS.items()},
            'paired_main': {factor: _paired(groups, domain, scenarios) for factor, groups in paired.items()},
            'style_controls': {}}
        for name, groups in control_pairs.items():
            threshold_units = {speaker: [(row,) for pair in pairs for row in pair]
                               for speaker, pairs in groups.items()}
            report['style_controls'][name] = {
                'thresholds': _thresholds(threshold_units, domain,
                    lambda row: 1 if row['condition'] == 'C7' else -1, scenarios),
                'paired': _paired(groups, domain, scenarios)}
        result['domains'][domain] = report
    return result
