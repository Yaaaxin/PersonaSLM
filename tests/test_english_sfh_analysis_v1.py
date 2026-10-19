import english_sfh_analysis_v1 as a


def test_literal_copy_is_not_a_fidelity_score():
    row = {'messages': [{'content': 'one two three four five six'}]}
    value = a.measure(row, {'content': 'one two three four five six', 'tokens_predicted': 6, 'stop_type': 'eos'}, 1.5)
    assert value['source_fivegram_coverage'] == 1
    assert value['native_eos'] == 1
    assert a.measure(row, {'content': 'one', 'tokens_predicted': 1, 'stop_type': 'limit'}, 1)['source_fivegram_coverage'] is None


def test_factorial_diagnostics_and_missingness():
    rows = []
    for speaker in ['p1', 'p2']:
        for case in ['a', 'b']:
            for condition in list(a.run.shared.CONDITIONS) + ['M_STYLE', 'N_STYLE']:
                value = 10 + (2 * a.run.shared.CONDITIONS[condition]['S'] if condition.startswith('C') else 0)
                rows.append({'speaker_id': speaker, 'case_id': case, 'condition': condition,
                             'measurements': dict.fromkeys(a.METRICS, value)})
    result = a.estimates(rows)
    assert result['factorial_effects']['output_tokens']['S']['mean'] == 2
    assert result['factorial_effects']['output_tokens']['SF']['mean'] == 0
    assert result['style_controls']['output_tokens']['correct_minus_mismatched']['mean'] == 2
    rows[0]['measurements']['output_tokens'] = None
    missing = a.estimates(rows)
    assert missing['factorial_effects']['output_tokens']['S']['n'] == 1
    assert missing['factorial_effects']['output_tokens']['S']['incomplete_speakers'] == 1
