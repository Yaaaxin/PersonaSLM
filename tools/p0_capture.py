"""Capture an actual command once, with immutable output and wall-clock timing."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time

from personaslm.journal import atomic_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if args.output.exists():
        raise FileExistsError(args.output)
    started = datetime.now(timezone.utc).isoformat()
    tick = time.perf_counter()
    result = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace")
    record = {"started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
              "argv": command, "exit_code": result.returncode, "duration_seconds": time.perf_counter()-tick,
              "stdout": result.stdout, "stderr": result.stderr}
    atomic_json(args.output, record)
    print(json.dumps(record, ensure_ascii=True, indent=2))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
