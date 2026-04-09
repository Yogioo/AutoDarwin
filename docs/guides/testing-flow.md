# AutoDarwin 测试流程（并发 + Web UI）

## 1) 快速健康检查

```bat
autodarwin.bat smoke --jobs 2
```

目标：
- passed=4
- crashed=0

---

## 2) 主集（推荐 UI 模式）

```bat
autodarwin.bat core-ui
```

你会看到：
- 浏览器 Web UI 自动打开
- 每个 case 的任务细节、Prompt、Agent 输出、Check 输出、原始日志
- suite 完成后弹出总结窗口

---

## 3) 主集（脚本模式）

```bat
python benchmarks/evaluator.py core --jobs 4 --progress off --progress-file .autodarwin/progress.jsonl --case-log-dir .autodarwin/case-logs --json
```

可单独打开 UI：

```bat
python tools/progress_web.py --file .autodarwin/progress.jsonl --case-log-dir .autodarwin/case-logs --open-browser
```

---

## 4) 验收与排障

- 结果 JSON：看 `pass_rate / reason_counts / case_results`
- case 详细日志：`.autodarwin/case-logs/<case_id>.log`
- API 自检：
  - `http://127.0.0.1:8765/api/state`
  - `http://127.0.0.1:8765/api/case?case_id=case_001`

---

## 5) 进化前最低门槛

- smoke/core 都稳定（无 crash）
- 无明显 timeout 热点
- 关键 case 日志可复现
