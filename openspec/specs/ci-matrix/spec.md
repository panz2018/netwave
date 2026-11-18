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
该链的命令细节 MUST 由 `scripts/run/test_rs.sh` 唯一承载：本地经根
`package.json` 的 `test:rs` 薄调用、CI 经 rust job 直接调
`scripts/run/test_rs.sh`，两端调同一脚本文件，参数物理同源不可漂移；
CI MUST NOT 为 rust job 补装 pnpm/Node 环境。
wasm32 格为 `cargo check`/wasm-pack 构建 + Node 侧 vitest 跑 wasm 产物。

#### Scenario: 矩阵全绿方可合并

- **WHEN** PR 触发 `ci.yml`
- **THEN** 五格 job 全部执行且 exit 0
- **AND** 任一格失败即整个 required check 失败，PR 不可合并

#### Scenario: core 测试只执行一遍

- **WHEN** 查看 native 任一格的步骤序列
- **THEN** core 测试仅经 `cargo llvm-cov -p netwave` 执行一次，
  ci.yml 不出现第二处执行同一批 core 测试的命令

#### Scenario: 本地与 CI 同脚本

- **WHEN** 对比本地 `pnpm test:rs` 与 ci.yml rust job 的测试步骤
- **THEN** 两端都只调用 `scripts/run/test_rs.sh`，llvm-cov、覆盖率地板、
  编译看门闸、profraw 清扫、插桩目录删除的参数只在该脚本内定义一处

### Requirement: rust 测试根聚合入口

根 `package.json` MUST 提供 `test:rs` 入口，薄调用 `scripts/run/test_rs.sh`；
该脚本 MUST 依次执行：profraw 前置清扫、`cargo-llvm-cov` 存在性探测（缺则打印
`scripts/install_cargo_llvm_cov.sh` 安装命令并非零退出，MUST NOT 自动安装）、
删除 `target/llvm-cov-target/`、core 覆盖率链与地板阅卷、编译看门闸、
profraw 后置清扫与再次删除 `target/llvm-cov-target/`（清扫顶后置块最前），且 MUST
`set -euo pipefail` 使任一环节失败即非零退出。本地跑绿 MUST 等价于 CI rust
job 同口径通过。

容差：存在性与退出码闸门，无数值阈值；覆盖率地板数值沿用铁律七与
`coverage_gate.py` 现有定义，本条不新增数值。

#### Scenario: 本地一条命令全链绿

- **WHEN** 开发者在仓库根运行 `pnpm test:rs` 且工具齐备
- **THEN** core 覆盖率报告产出并经地板阅卷，编译看门闸通过，脚本 exit 0

#### Scenario: 缺工具报错可行动

- **WHEN** `cargo-llvm-cov` 未安装时运行 `pnpm test:rs`
- **THEN** 脚本在任何 cargo 测试执行前以非零码退出，stderr 打印
  `bash scripts/install_cargo_llvm_cov.sh`，不发起网络安装

#### Scenario: 注入残留即红

- **WHEN** 仓库根存在人为放置的 `stray.profraw` 时运行 `pnpm test:rs`
- **THEN** 脚本以非零码失败并列出该文件名，且该文件已从磁盘删除

### Requirement: python 测试入口本地与 CI 同脚本

根 `package.json` MUST 提供 `test:py` 入口，薄调用 `scripts/run/test_py.sh`；
该脚本 MUST 依次执行：profraw 前置清扫、`cargo-llvm-cov` 与 `uv` 存在性探测
（缺则打印对应安装命令并非零退出，MUST NOT 自动安装）、
`cargo llvm-cov show-env`、`cargo llvm-cov clean --workspace`、`python/` 内
maturin develop 与 pytest、胶水覆盖率报告与地板阅卷、profraw 后置清扫与再次
`clean --workspace`，且 MUST `set -euo pipefail`。show-env、clean、build、test、
report MUST 共享脚本
单进程（插桩环境变量不跨进程）。本地跑绿 MUST 等价于 CI python job 同口径通过；
CI MUST NOT 为 python job 保留独立的 profraw drain 步骤（清扫已内置于脚本）。

容差：存在性与退出码闸门，无数值阈值；胶水覆盖率地板数值沿用铁律七与
`coverage_gate.py` 现有定义，本条不新增数值。

#### Scenario: python 入口本地全链绿

- **WHEN** 开发者在仓库根运行 `pnpm test:py` 且工具齐备
- **THEN** python 层 pytest 通过、胶水覆盖率报告产出并经地板阅卷，脚本 exit 0

#### Scenario: python 入口缺工具报错可行动

- **WHEN** 本地缺 `cargo-llvm-cov` 或 `uv` 时运行 `pnpm test:py`
- **THEN** 脚本在任何 maturin/pytest 执行前以非零码退出，stderr 打印对应安装
  命令，不发起网络安装

#### Scenario: python 胶水行未测即红

- **WHEN** `python/src/` 新增一行未被任何 pytest 用例执行的 rust 胶水产码
- **THEN** `pnpm test:py` 经 `coverage_gate.py` 对 `coverage/coverage-python.json`
  阅卷失败（exit ≠ 0），PR 不可合并

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
core 报告、胶水行归胶水报告，互不重复计分；绑定 crate 由 show-env/report
外部驱动采集度量。typescript/wasm crate 的 rust 行覆盖率暂不采集
（vitest 驱动下插桩计数倒出未验证），wasm 端 TS 层 vitest 100% 门槛不变。

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
workspace-layout「根级 Python 工具环境」）。

覆盖率的范围与阈值 MUST 定义在根 `pyproject.toml` 的 `[tool.coverage]`
与 `[tool.pytest.ini_options]`（单一真相源），`check:py` 命令行 MUST NOT
再携带 `--cov=` 范围或 `--cov-fail-under=` 阈值——范围列于命令行属易漏
清单，改测试域时须同步改命令与 CI，漂移即失效。行覆盖率地板范围 =
`scripts/versions` 域 + `scripts/coverage_gate.py` + `scripts/check_comments.py`
三者，阈值数值以 `pyproject.toml` 为唯一定义处（散文不复制数字）；
范围外的 `scripts/` 其余脚本暂不设地板。

#### Scenario: 闸门回归 CI 兜底

- **WHEN** 任一 PR 改动 `scripts/` 且使治理脚本单测失败
- **THEN** lint job FAIL 并指向失败用例——闸门脚本的回归不能只靠本地

#### Scenario: 不重复命令真相源

- **WHEN** 查看 lint job 步骤序列
- **THEN** 单测仅经 `pnpm check`（内含 `check:py`）运行一次，
  ci.yml 不出现第二处单测命令

#### Scenario: versions 域覆盖率地板生效

- **WHEN** `scripts/versions` 域行覆盖率低于 `pyproject.toml` 所钉
  `fail_under` 阈值（含新增未测行、也含删除既有覆盖用例）
- **THEN** `pnpm check:py` 退出码非 0，lint job FAIL——覆盖率不得
  无声下滑；结构性不可达行如需豁免，按铁律七逐条标注并附理由

#### Scenario: 阅卷人与门禁脚本覆盖率地板生效

- **WHEN** `scripts/coverage_gate.py` 或 `scripts/check_comments.py` 出现
  未测行（新增分支、或删除既有覆盖用例）
- **THEN** `pnpm check:py` 退出码非 0，lint job FAIL——阅卷人回归 =
  全部覆盖率地板失效，门禁脚本回归 = 该门禁静默失效，两者必须有测试兜底

#### Scenario: 覆盖率配置单一真相源

- **WHEN** 查看根 `package.json` 的 `check:py` 命令
- **THEN** 其中不含 `--cov=` 或 `--cov-fail-under=`——范围与阈值只在
  `pyproject.toml` 声明一处；命令行与配置文件两处并存即 review 打回
  （两份清单必漂移）

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
  格式检查，未经格式化的 YAML 使闸门 FAIL——YAML 格式有执法者，
  不靠散文约定

#### Scenario: Markdown 认领不重叠

- **WHEN** 有人从 `biome.jsonc` 的 `files.includes` 移除 Markdown 排除项
- **THEN** `pnpm check:ts` 因 biome 与 Prettier 对既有 Markdown 的格式
  分歧（列表续行缩进等）报 FAIL，重叠在合并前即被拦截——归属不变式由
  现有闸门兜底，无需第三工具

#### Scenario: 归属变更留痕

- **WHEN** 任何改动调整某类文件的格式化认领工具
- **THEN** 该改动 MUST 经 openspec change 提案并更新本 Requirement，
  `biome.jsonc` 注释与 spec 条文不得各说各话

### Requirement: 覆盖率中间产物不跨轮残留

凡驱动插桩代码执行的测试 harness MUST 在测试会话的开始与结束两处清除自身子树内
`target/` 之外的 `*.profraw`；`target/` 外出现 profraw = 覆盖率采集链未生效的
充分证据，故 harness MUST 先删除再报错退出（非警告、非静默、无跳过开关），
报错文本列出被删文件名与个数作为证据。
清扫逻辑 MUST 只有一份实现：`drain_stray_profraw` 函数（与剪枝清单
`SKIP_DIRS` 同库），CLI 壳 `scripts/run/clean_stray_profraw.py` 供 shell
消费；两个 pytest conftest 与 vitest 全局 setup MUST 消费同一实现
（import 共享函数或调用 CLI），MUST NOT 各自复制清扫逻辑。

CI MUST 与本地同流程：每个构建插桩代码的 job MUST 在测试步骤**之前与之后**
各有一道清理，扫描全仓 `target/` 外的 `*.profraw`，语义与 harness 钩子一致
（先删后报错）；rust job 的清扫由 `scripts/run/test_rs.sh` 内置，python job 的
清扫由 `scripts/run/test_py.sh` 内置，node job 的清理步骤 MUST 调用
`python3 scripts/run/clean_stray_profraw.py`；未插桩的 job（不产 profraw）
MUST NOT 加此步骤。

`scripts/run/test_rs.sh` MUST 在覆盖率步骤之前与之后各删除一次
`target/llvm-cov-target/` 整目录，MUST NOT 依赖 `cargo llvm-cov clean`——
该命令在 `CACHEDIR.TAG` 缺失时静默 no-op（exit 0 但不删），残留的旧插桩
二进制会按旧行号污染新报告。`scripts/run/test_py.sh` MUST 在覆盖率链之前与
之后各执行一次 `cargo llvm-cov clean --workspace`——python 胶水的插桩对象落
host `target/debug`，`clean --workspace` 是其适用的清理命令。两个脚本的后置
清理块 MUST 以 profraw 清扫（`clean_stray_profraw.py`）开头、插桩清理其后：
带"断链当轮即红"检测职责的清扫顶到后置块最前，防日后向后置块追加命令把清扫
挤到末尾而削弱检测；散落清扫（`SKIP_DIRS` 含 `target`，只删 `target/` 外）与
插桩清理（只清 `target/` 内）作用集互斥，换序不互相破坏。

容差：存在性闸门，无数值阈值；判定口径 = `target/` 外 `*.profraw` 计数为 0，
且 `target/llvm-cov-target/` 于 `test:rs` 运行前后均不存在、`test:py` 运行前后
`target/` 外 profraw 计数均为 0（不涉及数值计算真值，故不引用 oracle
manifest key）。

#### Scenario: 散落即报错并清除

- **WHEN** 测试会话开始时 `target/` 外存在 `*.profraw`（上一轮采集链断裂的残留）
- **THEN** harness 以非零码失败，报错文本列出被删文件名与个数
- **AND** 这些文件已从磁盘删除，工作区无残留

#### Scenario: 干净工作区静默通过

- **WHEN** 测试会话开始与结束时 `target/` 外均无 `*.profraw`
- **THEN** harness 不因本条款报错，正常执行测试并按原有闸门判定

#### Scenario: 断链当轮即红

- **WHEN** 本次测试会话自身因采集链未生效而在 `target/` 外写出 `*.profraw`
- **THEN** 会话结束处的检查当场以非零码失败，本轮覆盖率报告不被当作可信数字消费

#### Scenario: 下一轮自愈无需人工确认

- **WHEN** 上一轮因散落残留报错后，采集链已恢复正常并重跑同一测试命令
- **THEN** harness 通过（报错只发生一次），无需人工设置开关或删除文件

#### Scenario: 报告类产物与 target 内产物不误删

- **WHEN** 工作区存在 `.coverage`、`coverage/*.json` 或 `target/` 内的 profraw
  及清单文件
- **THEN** 散落清扫扫描不删除其中任何一项，覆盖率报告不受影响；
  `target/llvm-cov-target/` 整目录由 rust 入口的前后置删除，属另一机制，
  不经散落扫描器

#### Scenario: CI 测试前后各有一道清理闸门

- **WHEN** 查看 `.github/workflows/ci.yml` 中构建插桩代码的 job（rust / python /
  node）步骤序列
- **THEN** 测试步骤之前与之后各有一道清理，扫描 `target/` 外的 `*.profraw`，
  发现即先删后以非零码失败并列出文件名与个数
- **AND** rust job 的清理在 `scripts/run/test_rs.sh` 内、python job 的清理在
  `scripts/run/test_py.sh` 内，node job 的清理步骤调用
  `python3 scripts/run/clean_stray_profraw.py`
- **AND** 未插桩的 job（wasm、lint、bench）无此步骤

#### Scenario: 旧插桩二进制不跨轮残留

- **WHEN** `target/llvm-cov-target/` 存在上一轮遗留的插桩二进制与 profraw
- **THEN** `pnpm test:rs` 在运行 `cargo llvm-cov` 前删除该目录，覆盖率报告
  只含当前源码编译二进制的 region 数据
- **AND** 脚本结束后该目录再次删除，下一轮无旧污染向量

#### Scenario: python 入口前后各清一次插桩

- **WHEN** 查看 `scripts/run/test_py.sh` 的命令序列
- **THEN** `cargo llvm-cov clean --workspace` 在覆盖率链之前与之后各出现一次
- **AND** 后置清理块中 `clean_stray_profraw.py` 排在 `clean --workspace` 之前

#### Scenario: 后置块清扫先于插桩清理

- **WHEN** 查看 `scripts/run/test_rs.sh` 与 `scripts/run/test_py.sh` 的后置清理块
- **THEN** 两脚本后置块均以 `clean_stray_profraw.py` 开头、插桩清理命令其后，
  带检测职责的清扫不被后置追加的命令挤到末尾

#### Scenario: 清扫实现唯一不复制

- **WHEN** 在仓库内 grep profraw 清扫的遍历删除逻辑
- **THEN** 遍历 + 剪枝 + 先删后报的实现只存在于 `scripts/versions/lib/repository.py`
  一处，conftest 与 vitest setup 均为 import 或 CLI 消费，无第二份复制

### Requirement: 嵌套 Python 工程自带 pytest 配置

仓库内每个嵌套的 uv 工程（仓库根以外的 `pyproject.toml`）MUST 自带
`[tool.pytest.ini_options]` 表，并 MUST 在声明 `[tool.coverage]` 时钉住
`run.source`。理由：pytest 从调用目录上溯到最近一个含该表的 `pyproject.toml`
并整套采用，缺表的工程会继承仓库根配置——根 `addopts` 的裸 `--cov` 会覆盖命令行
传入的 `--cov=<pkg>`，使该工程的覆盖率地板静默扩大到整仓。该约束 MUST 由
`scripts/check_py.py` 机器强制。

容差：存在性闸门，无数值阈值；判定口径 = 嵌套 `pyproject.toml` 是否含
`[tool.pytest.ini_options]`、含 `[tool.coverage]` 者是否含 `run.source`，目标值均为
"是"（不涉及数值计算真值，故不引用 oracle manifest key）。

#### Scenario: 缺 pytest 表即报错

- **WHEN** 仓库根以外存在含 `[project]` 但无 `[tool.pytest.ini_options]` 的
  `pyproject.toml`
- **THEN** `python3 scripts/check_py.py` 以非零码失败，报错路径指向该文件

#### Scenario: 声明覆盖率却不钉范围即报错

- **WHEN** 某嵌套工程的 `pyproject.toml` 含 `[tool.coverage.report].fail_under`
  却无 `[tool.coverage.run].source`
- **THEN** `python3 scripts/check_py.py` 以非零码失败并指明 `run.source` 缺失

#### Scenario: python 工程覆盖率只测本包

- **WHEN** 在 `python/` 目录执行 `uv run pytest`
- **THEN** 覆盖率报告只含 `netwave/` 下的 Python 文件，不含 `tests/`、
  `conftest.py` 与仓库根 `scripts/` 下的文件
- **AND** 地板取自 `python/pyproject.toml` 的 `[tool.coverage.report].fail_under`，
  CI 与本地执行同一条命令得到同一测量范围
