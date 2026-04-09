#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
from pathlib import Path


def default_jobs_for_suite(suite: str) -> int:
    return 2 if suite == "smoke" else 4


def pick_port(preferred: int) -> int:
    for port in [preferred, preferred + 1, preferred + 2, preferred + 3, preferred + 4]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    return preferred


def start_viewer(progress_file: Path, case_log_dir: Path, python_cmd: str, ui_mode: str, stay_open: bool, ui_port: int) -> subprocess.Popen[str] | None:
    if ui_mode == "web":
        viewer_script = Path(__file__).with_name("progress_web.py")
        viewer_cmd = [
            python_cmd,
            str(viewer_script),
            "--file",
            str(progress_file),
            "--case-log-dir",
            str(case_log_dir),
            "--port",
            str(ui_port),
            "--open-browser",
        ]
    else:
        viewer_script = Path(__file__).with_name("progress_view.py")
        viewer_cmd = [python_cmd, str(viewer_script), "--file", str(progress_file), "--case-log-dir", str(case_log_dir)]
        if not stay_open:
            viewer_cmd += ["--exit-on-done", "--done-grace", "1.5"]

    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        return subprocess.Popen(viewer_cmd, creationflags=creationflags)

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run evaluator with external live UI")
    parser.add_argument("suite", nargs="?", default="core", help="Suite name (default: core)")
    parser.add_argument("--jobs", type=int, default=None, help="Parallel jobs (default: smoke=2, others=4)")
    parser.add_argument("--progress-file", default=".autodarwin/progress.jsonl", help="Progress JSONL path")
    parser.add_argument("--case-log-dir", default=".autodarwin/case-logs", help="Directory for per-case logs")
    parser.add_argument("--python-cmd", default=sys.executable, help="Python command for child processes")
    parser.add_argument("--ui", choices=["web", "text"], default="web", help="UI mode (default: web)")
    parser.add_argument("--ui-port", type=int, default=8765, help="Web UI port (default: 8765)")
    parser.add_argument("--stay-viewer", action="store_true", help="Keep viewer open after suite done")
    args, extra = parser.parse_known_args()

    progress_file = Path(args.progress_file)
    jobs = args.jobs if args.jobs is not None else default_jobs_for_suite(args.suite)

    case_log_dir = Path(args.case_log_dir)
    ui_port = pick_port(args.ui_port) if args.ui == "web" else args.ui_port
    viewer_proc = start_viewer(progress_file, case_log_dir, args.python_cmd, args.ui, args.stay_viewer, ui_port)

    evaluator = [
        args.python_cmd,
        str(Path("benchmarks") / "evaluator.py"),
        args.suite,
        "--jobs",
        str(jobs),
        "--progress",
        "off",
        "--progress-file",
        str(progress_file),
        "--case-log-dir",
        str(case_log_dir),
    ] + extra

    if viewer_proc is None:
        print("[ui] viewer window auto-open is Windows-only; running evaluator directly.")
        print(f"[ui] manual web ui: {args.python_cmd} tools/progress_web.py --file {progress_file} --case-log-dir {case_log_dir} --port {ui_port} --open-browser")
    else:
        if args.ui == "web":
            print(f"[ui] opened web viewer: http://127.0.0.1:{ui_port}/")
        else:
            print(f"[ui] opened text viewer: {progress_file}")

    return subprocess.call(evaluator)


if __name__ == "__main__":
    raise SystemExit(main())
