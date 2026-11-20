# Design

## Context

动机见 `proposal.md` 的 Why。当前状态：`test:wasm`/`test:browser` 仅存在于
`typescript/package.json`；真浏览器套件未进任何 `scripts/run/test_*.sh` 也未进
`pnpm test`；ci.yml wasm job 内联 build + node wasm 套件 + playwright 安装 + 浏览器套件
四步。`fromUrl` 的 fetch 在 wasm 内部（`core/src/touchstone.rs` 的 `fetch_text` 经
`js_sys::global()` 取 `fetch`），node 下解析为 `globalThis.fetch`。

## Goals / Non-Goals

**Goals:**

- 全项目 wasm 测试收进单一 `scripts/run/test_wasm.sh`，与 `test_ts.sh` 同构。
- wasm 壳 `functions` 满覆盖由 mock 实现，不引入 HTTP server 或新依赖。

**Non-Goals:**

- 不改 `fromUrl` 产品逻辑、不动 native 套件的 server 写法。
- 不做 wasm 胶水 rust 行覆盖（S5，独立立项）。

## Decisions

- **mock fetch 而非起 server**：wasm 的 fetch 经 `globalThis.fetch`，用
  `vi.stubGlobal` stub `fetch` 返回 `new Response(S1P)` 即可让 `fromUrl` 成功回调计数；node 22
  内置 `Response` 满足 `fetch_text` 校验的 `.ok()`/`.status()`/`.text()`。备选：起本地
  server（native 套件因 fetch 在 Rust 侧 reqwest 拦不到才被迫用，wasm 侧无此必要）；
  引 msw（为一个回调过重）。
- **build:wasm 双脚本各自跑**：`test_wasm.sh` 与 `test_ts.sh` 各含 `build:wasm`，幂等无
  副作用，因二者被不同 CI job（wasm job / node job）独立调用，互不依赖。备选：单一来源
  共享产物——引入跨脚本顺序耦合，违背各 job 自洽。
- **node 版本轴 wasm 验证保留**：`test_ts.sh` 不动，node 矩阵验"wasm 产物跨 node 版本可
  加载"是独立覆盖轴，删之即降级。
- **脚本探测不装**：沿用 `test_*.sh` 既有原则，chromium 缺失打印 `playwright install`
  命令退出；CI 保留 install 步。

## Risks / Trade-offs

- [mock 能否穿透到 wasm 的 `js_sys::global()` 未经实证] → 落地时 MUST 跑
  `pnpm -C typescript test:wasm` 实证 functions 从 56/57 翻满，不靠推断；不通则回退到
  本地 server 方案并更新本 design。
- [`pnpm test` 聚合新增浏览器套件使本地全量测试变重] → 用户已确认本地入口应全量；
  chromium 由项目级 playwright 缓存，首次后复用。
