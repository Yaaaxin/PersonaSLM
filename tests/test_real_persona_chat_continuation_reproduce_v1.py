"""Independent-auditor synthetic arithmetic tests; no corpus or model access."""
import base64
import copy
import json

import pytest

import real_persona_chat_continuation_reproduce_v1 as audit


def allocation():
    cases, rows = [], []
    for index in range(8):
        cases.append({"case_id": str(index), "pair_index": index // 2,
                      "target_candidate_index": index % 2, "candidate_texts": ["合成候補甲です", "合成候補乙です"],
                      "history": [], "query": {"text": "無関係の発話"}, "source_history": [], "donor_source_history": []})
        for order in (0, 1):
            for arm in audit.ARMS:
                rows.append({"phase": "MAIN", "case_id": str(index), "option_order": order, "arm": arm,
                             **audit.selection("AB"[order], "AB"[order] if arm == "CORRECT" else "AB"[1-order])})
    return cases, rows


def test_independent_pairing_invariance_bounds_and_missingness():
    cases, rows = allocation()
    conditions, contrasts = audit.summaries(rows, cases)
    assert conditions["CORRECT"]["position_invariant"] == 8
    assert conditions["CORRECT"]["protocol_success_mean"] == 1
    assert contrasts["CORRECT-MISMATCH"]["values"] == [1, 1, 1, 1]
    assert contrasts["CORRECT-MISMATCH"]["allocated_16_order_case_bounds"] == [1, 1]
    rows[1]["protocol_success"] = None
    result = audit.summaries(rows, cases)[1]["CORRECT-MISMATCH"]
    assert result["n"] == 3 and result["missing_paired_order_cases"] == 1
    assert result["allocated_16_order_case_bounds"] == [14/16, 1]


def test_fullwidth_and_explanatory_answers_remain_format_failures():
    assert audit.selection(" A\n", "A")["protocol_success"] == 1
    for text in ("Ａ", "A.", "Answer: A", "", None):
        result = audit.selection(text, "A")
        assert result["protocol_success"] == 0 and result["recognition_if_valid"] is None
    assert audit.grams("Ａ Ｂ\nＣ") == {("a", "b", "c")}


def test_http_reconciliation_and_tamper_rejection():
    request = {"request_id": "synthetic", "input_token_ids": [1, 2]}
    body = {"content": "A"}
    events = [
        {"kind": "continuation_started", "data": request},
        {"kind": "http_request", "data": {"route": "/completion", "payload": audit.expected_payload(request)}},
        {"kind": "http_response", "data": {"route": "/completion", "status": 200,
          "body_base64": base64.b64encode(json.dumps(body).encode()).decode(), "elapsed_seconds": .9}},
        {"kind": "continuation_raw", "data": {"request_id": "synthetic", "response": body, "latency_seconds": 1.0}},
    ]
    receipt = {"attempts": 1, "responses": 1, "completion_inference_seconds": 1., "failed_seconds": 0.,
               "cumulative_generations": 637, "cumulative_inference_seconds": 3829.328792899886,
               "unattempted": 51, "retries": 0}
    assert audit.reconcile({"requests": [request]}, receipt, events)[1:] == (1., 0)
    damaged = copy.deepcopy(events)
    damaged[-1]["data"]["response"]["content"] = "B"
    with pytest.raises(AssertionError, match="HTTP bytes"):
        audit.reconcile({"requests": [request]}, receipt, damaged)


def test_lexical_ties_and_no_reference_leakage():
    case = allocation()[0][0]
    assert audit.lexical(case, "NONE") == .5
    case["query"]["text"] = case["candidate_texts"][0]
    assert audit.lexical(case, "NONE") == 1.
    case["reference"] = "ignored reference"
    assert audit.lexical(case, "NONE") == 1.
