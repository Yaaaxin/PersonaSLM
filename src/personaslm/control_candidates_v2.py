"""Development-only fixed candidate pools; never registered as P1 treatments.

Selection uses complete-prompt token length only, never model responses.
The historical prompt factory and earlier candidate versions are unchanged.
"""
from dataclasses import asdict

from .conditioning import build_prompt
from .control_candidates import DEVELOPMENT_CASES as EARLIER_CASES
from .schemas import Case, ENDPOINTS

VERSION = "neutral_control_candidate_v2_dev"
PROMPT_VERSION = "transcript_base_v1"
FAMILIES = ("style_generic", "history_format", "history_topic", "history_stale_generalized")

# Complete single sentences, not repeated padding or instructions to the speaker.
# This generic discourse content still requires human semantic review.
STYLE_POOL = (
    "A conversation includes contributions from its participants.",
    "A conversation includes questions and replies from its participants.",
    "A conversation consists of contributions from the people taking part.",
    "A conversation consists of questions and replies from the people taking part.",
    "A conversation includes an exchange of questions and replies between participants.",
    "A conversation includes an exchange of questions and replies between the people taking part.",
    "A conversation consists of a question from one participant and a reply from another.",
    "A conversation consists of a question from one participant and a response from the other.",
    "A conversation involves participants who exchange questions and replies with one another.",
    "A conversation involves participants who contribute questions and responses to an exchange.",
    "The participants in a conversation contribute questions and replies to the exchange.",
    "The participants in a conversation contribute questions and replies to an exchange with one another.",
    "The participants in a conversation contribute questions and responses as part of the exchange.",
    "The participants in a conversation take part in an exchange of questions and replies.",
    "The participants in a conversation take part in an exchange that includes questions and replies.",
    "An exchange between participants includes questions and responses.",
    "An exchange between participants includes a question and a response.",
    "An exchange between participants includes a question from one person and a response from another.",
    "An exchange between participants consists of contributions from the people taking part in the conversation.",
    "An exchange between participants consists of questions and replies contributed by the people taking part.",
    "A participant asks a question and another participant gives a reply.",
    "A participant asks a question and another participant contributes a response to the conversation.",
    "A participant contributes a question to a conversation and another participant contributes a reply.",
    "A question from a participant forms part of an exchange with another participant.",
    "A question from one participant and a reply from another form part of a conversation.",
    "Questions and replies form part of a conversation between participants.",
    "Questions and replies from the participants form part of an exchange between them.",
    "Questions and replies from the participants form part of the exchange that constitutes a conversation.",
    "The exchange includes contributions from the participants in the conversation.",
    "The exchange includes a question from a participant in the conversation and a reply from another.",
    "The conversation has participants who exchange questions and responses with each other.",
    "The conversation has participants who contribute to an exchange of questions and replies with each other.",
)

# Each pair is an authored, coherent question/answer adjacency pair. These
# concern discourse, not residence: topic is deliberately NOT matched in A.
FORMAT_POOL = (
    ("What does a conversation involve?", "Questions and replies."),
    ("What does a conversation involve?", "An exchange of questions and replies."),
    ("What does a conversation involve?", "Questions and replies between participants."),
    ("What does a conversation involve?", "An exchange between the people taking part."),
    ("What does an exchange involve?", "Questions and replies between participants."),
    ("What does an exchange involve?", "A question and a response."),
    ("What does an exchange involve?", "A question from one participant and a reply."),
    ("What does an exchange involve?", "Contributions from the people taking part."),
    ("What can a conversation include?", "A question and a reply."),
    ("What can a conversation include?", "A question from one participant and a response."),
    ("What can a conversation include?", "Questions and responses from its participants."),
    ("What can a conversation include?", "An exchange of questions and replies between participants."),
    ("What follows a question in this exchange?", "A reply from another participant."),
    ("What follows a question in this exchange?", "A response from the other participant."),
    ("What is part of a conversation?", "An exchange of questions and replies."),
    ("What is part of a conversation?", "Questions and responses from the participants."),
)

# B retains the residence question but replies with clarification, not a
# claim about undisclosed knowledge. Clarification priming remains a confound.
TOPIC_REPLIES = (
    "Which place?", "Which city?", "The city?", "The city or the address?",
    "Do you mean the city?", "Are you asking which city?",
    "Do you mean which city?", "Are you asking about the city?",
    "Are you asking about my city?", "Do you mean the city or the address?",
    "Are you asking for the city or the address?",
    "Do you mean the name of the city?",
)

# C is an information-ablation DIAGNOSTIC, not a neutral placebo. It retains
# city residence but removes its name, changing specificity and pragmatics.
GENERALIZED_REPLIES = (
    "In a city.", "In a city then.", "In a city back then.",
    "In a city at the time.", "In a city at that time.",
    "I lived in a city.", "I lived in a city then.",
    "I was living in a city.", "I was living in a city then.",
    "I lived in a city at the time.",
)

CASE_SPECS = tuple({**c, "case_id": f"control_v2_dev_{i:03d}",
                    "origin": "Earlier v1 development case; wrapper restored"}
                   for i, c in enumerate(EARLIER_CASES, 1)) + (
    {"case_id": "control_v2_dev_004", "speaker": "Tessa", "current_city": "Norwich", "old_city": "Hull",
     "style": "The speaker uses contractions in conversational replies.", "date": "2025-06-18", "origin": "New development case"},
    {"case_id": "control_v2_dev_005", "speaker": "Blair", "current_city": "Lancaster", "old_city": "Carlisle",
     "style": "The speaker tends to acknowledge a question before giving an answer.", "date": "2025-08-21", "origin": "New development case"},
    {"case_id": "control_v2_dev_006", "speaker": "Robin", "current_city": "Plymouth", "old_city": "Gloucester",
     "style": "The speaker favors a single sentence when responding to a straightforward question.", "date": "2025-11-09", "origin": "New development case"},
)


def history(spec, question, reply):
    return f"Historical dialogue ({spec['date']}):\nUser: {question}\n{spec['speaker']}: {reply}"


def case_record(spec):
    speaker = spec["speaker"]
    record = asdict(Case.from_dict({
        "case_id": spec["case_id"], "persona_id": speaker.lower(), "evaluation_date": "2026-10-12",
        "task_type": "current_city", "context": ["User: Please use the dated factual record when answering."],
        "question": f"Where does {speaker} currently live?",
        "trusted_evidence": f"Verified current fact (2026-10-12): {speaker} currently lives in {spec['current_city']}.",
        "expected_answer": spec["current_city"], "facts": [
            {"fact_id": "old_residence", "attribute": "current_city", "value": spec["old_city"],
             "valid_from": "2024-01-01", "valid_until": "2026-09-30"},
            {"fact_id": "current_residence", "attribute": "current_city", "value": spec["current_city"],
             "valid_from": "2026-10-01", "valid_until": None}],
        "style_only": spec["style"], "supplemental_fact": "Not manipulated in this development-only diagnostic.",
        "history_dialogue": history(spec, "Where were you living back then?", f"In {spec['old_city']} at the time."),
        "neutral_style": "Development override required.", "neutral_history": "Development override required.",
        "applicability": {k: k in {"response_relevance", "factual_consistency", "temporal_consistency", "conversational_coherence"}
                          for k in ENDPOINTS}, "split": "development_only"}))
    record["context"] = list(record["context"])
    record["facts"] = list(record["facts"])
    return record


def candidate_texts(spec, family):
    if family == "style_generic":
        return list(STYLE_POOL)
    if family == "history_format":
        return [history(spec, q, r) for q, r in FORMAT_POOL]
    if family == "history_topic":
        return [history(spec, "Where were you living back then?", r) for r in TOPIC_REPLIES]
    if family == "history_stale_generalized":
        return [history(spec, "Where were you living back then?", r) for r in GENERALIZED_REPLIES]
    raise ValueError("Unknown development control family")


def pair(spec, family):
    if family not in FAMILIES:
        raise ValueError("Unknown development control family")
    record = case_record(spec)
    record["context"] = list(record["context"])
    case = Case.from_dict(record)
    reference, neutral = ("C1", "N_style") if family == "style_generic" else ("C3", "N_history")
    return {"case_id": case.case_id, "family": family, "reference_condition": reference,
            "render_condition": neutral, "reference_prompt": asdict(build_prompt(case, reference)),
            "trusted_evidence": case.trusted_evidence, "current_question": case.question,
            "candidates": [{"candidate_index": i, "conditioning_text": text,
                            "prompt": asdict(build_prompt(case, neutral, neutral_override=text))}
                           for i, text in enumerate(candidate_texts(spec, family))]}
