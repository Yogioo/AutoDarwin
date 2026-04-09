#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "benchmarks" / "cases"

HTML = """<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>AutoDarwin Live UI</title>
  <style>
    :root {
      --bg: #0b1020;
      --bg-soft: #111936;
      --bg-card: #10172e;
      --line: #27345a;
      --text: #e6edf3;
      --muted: #9fb0d1;
      --pass: #5ee38a;
      --fail: #ff8fa3;
      --run: #7ec8ff;
      --user: #2d4ee8;
      --assistant: #18305e;
    }
    * { box-sizing: border-box; }
    body { margin:0; background:var(--bg); color:var(--text); font-family: Inter, Segoe UI, Roboto, Arial, sans-serif; }
    .top {
      position: sticky; top:0; z-index:20;
      background: linear-gradient(180deg, #121b38 0%, #10172e 100%);
      border-bottom:1px solid var(--line);
      padding: 10px 14px;
    }
    .title { font-size:16px; font-weight:700; margin-bottom:4px; }
    .meta { color: var(--muted); font-size:13px; margin-bottom:6px; }
    .bar { height:8px; border-radius:999px; background:#1a2647; overflow:hidden; }
    .bar > div { height:100%; background:linear-gradient(90deg, #4da3ff, #63f4a5); width:0%; transition: width .25s linear; }

    .grid {
      display:grid;
      grid-template-columns:repeat(auto-fit,minmax(460px,1fr));
      gap:10px;
      padding:10px;
    }

    .pane {
      background: var(--bg-card);
      border:1px solid var(--line);
      border-radius:10px;
      min-height: 560px;
      display:flex;
      flex-direction:column;
      overflow:hidden;
      box-shadow: 0 6px 20px rgba(0,0,0,.18);
    }

    .pane-head {
      padding:8px 10px;
      border-bottom:1px solid var(--line);
      display:flex;
      justify-content:space-between;
      align-items:center;
      gap:8px;
      font-size:13px;
    }
    .badge { padding:2px 8px; border-radius:999px; font-size:12px; border:1px solid transparent; }
    .status-running { color:var(--run); border-color:#2f6ca8; background:#122744; }
    .status-pass { color:var(--pass); border-color:#2b7d4a; background:#102c1d; }
    .status-fail, .status-crash { color:var(--fail); border-color:#9e3e55; background:#371824; }

    .pane-meta { color:var(--muted); font-size:12px; margin-top:4px; }

    .chat {
      padding:10px;
      border-bottom:1px solid var(--line);
      height: 260px;
      overflow:auto;
      display:flex;
      flex-direction:column;
      gap:8px;
      background: #0e152c;
    }
    .msg { max-width:95%; border-radius:10px; padding:8px 10px; white-space:pre-wrap; word-break:break-word; font-size:12px; line-height:1.45; }
    .msg.user { background:var(--user); align-self:flex-end; }
    .msg.assistant { background:var(--assistant); align-self:flex-start; border:1px solid #2f4f90; }

    details { border-bottom:1px solid var(--line); }
    summary {
      cursor:pointer;
      list-style:none;
      padding:8px 10px;
      color: var(--muted);
      font-size:12px;
      user-select:none;
    }
    summary::-webkit-details-marker { display:none; }
    pre {
      margin:0;
      padding:0 10px 10px;
      white-space:pre-wrap;
      word-break:break-word;
      font-size:12px;
      line-height:1.4;
      max-height: 220px;
      overflow:auto;
      color:#dbe7ff;
    }

    .modal {
      position: fixed; inset: 0; background: rgba(0,0,0,.55);
      display:none; align-items:center; justify-content:center; z-index:99;
    }
    .modal.show { display:flex; }
    .dialog {
      width:min(700px, 92vw);
      background: #111936;
      border:1px solid var(--line);
      border-radius:12px;
      padding:14px;
      box-shadow:0 20px 60px rgba(0,0,0,.4);
    }
    .dialog h2 { margin:0 0 10px; font-size:20px; }
    .dialog .summary { color:var(--muted); font-size:14px; margin-bottom:10px; }
    .table { width:100%; border-collapse:collapse; font-size:13px; }
    .table th,.table td { border-bottom:1px solid #223054; padding:6px; text-align:left; }
    .btn { margin-top:12px; padding:8px 12px; background:#1e3a8a; color:#fff; border:none; border-radius:8px; cursor:pointer; }
  </style>
</head>
<body>
  <div class=\"top\">
    <div class=\"title\">AutoDarwin Live UI</div>
    <div id=\"meta\" class=\"meta\">loading...</div>
    <div class=\"bar\"><div id=\"barFill\"></div></div>
  </div>

  <div id=\"grid\" class=\"grid\"></div>

  <div id=\"doneModal\" class=\"modal\">
    <div class=\"dialog\">
      <h2>评测已完成</h2>
      <div id=\"doneText\" class=\"summary\"></div>
      <table class=\"table\" id=\"slowTable\">
        <thead><tr><th>case</th><th>status</th><th>duration(s)</th></tr></thead>
        <tbody></tbody>
      </table>
      <button class=\"btn\" onclick=\"closeDoneModal()\">关闭</button>
    </div>
  </div>

  <script>
    const panes = new Map();
    let shownDone = false;
    let failCount = 0;

    function esc(s) {
      return String(s ?? '').replace(/[&<>\"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[ch]));
    }

    function ensurePane(caseId) {
      if (panes.has(caseId)) return panes.get(caseId);

      const root = document.createElement('div');
      root.className = 'pane';
      root.innerHTML = `
        <div class="pane-head">
          <div>
            <div class="line1"></div>
            <div class="pane-meta"></div>
          </div>
          <span class="badge"></span>
        </div>
        <div class="chat"></div>
        <details open><summary>任务详情（Prompt / Case）</summary><pre class="task"></pre></details>
        <details><summary>Agent stderr / runner 输出</summary><pre class="agentErr"></pre></details>
        <details><summary>Check 输出</summary><pre class="checkOut"></pre></details>
        <details><summary>原始日志</summary><pre class="raw"></pre></details>
      `;
      document.getElementById('grid').appendChild(root);

      const pane = {
        root,
        line1: root.querySelector('.line1'),
        meta: root.querySelector('.pane-meta'),
        badge: root.querySelector('.badge'),
        chat: root.querySelector('.chat'),
        task: root.querySelector('.task'),
        agentErr: root.querySelector('.agentErr'),
        checkOut: root.querySelector('.checkOut'),
        raw: root.querySelector('.raw'),
        taskLoaded: false,
      };
      panes.set(caseId, pane);
      return pane;
    }

    function statusClass(status) {
      if (status === 'pass') return 'status-pass';
      if (status === 'fail' || status === 'crash') return 'status-fail';
      return 'status-running';
    }

    function renderChat(chatEl, prompt, assistantText) {
      const atBottom = (chatEl.scrollTop + chatEl.clientHeight) >= (chatEl.scrollHeight - 6);
      const html = `
        <div class="msg user">${esc(prompt || '(no prompt)')}</div>
        <div class="msg assistant">${esc(assistantText || '(waiting assistant output...)')}</div>
      `;
      if (chatEl.innerHTML !== html) {
        chatEl.innerHTML = html;
        if (atBottom) chatEl.scrollTop = chatEl.scrollHeight;
      }
    }

    async function fetchJson(url) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 2500);
      try {
        const r = await fetch(url, {cache:'no-store', signal: controller.signal});
        if (!r.ok) throw new Error('http ' + r.status);
        return await r.json();
      } finally {
        clearTimeout(timer);
      }
    }

    function closeDoneModal() {
      document.getElementById('doneModal').classList.remove('show');
    }
    window.closeDoneModal = closeDoneModal;

    function maybeShowDone(st) {
      if (!st.suite_done || shownDone) return;
      shownDone = true;
      const txt = `suite=${st.suite} | pass=${st.passed} fail=${st.failed} crash=${st.crashed} | pass_rate=${st.pass_rate ?? '-'} | total=${st.suite_seconds ?? '-'}s`;
      document.getElementById('doneText').textContent = txt;

      const slow = [...st.cases]
        .filter(c => c.duration_seconds != null)
        .sort((a,b) => Number(b.duration_seconds||0) - Number(a.duration_seconds||0))
        .slice(0,5);
      const tbody = document.querySelector('#slowTable tbody');
      tbody.innerHTML = slow.map(c => `<tr><td>${esc(c.case_id)}</td><td>${esc(c.status)}</td><td>${Number(c.duration_seconds||0).toFixed(2)}</td></tr>`).join('');
      document.getElementById('doneModal').classList.add('show');
    }

    async function refresh() {
      let st;
      try {
        st = await fetchJson('/api/state');
        failCount = 0;
      } catch (e) {
        failCount += 1;
        const msg = (e && e.message) ? e.message : String(e || 'unknown');
        document.getElementById('meta').textContent = `连接后端失败（${failCount}）: ${msg} | 尝试打开 /api/state 检查`;
        return;
      }

      const meta = `suite=${st.suite} jobs=${st.jobs} done=${st.done}/${st.total_cases} pass=${st.passed} fail=${st.failed} crash=${st.crashed} running=${st.running}`;
      document.getElementById('meta').textContent = meta;
      const pct = st.total_cases > 0 ? Math.floor((st.done / st.total_cases) * 100) : 0;
      document.getElementById('barFill').style.width = pct + '%';

      for (const c of st.cases) {
        const pane = ensurePane(c.case_id);
        const stage = c.stage ? '/' + c.stage : '';
        const duration = c.status === 'running'
          ? (c.elapsed_seconds != null ? ` ${c.elapsed_seconds}s` : '')
          : (c.duration_seconds != null ? ` ${Number(c.duration_seconds).toFixed(1)}s` : '');

        pane.line1.textContent = `${c.case_id} ${c.status || 'queued'}${stage}${duration}`;
        pane.meta.textContent = c.reason ? `reason: ${c.reason}` : '';
        pane.badge.className = 'badge ' + statusClass(c.status);
        pane.badge.textContent = c.status || 'running';

        try {
          const detail = await fetchJson('/api/case?case_id=' + encodeURIComponent(c.case_id));
          const caseMeta = detail.case || {};
          const parsed = detail.parsed || {};

          const taskText = [
            `id: ${caseMeta.id || c.case_id}`,
            `name: ${caseMeta.name || ''}`,
            `description: ${caseMeta.description || ''}`,
            `workspace: ${caseMeta.workspace || ''}`,
            `max_seconds: ${caseMeta.max_seconds ?? ''}`,
            `tools: ${(caseMeta.tools || []).join(', ')}`,
            `check: ${JSON.stringify(caseMeta.check || {})}`,
            '',
            '[Prompt]',
            String(caseMeta.prompt || '')
          ].join('\\n');
          if (pane.task.textContent !== taskText) pane.task.textContent = taskText;

          renderChat(pane.chat, caseMeta.prompt || '', parsed.agent_stdout || '');
          pane.agentErr.textContent = parsed.agent_stderr || '(empty)';
          pane.checkOut.textContent = [parsed.check_stdout || '', parsed.check_stderr || ''].filter(Boolean).join('\\n') || '(empty)';
          pane.raw.textContent = detail.raw_log || '(empty)';
        } catch (_) {
          // keep old content
        }
      }

      maybeShowDone(st);
    }

    setInterval(refresh, 900);
    refresh();
  </script>
</body>
</html>
"""


def parse_case_log(text: str) -> dict[str, str]:
    sections: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    mode = "other"

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("==== ") and line.endswith(" ===="):
            title = line[5:-5].strip()
            cur = {"title": title, "stdout": [], "stderr": [], "other": []}
            sections.append(cur)
            mode = "other"
            continue
        if line == "[stdout]":
            mode = "stdout"
            continue
        if line == "[stderr]":
            mode = "stderr"
            continue

        if cur is None:
            cur = {"title": "raw", "stdout": [], "stderr": [], "other": []}
            sections.append(cur)

        cur[mode].append(line)

    out = {
        "agent_stdout": "",
        "agent_stderr": "",
        "check_stdout": "",
        "check_stderr": "",
    }

    for sec in sections:
        title = str(sec.get("title", "")).lower()
        stdout = "\n".join(sec.get("stdout") or []).strip()
        stderr = "\n".join(sec.get("stderr") or []).strip()
        if title.startswith("agent"):
            if stdout:
                out["agent_stdout"] += ("\n" if out["agent_stdout"] else "") + stdout
            if stderr:
                out["agent_stderr"] += ("\n" if out["agent_stderr"] else "") + stderr
        elif title.startswith("check"):
            if stdout:
                out["check_stdout"] += ("\n" if out["check_stdout"] else "") + stdout
            if stderr:
                out["check_stderr"] += ("\n" if out["check_stderr"] else "") + stderr
        else:
            other_lines = sec.get("other") or []
            other_text = "\n".join(other_lines).strip()
            if other_text:
                out["agent_stderr"] += ("\n" if out["agent_stderr"] else "") + other_text

    return out


def load_case_meta(case_id: str) -> dict[str, Any] | None:
    case_path = CASES_DIR / case_id / "case.json"
    if not case_path.exists():
        return None
    try:
        return json.loads(case_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def parse_progress(progress_file: Path) -> dict[str, Any]:
    state: dict[str, Any] = {
        "suite": "-",
        "jobs": "-",
        "total_cases": 0,
        "cases": {},
        "suite_done": False,
        "suite_summary": {},
    }
    if not progress_file.exists():
        return state

    try:
        lines = progress_file.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return state

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue

        t = e.get("type")
        if t == "suite_start":
            state["suite"] = e.get("suite", "-")
            state["jobs"] = e.get("jobs", "-")
            state["total_cases"] = int(e.get("total_cases", 0) or 0)
            state["cases"] = {}
            state["suite_done"] = False
            state["suite_summary"] = {}
            continue

        if t == "suite_done":
            state["suite_done"] = True
            state["suite_summary"] = {
                "passed": e.get("passed"),
                "failed": e.get("failed"),
                "crashed": e.get("crashed"),
                "pass_rate": e.get("pass_rate"),
                "suite_seconds": e.get("suite_seconds"),
            }
            continue

        if t == "case_start":
            cid = str(e.get("case_id", ""))
            state["cases"].setdefault(cid, {"case_id": cid})
            state["cases"][cid].update(
                {
                    "index": e.get("index"),
                    "status": "running",
                    "started_at": e.get("ts"),
                }
            )
            continue

        if t == "case_stage":
            cid = str(e.get("case_id", ""))
            state["cases"].setdefault(cid, {"case_id": cid})
            state["cases"][cid]["stage"] = e.get("stage")
            if state["cases"][cid].get("status") not in {"pass", "fail", "crash"}:
                state["cases"][cid]["status"] = "running"
            continue

        if t == "case_done":
            cid = str(e.get("case_id", ""))
            state["cases"].setdefault(cid, {"case_id": cid})
            state["cases"][cid].update(
                {
                    "index": e.get("index"),
                    "status": e.get("status"),
                    "reason": e.get("reason"),
                    "duration_seconds": e.get("duration_seconds"),
                    "log_path": e.get("log_path"),
                }
            )
            continue

    now = time.time()
    rows = sorted(state["cases"].values(), key=lambda x: x.get("index", 10**9))
    for c in rows:
        if c.get("status") == "running" and isinstance(c.get("started_at"), (int, float)):
            c["elapsed_seconds"] = int(now - float(c["started_at"]))

    state["case_rows"] = rows
    return state


def make_handler(progress_file: Path, case_log_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path

            if path == "/":
                body = HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if path == "/api/state":
                st = parse_progress(progress_file)
                rows = st.get("case_rows", [])
                summary = st.get("suite_summary", {})
                payload = {
                    "suite": st.get("suite", "-"),
                    "jobs": st.get("jobs", "-"),
                    "total_cases": st.get("total_cases", 0),
                    "done": sum(1 for c in rows if c.get("status") in {"pass", "fail", "crash"}),
                    "passed": sum(1 for c in rows if c.get("status") == "pass"),
                    "failed": sum(1 for c in rows if c.get("status") == "fail"),
                    "crashed": sum(1 for c in rows if c.get("status") == "crash"),
                    "running": sum(1 for c in rows if c.get("status") == "running"),
                    "suite_done": st.get("suite_done", False),
                    "pass_rate": summary.get("pass_rate"),
                    "suite_seconds": summary.get("suite_seconds"),
                    "cases": rows,
                }
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            if path == "/api/case":
                q = urllib.parse.parse_qs(parsed.query)
                case_id = str((q.get("case_id") or [""])[0]).strip()
                if not case_id:
                    self.send_error(400, "missing case_id")
                    return

                case_meta = load_case_meta(case_id)
                p = case_log_dir / f"{case_id}.log"
                raw_log = ""
                if p.exists():
                    try:
                        raw_log = p.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        raw_log = ""
                parsed_log = parse_case_log(raw_log)
                payload = {
                    "case": case_meta,
                    "parsed": parsed_log,
                    "raw_log": raw_log,
                }
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            self.send_error(404)

        def log_message(self, fmt: str, *args: Any) -> None:
            return

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoDarwin web progress viewer")
    parser.add_argument("--file", default=".autodarwin/progress.jsonl", help="Progress JSONL file")
    parser.add_argument("--case-log-dir", default=".autodarwin/case-logs", help="Per-case log directory")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8765, help="Bind port")
    parser.add_argument("--open-browser", action="store_true", help="Open browser automatically")
    args = parser.parse_args()

    progress_file = Path(args.file)
    case_log_dir = Path(args.case_log_dir)

    server = ThreadingHTTPServer((args.host, args.port), make_handler(progress_file, case_log_dir))
    url = f"http://{args.host}:{args.port}/"
    print(f"[web-ui] {url}")

    if args.open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
