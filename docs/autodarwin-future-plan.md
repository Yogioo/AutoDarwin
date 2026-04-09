# AutoDarwin 未来计划文档

## 1. 文档目标

本文档描述 AutoDarwin 在 MVP v0 完成后的未来演进方向。

原则上，未来规划不应破坏当前的核心路线：

- 先做小闭环
- 再做可扩展结构
- 最后做复杂进化系统

因此，后续发展建议遵循：

> **从单体 prompt 进化，逐步升级到多层策略进化、种群进化、再到可扩展的 Agent 生态系统。**

---

## 2. 总体路线图

建议把 AutoDarwin 的未来拆成 4 个阶段：

### Phase 0：MVP 闭环

目标：

- 跑通基于 pi 的单体 Agent 进化闭环
- 只进化 `.pi/SYSTEM.md`
- 固定 benchmark
- keep / discard

### Phase 1：单体 Agent 增强

目标：

- 提升评测能力
- 提升 mutation 质量
- 增强可观测性
- 让单体 Agent 进化更稳定

### Phase 2：多层策略进化

目标：

- 不再只进化 SYSTEM prompt
- 开始进化 skill、workflow、memory policy、tool policy
- 形成可组合的 Agent 策略层

### Phase 3：种群与生态系统

目标：

- 多 lineage 并行
- 多候选并发评估
- 自动分工与 specialization
- 向“可进化 Agent 组织”升级

---

## 3. Phase 1：单体 Agent 增强计划

这一阶段仍然围绕单个 Agent 展开，但会比 MVP 更稳定、更可分析。

## 3.1 Benchmark 体系升级

### 目标

从“少量手工任务”升级到“更可信的小型评测集”。

### 计划

- 扩充 benchmark 数量，从 5~20 个增加到 20~100 个
- 按任务类型分组：
  - 代码修改
  - 代码理解
  - 文件定位
  - 命令执行
  - repo 操作
- 区分 smoke benchmark 与 full benchmark：
  - smoke：快速筛选
  - full：最终决策

### 预期价值

- 提高评估稳定性
- 减少偶然性提升
- 更容易发现策略退化

---

## 3.2 评分函数升级

### 当前问题

MVP 的评分函数会很简单，通常只看成功率，最多加入耗时 / 成本。

### 未来升级方向

加入更多行为质量指标：

- 工具调用效率
- 无效 bash 比例
- 无效编辑比例
- 重试次数
- 崩溃率
- 输出规范性
- 自检有效性

### 目标

把“结果对错”升级为“行为质量 + 结果质量”的综合评估。

---

## 3.3 Mutation 策略升级

### 当前问题

MVP 的 mutation 可能只是简单改写 prompt。

### 未来方向

引入分类型 mutation：

- 压缩型：删掉冗余规则
- 强化型：加强成功模式
- 探索型：尝试全新策略
- 修复型：针对失败样本修补 prompt
- 重排型：调整行为规则优先级

### 后续可增加的机制

- 基于失败样本的 targeted mutation
- 基于轨迹的 prompt repair
- 基于胜出版本的局部重组

---

## 3.4 实验可观测性升级

### 计划

增加更完整的实验元数据：

- 每个 benchmark case 的详细结果
- 每轮 diff 摘要
- 失败原因归档
- 平均工具调用次数
- 总 token 消耗
- 每轮版本 lineage

### 未来可视化方向

- 进化曲线图
- 版本对比视图
- benchmark 热点失败分布
- lineage 树视图

---

## 3.5 稳定性治理

### 目标

让进化结果不只“偶尔赢”，而是“稳定赢”。

### 计划

- 同一候选版本重复评测多次
- 对 benchmark 做随机种子控制
- 加入波动容忍区间
- 采用保守接受策略，避免噪音误判

这一步会让 AutoDarwin 从“实验玩具”走向“研究工具”。

---

## 4. Phase 2：多层策略进化

这一阶段，AutoDarwin 的进化对象将从单一 prompt 升级为多层结构。

## 4.1 从单一 SYSTEM prompt 到多层基因

未来可进化对象包括：

- `.pi/SYSTEM.md`
- `.pi/prompts/*.md`
- `.pi/skills/*/SKILL.md`
- workflow 配置
- memory 策略
- tool usage policy
- reflection policy

### 目标

从“一个大 prompt”进化为“多模块策略系统”。

---

## 4.2 Skill 进化

pi 的 skill 机制很适合 AutoDarwin 的第二阶段。

### 方向

- 把特定任务能力抽成独立 skill
- benchmark 不再只比较 SYSTEM prompt
- 开始比较 skill 是否触发合理、描述是否准确、步骤是否高效

### 可能做法

- 进化 `SKILL.md` 的说明和步骤
- 优化 skill 描述，提升触发准确性
- 拆分大 skill 为小 skill
- 合并重复 skill

### 价值

这会让进化从“整体行为优化”变成“模块化能力优化”。

---

## 4.3 Workflow / Policy 进化

未来可以把 Agent 工作流显式化，例如：

- 先检索再计划
- 先复现再修改
- 修改后必须验证
- 失败后最多重试几次
- 大任务是否先写计划文件

这些规则可以从 prompt 中抽离，成为独立 policy。

### 目标

形成：

- prompt 层
- workflow 层
- validation 层
- reflection 层

多层共同进化。

---

## 4.4 引入轻量 extension

虽然 MVP 尽量不依赖 extension，但在第二阶段，extension 会变得非常有价值。

### 候选方向

- 记录详细工具轨迹
- 自动生成实验摘要
- 提供受控的中间状态采集
- 动态调整 active tools
- 提供 benchmark 辅助工具

### 原则

extension 仍然应该服务于“可观测性和可控性”，而不是过早做复杂 UI。

---

## 5. Phase 3：种群进化与多 Agent 组织

这是 AutoDarwin 真正向“可进化 Agent 生态”迈进的阶段。

## 5.1 从单 lineage 到多 lineage

当前策略是：

- 单父代
- 单子代
- keep / discard

未来升级为：

- 保留 top-k 版本
- 每轮从多个父代产生多个子代
- 并行评测
- 用更优者继续繁殖

### 价值

- 避免局部最优
- 增加探索多样性
- 支持 specialization

---

## 5.2 种群角色分化

未来版本可以引入不同“进化角色”：

- Explorer：激进尝试新策略
- Refiner：局部微调已有好版本
- Simplifier：删掉无效复杂度
- Repairer：针对失败模式修复

这些角色不一定是多个运行时 Agent，也可以是多个 mutation 策略。

---

## 5.3 多 Agent 协作进化

更远一步，可以把 AutoDarwin 从“进化一个 Agent”扩展为：

- 进化一个 Agent 组织
- 每个 Agent 负责不同子任务
- 不同 Agent 拥有不同 prompt / skill / tool policy

例如：

- Researcher：分析失败原因
- Mutator：生成候选变体
- Evaluator：执行 benchmark
- Archivist：记录实验和 lineage

这与 autoresearch 的“研究组织”思路更接近。

---

## 5.4 自动 specialization

随着 benchmark 类型变多，可能出现不同 Agent 在不同任务上更强。

未来可以考虑：

- 针对 benchmark 类型训练 / 进化专精体
- 自动选择某类任务的最优 Agent 配置
- 形成“路由 + 专精 Agent”的系统

这会比单一通用 Agent 更强。

---

## 6. 更长期的演化方向

## 6.1 自我分析与自我归因

未来 AutoDarwin 不仅要知道“哪个版本更好”，还要知道：

- 为什么更好
- 是哪条规则起作用
- 哪类任务收益最大
- 哪类任务退化了

### 可探索方向

- 自动 diff 解释
- 失败模式聚类
- 成功模式抽象
- prompt rule attribution

---

## 6.2 自动生成训练素材

未来可以基于 benchmark 轨迹生成：

- 失败案例库
- 成功案例库
- 反思样本
- prompt 改写样本

这些素材可以进一步用于：

- mutation 提示增强
- 离线分析
- 甚至蒸馏成更稳定的策略模板

---

## 6.3 从 Prompt 进化到 Code 进化

MVP 只进化 `.pi/SYSTEM.md`，但未来可能逐步开放：

- skill 文件
- prompt templates
- extension 配置
- extension 代码
- benchmark 路由逻辑

这一步必须很谨慎，因为一旦开放代码级进化，系统复杂度会显著上升。

建议顺序：

1. Prompt
2. Skill
3. Workflow config
4. Extension config
5. Extension code

---

## 6.4 Online / Offline 混合进化

未来可以把进化分成两类：

### Online

- 用最新 benchmark 实时评估
- 快速迭代当前版本

### Offline

- 用历史轨迹做回放
- 大规模分析失败原因
- 从历史版本中寻找被误丢弃的有价值思路

这会让 AutoDarwin 更像一个持续研究系统。

---

## 7. 工程化路线建议

## 7.1 数据层

未来建议逐步建设：

- benchmark 数据规范
- 统一结果 schema
- 版本 lineage schema
- case-level 详细记录
- 失败日志归档

## 7.2 可视化层

未来可增加：

- Web dashboard
- 实验比较页面
- 版本演化树
- benchmark 细分统计

## 7.3 包化与可复用

如果 AutoDarwin 成熟，可以考虑：

- 把与 pi 集成的能力打包成项目模板
- 把 benchmark / evaluator 做成可复用模块
- 把 mutation / selection 做成策略接口

最终甚至可以考虑做成：

- 一个 pi package
- 或一个独立的 AutoDarwin toolkit

---

## 8. 里程碑建议

## Milestone 1：闭环成立

- baseline 可跑
- benchmark 可评
- mutation 可产生候选
- keep / discard 可执行

## Milestone 2：结果稳定

- 评测波动可控
- 日志完整
- 能看到连续改进

## Milestone 3：模块化进化

- SYSTEM prompt 外，再支持 skills / prompts / policy

## Milestone 4：种群化

- top-k 存活
- 并行候选评测
- lineage 树

## Milestone 5：Agent 组织化

- 多角色协作
- specialization
- 自动实验分工

---

## 9. 决策原则

未来不管走到哪一步，都建议坚持以下原则：

### 9.1 先可测，再可进化

没有稳定 benchmark，就不要扩大进化对象。

### 9.2 先少变量，再多变量

先保证单一变量的提升可信，再开放更多可变层。

### 9.3 先记录，再优化

没有足够日志和轨迹，就不要急着做复杂算法。

### 9.4 先模块化，再自动化

把 prompt、skill、workflow、tool policy 分层清楚后，再做多层联合进化。

### 9.5 始终保持回滚能力

任何自动进化系统，都必须保留清晰的版本与回滚机制。

---

## 10. 总结

AutoDarwin 的未来不应该一开始就追求庞大，而应该沿着一条非常清晰的路线前进：

1. **先用 pi 做底座，完成单体 Agent 的极简进化闭环**
2. **再增强 benchmark、mutation、评分、日志与稳定性**
3. **然后把进化对象扩展到 skills、workflow、tool policy 等多层结构**
4. **最后再进入种群进化、多 Agent 协作和 Agent 生态系统阶段**

如果 MVP 是 AutoDarwin 的“第一颗细胞”，那么未来计划的目标就是：

> 把这颗细胞逐步演化成一个真正具备适应、分化、选择和持续改进能力的 Agent 生命体。
