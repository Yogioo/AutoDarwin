# AutoDarwin 项目现状（当前代码）

最后更新：2026-04-09

## 现状结论（先说结论）

- 当前项目主线已可用：`评测 -> 进化 -> 回放` 闭环可跑。
- 项目内已有“现状文件”：`docs/status.md`（即本文件）。
- 目前**未直接集成** `auto research` 开源库；现阶段是参考其“研究组织/分工”理念。

## 已实现（可直接使用）

- 评测执行器：`benchmarks/evaluator.py`
  - suite：`smoke/core/holdout`
  - 并发：`--jobs N`
  - case 元数据：`workspace`、`check.type(script/command)`、`tools`
  - 约束：`forbid/allow paths`、`forbid/allow globs`、`max_changed_files`、`max_changed_lines`
  - 输出：`--json`（含 `reason_counts` / `case_results`）

- 运行层：`runner.py`
  - `pi --mode rpc --no-session`
  - 支持 `--tools`、`--seed`、`--timeout`

- 进化闭环：`evolve.py`
  - mutation -> baseline/candidate 评测 -> keep/discard
  - `--repeats`、`--margin`
  - tie-break：同分比 `avg_duration`
  - `--holdout-suite` + `--holdout-every`
  - 记录：`results.tsv` + `results.jsonl`

- 回放：`replay.py`
  - `--round-id` / `--candidate-hash`

- 入口与可视化
  - `autodarwin.bat`：`smoke|core|holdout|eval-ui|evolve|replay`
  - `tools/eval_with_ui.py`、`tools/progress_web.py`、`tools/progress_view.py`

## 基准集现状

- smoke：4 个 case（`case_001,003,006,008`）
- core：8 个 case（`case_001~008`）
- holdout：5 个 case（`case_009~013`）

## 与 auto research 理念的对齐状态

- 已对齐：
  - 小闭环优先（先跑通再扩展）
  - 可观测性（进度事件 + case 日志 + JSON 汇总）
  - 可回放（按轮次/候选复现）

- 未落地（当前缺口）：
  - 尚未引入 `auto research` 库本体（代码级依赖为 0）
  - 尚未形成“Researcher/Mutator/Evaluator/Archivist”多角色自动协作流
  - research 型 benchmark 仍偏少（现有 case 以本地编辑任务为主）

## AutoResearch（karpathy/autoresearch）核心思路提取

已新增提取文档：`docs/plans/autoresearch-core-notes.md`

提取结论（摘要）：
- 核心范式：最小闭环 + 固定预算评测 + keep/discard + 结果账本化
- 人类主要迭代策略文档，Agent主要执行实验
- AutoDarwin 当前架构与该范式同构，差异主要在任务域

## 下一步（最小可行）

1. 保持现有闭环不动，先新增 1~2 个 research 型 case。
2. 在 `.pi/SYSTEM.md` 增加“先研究后修改”的最小策略约束。
3. 用 `core + holdout` 做对比，确认提升是否稳定。

## 运行基线命令

```bat
autodarwin.bat smoke --jobs 2
autodarwin.bat core --jobs 4
python evolve.py --suite core --rounds 3 --pi-cmd "cmd /c pi"
```
