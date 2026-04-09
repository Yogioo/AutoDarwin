# AutoDarwin Benchmarks

This directory contains MVP benchmark cases for AutoDarwin.

## Structure

- `cases/<case_id>/case.json` - metadata and prompt for one case（支持 `workspace/check/tools/constraints`，含 `allow/forbid paths+globs` 与 changed 限制）
- `cases/<case_id>/<workspace_dir>/` - initial workspace copied into a temp directory before each run (`workspace_dir` comes from `case.json.workspace`)
- `cases/<case_id>/check.sh` or `check.bat` - validation script for the case
- `suites/*.txt` - benchmark suite definitions

## Runner convention

Recommended execution model:

1. Copy `cases/<case_id>/<workspace_dir>/` into a fresh temp directory (from `case.json.workspace`)
2. Write the candidate `.pi/SYSTEM.md` into that temp workspace
3. Run pi in the temp workspace with `--no-session`
4. Execute `bash <case_dir>/check.sh` with the temp workspace as cwd
5. Record pass/fail, duration, and logs
6. Apply optional `constraints` checks (e.g. forbid paths / max changed files)

The check scripts in this directory assume:

- the current working directory is the temp workspace copy
- the script itself is executed from its original case directory path

Example:

```bat
cmd.exe /c benchmarks\cases\case_003\check.bat
```

## Standard commands

```bat
autodarwin.bat smoke --jobs 2
autodarwin.bat core --jobs 4
autodarwin.bat holdout --jobs 4
autodarwin.bat core-ui
autodarwin.bat eval-ui core --jobs 6
autodarwin.bat evolve --suite core --rounds 5
autodarwin.bat evolve --suite core --rounds 20 --repeats 3 --seed 42 --holdout-suite holdout --holdout-every 5
autodarwin.bat replay --round-id 3
```

约定（给 AI/Agent）：
- 默认优先并发评测（`--jobs N`），不要逐 case 串行跑
- 仅在需要观察单 case 多轮对话细节时，才用 `--jobs 1`
- 快速回归用 `smoke`，日常进化用 `core`，阶段验收用 `holdout`

进度显示：
- `--progress auto`（默认）：交互终端单行刷新，不膨胀日志
- `--progress on|off`：强制开/关
- `--progress-file .autodarwin/progress.jsonl`：写入事件流，供独立 UI 读取

人类友好一键模式（Windows）：
- `autodarwin.bat core-ui`：自动启动评测 + 自动弹出实时 UI 窗口
- `autodarwin.bat eval-ui core --jobs 6`：指定 suite/jobs
- 默认是 Web UI（浏览器）：多列卡片显示每个 case 状态/阶段/耗时
- 每个 case 展示完整信息：Prompt、任务描述、Agent 聊天输出、Agent stderr、Check 输出、原始日志
- suite 完成后会弹出总结窗口（通过率/总耗时/慢 case）
- 文本 UI 仍可用：`autodarwin.bat eval-ui core --ui text`
- 默认同时写入 case 详细日志：`.autodarwin/case-logs/<case_id>.log`

独立查看器（不污染主日志）：
```bat
python tools/progress_view.py --file .autodarwin/progress.jsonl
```

查看某个 case 的内部输出：
```bat
type .autodarwin\case-logs\case_008.log
```

## Windows note

- Use `autodarwin.bat` as the one-command launcher.
- Cases ship with Windows-native `check.bat` scripts.
- `.sh` files are kept for bash-based environments.
