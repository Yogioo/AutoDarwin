# AutoDarwin 项目现状（当前代码）

最后更新：2026-04-09

## 现状结论（先说结论）

- 当前项目主线已可用：`评测 -> 进化 -> 回放` 闭环可跑。
- 项目内已有“现状文件”：`docs/status.md`（即本文件）。
- 目前**未直接集成** `auto research` 开源库；现阶段是参考其“研究组织/分工”理念。
- 最近方向已收敛：**近期优先级不是继续加功能，而是先把“自我进化器”本身做硬。**
- `research / 多 sub-agent 并行范式` 目前仅保留为候选方向，**不作为当前主线**。

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

## 当前进化依据（关键现状）

当前项目的“变好”依据，仍然主要来自**外部 benchmark 选择压力**，不是 Agent 内生理解。

现状可概括为：
- 变异对象：当前以 `.pi/SYSTEM.md` 为主
- 变异方式：`mutate.py` 调用模型，对当前 prompt 做“小改进”式改写
- 主评测指标：`pass_rate`
- 次排序指标：`avg_duration`
- 接受规则：`candidate_mean > baseline_mean + margin`；同分时选更快版本
- holdout：当前主要用于观察/记录，**不是主接受门槛**

这意味着：
- 当前闭环更像“可运行的 prompt 进化实验台”
- 还不是“基于失败归因的定向自我进化系统”
- 当前方向是否足够正确，**已进入重新审视阶段**

## 方向调整（最新）

近期共识：
- 优先做强进化闭环本身，而不是扩功能面
- benchmark 继续走“少而强”，不走堆量路线
- 可激进开放搜索空间，但评测/裁判层应保持稳定可信
- 真正需要重讨论的是：**fitness function / 进化依据到底该如何定义**

已暂停为主线的方向：
- 复杂 research 编排
- 主 Agent + 多 sub-agent 并行 research 融合
- 以“先补功能”为主的开发路线

## AutoResearch（karpathy/autoresearch）核心思路提取

已新增提取文档：`docs/plans/autoresearch-core-notes.md`

提取结论（摘要）：
- 核心范式：最小闭环 + 固定预算评测 + keep/discard + 结果账本化
- 人类主要迭代策略文档，Agent主要执行实验
- AutoDarwin 当前架构与该范式同构，差异主要在任务域

## 下一步（待重新讨论）

当前不直接拍板新实现，先记录待讨论重点：

1. 重新定义“什么叫变好”（fitness function）。
2. 重新评估 holdout 是否应进入主接受门槛。
3. 明确哪些层允许进化，哪些层必须冻结为可信裁判。
4. 在上述问题澄清前，暂不把 research / 多 sub-agent 作为近期主线。

## 运行基线命令

```bat
autodarwin.bat smoke --jobs 2
autodarwin.bat core --jobs 4
python evolve.py --suite core --rounds 3 --pi-cmd "cmd /c pi"
```
