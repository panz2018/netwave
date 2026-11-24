# Design

## Context

动机见 proposal.md - Why。当前状态约束：

- worker（`browser/src/netwave.worker.ts`）静态 import `coverage-dump.ts`，并在
  `onmessage` 里有三条 `control` 分支（`dumpCoverage`/`driveCoverage`/`stubFetch`）、
  顶层 `globalThis.__netwaveWasmInstance = wasmInstanceSlot` 赋值、`covDir` 探针与
  instrumented import 分支——这些只在覆盖率链下有意义，却随 tsdown 内联进发布产物。
- vitest（node pool 与 browser mode）跑的是 `src/`，**不经过 tsdown**；tsdown 只产
  发布物。故任何"仅影响发布产物"的构建手段对测试零风险。
- 真实浏览器里排空 wasm 计数器只能在 worker realm 做（vitest setupFiles 进不了
  app 创建的 Worker），所以 control 分支必须存在于某个 worker 构建里——不能整体
  移出 worker。

## Goals / Non-Goals

**Goals:**

- 发布产物 `browser/dist/netwave.worker.js` 零覆盖率/测试代码。
- 测试链（node unit + e2e + rust lcov）行为不变、阈值不变。
- 测试资产（入口脚本、coverage-dump）归位到 `browser/` 内。

**Non-Goals:**

- 不改 worker control 协议语义、不改 e2e/unit 测试逻辑。
- 不引入第二份 worker 构建产物（tests 消费 src，新产物无人消费）。

## Decisions

### D1：编译期常量 `__NETWAVE_COVERAGE__` + tree-shaking，而非独立测试 bundle

worker 源码用 `if (__NETWAVE_COVERAGE__)` 守卫所有覆盖率专用代码；tsdown 发布构建
`define: { __NETWAVE_COVERAGE__: "false" }`，两个 vitest 配置 `define: { ...: "true" }`。
tsdown 默认 `minify: 'dce-only'` 删死分支，`coverage-dump.ts`（无顶层副作用）随之被
ESM tree-shaking 整模块摇掉。

- 备选 A（独立测试 bundle）：tests 跑 src，新 bundle 无人消费，纯增负担——否。
- 备选 B（`import.meta.env.VITE_*`）：语义是运行时 env，不如编译期常量诚实；裸 define
  与 Vue/React `__DEV__`、tsdown `import.meta.TSDOWN_PRODUCTION` 惯例一致——选裸 define。
- 实证：vite 顶层 `define` 经 `createWorkerPlugins` 继承进 worker 配置，vitest browser
  mode 走同一 vite client transform 管线，`define` 均到达 worker；tsdown `define` 转发
  Rolldown `transform.define`，对同配置块内所有 entry（含 worker named entry）生效。

### D2：守卫必须覆盖顶层副作用，不止死分支

DCE 只删 `if (false)` 块，不删顶层副作用。故 `globalThis.__netwaveWasmInstance = ...`
赋值与 `covDir` 探针 MUST 一并包进守卫（或移入守卫内的初始化路径），否则连同
`wasmInstanceSlot` 残留发布产物。

### D3：tsdown `define` 加在 worker 所在配置块

`browser/tsdown.config.ts` 是数组多配置，tsdown 不跨数组项共享 `define`。worker 是
第二个配置对象的 named entry，`define: { __NETWAVE_COVERAGE__: "false" }` MUST 加在
该配置对象上（壳配置块不含 worker，可不加）。

### D4：发布闸门落 publish_shell.mjs 末尾

`browser/scripts/publish_shell.mjs` 本就是发布产物后处理归属地（现改写 import 路径）。
末尾 grep `dist/netwave.worker.js`，命中 `dumpCoverage|__cov|NETWAVE_WASM_DIR` 即非零
退出——把"发布物纯净"升级为构建期强制。

### D5：check_ci.py 委托识别

根 `test:<seg>` 值若匹配 `pnpm -C <pkg> <cmd>`，改校验 ci.yml 含该委托命令字符串
（`pnpm -C <pkg> <cmd>`），替代原 `bash scripts/run/test_<seg>.sh` 匹配。其余非委托
根脚本维持原逻辑。

注：委托识别仅当值以 `pnpm -C` 前缀（后接空格）开头才触发。

## Risks / Trade-offs

- [tsdown 版本不摇掉无副作用 import] → D4 发布闸门当场拦截，构建即失败暴露问题；
  必要时给 worker 配置块加 `treeshake: { moduleSideEffects: false }`。
- [守卫漏包某处顶层副作用] → D4 闸门 grep `__cov`/`NETWAVE_WASM_DIR` 覆盖实例槽与
  探针符号，漏包即红。
- [check_ci.py 委托识别误判其他根脚本] → 仅当值以 `pnpm -C` 前缀开头才走委托分支，
  其余保持原 `bash scripts/run/test_<seg>.sh` 匹配，影响面限于 `test:browser`。
