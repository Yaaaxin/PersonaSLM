"""Synthetic-only checks for the bounded posthoc decomposition."""
import real_persona_chat_continuation_position_diagnostic_v1 as diagnostic


def test_fixed_letter_and_invalid_format_decomposition():
    requests, raw = [], {}
    for order in (0, 1):
        for arm in diagnostic.ARMS:
            rid = str(len(requests))
            requests.append({"request_id": rid, "phase": "MAIN", "arm": arm, "case_id": "synthetic",
                             "option_order": order, "correct_label": "AB"[order]})
            content = "A explanation" if order == 0 and arm == "MISMATCH" else "A"
            raw[rid] = {"response": {"content": content, "tokens_evaluated": 5,
                                     "tokens_predicted": 1, "stop_type": "eos"}, "latency_seconds": .5}
    result = diagnostic.summarize(requests, raw)
    contrast = result["paired_order_contrast_decomposition"]["CORRECT-MISMATCH"]
    assert contrast["BOTH_VALID"]["count"] == 1
    assert contrast["BOTH_VALID"]["sum_protocol_score_difference"] == 0
    assert contrast["AT_LEAST_ONE_FORMAT_FAILURE"]["sum_protocol_score_difference"] == 1
    assert result["fixed_A_or_first_option_decomposition"]["MISMATCH"]["A_target_losses_to_invalid_format"] == 1
    assert result["observed_costs_by_phase_and_arm"]["MAIN"]["completion_wall_seconds"] == 3
    assert result["observed_costs_by_phase_and_arm"]["MAIN"]["input_tokens"] == 30
