import json
import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import literature_monitor as monitor


ARXIV_RECORD = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2601.12345v1</id>
    <updated>2026-01-02T00:00:00Z</updated>
    <published>2026-01-01T00:00:00Z</published>
    <title>Persona Memory Study</title>
    <summary>First abstract.</summary>
    <author><name>Ada Example</name></author>
  </entry>
</feed>"""


def minimal_ledger():
    return {
        "schema_version": "personaslm_reviewed_literature_ledger_v1",
        "records": [{
            "stable_id": "arxiv:2601.12345",
            "identifiers": {"arxiv": "2601.12345"},
            "versions": [],
            "relevance_assessment": {"classification": "PARTIAL_OVERLAP"},
            **{name: "x" for name in (
                "title", "venue_or_status", "publication_date", "source_url", "verified_abstract_or_summary",
                "research_methodology", "relevant_experimental_factors", "relevant_benchmarks",
                "overlap_with_personaslm", "difference_from_personaslm", "potential_novelty_threat",
                "potential_useful_baselines", "potential_methodological_improvements", "date_last_checked",
            )},
            "authors": ["A"],
            "verification": {"human_confirmation": "NOT_RECORDED"},
        }],
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


class ArxivDoiDedupTests(unittest.TestCase):
    def test_official_arxiv_doi_produces_arxiv_alias(self):
        record = {"identifiers": {"doi": "https://doi.org/10.48550/arXiv.2601.12345"}}
        self.assertEqual(monitor.arxiv_id_from_doi(record["identifiers"]["doi"]), "2601.12345")
        self.assertEqual(
            monitor.stable_aliases(record),
            ["arxiv:2601.12345", "doi:10.48550/arxiv.2601.12345"],
        )
        self.assertEqual(monitor.arxiv_id_from_doi("10.48550/example.2601.12345"), "")

    def test_explicit_arxiv_metadata_is_not_silently_overridden(self):
        record = {
            "identifiers": {
                "doi": "10.48550/arxiv.2601.12345",
                "arxiv": "2601.99999",
            }
        }
        self.assertEqual(
            monitor.stable_aliases(record),
            ["arxiv:2601.99999", "doi:10.48550/arxiv.2601.12345"],
        )

    def test_arxiv_record_and_official_arxiv_doi_deduplicate(self):
        arxiv = monitor.parse_arxiv_atom(ARXIV_RECORD)
        crossref = monitor.parse_crossref_message(
            {"message": {"items": [{
                "DOI": "10.48550/arXiv.2601.12345",
                "title": ["Persona Memory Study"],
                "issued": {"date-parts": [[2026, 1, 1]]},
            }]}}
        )
        merged = monitor.deduplicate(arxiv + crossref)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["stable_id"], "doi:10.48550/arxiv.2601.12345")
        self.assertEqual(merged[0]["identifiers"]["arxiv"], "2601.12345")
        self.assertEqual(set(merged[0]["source_names"]), {"arXiv", "Crossref"})

    def test_official_arxiv_doi_matches_arxiv_only_reviewed_record(self):
        def fetch(url, _timeout):
            if "crossref" in url:
                return json.dumps({"message": {"items": [{
                    "DOI": "10.48550/arXiv.2601.12345",
                    "title": ["Persona Memory Study"],
                    "issued": {"date-parts": [[2026, 1, 1]]},
                }]}}).encode()
            if "arxiv" in url:
                return b'<feed xmlns="http://www.w3.org/2005/Atom" />'
            return b'{"results":[]}'

        snapshot, ok = monitor.make_snapshot(
            minimal_config(), minimal_ledger(), date(2026, 1, 5), fetch=fetch, sleep=lambda _: None
        )
        self.assertTrue(ok)
        self.assertEqual(snapshot["record_count"], 1)
        self.assertEqual(snapshot["records"][0]["discovery_status"], "KNOWN_NO_NEW_VERSION_DETECTED")


if __name__ == "__main__":
    unittest.main()
