"""No private user data: synthetic city-update test cases only."""
import json
from pathlib import Path
from .schemas import Case

CITIES = [
    ("Lyon", "Paris"), ("Nantes", "Rennes"), ("Lille", "Dijon"),
    ("Bordeaux", "Toulouse"), ("Nice", "Grenoble"),
    ("Tours", "Rouen"), ("Caen", "Amiens"), ("Metz", "Nancy"),
    ("Reims", "Orleans"), ("Angers", "Poitiers"),
]


def build_cases() -> list[dict]:
    cases = []
    for i in range(20):
        old, new = CITIES[i % len(CITIES)]
        pronoun = "Alice" if i % 2 == 0 else "the person"
        question = (
            f"Where does {pronoun} currently live?" if i % 3 else
            f"What city is {pronoun} living in now?"
        )
        case = {
            "case_id": f"synthetic_{i+1:03d}", "persona_id": "alice",
            "evaluation_date": "2026-10-12", "task_type": "temporal_factual",
            "context": ["User: Please use the dated factual record when answering."],
            "question": question,
            "trusted_evidence": f"Verified current fact (2026-10-12): {pronoun} currently lives in {new}.",
            "expected_answer": new,
            "facts": [
                {"fact_id": f"past_{i:03d}", "attribute": "current_city", "value": old,
                 "valid_from": "2024-01-01", "valid_until": "2026-09-30"},
                {"fact_id": f"current_{i:03d}", "attribute": "current_city", "value": new,
                 "valid_from": "2026-10-01"},
            ],
            "style_only": "The target speaker uses short casual responses, sometimes saying 'haha'. This text has no factual details about homes, places or dates.",
            "supplemental_fact": "Additional unrelated verified fact: the target speaker likes board games.",
            "history_dialogue": f"Historical dialogue (2025-05-12):\nUser: Where were you living back then?\nAlice: In {old} at the time.",
            "neutral_style": "This is unrelated neutral filler about the formatting of written records. It does not mention people, addresses, locations or dates.",
            "neutral_history": "Archival transcript (2025-05-12):\nSpeaker A: Have you seen the document format?\nSpeaker B: Yes, the layout is readable.",
            "applicability": {
                "response_relevance": True, "factual_consistency": True,
                "temporal_consistency": True, "conversational_coherence": False,
                "linguistic_fidelity": False, "behavioral_fidelity": False,
            },
            "split": "p0_synthetic_only",
        }
        Case.from_dict(case)
        cases.append(case)
    return cases


def write_fixtures(path: Path) -> int:
    cases = build_cases()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
    return len(cases)


def load_cases(path: Path) -> list[Case]:
    cases = [Case.from_dict(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len({case.case_id for case in cases}) != len(cases):
        raise ValueError("duplicate case IDs")
    return cases
