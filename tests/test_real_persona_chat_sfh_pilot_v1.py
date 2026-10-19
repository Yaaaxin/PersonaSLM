import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "rpc_sfh_v1", REPO / "tools/real_persona_chat_sfh_pilot_v1.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_no_answer_leak_rejects_exact_and_near_copy():
    assert not MODULE._no_answer_leak("これは十分に長い正解です", ["これは十分に長い正解です"])
    assert not MODULE._no_answer_leak("これは十分に長い正解です", ["前置きこれは十分に長い正解です後書き"])
    assert MODULE._no_answer_leak("今日は散歩に行こうと思います", ["昨日は読書をしました"])
    assert not MODULE._no_answer_leak(
        "今も東京で暮らしています", [], ["東京に住んでいます"])


def test_messages_hold_surface_constant_and_apply_factor_bits():
    profile = {
        "speaker": "dev-a",
        "facts": ["事実一", "事実二"],
        "history": [
            {"interlocutor_id": "dev-a", "text": "前の返答"},
            {"interlocutor_id": "dev-b", "text": "前の質問"},
        ],
        "query": {"text": "今の質問"},
    }
    c0 = MODULE._messages(profile, (0, 0, 0), "平均発話長42文字")
    c7 = MODULE._messages(profile, (1, 1, 1), "平均発話長42文字")
    assert [value["role"] for value in c0] == ["system", "user"]
    for header in ("[話し方]", "[人物情報]", "[過去の会話]", "[相手の発話]"):
        assert header in c0[1]["content"] and header in c7[1]["content"]
    assert "平均発話長42文字" not in c0[1]["content"]
    assert "事実一" not in c0[1]["content"]
    assert "前の返答" not in c0[1]["content"]
    assert all(value in c7[1]["content"]
               for value in ("平均発話長42文字", "事実一", "前の返答"))
    assert "今の質問" in c0[1]["content"] and "今の質問" in c7[1]["content"]


def test_public_receipt_contains_no_private_text_or_ids(tmp_path, monkeypatch):
    private = tmp_path / "private.json"
    private.write_bytes(b"private\n")
    controller = tmp_path / "controller.py"
    controller.write_bytes(b"controller\n")
    intake_receipt = (tmp_path / "docs/validation/p1/real_persona_chat_intake_v1/"
                      "intake_receipt_v1.json")
    intake_receipt.parent.mkdir(parents=True)
    intake_receipt.write_bytes(b"{}\n")
    monkeypatch.setattr(MODULE, "__file__", str(controller))
    monkeypatch.setattr(MODULE, "REPO", tmp_path)
    material = {
        "dataset_root": str(tmp_path.resolve()),
        "split_assignment_sha256": "split",
        "selection_binding_sha256": "selection",
        "frozen_style_cohort_sha256": "style-cohort",
        "live_source": {
            "version": "1.0.0", "revision": "revision",
            "version_sha256": "version", "license_sha256": "license",
            "readme_sha256": "readme", "dialogues": 1,
            "dialogue_manifest_sha256": "dialogues",
            "interlocutors_sha256": "people",
        },
        "cases": [{
            "case_id": "RPCDEV01", "speaker_id": "SECRET-SPEAKER",
            "source_dialogue_ids": ["SECRET-DIALOGUE"],
            "style_source_turn_count": 20, "facts": ["SECRET-FACT"],
        }],
        "requests": [{
            "request_id": "RPCSFH000", "block": "B1", "latin_mask": 0,
            "within_case_position": 0, "condition": "C0",
            "prompt_sha256": "prompt", "reference_sha256": "reference",
        }],
    }
    monkeypatch.setattr(MODULE, "verify_live_source",
                        lambda root: material["live_source"])
    receipt = MODULE.public_receipt(material, private, tmp_path)
    rendered = json.dumps(receipt, ensure_ascii=False)
    assert "SECRET-SPEAKER" not in rendered
    assert "SECRET-DIALOGUE" not in rendered
    assert "SECRET-FACT" not in rendered
    assert receipt["privacy"]["participant_text_in_receipt"] is False


def test_conditions_and_xor_latin_schedule_are_balanced():
    assert set(MODULE.CONDITIONS) == {f"C{i}" for i in range(8)}
    assert set(MODULE.CONDITIONS.values()) == {
        (s, f, h) for s in (0, 1) for f in (0, 1) for h in (0, 1)}
    all_masks = MODULE.BLOCK_MASKS["B1"] + MODULE.BLOCK_MASKS["B2"]
    for position in range(8):
        assert sorted(MODULE.condition_schedule(mask)[position]
                      for mask in all_masks) == [f"C{i}" for i in range(8)]
        for block in ("B1", "B2"):
            bits = [MODULE.CONDITIONS[MODULE.condition_schedule(mask)[position]]
                    for mask in MODULE.BLOCK_MASKS[block]]
            assert all(sum(row[factor] for row in bits) == 2 for factor in range(3))


def test_development_people_does_not_decode_unselected_record(tmp_path):
    path = tmp_path / "people.json"
    path.write_text(
        '{\n'
        '    "dev": {\n'
        '        "interlocutor_id": "dev",\n'
        '        "persona": ["allowed"],\n'
        '        "personality": {"excluded": true}\n'
        '    },\n'
        '    "reserved": {\n'
        '        "interlocutor_id": "reserved",\n'
        '        "persona": [INVALID_RESERVED_JSON]\n'
        '    }\n'
        '}\n', encoding="utf-8")
    selected = MODULE._development_people(path, {"dev"})
    assert selected == {"dev": {"interlocutor_id": "dev", "persona": ["allowed"]}}


def test_dialogue_header_never_parses_utterance_body(tmp_path):
    path = tmp_path / "dialogue.json"
    path.write_text(
        '{\n'
        '    "dialogue_id": 1,\n'
        '    "interlocutors": [\n'
        '        "dev-a",\n'
        '        "reserved-b"\n'
        '    ],\n'
        '    "utterances": [\n'
        '        INVALID_RESERVED_UTTERANCE_JSON\n', encoding="utf-8")
    assert MODULE._dialogue_participants(path) == ["dev-a", "reserved-b"]


def test_private_output_is_forced_under_local(tmp_path, monkeypatch):
    monkeypatch.setattr(MODULE, "REPO", tmp_path)
    allowed = MODULE.private_output_path(tmp_path / ".local" / "experiment" / "rows.json")
    assert tmp_path / ".local" in allowed.parents
    for forbidden in (tmp_path / "docs" / "rows.json", tmp_path / ".local"):
        try:
            MODULE.private_output_path(forbidden)
        except ValueError:
            pass
        else:
            raise AssertionError(f"private path escape accepted: {forbidden}")


def test_live_source_hash_rejects_changed_dialogue_bytes(tmp_path, monkeypatch):
    dataset = tmp_path / "dataset"
    dialogue_dir = dataset / "real_persona_chat" / "dialogues"
    dialogue_dir.mkdir(parents=True)
    (dataset / "LICENSE").write_text("license", encoding="utf-8")
    (dataset / "README.md").write_text("readme", encoding="utf-8")
    (dataset / "VERSION").write_text("1.0.0", encoding="utf-8")
    people = dataset / "real_persona_chat" / "interlocutors.json"
    people.write_text("{}", encoding="utf-8")
    dialogue = dialogue_dir / "00001.json"
    dialogue.write_text("{\"safe\":true}", encoding="utf-8")
    manifest = MODULE.hashlib.sha256()
    file_hash = MODULE.digest_file(dialogue)
    manifest.update(b"00001.json\0" + file_hash.encode("ascii") + b"\n")
    expected = {
        "version": "1.0.0", "revision": "revision",
        "license_sha256": MODULE.digest_file(dataset / "LICENSE"),
        "readme_sha256": MODULE.digest_file(dataset / "README.md"),
        "version_sha256": MODULE.digest_file(dataset / "VERSION"),
        "interlocutors_sha256": MODULE.digest_file(people),
        "dialogue_manifest_sha256": manifest.hexdigest(), "dialogues": 1,
    }
    receipt = (tmp_path / "repo/docs/validation/p1/real_persona_chat_intake_v1/"
               "intake_receipt_v1.json")
    receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps({"status": "PASS", "source": expected}),
                       encoding="utf-8")
    monkeypatch.setattr(MODULE, "REPO", tmp_path / "repo")
    monkeypatch.setattr(MODULE.intake, "EXPECTED", expected)
    monkeypatch.setattr(MODULE.intake, "revision", lambda root: "revision")
    assert MODULE.verify_live_source(dataset) == expected
    dialogue.write_text("{\"safe\":false}", encoding="utf-8")
    with pytest.raises(ValueError, match="source changed"):
        MODULE.verify_live_source(dataset)


def test_main_removes_new_private_file_if_receipt_construction_fails(
        tmp_path, monkeypatch):
    monkeypatch.setattr(MODULE, "REPO", tmp_path)
    monkeypatch.setattr(MODULE, "build_material", lambda root: {"private": "text"})

    def fail_receipt(*args):
        raise RuntimeError("receipt failed")

    monkeypatch.setattr(MODULE, "public_receipt", fail_receipt)
    private = tmp_path / ".local" / "experiment" / "materials.json"
    public = tmp_path / "docs" / "receipt.json"
    with pytest.raises(RuntimeError, match="receipt failed"):
        MODULE.main([
            "--dataset-root", str(tmp_path / "dataset"),
            "--private-output", str(private),
            "--public-output", str(public),
        ])
    assert not private.exists()
    assert not public.exists()


def test_style_prompt_converts_scaled_length_back_to_characters(monkeypatch):
    observed = {
        "mean_turn_length": 0.5,
        "sd_turn_length": 0.2,
        "question_turn_rate": 0.1,
        "exclamation_turn_rate": 0.2,
        "ellipsis_turn_rate": 0.3,
        "laughter_turn_rate": 0.4,
        "polite_ending_rate": 0.5,
    }
    monkeypatch.setattr(MODULE.style_signal, "style_vector", lambda rows: observed)
    profile = {"sources": [{"speaker_turns": ["a"]}, {"speaker_turns": ["b"]}]}
    text, stored = MODULE._style_profile(profile)
    assert "平均約25.0文字" in text
    assert "標準偏差は約10.0文字" in text
    assert stored["mean_turn_length_characters"] == 25.0
    assert stored["sd_turn_length_characters"] == 10.0
    assert "mean_turn_length" not in stored
