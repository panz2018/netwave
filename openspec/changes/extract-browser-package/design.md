# Design

## Context

见 proposal.md - Why。当前 wasm-bindgen crate 在 `typescript/wasm/`（crate
`netwave-wasm`，空 force-link 壳），worker/传输壳/协议类型在 `typescript/src/`，
浏览器端测试在 `typescript/test/{wasm,browser}/`。core 仍持有浏览器 dispatch
（`call_namespace`/`resources.rs`/start 钩子），本变更不动它。CI 的 wasm job 与
typescript(node) job OS 矩阵相同但并行独立，各自 build wasm 产物（node job 的
产物还供 cross dump 复用）。

## Goals / Non-Goals

**Goals:**

- 浏览器端立成顶层 `browser/` 自包含包，依赖单向指向 core。
- typescript 回归 node + 薄封装单一职责，经 workspace 依赖消费 browser。
- 平台名 `browser` 统一对外命名（crate/目录/命令/CI job），技术名保留。

**Non-Goals:**

- 不搬 core 里的 dispatch（glue crate 本轮仍空壳）。
- 不动 native、不改覆盖率链内部文件名、不独立发 browser。

## Decisions

### D1：browser 为顶层包，Rust glue + TS worker/壳/测试混装一个目录

替代方案：browser 只作 Rust crate、TS 文件另放。选混装——"自我完整"要求
worker↔壳↔测试同处一个可独立理解/测试的边界；拆开等于把 postMessage 两端
分两个项目。代价：browser 目录同时有 Cargo.toml 与 package.json，构建链
（cargo→wasm-pack→vitest）较长，由包内 scripts 收口。

### D2：构建期合并——壳直接导入 + typescript 工具发射 wasm 资产

browser 私有不发 npm（见 proposal 已定裁决 `browser私有包`），故发布物必须自包含。机制分两类产物：

- **TS 壳**（index.browser.ts、worker）：typescript 的 tsdown 直接 import
  browser 包源码编译进 `typescript/dist`，不复制（tsdown 默认把 workspace
  依赖当 external，需把 `netwave-browser` 标为可打包）。
- **wasm 二进制 + glue.js + constants**：`.wasm` 无法被打包器塞进 JS，只能作
  文件进 dist。由 typescript 构建的 asset 步骤从 `browser/dist/` 读、发射进
  `typescript/dist`——方向是 typescript→browser，正确。

替代方案与否决：(a) browser 直接把产物写进 typescript/dist——依赖方向反了
（browser→typescript），破坏 browser 自包含，正是本次要消灭的耦合（现状
`wasm-pack --out-dir ../dist/wasm-web` 即此反模式，本次改掉）；(b) browser
也发 npm——撤 `browser私有包` 裁决，改动更大且违背"本轮不发 browser"。

`./standalone`、`./worker` 子路径归 typescript 产出（发布壳职责），从 browser
的 worker/壳源码编译。构建顺序：browser build → typescript build（workspace
依赖强制）。

### D3：CI 维持两 job 各自自建 browser 产物，不加 `needs: browser`

实证：两 job OS 矩阵相同但并行独立；node job 自建产物还供 cross dump 复用。
跨 job artifact 需按 matrix.os 配对下载、违背两 job "zero conditionals" 设计
原则，且把包依赖升级成 CI 串行依赖拖慢并行度。wasm build 不贵，重复构建成本
低于耦合。

### D4：测试改名 unit/e2e 而非 browser:unit/browser:e2e

browser 包内部 `browser:` 前缀冗余。`test:unit`（node 模拟）/`test:e2e`
（真浏览器）在 browser 包上下文自洽。根级仍用 `test:browser`（与 test:py/
test:ts 并列需平台名区分）。

### D5：覆盖率链内部命名本轮不动

`test_wasm.sh`、`coverage-wasm.lcov`、`coverage_gate.py` 匹配留原名，只改对外
名。降低单次改动面、保回滚点；内部改名留后续独立 change（已记 Plan）。

## Risks / Trade-offs

- [worker 的 `new Worker(new URL("./netwave.worker.ts", ...))` vite 邻接约束] →
  搬目录时保持 `new URL(...)` 是 `new Worker(...)` 的直接参数，中间不插注释/
  变量；publish_shell.mjs 的 dist 重写路径同步改。
- [wasm-pack 产物名随 crate 变 `netwave_browser.js`] → 全仓 grep
  `netwave_wasm` 引用（index.browser.ts、worker、vitest alias、tsdown）逐处改。
- [Cargo members 由 typescript/wasm 改 browser] → `cargo metadata --no-deps`
  scenario 兜底，漏改当场红。
- [glue crate 仍空壳，browser 名实暂不完全符] → proposal Non-goals 与 Plan
  后续项显式声明 dispatch 搬迁为下一阶段，防误读为已独立。

## Migration Plan

1. 建 `browser/` 目录骨架（Cargo.toml、package.json、src、test），迁入 glue
   crate、worker、壳、types、测试，改 import 路径与产物目录。
2. 根 `Cargo.toml` members、`pnpm-workspace.yaml` 纳入 browser，移除
   typescript/wasm。
3. typescript 删 worker/壳/types/test，加 browser workspace 依赖，exports.browser
   改再导出；vitest 配置改名 unit/e2e。
4. 命令与 CI 改名（根 test:browser、CI job browser、artifact coverage-browser-*）。
5. 全链验证 `pnpm test`；回滚 = revert 本 change 提交（纯搬运，无数据迁移）。

## Open Questions

- browser 包内 `gen:constants` 与 typescript 是否共用同一常量源——apply 时按
  实际 import 关系定，不影响本设计结构。
