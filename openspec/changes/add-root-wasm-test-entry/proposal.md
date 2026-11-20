# Proposal

## Why

`typescript/package.json` 的 `test:wasm`/`test:browser` 只覆盖 typescript 子目录的
wasm 测试，且真浏览器套件（`test:browser`）既没进任何 `scripts/run/test_*.sh`，也没进
根 `pnpm test` 聚合——本地 `pnpm test` 跑不到浏览器面，CI 的 wasm job 又把 build、
node wasm 套件、playwright 安装、浏览器套件四步内联在 ci.yml 里，与 `test:rs`/`test:py`/
`test:ts` 的"命令细节单源在 scripts/run"模式不一致。同时 `vitest.wasm.config.ts` 漏卡
`functions`，`fromUrl` 成功回调在 wasm 套件下计数为 0。

## What Changes

- 新建根 `scripts/run/test_wasm.sh`：全项目 wasm 测试总入口，含 `build:wasm` +
  node 驱动 wasm 套件 + 真浏览器套件；工具（wasm-pack/wasm-opt/wasm32 目标/chromium）
  只探测缺失即打印命令退出，绝不自动安装。
- 根 `package.json` 新增 `test:wasm` 薄入口并加入 `pnpm test` 聚合链。
- ci.yml 的 wasm job 测试步骤收成一行 `bash scripts/run/test_wasm.sh`，前置 install
  步（binaryen/wasm-pack/pnpm/playwright chromium）保留——脚本探测、CI 负责装。
- `vitest.wasm.config.ts` 的 `thresholds` 补 `functions: 100`。
- `test/wasm/touchstone.test.ts` 用 `vi.stubGlobal('fetch', ...)` 补 `fromUrl` 成功
  路径用例（不起 HTTP server），使 wasm 套件单跑 functions 满覆盖。
- `scripts/run/test_ts.sh` 不动：node 版本轴的 wasm 验证保留，build:wasm 两脚本各自幂等跑。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ci-matrix`: 新增"全项目 wasm 测试根聚合入口"Requirement（根 `test:wasm` 薄调
  `scripts/run/test_wasm.sh`，含 build:wasm + node wasm 套件 + 真浏览器套件，工具只探测
  不装，进 `pnpm test` 聚合，ci.yml wasm job 收成一行调脚本）。wasm 壳 `functions`
  阈值补 100 属配置数值变化，阈值数值以 `vitest.*.config.ts` 为唯一定义处、spec 不复制
  数值，故不改 spec 覆盖率门槛 Requirement。

## Impact

- 新建：`scripts/run/test_wasm.sh`
- 修改：根 `package.json`、`.github/workflows/ci.yml`、`typescript/vitest.wasm.config.ts`、
  `typescript/test/wasm/touchstone.test.ts`
- 闸门：`scripts/check_ci.py`（根新增 `test:wasm` 强制 ci.yml 出现该脚本调用）
- 波及文档：`openspec/specs/ci-matrix/spec.md`、`Plan/覆盖率统一-2026-11-12.md`（延后项结论回写）
- 受影响铁律：铁律七（覆盖率门槛）、LL-034（CI 构建不变式）、LL-092（胶水覆盖率三坑）

## Non-goals

- 不做 S5 wasm 胶水（rust 行）覆盖率 spike——插桩计数倒出仍未验证，独立立项。
- 不改 `test_ts.sh` 的 node 版本轴 wasm 验证（保留现状语义）。
- 不引入 msw 等新依赖，不改 `fromUrl` 产品代码逻辑。
- 不让脚本自动安装 chromium/playwright（机器/网络副作用归 CI 与人工）。

## Prior art

- 仓库内同构先例：`scripts/run/test_ts.sh`、`scripts/run/test_rs.sh`、
  `scripts/run/test_py.sh`（薄入口 + 工具探测 + 单进程单真相源）。
- mock fetch 现成方案：vitest 官方 `vi.stubGlobal`
  （<https://vitest.dev/api/vi#vi-stubglobal>），
  仓库内 `typescript/src/netwave.worker.ts` 已用 `/* v8 ignore */` 处理环境分支。
- node 起 server 跑 fromUrl 的对照写法：`typescript/test/native/touchstone.test.ts`
  （native 走 reqwest 拦不到才起 server；wasm 走 `web_sys::fetch`→`globalThis.fetch` 可 mock）。

## 专家增补

- 顶尖专家会确认 mock 穿透边界：`core/src/touchstone.rs` 的 `fetch_text` 经
  `js_sys::global()` 取 `fetch`，node 下即 `globalThis.fetch`，故 `vi.stubGlobal('fetch')`
  能拦到——落地时 MUST 跑 `pnpm -C typescript test:wasm` 实证 functions 翻满，不靠推断。
- 顶尖专家会核对 `check_ci.py` 的 `bash scripts/run/test_<段>.sh` 字面匹配，确保 ci.yml
  用调用形式而非注释提及路径，否则闸门误判。

## 已定裁决

- `stub-global-fetch`：`fromUrl` 成功回调用 `vi.stubGlobal('fetch', ...)` mock 覆盖，不起 HTTP server。
- `wasm-functions-threshold`：`vitest.wasm.config.ts` 补 `functions: 100`。
- `verify-functions`：改完当场跑 `pnpm -C typescript test:wasm` 验证 functions 翻满、阈值过。
- `root-test-wasm-entry`：根 `test:wasm` = 全项目 wasm 测试总入口（build:wasm + node wasm 套件 + 真浏览器套件）。
- `probe-not-install`：`test_wasm.sh` 对 chromium 等工具只探测缺失即打印命令退出，不自动安装。
- `test-wasm-in-aggregate`：根 `test:wasm` 加入 `pnpm test` 聚合链（本地全量入口）。
- `keep-node-axis-wasm`：`test_ts.sh` 保留 build:wasm + test:wasm，node 版本轴 wasm 验证不删。
- `build-wasm-idempotent`：`test_wasm.sh` 与 `test_ts.sh` 各自 build:wasm，幂等互不依赖。
- `ci-wasm-job-one-line`：ci.yml wasm job 测试步骤收成一行 `bash scripts/run/test_wasm.sh`，前置 install 步保留。
