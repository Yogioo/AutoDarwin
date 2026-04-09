from __future__ import annotations

import argparse
import difflib
import fnmatch
import json
import os
import queue
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CASES_DIR = ROOT / "cases"
SUITES_DIR = ROOT / "suites"

DIFF_IGNORE_FILES = {
    "autodarwin-case.json",
    "autodarwin-prompt.txt",
    ".pi/SYSTEM.md",
}
DIFF_IGNORE_DIRS = {"__pycache__", ".pytest_cache", ".git", ".svn"}


def to_bash_path(path: Path) -> str:
    resolved = path.resolve()
    if resolved.drive:
        drive = resolved.drive.rstrip(":").lower()
        return "/mnt/" + drive + "/" + "/".join(resolved.parts[1:])
    return str(resolved)


@dataclass
class CaseResult:
    case_id: str
    name: str
    status: str
    duration_seconds: float
    agent_returncode: int | None = None
    check_returncode: int | None = None
    message: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "name": self.name,
            "status": self.status,
            "duration_seconds": round(self.duration_seconds, 6),
            "agent_returncode": self.agent_returncode,
            "check_returncode": self.check_returncode,
            "message": self.message,
            "reason": self.reason,
        }


def load_case(case_dir: Path) -> dict[str, Any]:
    case_path = case_dir / "case.json"
    if not case_path.exists():
        raise FileNotFoundError(f"missing case.json: {case_path}")
    return json.loads(case_path.read_text(encoding="utf-8"))


def load_suite(suite: str) -> list[str]:
    suite_path = Path(suite)
    if not suite_path.exists():
        if not suite.endswith(".txt"):
            suite_path = SUITES_DIR / f"{suite}.txt"
    if not suite_path.exists():
        raise FileNotFoundError(f"suite not found: {suite}")

    case_ids: list[str] = []
    for line in suite_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        case_ids.append(line)
    return case_ids


def parse_tools(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [tool.strip() for tool in value.split(",") if tool.strip()]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                result.append(text)
        return result
    return []


def normalize_relpath(value: str) -> str:
    normalized = value.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    while normalized.startswith("/"):
        normalized = normalized[1:]
    return normalized


def should_ignore_for_diff(rel_path: str) -> bool:
    if rel_path in DIFF_IGNORE_FILES:
        return True
    parts = Path(rel_path).parts
    return any(part in DIFF_IGNORE_DIRS for part in parts)


def snapshot_workspace_files(root: Path) -> dict[str, bytes]:
    snapshot: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_path = normalize_relpath(path.relative_to(root).as_posix())
        if should_ignore_for_diff(rel_path):
            continue
        snapshot[rel_path] = path.read_bytes()
    return snapshot


def detect_changed_files(before: dict[str, bytes], after: dict[str, bytes]) -> list[str]:
    changed: list[str] = []
    for rel_path in sorted(set(before) | set(after)):
        if before.get(rel_path) != after.get(rel_path):
            changed.append(rel_path)
    return changed


def count_changed_lines(before: dict[str, bytes], after: dict[str, bytes], changed_files: list[str]) -> int:
    total = 0
    for rel_path in changed_files:
        before_bytes = before.get(rel_path)
        after_bytes = after.get(rel_path)

        if before_bytes is None and after_bytes is not None:
            total += max(1, len(after_bytes.decode("utf-8", errors="replace").splitlines()))
            continue
        if after_bytes is None and before_bytes is not None:
            total += max(1, len(before_bytes.decode("utf-8", errors="replace").splitlines()))
            continue

        before_lines = (before_bytes or b"").decode("utf-8", errors="replace").splitlines()
        after_lines = (after_bytes or b"").decode("utf-8", errors="replace").splitlines()
        for line in difflib.ndiff(before_lines, after_lines):
            if line.startswith("+ ") or line.startswith("- "):
                total += 1

    return total


def match_path_rule(path: str, rule: str) -> bool:
    norm_rule = normalize_relpath(rule)
    if not norm_rule:
        return False
    if norm_rule.endswith("/"):
        return path.startswith(norm_rule)
    return path == norm_rule or path.startswith(norm_rule + "/")


def match_glob_rule(path: str, rule: str) -> bool:
    norm_rule = normalize_relpath(rule)
    if not norm_rule:
        return False
    return fnmatch.fnmatch(path, norm_rule)


def evaluate_constraints(changed_files: list[str], changed_lines: int, constraints: Any) -> list[str]:
    if not isinstance(constraints, dict):
        return []

    violations: list[str] = []

    max_changed_files = constraints.get("max_changed_files")
    if isinstance(max_changed_files, int) and max_changed_files >= 0 and len(changed_files) > max_changed_files:
        violations.append(f"changed_files={len(changed_files)} exceeds max_changed_files={max_changed_files}")

    max_changed_lines = constraints.get("max_changed_lines")
    if isinstance(max_changed_lines, int) and max_changed_lines >= 0 and changed_lines > max_changed_lines:
        violations.append(f"changed_lines={changed_lines} exceeds max_changed_lines={max_changed_lines}")

    forbid_paths = constraints.get("forbid_paths") if isinstance(constraints.get("forbid_paths"), list) else []
    forbid_globs = constraints.get("forbid_globs") if isinstance(constraints.get("forbid_globs"), list) else []
    for changed in changed_files:
        if any(match_path_rule(changed, str(rule)) for rule in forbid_paths):
            violations.append(f"forbidden path changed: {changed}")
            continue
        if any(match_glob_rule(changed, str(rule)) for rule in forbid_globs):
            violations.append(f"forbidden glob matched: {changed}")

    allow_paths = constraints.get("allow_paths") if isinstance(constraints.get("allow_paths"), list) else []
    allow_globs = constraints.get("allow_globs") if isinstance(constraints.get("allow_globs"), list) else []
    if allow_paths or allow_globs:
        for changed in changed_files:
            if any(match_path_rule(changed, str(rule)) for rule in allow_paths):
                continue
            if any(match_glob_rule(changed, str(rule)) for rule in allow_globs):
                continue
            violations.append(f"path outside allow rules: {changed}")

    return violations


def copy_workspace(case_dir: Path, workspace_name: str) -> Path:
    src = case_dir / workspace_name
    if not src.exists():
        raise FileNotFoundError(f"missing workspace: {src}")
    temp_dir = Path(tempfile.mkdtemp(prefix=f"autodarwin-{case_dir.name}-"))
    shutil.copytree(src, temp_dir, dirs_exist_ok=True)
    return temp_dir


def run_shell(command: str, cwd: Path, env: dict[str, str], timeout: int | None = None) -> subprocess.CompletedProcess[bytes]:
    full_command = f"cd {shlex.quote(to_bash_path(cwd))} && {command}"
    return subprocess.run(
        ["bash", "-c", full_command],
        cwd=str(cwd.resolve()),
        env=env,
        capture_output=True,
        timeout=timeout,
    )


def run_script_check(script_path: Path, cwd: Path, env: dict[str, str], timeout: int | None = None) -> subprocess.CompletedProcess[bytes]:
    suffix = script_path.suffix.lower()
    if suffix in {".bat", ".cmd"}:
        return subprocess.run(
            ["cmd.exe", "/c", str(script_path.resolve())],
            cwd=str(cwd.resolve()),
            env=env,
            capture_output=True,
            timeout=timeout,
        )

    full_command = f"cd {shlex.quote(to_bash_path(cwd))} && bash {shlex.quote(to_bash_path(script_path))}"
    return subprocess.run(
        ["bash", "-c", full_command],
        cwd=str(cwd.resolve()),
        env=env,
        capture_output=True,
        timeout=timeout,
    )


def run_subprocess_with_chat_stream(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
    timeout: int | None,
    case_id: str,
    progress_file: Path | None,
) -> subprocess.CompletedProcess[bytes]:
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd.resolve()),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    q: queue.Queue[tuple[str, str]] = queue.Queue()

    def reader(stream: Any, kind: str) -> None:
        try:
            while True:
                chunk = stream.read(1)
                if not chunk:
                    break
                q.put((kind, chunk))
        finally:
            q.put((kind, ""))

    if proc.stdout is None or proc.stderr is None:
        raise RuntimeError("failed to start subprocess with pipes")

    t_out = threading.Thread(target=reader, args=(proc.stdout, "stdout"), daemon=True)
    t_err = threading.Thread(target=reader, args=(proc.stderr, "stderr"), daemon=True)
    t_out.start()
    t_err.start()

    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    preview = ""
    done_streams: set[str] = set()
    start = time.perf_counter()
    last_emit = 0.0

    while True:
        if timeout is not None and (time.perf_counter() - start) > timeout:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
            raise subprocess.TimeoutExpired(cmd, timeout)

        try:
            kind, chunk = q.get(timeout=0.1)
            if chunk == "":
                done_streams.add(kind)
            elif kind == "stdout":
                stdout_parts.append(chunk)
                preview = (preview + chunk)[-160:]
            else:
                stderr_parts.append(chunk)
        except queue.Empty:
            pass

        now = time.perf_counter()
        if now - last_emit >= 0.8 and preview.strip():
            emit_progress_event(
                progress_file,
                {
                    "type": "case_chat",
                    "case_id": case_id,
                    "text": preview.replace("\n", " ")[-120:],
                },
            )
            last_emit = now

        if proc.poll() is not None and done_streams == {"stdout", "stderr"} and q.empty():
            break

    return subprocess.CompletedProcess(
        args=cmd,
        returncode=proc.returncode if proc.returncode is not None else 1,
        stdout="".join(stdout_parts).encode("utf-8", errors="replace"),
        stderr="".join(stderr_parts).encode("utf-8", errors="replace"),
    )


def run_case_check(case: dict[str, Any], case_dir: Path, cwd: Path, env: dict[str, str], timeout: int | None = None) -> subprocess.CompletedProcess[bytes]:
    check = case.get("check", {})
    check_type = str(check.get("type", "script")).strip().lower() or "script"

    if check_type == "script":
        script_rel = check.get("path", "check.sh")
        script_path = case_dir / script_rel
        if not script_path.exists():
            raise FileNotFoundError(f"missing check script: {script_path}")
        return run_script_check(script_path, cwd=cwd, env=env, timeout=timeout)

    if check_type == "command":
        command = str(check.get("command", "")).strip()
        if not command:
            raise ValueError("check.command is required when check.type=command")
        return run_shell(command, cwd=cwd, env=env, timeout=timeout)

    raise ValueError(f"unsupported check.type: {check_type}")


def print_completed_process_output(proc: subprocess.CompletedProcess[bytes]) -> None:
    if proc.stdout:
        print(proc.stdout.decode("utf-8", errors="replace"), end="")
    if proc.stderr:
        print(proc.stderr.decode("utf-8", errors="replace"), end="", file=sys.stderr)


def append_case_log(log_path: Path | None, title: str, proc: subprocess.CompletedProcess[bytes] | None = None) -> None:
    if log_path is None:
        return
    parts = [f"\n==== {title} ====\n"]
    if proc is not None:
        parts.append(f"returncode: {proc.returncode}\n")
        stdout = (proc.stdout or b"").decode("utf-8", errors="replace")
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace")
        if stdout:
            parts.append("[stdout]\n")
            parts.append(stdout)
            if not stdout.endswith("\n"):
                parts.append("\n")
        if stderr:
            parts.append("[stderr]\n")
            parts.append(stderr)
            if not stderr.endswith("\n"):
                parts.append("\n")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write("".join(parts))


def classify_agent_failure(returncode: int | None, stderr: bytes | None) -> str:
    text = (stderr or b"").decode("utf-8", errors="replace").lower()
    if returncode in {127, 9009}:
        return "agent_command_not_found"
    if "prompt response not received" in text:
        return "agent_protocol_error"
    if "did not finish before timeout" in text:
        return "agent_timeout"
    return "agent_failed"


def classify_check_failure(returncode: int | None, stderr: bytes | None) -> str:
    if returncode in {127, 9009}:
        return "check_command_not_found"
    return "check_failed"


def execute_case(
    case_dir: Path,
    agent_cmd: str | None,
    keep_temp: bool = False,
    verbose: bool = True,
    seed: int | None = None,
    progress_file: Path | None = None,
    case_log_dir: Path | None = None,
) -> CaseResult:
    case = load_case(case_dir)
    case_id = case["id"]
    name = case.get("name", case_id)
    max_seconds = int(case.get("max_seconds", 90))
    log_path = (case_log_dir / f"{case_id}.log") if case_log_dir is not None else None
    workspace_name = str(case.get("workspace", "workspace"))
    constraints = case.get("constraints")

    temp_workspace = copy_workspace(case_dir, workspace_name)
    baseline_snapshot = snapshot_workspace_files(temp_workspace)
    start = time.perf_counter()

    env = os.environ.copy()
    if seed is not None:
        env["AUTODARWIN_SEED"] = str(seed)
        env["PYTHONHASHSEED"] = str(seed)

    (temp_workspace / "autodarwin-case.json").write_text(
        json.dumps(case, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (temp_workspace / "autodarwin-prompt.txt").write_text(
        case.get("prompt", ""),
        encoding="utf-8",
    )

    root_system = ROOT.parent / ".pi" / "SYSTEM.md"
    if root_system.exists():
        target = temp_workspace / ".pi" / "SYSTEM.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root_system, target)

    try:
        stage = "agent"
        agent_returncode: int | None = None
        emit_progress_event(progress_file, {"type": "case_stage", "case_id": case_id, "stage": "agent"})
        if agent_cmd is None:
            runner = (ROOT.parent / "runner.py").resolve()
            runner_cmd = [sys.executable, str(runner), "--timeout", str(max_seconds)]
            tools = parse_tools(case.get("tools"))
            if tools:
                runner_cmd += ["--tools", ",".join(tools)]
            if seed is not None:
                runner_cmd += ["--seed", str(seed)]
            agent_proc = run_subprocess_with_chat_stream(
                runner_cmd,
                cwd=temp_workspace,
                env=env,
                timeout=max_seconds,
                case_id=case_id,
                progress_file=progress_file,
            )
            agent_returncode = agent_proc.returncode
            append_case_log(log_path, "agent", agent_proc)
            tail_text = (agent_proc.stdout or b"").decode("utf-8", errors="replace").replace("\n", " ")[-120:]
            if tail_text.strip():
                emit_progress_event(progress_file, {"type": "case_chat", "case_id": case_id, "text": tail_text})
            emit_progress_event(progress_file, {"type": "case_stage", "case_id": case_id, "stage": "agent_done", "returncode": agent_returncode})
            if verbose:
                print_completed_process_output(agent_proc)
            if agent_proc.returncode != 0:
                duration = time.perf_counter() - start
                return CaseResult(
                    case_id=case_id,
                    name=name,
                    status="crash",
                    duration_seconds=duration,
                    agent_returncode=agent_proc.returncode,
                    message="agent command failed",
                    reason=classify_agent_failure(agent_proc.returncode, agent_proc.stderr),
                )
        else:
            agent_proc = run_shell(agent_cmd, cwd=temp_workspace, env=env, timeout=max_seconds)
            agent_returncode = agent_proc.returncode
            append_case_log(log_path, "agent", agent_proc)
            tail_text = (agent_proc.stdout or b"").decode("utf-8", errors="replace").replace("\n", " ")[-120:]
            if tail_text.strip():
                emit_progress_event(progress_file, {"type": "case_chat", "case_id": case_id, "text": tail_text})
            emit_progress_event(progress_file, {"type": "case_stage", "case_id": case_id, "stage": "agent_done", "returncode": agent_returncode})
            if verbose:
                print_completed_process_output(agent_proc)
            if agent_proc.returncode != 0:
                duration = time.perf_counter() - start
                return CaseResult(
                    case_id=case_id,
                    name=name,
                    status="crash",
                    duration_seconds=duration,
                    agent_returncode=agent_proc.returncode,
                    message="agent command failed",
                    reason=classify_agent_failure(agent_proc.returncode, agent_proc.stderr),
                )

        stage = "check"
        emit_progress_event(progress_file, {"type": "case_stage", "case_id": case_id, "stage": "check"})
        check_proc = run_case_check(case, case_dir=case_dir, cwd=temp_workspace, env=env, timeout=max_seconds)
        append_case_log(log_path, "check", check_proc)
        emit_progress_event(progress_file, {"type": "case_stage", "case_id": case_id, "stage": "check_done", "returncode": check_proc.returncode})
        if verbose:
            print_completed_process_output(check_proc)

        final_snapshot = snapshot_workspace_files(temp_workspace)
        changed_files = detect_changed_files(baseline_snapshot, final_snapshot)
        changed_lines = count_changed_lines(baseline_snapshot, final_snapshot, changed_files)
        constraint_violations = evaluate_constraints(changed_files, changed_lines, constraints)

        duration = time.perf_counter() - start
        if check_proc.returncode == 0 and not constraint_violations:
            return CaseResult(
                case_id=case_id,
                name=name,
                status="pass",
                duration_seconds=duration,
                agent_returncode=agent_returncode,
                check_returncode=check_proc.returncode,
                reason="pass",
            )

        if constraint_violations:
            return CaseResult(
                case_id=case_id,
                name=name,
                status="fail",
                duration_seconds=duration,
                agent_returncode=agent_returncode,
                check_returncode=check_proc.returncode,
                message="constraint failed: " + "; ".join(constraint_violations),
                reason="constraint_failed",
            )

        return CaseResult(
            case_id=case_id,
            name=name,
            status="fail",
            duration_seconds=duration,
            agent_returncode=agent_returncode,
            check_returncode=check_proc.returncode,
            message="check failed",
            reason=classify_check_failure(check_proc.returncode, check_proc.stderr),
        )
    except subprocess.TimeoutExpired:
        duration = time.perf_counter() - start
        timeout_reason = "agent_timeout" if stage == "agent" else "check_timeout"
        append_case_log(log_path, f"timeout:{timeout_reason}")
        emit_progress_event(progress_file, {"type": "case_stage", "case_id": case_id, "stage": timeout_reason})
        return CaseResult(
            case_id=case_id,
            name=name,
            status="crash",
            duration_seconds=duration,
            message="timeout",
            reason=timeout_reason,
        )
    except Exception as exc:
        duration = time.perf_counter() - start
        append_case_log(log_path, f"internal_error: {exc}")
        emit_progress_event(progress_file, {"type": "case_stage", "case_id": case_id, "stage": "internal_error", "message": str(exc)})
        return CaseResult(
            case_id=case_id,
            name=name,
            status="crash",
            duration_seconds=duration,
            agent_returncode=agent_returncode,
            message=str(exc),
            reason="internal_error",
        )
    finally:
        if keep_temp:
            print(f"[keep-temp] {temp_workspace}")
        else:
            shutil.rmtree(temp_workspace, ignore_errors=True)


def format_seconds(value: float) -> str:
    return f"{value:.2f}s"


def format_progress_line(total: int, done: int, passed: int, failed: int, crashed: int, running_labels: list[str]) -> str:
    running_text = ", ".join(running_labels) if running_labels else "-"
    return f"[progress] {done}/{total} done | pass={passed} fail={failed} crash={crashed} | running: {running_text}"


def print_progress_line(line: str) -> None:
    print("\r" + line + " " * 8, end="", file=sys.stderr, flush=True)


def clear_progress_line() -> None:
    print("\r" + " " * 200 + "\r", end="", file=sys.stderr, flush=True)


def emit_progress_event(progress_file: Path | None, payload: dict[str, Any]) -> None:
    if progress_file is None:
        return
    event = {"ts": time.time(), **payload}
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    with progress_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def build_summary(suite: str, results: list[CaseResult], suite_seconds: float) -> dict[str, Any]:
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    crashed = sum(1 for r in results if r.status == "crash")
    total = len(results)
    pass_rate = passed / total if total else 0.0
    avg_duration = sum(r.duration_seconds for r in results) / total if total else 0.0

    reason_counts: dict[str, int] = {}
    for result in results:
        key = result.reason or "unknown"
        reason_counts[key] = reason_counts.get(key, 0) + 1

    return {
        "suite": suite,
        "total_cases": total,
        "passed": passed,
        "failed": failed,
        "crashed": crashed,
        "pass_rate": round(pass_rate, 6),
        "avg_duration": round(avg_duration, 6),
        "suite_seconds": round(suite_seconds, 6),
        "reason_counts": reason_counts,
        "case_results": [r.to_dict() for r in results],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoDarwin benchmark evaluator")
    parser.add_argument("suite", nargs="?", default="smoke", help="Suite name or path (default: smoke)")
    parser.add_argument("--agent-cmd", default=None, help="Shell command to run inside each temp workspace before checking")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary workspaces for inspection")
    parser.add_argument("--list", action="store_true", help="List case ids in the suite and exit")
    parser.add_argument("--json", action="store_true", help="Print summary as JSON")
    parser.add_argument("--seed", type=int, default=None, help="Optional deterministic seed")
    parser.add_argument("--jobs", type=int, default=1, help="Number of parallel worker processes (default: 1)")
    parser.add_argument("--progress", choices=["auto", "on", "off"], default="auto", help="Progress display mode (default: auto)")
    parser.add_argument("--progress-file", default=None, help="Optional JSONL event file for external progress UI")
    parser.add_argument("--case-log-dir", default=None, help="Optional directory for per-case stdout/stderr logs")
    args = parser.parse_args()

    if args.jobs < 1:
        parser.error("--jobs must be >= 1")

    case_ids = load_suite(args.suite)
    if args.list:
        for case_id in case_ids:
            print(case_id)
        return 0

    results: list[CaseResult | None] = [None] * len(case_ids)
    suite_start = time.perf_counter()
    verbose = not args.json
    live_progress = verbose and (args.progress == "on" or (args.progress == "auto" and sys.stderr.isatty()))
    progress_file = Path(args.progress_file) if args.progress_file else None
    case_log_dir = Path(args.case_log_dir) if args.case_log_dir else None

    if progress_file is not None:
        progress_file.parent.mkdir(parents=True, exist_ok=True)
        progress_file.write_text("", encoding="utf-8")
    if case_log_dir is not None:
        case_log_dir.mkdir(parents=True, exist_ok=True)
    emit_progress_event(
        progress_file,
        {
            "type": "suite_start",
            "suite": args.suite,
            "total_cases": len(case_ids),
            "jobs": args.jobs,
        },
    )

    valid_tasks: list[tuple[int, Path, int | None]] = []
    for idx, case_id in enumerate(case_ids):
        case_dir = CASES_DIR / case_id
        case_seed = args.seed + idx if args.seed is not None else None
        if not case_dir.exists():
            if verbose:
                print(f"[missing] {case_id}: case directory not found", file=sys.stderr)
            missing_result = CaseResult(case_id, case_id, "crash", 0.0, message="missing case directory", reason="missing_case_dir")
            results[idx] = missing_result
            emit_progress_event(
                progress_file,
                {
                    "type": "case_done",
                    "suite": args.suite,
                    "index": idx,
                    "case_id": case_id,
                    "name": case_id,
                    "status": missing_result.status,
                    "reason": missing_result.reason,
                    "duration_seconds": missing_result.duration_seconds,
                    "log_path": str(case_log_dir / f"{case_id}.log") if case_log_dir is not None else None,
                },
            )
            continue
        valid_tasks.append((idx, case_dir, case_seed))

    if args.jobs == 1 or len(valid_tasks) <= 1:
        for idx, case_dir, case_seed in valid_tasks:
            emit_progress_event(
                progress_file,
                {
                    "type": "case_start",
                    "suite": args.suite,
                    "index": idx,
                    "case_id": case_dir.name,
                    "name": case_dir.name,
                },
            )
            if verbose:
                print(f"==> {case_dir.name}")
            result = execute_case(
                case_dir,
                args.agent_cmd,
                keep_temp=args.keep_temp,
                verbose=verbose,
                seed=case_seed,
                progress_file=progress_file,
                case_log_dir=case_log_dir,
            )
            results[idx] = result
            emit_progress_event(
                progress_file,
                {
                    "type": "case_done",
                    "suite": args.suite,
                    "index": idx,
                    "case_id": result.case_id,
                    "name": result.name,
                    "status": result.status,
                    "reason": result.reason,
                    "duration_seconds": result.duration_seconds,
                    "log_path": str(case_log_dir / f"{result.case_id}.log") if case_log_dir is not None else None,
                },
            )
            if verbose:
                print(f"    {result.status:5s}  {format_seconds(result.duration_seconds)}  {result.name}")
                if result.message:
                    print(f"    note: {result.message}")
    else:
        if verbose:
            print(f"[parallel] jobs={args.jobs}")
        max_workers = min(args.jobs, len(valid_tasks))
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            future_to_meta = {}
            for idx, case_dir, case_seed in valid_tasks:
                future = pool.submit(
                    execute_case,
                    case_dir,
                    args.agent_cmd,
                    args.keep_temp,
                    False,
                    case_seed,
                    progress_file,
                    case_log_dir,
                )
                future_to_meta[future] = (idx, case_dir.name, time.perf_counter())
                emit_progress_event(
                    progress_file,
                    {
                        "type": "case_start",
                        "suite": args.suite,
                        "index": idx,
                        "case_id": case_dir.name,
                        "name": case_dir.name,
                    },
                )

            pending = set(future_to_meta)
            while pending:
                done_now, pending = wait(pending, timeout=0.5, return_when=FIRST_COMPLETED)

                if live_progress:
                    done_count = sum(1 for r in results if r is not None)
                    passed = sum(1 for r in results if r is not None and r.status == "pass")
                    failed = sum(1 for r in results if r is not None and r.status == "fail")
                    crashed = sum(1 for r in results if r is not None and r.status == "crash")
                    now = time.perf_counter()
                    running_labels: list[str] = []
                    for future in list(pending)[:4]:
                        _, case_id, started_at = future_to_meta[future]
                        running_labels.append(f"{case_id}({int(now - started_at)}s)")
                    line = format_progress_line(len(case_ids), done_count, passed, failed, crashed, running_labels)
                    print_progress_line(line)

                for future in done_now:
                    idx, case_id, _ = future_to_meta[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        result = CaseResult(
                            case_id=case_id,
                            name=case_id,
                            status="crash",
                            duration_seconds=0.0,
                            message=str(exc),
                            reason="internal_error",
                        )
                    results[idx] = result
                    emit_progress_event(
                        progress_file,
                        {
                            "type": "case_done",
                            "suite": args.suite,
                            "index": idx,
                            "case_id": result.case_id,
                            "name": result.name,
                            "status": result.status,
                            "reason": result.reason,
                            "duration_seconds": result.duration_seconds,
                            "log_path": str(case_log_dir / f"{result.case_id}.log") if case_log_dir is not None else None,
                        },
                    )
                    if verbose:
                        if live_progress:
                            clear_progress_line()
                        print(f"==> {case_id}")
                        print(f"    {result.status:5s}  {format_seconds(result.duration_seconds)}  {result.name}")
                        if result.message:
                            print(f"    note: {result.message}")
                        if live_progress:
                            done_count = sum(1 for r in results if r is not None)
                            passed = sum(1 for r in results if r is not None and r.status == "pass")
                            failed = sum(1 for r in results if r is not None and r.status == "fail")
                            crashed = sum(1 for r in results if r is not None and r.status == "crash")
                            now = time.perf_counter()
                            running_labels = []
                            for p in list(pending)[:4]:
                                _, running_case_id, started_at = future_to_meta[p]
                                running_labels.append(f"{running_case_id}({int(now - started_at)}s)")
                            line = format_progress_line(len(case_ids), done_count, passed, failed, crashed, running_labels)
                            print_progress_line(line)

            if live_progress:
                clear_progress_line()

    finalized_results = [r for r in results if r is not None]

    suite_seconds = time.perf_counter() - suite_start
    summary = build_summary(args.suite, finalized_results, suite_seconds)
    emit_progress_event(
        progress_file,
        {
            "type": "suite_done",
            "suite": args.suite,
            "total_cases": summary["total_cases"],
            "passed": summary["passed"],
            "failed": summary["failed"],
            "crashed": summary["crashed"],
            "pass_rate": summary["pass_rate"],
            "suite_seconds": summary["suite_seconds"],
        },
    )

    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print("---")
        print(f"suite:         {summary['suite']}")
        print(f"total_cases:   {summary['total_cases']}")
        print(f"passed:        {summary['passed']}")
        print(f"failed:        {summary['failed']}")
        print(f"crashed:       {summary['crashed']}")
        print(f"pass_rate:     {summary['pass_rate']:.3f}")
        print(f"avg_duration:  {summary['avg_duration']:.2f}")
        print(f"suite_seconds: {summary['suite_seconds']:.2f}")
        if summary["reason_counts"]:
            print(f"reasons:       {json.dumps(summary['reason_counts'], ensure_ascii=False)}")

    return 0 if summary["failed"] == 0 and summary["crashed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
