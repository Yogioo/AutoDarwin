# AutoResearch 核心思路提取（对齐 `karpathy/autoresearch`）

最后更新：2026-04-09
来源：
- https://github.com/karpathy/autoresearch
- https://github.com/karpathy/autoresearch/blob/master/README.md
- https://github.com/karpathy/autoresearch/blob/master/program.md

> 目标：提炼可复用的“方法论”，并映射到 AutoDarwin。

---

## 1. 核心方法（抽象后）

1) **极小闭环优先**
- 固定一个可跑的真实任务（不是纯玩具）
- 每轮只做一小步改动
- 立即评估，直接保留/丢弃

2) **职责清晰的最小文件边界**
- 固定不动区（类似 `prepare.py`）
- 可进化区（类似 `train.py`）
- 人类策略区（类似 `program.md`）

3) **固定预算、可比较评测**
- 每轮实验预算一致（时间/资源）
- 指标单一且稳定（如 `val_bpb`，越低越好）
- 目标是“可比较”，不是“绝对最优”

4) **实验账本化**
- 每轮结果落盘
- 明确 crash / fail / pass
- 失败可追溯，成功可复现

5) **策略即代码（但保持轻量）**
- 人类主要迭代“策略文档”（`program.md`）
- Agent按策略执行
- 用实验结果反推策略是否有效

---

## 2. 与 AutoDarwin 的映射

对应关系（当前仓库）：

- 固定不动区：`benchmarks/*`（case + check + suites）
- 可进化区：`.pi/SYSTEM.md`
- 人类策略区：同样是 `.pi/SYSTEM.md`（当前是单文件形态）
- 评测执行：`benchmarks/evaluator.py`
- keep/discard：`evolve.py`
- 实验账本：`results.tsv` + `results.jsonl` + `.autodarwin/history/*.md`

结论：
- AutoDarwin 当前架构已与 AutoResearch 核心范式同构（最小闭环 + 可比较评测 + keep/discard）。
- 主要差异在任务域：
  - AutoResearch 偏“训练代码优化”
  - AutoDarwin 偏“通用 coding task benchmark”

---

## 3. 可直接借鉴的 5 条规则

1. **单轮只允许一个小改动**（防止多变量混杂）
2. **固定预算评测**（同条件比较）
3. **结果账本必须结构化**（可回放、可分析）
4. **优先简单改动带来的稳定收益**（拒绝 hacky 复杂化）
5. **失败优先归因再迭代**（不是盲目多跑）

---

## 4. 对 AutoDarwin 的最小落地建议（不扩复杂度）

1. 在 prompt 进化策略中显式加入：
- “每次 mutation 只做 1 个局部改动”
- “若收益不稳定则回退”

2. 在 benchmark 使用上坚持：
- smoke 快速回归
- core 日常决策
- holdout 阶段验收（防过拟合）

3. 在结果复盘时固定看三项：
- `pass_rate`
- `reason_counts`
- 慢/易崩 case 列表

---

## 5. 当前边界（避免误解）

- 本项目目前**未直接引入** `karpathy/autoresearch` 代码。
- 当前是方法论对齐，不是代码依赖对齐。
- 若未来引库，建议先做“可选实验分支”，不要污染主闭环。
