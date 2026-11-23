# Proposal

## Why

浏览器端代码当前散落在两处：wasm-bindgen Rust crate 在 `typescript/wasm/`，而
worker、主线程传输壳与对应测试散在 `typescript/src` 与 `typescript/test`，且
crate/目录/命令/CI job 仍叫 `wasm`（实现技术名）而非平台名 `browser`。这使
"浏览器端"没有自我完整的归属，难以独立理解、测试与更新。本变更把浏览器端
立成顶层 `browser/` 自包含包，让 typescript 回归"node + 薄封装"的单一职责。

## What Changes

- 新建顶层 `browser/` 包（与 `core/`、`python/`、`typescript/` 平级），内含
  Rust glue crate + worker + 主线程传输壳 + 浏览器端测试。
- **BREAKING**（内部命名）：crate `netwave-wasm` → `netwave-browser`；目录
  `typescript/wasm/` → `browser/`；wasm-pack 产物 `netwave_wasm.js` →
  `netwave_browser.js`。
- **BREAKING**（命令名）：根 `test:wasm` → `test:browser`；typescript 包内
  `test:wasm` → `test:unit`、`test:browser` → `test:e2e`；目录
  `test/wasm/` → `test/unit/`、`test/browser/` → `test/e2e/`。
- **BREAKING**（CI）：job `wasm` → `browser`、artifact `coverage-wasm-*` →
  `coverage-browser-*`；技术名（`wasm32-unknown-unknown`、`wasm-pack`、
  `wasm-opt`）一律保留。
- worker（`netwave.worker.ts`）、传输壳（`index.browser.ts`）、worker 协议
  类型（`types.ts`）及对应测试从 typescript 迁入 browser。
- browser 自产全部浏览器产物（壳/`./standalone`/`./worker`/wasm/constants/dts）
  落 `browser/dist/`，结构上可独立发布。
- typescript 经 pnpm workspace 依赖消费 browser：browser build 产全部浏览器
  dist，typescript build 合并进 typescript/dist（对外单包）；typescript 只保留
  node + 薄封装 + 集成测试。
- Cargo workspace members、`pnpm-workspace.yaml` 同步纳入 `browser/`。

## Capabilities

### New Capabilities

<!-- 无新建能力：worker 分发等跨端契约留在 api-contract，子项目边界归
     workspace-layout（见 grilling Q7 裁决）。 -->

### Modified Capabilities

- `workspace-layout`: 平铺 monorepo 结构新增顶层 `browser/` 子项目；
  typescript 由"单包含 native+wasm 两构建目标"改为"node + 薄封装，经
  workspace 依赖消费 browser"；exports 条件与产物归属随之更新。
- `ci-matrix`: 浏览器端 CI job 与覆盖率 artifact 由 `wasm` 更名为 `browser`，
  技术名保留；typescript job 维持自建 browser 产物（不引入跨 job 依赖）。

## Impact

- 代码：`typescript/wasm/`、`typescript/src/{netwave.worker.ts,index.browser.ts,types.ts}`、
  `typescript/test/{wasm,browser}/`、`typescript/vitest.{wasm,browser}.config.ts`、
  `typescript/package.json`、`typescript/tsdown.config.ts`。
- 配置：根 `Cargo.toml` members、`pnpm-workspace.yaml`、根 `package.json`
  scripts、`.github/workflows/ci.yml`、`scripts/run/test_wasm.sh`/`test_ts.sh`。
- spec：`workspace-layout`、`ci-matrix`（delta）。
- 受影响铁律：铁律八（wasm 只运行在 worker、主线程零 wasm）、铁律十一
  （壳不计算）——本变更只搬位置不改这两条语义。

## Non-goals

- 不把 core 里的浏览器 dispatch（`call_namespace`/`resources.rs`/start 钩子）
  搬出 core——browser 的 Rust glue crate 本轮仍是空 force-link 壳，dispatch
  搬迁留作后续独立 change。
- 不把 native（node 的 napi crate）从 `typescript/native/` 独立出来。
- 不改覆盖率链内部命名（`test_wasm.sh`、`coverage-wasm.lcov`、
  `coverage_gate.py` 文件匹配）——只改对外名（crate/目录/命令/CI job）。
- 不让 browser 独立发 npm（本轮 `private: true`，仅被 typescript 消费）。
- 不新建 browser spec。

## Prior art

- 仓库内既有平台命名先例：core feature `browser`、`typescript/src/index.browser.ts`、
  `typescript/test/browser/`、`vitest.browser.config.ts`、`package.json`
  `exports.browser` 条件——本变更把落后的 crate/目录/命令名追平到该词汇。
- python/node 绑定的 newtype 自包含模式（`python/src/lib.rs`、
  `typescript/native/src/lib.rs`）作为"下游自我完整"的参照。

## 专家增补

- 建议把 `browser` 包的构建顺序（browser → typescript）写进
  `workspace-layout` 的 workspace 清单 scenario，防后续有人误加跨 job CI
  依赖（grilling Q17 实证：两 job OS 矩阵相同但并行独立，typescript job
  自建 browser 产物供 cross dump 复用）。
- 建议 `types.ts`（worker↔壳私有协议）随 worker 进 browser，typescript
  薄封装若需类型从 browser 包再导出取，避免协议类型两处真相源。

## 已定裁决

- `browser顶层包`：浏览器端立成与 core/python/typescript 平级的自包含目录
  （Rust glue + worker + 壳 + 测试）。
- `browser命名`：crate/目录/产物统一用平台名 browser，技术名 wasm32/wasm-pack/
  wasm-opt 保留。
- `壳随worker进browser`：index.browser.ts、netwave.worker.ts、types.ts 及测试全进 browser。
- `typescript承载node加薄封装`：只留 node + 薄封装 + 集成测试，构建期合并
  browser 产物（壳直接导入、wasm 资产由 typescript 工具发射），发布物自包含。
- `browser内测试改名`：test:wasm→test:unit、test:browser→test:e2e，目录同步。
- `根命令与CI改名`：根 test:wasm→test:browser、CI job wasm→browser。
- `覆盖率链内部命名不动`：本轮只改对外名，内部命名留后续。
- `不新建browser-spec`：边界写 workspace-layout，措辞改 ci-matrix，worker 分发留 api-contract。
- `native本轮不动`：仍住 typescript/native/。
- `workspace依赖消费`：typescript 经 pnpm workspace 依赖 import browser，产物归 browser/dist。
- `glue空壳`：browser Rust crate 本轮仍是空 force-link 壳，dispatch 留 core。
- `browser私有包`：本轮 private，不独立发 npm。
- `browser自包含可独立发布`：browser 自产全部浏览器产物（壳/standalone/
  worker/wasm/constants/dts），未来砍 node 后 browser 一字不改即可单独发布。
- `CI各自自建产物`：typescript job 维持自建 browser 产物，不加 needs:browser 跨 job 依赖。
- `跳过archive态体检`：本 change 归档完成后的 archive 态全项目只读体检跳过
  （health-check spec「archive 态」），apply 态被触碰文件体检照常执行。

## 后续未完成项（本 change 不做，留待独立 change）

- dispatch 搬迁：core 里的 `call_namespace`/`resources.rs`/start 钩子搬进
  browser crate，使 glue 不再是空 force-link 壳（本 change Non-goals）。
- native 独立：`typescript/native/` napi crate 拆成对等独立子项目。
- 覆盖率链内部改名：`test_wasm.sh`、`coverage-wasm.lcov`、`coverage_gate.py`
  文件匹配等内部命名由 wasm→browser（本 change 只改对外名）。
- 发布形态：browser/native 是否独立发 npm、typescript 壳包发包策略（阶段 E）。
