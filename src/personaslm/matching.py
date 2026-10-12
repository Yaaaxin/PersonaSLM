"""Bounded neutral matching via the actual server tokenizer on full prompts."""
from dataclasses import dataclass
import itertools
import re

from .conditioning import Prompt, build_prompt
from .inference import validate_token_ids

MATCHER_VERSION = "neutral_sentences_v3_multiset_style"
NEUTRAL_SENTENCES = (
    "The page is plain.", "This is a text record.", "The layout has a heading.",
    "The document contains paragraphs.", "A line separates the sections.",
    "The margin is blank.", "The heading is printed above the text.", "The format is simple.",
)


@dataclass(frozen=True)
class MatchedPrompt:
    prompt: Prompt
    token_ids: list[int]
    audit: dict


class TokenMatchError(ValueError):
    def __init__(self, audit):
        self.audit = audit
        super().__init__(f"No neutral candidate meets token tolerance: {audit}")


def neutral_candidates(case, condition):
    # Preserve target block heading, date, speaker labels and line count.
    if condition == "N_style":
        yield case.neutral_style
        # Cover all supported lengths inside a bounded budget instead of exhausting
        # the short Cartesian products first. Acceptance tolerance is unchanged.
        # Reordering the same filler sentences consumes the budget without
        # broadening length coverage. Enumerate multisets before permutations;
        # still measure every complete candidate with the real tokenizer.
        pools = [itertools.combinations_with_replacement(NEUTRAL_SENTENCES, count) for count in range(1, 5)]
        for group in itertools.zip_longest(*pools):
            for parts in group:
                if parts is not None:
                    yield " ".join(parts)
    elif condition == "N_history":
        lines = case.history_dialogue.splitlines()
        if len(lines) != 3 or not lines[1].startswith("User: ") or not lines[2].startswith("Alice: "):
            raise ValueError("P0 neutral history requires the three-line synthetic history format")
        for count in range(2, 6):
            for parts in itertools.product(NEUTRAL_SENTENCES, repeat=count):
                yield f"{lines[0]}\nUser: {parts[0]}\nAlice: {' '.join(parts[1:])}"
    else:
        raise ValueError("Neutral matching requires N_style or N_history")


def match_neutral(case, condition, tokenizer, *, tolerance=0, max_candidates=256) -> MatchedPrompt:
    if type(tolerance) is not int or tolerance < 0 or type(max_candidates) is not int or max_candidates < 1:
        raise ValueError("Invalid matching tolerance or candidate limit")
    reference_condition = {"N_style": "C1", "N_history": "C3"}[condition]
    target = build_prompt(case, reference_condition)
    target_ids = validate_token_ids(tokenizer(target.text), allow_empty=False)
    best_delta = None
    attempted = 0
    candidate_search = []
    audit = {"matcher_version": MATCHER_VERSION, "reference_condition": reference_condition,
             "target_prompt": target.text, "target_token_ids": target_ids, "target_tokens": len(target_ids),
             "tolerance": tolerance, "format_policy": "same block heading, line count and speaker labels",
             "semantic_review": "P0 synthetic filler; human review required before confirmatory use"}
    for candidate in itertools.islice(neutral_candidates(case, condition), max_candidates):
        attempted += 1
        # Never introduce a known city answer into the additional neutral block.
        if any(re.search(r"\b" + re.escape(f.value) + r"\b", candidate, re.IGNORECASE) for f in case.facts):
            candidate_search.append({"attempt": attempted, "text": candidate, "rejected": "known_city"})
            continue
        prompt = build_prompt(case, condition, neutral_override=candidate)
        signature = lambda block: [line.split(":", 1)[0] for line in block.splitlines()]
        if signature(prompt.additions[0]) != signature(target.additions[0]):
            candidate_search.append({"attempt": attempted, "text": candidate, "rejected": "format"})
            continue
        if prompt.evidence_block != target.evidence_block or prompt.text.count(target.evidence_block) != 1:
            raise AssertionError("Neutral matching changed trusted evidence")
        ids = validate_token_ids(tokenizer(prompt.text), allow_empty=False)
        delta = len(ids) - len(target_ids)
        candidate_search.append({"attempt": attempted, "text": candidate, "tokens": len(ids), "delta": delta})
        if best_delta is None or abs(delta) < abs(best_delta):
            best_delta = delta
        if abs(delta) <= tolerance:
            return MatchedPrompt(prompt, ids, {**audit, "status": "PASS", "attempted": attempted,
                                 "actual_tokens": len(ids), "delta": delta, "neutral_text": candidate,
                                 "candidate_search": candidate_search})
    raise TokenMatchError({**audit, "status": "BLOCKED", "attempted": attempted, "best_delta": best_delta,
                          "candidate_search": candidate_search})
