# ci-matrix Specification Delta

## MODIFIED Requirements

### Requirement: 全项目浏览器测试根聚合入口

根 `package.json` MUST 提供 `test:browser` 入口，薄调用浏览器端测试脚本
`browser/scripts/test.sh`（随浏览器端测试资产归位迁入 `browser/`），使本地单命令
复现全项目浏览器端测试面（browser 产物构建、node 驱动单元套件、真浏览器 e2e 套件、
browser rust 覆盖率链），且 MUST `set -euo pipefail` 并纳入 `pnpm test` 聚合链。
根入口 MUST 以 `pnpm -C browser test` 委托形式调用（`browser/package.json` 的
`test` 指向 `bash scripts/test.sh`），使本地与 CI 走同一命令、参数物理同源。脚本
对工具与浏览器 MUST 只探测存在性、缺失即非零退出并打印安装命令，MUST NOT 发起
网络安装。`ci.yml` 的 browser job 测试步骤 MUST 缩成一行调该委托命令，前置安装步
保留。

容差：存在性与退出码闸门，无数值阈值；browser 壳覆盖率阈值数值以对应 vitest
配置的 `thresholds` 为唯一定义处，本条不复制数值。

#### Scenario: wasm 入口本地全链绿

- **WHEN** 开发者在仓库根运行 `pnpm test:browser` 且工具与 chromium 齐备
- **THEN** 脚本依次执行工具链探测（含 llvm-tools/wasi-sdk/wasm-bindgen）、
  browser 产物构建、node 驱动单元套件、插桩构建 + wasm-bindgen 胶水 + env 驱动
  真浏览器 e2e（关 v8）倒 profraw + merge/llc/export + rust lcov 地板阅卷、
  生产真浏览器套件，两套件均按各自 vitest 配置阈值阅卷通过、rust lcov 经地板
  阅卷，脚本 exit 0

#### Scenario: wasm 入口缺覆盖率工具报错可行动

- **WHEN** 本地缺 llvm-tools 三件套（`llc`/`llvm-profdata`/`llvm-cov`）、
  wasi-sdk clang 或 `wasm-bindgen` 之一时运行 `pnpm test:browser`
- **THEN** 脚本在插桩构建前以非零码退出，stderr 打印对应安装指引
  （`rustup component add llvm-tools` / `browser/scripts/install_wasi_sdk.sh` /
  `browser/scripts/install_wasm_bindgen_cli.sh`），不发起自动安装

#### Scenario: wasm 入口缺工具或缺浏览器报错可行动

- **WHEN** 本地缺 `wasm-pack`、`wasm-opt`、`wasm32-unknown-unknown` 目标或 chromium
  之一时运行 `pnpm test:browser`
- **THEN** 脚本在任何 build/测试执行前以非零码退出，stderr 打印对应安装命令
  （`scripts/install_wasm_pack.sh`、`scripts/install_binaryen.sh`、
  `rustup target add wasm32-unknown-unknown`、playwright chromium 安装命令），
  不发起网络安装

#### Scenario: ci.yml wasm job 不再内联测试命令

- **WHEN** 检查 `ci.yml` 的 browser job 测试步骤
- **THEN** 测试步骤为单行 `pnpm -C browser test`，无内联的产物构建 /
  `test:unit` / `test:e2e` 命令；前置工具安装步仍在调该命令之前

#### Scenario: 根 test:wasm 纳入本地聚合

- **WHEN** 检查根 `package.json` 的 `test` 聚合脚本
- **THEN** 聚合链含 `pnpm test:browser`，本地 `pnpm test` 覆盖到真浏览器套件

#### Scenario: node 版本轴 wasm 验证保留

- **WHEN** 检查 `scripts/run/test_ts.sh`
- **THEN** 仍含 browser 产物构建与 node 驱动单元套件，node 矩阵继续验浏览器
  产物跨 node 版本可加载；browser 产物构建在浏览器脚本与 `test_ts.sh` 各自
  幂等执行、互不依赖（无跨 job `needs` 依赖）

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
外部驱动采集度量。typescript/wasm crate 的 rust 行覆盖率 MUST 以 minicov runtime +
`RUSTC_BOOTSTRAP=1` 解锁 `-Zno-profiler-runtime` 在钉死 stable 上编插桩 wasm，
由真浏览器 job（chromium Worker）采集——core 的 fetch 后端仅在真实浏览器
global scope 上解析，node harness 的 fakeSelf 恒落「无 fetch 能力 scope」臂，
故这些行 MUST NOT 由 node 驱动 vitest 采集（采不到即漏分母）：minicov 的
wasm32 C runtime MUST 由能编 wasm32 的 clang（wasi-sdk 自带，`CC` 指向
`browser/scripts/install_wasi_sdk.sh` 装到 `~/.local` 的 clang）编译（gcc 无 wasm32
后端），插桩构建走独立 target dir（不覆盖生产 `build:browser` 产物），dump 导出
MUST 以 `#[cfg(feature = "coverage")]` 门控（生产产物零污染），profraw MUST
由浏览器测试末尾经 worker 控制消息调 dump 倒出、以 base64 经 vitest browser
command 回传 node 落盘（Uint8Array 直传经序列化降级成 Object，故须 base64），
profraw 文件名 MUST 带 minicov module_signature 防多 worker 覆盖，合并 profraw
MUST 用 `llvm-profdata merge` 加 `-sparse`，合并后以 `llc` 把 `.ll`（由
`--emit=llvm-ir` 产出）编成宿主对象文件，再调 `llvm-cov export --format=lcov`
（llvm-cov 读不了 wasm 符号，故须先 `llc` 编宿主 `.o`；llvm-cov 无 `--codecov`
flag，那是 cargo-llvm-cov 的，散装 `.o` 无独立 codecov 入口）。报告 MUST 度量
core browser-gated 代码，以 `--ignore-filename-regex` 剔除 `.cargo/registry`
第三方后独立阅卷，落 `coverage/coverage-browser.lcov` 并以
`scripts/coverage_gate.py ... 99` 阅卷（该脚本 MUST 支持 lcov tracefile 输入，
把每条 `DA:<行>,<命中>` 视作 OR 合并后的行级命中；浏览器端 rust 地板为 99 而非
100——fetch「无 fetch-capable scope」臂读 `js_sys::global()` 真实全局、无参数
注入点，任何测试或 mock 均不可达）。
浏览器端 rust 覆盖率链前后 MUST 各执行 `clean_stray_profraw.py`。浏览器端 rust
覆盖率 MUST 仅在真浏览器 job 单采（node matrix 格的浏览器套件维持 TS-only v8，不产
浏览器 lcov）。浏览器端 TS 层 vitest 100% 门槛不变。

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
  `#[wasm_bindgen]` 代码新增一行未被真浏览器 wasm 套件任何用例执行
- **THEN** `coverage_gate.py` 对 `coverage/coverage-browser.lcov` 阅卷失败
  （exit ≠ 0），PR 不可合并

#### Scenario: wasm 覆盖率报告须含 core browser 路径且命中大于零

- **WHEN** 生成 `coverage/coverage-browser.lcov`
- **THEN** 报告 MUST 含 `core/src/` 路径行且命中数 > 0（仅命令 exit 0
  不算通，LL-093）；缺目标路径行或全零命中即判链未生效、阅卷失败

#### Scenario: wasm 豁免须先经人工确认清单

- **WHEN** `coverage/coverage-browser.lcov` 出现未达 99% 地板的行
- **THEN** MUST NOT 直接豁免；先列「真不可达」候选清单（逐条附文件+行号+
  不可达理由）交人工确认，确认后方可按 stable 通道标注豁免或计入 99 地板
  容差；未确认者 MUST 补单元测试至达标（fetch「无 fetch-capable scope」臂
  经人工确认属真不可达，是 99 地板的由来）

#### Scenario: 生产 wasm 产物不含覆盖率导出

- **WHEN** 运行 `pnpm -C browser build:browser`（不带 coverage feature）
- **THEN** 产出的 wasm 不含 `__cov_dump`/`__cov_ptr`/`__cov_len` 导出
  （feature 门控），发布产物零污染

### Requirement: wasm 覆盖率链的编译与阅卷工具均无需 sudo

wasm rust 覆盖率链分两段取工具，均 MUST NOT 依赖 sudo：编译期 minicov 的
wasm32 C runtime MUST 由 wasi-sdk 自带的标准 clang 编译（`browser/scripts/install_wasi_sdk.sh`
下 tarball 解压到 `~/.local/opt/wasi-sdk`，仿 install_binaryen.sh）；阅卷期
`llc`/`llvm-profdata`/`llvm-cov` MUST 取自钉版 rust 工具链自带的 `llvm-tools`
组件（写进 `rust-toolchain.toml` 的 `components`，rustup 激活工具链时自动装）。
`scripts/run/test_browser.sh` MUST 从 `$(rustc --print sysroot)` 下的 llvm-tools bin
目录取阅卷三件套，MUST 探测 wasi-sdk clang、缺失时提示跑
`browser/scripts/install_wasi_sdk.sh` 并以非零退出。

#### Scenario: 缺 wasi-sdk clang 时本地测试入口可行动报错

- **WHEN** 本机未装 wasi-sdk clang 时运行 `pnpm test:wasm`
- **THEN** `test_browser.sh` 探测段打印跑 `browser/scripts/install_wasi_sdk.sh` 的指引并以非零退出，
  不发起自动安装

#### Scenario: llvm-tools 组件随工具链自动就位

- **WHEN** rustup 激活 `rust-toolchain.toml` 钉定的工具链（本地或 CI）
- **THEN** `llvm-tools` 组件随之安装，`$(rustc --print sysroot)` 下 llvm-tools
  bin 目录含 `llc`/`llvm-profdata`/`llvm-cov`，`test_browser.sh` 无需外部安装步即可阅卷
