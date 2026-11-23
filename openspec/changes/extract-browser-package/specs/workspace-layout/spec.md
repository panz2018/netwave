# workspace-layout Delta

## Modified Requirements

### Requirement: 平铺 monorepo 结构

仓库根 MUST 包含 `core/`、`python/`、`browser/`、`typescript/`、`oracle/` 子项目
目录与根 `[workspace]` `Cargo.toml`（members = core、python、browser、
typescript/native），以及 `pnpm-workspace.yaml`（packages = browser、typescript）。
`oracle/` 为数值真值参照与阅卷子项目（契约、样本、阅卷脚本；不发布、不参与
Cargo/pnpm workspace）。`browser/` 为浏览器端自包含子项目：内含 wasm-bindgen
Rust glue crate、resident worker、主线程传输壳与浏览器端测试，依赖方向单向
指向 core。TypeScript 侧承载 node（`typescript/native/` napi Rust crate）与
node+browser 薄封装发布壳，经 pnpm workspace 依赖消费 `browser/`，不再持有
wasm-bindgen crate。exports 条件分发，单包发布名 `netwave`。目录一律短名，
发布名在各清单文件独立声明。数值真值内容（manifest、样本、LICENSE-NOTES）居
`oracle/`，仓库根无 `testdata/` 目录。

#### Scenario: workspace 清单一致

- **WHEN** 在仓库根运行 `cargo metadata --no-deps`
- **THEN** 输出的 workspace members 恰为 core、python、browser、
  typescript/native 四个包
- **AND** `pnpm-workspace.yaml` 列出 browser 与 typescript
- **AND** 仓库根存在 `oracle/` 目录且不存在 `testdata/` 目录

#### Scenario: 发布名与目录名解耦

- **WHEN** 读取各清单文件
- **THEN** `python/pyproject.toml` 的 `[project] name` 为 `netwave`；
  `typescript/package.json` 的 `name` 为 `netwave`；`core/Cargo.toml` 的
  package name 为 `netwave`（`publish = false` 占位）；`browser/` 的 Rust crate
  name 为 `netwave-browser`、pnpm 包 `private: true`

#### Scenario: 单包按环境自动分发

- **WHEN** 读取 `typescript/package.json`（npm 发布名 `netwave`）
- **THEN** 其 `exports` 条件映射：`"node"` 条件指向 napi 产物（`.node` +
  ESM/CJS 双壳），`"browser"`/`"default"` 条件指向构建期从 `browser/` 包合并
  进 typescript 产物的浏览器 ESM（发布物自包含，运行时不依赖未发布的 browser）；
  另含纯 HTML 零构建单文件入口（`./standalone` 子路径）与预置 `./worker`
  （浏览器 Worker 胶水，零数值逻辑）
- **AND** 原生二进制按平台拆 `optionalDependencies`（`os`/`cpu` 标签），
  install 只拉本平台块
- **AND** 不发 UMD 格式（`<script type="module">` 即标准答案，UMD 是历史包袱）
- **AND** 单包不含任何数值代码，数值全在 core

#### Scenario: browser 子项目自我完整

- **WHEN** 检查 `browser/` 目录内容
- **THEN** worker、主线程传输壳、worker 协议类型与浏览器端测试均在 `browser/`
  内，wasm 构建产物落 `browser/dist/`
- **AND** `typescript/` 不再持有 worker、传输壳或 wasm-bindgen crate
- **AND** `browser/` 仅依赖 core，不被 core 反向依赖

#### Scenario: 命名空间预留名不占用

- **WHEN** 未来新增网页端插件（如 Touchstone 格式转换器 / 显示器）
- **THEN** 其 npm 发布名 MUST 使用 `@netwave/<功能名>` 形式
  （预留：`@netwave/converter`、`@netwave/touchstone`），
  与本变更已定名字不冲突
