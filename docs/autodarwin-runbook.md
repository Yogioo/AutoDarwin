# AutoDarwin 运行命令（MVP）

## 日常

```bat
autodarwin.bat core
autodarwin.bat evolve --suite core --rounds 5
autodarwin.bat evolve --suite core --rounds 20 --holdout-suite holdout --holdout-every 5
autodarwin.bat evolve --suite core --rounds 20 --repeats 3 --seed 42
```

## 快速回归

```bat
autodarwin.bat smoke
```

## 阶段验收

```bat
autodarwin.bat holdout
```

## 回放

```bat
autodarwin.bat replay --round-id 3
autodarwin.bat replay --candidate-hash <hash>
```

## 约定

- 日常选择：`core`
- 快速回归：`smoke`
- 阶段验收：`holdout`
