# ci-matrix Specification

## Purpose

定义 netwave 的 CI 质量闸门：五格构建矩阵、lint/格式/基准/覆盖率门槛，
保证任何平台的构建断裂与质量劣化在 PR 上即时暴露。

## Requirements

### Requirement: 五格构建矩阵

主 CI MUST 在以下五格全部通过：linux-x64、linux-arm64、windows-x64、
darwin-arm64、wasm32-unknown-unknown。macOS MUST NOT 提供 x64（Intel）
支持——Apple 已宣布停止支持 x86 程序，macOS 目标仅 Apple Silicon。
native 四格 MUST 执行 rust 测试与覆盖率合并命令：
`cargo llvm-cov -p netwave` 执行 core 测试，
加 `cargo build --workspace --all-targets` 作编译看门闸
（命令构成见「覆盖率门槛生效（铁律七）」）；MUST NOT 另跑
`cargo test --workspace`（core 测试由 llvm-cov 执行，绑定 crate 编译闸门
由 build 承担；本仓库源码无可执行 doctest——grep `core/src`、`python/src`、
`typescript/*/src` 的文档注释围栏仅 `text` 标注（非 rust、不可执行）且位于
bin target（bin 不跑 doctest），将来引入可执行 doctest 须另行立项补执行者）。
wasm32 格为 `cargo check`/wasm-pack 构建 + Node 侧 vitest 跑 wasm 产物。

#### Scenario: 矩阵全绿方可合并

- **WHEN** PR 触发 `ci.yml`
- **THEN** 五格 job 全部执行且 exit 0
- **AND** 任一格失败即整个 required check 失败，PR 不可合并

#### Scenario: core 测试只执行一遍

- **WHEN** 查看 native 任一格的步骤序列
- **THEN** core 测试仅经 `cargo llvm-cov -p netwave` 执行一次，
  ci.yml 不出现第二处执行同一批 core 测试的命令

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
  python/node job 另在 windows-latest、macos-latest 与 linux-arm64
  （`ubuntu-26.04-arm`）各跑最新一格，验证 `.so`/`.pyd`/`.dylib`/`.node`
  addon 与零拷贝 base object 的平台 ABI；linux-arm64 格验证 aarch64 ABI。

Rust MUST 只跑单一 stable（`rust-toolchain.toml` 钉死当前 stable）——
消费者自带 toolchain 编译，`rust-version` 由 cargo 自动检查。

#### Scenario: python/node 版本格 + 平台格

- **WHEN** PR 触发 `ci.yml`
- **THEN** python job 在 ubuntu 含 `python/.python-version` 所指底线与
  最新稳定两格、node job 在 ubuntu 含 `engines.node` 所指底线与最新 LTS
  两格；两者另在 windows/macos/linux-arm64 各跑最新一格验 ABI，全部通过
  方可合并

#### Scenario: 矩阵数字单源

- **WHEN** 语言矩阵的版本号变更（如新 LTS 转换、新稳定 minor 落地）
- **THEN** 数字只改 `ci.yml` 矩阵格与对应底线声明文件，本 spec 措辞
  不随版本号变化

### Requirement: 覆盖率门槛生效（铁律七）

CI MUST 启用覆盖率采集并使 100% 行覆盖门槛生效，且 MUST 按 crate/包归属
独立度量、独立地板：core 用
`cargo llvm-cov -p netwave --codecov --output-path coverage/coverage-core.json`

- `scripts/coverage_gate.py coverage/coverage-core.json 100`
  （单 crate + codecov 行合并：同一行任一二进制执行过即计覆盖，绕开默认
  report 按实例计缺的重复计数，LL-057），Python 用
  `pytest-cov --cov-fail-under=100`（python 侧仅胶水时豁免项逐条标注），
  Node/wasm 用 vitest coverage `lines: 100` 阈值写进配置。结构性不可达代码
  MUST 逐条标注豁免（stable 通道 `#[cfg(not(coverage))]` / `# pragma: no cover` /
  `/* v8 ignore start/stop */`，vitest v8 provider；`#[coverage(off)]`
  nightly-only 禁用，LL-020）并附理由。impl 块宏属性行（`#[pymethods]` /
  `#[napi ...]`）MUST 由阅卷脚本按模式豁免（该行缺命中、源码行匹配该宏属性、
  下方首个代码行以 `impl` 开头）——llvm-cov 把宏属性行计作一个 region，宏
  展开 wrapper 的实例计数不并回该行（rustc#79651），该行结构性不可命中，且
  llvm-cov 不认 lcov-perl 的 `LCOV_EXCL_*` 行级标记、无稳定行级排除参数；
  源码读不到的缺行 MUST NOT 豁免（照常报红）；豁免 MUST NOT 硬编码行号。

绑定 crate（python、typescript/native）的 rust 胶水行 MUST 在各自语言 job
内以 `cargo llvm-cov show-env --sh --no-cfg-coverage` + 构建 + 外部测试驱动
（pytest / vitest）+ `cargo llvm-cov report --codecov` 采集
（show-env、clean、构建、外部测试、report MUST 同一 step——环境变量不跨 step；
`--no-cfg-coverage` 防 show-env 默认 `cfg(coverage)` 剥掉源码胶水；
typescript/native 的 report MUST 带 `--target <triple>`——napi `--platform` 把对象
建进 `target/<triple>/debug/`，不带则 report 只搜 host `target/debug` 报 not found；
python 的 maturin 不带 `--target`，对象落 host `target/debug`，report 无需 `--target`），
报告以 `--ignore-filename-regex` 剔除 core 路径后独立阅卷——core 行归
core 报告、胶水行归胶水报告，互不重复计分。原"绑定 crate 不进 llvm-cov
job 属工具作用域分离"口径废止：该口径的成立前提（绑定 crate 无法被
llvm-cov 度量）已被 show-env/report 外部驱动采集推翻。typescript/wasm crate 的
rust 行覆盖率暂不采集（vitest 驱动下插桩计数倒出未验证，另行 spike
立项），wasm 端 TS 层 vitest 100% 门槛不变。

#### Scenario: 空 crate 即 100%

- **WHEN** 各 crate/包只有最小 hello/往返代码且全部被测试执行
- **THEN** 覆盖率 job 通过（lines = 100%）

#### Scenario: 未测代码即红

- **WHEN** 新增一行未被任何测试执行的产码
- **THEN** 覆盖率 job 失败（exit ≠ 0），PR 不可合并

#### Scenario: 胶水行未测即红

- **WHEN** `python/src/` 或 `typescript/native/src/` 新增一行未被
  pytest / vitest 任何用例执行的 rust 胶水产码
- **THEN** 对应 job 的胶水阅卷（`coverage_gate.py` 对
  `coverage/coverage-python.json` / `coverage/coverage-native.json`）
  失败（exit ≠ 0），PR 不可合并

#### Scenario: 宏属性行按模式豁免不误红

- **WHEN** 胶水报告缺行是 `impl` 块上的 `#[pymethods]` / `#[napi ...]`
  宏属性行（宏展开 wrapper 实例计数不并回该行，rustc#79651）
- **THEN** 阅卷脚本按三重条件豁免该行并打印理由，阅卷不因此判红；
  缺行源码读不到时不豁免、照常报红

### Requirement: core 覆盖率全平台产出

core 覆盖率 MUST 在 native 四格（linux-x64、linux-arm64、windows-x64、
darwin-arm64）全部产出并各自阅卷，MUST NOT 以 step 级 `if` 限定单格。
平台差异仅剩编译器内联决策（`core/src/` 无 `cfg(windows)`/`cfg(unix)`/
`cfg(target_os)` 平台分支，grep 实证），codecov OR 合并语义可消。

#### Scenario: 四格各出数字

- **WHEN** rust job 四格运行完成
- **THEN** 每格产出 core 覆盖率报告且经 `coverage_gate.py` 阅卷通过

### Requirement: 覆盖率报告命名与留存

覆盖率报告 MUST 统一落 `coverage/` 目录（已被根 `.gitignore` 覆盖，
不入库），命名 `coverage-<被测对象>.json`（`coverage-core`、
`coverage-python`、`coverage-native`），MUST NOT 使用工具格式名或黑话
命名。每格产出的报告 MUST 以 upload-artifact 留存供人工核对。

#### Scenario: 报告可追溯

- **WHEN** CI 运行完成
- **THEN** 每格产物含对应 `coverage-<对象>.json`，文件名直接表明被测
  对象，人工可下载核对数字与缺行清单

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

### Requirement: 格式化归属单一来源

每类源文件的格式化 MUST 由唯一工具认领：Markdown 归 markdownlint +
Prettier，YAML、JavaScript、TypeScript、JSON 归 biome。认领关系 MUST 在
`biome.jsonc` 的 `files.includes` 与 Prettier 的管辖范围中互斥表达——
任一文件类型不得同时被两个格式化工具认领（两工具对同一文件输出不一致时
来回格式化产生 ping-pong diff）。本要求 MUST NOT 依赖新增专用检查脚本
执法：现有双闸门（`pnpm check:ts` 跑 biome、`pnpm check:md` 跑 Prettier）
已构成拦截网——认领一旦重叠，两工具输出分歧必使其中一道闸门红。

#### Scenario: YAML 纳入 biome 认领

- **WHEN** 运行 `pnpm check:ts`
- **THEN** 仓库内 YAML 文件（`pnpm-lock.yaml` 等生成物除外）经 biome
  格式检查，未经格式化的 YAML 使闸门 FAIL——YAML 自此有执法者，不再是
  仅靠散文约定的真空

#### Scenario: Markdown 认领不重叠

- **WHEN** 有人从 `biome.jsonc` 的 `files.includes` 移除 Markdown 排除项
- **THEN** `pnpm check:ts` 因 biome 与 Prettier 对既有 Markdown 的格式
  分歧（列表续行缩进等）报 FAIL，重叠在合并前即被拦截——归属不变式由
  现有闸门兜底，无需第三工具

#### Scenario: 归属变更留痕

- **WHEN** 任何改动调整某类文件的格式化认领工具
- **THEN** 该改动 MUST 经 openspec change 提案并更新本 Requirement，
  `biome.jsonc` 注释与 spec 条文不得各说各话
