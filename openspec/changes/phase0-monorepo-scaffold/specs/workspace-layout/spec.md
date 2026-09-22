# Spec Delta

## Purpose

定义 netwave monorepo 的目录结构、workspace 组织与发布名解耦契约，保证 core 与
三绑定同仓同步发版（ABI 严格同步）且各注册表命名稳定。

## ADDED Requirements

### Requirement: 平铺 monorepo 结构

仓库根 MUST 包含 `core/`、`python/`、`typescript/`、`testdata/`
四个子项目目录与根 `[workspace]` `Cargo.toml`（members = core、python、
typescript/native、typescript/wasm），以及 `pnpm-workspace.yaml`（typescript）。
TypeScript 侧为**单一 npm 包单目录**：`typescript/` 内含 `native/`（napi Rust
crate）与 `wasm/`（wasm-bindgen Rust crate）两个构建目标，exports 条件分发，
不再拆 `@netwave/node`/`@netwave/wasm` 独立包（2026-09-21 定案）。目录一律
短名，发布名在各清单文件独立声明。

#### Scenario: workspace 清单一致

- **WHEN** 在仓库根运行 `cargo metadata --no-deps`
- **THEN** 输出的 workspace members 恰为 core、python、typescript/native、
  typescript/wasm 四个包
- **AND** `pnpm-workspace.yaml` 列出 typescript

#### Scenario: 发布名与目录名解耦

- **WHEN** 读取各清单文件
- **THEN** `python/pyproject.toml` 的 `[project] name` 为 `netwave`；
  `typescript/package.json` 的 `name` 为 `netwave`；`core/Cargo.toml` 的
  package name 为 `netwave`（`publish = false` 占位）

#### Scenario: 单包按环境自动分发

- **WHEN** 读取 `typescript/package.json`（npm 发布名 `netwave`）
- **THEN** 其 `exports` 条件映射：`"node"` 条件指向 napi 产物（`.node` +
  ESM/CJS 双壳），`"browser"`/`"default"` 条件指向 wasm 产物 ESM；
  另含纯 HTML 零构建单文件入口（`./standalone` 子路径）与预置
  `./worker`（浏览器 Worker 胶水，零数值逻辑）
- **AND** 原生二进制按平台拆 `optionalDependencies`（`os`/`cpu` 标签），
  install 只拉本平台块
- **AND** 不发 UMD 格式（`<script type="module">` 即标准答案，UMD 是历史包袱）
- **AND** 单包不含任何数值代码，数值全在 core

#### Scenario: 命名空间预留名不占用

- **WHEN** 未来新增网页端插件（如 Touchstone 格式转换器 / 显示器）
- **THEN** 其 npm 发布名 MUST 使用 `@netwave/<功能名>` 形式
  （预留：`@netwave/converter`、`@netwave/touchstone`），
  与本变更已定名字不冲突

### Requirement: 版本底线

全仓 MUST 满足底线版本（= 兼容性下限，覆盖其上所有版本）：Rust edition 2024、
MSRV = 当前 stable（1.98，升版走 OpenSpec 变更）；Python ≥3.10、NumPy 2.x
（abi3 一个 wheel 覆盖 3.10–3.14）；Node ≥22（最旧在支持期 LTS，Node 20 已
2026-04 EOL）。开发版本用当前 latest stable：Python 3.14（`.python-version`
进 git）、Node 26；CI 版本矩阵见 ci-matrix spec。
包管理器版本 MUST 钉死：根 `package.json` 含 `"packageManager":
"pnpm@<exact>"`；`python/` 含 `pyproject.toml` 与 `uv.lock` 且 maturin 为 dev
dependency。

#### Scenario: 底线版本可校验

- **WHEN** 检查 `core/Cargo.toml`、`python/pyproject.toml`、根 `package.json`
- **THEN** edition = "2024"、rust-version ≥ 1.98、`requires-python` ≥ ">=3.10"、
  `engines.node` ≥ ">=22"、`packageManager` 为精确版本号
- **AND** `python/uv.lock` 存在且进 git

### Requirement: 主 CI 零 Python 依赖

主构建/测试路径（cargo test、pytest 读 testdata、vitest、wasm 构建）MUST NOT
依赖 Python 运行时生成数据；`testdata/` 在本阶段仅建目录骨架与 LICENSE-NOTES.md
占位。

#### Scenario: 构建不触发 Python

- **WHEN** 在无 skrf 安装的环境执行 `cargo test --workspace` 与
  `pnpm -r build`
- **THEN** 全部命令成功退出（exit 0），无 skrf 导入错误
