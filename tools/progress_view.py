#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any


def clear_screen() -> None:
    print("\x1b[2J\x1b[H", end="")


def load_new_events(path: Path, offset: int) -> tuple[list[dict[str, Any]], int]:
    if not path.exists():
        return [], offset

    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        f.seek(offset)
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
        offset = f.tell()
    return events, offset


def read_case_log_incremental(case: dict[str, Any]) -> None:
    log_path = case.get("log_path")
    if not log_path:
        return

    path = Path(str(log_path))
    if not path.exists():
        return

    current_offset = int(case.get("log_offset", 0))
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(current_offset)
            chunk = f.read()
            case["log_offset"] = f.tell()
    except OSError:
        return

    if not chunk:
        return

    history: list[str] = case.setdefault("history", [])
    for raw in chunk.splitlines():
        line = raw.rstrip()
        if line:
            history.append(line)

    if len(history) > 2000:
        case["history"] = history[-2000:]


def wrap_line(text: str, width: int) -> list[str]:
    if width <= 1:
        return [text[:1]]
    if not text:
        return [""]
    out: list[str] = []
    left = text
    while len(left) > width:
        out.append(left[:width])
        left = left[width:]
    out.append(left)
    return out


def format_case_title(case: dict[str, Any], active: bool) -> str:
    marker = "*" if active else " "
    case_id = str(case.get("case_id", "-"))
    status = str(case.get("status", "queued"))
    stage = str(case.get("stage", ""))
    elapsed = ""
    now = time.time()
    if status == "running" and isinstance(case.get("started_at"), (int, float)):
        elapsed = f" {int(now - float(case['started_at']))}s"
    elif status in {"pass", "fail", "crash"} and case.get("duration_seconds") is not None:
        elapsed = f" {float(case['duration_seconds']):.1f}s"
    stage_text = f"/{stage}" if stage else ""
    return f"[{marker}] {case_id} {status}{stage_text}{elapsed}"


def get_body_lines(case: dict[str, Any], body_h: int, body_w: int) -> list[str]:
    history: list[str] = case.get("history", [])
    if not history:
        chat = str(case.get("chat", "")).strip()
        if chat:
            history = [chat]
        else:
            history = ["(waiting logs/chat...)"]

    wrapped: list[str] = []
    for line in history:
        wrapped.extend(wrap_line(line, max(1, body_w)))

    scroll = int(case.get("scroll", 0))
    total = len(wrapped)
    start = max(0, total - body_h - scroll)
    end = min(total, start + body_h)
    return wrapped[start:end]


def render_multi_column(state: dict[str, Any]) -> None:
    term = shutil.get_terminal_size((140, 40))
    term_w = max(80, term.columns)
    term_h = max(20, term.lines)

    cases_map: dict[str, dict[str, Any]] = state.get("cases", {})
    rows = sorted(cases_map.values(), key=lambda x: x.get("index", 10**9))

    total = int(state.get("total_cases", 0))
    done = sum(1 for v in rows if v.get("status") in {"pass", "fail", "crash"})
    passed = sum(1 for v in rows if v.get("status") == "pass")
    failed = sum(1 for v in rows if v.get("status") == "fail")
    crashed = sum(1 for v in rows if v.get("status") == "crash")
    running = sum(1 for v in rows if v.get("status") == "running")

    clear_screen()
    print("AutoDarwin Live Multi-Panel")
    print(f"suite={state.get('suite', '-')} jobs={state.get('jobs', '-')} done={done}/{total} pass={passed} fail={failed} crash={crashed} running={running}")
    print("keys: ←/→ switch panel | ↑/↓ scroll panel history | PgUp/PgDn faster | Home/End top/bottom | q quit")

    if not rows:
        print("(waiting for cases...)")
        return

    cols = min(len(rows), max(1, term_w // 46))
    pane_w = max(40, term_w // cols)
    body_h = max(6, term_h - 6)

    active_idx = int(state.get("active_index", 0))
    active_idx = max(0, min(active_idx, len(rows) - 1))
    state["active_index"] = active_idx

    # render row by row: each terminal row contains one text line per pane
    pane_buffers: list[list[str]] = []
    for i, case in enumerate(rows):
        title = format_case_title(case, i == active_idx)
        title = title[: pane_w - 1]
        sep = "-" * (pane_w - 1)
        body = get_body_lines(case, body_h, pane_w - 1)
        while len(body) < body_h:
            body.append("")
        pane_lines = [title, sep] + body
        pane_buffers.append(pane_lines)

    pane_rows = len(pane_buffers[0])
    for row_idx in range(pane_rows):
        line_parts: list[str] = []
        for col in range(cols):
            pane_i = (row_idx * 0)  # no-op for clarity
            idx = col
            # map visible column to case index window
            start = (active_idx // cols) * cols
            case_idx = start + idx
            if case_idx >= len(pane_buffers):
                line_parts.append(" " * pane_w)
                continue
            text = pane_buffers[case_idx][row_idx]
            line_parts.append(text.ljust(pane_w))
        print("".join(line_parts)[:term_w])


def _poll_key_windows() -> str | None:
    try:
        import msvcrt  # type: ignore
    except Exception:
        return None

    if not msvcrt.kbhit():
        return None

    ch = msvcrt.getwch()
    if ch in {"\x00", "\xe0"}:
        ch2 = msvcrt.getwch()
        mapping = {
            "K": "left",
            "M": "right",
            "H": "up",
            "P": "down",
            "I": "pgup",
            "Q": "pgdn",
            "G": "home",
            "O": "end",
        }
        return mapping.get(ch2)

    if ch.lower() == "q":
        return "quit"
    return None


def poll_key() -> str | None:
    if os.name == "nt":
        return _poll_key_windows()
    return None


def handle_key(state: dict[str, Any], key: str) -> bool:
    cases = sorted(state.get("cases", {}).values(), key=lambda x: x.get("index", 10**9))
    if not cases:
        return True

    active_idx = int(state.get("active_index", 0))
    active_idx = max(0, min(active_idx, len(cases) - 1))

    if key == "quit":
        return False
    if key == "left":
        state["active_index"] = max(0, active_idx - 1)
        return True
    if key == "right":
        state["active_index"] = min(len(cases) - 1, active_idx + 1)
        return True

    case = cases[active_idx]
    scroll = int(case.get("scroll", 0))
    if key == "up":
        case["scroll"] = scroll + 1
    elif key == "down":
        case["scroll"] = max(0, scroll - 1)
    elif key == "pgup":
        case["scroll"] = scroll + 8
    elif key == "pgdn":
        case["scroll"] = max(0, scroll - 8)
    elif key == "home":
        case["scroll"] = 10**9
    elif key == "end":
        case["scroll"] = 0
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoDarwin progress viewer")
    parser.add_argument("--file", default=".autodarwin/progress.jsonl", help="Progress JSONL file")
    parser.add_argument("--refresh", type=float, default=0.2, help="Refresh interval seconds")
    parser.add_argument("--case-log-dir", default=".autodarwin/case-logs", help="Directory containing per-case log files")
    parser.add_argument("--exit-on-done", action="store_true", help="Auto exit after suite_done event")
    parser.add_argument("--done-grace", type=float, default=1.0, help="Seconds to wait before exit when --exit-on-done")
    args = parser.parse_args()

    path = Path(args.file)
    case_log_dir = Path(args.case_log_dir)
    offset = 0
    state: dict[str, Any] = {"cases": {}, "suite": "-", "jobs": "-", "total_cases": 0, "active_index": 0}
    suite_done_at: float | None = None

    try:
        while True:
            events, offset = load_new_events(path, offset)
            for event in events:
                event_type = event.get("type")
                if event_type == "suite_start":
                    state["suite"] = event.get("suite", "-")
                    state["jobs"] = event.get("jobs", "-")
                    state["total_cases"] = event.get("total_cases", 0)
                    state["cases"] = {}
                    state["suite_done"] = False
                    state["active_index"] = 0
                    suite_done_at = None
                    continue

                if event_type == "case_start":
                    case_id = str(event.get("case_id", ""))
                    state["cases"][case_id] = {
                        "index": event.get("index"),
                        "case_id": case_id,
                        "status": "running",
                        "stage": "agent",
                        "started_at": event.get("ts", time.time()),
                        "history": [],
                        "log_path": str(case_log_dir / f"{case_id}.log"),
                        "log_offset": 0,
                        "scroll": 0,
                    }
                    continue

                if event_type == "case_stage":
                    case_id = str(event.get("case_id", ""))
                    existing = state["cases"].get(case_id, {"case_id": case_id, "history": [], "scroll": 0})
                    existing["stage"] = event.get("stage")
                    if existing.get("status") not in {"pass", "fail", "crash"}:
                        existing["status"] = "running"
                    state["cases"][case_id] = existing
                    continue

                if event_type == "case_chat":
                    case_id = str(event.get("case_id", ""))
                    existing = state["cases"].get(case_id, {"case_id": case_id, "history": [], "scroll": 0})
                    text = str(event.get("text", "")).strip()
                    if text:
                        history = existing.setdefault("history", [])
                        history.append(text)
                        if len(history) > 2000:
                            existing["history"] = history[-2000:]
                    existing["chat"] = text[-120:] if text else ""
                    if existing.get("status") not in {"pass", "fail", "crash"}:
                        existing["status"] = "running"
                    state["cases"][case_id] = existing
                    continue

                if event_type == "case_done":
                    case_id = str(event.get("case_id", ""))
                    existing = state["cases"].get(case_id, {"index": event.get("index"), "case_id": case_id, "history": [], "scroll": 0})
                    existing["status"] = event.get("status", "unknown")
                    existing["reason"] = event.get("reason")
                    existing["duration_seconds"] = event.get("duration_seconds")
                    lp = event.get("log_path")
                    if lp:
                        existing["log_path"] = lp
                    elif not existing.get("log_path"):
                        existing["log_path"] = str(case_log_dir / f"{case_id}.log")
                    state["cases"][case_id] = existing
                    continue

                if event_type == "suite_done":
                    state["suite_done"] = True
                    suite_done_at = event.get("ts", time.time())

            for case in state.get("cases", {}).values():
                read_case_log_incremental(case)

            render_multi_column(state)

            key = poll_key()
            if key is not None:
                if not handle_key(state, key):
                    return 0

            if args.exit_on_done and state.get("suite_done") and suite_done_at is not None:
                if time.time() - float(suite_done_at) >= max(0.1, args.done_grace):
                    return 0

            time.sleep(max(0.05, args.refresh))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
