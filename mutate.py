#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


DEFAULT_MODEL = "openai-codex/gpt-5.4-mini"


def mutate_text(current: str, pi_cmd: str, model: str | None = DEFAULT_MODEL, seed: int | None = None) -> str:
    prompt = (
        "Rewrite the following AutoDarwin system prompt. "
        "Make one small improvement only. "
        "Keep it short, strict, and minimal. "
        "Return only the full markdown, no explanation."
    )
    env = os.environ.copy()
    if seed is not None:
        env["AUTODARWIN_SEED"] = str(seed)
        env["PYTHONHASHSEED"] = str(seed)

    cmd = [*shlex.split(pi_cmd), "--no-session"]
    if model:
        cmd += ["--model", model]
    cmd += ["-p", prompt]

    proc = subprocess.run(
        cmd,
        input=current,
        text=True,
        capture_output=True,
        env=env,
    )
    if proc.returncode != 0:
        return current
    text = proc.stdout.strip()
    return text or current


def main() -> int:
    parser = argparse.ArgumentParser(description="Mutate AutoDarwin system prompt")
    parser.add_argument("path", nargs="?", default=".pi/SYSTEM.md", help="Prompt path")
    parser.add_argument("--pi-cmd", default="pi", help="pi command")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL})")
    parser.add_argument("--seed", type=int, default=None, help="Optional deterministic seed")
    args = parser.parse_args()

    path = Path(args.path)
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    mutated = mutate_text(current, args.pi_cmd, model=args.model, seed=args.seed)
    sys.stdout.write(mutated)
    if not mutated.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
