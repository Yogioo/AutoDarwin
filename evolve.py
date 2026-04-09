#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from mutate import mutate_text


ROOT = Path(__file__).resolve().parent
SYSTEM_PATH = ROOT / ".pi" / "SYSTEM.md"
RESULTS_PATH = ROOT / "results.tsv"
RESULTS_JSONL_PATH = ROOT / "results.jsonl"
HISTORY_DIR = ROOT / ".autodarwin" / "history"
EVALUATOR = ROOT / "benchmarks" / "evaluator.py"


def default_summary(suite: str) -> dict[str, Any]:
    return {
        "suite": suite,
        "total_cases": 0,
        "passed": 0,
        "failed": 0,
        "crashed": 0,
        "pass_rate": 0.0,
        "avg_duration": 0.0,
        "suite_seconds": 0.0,
        "case_results": [],
    }


def score_suite(suite: str, agent_cmd: str | None = None, seed: int | None = None) -> dict[str, Any]:
    cmd = [sys.executable, str(EVALUATOR), suite, "--json"]
    if agent_cmd is not None:
        cmd += ["--agent-cmd", agent_cmd]
    if seed is not None:
        cmd += ["--seed", str(seed)]

    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")

    payload = proc.stdout.strip()
    if not payload:
        return default_summary(suite)

    try:
        summary = json.loads(payload)
    except json.JSONDecodeError:
        return default_summary(suite)

    if not isinstance(summary, dict):
        return default_summary(suite)
    return summary


def simplify_case_results(case_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    simplified: list[dict[str, Any]] = []
    for case in case_results:
        simplified.append(
            {
                "case_id": case.get("case_id", ""),
                "status": case.get("status", "crash"),
                "duration": float(case.get("duration_seconds", 0.0) or 0.0),
                "reason": case.get("reason", ""),
            }
        )
    return simplified


def evaluate_with_repeats(suite: str, repeats: int, agent_cmd: str | None = None, seed: int | None = None) -> dict[str, Any]:
    repeat_count = max(1, repeats)
    runs: list[dict[str, Any]] = []
    for i in range(repeat_count):
        run_seed = seed + i if seed is not None else None
        runs.append(score_suite(suite, agent_cmd=agent_cmd, seed=run_seed))

    pass_rates = [float(run.get("pass_rate", 0.0) or 0.0) for run in runs]
    durations = [float(run.get("avg_duration", 0.0) or 0.0) for run in runs]

    return {
        "runs": runs,
        "mean_pass_rate": mean(pass_rates),
        "std_pass_rate": pstdev(pass_rates) if len(pass_rates) > 1 else 0.0,
        "mean_avg_duration": mean(durations),
        "std_avg_duration": pstdev(durations) if len(durations) > 1 else 0.0,
        "case_results": simplify_case_results(runs[-1].get("case_results", [])) if runs else [],
    }


def append_result(round_id: int, baseline: float, candidate: float, status: str, description: str) -> None:
    if not RESULTS_PATH.exists():
        RESULTS_PATH.write_text("round\tbaseline\tcandidate\tstatus\tdescription\n", encoding="utf-8")
    with RESULTS_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{round_id}\t{baseline:.3f}\t{candidate:.3f}\t{status}\t{description}\n")


def append_result_jsonl(entry: dict[str, Any]) -> None:
    with RESULTS_JSONL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def snapshot_prompt(text: str) -> str:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    digest = prompt_hash(text)
    snapshot = HISTORY_DIR / f"{digest}.md"
    if not snapshot.exists():
        snapshot.write_text(text, encoding="utf-8")
    return digest


def build_mutation_diff_summary(before: str, after: str, max_preview_lines: int = 40) -> dict[str, Any]:
    if before == after:
        return {
            "changed": False,
            "added_lines": 0,
            "removed_lines": 0,
            "preview": [],
        }

    diff_lines = list(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile="before",
            tofile="after",
            lineterm="",
        )
    )

    added_lines = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    removed_lines = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))

    return {
        "changed": True,
        "added_lines": added_lines,
        "removed_lines": removed_lines,
        "preview": diff_lines[:max_preview_lines],
    }


def maybe_run_holdout(
    round_id: int,
    holdout_suite: str | None,
    holdout_every: int,
    repeats: int,
    agent_cmd: str | None,
    seed: int | None = None,
) -> dict[str, Any] | None:
    if not holdout_suite:
        return None
    if holdout_every <= 0:
        return None
    if round_id % holdout_every != 0:
        return None

    holdout_eval = evaluate_with_repeats(holdout_suite, repeats=repeats, agent_cmd=agent_cmd, seed=seed)
    mean_score = float(holdout_eval["mean_pass_rate"])
    std_score = float(holdout_eval["std_pass_rate"])
    print(f"round {round_id}: holdout {holdout_suite}={mean_score:.3f}±{std_score:.3f}")

    return {
        "suite": holdout_suite,
        "mean": mean_score,
        "std": std_score,
        "avg_duration": float(holdout_eval["mean_avg_duration"]),
        "seed": seed,
        "reason_counts": holdout_eval["runs"][-1].get("reason_counts", {}) if holdout_eval["runs"] else {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoDarwin evolve loop")
    parser.add_argument("--suite", default="smoke", help="Benchmark suite")
    parser.add_argument("--pi-cmd", default="pi", help="pi command for mutation")
    parser.add_argument("--agent-cmd", default=None, help="Optional shell command to replace runner during evaluation")
    parser.add_argument("--rounds", type=int, default=1, help="Number of rounds")
    parser.add_argument("--repeats", type=int, default=1, help="Repeated evaluations per baseline/candidate")
    parser.add_argument("--margin", type=float, default=0.0, help="Keep only when candidate_mean > baseline_mean + margin")
    parser.add_argument("--seed", type=int, default=None, help="Optional deterministic seed")
    parser.add_argument("--holdout-suite", default=None, help="Optional holdout suite for staged validation")
    parser.add_argument("--holdout-every", type=int, default=0, help="Run holdout every N rounds (0 to disable)")
    args = parser.parse_args()

    SYSTEM_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SYSTEM_PATH.exists():
        SYSTEM_PATH.write_text(
            "你是 AutoDarwin 的极简 coding agent。\n\n原则：\n- 先读再改\n- 只做必要修改\n- 改完就验证\n- 输出保持简洁\n- 不要为了看起来聪明而增加复杂度\n",
            encoding="utf-8",
        )

    for round_id in range(1, args.rounds + 1):
        baseline_text = SYSTEM_PATH.read_text(encoding="utf-8")
        parent_hash = snapshot_prompt(baseline_text)

        round_seed = args.seed + (round_id - 1) * 1000 if args.seed is not None else None
        mutation_seed = round_seed + 999 if round_seed is not None else None

        baseline_eval = evaluate_with_repeats(args.suite, repeats=args.repeats, agent_cmd=args.agent_cmd, seed=round_seed)
        baseline_score = float(baseline_eval["mean_pass_rate"])

        candidate_text = mutate_text(baseline_text, args.pi_cmd, seed=mutation_seed)
        candidate_hash = snapshot_prompt(candidate_text)
        mutation_diff = build_mutation_diff_summary(baseline_text, candidate_text)

        if candidate_text == baseline_text:
            status = "discard"
            candidate_score = baseline_score
            candidate_eval = baseline_eval
            decision_reason = "no_mutation"
            holdout_result = maybe_run_holdout(
                round_id,
                holdout_suite=args.holdout_suite,
                holdout_every=args.holdout_every,
                repeats=args.repeats,
                agent_cmd=args.agent_cmd,
                seed=(round_seed + 500 if round_seed is not None else None),
            )
            append_result(round_id, baseline_score, candidate_score, status, decision_reason)
            record = {
                "round_id": round_id,
                "suite": args.suite,
                "baseline_score": baseline_score,
                "candidate_score": candidate_score,
                "status": status,
                "parent_hash": parent_hash,
                "candidate_hash": candidate_hash,
                "case_results": candidate_eval["case_results"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "baseline_mean": baseline_eval["mean_pass_rate"],
                "baseline_std": baseline_eval["std_pass_rate"],
                "candidate_mean": candidate_eval["mean_pass_rate"],
                "candidate_std": candidate_eval["std_pass_rate"],
                "baseline_avg_duration": baseline_eval["mean_avg_duration"],
                "candidate_avg_duration": candidate_eval["mean_avg_duration"],
                "margin": args.margin,
                "seed": args.seed,
                "round_seed": round_seed,
                "mutation_seed": mutation_seed,
                "decision_reason": decision_reason,
                "mutation_diff": mutation_diff,
            }
            if holdout_result is not None:
                record["holdout"] = holdout_result
            append_result_jsonl(record)
            print(f"round {round_id}: no mutation")
            continue

        SYSTEM_PATH.write_text(candidate_text, encoding="utf-8")
        candidate_eval = evaluate_with_repeats(args.suite, repeats=args.repeats, agent_cmd=args.agent_cmd, seed=round_seed)
        candidate_score = float(candidate_eval["mean_pass_rate"])

        baseline_duration = float(baseline_eval["mean_avg_duration"])
        candidate_duration = float(candidate_eval["mean_avg_duration"])

        keep_candidate = False
        decision_reason = "not_better"
        if candidate_score > baseline_score + args.margin:
            keep_candidate = True
            decision_reason = "higher_pass_rate"
        elif abs(candidate_score - baseline_score) <= 1e-12 and candidate_duration < baseline_duration:
            keep_candidate = True
            decision_reason = "tie_break_avg_duration"

        if keep_candidate:
            status = "keep"
            append_result(round_id, baseline_score, candidate_score, status, decision_reason)
            print(
                f"round {round_id}: keep "
                f"(base={baseline_score:.3f}±{baseline_eval['std_pass_rate']:.3f}, "
                f"cand={candidate_score:.3f}±{candidate_eval['std_pass_rate']:.3f}, "
                f"base_dur={baseline_duration:.3f}, cand_dur={candidate_duration:.3f})"
            )
        else:
            SYSTEM_PATH.write_text(baseline_text, encoding="utf-8")
            status = "discard"
            append_result(round_id, baseline_score, candidate_score, status, decision_reason)
            print(
                f"round {round_id}: discard "
                f"(base={baseline_score:.3f}±{baseline_eval['std_pass_rate']:.3f}, "
                f"cand={candidate_score:.3f}±{candidate_eval['std_pass_rate']:.3f}, "
                f"base_dur={baseline_duration:.3f}, cand_dur={candidate_duration:.3f})"
            )

        holdout_result = maybe_run_holdout(
            round_id,
            holdout_suite=args.holdout_suite,
            holdout_every=args.holdout_every,
            repeats=args.repeats,
            agent_cmd=args.agent_cmd,
            seed=(round_seed + 500 if round_seed is not None else None),
        )

        record = {
            "round_id": round_id,
            "suite": args.suite,
            "baseline_score": baseline_score,
            "candidate_score": candidate_score,
            "status": status,
            "parent_hash": parent_hash,
            "candidate_hash": candidate_hash,
            "case_results": candidate_eval["case_results"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "baseline_mean": baseline_eval["mean_pass_rate"],
            "baseline_std": baseline_eval["std_pass_rate"],
            "candidate_mean": candidate_eval["mean_pass_rate"],
            "candidate_std": candidate_eval["std_pass_rate"],
            "baseline_avg_duration": baseline_duration,
            "candidate_avg_duration": candidate_duration,
            "margin": args.margin,
            "seed": args.seed,
            "round_seed": round_seed,
            "mutation_seed": mutation_seed,
            "decision_reason": decision_reason,
            "mutation_diff": mutation_diff,
        }
        if holdout_result is not None:
            record["holdout"] = holdout_result
        append_result_jsonl(record)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
