# AutoDarwin MVP 未完成项细化与并行开发评估

基于 `docs/autodarwin-mvp-unfinished.md` 的细化任务清单。

## 1. 任务拆解（按优先级）

## P0（建议先完成）

### T1. 补齐 benchmark 资产（case + suite）
- 目标：补齐 MVP 8 个 case，新增 `core` 与 `holdout`。
- 产出：
  - `benchmarks/cases/case_002/`
  - `benchmarks/cases/case_004/`
  - `benchmarks/cases/case_005/`
  - `benchmarks/cases/case_007/`
  - `benchmarks/suites/core.txt`
  - `benchmarks/suites/holdout.txt`
- 验收：
  - `python benchmarks/evaluator.py smoke --list`
  - `python benchmarks/evaluator.py core --list`
  - `python benchmarks/evaluator.py holdout --list`
  - 三个 suite 均可加载，无缺失 case
- 主要改动文件：`benchmarks/cases/**`, `benchmarks/suites/**`

### T2. evaluator 消费 case 元数据
- 目标：让 `case.json` 的关键字段真正生效。
- 必做：
  1. `workspace` 字段生效（不再硬编码 `workspace/`）
  2. `check.type` 分发（至少支持 `script`，并为后续类型留接口）
  3. `tools` 透传到 runner（runner 接受并转换为 `pi --tools ...`）
- 验收：
  - 修改某 case 的 `workspace` 名称后仍可跑通
  - `check.type=script` 正常执行
  - 指定 `tools` 时，runner 的 pi 参数可见
- 主要改动文件：`benchmarks/evaluator.py`, `runner.py`

### T3. 结构化结果日志（results.jsonl）
- 目标：替代/并行 `results.tsv`，落地结构化记录。
- 必做字段：
  - round_id, suite, baseline_score, candidate_score, status
  - parent_hash, candidate_hash
  - case_results（最少含 case_id/status/duration）
  - timestamp
- 验收：
  - `evolve.py` 每轮产出 1 条有效 JSONL
  - 可被 Python `json.loads` 全量解析
- 主要改动文件：`evolve.py`（可选：保留 `results.tsv` 兼容）

### T4. 运行规范命令化
- 目标：统一 smoke/core/holdout 执行入口。
- 产出：
  - `autodarwin.bat` / README 中增加标准命令示例
  - 约定：日常选择用 `core`，快速回归用 `smoke`
- 验收：
  - 文档与脚本参数一致
- 主要改动文件：`autodarwin.bat`, `docs/*.md`

---

## P1（P0 后推进）

### T5. 稳定性治理（重复评测 + 保守接受）
- 目标：降低单次评测噪声。
- 必做：
  - 支持每个候选重复评测 N 次（默认 1）
  - 接受条件改为：`candidate_mean > baseline_mean + margin`
- 验收：
  - `--repeats N` 可用
  - 日志中记录 mean/std
- 主要改动文件：`evolve.py`（可能少量改 `evaluator.py`）

### T6. 评分扩展（主排序 + 次排序）
- 目标：在 pass_rate 一致时用次指标排序。
- 建议：
  - 主排序：pass_rate
  - 次排序：avg_duration（更低更好）
- 验收：
  - 同 pass_rate 时选择耗时更低版本
- 主要改动文件：`benchmarks/evaluator.py`, `evolve.py`

### T7. 实验回放能力
- 目标：按 round 复跑并对比结果。
- 产出：
  - `replay.py`（输入 round_id 或候选 hash）
- 验收：
  - 能重放指定轮次并输出新旧差异
- 主要改动文件：`replay.py`（新增）

---

## 2. 并行开发判断

结论：**可以并行，但要按“低耦合任务包”拆分；共享文件（`evaluator.py`/`evolve.py`）不宜多人同时改。**

## 可并行（建议立即并行）
1. **任务包A：Benchmark 资产包（T1）**
   - 仅改 `benchmarks/cases/**` 与 `benchmarks/suites/**`
   - 与核心代码冲突小
2. **任务包B：运行规范文档/脚本（T4）**
   - 仅改 `autodarwin.bat` + docs
   - 与 A/C 冲突小
3. **任务包C：回放脚手架（T7）**
   - 新增文件为主，冲突小

## 不建议并行（建议串行）
1. **T2 evaluator 元数据生效**
2. **T6 评分扩展**

原因：都重度修改 `benchmarks/evaluator.py`，并行会高冲突。

3. **T3 结构化日志**
4. **T5 稳定性治理**

原因：都重度修改 `evolve.py`，应串行。

---

## 3. 推荐 sub-agent 分工（最小冲突版）

- **SA-1（资产）**：T1
- **SA-2（执行层）**：T2 → T6（同一人连续做，避免 evaluator 冲突）
- **SA-3（进化控制层）**：T3 → T5（同一人连续做，避免 evolve 冲突）
- **SA-4（工具与文档）**：T4 + T7

合并顺序建议：
1) SA-1 + SA-4 先合并
2) SA-2 合并
3) SA-3 最后合并（依赖 evaluator 输出字段）

---

## 4. 是否可下发并行开发（最终判断）

**可以下发。**

但建议按上面的 4 个任务包下发，而不是按原始 7 个任务点直接分发。否则会在 `evaluator.py` 和 `evolve.py` 上产生高频冲突。

