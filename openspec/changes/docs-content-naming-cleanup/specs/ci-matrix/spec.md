# Spec Delta

## MODIFIED Requirements

### Requirement: criterion 基准进 CI

CI MUST 运行 criterion 基准 job（在真实基准落地前允许空基准/极小基准，但
job 必须存在且通过），为铁律六的阈值回归守护提供对比基线。显著劣化（>20%）
MUST 失败。

#### Scenario: 基准 job 存在且记录基线

- **WHEN** `ci.yml` 运行完成
- **THEN** criterion job 产出基准结果并缓存为下次对比基线

### Requirement: 覆盖率门槛生效（铁律七）

CI MUST 启用覆盖率采集并使 100% 行覆盖门槛从第一天生效：Rust 用
`cargo llvm-cov --fail-under-lines 100`（或等效 `--fail-under-lines` 参数），
Python 用 `pytest-cov --cov-fail-under=100`（python 侧仅胶水时豁免项
逐条标注），Node/wasm 用 vitest coverage `lines: 100` 阈值写进配置。
结构性不可达代码 MUST 逐条标注豁免（`#[coverage(off)]` /
`# pragma: no cover` / `/* v8 ignore start/stop */`，vitest v8 provider）并附理由。

绑定 crate（python、typescript/native、typescript/wasm）从 Rust
`cargo llvm-cov` job 排除（`--ignore-filename-regex`）属**工具作用域分离**
而非批量豁免：这些 crate 依赖 JS/Python 运行时，无法在 `cargo test` 下执行，
其产码由各自语言的覆盖率工具（pytest-cov / vitest）在自身 job 内独立
100% 度量。逐条标注规则适用于**同一工具正在度量**的代码内的不可达分支。

#### Scenario: 空 crate 即 100%

- **WHEN** 各 crate/包只有最小 hello/往返代码且全部被测试执行
- **THEN** 覆盖率 job 通过（lines = 100%）

#### Scenario: 未测代码即红

- **WHEN** 新增一行未被任何测试执行的产码
- **THEN** 覆盖率 job 失败（exit ≠ 0），PR 不可合并

### Requirement: 主 CI 零 Python 运行时依赖

`ci.yml` 的构建/测试 job MUST NOT 安装或调用 scikit-rf；Python 仅出现在
`python/` 绑定自身的测试 job（pytest 读 `testdata/`），golden 生成
（`golden-refresh.yml`）另行立项，不在本变更。

#### Scenario: ci.yml 无 skrf

- **WHEN** 检查 `.github/workflows/ci.yml`
- **THEN** 无任何 `pip install scikit-rf` / `uv add scikit-rf` 步骤
