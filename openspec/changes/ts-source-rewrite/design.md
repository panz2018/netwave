# Design

## Context

`typescript/src/` 现为五个手写壳（`index.node.mjs` / `index.node.cjs` /
`index.browser.mjs` / `netwave.worker.js` / `standalone.js`）+ 手写
`index.d.ts`。构建现状：

- `build:native` 跑两遍 napi 各出 ESM/CJS glue 进 `dist/`，末尾跑
  `publish_shell.mjs` 把 `src/` 壳复制进 `dist/` 并把 `"../dist/` 重写为
  `"./`（LL-017：只改 `src/` 禁手改 `dist/`）。
- vitest 直接测 `src/`，coverage include 写死五个 `.mjs`/`.cjs`/`.js`。
- `tsconfig.json` 以 `checkJs: false` + `exclude: ["test"]` 豁免换 `tsc
  --noEmit` 绿；`exports.test.ts` 读 `src/` 源文本断言无 `export *`。
- tsdown `^0.23.0` 已在 devDependencies，无 config、无脚本引用；
  dts × TS7（tsgo）不兼容已实测，钉 `typescript@6` 可行且 esm dts 产物名为
  `.d.mts`。

约束：napi/wasm glue 保持 external；零拷贝契约（描述符、await 后重建视图、
worker transfer 表）不受影响；worker 常驻架构与浏览器 `_` 废止不进本次
（见 proposal Non-goals）。

## Goals / Non-Goals

**Goals:**

- `src/` 全部为 `.ts`，`types.ts` 是公共类型单一来源；手写 `index.d.ts`
  与壳内 `@returns` JSDoc 删除。
- `dist/` 壳与 dts 由 tsdown 一次生成，产物名与 `exports` 逐一对齐。
- 类型门禁真实化：`checkJs: true`、`test/` 进 include、TS2339 清零。
- 行为冻结：公开/内部导出面、worker 消息语义、standalone re-export 与现壳
  逐一等价（LL-007：测试只用公共面不受影响）。

**Non-Goals:**

- 见 proposal Non-goals（worker 常驻、IIFE standalone、wasm 源码集成、
  额外 strict 开关、CJS 砍除均不做）。
- 不改 `build:native` / `build:wasm` 命令本身。

## Decisions

### D1：tsdown 多 entry 单次构建，而非多次调用

`tsdown.config.ts` 单 config 声明全部 entry：
`index.node`（format `["esm","cjs"]`）、`index.browser`、`worker`、
`standalone`（各 `esm`）。`deps.neverBundle` 钉住
`../dist/index.node.generated.mjs`、`../dist/index.node.generated.cjs`、
`../dist/wasm-web/netwave_wasm.js`（`external` 旗标已弃用）。

替代方案：每 entry 一次 tsdown 调用——配置重复、构建时间翻倍，弃。

### D2：产物扩展名对齐——`fixedExtension` 双出 dts

`fixedExtension: true` 使 esm 产物为 `.mjs`、cjs 为 `.cjs`，与现有
`exports` 路径（`index.node.mjs`/`index.node.cjs`/`index.browser.mjs`）
零改动对齐；dts 双出 `.d.ts` + `.d.mts`，`exports.types` 指
`./dist/index.d.ts`（`types` 条件置于 `node` 之前）。worker/standalone 保持
`.js`（`exports` 子路径不变）。

替代方案：只出 `.d.mts`——CJS `require()` 消费者丢类型，弃；产物全改
`.js`——破坏 `exports.test.ts` 现有断言且 CJS/ESM 双格式无法同名，弃。

### D3：`publish_shell.mjs` 瘦身而非删除

tsdown 不重写 external specifier，`src/` 壳 import `"../dist/..."` 进
`dist/` 后路径错误。publish_shell 保留，职责缩为：对 tsdown 产物做
`"../dist/` → `"./` 重写 + 打印 dumped 绝对路径清单（对拍脚本依赖该输出
格式，LL-006）。不再做复制（产物本就在 `dist/`）。

替代方案：`src/` 直接写 `"./"` 相对路径——vitest 测 `src/` 时解析不到
glue（glue 只落 `dist/`），需另维符号链接，复杂度更高，弃。

### D4：覆盖率仍测 `src/`，include 切 `.ts`

vitest 继续直接跑 `.ts` 源（esbuild transform 由 vitest 内建承担），
coverage include 改为对应 `.ts` 文件；`/* v8 ignore */` 豁免随源码改写
逐条平移并保留理由注释（LL-025、铁律七）。100% 阈值不动。

替代方案：测 `dist/` 产物——覆盖率归因到生成代码，豁免失去意义，弃。

### D5：worker 的 `self` 全局类型

`worker.ts` 用 `/// <reference lib="webworker" />` 引入 worker 全局类型，
不引 `@types/webworker` 独立包；`standalone.ts`/`index.browser.ts` 用
`lib="dom"`。tsconfig `lib` 显式列 `["ES2022","DOM","DOM.Iterable"]`，
worker 文件靠三斜线指令覆盖 `self` 声明。

### D6：`exports.test.ts` 断言扩展（TDD，铁律二）

先扩展断言（RED）：`dist/` 产物清单存在性 + `exports` 每个目标路径实际
存在 + dts 双产物存在；再改构建使其 GREEN。`src/` 文本断言（无 `export *`）
文件名单改为 `.ts`。

## Risks / Trade-offs

- [tsdown 对 `import.meta.url` 相对 wasm 路径的处理改变语义] → web glue
  路径保持 external import 原样输出，构建后跑 `test:wasm` 全套件验证
  node/vitest 下 wasm 加载不回归。
- [dts 生成面与手写 `index.d.ts` 有出入（如 `_` 逃生口的 `@internal` 丢失）]
  → `types.ts` 中 `@internal` 注释写在导出符号上，构建后人工比对
  `dist/index.d.ts` 导出面与旧手写版一致。
- [checkJs 翻开后 test/ 暴露存量类型错误超出预期] → 属预期收益；逐条修
  测试文件（补 `NetwaveBuffer` 标注引用），不放宽门禁（LL-003）。
- [publish_shell specifier 重写漏网产物] → 重写后 grep `dist/` 中残留
  `"../dist/` 必须为空，加进验证步骤。
- [TS7 dts 兼容性未知] → 本 change 钉 `typescript@6`；源码化完成后在
  Plan/ 保留"重测 TS7 dts"未执行项，兼容则升回。

## Migration Plan

单 PR 落地：改写 → 本地四闸门（tsc/vitest×2/cross_compare）→ CI 同构验证。
回滚 = revert 该 PR（`src/` 手写壳与 `publish_shell.mjs` 旧版随 git 恢复，
无数据/接口迁移）。

## Open Questions

（无——worker 常驻相关的待定项均属 worker 实现 change，不在本 change 范围。）
