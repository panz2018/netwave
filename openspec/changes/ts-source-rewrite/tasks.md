# Tasks

## 1. RED：先扩展断言（铁律二）

- [x] 1.1 扩展 `typescript/test/native/exports.test.ts`：新增 `dist/` 产物
      清单断言（`index.node.mjs`/`index.node.cjs`/`index.browser.mjs`/
      `standalone.js`/`netwave.worker.js`/`index.d.ts`/`index.d.mts` 存在）
      与 `exports` 每目标路径实际存在断言；`export *` 文本扫描文件名单改
      `.ts` → 验证：新断言 RED（dts 双产物尚不存在、`.ts` 名单不存在）

## 2. TS 源码改写（行为冻结）

- [x] 2.1 新建 `typescript/src/types.ts`：收编 `index.d.ts` 全部契约
      （`NetwaveBuffer`、公共 async 动词签名、`_` 逃生口 `@internal` 标注）
      → 验证：`tsc --noEmit` 通过
- [x] 2.2 `index.node.mjs`/`index.node.cjs` → `index.node.ts`（单源码，
      CJS 由 tsdown 产出）：napi glue import 保持 `"../dist/..."` external，
      返回值标注 `NetwaveBuffer`，删 `@returns` JSDoc → 验证：
      `tsc --noEmit` 通过，导出面与旧壳逐一等价
- [x] 2.3 `index.browser.mjs` → `index.browser.ts`：wasm glue import 保持
      external，`isNode` 探测与 `wasmSource` 补类型，`/* v8 ignore */` 豁免
      逐条平移并保留理由（LL-025）→ 验证：`tsc --noEmit` 通过
- [x] 2.4 `netwave.worker.js` → `worker.ts`（见 design
      [worker 的 `self` 全局类型](./design.md#worker-的-self-全局类型)）
      与 `standalone.js` → `standalone.ts`：transfer 表与 re-export 面逐行
      等价 → 验证：`tsc --noEmit` 通过
- [x] 2.5 删除手写 `src/index.d.ts` 与旧 `.mjs`/`.cjs`/`.js` 壳 →
      验证：`grep -rn "index.d.ts" typescript/src` 无残留引用

## 3. tsdown 接入与发布管线

- [x] 3.1 新建 `typescript/tsdown.config.ts`：多 entry + `format` 按 design
      [tsdown 多 entry 单次构建](./design.md#tsdown-多-entry-单次构建而非多次调用)
      与[产物扩展名对齐](./design.md#产物扩展名对齐fixedextension-双出-dts)
      （`fixedExtension: true`、dts 双出）、`deps.neverBundle` 钉三个 glue
      → 验证：`pnpm exec tsdown` 产出 `dist/` 七产物（1.1 清单）
- [x] 3.2 `publish_shell.mjs` 瘦身为 specifier 重写 + dumped 清单（见 design
      [`publish_shell.mjs` 瘦身而非删除](./design.md#publishshellmjs-瘦身而非删除)），
      `package.json` 新增 `build` 脚本（tsdown → publish_shell）→
      验证：grep `typescript/dist` 中残留 `"../dist/` 必须为空；dumped
      输出为绝对路径（LL-006）
- [x] 3.3 `package.json` `exports.types` 对齐 `.d.ts`（`.d.mts` 同存）→
      验证：1.1 断言转 GREEN

## 4. 类型门禁与测试入口切换

- [x] 4.1 `tsconfig.json`：`checkJs: true`、`include` 加回 `test/`、删两段
      豁免注释 → 验证：`pnpm typecheck` 含 test 全绿（TS2339 清零，LL-003
      禁放宽门禁）
- [x] 4.2 两个 vitest config 的 coverage include 切 `.ts` 源码 → 验证：
      `pnpm test:native --coverage` / `test:wasm --coverage` 100% 达标
      （铁律七）
- [x] 4.3 `pnpm check:ts`（Biome + tsc）全绿 → 验证：退出码 0

## 5. 回归对拍与 CI

- [x] 5.1 跨绑定对拍回归（LL-024 先重建 node/wasm）：
      `pnpm -C typescript build:native && build:wasm && pnpm check:cross`
      → 验证：逐 bit + 容差 + 篡改自检全绿
- [x] 5.2 CI node job build 步骤换 tsdown 管线（napi/wasm 构建保留在前，
      先本地模拟每格，LL-004）→ 验证：本地按 ci.yml 步骤序全绿

## 6. 文档同步

- [x] 6.1 更新 `typescript/README.md` Layout 与 Commands（tsdown 管线、
      `pnpm build`）→ 验证：README 命令逐条实跑存在（LL-005、LL-008）
- [x] 6.2 `Plan/typescript源码化规划.md` 删除已落地章节（执行步骤 0–2、
      已实现的工具选型细节），只留未执行项（worker 实现同步、TS7 dts
      重测、四端对拍常态化）→ 验证：`pnpm check:md` 退出码 0
