# AutoDarwin 文档实现状态（按当前代码）

最后核对：2026-04-09

## 已实现（可直接用）

- 评测执行器：`benchmarks/evaluator.py`
  - suite 加载：`smoke/core/holdout`
  - case 元数据生效：`workspace`、`check.type(script/command)`、`tools`
  - 约束检查：`forbid/allow paths`、`forbid/allow globs`、`max_changed_files`、`max_changed_lines`
  - 并发评测：`--jobs N`
  - 进度与日志：`--progress auto|on|off`、`--progress-file`、`--case-log-dir`
  - 结构化输出：`--json`（含 `reason_counts`/`case_results`）

- 运行层：`runner.py`
  - `pi --mode rpc --no-session`
  - 支持 `--tools`、`--seed`、`--timeout`

- 进化闭环：`evolve.py`
  - mutation → baseline/candidate 评测 → keep/discard
  - `--repeats`、`--margin`
  - 同分耗时 tie-break（`avg_duration`）
  - `--holdout-suite` + `--holdout-every`
  - 结果记录：`results.tsv` + `results.jsonl`
  - prompt 历史快照：`.autodarwin/history/*.md`

- 回放：`replay.py`
  - `--round-id` / `--candidate-hash` 重放

- UI 与入口
  - `autodarwin.bat`：`smoke|core|holdout|eval-ui|evolve|replay`
  - `tools/eval_with_ui.py`、`tools/progress_web.py`、`tools/progress_view.py`

## 部分实现 / 仍待增强

- 失败归因已具备基础分类（`agent_*`/`check_*`/`constraint_failed`），但还未细到 tool-error 子类与命令级标签。
- 约束系统已覆盖常用规则，但未实现更复杂策略（如命令白名单、目录配额）。

## 过期/历史文档判断

- `plans/mvp-subagent-plan.md`：任务拆解文档，绝大多数事项已完成；现主要作为历史记录。
- `plans/mvp-v0.md`：设计基线仍有参考价值，但其中部分目录示例已不是当前真实结构（历史语境）。
- `plans/future-plan.md`：未来路线文档，不是当前实现清单。

## 这次整理动作

- 已移除 `docs/` 根目录下的重复“已迁移”占位文件，统一只保留：
  - `docs/guides/*`
  - `docs/benchmarks/*`
  - `docs/plans/*`
  - `docs/status.md`
