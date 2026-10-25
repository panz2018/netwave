# Proposal

> **⏸ 暂停实施**：升级治理机制（过期检查门禁化、bug 版本黑名单、登记表分工、
> `paired_with` 版本相容校验）尚未拍板，机制未定则升级无法有效执行——
> 详见 [tasks.md](tasks.md) 顶部说明与
> [Plan/测试规划.md 待议节](../../../Plan/测试规划.md#待议过期检查升级为-ci-门禁--bug-版本黑名单--登记表瘦身--配对版本校验)。

## Why

Python 3.15 已于 2026-10-09 发布为稳定版，且本项目所需库全部支持
（numpy 2.5.4、pyo3 0.30、maturin 1.15、pytest 9.1、ruff 0.17、scikit-rf 2.2
均声明支持 3.15）。按 `dependency-upgrade` spec 的选线原则（单线运行时取
最新稳定 minor），netwave 应升到 3.15。pyo3 0.30 含 breaking changes
（`#[pyclass]` 默认不再生成 `FromPyObject`、abi3 feature 选择逻辑变更等），
属结构性升级，按该 spec 的升级分级走本 OpenSpec change。

## What Changes

- Python 运行时 3.14→3.15：`python/.python-version`、CI python job 最新格
  3.14→3.15（底线 3.10 不变）、登记表数字同步。
- pyo3 0.29→0.30、numpy 0.29→0.30（配对联动）、pyo3-stub-gen 升至配套版本；
  适配 breaking changes（`FromPyObject` 默认不再生成、abi3 相关变更、
  `PyBuffer` 弃用方法等，以实际编译报错为准逐项处理）。
- abi3 覆盖范围评估：维持 `abi3-py310`（底线不变，一个 wheel 覆盖 3.10–3.15）；
  `requires-python` 维持 `>=3.10`。
- oracle 环境（skrf）随本 change 在 3.15 下重建 uv.lock（skrf 2.2 已支持 3.15）。
- 文档同步：workspace-layout/ci-matrix 中 "3.14" 相关措辞随
  `dependency-upgrade` 单源化结果核对更新；README 等散文不复制数字。
- 全程按 `dependency-upgrade` spec 的升级流程执行（全局 CLI 体检 →
  uv/工具链 → 配对联动 → 依赖刷新 → 代码兼容 → 全闸门 + 四端对拍 → 文档）。

## Capabilities

### New Capabilities

（无——本 change 是 `dependency-upgrade` spec 流程的首次实战执行。）

### Modified Capabilities

（无。版本数字的真相源是登记表 `scripts/version_pins.json` 与清单文件，
改数字不是 spec 级行为变化；`ci-matrix`/`workspace-layout` 的数字单源化由
`add-dependency-upgrade-spec` 完成。本 change 声明 `skip_specs: true`；
若实施时发现主 spec 仍有残留数字（change 1 未归档所致），当场补 delta。）

## Impact

- 代码：`python/src/lib.rs`（pyo3 0.30 API 适配）、`python/Cargo.toml`
  （pyo3/numpy/pyo3-stub-gen 版本）、`python/netwave/`（如 stub 再生成有差异）。
- 配置：`python/.python-version`、`python/pyproject.toml`、`python/uv.lock`、
  `oracle/` uv 环境 lock、`scripts/version_pins.json`、`.github/workflows/ci.yml`
  （python 矩阵格）。
- 验证：`cargo test --workspace`、pytest、`pnpm check`、`pnpm check:cross`
  （四端对拍数值不变，铁律三容差不变）。
- 不涉及：core 数值代码、公开 API 命名、Node/wasm 端（除 lockfile 例行刷新）。

## Non-goals

- 不抬 Python 底线（`requires-python` 维持 >=3.10；3.9 及以下不支持）。
- 不切 abi3-py315（维持 abi3-py310，兼容性下限不动）。
- 不动 Node 矩阵（22 + 26 均为 LTS，无需变更）。
- 不做 pyo3 新特性采纳（`PyFrozenDict`、`PyContext` 等）——只做到兼容迁移，
  新特性另议。
- 不改任何数值行为与容差。
