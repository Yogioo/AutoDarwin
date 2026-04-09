# AutoDarwin 到家后执行清单

> 目的：先确认当前版本可稳定运行。默认优先并发评测（更快）；仅在需要逐条观察/多轮交互排障时再用串行。

## 0. 同步代码

```bat
git pull
```

如果本地还没配置远端，先设置后再 pull/push。

---

## 1. 快速健康检查（必须先做）

```bat
autodarwin.bat smoke --jobs 2
```

预期：
- `passed = 4`
- `crashed = 0`

---

## 2. 主集检查（确认稳定性）

```bat
autodarwin.bat core-ui
```

> `core-ui` 会自动开始评测并自动打开 Web UI（Windows，浏览器），多列显示每个 case 全量信息（Prompt/任务/聊天/日志）；全部完成后会弹出总结窗口。

手动模式（可选）：
```bat
autodarwin.bat core --jobs 4 --progress-file .autodarwin/progress.jsonl
python tools/progress_view.py --file .autodarwin/progress.jsonl
```

预期：
- `passed = 8`
- `crashed = 0`

---

## 3. 小轮数进化试跑（先保守）

Windows 下建议显式传 `pi` 命令，避免找不到可执行文件：

```bat
python evolve.py --suite core --rounds 3 --pi-cmd "cmd /c pi"
```

建议先不加 `--repeats`，先看链路是否稳定。

> 并发建议：常规回归优先 `--jobs N`。仅当你要盯单个 case 的完整会话输出时，用 `--jobs 1`。

---

## 4. 阶段验收（可选）

```bat
autodarwin.bat holdout
```

用于确认没有明显过拟合。

---

## 5. 记录结果（回家后给我）

请把以下信息发我：
1. smoke/core 的 `pass_rate`
2. evolve 3 轮是否跑完
3. 是否出现超时或卡慢（哪一轮、哪一个 case）

---

## 6. 并发评测使用约定（已支持）

- 默认优先并发：`autodarwin.bat core --jobs 4`
- 串行排障：`autodarwin.bat core --jobs 1`
- JSON/自动化采集：`python benchmarks/evaluator.py core --jobs 4 --json`

进度显示：
- 默认 `--progress auto`：仅在交互终端显示单行进度，不刷屏
- 强制开启：`--progress on`
- 关闭：`--progress off`
- 旁路可视化：`--progress-file .autodarwin/progress.jsonl` + `python tools/progress_view.py`
