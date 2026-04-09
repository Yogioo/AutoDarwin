# AutoDarwin 运行手册（当前）

## 常用命令

```bat
autodarwin.bat smoke --jobs 2
autodarwin.bat core-ui
autodarwin.bat holdout --jobs 4
```

## 人类友好评测（推荐）

```bat
autodarwin.bat core-ui
```

说明：
- 自动并发评测（默认 core=4 jobs）
- 自动打开 Web UI
- 每个 case 展示 Prompt / 任务 / Agent 输出 / Check 输出 / 原始日志
- 完成后自动弹出总结窗口

## 手动模式（脚本化/CI）

```bat
python benchmarks/evaluator.py core --jobs 4 --progress off --progress-file .autodarwin/progress.jsonl --case-log-dir .autodarwin/case-logs --json
python tools/progress_web.py --file .autodarwin/progress.jsonl --case-log-dir .autodarwin/case-logs --open-browser
```

## 进化

```bat
python evolve.py --suite core --rounds 3 --pi-cmd "cmd /c pi"
```

## 回放

```bat
autodarwin.bat replay --round-id 3
autodarwin.bat replay --candidate-hash <hash>
```
