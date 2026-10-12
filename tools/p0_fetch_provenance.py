"""Fetch small public publisher metadata only; never downloads model weights."""
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

from personaslm.journal import atomic_json, utc_now


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    repo = "aashish1904/Qwen3.5-2B-Base-GGUF"
    revision = "765d2baaa04dbb8d6df3e78af571e6beaa4373d7"
    urls = [f"https://huggingface.co/api/models/{repo}/tree/{revision}",
            f"https://huggingface.co/{repo}/raw/{revision}/README.md"]
    responses = []
    for url in urls:
        record = {"url": url, "started_utc": utc_now()}
        try:
            with urlopen(Request(url, headers={"User-Agent": "PersonaSLM-P0-provenance-audit"}), timeout=20) as response:
                body = response.read(2_000_001)
                if len(body) > 2_000_000:
                    raise ValueError("Metadata response exceeds size limit")
                record.update(status=response.status, body=body.decode("utf-8"), final_url=response.url)
        except Exception as exc:
            record.update(error_type=type(exc).__name__, error=str(exc))
        record["finished_utc"] = utc_now()
        responses.append(record)
        if "error" in record:
            break
    atomic_json(args.output, {"responses": responses})
    print(json.dumps(responses, ensure_ascii=True))
    raise SystemExit(2 if any("error" in r for r in responses) else 0)


if __name__ == "__main__":
    main()
