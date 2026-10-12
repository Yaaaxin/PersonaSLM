"""Track A: verified task evidence must remain identical in all treatments."""
from dataclasses import dataclass
from .schemas import Case

FACTORIAL = {
    "C0": (0, 0, 0), "C1": (1, 0, 0), "C2": (0, 1, 0), "C3": (0, 0, 1),
    "C4": (1, 1, 0), "C5": (1, 0, 1), "C6": (0, 1, 1), "C7": (1, 1, 1),
}
P0_CONDITIONS = ("C0", "C1", "N_style", "C3", "N_history")


@dataclass(frozen=True)
class Prompt:
    case_id: str
    condition: str
    text: str
    evidence_block: str
    additions: tuple[str, ...]


def build_prompt(case: Case, condition: str, *, neutral_override: str | None = None) -> Prompt:
    """Build a Base-model transcript prompt. NOT suitable for an Instruct model as-is."""
    if condition in FACTORIAL:
        s, f, h = FACTORIAL[condition]
        additions = tuple(
            block for enabled, block in (
                (s, f"Speaker style profile: {case.style_only}"),
                (f, f"Additional fact: {case.supplemental_fact}"),
                (h, case.history_dialogue),
            ) if enabled
        )
    elif condition == "N_style":
        additions = ((f"Speaker context note: {case.neutral_style}" if neutral_override is None
                      else f"Speaker style profile: {neutral_override}"),)
    elif condition == "N_history":
        additions = (case.neutral_history if neutral_override is None else neutral_override,)
    else:
        raise ValueError(f"Unknown conditioning treatment: {condition}")
    if neutral_override is not None and condition not in ("N_style", "N_history"):
        raise ValueError("Only neutral conditions accept a neutral override")

    evidence = f"TRUSTED EVIDENCE:\n{case.trusted_evidence}"
    extra = "\n\n".join(additions)
    context = "\n".join(case.context)
    parts = ["CONTINUE THE DIALOGUE. Use the verified facts for factual questions.", evidence]
    if extra:
        parts.append("ADDITIONAL CONTEXT:\n" + extra)
    parts.extend(["RECENT CONVERSATION:\n" + context,
                  f"User: {case.question}\nAssistant:"])
    return Prompt(case.case_id, condition, "\n\n".join(parts), evidence, additions)


def assert_same_evidence(case: Case, conditions: tuple[str, ...] | list[str]) -> None:
    built = [build_prompt(case, c) for c in conditions]
    if len({p.evidence_block for p in built}) != 1:
        raise AssertionError("Track A evidence differed between conditions")
    if any(p.text.count(p.evidence_block) != 1 for p in built):
        raise AssertionError("Trusted evidence missing or duplicated")
    if any(case.question not in p.text for p in built):
        raise AssertionError("The fixed user question changed")
