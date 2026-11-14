# Spec Delta

## MODIFIED Requirements

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

### Requirement: 覆盖率门槛生效（铁律七）

CI MUST 启用覆盖率采集并使 100% 行覆盖门槛生效，且 MUST 按 crate/包归属
独立度量、独立地板：core 用
`cargo llvm-cov -p netwave --codecov --output-path coverage/coverage-core.json`

- `scripts/coverage_gate.py coverage/coverage-core.json 100`
  （单 crate + codecov 行合并：同一行任一二进制执行过即计覆盖，绕开默认
  report 按实例计缺的重复计数，LL-057），Python 用
  `pytest-cov --cov-fail-under=100`（python 侧仅胶水时豁免项逐条标注），
  Node/wasm 用 vitest coverage `lines: 100` 阈值写进配置。结构性不可达代码
  MUST 逐条
  标注豁免（stable 通道 `#[cfg(not(coverage))]` / `# pragma: no cover` /
  `/* v8 ignore start/stop */`，vitest v8 provider；`#[coverage(off)]`
  nightly-only 禁用，LL-020）并附理由。

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

#### Scenario: 胶水行未测即红（地板启用后）

- **WHEN** `python/src/` 或 `typescript/native/src/` 新增一行未被
  pytest / vitest 任何用例执行的 rust 胶水产码
- **THEN** 对应 job 的胶水阅卷（`coverage_gate.py` 对
  `coverage/coverage-python.json` / `coverage/coverage-native.json`）
  失败（exit ≠ 0），PR 不可合并

## ADDED Requirements

### Requirement: core 覆盖率全平台产出

core 覆盖率 MUST 在 native 四格（linux-x64、linux-arm64、windows-x64、
darwin-arm64）全部产出并各自阅卷，MUST NOT 以 step 级 `if` 限定单格。
平台差异仅剩编译器内联决策（`core/src/` 无 `cfg(windows)`/`cfg(unix)`/
`cfg(target_os)` 平台分支，grep 实证），codecov OR 合并语义可消。

#### Scenario: 四格各出数字

- **WHEN** rust job 四格运行完成
- **THEN** 每格产出 core 覆盖率报告且经 `coverage_gate.py` 阅卷通过

### Requirement: 覆盖率地板两阶段标定

新纳入度量的代码域（首次被某覆盖率报告覆盖的 crate/平台格：core 的
linux-arm64、windows-x64、darwin-arm64 三格与 python/native 两胶水域）
MUST 先以地板 0 运行一轮——阅卷照常打印百分比与缺行清单但恒不判红；
人工核对数字后，缺行逐条定性（真缺口补测试 / 结构性不可达按铁律七逐条
豁免），再于同一 change 内将地板翻至 100。已标定域（core@linux-x64）
在过渡期随四格统一命令同受地板 0 约束，标定轮后与其余格同步翻回 100。
地板数值以 ci.yml 阅卷命令参数为唯一定义处（散文不复制数字）。

#### Scenario: 标定轮只打印不判红

- **WHEN** 某代码域首轮纳入覆盖率度量
- **THEN** 该域阅卷以地板 0 运行，打印数字与缺行清单且 exit 0

#### Scenario: 标定完成即启用

- **WHEN** 人工核对确认该域缺行已清零（补测试或逐条豁免）
- **THEN** 同一 change 内该域地板参数翻至 100，此后未测即红

### Requirement: 覆盖率报告命名与留存

覆盖率报告 MUST 统一落 `coverage/` 目录（已被根 `.gitignore` 覆盖，
不入库），命名 `coverage-<被测对象>.json`（`coverage-core`、
`coverage-python`、`coverage-native`），MUST NOT 使用工具格式名或黑话
命名。每格产出的报告 MUST 以 upload-artifact 留存供人工核对。

#### Scenario: 报告可追溯

- **WHEN** CI 运行完成
- **THEN** 每格产物含对应 `coverage-<对象>.json`，文件名直接表明被测
  对象，人工可下载核对数字与缺行清单
