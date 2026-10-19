"""Synthetic scorer/runtime tests; no model or participant records."""
import pytest
import real_persona_chat_continuation_v1 as study


@pytest.mark.parametrize('text,valid,success', [('A', True, 1), (' B\n', True, 0), ('A.', False, 0),
                         ('Ａ', False, 0), ('Answer: A', False, 0), ('AB', False, 0), ('', False, 0)])
def test_exact_choice_parser(text, valid, success):
    row = study.score(text, 'A')
    assert row['format_valid'] is valid and row['protocol_success'] == success
    assert (row['recognition_if_valid'] is not None) == valid


def test_authored_controls_are_two_counterbalanced_pairs():
    rows = study.controls()
    assert len(rows) == 4 and [r['correct_label'] for r in rows] == ['A', 'B', 'A', 'B']
    assert all(r['phase'] == 'CONTROL' and 'A: ' in r['messages'][1]['content'] for r in rows)


def test_payload_and_context_do_not_inherit_old_model_limits():
    result = study.payload({'input_token_ids': [1, 2, 3]})
    assert result['n_predict'] == 8 and result['temperature'] == 0 and not result['stop']
    config = study.config({'model': {'model_file': 'synthetic.gguf'}})
    assert config.n_ctx == 2048 and config.max_new_tokens == 8 and config.model_sha256 == study.MODEL_SHA
    assert study.GEN_BASE + study.N == 688


def test_influence_ranges_not_confidence_intervals():
    result = study.statistics_for([0, 0, 1, -1])
    assert result['mean'] == 0 and result['leave_one_pair_out_mean_range'] == [-1/3, 1/3]


def test_correct_and_mismatched_prompts_keep_candidates_and_local_context():
    case = {'candidate_texts': ['合成候補一', '合成候補二'], 'target_candidate_index': 0,
            'speaker_id': 'synthetic', 'history': [{'interlocutor_id': 'synthetic', 'text': '合成現在発話'}],
            'query': {'text': '合成質問'}, 'correct_external_history': '[以前の別の会話]\n合成正しい資料',
            'mismatched_external_history': '[以前の別の会話]\n合成異なる資料'}
    correct, label = study.messages(case, 'CORRECT', 0)
    mismatch, other = study.messages(case, 'MISMATCH', 0)
    assert label == other == 'A' and correct[0] == mismatch[0]
    assert correct[1]['content'].split('[現在の会話]')[1] == mismatch[1]['content'].split('[現在の会話]')[1]
    reversed_messages, reversed_label = study.messages(case, 'CORRECT', 1)
    assert reversed_label == 'B' and 'A: 合成候補二\nB: 合成候補一' in reversed_messages[1]['content']
