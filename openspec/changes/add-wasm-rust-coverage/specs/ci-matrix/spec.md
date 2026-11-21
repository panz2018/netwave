# Spec Delta: ci-matrix

## MODIFIED Requirements

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
外部驱动采集度量。

typescript/wasm crate 的 rust 行覆盖率 MUST 以 minicov runtime +
`RUSTC_BOOTSTRAP=1` 解锁 `-Zno-profiler-runtime` 在钉死 stable 上编插桩 wasm，
由 node 驱动 vitest 套件采集：插桩构建走独立 target dir（不覆盖生产
`build:wasm` 产物），dump 导出 MUST 以 `#[cfg(feature = "coverage")]` 门控
（生产产物零污染），profraw MUST 由 worker 上下文内的钩子调 dump 倒出
（globalSetup 主进程读不到 worker wasm 内存），profraw 文件名 MUST 带 minicov
module_signature 防多 worker 覆盖，合并 profraw MUST 用 `llvm-profdata merge`
加 `-sparse`，合并后以 `llc` 把 `.ll`（由 `--emit=llvm-ir` 产出）编成宿主对象文件，
再调 `llvm-cov report` 加 `--codecov`（llvm-cov 读不了 wasm 符号）。报告 MUST
度量 core browser-gated 代码，
以 `--ignore-filename-regex` 剔除 python/native 路径后独立阅卷，落
`coverage/coverage-wasm.json` 并以 `scripts/coverage_gate.py ... 100` 阅卷。
wasm rust 覆盖率链前后 MUST 各执行 `clean_stray_profraw.py` 与
`cargo llvm-cov clean --workspace`。wasm rust 覆盖率 MUST 在全部 node matrix
格采集（不以 step 级 `if` 限定单格）。wasm 端 TS 层 vitest 100% 门槛不变。
浏览器侧（chromium Worker）rust 覆盖率 MUST NOT 采集（worker 内 profraw 倒出
未验证），维持 TS-only v8 覆盖率。

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

#### Scenario: wasm browser-gated 代码未测即红

- **WHEN** `core/src/` 中 `#[cfg(feature = "browser")]` 门控的
  `#[wasm_bindgen]` 代码新增一行未被 node 驱动 wasm 套件任何用例执行
- **THEN** `coverage_gate.py` 对 `coverage/coverage-wasm.json` 阅卷失败
  （exit ≠ 0），PR 不可合并

#### Scenario: wasm 覆盖率报告须含 core browser 路径且命中大于零

- **WHEN** 生成 `coverage/coverage-wasm.json`
- **THEN** 报告 MUST 含 `core/src/` 路径行且命中数 > 0（仅命令 exit 0
  不算通，LL-093）；缺目标路径行或全零命中即判链未生效、阅卷失败

#### Scenario: wasm 豁免须先经人工确认清单

- **WHEN** `coverage/coverage-wasm.json` 出现未达 100% 的行
- **THEN** MUST NOT 直接豁免；先列「真不可达」候选清单（逐条附文件+行号+
  不可达理由）交人工确认，确认后方可按 stable 通道标注豁免；未确认者
  MUST 补单元测试至 100%

#### Scenario: 生产 wasm 产物不含覆盖率导出

- **WHEN** 运行 `pnpm -C typescript build:wasm`（不带 coverage feature）
- **THEN** 产出的 wasm 不含 `__cov_dump`/`__cov_ptr`/`__cov_len` 导出
  （feature 门控），发布产物零污染

## ADDED Requirements

### Requirement: wasm 覆盖率阅卷工具取自 rustup llvm-tools 组件

wasm rust 覆盖率链所需的 `llc`/`llvm-profdata`/`llvm-cov` MUST 取自钉版 rust
工具链自带的 `llvm-tools` 组件（写进 `rust-toolchain.toml` 的 `components`，
rustup 激活工具链时自动装），MUST NOT 引入外部 clang、MUST NOT 依赖 sudo。
该组件版本随 `rust-toolchain.toml` 钉版走，MUST NOT 纳入
`scripts/versions/check_outdated.py` 作为独立追最新工具（已被工具链新鲜度
覆盖）。`scripts/run/test_ts.sh` MUST 从 `$(rustc --print sysroot)` 下的
llvm-tools bin 目录取这三个二进制。

#### Scenario: llvm-tools 组件随工具链自动就位

- **WHEN** rustup 激活 `rust-toolchain.toml` 钉定的工具链（本地或 CI）
- **THEN** `llvm-tools` 组件随之安装，`$(rustc --print sysroot)` 下 llvm-tools
  bin 目录含 `llc`/`llvm-profdata`/`llvm-cov`，`test_ts.sh` 无需外部安装步即可阅卷

#### Scenario: check:outdated 报 clang LAG

- **WHEN** 本机 clang 版本落后上游最新稳定版
- **THEN** `pnpm check:outdated` 在 CLI/tarball 组对 clang 报 LAG，按追最新
  消化

#### Scenario: action 缺版本或 clang 不兼容时可行动回退

- **WHEN** install-llvm-action 的 assets.json 缺目标 LLVM 版本，或追最新的
  clang 与 rustc LLVM 不兼容致 `.ll`→`.o` 失败
- **THEN** 前者用 action 的 `force-url` 输入指向 LLVM 官方对应平台 tarball；
  后者按「latest by default, roll back only on a real bug」回退，不阻塞
