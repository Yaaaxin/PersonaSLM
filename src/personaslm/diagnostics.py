"""Distinguish model output, stop behavior, and parser deletion."""
from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class ParseResult:
    raw_text: str
    parsed_text: str
    steps: tuple[str, ...]
    classification: str
    transformations: tuple[dict, ...] = ()

    def audit(self) -> dict:
        return {"parser_version": "p0_parser_v2", "classification": self.classification,
                "raw_characters": len(self.raw_text), "parsed_characters": len(self.parsed_text),
                "raw_empty": not self.raw_text, "raw_visible_empty": not self.raw_text.strip(),
                "parsed_empty": not self.parsed_text, "changed": self.raw_text != self.parsed_text,
                "raw_sha256": hashlib.sha256(self.raw_text.encode("utf-8")).hexdigest(),
                "parsed_sha256": hashlib.sha256(self.parsed_text.encode("utf-8")).hexdigest(),
                "steps": self.steps, "transformations": self.transformations,
                "eos_classification_basis": "reported termination plus empty content; not a token-level proof"}


def parse_reply(raw_text: str, *, stop_reason: str | None = None,
                stop_at_first_newline: bool = False, filter_all: bool = False) -> ParseResult:
    """P0 diagnostic parser. Never modifies the logged raw_text."""
    if not isinstance(raw_text, str):
        raise TypeError("raw_text must be a string")
    steps: list[str] = []
    transformations: list[dict] = []
    parsed = raw_text

    def apply_step(name, before, after):
        steps.append(name)
        transformations.append({"step": name, "before": before, "after": after,
                                "removed_characters": len(before) - len(after)})

    if not parsed:
        if stop_reason in {"eos", "end_of_sequence", "eog"}:
            return ParseResult(raw_text, "", tuple(steps), "direct_eos")
        if stop_reason in {"stop", "stop_sequence", "word"}:
            return ParseResult(raw_text, "", tuple(steps), "stop_without_visible_text")
        return ParseResult(raw_text, "", tuple(steps), "raw_empty")

    if stop_at_first_newline and ("\n" in parsed or "\r" in parsed):
        before = parsed
        parsed = parsed.splitlines()[0]
        apply_step("first_newline_stop", before, parsed)
        if not parsed.strip():
            if parsed:
                apply_step("whitespace_strip", parsed, "")
            return ParseResult(raw_text, "", tuple(steps), "newline_truncation", tuple(transformations))

    before = parsed
    parsed = parsed.strip()
    if parsed != before:
        apply_step("whitespace_strip", before, parsed)

    for prefix in ("Assistant:", "Alice:"):
        if parsed.startswith(prefix):
            before = parsed
            parsed = parsed[len(prefix):].strip()
            apply_step("speaker_prefix_removed", before, parsed)
            break

    if filter_all:
        before = parsed
        parsed = ""
        apply_step("downstream_filter_removed", before, parsed)

    if not parsed:
        return ParseResult(raw_text, "", tuple(steps), "parsing_or_filter_removed", tuple(transformations))
    return ParseResult(raw_text, parsed, tuple(steps), "preserved", tuple(transformations))
