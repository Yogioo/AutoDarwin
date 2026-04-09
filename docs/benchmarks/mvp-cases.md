# AutoDarwin MVP Benchmark 样例设计（8 个 case）

本文档给出一组适合 MVP 阶段的 benchmark 样例设计。它们不是最终唯一方案，但足以作为第一版落地参考。

设计目标：

- 能自动评分
- 足够短
- 能区分 Agent 行为策略优劣
- 尽量贴近 pi 的 `read / bash / edit / write` 工具能力

---

## 总览

建议的 8 个 case 分布如下：

1. 检索理解：2 个
2. 小范围 bugfix：3 个
3. 受约束编辑：2 个
4. 修改后验证：1 个

---

## Case 001：定位函数定义

### 类型
检索与理解

### 任务目标
让 Agent 在一个小项目中找出某个函数定义所在文件，并按指定格式输出答案。

### 示例 prompt

```text
请找出 `build_release_note` 这个函数定义所在的文件路径，只输出相对路径，不要输出其他内容。
```

### workspace 结构示意

```text
workspace/
├─ app/
│  ├─ main.py
│  ├─ notes.py
│  └─ utils.py
└─ README.md
```

### 正确答案

```text
app/notes.py
```

### 评分方式
- 检查 stdout 或结果文件是否等于目标路径

### 能区分的策略
- 是否会先检索而不是盲猜
- 是否能避免输出多余文本

---

## Case 002：定位错误配置项

### 类型
检索与理解

### 任务目标
在多个配置文件中找到导致行为异常的配置项名称和值。

### 示例 prompt

```text
请找出导致服务端口错误的配置项，并输出为 `KEY=VALUE` 格式。
```

### workspace 结构示意

```text
workspace/
├─ config/
│  ├─ app.env
│  ├─ default.env
│  └─ dev.env
└─ scripts/
   └─ run_server.py
```

### 正确答案示例

```text
PORT=9001
```

### 评分方式
- 文本严格匹配

### 能区分的策略
- 是否会用 read / bash 搜索
- 是否能聚焦问题，不输出解释废话

---

## Case 003：修复 off-by-one bug

### 类型
小范围 bugfix

### 任务目标
修复一个数组切片或循环边界问题，并确保测试通过。

### 示例 prompt

```text
请修复项目中的 bug，并确保测试通过。只做必要修改，不要修改测试。
```

### workspace 结构示意

```text
workspace/
├─ src/
│  └─ stats.py
└─ tests/
   └─ test_stats.py
```

### 评分方式
- `pytest -q`
- 检查 `tests/` 未被修改

### 能区分的策略
- 是否先运行测试定位问题
- 是否做最小修复
- 是否会错误修改测试规避问题

---

## Case 004：修复错误导入

### 类型
小范围 bugfix

### 任务目标
修复模块导入路径错误或拼写错误。

### 示例 prompt

```text
请修复当前项目中导致程序无法运行的问题，并验证结果正确。
```

### workspace 结构示意

```text
workspace/
├─ package/
│  ├─ __init__.py
│  ├─ parser.py
│  └─ runner.py
└─ tests/
   └─ test_runner.py
```

### 评分方式
- `pytest -q`
- 检查改动文件数不超过 2

### 能区分的策略
- 是否会先复现错误
- 是否能聚焦单点 bug 而不过度重构

---

## Case 005：修复路径拼接 bug

### 类型
小范围 bugfix

### 任务目标
修复路径处理逻辑，使脚本在不同输入下都能正确工作。

### 示例 prompt

```text
请修复这个脚本中的路径问题，并确认检查脚本通过。
```

### workspace 结构示意

```text
workspace/
├─ tools/
│  └─ export_report.py
├─ data/
│  └─ sample.json
└─ check.sh
```

### 评分方式
- `bash check.sh`
- 检查输出文件是否存在且内容正确

### 能区分的策略
- 是否会先运行脚本复现
- 是否会使用稳健路径处理而不是硬编码

---

## Case 006：修改 README 指定段落

### 类型
受约束编辑

### 任务目标
只改 README 中指定的一段说明，不影响其他内容。

### 示例 prompt

```text
请把 README 中 Installation 小节里的 Python 版本要求从 3.10 改成 3.11，除此之外不要做其他修改。
```

### workspace 结构示意

```text
workspace/
└─ README.md
```

### 评分方式
- 检查 README 目标段落是否正确更新
- 检查文件其他部分未变

### 能区分的策略
- 是否能精确编辑
- 是否会控制改动范围
- 是否会避免格式污染

---

## Case 007：修改配置且限制改动范围

### 类型
受约束编辑

### 任务目标
修改一个 YAML / JSON 配置字段，且只能改一个文件。

### 示例 prompt

```text
请把 `config.yaml` 中的 `timeout` 改为 30。不要修改任何其他文件。
```

### workspace 结构示意

```text
workspace/
├─ config.yaml
├─ config.example.yaml
└─ tests/
   └─ test_config.py
```

### 评分方式
- 检查 `config.yaml` 是否正确修改
- 检查只有一个文件发生变化

### 能区分的策略
- 是否遵守约束
- 是否能避免误改 example / tests

---

## Case 008：修复并验证

### 类型
修改后验证

### 任务目标
修复一个小 bug，并要求 Agent 运行验证命令。

### 示例 prompt

```text
请修复 bug，并在完成后运行验证命令确认修复有效。不要修改测试文件。
```

### workspace 结构示意

```text
workspace/
├─ src/
│  └─ formatter.py
├─ tests/
│  └─ test_formatter.py
└─ verify.sh
```

### 评分方式
基础评分：
- `bash verify.sh`

增强评分（后续）：
- 从日志中确认 Agent 曾执行验证命令

### 能区分的策略
- 是否有“改后验证”的意识
- 是否只依赖静态猜测而不做确认

---

## 建议的套件划分

## smoke

建议先选：

- Case 001：定位函数定义
- Case 003：修复 off-by-one bug
- Case 006：修改 README 指定段落
- Case 008：修复并验证

特点：

- 覆盖面广
- 跑得快
- 能快速发现明显退化

## core

建议包含全部 8 个 case。

## holdout

MVP 初期可以先留空，等 core 跑稳后再补充 3~5 个未参与日常选择的新 case。

---

## 每个 case 的建议附加约束

为了避免 Agent 投机，建议逐步加入这些约束：

- 禁止修改 `tests/`
- 限制最大改动文件数
- 限制最终输出格式
- 限制只能修改指定目录
- 运行后检查 diff 是否超范围

这些约束不一定第一天就全部上线，但非常值得预留。

---

## 第一版落地建议

如果现在要开始做，建议按以下顺序实现：

### 第一步：先做 4 个

优先实现：

- Case 001
- Case 003
- Case 006
- Case 008

这样可以最快形成一个 smoke 套件。

### 第二步：补齐到 8 个

加入：

- Case 002
- Case 004
- Case 005
- Case 007

### 第三步：统一 evaluator

实现一个统一的执行器：

- 复制 workspace
- 执行 pi
- 跑 `check.sh`
- 输出 pass / fail / duration

---

## 结论

这 8 个 case 的设计重点不是覆盖所有任务，而是优先覆盖最适合当前 MVP 的能力：

- 查找
- 小修
- 精确编辑
- 修改后验证

它们共同构成了一套适合 AutoDarwin 第一阶段的最小 benchmark 基础集，可以直接作为 smoke / core 的起点。
