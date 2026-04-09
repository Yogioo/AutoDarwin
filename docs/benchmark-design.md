# AutoDarwin Benchmark 设计文档

## 1. 目标

AutoDarwin 的 Benchmark 不是为了评估“通用 AI 有多强”，而是为了评估：

> 当前这版基于 pi 的 Agent，在目标任务场景中是否比上一版更有效。

因此，Benchmark 的设计必须服务于进化闭环，而不是服务于通用排行榜。

MVP 阶段的 Benchmark 应该满足五个关键词：

- 小
- 稳
- 便宜
- 可自动评分
- 和目标任务强相关

---

## 2. 适用场景

当前 AutoDarwin 的第一版默认面向：

- coding agent
- repo task agent
- 本地自动化 agent

也就是说，Benchmark 优先覆盖这类能力：

- 理解项目结构
- 定位文件与代码
- 执行命令
- 修改文件
- 修复小 bug
- 修改配置
- 进行必要验证
- 控制改动范围

MVP 阶段不优先覆盖：

- 开放式问答
- 创意写作
- 数学推理
- 浏览器自动化
- 多模态任务
- 强依赖联网的任务

---

## 3. 核心设计原则

## 3.1 固定输入

每个 case 必须固定：

- prompt
- workspace 初始状态
- 工具集合
- 时间预算
- 评测方式

这样每一轮实验结果才可比较。

## 3.2 自动评分优先

MVP 阶段尽量避免使用 LLM 作为裁判。优先采用：

- shell 命令 exit code
- 单元测试
- 文件内容比对
- JSON schema 校验
- git diff 约束检查

## 3.3 case 足够短

每个 case 应尽量在几秒到几十秒内完成。过长会显著拖慢进化速度。

## 3.4 能区分策略优劣

好的 case 应该能够区分：

- 是否先读后改
- 是否选择正确工具
- 是否做最小修改
- 是否会主动验证
- 是否会避免无关编辑

## 3.5 封闭稳定

MVP 优先本地可复现环境：

- 尽量不联网
- 尽量少外部依赖
- 尽量少复杂环境变量
- 每个 case 都能独立运行

## 3.6 分层评测

建议把 Benchmark 拆成三层：

- `smoke`：快速回归，5 个左右
- `core`：日常进化主集，10~20 个
- `holdout`：阶段验收，不参与日常选择

---

## 4. 目录结构建议

```text
benchmarks/
├─ cases/
│  ├─ case_001/
│  │  ├─ case.json
│  │  ├─ workspace/
│  │  └─ check.sh
│  ├─ case_002/
│  │  ├─ case.json
│  │  ├─ workspace/
│  │  └─ check.sh
│  └─ ...
├─ suites/
│  ├─ smoke.txt
│  ├─ core.txt
│  └─ holdout.txt
└─ evaluator.py
```

说明：

- `cases/`：每个 benchmark case 独立目录
- `workspace/`：该 case 的初始项目副本
- `case.json`：case 元信息与运行要求
- `check.sh`：自动校验脚本
- `suites/`：定义各个测试集合
- `evaluator.py`：统一执行与汇总逻辑

---

## 5. case 结构建议

每个 case 至少包含以下文件：

### 5.1 `workspace/`

Agent 实际工作的目录。

运行时流程建议为：

1. 复制 `workspace/` 到临时目录
2. 在临时目录下写入当前候选版本的 `.pi/SYSTEM.md`
3. 用 pi 在该目录中执行任务
4. 执行 `check.sh`
5. 得到 pass / fail 与附加指标

### 5.2 `case.json`

建议字段：

```json
{
  "id": "case_001",
  "name": "fix-off-by-one",
  "description": "修复一个小 bug，并确保测试通过",
  "prompt": "请修复这个项目中的 bug，并确保测试通过。只做必要修改。",
  "workspace": "workspace",
  "max_seconds": 90,
  "tools": ["read", "bash", "edit", "write"],
  "check": {
    "type": "command",
    "command": "bash check.sh"
  },
  "constraints": {
    "forbid_paths": ["tests/"],
    "max_changed_files": 2
  },
  "tags": ["bugfix", "python", "minimal-edit"]
}
```

### 5.3 `check.sh`

检查 case 是否完成。可以很简单，也可以包含额外约束。

示例：

```bash
#!/usr/bin/env bash
set -e
pytest -q
```

更严格的版本：

```bash
#!/usr/bin/env bash
set -e
pytest -q >/dev/null
python checker.py
```

---

## 6. 套件设计

## 6.1 smoke

用途：

- 快速验证运行链路
- 做轻量回归
- 在 mutation 频繁试错时减少成本

建议规模：

- 3~5 个 case

## 6.2 core

用途：

- 日常进化主 benchmark
- 作为 keep / discard 的主要依据

建议规模：

- 8~20 个 case

## 6.3 holdout

用途：

- 防止过拟合 core
- 做阶段性验收

建议规模：

- 5~10 个 case

---

## 7. 任务类型建议

MVP 阶段建议只覆盖四类任务。

## 7.1 检索与理解

测试 Agent 是否能快速定位关键信息。

例子：

- 找出某函数定义在哪个文件
- 找出导致某报错的配置项
- 找出某命令在哪里被调用

评分方式：

- 输出结果文本比对
- 结果文件比对

## 7.2 小范围 bugfix

最适合当前 pi 工具链。

例子：

- 修复 off-by-one
- 修复 import 错误
- 修复错误路径拼接
- 修复一个简单测试失败

评分方式：

- `pytest -q`
- 辅以禁止修改测试等约束检查

## 7.3 受约束编辑

测试 Agent 是否能控制改动面。

例子：

- 只修改 README 某一段
- 修改配置文件一个字段
- 补充 docstring
- 在不改接口的前提下小重构

评分方式：

- 文件内容检查
- diff 范围检查
- 格式检查

## 7.4 修改后验证

测试 Agent 是否会在修改后做验证。

例子：

- 修 bug 并运行测试
- 改配置后运行脚本确认输出
- 修改脚本后验证返回值

评分方式：

- 功能是否通过
- 后续可选增加“是否执行过验证命令”的轨迹分析

---

## 8. 评分策略建议

## 8.1 MVP 主评分

第一版建议极简：

```text
fitness = pass_rate
```

即：

- 每个 case：通过记 1，失败记 0
- 整个 suite：成功率即 fitness

## 8.2 后续扩展评分

当闭环稳定后，再引入次级指标：

```text
fitness = pass_rate * 100 - avg_duration * a - avg_cost * b
```

或采用分级排序：

1. 主排序：成功率
2. 次排序：平均耗时
3. 再次排序：平均成本

MVP 阶段不建议一开始引入太多复杂加权项。

---

## 9. 建议记录但暂不纳入主评分的指标

这些数据很有价值，但早期先用于观察，不直接决定 keep / discard：

- 总耗时
- 工具调用次数
- bash 次数
- edit 次数
- write 次数
- crash 次数
- diff 大小
- 是否执行验证命令
- 最终输出长度

这些会在后续帮助分析“为什么某个版本更好”。

---

## 10. 运行规范建议

为了保证 Benchmark 结果稳定，建议每个 case 运行时固定以下条件：

- 固定模型
- 固定 thinking level
- 固定工具集合
- 使用 `--no-session`
- 固定 cwd 为临时 workspace 根目录
- 每次从干净副本开始

建议流程：

1. 复制 case workspace 到临时目录
2. 写入候选 `.pi/SYSTEM.md`
3. 用 pi 跑 case prompt
4. 收集执行日志
5. 运行 `check.sh`
6. 记录结果

---

## 11. 避免过拟合的建议

随着进化轮数增加，Agent 可能逐渐过拟合到 `core` 集合。因此建议：

- 保留 `holdout` 集合，日常不参与选择
- 定期抽样做完整验收
- 新增少量 unseen case 验证泛化
- 不要让 mutation 过程直接接触 holdout case 详情

---

## 12. MVP 落地建议

如果现在开始实施，推荐顺序如下：

### 第一步
先做 8 个 case，覆盖 4 类任务：

- 2 个检索理解
- 3 个小 bugfix
- 2 个受约束编辑
- 1 个修改后验证

### 第二步
先实现最小 evaluator：

- 顺序执行 case
- 收集 pass / fail
- 计算 success rate

### 第三步
把 smoke / core / holdout 分出来：

- smoke：3~5 个
- core：8 个起步
- holdout：后续再补

---

## 13. 结论

AutoDarwin 的 Benchmark 设计重点不是“大而全”，而是：

- 让实验稳定可复现
- 让 case 能区分 Agent 策略差异
- 让评分尽量自动化
- 让单轮成本足够低

对于 MVP，最合适的 Benchmark 方案是：

- 每个 case 一个独立 workspace
- 一个 `case.json`
- 一个 `check.sh`
- pass / fail 为主评分
- smoke / core / holdout 三层管理

这样既足够简单，又足够支撑第一版进化闭环。
