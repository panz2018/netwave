# Proposal

## Why

`extract-browser-test-chain` 归档后的 apply 态体检（Plan/体检发现-extract-browser-test-chain.md）
登记了 `browser/test/coverage-dump.ts` 的 stale 自指路径；本会话实测确认同类死引用共三处，
全部是 wasm→browser 迁移（`5b4db41`、`ab39881`）遗留：注释指向已不存在的 `test/wasm/` 路径，
或整个文件（`typescript/test/vite-env.d.ts`）已成孤儿。死引用误导首次读码者，须一次清扫干净。

## What Changes

- `browser/test/coverage-dump.ts:3` 注释：删去指向不存在的 `test/wasm/coverage-dump.ts`
  的历史指针，只留当前契约（独立成模块、dump 臂只在插桩实例执行故不入 v8 分母）。
- `browser/vitest.e2e.config.ts:4` 注释：「test/wasm/** runs unmodified here」改为实际
  include 口径（`test/unit/**` + `test/e2e/**`）。
- 删除孤儿文件 `typescript/test/vite-env.d.ts`：`typescript/` 下已无 `?raw` 使用者
  （唯一使用者 `worker.test.ts` 已迁至 `browser/test/unit/`，browser 侧有同名声明），
  删除不影响 tsc 类型门。
- 删除 `Plan/体检发现-extract-browser-test-chain.md`：发现项全部被本 change 吸收，
  Plan/ 不留终态记录。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——本 change 只改注释与删孤儿文件，无 spec 级行为变化；`.openspec.yaml` 设
`skip_specs: true`。）

## Impact

- 注释：`browser/test/coverage-dump.ts`、`browser/vitest.e2e.config.ts`
- 删除：`typescript/test/vite-env.d.ts`、`Plan/体检发现-extract-browser-test-chain.md`
- 不触碰：构建配置、CI、公开 API、测试逻辑；archive 内历史工件（冻结记录）不动。
- 受影响铁律：无（不涉代码行为）。

## Non-goals

- 不修 `openspec/changes/archive/` 内的历史 `test/wasm` 引用（冻结记录，追溯靠 git log）。
- 不处理其他 `Plan/体检发现-*` 文件的登记项（属各自 change 的登记面）。
- 不顺手改进被触碰文件的其余注释或格式。

## Prior art

- `browser/test/vite-env.d.ts`：修正过口径的同名声明已存在于 browser 侧，本次删除
  typescript 侧孤儿即对齐该现存写法。
- `Plan/体检发现-extract-browser-test-chain.md`：本 change 的发现登记与证据来源。

## 专家增补

- 收尾以 `grep -rn "test/wasm"`（排除 `openspec/changes/archive/`）验证活文件清零，
  防同类死引用漏网——具体为 `browser/test/coverage-dump.ts`、
  `browser/vitest.e2e.config.ts`、`typescript/test/vite-env.d.ts` 三处之外无残留。

## 已定裁决

- `三处一起修`：#1 coverage-dump 注释、#2 e2e 配置注释、#3 vite-env 孤儿文件同场清扫，
  同一迁移遗留不拆两次。
- `删指针留契约`：#1 不改为现存兄弟文件实名，直接删历史指针只留当前契约，
  实名会随下次迁移再烂掉。
- `e2e注释改实glob`：#2 注释口径改为实际 include（`test/unit/**`、`test/e2e/**`）。
- `删孤儿文件`：#3 整删 `typescript/test/vite-env.d.ts`（typescript 下无 ?raw 使用者）。
- `新开微小change`：结论进 `fix-browser-test-chain-stale-refs` 承载，不并入他处。
- `Plan体检文件整删`：`Plan/体检发现-extract-browser-test-chain.md` 修完即整篇删除。
- `grep清零验证`：收尾验证 = archive 外 `test/wasm` 引用 grep 清零。
- `归档态体检跳过`：本 change 归档时跳过 health-check spec 的 archive 态只读体检
  （人工拍板 2026-11-24）；apply 态体检（tasks 2.6）不受影响，照跑。
