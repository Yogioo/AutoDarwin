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
autodarwin.bat smoke
autodarwin.bat core
autodarwin.bat holdout
autodarwin.bat evolve --suite core --rounds 5
autodarwin.bat evolve --suite core --rounds 20 --repeats 3 --seed 42 --holdout-suite holdout --holdout-every 5
autodarwin.bat replay --round-id 3
```

约定：
- 快速回归用 `smoke`
- 日常进化用 `core`
- 阶段验收用 `holdout`

## Windows note

- Use `autodarwin.bat` as the one-command launcher.
- Cases ship with Windows-native `check.bat` scripts.
- `.sh` files are kept for bash-based environments.
