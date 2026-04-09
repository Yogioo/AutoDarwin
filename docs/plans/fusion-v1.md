# AutoDarwin 融合开发候选方案（v1.1）

最后更新：2026-04-09  
状态：**候选方向，非当前主线**；当前主线以 `docs/status.md` 为准。  
定位：在不堆简单 case 的前提下，落地“**主 Agent 编排 + 多 sub-agent 并行 research + 主 Agent 总结**”范式。

---

## 1. 核心决策

采用你提出的工程范式，但控制风险：

- **架构一步到位**：一次性设计主从并行 research 骨架
- **能力分档启用**：`off / light / full`，默认 `off`
- **评测先行**：任何模式都必须可 A/B、可回滚、可复盘

一句话：不是慢慢试错拼架构，而是先把架构定好，再逐档放量。

---

## 2. 目标流程（v1.1）

新流程：

`评测 baseline -> 主Agent下发research任务 -> 多sub-agent并行探索 -> 主Agent汇总摘要 -> mutation -> 评测candidate -> keep/discard -> 回放`

其中：
- 主 Agent：Orchestrator + Synthesizer（下发/汇总/决策）
- sub-agent：多角度并行（代码、风险、验证、策略）

---

## 3. 模式分档

## 3.1 off（默认）
- 不做 research
- 完全保持现有 evolve 行为

## 3.2 light（首个上线档）
- 并行 2 个 sub-agent
- 每个 1 轮、短输出
- 主 Agent 生成 <= 20 行摘要

## 3.3 full（实验档）
- 并行 3~4 个 sub-agent
- 可做 1~2 轮补充探索
- 主 Agent 结构化总结（发现/证据/建议/风险）

---

## 4. sub-agent 角色（建议）

最小角色集（先 2 个，后扩展）：

1. **Code Explorer**：定位关键文件、实现路径、潜在修改点  
2. **Failure Analyst**：基于 recent fail/reason_counts 给出失败归因

full 档可再加：

3. **Risk Reviewer**：评估改动风险与回滚点  
4. **Validation Planner**：给出最小验证路径（先测什么、后测什么）

---

## 5. 预算与门控（必须）

为避免 token/时延失控，强制预算：

- `--research-mode off|light|full`（默认 off）
- `--research-subagents 2`（light 默认 2）
- `--research-max-rounds 1`（默认 1）
- `--research-budget-lines 20`（主摘要上限）
- `--research-timeout-sec 45`（每个 sub-agent 超时）

任一子任务失败：
- 不中断主流程
- 记日志并降级（继续用可用结果）

---

## 6. 数据记录（results.jsonl）

新增字段（可选）：

- `research_mode`
- `research_subagents`
- `research_summary`
- `research_findings`（裁剪版）
- `research_failures`（超时/异常）
- `research_cost_hint`（摘要行数、子任务数）

目标：保证 replay/归因可用，不做复杂 telemetry。

---

## 7. case 策略（少而精）

不扩大量简单 case，仅新增 **1~2 个高价值 research 型 case**：

- 跨文件定位 + 小修改 + 自验证
- 单步猜测难稳定通过
- 有明确 pass/fail 边界

用于检验并行 research 是否“真提升”。

---

## 8. 里程碑

## M1（1-2 天）：架构骨架接入

交付：
- evolve 增加 `off/light/full` 三档开关
- light 模式支持 2 个 sub-agent 并行 + 主总结
- 不影响旧命令

验收：
- `off` 行为与当前一致
- `light` 能稳定跑完 3 轮

## M2（2-3 天）：有效性验证

交付：
- 1 个 research 型 case
- off vs light A/B 报告（repeats>=3）

验收：
- pass_rate 不下降
- crash 不上升
- avg_duration 增幅可控（建议 <20%）

## M3（1 天）：full 实验档与回放

交付：
- full 档可跑
- replay 支持展示 research 记录

验收：
- round 级可复盘
- 能看见“哪些 research 结论影响了 mutation”

---

## 9. 最小改动清单

1. `evolve.py`
   - 新增 research 参数与分档逻辑
   - 在 mutation 前调用并行 research
   - 写入 results.jsonl 新字段

2. `mutate.py`
   - 支持接收 `research_summary` 作为附加上下文

3. `replay.py`
   - 展示/对比 research 相关字段（如有）

4. `benchmarks/cases/*`
   - 新增 1~2 个 research 型高价值 case

---

## 10. 命令建议

基线：
```bat
autodarwin.bat core --jobs 4
```

A/B（off）：
```bat
python evolve.py --suite core --rounds 3 --repeats 3 --research-mode off --pi-cmd "cmd /c pi"
```

A/B（light）：
```bat
python evolve.py --suite core --rounds 3 --repeats 3 --research-mode light --research-subagents 2 --research-budget-lines 20 --pi-cmd "cmd /c pi"
```

实验（full）：
```bat
python evolve.py --suite core --rounds 3 --repeats 3 --research-mode full --research-subagents 4 --research-max-rounds 2 --research-budget-lines 40 --pi-cmd "cmd /c pi"
```

---

## 11. 继续/停止门槛

继续推进条件：
- light 相比 off：收益稳定且成本可控
- full 相比 light：有额外收益，否则不默认启用

不满足则：
- 默认回退 `off`
- 保留骨架与日志字段，等待下一轮优化

---

## 12. 一句话总结

> v1.1 不是“盲目一步到位开满并行”，而是“架构一步到位 + 能力分档上线 + 数据驱动启用”。
