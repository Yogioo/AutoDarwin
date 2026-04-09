#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import queue
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path


def load_prompt(prompt_file: Path) -> str:
    if not prompt_file.exists():
        raise FileNotFoundError(f"missing prompt file: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8")


def parse_tools(tools_arg: str | None) -> list[str]:
    if not tools_arg:
        return []
    return [tool.strip() for tool in tools_arg.split(",") if tool.strip()]


def start_pi_process(pi_args: list[str], env: dict[str, str] | None = None) -> subprocess.Popen[str]:
    popen_kwargs = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": sys.stderr,
        "text": True,
        "bufsize": 1,
    }

    try:
        return subprocess.Popen(pi_args, env=env, **popen_kwargs)
    except FileNotFoundError:
        if os.name != "nt":
            raise
        command = subprocess.list2cmdline(pi_args)
        return subprocess.Popen(command, shell=True, env=env, **popen_kwargs)


DEFAULT_MODEL = "openai-codex/gpt-5.4-mini"


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoDarwin pi runner")
    parser.add_argument("--prompt-file", default="autodarwin-prompt.txt", help="Prompt file in the workspace (default: autodarwin-prompt.txt)")
    parser.add_argument("--pi-cmd", default="pi", help="pi command to run (default: pi)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL})")
    parser.add_argument("--thinking", default=None, help="Optional thinking level override")
    parser.add_argument("--tools", default=None, help="Comma-separated tool list, forwarded to pi --tools")
    parser.add_argument("--seed", type=int, default=None, help="Optional deterministic seed (exported to env)")
    parser.add_argument("--timeout", type=int, default=600, help="Overall timeout in seconds")
    args = parser.parse_args()

    prompt = load_prompt(Path(args.prompt_file))
    pi_args = shlex.split(args.pi_cmd) + ["--mode", "rpc", "--no-session"]
    if args.model:
        pi_args += ["--model", args.model]
    if args.thinking:
        pi_args += ["--thinking", args.thinking]

    tools = parse_tools(args.tools)
    if tools:
        pi_args += ["--tools", ",".join(tools)]

    print(f"[runner] pi args: {' '.join(shlex.quote(arg) for arg in pi_args)}", file=sys.stderr)

    child_env = os.environ.copy()
    if args.seed is not None:
        child_env["AUTODARWIN_SEED"] = str(args.seed)
        child_env["PYTHONHASHSEED"] = str(args.seed)

    proc = start_pi_process(pi_args, env=child_env)
    if proc.stdin is None or proc.stdout is None:
        raise RuntimeError("failed to start pi rpc process")

    events: queue.Queue[dict[str, object]] = queue.Queue()

    def reader() -> None:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                events.put(json.loads(line))
            except json.JSONDecodeError:
                continue

    threading.Thread(target=reader, daemon=True).start()

    request_id = f"req-{int(time.time() * 1000)}"
    proc.stdin.write(json.dumps({"id": request_id, "type": "prompt", "message": prompt}) + "\n")
    proc.stdin.flush()

    response_seen = False
    agent_done = False
    deadline = time.time() + args.timeout

    while time.time() < deadline:
        try:
            event = events.get(timeout=0.25)
        except queue.Empty:
            if proc.poll() is not None and not agent_done:
                break
            continue

        event_type = event.get("type")
        if event_type == "response" and event.get("id") == request_id:
            if not event.get("success", False):
                print(json.dumps(event, ensure_ascii=False), file=sys.stderr)
                proc.terminate()
                return 1
            response_seen = True
            continue

        if event_type == "message_update":
            assistant_event = event.get("assistantMessageEvent") or {}
            if isinstance(assistant_event, dict) and assistant_event.get("type") == "text_delta":
                sys.stdout.write(str(assistant_event.get("delta", "")))
                sys.stdout.flush()
            continue

        if event_type == "agent_end":
            agent_done = True
            break

        if event_type == "extension_error":
            print(json.dumps(event, ensure_ascii=False), file=sys.stderr)
            proc.terminate()
            return 1

    if not response_seen:
        print("pi rpc prompt response not received", file=sys.stderr)
        proc.terminate()
        return 1

    if not agent_done:
        print("pi rpc agent did not finish before timeout", file=sys.stderr)
        proc.terminate()
        return 1

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
