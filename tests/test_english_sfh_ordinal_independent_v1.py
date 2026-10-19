"""Authored ordinal fixtures only; no private input, condition map or model IO."""
import copy
import json

import pytest

import english_sfh_ordinal_independent_v1 as ordinal


def authored_rows():
    rows = []
    for speaker in range(5):
        for context in range(2):
            for condition in ordinal.CONDITIONS:
                index = int(condition[1:]) if condition.startswith('C') else 7
                style, facts = bool(index & 1), bool(index & 2)
                relevance = 5 if style else 0
                latency = 2.0 if style else 1.0
                if condition == 'M_STYLE':
                    relevance, latency = 4, 2.5
                rows.append({'speaker_id': f'authored_speaker_{speaker}',
                    'case_id': f'authored_context_{speaker}_{context}', 'condition': condition,
                    'ratings': {'relevance': relevance, 'coherence': 3,
                                'linguistic_resemblance': 4 if style == facts else 1},
                    'latency_seconds': latency})
    return rows


@pytest.fixture(scope='module')
def complete_result():
    return ordinal.compute(authored_rows())


def test_full_grid_all_ordered_cuts_and_interaction_scaling(complete_result):
    relevance = complete_result['domains']['relevance']
    for cut in map(str, range(1, 6)):
        effect = relevance['threshold_factorial']['S'][cut]
        assert effect['mean_complete_speakers'] == 1.0
        assert effect['full_design_bounds'] == [1.0, 1.0]
        assert effect['allocated_units'] == effect['observed_units'] == 80
        assert effect['speaker_values_sorted'] == [1.0] * 5
        for contrast in ('F', 'H', 'SF', 'SH', 'FH', 'SFH'):
            assert relevance['threshold_factorial'][contrast][cut]['full_design_bounds'] == [0.0, 0.0]
    resemblance = complete_result['domains']['linguistic_resemblance']
    # Balanced binary SF parity has factorial-scaled interaction1, not unscaled DID2.
    assert [resemblance['threshold_factorial']['SF'][str(k)]['mean_complete_speakers']
            for k in range(1, 6)] == [0.0, 1.0, 1.0, 1.0, 0.0]
    assert relevance['completion_category_scenarios'] == [None]
    assert 'authored_speaker' not in json.dumps(complete_result)


def test_zero_is_observed_median_keeps_categories_and_controls_use_c6(complete_result):
    relevance = complete_result['domains']['relevance']
    assert relevance['condition_distributions']['C0'] == {
        'counts': [10, 0, 0, 0, 0, 0], 'observed': 10, 'missing': 0, 'central_categories': [0, 0]}
    controls = relevance['style_controls']
    assert controls['correct_minus_mismatched']['paired']['win']['mean_complete_speakers'] == 1.0
    assert controls['correct_minus_pooled']['paired']['tie']['mean_complete_speakers'] == 1.0
    assert controls['correct_minus_no_style_at_FH']['paired']['win']['mean_complete_speakers'] == 1.0
    assert controls['correct_minus_no_style_at_FH']['thresholds']['1']['allocated_units'] == 20
    assert ordinal._distribution([{'ratings': {'relevance': x}} for x in (0, 2, 4, 5)], 'relevance')['central_categories'] == [2, 4]


def test_paired_main_and_nominal_quality_latency_are_not_independent_people(complete_result):
    paired = complete_result['domains']['relevance']['paired_main']['S']
    assert paired['win']['allocated_units'] == paired['win']['observed_units'] == 40
    assert paired['win']['complete_speakers'] == 5
    assert paired['net']['mean_complete_speakers'] == 1.0
    assert paired['quality_latency']['win_slower']['mean_complete_speakers'] == 1.0
    assert sum(cell['mean_complete_speakers'] for cell in paired['quality_latency'].values()) == 1.0
    assert paired['net']['leave_one_speaker_out_mean_range'] == [1.0, 1.0]
    assert paired['net']['positive'] == 5 and paired['net']['zero'] == paired['net']['negative'] == 0


def test_missing_factorial_category_exact_bounds_and_joint_scenarios_not_imputation():
    rows = authored_rows()
    rows[0]['ratings'] = dict.fromkeys(ordinal.DOMAINS)
    before = copy.deepcopy(rows)
    result = ordinal.compute(rows)['domains']['relevance']
    assert rows == before
    assert result['completion_category_scenarios'] == list(range(6))
    effect = result['threshold_factorial']['S']['3']
    assert effect['observed_units'] == 79 and effect['complete_speakers'] == 4
    assert effect['mean_complete_speakers'] == 1.0
    assert effect['full_design_bounds'] == [0.975, 1.0]
    assert effect['full_design_completion_values'] == [1.0, 1.0, 1.0, 0.975, 0.975, 0.975]
    paired = result['paired_main']['S']
    assert paired['win']['observed_units'] == 39 and paired['win']['complete_speakers'] == 4
    assert paired['net']['full_design_bounds'] == [0.975, 1.0]
    assert result['condition_distributions']['C0']['missing'] == 1
    assert result['style_controls']['correct_minus_mismatched']['paired']['net']['complete_speakers'] == 5


def test_missing_diagnostic_retains_full_factorial_and_control_width():
    rows = authored_rows()
    next(row for row in rows if row['condition'] == 'M_STYLE')['ratings'] = dict.fromkeys(ordinal.DOMAINS)
    result = ordinal.compute(rows)['domains']['relevance']
    assert result['threshold_factorial']['S']['5']['complete_speakers'] == 5
    control = result['style_controls']['correct_minus_mismatched']
    assert control['thresholds']['5']['full_design_bounds'] == [0.9, 1.0]
    assert control['thresholds']['5']['observed_units'] == 19
    assert control['paired']['win']['observed_units'] == 9
    assert control['paired']['win']['full_design_bounds'] == [0.9, 1.0]


def test_interior_comparator_gives_two_sided_net_missing_bounds():
    rows = authored_rows()
    rows[0]['ratings'] = dict.fromkeys(ordinal.DOMAINS)
    rows[1]['ratings']['relevance'] = 2
    result = ordinal.compute(rows)['domains']['relevance']['paired_main']['S']['net']
    assert result['mean_complete_speakers'] == 1.0
    assert result['full_design_bounds'] == [0.95, 1.0]
    assert result['full_design_completion_values'] == [1.0, 1.0, 0.975, 0.95, 0.95, 0.95]


def test_heterogeneous_speakers_equal_weight_and_loo_is_influence():
    rows = authored_rows()
    for row in rows:
        if row['speaker_id'] == 'authored_speaker_0':
            row['ratings']['relevance'] = 0
    result = ordinal.compute(rows)['domains']['relevance']['threshold_factorial']['S']['3']
    assert result['speaker_values_sorted'] == [0.0, 1.0, 1.0, 1.0, 1.0]
    assert result['mean_complete_speakers'] == 0.8
    assert result['leave_one_speaker_out_mean_range'] == [0.75, 1.0]
    assert result['full_design_bounds'] == [0.8, 0.8]


def test_all_seven_original_factor_code_signs():
    expected = {'S': [-1, 1, -1, 1, -1, 1, -1, 1],
                'F': [-1, -1, 1, 1, -1, -1, 1, 1],
                'H': [-1, -1, -1, -1, 1, 1, 1, 1],
                'SF': [1, -1, -1, 1, 1, -1, -1, 1],
                'SH': [1, -1, 1, -1, -1, 1, -1, 1],
                'FH': [1, 1, -1, -1, -1, -1, 1, 1],
                'SFH': [-1, 1, 1, -1, 1, -1, -1, 1]}
    for name, signs in expected.items():
        assert [ordinal._sign(index, ordinal.MASKS[name]) for index in range(8)] == signs


def test_strictly_increasing_nonlinear_category_relabeling_preserves_order_and_cuts():
    relabel = [-100, -20, -1, 7, 8, 1000]
    for left in range(6):
        for right in range(6):
            assert ordinal.ordinal_relation(left, right) == ordinal.ordinal_relation(relabel[left], relabel[right])
        for cut in range(1, 6):
            assert (left >= cut) == (relabel[left] >= relabel[cut])


def test_input_order_does_not_change_equal_speaker_pairing(complete_result):
    assert ordinal.compute(list(reversed(authored_rows()))) == complete_result


@pytest.mark.parametrize('problem', ['duplicate', 'partial', 'bool', 'outside', 'two_missing', 'nan', 'extra'])
def test_fixed_design_and_numeric_boundaries_fail_closed(problem):
    rows = authored_rows()
    if problem == 'duplicate':
        rows[-1] = copy.deepcopy(rows[0])
    elif problem == 'partial':
        rows[0]['ratings']['relevance'] = None
    elif problem == 'bool':
        rows[0]['ratings']['relevance'] = True
    elif problem == 'outside':
        rows[0]['ratings']['relevance'] = 6
    elif problem == 'two_missing':
        for row in rows[:2]:
            row['ratings'] = dict.fromkeys(ordinal.DOMAINS)
    elif problem == 'nan':
        rows[0]['latency_seconds'] = float('nan')
    else:
        rows[0]['raw_dialogue'] = 'authored forbidden extra field'
    with pytest.raises(ValueError):
        ordinal.compute(rows)
