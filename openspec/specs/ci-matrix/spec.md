# ci-matrix Specification

## Purpose

定义 netwave 的 CI 质量闸门：五格构建矩阵、lint/格式/基准/覆盖率门槛，
保证任何平台的构建断裂与质量劣化在 PR 上即时暴露。

## Requirements

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

CI MUST 运行 criterion 基准 job（在真实基准落地前允许空基准/极小基准，
但 job 必须存在且通过），为铁律六的阈值回归守护提供对比基线。显著劣化
（>20%）MUST 失败。

#### Scenario: 基准 job 存在且记录基线

- **WHEN** `ci.yml` 运行完成
- **THEN** criterion job 产出基准结果并缓存为下次对比基线

### Requirement: 语言版本矩阵

语言版本轴与硬件平台轴是两个正交维度，须分别覆盖：

- **语言版本轴**（主 runner ubuntu 上跑底线 + 最新两格）：python job 跑
  Python 底线版与最新稳定版两格；node job 跑 Node 底线 LTS 与最新 LTS 两格。
  具体版本号 MUST 取自承载它们的钉版文件（`.github/workflows/ci.yml` 矩阵格、
  `python/.python-version`、`typescript/package.json` 的 `engines.node`），
  一致性由 `dependency-upgrade` spec 的规则驱动闸门校验，本 spec 不写死数字。
- **硬件平台轴**（各 OS 跑最新语言版本，验平台 ABI 而非版本 spread）：
  python/node job 另在 windows-latest 与 macos-latest 各跑最新一格，
  验证 `.so`/`.pyd`/`.dylib`/`.node` addon 与零拷贝 base object 的平台 ABI。

Rust MUST 只跑单一 stable（`rust-toolchain.toml` 钉死当前 stable）——
消费者自带 toolchain 编译，`rust-version` 由 cargo 自动检查。

#### Scenario: python/node 版本格 + 平台格

- **WHEN** PR 触发 `ci.yml`
- **THEN** python job 在 ubuntu 含 `python/.python-version` 所指底线与
  最新稳定两格、node job 在 ubuntu 含 `engines.node` 所指底线与最新 LTS
  两格；两者另在 windows/macos 各跑最新一格验 ABI，全部通过方可合并

#### Scenario: 矩阵数字单源

- **WHEN** 语言矩阵的版本号变更（如新 LTS 转换、新稳定 minor 落地）
- **THEN** 数字只改 `ci.yml` 矩阵格与对应底线声明文件，本 spec 措辞
  不随版本号变化

### Requirement: 覆盖率门槛生效（铁律七）

CI MUST 启用覆盖率采集并使 100% 行覆盖门槛从第一天生效，且 MUST 按
crate/包归属度量：core 用
`cargo llvm-cov -p netwave --codecov --output-path codecov.json` +
`scripts/coverage_gate.py codecov.json 100`
（单 crate + codecov 行合并：同一行任一二进制执行过即计覆盖，绕开默认 report 按实例计缺的
重复计数，LL-057），Python 用 `pytest-cov --cov-fail-under=100`（python
侧仅胶水时豁免项逐条标注），Node/wasm 用 vitest coverage `lines: 100`
阈值写进配置。结构性不可达代码 MUST 逐条标注豁免（stable 通道
`#[cfg(not(coverage))]` / `# pragma: no cover` / `/* v8 ignore start/stop */`，
vitest v8 provider；`#[coverage(off)]` nightly-only 禁用，LL-020）并附理由。

绑定 crate（python、typescript/native、typescript/wasm）不进 Rust
`cargo llvm-cov` job（`-p netwave` 天然排除）属**工具作用域分离**
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
`python/` 绑定自身的测试 job（pytest 读 `oracle/samples/`）。golden 生成
（`oracle/gen_golden.py`，oracle 的 uv 环境钉版 skrf）另行立项，不在本变更；
落地后 skrf 亦只出现在 oracle 阅卷步骤，各端构建/测试步骤保持零 skrf。

#### Scenario: ci.yml 无 skrf

- **WHEN** 检查 `.github/workflows/ci.yml`
- **THEN** 无任何 `pip install scikit-rf` / `uv add scikit-rf` 步骤

### Requirement: 治理脚本单测进 CI

CI MUST 运行治理脚本单测（`scripts/tests/`，命令细节唯一定义在根
`package.json` 的 `check:py`），使 `scripts/` 闸门的回归由 CI 兜底；
lint job MUST 经 `pnpm check` 覆盖该单测，MUST NOT 在 `pnpm check` 之外
重复跑单测命令（命令唯一真相源），MUST NOT 新增独立 job 或重复环境
准备，MUST NOT 引入联网测试（联网一致性验证为本地一次性基线，见
workspace-layout「根级 Python 工具环境」）。`check:py` MUST 以
`--cov-fail-under` 对 `scripts/versions` 域设行覆盖率地板，阈值数值以
根 `package.json` 该 flag 为唯一定义处（散文不复制数字）；度量范围外
的 `scripts/` 其余脚本不设地板（另议题）。

#### Scenario: 闸门回归 CI 兜底

- **WHEN** 任一 PR 改动 `scripts/` 且使治理脚本单测失败
- **THEN** lint job FAIL 并指向失败用例——闸门脚本的回归不能只靠本地

#### Scenario: 不重复命令真相源

- **WHEN** 查看 lint job 步骤序列
- **THEN** 单测仅经 `pnpm check`（内含 `check:py`）运行一次，
  ci.yml 不出现第二处单测命令

#### Scenario: versions 域覆盖率地板生效

- **WHEN** `scripts/versions` 域行覆盖率低于 `check:py` 所钉
  `--cov-fail-under` 阈值（含新增未测行、也含删除既有覆盖用例）
- **THEN** `pnpm check:py` 退出码非 0，lint job FAIL——覆盖率不得
  无声下滑；结构性不可达行如需豁免，按铁律七逐条标注并附理由
