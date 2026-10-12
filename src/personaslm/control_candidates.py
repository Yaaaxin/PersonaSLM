"""Frozen-pool development controls; never used by the historical runner.

Candidate design v1 is a proposal, not an approved neutral intervention.
Candidate strings depend on speaker/date for formatting, never on city evidence.
"""
from itertools import combinations

VERSION = "neutral_control_candidate_v1_dev"
PROMPT_VERSION = "control_candidate_prompt_v1_dev"
STYLE_SENTENCES = (
    "A conversation includes contributions from its participants.",
    "Each contribution belongs to the ongoing exchange.",
    "A reply follows a contribution from another participant.",
    "The exchange contains contributions from both participants.",
    "Participants take part in the same conversation.",
    "The conversation has a participant on each side.",
    "A contribution forms part of a conversation.",
    "The participants are engaged in an exchange.",
)
HISTORY_REPLIES = (
    "I did not say.", "I did not name it.", "The city was not named.",
    "The city was not specified then.", "No city was stated then.",
    "I had not specified the city.", "The location was not mentioned.",
    "I had not named the city at that point.",
)
# These three invented people are new development inputs, not a pilot/test set.
DEVELOPMENT_CASES = (
    {"case_id": "control_dev_001", "speaker": "Riley", "current_city": "Leeds", "old_city": "York",
     "style": "The speaker favors brief replies with short sentences and avoids extended elaboration.", "date": "2025-03-14"},
    {"case_id": "control_dev_002", "speaker": "Samara", "current_city": "Bristol", "old_city": "Bath",
     "style": "The speaker favors formal wording and complete sentences in ordinary conversation.", "date": "2025-03-14"},
    {"case_id": "control_dev_003", "speaker": "Devon", "current_city": "Durham", "old_city": "Exeter",
     "style": "The speaker sometimes uses the word certainly when acknowledging a request.", "date": "2025-03-14"},
)


def candidates(case, condition):
    if condition == "N_style":
        # Fixed enumeration; no repeated sentence or search using model answers.
        return list(STYLE_SENTENCES) + [a + " " + b for a, b in combinations(STYLE_SENTENCES, 2)]
    if condition == "N_history":
        return [history(case, response) for response in HISTORY_REPLIES]
    raise ValueError("Only development neutral conditions supported")


def history(case, reply):
    return f"Historical dialogue ({case['date']}):\nUser: Where were you living back then?\n{case['speaker']}: {reply}"


def prompt(case, condition, neutral=None):
    if condition == "C1":
        addition = "Speaker context: " + case["style"]
    elif condition == "N_style" and neutral is not None:
        addition = "Speaker context: " + neutral
    elif condition == "C3":
        addition = history(case, f"In {case['old_city']} at the time.")
    elif condition == "N_history" and neutral is not None:
        addition = neutral
    else:
        raise ValueError("Invalid candidate prompt request")
    evidence = f"Verified current fact (2026-10-12): {case['speaker']} currently lives in {case['current_city']}."
    question = f"Where does {case['speaker']} currently live?"
    text = ("CONTINUE THE DIALOGUE. Use the verified facts for factual questions.\n\n"
            f"TRUSTED EVIDENCE:\n{evidence}\n\nADDITIONAL CONTEXT:\n{addition}\n\n"
            "RECENT CONVERSATION:\nUser: Please use the dated factual record when answering.\n\n"
            f"User: {question}\nAssistant:")
    return {"text": text, "trusted_evidence": evidence, "current_question": question, "conditioning_text": addition}


def select_match(attempts):
    if not attempts:
        raise ValueError("No candidate observations")
    best = min(attempts, key=lambda r: (abs(r["token_difference"]), r["candidate_index"]))
    return {"status": "PASS" if best["token_difference"] == 0 else "FAILED",
            "best_candidate_index": best["candidate_index"], "best_token_difference": best["token_difference"],
            "candidate_search_attempts": len(attempts), "tolerance": 0,
            "semantic_status": "UNREVIEWED", "generation_authorized_by_match": False}
