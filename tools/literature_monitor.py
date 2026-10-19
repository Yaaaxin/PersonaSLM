"""Deterministic discovery snapshots for PersonaSLM literature surveillance.

Discovery records are deliberately *not* scientific assessments.  The reviewed
ledger remains a human/agent-reviewed artifact whose entries cite primary
sources.  This module uses only the Python standard library and free public
metadata APIs; it never needs repository or service credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


USER_AGENT = "PersonaSLM-Literature-Monitor/1.0 (+https://github.com/Yaaaxin/PersonaSLM)"
CLASSIFICATIONS = {
    "DIRECT_OVERLAP",
    "PARTIAL_OVERLAP",
    "COMPLEMENTARY",
    "BASELINE_RELEVANT",
    "EVALUATION_RELEVANT",
    "LOW_RELEVANCE",
}
IDENTIFIER_KEYS = ("doi", "arxiv", "acl_anthology", "openreview", "openalex")
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def normalize_doi(value: Any) -> str:
    doi = clean_text(value).lower()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi)
    return doi.rstrip(" .")


def parse_arxiv_id(value: Any) -> tuple[str, str]:
    text = clean_text(value)
    text = re.sub(r"^https?://(?:export\.)?arxiv\.org/(?:abs|pdf)/", "", text)
    text = re.sub(r"^arxiv:\s*", "", text, flags=re.I)
    text = text.removesuffix(".pdf")
    match = re.search(r"(?P<base>(?:[a-z-]+/\d{7}|\d{4}\.\d{4,5}))(?P<version>v\d+)?$", text, re.I)
    if not match:
        return "", ""
    return match.group("base").lower(), (match.group("version") or "").lower()


def arxiv_id_from_doi(value: Any) -> str:
    """Return the base arXiv ID represented by an official arXiv DOI."""
    doi = normalize_doi(value)
    prefix = "10.48550/arxiv."
    if not doi.startswith(prefix):
        return ""
    return parse_arxiv_id(doi.removeprefix(prefix))[0]


def normalize_acl_id(value: Any) -> str:
    text = clean_text(value)
    text = re.sub(r"^https?://aclanthology\.org/", "", text, flags=re.I)
    return text.rstrip("/.").lower()


def normalize_openreview_id(value: Any) -> str:
    text = clean_text(value)
    match = re.search(r"(?:id=|/forum\?id=)([A-Za-z0-9_-]+)", text)
    return (match.group(1) if match else text).strip()


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def json_read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _date_parts(value: Any) -> str:
    try:
        parts = value[0]
    except (IndexError, TypeError):
        return ""
    if not isinstance(parts, (list, tuple)):
        return ""
    rendered = []
    for index, part in enumerate(parts[:3]):
        if part in (None, ""):
            break
        try:
            number = int(part)
        except (TypeError, ValueError):
            return ""
        if index == 0:
            if not 1000 <= number <= 9999:
                return ""
            rendered.append(f"{number:04d}")
        elif index == 1:
            if not 1 <= number <= 12:
                break
            rendered.append(f"{number:02d}")
        else:
            if not 1 <= number <= 31:
                break
            rendered.append(f"{number:02d}")
    return "-".join(rendered)


def _openalex_abstract(index: Any) -> str:
    if not isinstance(index, dict):
        return ""
    positions: list[tuple[int, str]] = []
    for word, offsets in index.items():
        if isinstance(offsets, list):
            positions.extend((int(offset), str(word)) for offset in offsets)
    return " ".join(word for _, word in sorted(positions))


def parse_arxiv_atom(payload: str) -> list[dict[str, Any]]:
    root = ET.fromstring(payload)
    records = []
    for entry in root.findall(f"{ATOM}entry"):
        raw_id = entry.findtext(f"{ATOM}id", default="")
        arxiv_id, version = parse_arxiv_id(raw_id)
        if not arxiv_id:
            continue
        doi = normalize_doi(entry.findtext(f"{ARXIV}doi", default=""))
        links = [link.attrib.get("href", "") for link in entry.findall(f"{ATOM}link")]
        records.append(
            {
                "title": clean_text(entry.findtext(f"{ATOM}title", default="")),
                "authors": [
                    clean_text(author.findtext(f"{ATOM}name", default=""))
                    for author in entry.findall(f"{ATOM}author")
                ],
                "publication_date": clean_text(entry.findtext(f"{ATOM}published", default=""))[:10],
                "updated_date": clean_text(entry.findtext(f"{ATOM}updated", default=""))[:10],
                "venue_or_status": clean_text(entry.findtext(f"{ARXIV}journal_ref", default="")) or "arXiv preprint",
                "abstract": clean_text(entry.findtext(f"{ATOM}summary", default="")),
                "identifiers": {"arxiv": arxiv_id, "doi": doi},
                "versions": ([{"label": version, "updated_date": clean_text(entry.findtext(f"{ATOM}updated", default=""))[:10]}] if version else []),
                "source_names": ["arXiv"],
                "source_urls": sorted(set([raw_id, *links]) - {""}),
            }
        )
    return records


def parse_crossref_message(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get("message", {}).get("items", [])
    records = []
    for item in items if isinstance(items, list) else []:
        title_values = item.get("title") or []
        container = item.get("container-title") or []
        authors = []
        for author in item.get("author") or []:
            name = clean_text(" ".join(part for part in (author.get("given", ""), author.get("family", "")) if part))
            if name:
                authors.append(name)
        published = item.get("published-online") or item.get("published-print") or item.get("issued") or {}
        doi = normalize_doi(item.get("DOI", ""))
        url = clean_text(item.get("URL", ""))
        records.append(
            {
                "title": clean_text(title_values[0] if title_values else ""),
                "authors": authors,
                "publication_date": _date_parts(published.get("date-parts")),
                "updated_date": clean_text((item.get("indexed") or {}).get("date-time", ""))[:10],
                "venue_or_status": clean_text(container[0] if container else item.get("publisher", "")),
                "abstract": clean_text(item.get("abstract", "")),
                "identifiers": {"doi": doi},
                "versions": [],
                "source_names": ["Crossref"],
                "source_urls": sorted(set(filter(None, [url, f"https://doi.org/{doi}" if doi else ""]))),
            }
        )
    return [record for record in records if record["title"] and any(record["identifiers"].values())]


def parse_openalex_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for item in payload.get("results", []) if isinstance(payload.get("results", []), list) else []:
        ids = item.get("ids") or {}
        doi = normalize_doi(ids.get("doi") or item.get("doi") or "")
        arxiv_id, arxiv_version = parse_arxiv_id(ids.get("arxiv", ""))
        primary_location = item.get("primary_location") or {}
        source = primary_location.get("source") or {}
        authors = [
            clean_text((authorship.get("author") or {}).get("display_name", ""))
            for authorship in item.get("authorships") or []
        ]
        openalex_id = clean_text(ids.get("openalex") or item.get("id") or "").rsplit("/", 1)[-1]
        records.append(
            {
                "title": clean_text(item.get("title") or item.get("display_name") or ""),
                "authors": [author for author in authors if author],
                "publication_date": clean_text(item.get("publication_date", "")),
                "updated_date": clean_text(item.get("updated_date", ""))[:10],
                "venue_or_status": clean_text(source.get("display_name") or item.get("type_crossref") or item.get("type") or ""),
                "abstract": clean_text(_openalex_abstract(item.get("abstract_inverted_index"))),
                "identifiers": {"doi": doi, "arxiv": arxiv_id, "openalex": openalex_id},
                "versions": ([{"label": arxiv_version, "updated_date": clean_text(item.get("updated_date", ""))[:10]}] if arxiv_version else []),
                "source_names": ["OpenAlex"],
                "source_urls": sorted(
                    set(
                        filter(
                            None,
                            [
                                clean_text(item.get("id", "")),
                                clean_text(primary_location.get("landing_page_url", "")),
                                f"https://doi.org/{doi}" if doi else "",
                            ],
                        )
                    )
                ),
            }
        )
    return [record for record in records if record["title"] and any(record["identifiers"].values())]


def stable_aliases(record: dict[str, Any]) -> list[str]:
    identifiers = record.get("identifiers") or {}
    explicit_arxiv_id = parse_arxiv_id(identifiers.get("arxiv", ""))[0]
    aliases = []
    for key in IDENTIFIER_KEYS:
        value = clean_text(identifiers.get(key, ""))
        if not value:
            continue
        if key == "doi":
            value = normalize_doi(value)
            arxiv_id = arxiv_id_from_doi(value)
            if arxiv_id and not explicit_arxiv_id:
                aliases.append(f"arxiv:{arxiv_id}")
        elif key == "arxiv":
            value = parse_arxiv_id(value)[0]
        elif key == "acl_anthology":
            value = normalize_acl_id(value)
        elif key == "openreview":
            value = normalize_openreview_id(value)
        elif key == "openalex":
            value = value.rsplit("/", 1)[-1]
        if value:
            aliases.append(f"{key}:{value}")
    return sorted(set(aliases))


def canonical_stable_id(record: dict[str, Any]) -> str:
    aliases = stable_aliases(record)
    for prefix in ("doi:", "arxiv:", "acl_anthology:", "openreview:", "openalex:"):
        match = next((alias for alias in aliases if alias.startswith(prefix)), None)
        if match:
            return match
    raise ValueError(f"record has no stable identifier: {record.get('title', '<untitled>')}")


def _merge_unique(left: Iterable[Any], right: Iterable[Any], key: Callable[[Any], str] = lambda value: str(value)) -> list[Any]:
    output: dict[str, Any] = {}
    for value in [*left, *right]:
        output.setdefault(key(value), value)
    return [output[name] for name in sorted(output)]


def merge_record(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    result = dict(existing)
    for field in ("title", "publication_date", "updated_date", "venue_or_status", "abstract"):
        old, new = clean_text(result.get(field, "")), clean_text(incoming.get(field, ""))
        if (not old) or (field == "abstract" and len(new) > len(old)) or (field == "updated_date" and new > old):
            result[field] = new
    result["authors"] = _merge_unique(result.get("authors", []), incoming.get("authors", []), clean_text)
    identifiers = dict(result.get("identifiers") or {})
    for key, value in (incoming.get("identifiers") or {}).items():
        if value and not identifiers.get(key):
            identifiers[key] = value
    result["identifiers"] = {key: identifiers[key] for key in sorted(identifiers) if identifiers[key]}
    result["versions"] = _merge_unique(
        result.get("versions", []),
        incoming.get("versions", []),
        lambda value: f"{value.get('label', '')}|{value.get('updated_date', '')}",
    )
    result["source_names"] = _merge_unique(result.get("source_names", []), incoming.get("source_names", []))
    result["source_urls"] = _merge_unique(result.get("source_urls", []), incoming.get("source_urls", []))
    return result


def deduplicate(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    alias_to_group: dict[str, int] = {}
    for record in sorted(records, key=lambda item: (canonical_stable_id(item), clean_text(item.get("title", "")))):
        aliases = stable_aliases(record)
        matched = sorted({alias_to_group[alias] for alias in aliases if alias in alias_to_group})
        if not matched:
            group_index = len(groups)
            groups.append(record)
        else:
            group_index = matched[0]
            groups[group_index] = merge_record(groups[group_index], record)
            for other in reversed(matched[1:]):
                groups[group_index] = merge_record(groups[group_index], groups[other])
                del groups[other]
                alias_to_group = {
                    alias: (index - 1 if index > other else index)
                    for alias, index in alias_to_group.items()
                    if index != other
                }
        for alias in stable_aliases(groups[group_index]):
            alias_to_group[alias] = group_index
    output = []
    for record in groups:
        item = dict(record)
        item["stable_id"] = canonical_stable_id(item)
        output.append(item)
    return sorted(output, key=lambda item: item["stable_id"])


def validate_config(config: dict[str, Any]) -> list[str]:
    errors = []
    if config.get("schema_version") != "personaslm_literature_monitor_config_v1":
        errors.append("unexpected config schema_version")
    topics = config.get("topic_queries")
    if not isinstance(topics, list) or not topics or not all(isinstance(value, str) and value.strip() for value in topics):
        errors.append("topic_queries must be a non-empty string list")
    sources = config.get("sources")
    if not isinstance(sources, dict) or not {"arxiv", "crossref", "openalex"}.issubset(sources):
        errors.append("sources must configure arxiv, crossref, and openalex")
    if not isinstance(config.get("lookback_days"), int) or not 1 <= config.get("lookback_days", 0) <= 365:
        errors.append("lookback_days must be between 1 and 365")
    return errors


def validate_ledger(ledger: dict[str, Any]) -> list[str]:
    errors = []
    if ledger.get("schema_version") != "personaslm_reviewed_literature_ledger_v1":
        errors.append("unexpected ledger schema_version")
    records = ledger.get("records")
    if not isinstance(records, list):
        return errors + ["records must be a list"]
    seen: set[str] = set()
    required = {
        "stable_id", "title", "authors", "venue_or_status", "publication_date", "identifiers",
        "source_url", "verified_abstract_or_summary", "research_methodology", "relevant_experimental_factors",
        "relevant_benchmarks", "overlap_with_personaslm", "difference_from_personaslm",
        "potential_novelty_threat", "potential_useful_baselines", "potential_methodological_improvements",
        "relevance_assessment", "versions", "verification", "date_last_checked",
    }
    for index, record in enumerate(records):
        missing = sorted(required - set(record))
        if missing:
            errors.append(f"records[{index}] missing: {', '.join(missing)}")
        stable_id = record.get("stable_id")
        if not isinstance(stable_id, str) or not stable_id:
            errors.append(f"records[{index}].stable_id is empty")
        elif stable_id in seen:
            errors.append(f"duplicate stable_id: {stable_id}")
        else:
            seen.add(stable_id)
        relevance = record.get("relevance_assessment")
        relevance = relevance if isinstance(relevance, dict) else {}
        classification = relevance.get("classification")
        if classification not in CLASSIFICATIONS:
            errors.append(f"records[{index}] invalid relevance classification: {classification}")
        verification = record.get("verification")
        verification = verification if isinstance(verification, dict) else {}
        if verification.get("human_confirmation") not in {"NOT_RECORDED", "CONFIRMED"}:
            errors.append(f"records[{index}] invalid human_confirmation")
        try:
            derived = canonical_stable_id(record)
            aliases = stable_aliases(record)
            if stable_id not in aliases and stable_id != derived:
                errors.append(f"records[{index}] stable_id is not represented by identifiers")
        except ValueError as exc:
            errors.append(f"records[{index}] {exc}")
    return errors


def _http_get(url: str, timeout_seconds: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/atom+xml;q=0.9, text/xml;q=0.8"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return response.read()


def _query_urls(config: dict[str, Any], as_of: date) -> list[tuple[str, str]]:
    cutoff = as_of - timedelta(days=config["lookback_days"])
    topics = config["topic_queries"]
    sources = config["sources"]
    arxiv_terms = " OR ".join(f'all:"{term}"' for term in topics)
    urls = [
        (
            "arxiv",
            sources["arxiv"]["endpoint"] + "?" + urllib.parse.urlencode(
                {"search_query": arxiv_terms, "start": 0, "max_results": sources["arxiv"]["max_results"], "sortBy": "lastUpdatedDate", "sortOrder": "descending"}
            ),
        )
    ]
    for topic in topics:
        urls.append(
            (
                "crossref",
                sources["crossref"]["endpoint"] + "?" + urllib.parse.urlencode(
                    {
                        "query.bibliographic": topic,
                        "filter": f"from-index-date:{cutoff.isoformat()},until-index-date:{as_of.isoformat()}",
                        "rows": sources["crossref"]["max_results_per_query"],
                        "select": "DOI,title,author,published-online,published-print,issued,indexed,container-title,publisher,abstract,URL",
                    }
                ),
            )
        )
        urls.append(
            (
                "openalex",
                sources["openalex"]["endpoint"] + "?" + urllib.parse.urlencode(
                    {
                        "search": topic,
                        "filter": f"from_publication_date:{cutoff.isoformat()},to_publication_date:{as_of.isoformat()}",
                        "per-page": sources["openalex"]["max_results_per_query"],
                        "select": "id,doi,title,display_name,publication_date,updated_date,type,type_crossref,authorships,primary_location,abstract_inverted_index,ids",
                    }
                ),
            )
        )
    return urls


def _known_aliases(ledger: dict[str, Any]) -> tuple[set[str], dict[str, set[str]]]:
    aliases: set[str] = set()
    versions: dict[str, set[str]] = {}
    for record in ledger.get("records", []):
        record_aliases = set(stable_aliases(record)) | {record.get("stable_id", "")}
        aliases.update(record_aliases - {""})
        labels = {clean_text(value.get("label", "")) for value in record.get("versions", []) if isinstance(value, dict)} - {""}
        for alias in record_aliases:
            if alias:
                versions.setdefault(alias, set()).update(labels)
    return aliases, versions


def make_snapshot(
    config: dict[str, Any],
    ledger: dict[str, Any],
    as_of: date,
    fetch: Callable[[str, int], bytes] = _http_get,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[dict[str, Any], bool]:
    errors = validate_config(config) + validate_ledger(ledger)
    if errors:
        raise ValueError("; ".join(errors))
    records: list[dict[str, Any]] = []
    requests = []
    successes = 0
    cutoff = as_of - timedelta(days=config["lookback_days"])
    previous_source = ""
    interval = float(config.get("request_interval_seconds", 0))
    for source, url in _query_urls(config, as_of):
        if previous_source == source and interval:
            sleep(interval)
        previous_source = source
        request_record = {
            "source": source,
            "query_url": url,
            "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
            "status": "FAILED",
        }
        try:
            payload = fetch(url, int(config.get("timeout_seconds", 30)))
            request_record["response_sha256"] = hashlib.sha256(payload).hexdigest()
            if source == "arxiv":
                parsed = parse_arxiv_atom(payload.decode("utf-8"))
                parsed = [
                    record
                    for record in parsed
                    if cutoff.isoformat()
                    <= (record.get("updated_date") or record.get("publication_date") or "")
                    <= as_of.isoformat()
                ]
            elif source == "crossref":
                parsed = parse_crossref_message(json.loads(payload.decode("utf-8")))
            else:
                parsed = parse_openalex_results(json.loads(payload.decode("utf-8")))
            records.extend(parsed)
            request_record.update(status="OK", records=len(parsed))
            successes += 1
        except (
            OSError, ValueError, TypeError, KeyError, AttributeError,
            ET.ParseError, UnicodeDecodeError, urllib.error.URLError,
        ) as exc:
            request_record["error_type"] = type(exc).__name__
        requests.append(request_record)
    known, known_versions = _known_aliases(ledger)
    discovered = deduplicate(records)
    for record in discovered:
        aliases = set(stable_aliases(record)) | {record["stable_id"]}
        labels = {clean_text(value.get("label", "")) for value in record.get("versions", [])} - {""}
        matched = aliases & known
        prior_labels = set().union(*(known_versions.get(alias, set()) for alias in aliases))
        if not matched:
            status = "NEW_STABLE_ID"
        elif labels - prior_labels:
            status = "POSSIBLE_VERSION_UPDATE"
        else:
            status = "KNOWN_NO_NEW_VERSION_DETECTED"
        record["discovery_status"] = status
        record["review_status"] = "UNVERIFIED_AUTOMATED_DISCOVERY"
        record["automated_topic_matches"] = sorted(
            term for term in config["topic_queries"] if term.casefold() in f"{record.get('title', '')} {record.get('abstract', '')}".casefold()
        )
    snapshot = {
        "schema_version": "personaslm_literature_discovery_snapshot_v1",
        "as_of_date": as_of.isoformat(),
        "lookback_days": config["lookback_days"],
        "config_sha256": sha256_json(config),
        "reviewed_ledger_sha256": sha256_json(ledger),
        "scientific_status": "AUTOMATED_DISCOVERY_ONLY_REQUIRES_PRIMARY_SOURCE_REVIEW",
        "source_request_summary": {
            "attempted": len(requests),
            "succeeded": successes,
            "failed": len(requests) - successes,
            "requests": requests,
        },
        "record_count": len(discovered),
        "records": discovered,
    }
    return snapshot, successes > 0


def command_validate(args: argparse.Namespace) -> int:
    config = json_read(args.config)
    ledger = json_read(args.ledger)
    errors = validate_config(config) + validate_ledger(ledger)
    result = {"config": args.config.as_posix(), "ledger": args.ledger.as_posix(), "errors": errors, "record_count": len(ledger.get("records", []))}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 1 if errors else 0


def command_collect(args: argparse.Namespace) -> int:
    config = json_read(args.config)
    ledger = json_read(args.ledger)
    as_of = date.fromisoformat(args.as_of) if args.as_of else datetime.now(timezone.utc).date()
    snapshot, source_success = make_snapshot(config, ledger, as_of)
    json_write(args.output, snapshot)
    print(json.dumps({"output": args.output.as_posix(), "records": snapshot["record_count"], "source_requests": snapshot["source_request_summary"]}, ensure_ascii=False, sort_keys=True))
    return 0 if source_success else 2


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate the reviewed ledger and monitor config")
    validate.add_argument("--config", type=Path, required=True)
    validate.add_argument("--ledger", type=Path, required=True)
    validate.set_defaults(function=command_validate)
    collect = commands.add_parser("collect", help="write an unreviewed deterministic discovery snapshot")
    collect.add_argument("--config", type=Path, required=True)
    collect.add_argument("--ledger", type=Path, required=True)
    collect.add_argument("--output", type=Path, required=True)
    collect.add_argument("--as-of", help="UTC YYYY-MM-DD; defaults to current UTC date")
    collect.set_defaults(function=command_collect)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return int(args.function(args))


if __name__ == "__main__":
    sys.exit(main())
