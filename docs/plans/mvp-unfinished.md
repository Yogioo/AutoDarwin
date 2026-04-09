# AutoDarwin 未完成项清单（收口版）

> 截止当前代码：T1~T7 主体已落地。这里仅保留仍待完善项。

## 1) Benchmark 与评测策略

- [x] `holdout` 已与 `core` 解耦并扩到 5 个 case（009~013）
- [x] evaluator 已统一执行基础 `constraints`（`forbid_paths` / `allow_paths` / `max_changed_files`）
- [x] 已支持复杂约束：`forbid_globs` / `allow_globs` / `max_changed_lines`
- [ ] 复杂约束仍可继续扩展（如命令白名单、按目录配额）

## 2) 结果可观测性

- [x] `results.jsonl` 已包含 mutation diff 摘要（added/removed/preview）
- [x] 已统一输出失败归因（`reason`/`reason_counts`）
- [x] 已有细分失败归因（如 `agent_command_not_found` / `agent_protocol_error` / `check_failed`）
- [ ] 仍可继续细化到 tool-error 子类和命令级标签

## 3) 稳定性治理

- [x] `--repeats N`
- [x] 保守接受：`candidate_mean > baseline_mean + margin`
- [x] 已支持 `--seed` 固定评测/进化流程种子（含 repeat seed 序列）

## 4) 运行与实验管理

- [x] 标准入口：`autodarwin.bat smoke|core|holdout|evolve|replay`
- [x] 回放：`replay.py --round-id/--candidate-hash`
- [x] 已支持 `--holdout-suite holdout --holdout-every N` 内建阶段验收

---

## 当前判断

- 已完成：MVP 闭环 + 分层套件 + 元数据消费 + 结构化日志 + 回放
- 待完善：失败归因细化、复杂约束扩展
