import json
import hashlib
import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import literature_monitor as monitor


ARXIV_V1 = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2601.12345v1</id><updated>2026-01-02T00:00:00Z</updated>
    <published>2026-01-01T00:00:00Z</published><title> Persona Memory Study </title>
    <summary>First abstract.</summary><author><name>Ada Example</name></author>
    <link href="https://arxiv.org/abs/2601.12345v1" rel="alternate" />
  </entry>
</feed>"""

ARXIV_V2 = ARXIV_V1.replace("v1</id>", "v2</id>").replace(
    "2026-01-02T00:00:00Z", "2026-01-03T00:00:00Z"
).replace("First abstract.", "A longer revised abstract for the same stable preprint.").replace(
    "2601.12345v1\"", "2601.12345v2\""
)


def minimal_ledger():
    return {
        "schema_version": "personaslm_reviewed_literature_ledger_v1",
        "records": [],
    }


def minimal_config():
    return {
        "schema_version": "personaslm_literature_monitor_config_v1",
        "lookback_days": 21,
        "request_interval_seconds": 0,
        "timeout_seconds": 3,
        "topic_queries": ["persona memory"],
        "sources": {
            "arxiv": {"endpoint": "https://export.arxiv.org/api/query", "max_results": 10},
            "crossref": {"endpoint": "https://api.crossref.org/works", "max_results_per_query": 10},
            "openalex": {"endpoint": "https://api.openalex.org/works", "max_results_per_query": 10},
        },
    }


class LiteratureMonitorTests(unittest.TestCase):
    def test_identifier_normalization(self):
        self.assertEqual(monitor.normalize_doi("https://doi.org/10.1234/ABC.1"), "10.1234/abc.1")
        self.assertEqual(monitor.parse_arxiv_id("https://arxiv.org/pdf/2601.12345v7.pdf"), ("2601.12345", "v7"))
        self.assertEqual(monitor.normalize_acl_id("https://aclanthology.org/2026.ACL-LONG.1/"), "2026.acl-long.1")

    def test_arxiv_parser_retains_version(self):
        record = monitor.parse_arxiv_atom(ARXIV_V1)[0]
        self.assertEqual(record["identifiers"]["arxiv"], "2601.12345")
        self.assertEqual(record["versions"][0]["label"], "v1")
        self.assertEqual(record["authors"], ["Ada Example"])

    def test_arxiv_versions_deduplicate_by_base_identifier(self):
        records = monitor.parse_arxiv_atom(ARXIV_V1) + monitor.parse_arxiv_atom(ARXIV_V2)
        merged = monitor.deduplicate(records)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["stable_id"], "arxiv:2601.12345")
        self.assertEqual({item["label"] for item in merged[0]["versions"]}, {"v1", "v2"})
        self.assertIn("revised", merged[0]["abstract"])

    def test_crossref_and_openalex_deduplicate_by_doi(self):
        crossref = monitor.parse_crossref_message(
            {"message": {"items": [{
                "DOI": "10.1000/XYZ", "title": ["Shared paper"],
                "author": [{"given": "A", "family": "Author"}],
                "issued": {"date-parts": [[2026, 2, 3]]}, "URL": "https://doi.org/10.1000/xyz",
            }]}}
        )
        openalex = monitor.parse_openalex_results(
            {"results": [{
                "id": "https://openalex.org/W1", "doi": "https://doi.org/10.1000/XYZ",
                "title": "Shared paper", "publication_date": "2026-02-03",
                "authorships": [{"author": {"display_name": "A Author"}}],
                "primary_location": {"source": {"display_name": "Venue"}}, "ids": {"openalex": "https://openalex.org/W1"},
            }]}
        )
        merged = monitor.deduplicate(crossref + openalex)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["stable_id"], "doi:10.1000/xyz")
        self.assertEqual(set(merged[0]["source_names"]), {"Crossref", "OpenAlex"})

    def test_crossref_null_month_and_day_preserve_verified_year(self):
        records = monitor.parse_crossref_message(
            {"message": {"items": [{
                "DOI": "10.1000/null-date", "title": ["Partial date paper"],
                "issued": {"date-parts": [[2026, None, None]]},
            }]}}
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["publication_date"], "2026")

    def test_openalex_reconstructs_abstract(self):
        record = monitor.parse_openalex_results(
            {"results": [{
                "id": "https://openalex.org/W2", "title": "X", "ids": {"openalex": "https://openalex.org/W2"},
                "abstract_inverted_index": {"Temporal": [0], "memory": [1], "works": [2]},
            }]}
        )[0]
        self.assertEqual(record["abstract"], "Temporal memory works")

    def test_snapshot_is_deterministic_and_marks_known_version_update(self):
        ledger = minimal_ledger()
        ledger["records"] = [{
            "stable_id": "arxiv:2601.12345", "identifiers": {"arxiv": "2601.12345"},
            "versions": [{"label": "v1"}], "relevance_assessment": {"classification": "PARTIAL_OVERLAP"},
            **{name: "x" for name in (
                "title", "venue_or_status", "publication_date", "source_url", "verified_abstract_or_summary",
                "research_methodology", "relevant_experimental_factors", "relevant_benchmarks", "overlap_with_personaslm",
                "difference_from_personaslm", "potential_novelty_threat", "potential_useful_baselines",
                "potential_methodological_improvements", "date_last_checked",
            )},
            "authors": ["A"],
            "verification": {"human_confirmation": "NOT_RECORDED"},
        }]

        def fetch(url, _timeout):
            if "arxiv" in url:
                return ARXIV_V2.encode()
            if "crossref" in url:
                return b'{"message":{"items":[]}}'
            return b'{"results":[]}'

        first, ok1 = monitor.make_snapshot(minimal_config(), ledger, date(2026, 1, 5), fetch=fetch, sleep=lambda _: None)
        second, ok2 = monitor.make_snapshot(minimal_config(), ledger, date(2026, 1, 5), fetch=fetch, sleep=lambda _: None)
        self.assertTrue(ok1 and ok2)
        self.assertEqual(first, second)
        self.assertEqual(first["records"][0]["discovery_status"], "POSSIBLE_VERSION_UPDATE")
        self.assertEqual(first["scientific_status"], "AUTOMATED_DISCOVERY_ONLY_REQUIRES_PRIMARY_SOURCE_REVIEW")

    def test_failed_sources_are_recorded_without_invented_results(self):
        def fail(_url, _timeout):
            raise OSError("offline")

        snapshot, ok = monitor.make_snapshot(minimal_config(), minimal_ledger(), date(2026, 1, 5), fetch=fail, sleep=lambda _: None)
        self.assertFalse(ok)
        self.assertEqual(snapshot["record_count"], 0)
        self.assertEqual(snapshot["source_request_summary"]["failed"], 3)
        self.assertTrue(all(row["error_type"] == "OSError" for row in snapshot["source_request_summary"]["requests"]))

    def test_repository_config_and_reviewed_ledger_validate(self):
        config = monitor.json_read(ROOT / "docs/validation/literature_monitor_v1/config_v1.json")
        ledger = monitor.json_read(ROOT / "docs/validation/literature_monitor_v1/reviewed_ledger_v1.json")
        self.assertEqual(monitor.validate_config(config), [])
        self.assertEqual(monitor.validate_ledger(ledger), [])
        self.assertEqual(len(ledger["records"]), 14)

    def test_workflow_is_daily_read_only_and_token_free(self):
        text = (ROOT / ".github/workflows/daily-literature-monitor.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '23 4 * * *'", text)
        self.assertIn("contents: read", text)
        self.assertIn("upload-artifact", text)
        for forbidden in ("contents: write", "git push", "git commit", "git add", "secrets."):
            self.assertNotIn(forbidden, text)

    def test_schema_lists_all_scientific_review_fields(self):
        schema = monitor.json_read(ROOT / "docs/validation/literature_monitor_v1/ledger_schema_v1.json")
        required = set(schema["properties"]["records"]["items"]["required"])
        self.assertTrue({
            "title", "authors", "publication_date", "identifiers", "source_url", "research_methodology",
            "relevant_experimental_factors", "relevant_benchmarks", "overlap_with_personaslm",
            "difference_from_personaslm", "potential_novelty_threat", "potential_useful_baselines",
            "potential_methodological_improvements", "relevance_assessment", "date_last_checked",
        }.issubset(required))

    def test_latest_check_receipt_hashes_all_bound_artifacts_and_preserves_predecessor(self):
        receipt = monitor.json_read(
            ROOT / "docs/validation/literature_monitor_v1/literature_checkpoint_2026-10-18_v1.json"
        )
        predecessor = ROOT / receipt["predecessor"]["path"]
        self.assertTrue(predecessor.is_file())
        self.assertEqual(
            hashlib.sha256(predecessor.read_bytes()).hexdigest(),
            receipt["predecessor"]["sha256"],
        )
        self.assertGreaterEqual(len(receipt["artifact_hashes"]), 6)
        for relative_path, expected in receipt["artifact_hashes"].items():
            path = ROOT / relative_path
            self.assertTrue(path.is_file(), relative_path)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected, relative_path)


if __name__ == "__main__":
    unittest.main()
