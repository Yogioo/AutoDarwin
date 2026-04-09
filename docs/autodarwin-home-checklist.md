# AutoDarwin 到家后执行清单

> 目的：先确认当前版本可稳定运行，再决定是否做并发评测改造。

## 0. 同步代码

```bat
git pull
```

如果本地还没配置远端，先设置后再 pull/push。

---

## 1. 快速健康检查（必须先做）

```bat
autodarwin.bat smoke
```

预期：
- `passed = 4`
- `crashed = 0`

---

## 2. 主集检查（确认稳定性）

```bat
autodarwin.bat core
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

## 6. 下一步计划（并发评测）

若第 1~3 步都通过，下一步改造目标：
- 在 `benchmarks/evaluator.py` 增加 `--jobs N`
- case 级并发执行（多进程）
- 保持结果格式兼容（`--json` 输出不变）

验收目标：
- `smoke/core` 结果与串行一致
- 总耗时明显下降
