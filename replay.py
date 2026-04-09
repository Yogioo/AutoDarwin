#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SYSTEM_PATH = ROOT / ".pi" / "SYSTEM.md"
RESULTS_JSONL_PATH = ROOT / "results.jsonl"
HISTORY_DIR = ROOT / ".autodarwin" / "history"
EVALUATOR = ROOT / "benchmarks" / "evaluator.py"


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"results jsonl not found: {path}")

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def pick_record(records: list[dict[str, Any]], round_id: int | None, candidate_hash: str | None) -> dict[str, Any]:
    if round_id is not None:
        for record in records:
            if int(record.get("round_id", -1)) == round_id:
                return record
        raise ValueError(f"round_id not found: {round_id}")

    if candidate_hash:
        for record in reversed(records):
            if str(record.get("candidate_hash", "")) == candidate_hash:
                return record
        raise ValueError(f"candidate_hash not found: {candidate_hash}")

    raise ValueError("one of --round-id or --candidate-hash is required")


def evaluate_suite(suite: str, agent_cmd: str | None) -> dict[str, Any]:
    cmd = [sys.executable, str(EVALUATOR), suite, "--json"]
    if agent_cmd:
        cmd += ["--agent-cmd", agent_cmd]

    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")

    payload = proc.stdout.strip()
    if not payload:
        raise RuntimeError("empty evaluator output")
    return json.loads(payload)


def status_map(case_results: list[dict[str, Any]]) -> dict[str, str]:
    return {str(item.get("case_id", "")): str(item.get("status", "")) for item in case_results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay a recorded AutoDarwin round")
    parser.add_argument("--results", default=str(RESULTS_JSONL_PATH), help="results.jsonl path")
    parser.add_argument("--round-id", type=int, default=None, help="Round id to replay")
    parser.add_argument("--candidate-hash", default=None, help="Candidate hash to replay")
    parser.add_argument("--suite", default=None, help="Override suite")
    parser.add_argument("--agent-cmd", default=None, help="Optional shell command to replace runner during replay")
    args = parser.parse_args()

    records = load_records(Path(args.results))
    record = pick_record(records, round_id=args.round_id, candidate_hash=args.candidate_hash)

    suite = args.suite or str(record.get("suite", "smoke"))
    hash_value = str(record.get("candidate_hash", ""))
    snapshot = HISTORY_DIR / f"{hash_value}.md"
    if not snapshot.exists():
        raise FileNotFoundError(f"candidate snapshot not found: {snapshot}")

    original_exists = SYSTEM_PATH.exists()
    original_text = SYSTEM_PATH.read_text(encoding="utf-8") if original_exists else ""

    try:
        SYSTEM_PATH.parent.mkdir(parents=True, exist_ok=True)
        SYSTEM_PATH.write_text(snapshot.read_text(encoding="utf-8"), encoding="utf-8")

        replay_summary = evaluate_suite(suite, agent_cmd=args.agent_cmd)

        old_score = float(record.get("candidate_score", 0.0) or 0.0)
        new_score = float(replay_summary.get("pass_rate", 0.0) or 0.0)
        delta = new_score - old_score

        old_map = status_map(list(record.get("case_results", [])))
        new_map = status_map(list(replay_summary.get("case_results", [])))
        changed = []
        for case_id in sorted(set(old_map) | set(new_map)):
            old_status = old_map.get(case_id, "")
            new_status = new_map.get(case_id, "")
            if old_status != new_status:
                changed.append((case_id, old_status, new_status))

        print(f"round_id:        {record.get('round_id')}")
        print(f"candidate_hash:  {hash_value}")
        print(f"suite:           {suite}")
        print(f"recorded_score:  {old_score:.3f}")
        print(f"replay_score:    {new_score:.3f}")
        print(f"delta:           {delta:+.3f}")

        if changed:
            print("changed_cases:")
            for case_id, old_status, new_status in changed:
                print(f"  - {case_id}: {old_status} -> {new_status}")
        else:
            print("changed_cases:   none")

    finally:
        if original_exists:
            SYSTEM_PATH.write_text(original_text, encoding="utf-8")
        elif SYSTEM_PATH.exists():
            SYSTEM_PATH.unlink()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
