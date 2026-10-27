# workspace-layout Specification

## Purpose

定义 netwave monorepo 的目录结构、workspace 组织与发布名解耦契约，保证 core 与
三绑定同仓同步发版（ABI 严格同步）且各注册表命名稳定。

## Requirements

### Requirement: 平铺 monorepo 结构

仓库根 MUST 包含 `core/`、`python/`、`typescript/`、`oracle/` 四个子项目目录
与根 `[workspace]` `Cargo.toml`（members = core、python、typescript/native、
typescript/wasm），以及 `pnpm-workspace.yaml`（typescript）。`oracle/` 为数值
真值参照与阅卷子项目（契约、样本、阅卷脚本；不发布、不参与 Cargo/pnpm
workspace）。TypeScript 侧为**单一 npm 包单目录**：`typescript/` 内含 `native/`（napi Rust
crate）与 `wasm/`（wasm-bindgen Rust crate）两个构建目标，exports 条件分发，
不再拆 `@netwave/node`/`@netwave/wasm` 独立包。目录一律
短名，发布名在各清单文件独立声明。`testdata/` 废止，其内容
（manifest、样本、LICENSE-NOTES）整体迁入 `oracle/`。

#### Scenario: workspace 清单一致

- **WHEN** 在仓库根运行 `cargo metadata --no-deps`
- **THEN** 输出的 workspace members 恰为 core、python、typescript/native、
  typescript/wasm 四个包
- **AND** `pnpm-workspace.yaml` 列出 typescript
- **AND** 仓库根存在 `oracle/` 目录且不存在 `testdata/` 目录

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

### Requirement: 主 CI 零 Python 依赖

各端主构建/测试路径（cargo test、pytest 读 oracle 样本、vitest、wasm 构建）
MUST NOT 依赖 Python 运行时生成数据；oracle 的生成/阅卷步骤不在此条款范围
（skrf 圈禁于 oracle 环境，见 governance 铁律四）。`oracle/` 承载容差
manifest 与 Touchstone 输入样本（本阶段 manifest 为骨架、样本为脚手架三件）。

#### Scenario: 构建不触发 Python

- **WHEN** 在无 skrf 安装的环境执行 `cargo test --workspace` 与
  `pnpm -r build`
- **THEN** 全部命令成功退出（exit 0），无 skrf 导入错误

### Requirement: 根级 Python 工具环境

仓库根 MUST 存在 uv 工具工程 `pyproject.toml`（private，不发布）及其
`uv.lock`、`.python-version`，作为全部仓库治理脚本（`scripts/` 闸门与后续
测试）的统一 Python 环境：工具依赖（pytest、pytest-cov、ruff）MUST 在该
工程 dev 组声明并锁死，MUST NOT 依赖开发者全局 Python 所装内容。根工程
MUST NOT 声明 uv workspace 成员；`python/` 维持独立 uv 工程（发布物依赖
故事独立，uv 按就近目录解析互不干扰）。根 `.python-version` 与主工程
`python/.python-version` 同值，随登记表条目纳入对账。

#### Scenario: 门禁脚本经根环境运行

- **WHEN** 在仓库根运行 `uv run python scripts/versions/check_versions.py`
- **THEN** 命令经根 `uv.lock` 锁定的环境执行成功，不要求任何全局安装的
  第三方包

#### Scenario: 发布工程环境独立

- **WHEN** 在 `python/` 目录运行 `uv sync`
- **THEN** 解析到 `python/pyproject.toml` 自身工程（numpy/maturin/pytest
  等发布侧依赖），与根工具工程互不影响

#### Scenario: 根 pin 纳入自登记

- **WHEN** 对账闸门发现式扫描扫到根 `uv.lock` 或根 `.python-version`
- **THEN** 二者已登记为登记表条目（root-uv-lock / root-python / root-requires），
  `pnpm check:meta` 通过；缺登记即 FAIL
