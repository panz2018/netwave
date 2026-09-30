# Proposal

## Why

`typescript/src/` 目前只有手写 `.mjs`/`.cjs`/`.js` 壳 + 手写 `index.d.ts`，
契约在 `index.d.ts` 与壳内 JSDoc 各写一遍会漂移，CJS 壳是 ESM 壳的手工翻译版；
类型门禁 `tsc --noEmit` 靠 `checkJs: false` + `exclude: ["test"]` 双重豁免才绿，
形同虚设。源码化为 typed TS 后由打包器自动生成多格式产物与 `d.ts`，
消除双份维护并让类型门禁真实生效。

## What Changes

- `typescript/src/` 五个手写壳改写为 TS 源码：`types.ts`（收编 `index.d.ts`
  契约，成为公共类型单一来源）、`index.node.ts`、`index.browser.ts`、
  `worker.ts`、`standalone.ts`；删除手写 `index.d.ts` 与壳内重复的
  `@returns` JSDoc（不留双份）。
- 接入 tsdown（已钉 `typescript@6`，dts × TS7 不兼容）：`dist/` 壳与
  `index.d.ts`/`index.d.mts` 全部由 tsdown 生成；napi/wasm glue 保持
  external 不进 bundle。
- `package.json` 新增 `build` 脚本（tsdown）；`publish_shell.mjs` 瘦身为
  对 tsdown 产物做 `"../dist/"` → `"./"` specifier 重写 + 打印 dumped 清单
  （对拍脚本输出格式不变）。
- 类型门禁翻开：`tsconfig.json` 设 `checkJs: true`、`include` 加回 `test/`，
  删除两段豁免注释；`exports.types` 对齐双产物（`.d.ts` + `.d.mts`）。
- 测试入口与覆盖率 include 从 `.mjs`/`.cjs`/`.js` 切到 `.ts` 源码；
  覆盖率 `/* v8 ignore */` 豁免逐条保留理由（铁律七）。
- `exports.test.ts` 扩展断言：`dist/` 产物与 `exports` 逐一对齐。
- 文档同步：`typescript/README.md` Commands 更新为 tsdown 管线；
  `Plan/typescript源码化规划.md` 删除已落地章节（执行步骤、工具选型中
  已定案且已实现的部分），只留未执行任务。

## Capabilities

### New Capabilities

（无——纯构建/类型工具链重构，不新增能力。）

### Modified Capabilities

（无——公开 API 面、零拷贝契约、worker 语义全部冻结不变；
`zero-copy-roundtrip` 与 governance 的契约级修订随 worker 实现 change
另行同步，见 `Plan/typescript源码化规划.md`。）

本 change 为纯工具链重构（skip_specs），无 spec 级行为变化。

## Non-goals

- **worker 常驻架构不进本次**：浏览器端 `_` 同步逃生口不废止、`standalone.js`
  不改 IIFE、worker 不改为常驻托管——全部行为冻结，语义与现壳逐一对齐；
  契约级修订随 worker 实现 change 落地。
- 不启用打包器的 wasm 源码集成（compile/preserve 等模式），wasm 仍由
  wasm-pack `--target web` 自带 glue。
- 不动 napi/wasm 二进制构建管线（`build:native` / `build:wasm` 命令不变）。
- 不加 `noUncheckedIndexedAccess` / `exactOptionalPropertyTypes` 等额外
  strict 开关（收益低、测试噪音大）。
- 不动 biome 规则集。
- 不砍 CJS 产物（已拍板防御性保留）。

## Impact

- **受影响铁律**：铁律二（TDD——`exports.test.ts` 断言先扩展再改构建产物
  对齐）、铁律七（覆盖率 100% 硬约束——include 切 `.ts` 后阈值不降）。
- **代码**：`typescript/src/`（五壳 + `types.ts`，删 `index.d.ts`）、
  `typescript/test/`（import 路径与 typing 修复）、`typescript/scripts/publish_shell.mjs`。
- **配置**：`typescript/package.json`（scripts + exports）、
  `typescript/tsconfig.json`（checkJs/include）、新增 `typescript/tsdown.config.ts`、
  两个 vitest config 的 coverage include。
- **CI**：`.github/workflows/ci.yml` node job 的 build 步骤换为 tsdown 产物
  （napi/wasm 构建步骤保留在前）。
- **依赖**：`tsdown`（已在 devDependencies）、`typescript` 钉 `^6.0.3`。
- **对拍链**：`scripts/cross_compare.py` 四端对拍输出格式不变，须全绿回归。
