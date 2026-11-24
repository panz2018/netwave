# 体检发现：extract-browser-test-chain（apply 态只读体检）

被触碰文件全文语义考古 + 四维扫描结论。发现项附文件+行号+证据，等点名再改，
不阻塞本 change。

## 发现 1：stale 自指路径（被触碰文件，不在本次 diff 行内）

- 文件：`browser/test/coverage-dump.ts:3`
- 证据：注释写「for the same reason as `test/wasm/coverage-dump.ts`」，但
  `test/wasm/coverage-dump.ts` 不存在——wasm→browser 迁移后真实同目录文件是
  `browser/test/unit/coverage-dump.ts` 与 `browser/test/e2e/coverage-dump.ts`。
- 性质：迁移遗留的旧路径（早于本 change 即 stale），本次把该文件从 `src/`
  移到 `test/` 时未触碰此行，故暴露。
- 建议改法：把 `test/wasm/coverage-dump.ts` 改为现存兄弟文件实名，或删去该
  历史指针只留当前契约（"独立成模块、dump 臂只在插桩实例执行故不入 v8 分母"）。
- 去向：等点名；属精准修改原则下"不顺手改 diff 外旧注释"，故仅登记。

## 其余被触碰文件：无适用发现

`netwave.worker.ts`、`global.d.ts`、`vite-env.d.ts`、`publish_shell.mjs`、
`test.sh`、三处 vitest/tsdown 配置、`check_ci.py`——全文扫描无门禁词表外的
语义考古（历史归因/口径变更叙述），注释均陈述当前契约。
