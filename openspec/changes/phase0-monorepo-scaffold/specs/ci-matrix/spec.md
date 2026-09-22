# Spec Delta

## Purpose

定义阶段 0 的 CI 质量闸门：三平台五格构建矩阵、lint/格式/基准/覆盖率门槛，
保证任何平台的构建断裂与质量劣化在 PR 上即时暴露。

## ADDED Requirements

### Requirement: 五格构建矩阵

主 CI MUST 在以下五格全部通过：linux-x64、linux-arm64、windows-x64、
darwin-arm64、wasm32-unknown-unknown。macOS MUST NOT 提供 x64（Intel）
支持——Apple 已宣布停止支持 x86 程序，macOS 目标仅 Apple Silicon。
每格 MUST 执行 `cargo test`
（wasm32 格为 `cargo check`/wasm-pack 构建 + Node 侧 vitest 跑 wasm 产物）。

#### Scenario: 矩阵全绿方可合并

- **WHEN** PR 触发 `ci.yml`
- **THEN** 五格 job 全部执行且 exit 0
- **AND** 任一格失败即整个 required check 失败，PR 不可合并

### Requirement: Rust 质量闸门

CI MUST 运行 `cargo clippy --workspace --all-targets -- -D warnings` 与
`cargo fmt --all --check`，任一失败即 CI 失败。

#### Scenario: warning 即红

- **WHEN** 代码存在 clippy warning 或格式不符
- **THEN** 对应 CI job 失败（exit ≠ 0）

### Requirement: criterion 基准进 CI

CI MUST 运行 criterion 基准 job（阶段 0 允许空基准/极小基准，但 job 必须存在且
通过），为铁律六的阈值回归守护提供对比基线。显著劣化（>20%）MUST 失败。

#### Scenario: 基准 job 存在且记录基线

- **WHEN** `ci.yml` 运行完成
- **THEN** criterion job 产出基准结果并缓存为下次对比基线

### Requirement: 语言版本矩阵

预编译二进制分发 MUST 在 CI 实测底线与最新两个版本：python job 跑
Python 3.10（底线）与 3.14（最新 stable）双格；node job 跑 Node 22（底线
LTS）与 26（最新 stable）双格。Rust MUST 只跑单一 stable（1.98，
rust-toolchain.toml 钉死）——消费者自带 toolchain 编译，`rust-version`
由 cargo 自动检查。

#### Scenario: python/node 双版本格

- **WHEN** PR 触发 `ci.yml`
- **THEN** python job 矩阵含 3.10 与 3.14 两格、node job 矩阵含 22 与 26 两格，
  全部通过方可合并

### Requirement: 覆盖率门槛生效（铁律七）

CI MUST 启用覆盖率采集并使 100% 行覆盖门槛从第一天生效：Rust 用
`cargo llvm-cov --fail-under-lines 100`（或等效 `--fail-under-lines` 参数），
Python 用 `pytest-cov --cov-fail-under=100`（阶段 0 python 侧仅胶水则豁免项
逐条标注），Node/wasm 用 vitest coverage `lines: 100` 阈值写进配置。
结构性不可达代码 MUST 逐条标注豁免（`#[coverage(off)]` /
`# pragma: no cover` / `/* istanbul ignore next */`）并附理由。

#### Scenario: 空 crate 即 100%

- **WHEN** 阶段 0 各 crate/包只有最小 hello/往返代码且全部被测试执行
- **THEN** 覆盖率 job 通过（lines = 100%）

#### Scenario: 未测代码即红

- **WHEN** 新增一行未被任何测试执行的产码
- **THEN** 覆盖率 job 失败（exit ≠ 0），PR 不可合并

### Requirement: 主 CI 零 Python 运行时依赖

`ci.yml` 的构建/测试 job MUST NOT 安装或调用 scikit-rf；Python 仅出现在
`python/` 绑定自身的测试 job（pytest 读 `testdata/`），golden 生成
（`golden-refresh.yml`）属阶段 1，不在本变更。

#### Scenario: ci.yml 无 skrf

- **WHEN** 检查 `.github/workflows/ci.yml`
- **THEN** 无任何 `pip install scikit-rf` / `uv add scikit-rf` 步骤
