# Proposal

## Why

netwave 的一切功能（阶段 2 起的 Touchstone/Network/Circuit）都要求"地基从阶段 0 就是
四端的"（core + python + node + wasm 同仓同步发版）。没有 monorepo 骨架、三绑定 hello
world 与 CI 矩阵，后续每个功能变更都无处落地，零拷贝这一立项卖点也无法被验证。
本变更立起这套骨架，是路线图的阶段 0。

## What Changes

- 创建平铺 monorepo：`core/`（Rust 核心 crate）、`python/`（PyO3 + maturin）、
  `typescript/`（单一 npm 包：内含 `native/` napi Rust crate 与 `wasm/`
  wasm-bindgen Rust crate，exports 条件分发 + 预置 `worker.js`）、
  `testdata/`（空骨架 + LICENSE-NOTES 占位）；根 `Cargo.toml` workspace
  （members = core/python/typescript/native/typescript/wasm）与
  `pnpm-workspace.yaml`（typescript）。
- 发布名统一方案（能统一处统一）：crates.io `netwave`（core，`publish = false`
  占位）、PyPI `netwave`、npm `netwave`（单包：exports 条件 node → napi 产物、
  browser/default → wasm 产物；另发纯 HTML 零构建单文件 ESM 入口与预置
  `netwave.worker.js`；不发 UMD——`<script type="module">` 即标准答案）。
  **不再拆 `@netwave/node`/`@netwave/wasm` 独立包**（2026-09-21 定案：打包器
  按 exports 条件只拉命中分支，消费者产物体积无感；install 磁盘占用用 napi
  按平台 `optionalDependencies` 缓解；三包同版本同步机器整个省掉）。
  未来网页端插件预留 `@netwave/converter`（Touchstone 格式转换 web
  component）、`@netwave/touchstone`（Touchstone 显示等网页插件）。
  本变更只写清单字段，不发布。
- core 暴露唯一临时 API `fill_pattern()`：分配 `(nfreq, nports, nports)` 交错复数
  f64 缓冲并写入可预测图案，作为零拷贝往返验证的载体（阶段 2 被真实数据模型替换）。
- 三绑定各暴露 `hello` + buffer 视图获取函数：Python `PyArray` 视图、Node
  `ArrayBuffer`/External、wasm `Float64Array` 视图；四端测试改视图元素 → 回读
  core 验证同一块内存（cross-binding 对拍的最早形态）。
- 异步/Worker 契约钉死（2026-09-22 修订；阶段 0 只写契约与 exports 骨架，
  实现在阶段 3/6）：**JS 公开计算面单一 async**——计算动词不加后缀、直接返回
  `Promise`，用户统一 `await`，不存在"同步/异步选哪个"的困惑；同步直通版降级为
  `_` 前缀逃生口（外部可调用、`.d.ts` 标 `@internal`、铁律七覆盖率照常计入）；
  属性/元数据读取保持同步。**Worker 分流库内自动**：小数据立即 resolve，
  大数据进 Worker 池/napi AsyncTask，用户代码不变（阈值阶段 3/6 按 benchmark 定）。
  边界 transfer 决策表：普通调用输入结构化克隆进入（输入永不消耗）、`upload`
  显式托管才 transfer、结果 buffer 一律 transfer 送回、`await` 后从返回值重建
  视图（wasm memory.grow 会 detach 旧视图）；SAB 可选升级，接口不变。
  Worker 容器归宿主 JS：预置 `netwave.worker.js` 由 async 壳内部托管，
  普通用户不直接接触；多线程 wasm（wthreads + COOP/COEP）属阶段 3。
  **tree-shaking**：包入口禁 `export *`，显式具名导出；Worker 用显式静态分发表；
  wasm 体积靠 Rust 侧 LTO + wasm-opt（JS 摇树摇不掉 wasm 二进制，诚实声明）。
- CI 五格矩阵全铺：linux-x64、linux-arm64、windows-x64、darwin-arm64、
  wasm32-unknown-unknown（macOS 放弃 Intel x64——Apple 即将停止支持 x86 程序，
  只支持 Apple Silicon）；含 clippy `-D warnings`、fmt、criterion 空基准、
  覆盖率门槛（铁律七：100% 行覆盖，空 crate 即达标，门槛从第一天生效）。
- 根 `package.json` 钉死 `"packageManager": "pnpm@12.5.1"`（corepack）；
  `python/` 用 uv 管理（`pyproject.toml` + `uv.lock`，maturin 为 dev dependency）。

## Capabilities

### New Capabilities

- `workspace-layout`: monorepo 目录结构、workspace 清单、发布名解耦与版本底线。
- `zero-copy-roundtrip`: 四端零拷贝 buffer 往返验证契约（视图可写、core 可见、
  布局逐字节为交错复数 f64）。
- `ci-matrix`: 三平台五格 CI 矩阵与质量闸门（clippy/fmt/criterion/覆盖率）。

### Modified Capabilities

（无——首个变更，`openspec/specs/` 为空。）

## Impact

- 新增目录：`core/`、`python/`、`typescript/native/`、`typescript/wasm/`、
  `typescript/test/`、`testdata/`、`.github/workflows/`。
- 新增根文件：`Cargo.toml`、`Cargo.lock`、`pnpm-workspace.yaml`、`package.json`、
  `.gitignore`。
- 依赖：Rust crate `pyo3`/`numpy`/`napi`+`napi-derive`/`wasm-bindgen`/`criterion`；
  工具链已核实就位（见[开发流程·工具链状态](../../../Plan/开发流程.md#工具链状态)）。
- 受影响铁律：铁律一（数据布局是往返验证的契约）、铁律四（主 CI 零 Python 依赖）、
  铁律六（criterion 空基准进 CI）、铁律七（覆盖率 100% 门槛生效）。

## Non-goals

- 不做任何真实数值功能：Touchstone 解析、Network/Circuit 均属阶段 2+；
  `fill_pattern()` 是临时脚手架 API，非契约的一部分。
- 不发布任何注册表包（抢注/发版是账号侧独立动作，另行跟踪）。
- 不做 `viewer/`（独立立项）、不做 Calibration/Vector Fitting（阶段 7+）。
- 不做 wasm 性能定标（阶段 3）；本变更只保证 wasm 能构建、往返能验证。
- 不建 `testdata/` 的 manifest/golden 内容（阶段 1），只建目录骨架。
