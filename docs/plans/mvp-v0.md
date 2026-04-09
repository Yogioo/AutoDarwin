# AutoDarwin MVP v0 设计文档

## 1. 项目目标

AutoDarwin 的第一阶段目标不是构建一个完整的“可进化 AI Agent 平台”，而是先做出一个**最小可运行闭环**：

- 以 **pi** 作为 Agent 基础运行框架
- 以 **固定 benchmark** 作为评测环境
- 以 **单一可变文件** 作为 Agent 的“基因”
- 以 **keep / discard** 的方式进行最简单的进化选择

一句话定义：

> 让系统能够自动改写 `.pi/SYSTEM.md`，并通过 pi 在固定 benchmark 上运行 Agent，完成可比较、可回滚、可持续迭代的进化闭环。

---

## 2. 为什么选择 pi 作为基础框架

选择 pi 的原因很明确：它已经提供了 Agent 运行中最昂贵、最通用的基础能力。

pi 已经具备：

- 模型接入与切换
- 会话管理
- 内置工具能力：`read`、`bash`、`edit`、`write`
- `AGENTS.md` / `.pi/SYSTEM.md` / prompts / skills / extensions 等上下文机制
- SDK / RPC / CLI 三种集成方式

这意味着 AutoDarwin 不需要自己重写：

- 模型调用层
- 工具调用层
- 会话管理层
- 基础 Agent 交互框架

因此，AutoDarwin 的关注点可以集中在：

- benchmark 设计
- 评测器设计
- 变异策略
- 选择策略
- 日志与版本演化

这与 MVP 极简主义高度一致。

---

## 3. MVP 设计原则

### 3.1 极简优先

第一版只验证一件事：

> “基于 pi 的 Agent，是否能在固定评测环境中通过自动修改自身行为规则获得可衡量提升？”

### 3.2 不重造 pi

AutoDarwin 把 pi 当作运行内核，不在 v0 阶段重写其已有能力。

### 3.3 固定环境，限制变量

MVP 必须保证实验可比较，因此需要固定：

- benchmark 数据集
- 任务输入
- 评测逻辑
- 工具集合
- 运行预算
- 模型配置（至少在同一轮实验中固定）

### 3.4 单一可变体

第一版只允许进化一个文件：

- `.pi/SYSTEM.md`

这样做的目的：

- 缩小搜索空间
- 降低不稳定性
- 提高结果可解释性
- 简化回滚和 diff 分析

### 3.5 快速反馈

每轮评测必须足够短，才能形成有效的自动进化回路。

### 3.6 Keep / Discard

第一版不做复杂种群算法，只做最简单的：

- 新版本更好：保留
- 新版本不如当前版本：丢弃

---

## 4. MVP 范围定义

## 4.1 v0 要做的事

- 使用 pi 作为 Agent runtime
- 固定一组 benchmark 任务
- 建立自动评分机制
- 把 `.pi/SYSTEM.md` 作为唯一可变“基因”
- 建立 mutation -> run -> evaluate -> select 的主循环
- 记录每一轮实验结果

## 4.2 v0 不做的事

为了保持极简，以下内容明确不进入 MVP：

- 多 Agent swarm
- 种群并行进化
- 自修改 extension / tool 代码
- 长期记忆系统
- 自动生成技能体系
- 自定义 TUI
- 复杂工作流编排
- 动态工具注入优化
- 训练型 RL / 蒸馏 / 自监督数据闭环

这些都属于未来阶段内容。

---

## 5. 整体架构

建议采用：

> **外部控制器 + pi 执行内核**

也就是：

### pi 负责

- 执行 Agent 推理
- 调用工具
- 在项目上下文中完成任务
- 读取 `.pi/SYSTEM.md` 作为行为规则

### AutoDarwin 控制器负责

- 选择 benchmark
- 运行实验
- 评分
- 变异 `.pi/SYSTEM.md`
- 保留或回滚版本
- 记录 lineage 和实验日志

这种架构的优点：

- 结构清晰
- 对 pi 侵入低
- 初始开发成本低
- 后续可平滑升级到 SDK / extension 方案

---

## 6. 推荐目录结构

```text
AutoDarwin/
├─ benchmarks/
│  ├─ cases/
│  │  ├─ case_001.json
│  │  ├─ case_002.json
│  │  └─ ...
│  └─ evaluator.py
├─ .pi/
│  └─ SYSTEM.md
├─ runner.py
├─ mutate.py
├─ evolve.py
├─ results.jsonl
└─ docs/
   ├─ plans/mvp-v0.md
   └─ plans/future-plan.md
```

---

## 7. 核心模块说明

## 7.1 `.pi/SYSTEM.md`

这是 v0 唯一允许进化的文件。

它代表当前 Agent 的行为策略，也就是系统的“基因”。

内容重点包括：

- 如何理解任务
- 如何拆解任务
- 如何选择工具
- 如何限制无效操作
- 如何做最小修改
- 如何进行自检与验证
- 如何组织最终输出

### 为什么先只进化 SYSTEM prompt

相比修改代码、技能、扩展，修改 `.pi/SYSTEM.md` 的好处是：

- 改动简单
- 风险低
- 成本低
- 适合快速迭代
- 易于归因

这非常适合 MVP 阶段。

---

## 7.2 `runner.py`

职责：运行一次 benchmark。

建议输入：

- benchmark case
- 当前 `.pi/SYSTEM.md`
- 模型配置
- 运行预算

建议输出：

- 是否成功
- 任务得分
- 耗时
- token / cost（如可获取）
- 关键日志

### 推荐集成方式

MVP 阶段优先推荐：

- **Python 控制器 + pi CLI / RPC**

原因：

- 接入快
- 少写 TypeScript glue code
- benchmark / evaluator 更容易快速迭代

如果未来需要更强控制力，再切到 pi SDK。

---

## 7.3 `benchmarks/cases/*.json`

每个 benchmark case 定义一个固定任务。

建议字段示例：

```json
{
  "id": "case_001",
  "name": "find-and-fix-small-bug",
  "prompt": "请修复项目中的一个小 bug，并确保测试通过。",
  "workspace": "fixtures/case_001",
  "expected": {
    "type": "command",
    "command": "pytest -q",
    "success_exit_code": 0
  }
}
```

原则：

- 任务固定
- 输入固定
- 可自动评测
- 尽量短小
- 能区分策略优劣

---

## 7.4 `benchmarks/evaluator.py`

职责：统一评分。

第一版不追求复杂，只追求稳定和可比较。

建议先支持：

- 成功 / 失败
- 基础得分
- 耗时惩罚
- 成本惩罚（如果可取到）

示意：

```text
fitness = 成功率 * 100 - 平均耗时 * a - 平均成本 * b
```

如果前期成本不好取，先简化为：

```text
fitness = 成功率
```

---

## 7.5 `mutate.py`

职责：生成 `.pi/SYSTEM.md` 的候选变体。

MVP 阶段只做最简单 mutation：

- 调整行为规则表述
- 删掉冗余规则
- 加入更明确的工具使用约束
- 加入更明确的验证策略
- 优化输出格式规则

### 不建议 v0 使用的复杂 mutation

- 多版本并行组合
- 自动结构重写 prompt 树
- 根据轨迹做层级反思回写
- 联动修改 skill / extension / prompt template

v0 只需能稳定产生一个候选版本即可。

---

## 7.6 `evolve.py`

职责：驱动完整进化循环。

主流程建议为：

1. 读取当前基线 `.pi/SYSTEM.md`
2. 跑 baseline benchmark
3. 生成一个候选变体
4. 用候选变体重新跑 benchmark
5. 计算 fitness
6. 如果更优则保留，否则回滚
7. 记录到 `results.jsonl`
8. 继续下一轮

这是 AutoDarwin v0 的核心。

---

## 8. 基因定义

MVP 阶段，基因只定义为：

- `.pi/SYSTEM.md` 的文本内容

换句话说，当前系统的“可进化对象”不是代码，而是：

- Agent 的行为规则
- 工具使用偏好
- 计划与验证策略

这样做与 autoresearch 的核心思想一致：

- 固定环境
- 限制变异面
- 快速比较
- 优胜保留

---

## 9. 评测设计

## 9.1 benchmark 数量

MVP 建议：

- 先从 **5~20 个任务** 开始

理由：

- 足够快
- 易于调试
- 能快速验证进化是否有效

## 9.2 benchmark 类型建议

如果 AutoDarwin 面向 coding / automation Agent，可优先选择：

- 文件检索
- 命令执行
- 小范围代码修改
- 错误修复
- 输出格式约束
- 简单 repo 理解任务

## 9.3 benchmark 原则

- 自动可判分
- 输入输出明确
- 成本低
- 稳定复现
- 尽量减少主观评分

---

## 10. 评分函数建议

MVP 阶段优先简单稳定。

### 最简版本

```text
fitness = 成功率
```

### 稍完整版本

```text
fitness = 成功率 * 100 - 平均耗时 * a - 平均成本 * b
```

后续才考虑加入：

- 工具误用率
- 崩溃率
- 无效编辑率
- 输出质量分
- 自检质量分

第一版一定要避免 reward 过于复杂，否则会难以调试。

---

## 11. 实验日志设计

建议使用 `results.jsonl` 记录每轮实验，便于后续分析。

每条记录建议包含：

```json
{
  "iteration": 12,
  "parent_version": "v0.0.11",
  "candidate_version": "v0.0.12",
  "status": "keep",
  "fitness": 73.5,
  "success_rate": 0.8,
  "avg_duration": 12.4,
  "avg_cost": 0.0,
  "mutation_summary": "强化先读后改和最小编辑原则",
  "timestamp": "2026-04-09T10:00:00Z"
}
```

状态建议只保留三类：

- `keep`
- `discard`
- `crash`

---

## 12. 版本与选择策略

MVP 只采用单 lineage 策略：

- 当前版本为唯一父代
- 每轮只产生一个候选子代
- 候选优于父代则替换父代
- 否则直接丢弃

这本质上是最简单的 hill climbing。

优点：

- 实现简单
- 成本低
- 行为清晰
- 易于调试

缺点：

- 容易陷入局部最优

但这是可以接受的 MVP 取舍。

---

## 13. 为什么不优先用 extension

pi 的 extension 非常强大，但在 v0 阶段不作为重点。

原因：

- extension 会把问题从“验证进化闭环”变成“设计平台能力”
- 增加系统复杂度
- 提高调试成本
- 延缓第一个可运行版本

因此，v0 的原则是：

- **优先使用 pi 原生能力**
- **尽量避免额外 extension**
- 如需 extension，也只允许非常薄的一层辅助能力

---

## 14. 推荐技术路线

## 14.1 控制器语言

推荐：

- Python 作为 benchmark / evolve 主控

原因：

- 编写 evaluator 更快
- 处理 JSON / 文件 / subprocess 更方便
- 与实验驱动风格天然匹配

## 14.2 pi 集成方式

推荐顺序：

1. **CLI / RPC**
2. SDK
3. Extension 深度集成

MVP 优先用 CLI / RPC，先把闭环跑起来。

---

## 15. 第一阶段交付标准

当满足以下条件时，可认为 AutoDarwin MVP v0 成立：

1. 存在一套固定 benchmark
2. baseline Agent 可稳定运行并得分
3. `.pi/SYSTEM.md` 可自动生成候选变体
4. 候选变体可被自动评测
5. 系统能自动执行 keep / discard
6. 实验结果可记录、可回放、可比较

如果这 6 点完成，就说明 AutoDarwin 已经具备“可进化 Agent”的最小生命体征。

---

## 16. 当前结论

AutoDarwin 的正确起点不是“大而全”，而是：

- 以 pi 作为稳定内核
- 以 `.pi/SYSTEM.md` 作为唯一可变基因
- 以 benchmark 作为固定环境
- 以 keep / discard 作为最小进化机制

这个设计具备三个明显优点：

- 足够小，可以尽快落地
- 足够清晰，便于观察和纠偏
- 足够通用，后续可自然演化为更完整的平台

这就是 AutoDarwin v0 的设计基线。
