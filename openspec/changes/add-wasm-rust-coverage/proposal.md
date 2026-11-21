# Proposal

## Why

`typescript/wasm` 的 rust 行覆盖率当前不采集——ci-matrix spec 明写「vitest 驱动下插桩计数倒出未验证」。但 wasm 的整个 rust 表面就是 core 里 `#[cfg(feature = "browser")]` 门控的 `#[wasm_bindgen]` 代码（`core/src/frequency.rs`、`touchstone.rs`、`resources.rs` 共 19 处导出），native/python 覆盖率链跑 host target，**永远测不到这些 browser-gated 分支**。这是一块无人度量的 rust 代码。/tmp spike 已端到端证明 vitest 驱动下倒出 profraw 可行，故补上这块覆盖率。

## What Changes

- 新增 wasm rust 行覆盖率链：minicov runtime + `RUSTC_BOOTSTRAP=1` 解锁 `-Zno-profiler-runtime`，在钉死 stable 上编插桩 wasm，vitest node 驱动跑测试后由 worker 内 `afterAll` 钩子调 `__cov_dump()` 倒 profraw，`llvm-profdata merge` + `llc` 把 `.ll` 编成宿主 `.o` + `llvm-cov report --codecov` 出报告。
- 度量对象为 core browser-gated 代码，独立出 `coverage/coverage-wasm.json` + 地板 100（结构性不可达须先列清单人工确认才可豁免，否则补单测）。
- 编译期 C 编译器：minicov `build.rs` 硬编码用 clang 编其 wasm32 C runtime（gcc 无 wasm32 后端），故需一个能编 wasm32 的 clang——用 **wasi-sdk**（自带标准 clang，192MB tarball 解压到 `~/.local`，零 sudo），新增 `scripts/install_wasi_sdk.sh`（仿 install_binaryen.sh）。
- 阅卷三件套（`llc`/`llvm-profdata`/`llvm-cov`）取自钉版 rust 工具链自带的 `llvm-tools` 组件（写进 `rust-toolchain.toml` 的 `components`，rustup 本地与 CI 激活工具链时自动装），零额外下载、零 sudo、版本天然与 rustc 的 LLVM 一致。
- ci-matrix spec「暂不采集」那句改为「已采集」并补对应 Scenario。
- 浏览器侧维持 TS-only v8 覆盖率不变；`typescript/wasm` 生产产物零污染（dump 导出 feature 门控、插桩走独立 target dir）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ci-matrix`: 覆盖率条款中「typescript/wasm crate 的 rust 行覆盖率暂不采集」改为以 minicov + `RUSTC_BOOTSTRAP` 外部驱动采集，新增 wasm rust 覆盖率链、编译期 clang 取自 wasi-sdk、阅卷工具取自 llvm-tools 组件、独立地板与豁免清单的 Requirement 与 Scenario。

## Impact

- 代码：`typescript/wasm/Cargo.toml`（minicov 依赖 + `coverage` feature）、`typescript/wasm/src/lib.rs`（`#[cfg(feature = "coverage")]` 门控的 `__cov_dump`/`__cov_ptr`/`__cov_len` 导出）。
- 测试脚本：`scripts/run/test_ts.sh`（新增 wasm 插桩构建 + dump + merge + report + gate 段，编译期 CC 指向 wasi-sdk clang、阅卷工具从 `rustc --print sysroot` 下的 llvm-tools bin 目录取，前后各加 `clean_stray_profraw.py` 与 `cargo llvm-cov clean --workspace`）。
- vitest：`typescript/vitest.wasm.config.ts`（加 `setupFiles`）、新增 setup 文件注册 worker 内 `afterAll` dump。
- 工具链：`rust-toolchain.toml` 的 `components` 加 `llvm-tools`（rustup 自动装，本地与 CI 一致）；新增 `scripts/install_wasi_sdk.sh`（下 wasi-sdk 到 `~/.local/opt/wasi-sdk`，仿 install_binaryen.sh）。
- CI：node job 加 `scripts/install_wasi_sdk.sh` 安装步（wasi-sdk clang）。
- 新鲜度：`scripts/versions/check_outdated.py` section 3 加 wasi-sdk clang 探测（同 binaryen/wasm-pack）。
- spec：`openspec/specs/ci-matrix/spec.md`。
- 受影响铁律：LL-092（外部驱动胶水覆盖率三坑）、LL-093（胶水报告须验命中）、LL-020（nightly-only 禁用——本 change 经裁决认定解锁编译 flag 不属此列）、LL-034（波及面同步）。

## Non-goals

- 不做浏览器侧（chromium Worker）的 rust 覆盖率——profraw 在 worker 线程 wasm 内存，须 postMessage 回主线程落盘，未验证，另立 spike。
- 不改 `typescript/wasm` 生产发布产物（dump 导出 feature 门控、插桩走独立 target dir，发布路径零污染）。
- 不动 native/python/core 既有覆盖率链与地板。
- 不在本 change 引入 nightly 工具链或源码级 nightly feature。

## Prior art

- wasm-bindgen 官方覆盖率方案（minicov + `-Zno-profiler-runtime` + profraw 倒出）：<https://wasm-bindgen.github.io/wasm-bindgen/wasm-bindgen-test/coverage.html>
- NEAR/Hacken wasmcov（宿主侧调 `capture_coverage` 倒 profraw + `.ll`→`.o` 阅卷）：<https://github.com/hknio/wasmcov>
- minicov（no_std LLVM profiling runtime）：<https://github.com/Amanieu/minicov>
- 仓库内 native glue 外部驱动覆盖率链（show-env + vitest + report）：`scripts/run/test_ts.sh`、账本 LL-092
- cargo-llvm-cov 阅卷即用 rustup `llvm-tools` 组件的 `llvm-cov`/`llvm-profdata`（非独立 clang），本 change 沿用同一取工具方式
- wasi-sdk（自带标准 clang + wasm sysroot，解压即用无 sudo）：<https://github.com/WebAssembly/wasi-sdk>
- 仓库内同款 tarball 直装脚本先例：`scripts/install_binaryen.sh`、`install_wasm_pack.sh`、`install_cargo_llvm_cov.sh`

## 专家增补

- 前置验证（2026-11-20 已跑通）：在 /tmp 用真 `typescript/wasm`（wasm-bindgen 胶水 + core browser-gated + minicov `coverage` feature）以 wasi-sdk clang 编插桩 wasm、node 加载调 dump 倒出 187KB profraw、merge+llc+llvm-cov 出含 `core/src/{frequency,resources,touchstone}.rs` 的报告——编译/加载/dump/阅卷四段均通。
- profraw 命名带 minicov `module_signature`（`minicov::module_signature()`）防多 worker 覆盖，落 `scripts/run/test_ts.sh`。
- 编译期 clang 与 rustc LLVM major 对齐：wasi-sdk 34 自带 clang 23.1，与钉版 rustc（LLVM 23）同 major；插桩 IR/profraw 由 rustc 产、阅卷由 llvm-tools（同份 LLVM）做，wasi-sdk clang 仅编 minicov 的 freestanding C runtime（`-nostdlibinc`），不参与 IR/profraw 格式，错配风险低。
- `zig cc` 实测不可用：zig 内置 clang 但给 wasm32 对象打非标准 ELF machine（`e_machine` 0xb7≠`EM_WASM` 247），`rust-lld` 无视其对象致符号未定义，故排除零下载的 zig 路线。

## 已定裁决

- `RUSTC_BOOTSTRAP放行`：用 `RUSTC_BOOTSTRAP=1` 解锁 nightly-only 编译 flag `-Zno-profiler-runtime`，判定不违反 LL-020（LL-020 禁的是源码 nightly-only 属性，本处解锁编译 flag、不写 nightly feature）。
- `全矩阵采集`：全部 5 个 node matrix cell 都跑 wasm rust 覆盖率，不分平台门控。
- `仅node侧`：只做 node 驱动 wasm 套件的 rust 覆盖率，浏览器侧维持 TS-only。
- `手动llvm链`：报告走手动 `llvm-profdata merge` + `llc` `.ll`→`.o` + `llvm-cov report --codecov`，不用 cargo-llvm-cov 包 wasm。
- `度量core-browser`：wasm 报告度量 core browser-gated 代码，`--ignore-filename-regex` 剔 python/native。
- `llvm-tools组件取工具`：阅卷三件套取自钉版 rust 工具链的 `llvm-tools` 组件（写进 `rust-toolchain.toml` 的 `components`，rustup 自动装），阅卷不需 sudo、不进 check:outdated（版本随 `rust-toolchain.toml` 钉版走，已被工具链新鲜度覆盖）。
- `wasi-sdk编C`：编译期 minicov 的 wasm32 C runtime 用 wasi-sdk 自带的标准 clang（`scripts/install_wasi_sdk.sh` 下 192MB tarball 到 `~/.local/opt/wasi-sdk`，无 sudo），纳入 check:outdated section 3（同 binaryen/wasm-pack）；gcc 无 wasm32 后端、zig cc 对象 ELF machine 非标准均实测排除。
- `地板100先列清单`：wasm rust 覆盖率地板 100，豁免前必须先列「真不可达」清单人工确认，否则补单元测试。
- `spec同步改`：ci-matrix spec「暂不采集」那句必须改为已采集并补 Scenario（LL-034）。
- `dump放setupFiles`：dump 钩子放 vitest `setupFiles` 的 worker 内 `afterAll`，不放 globalSetup（主进程读不到 worker wasm 内存）。
- `独立target加feature门控`：插桩走独立 target dir，`__cov_dump` 用 `#[cfg(feature = "coverage")]` 门控，生产产物零污染。
- `profraw带签名合并`：profraw 按 minicov module_signature 命名防覆盖，`llvm-profdata merge -sparse *.profraw` 合并。
- `前后双清理`：wasm 覆盖率链前后各加 `clean_stray_profraw.py` + `cargo llvm-cov clean --workspace`。
- `archive体检跳过`：本 change 归档阶段（archive 态）的 health-check 只读体检
  一次性跳过（2026-11-20），apply 态体检照常执行。
- `编译阅卷工具分离`（2026-11-20 实测定案）：编译期需 wasm32-capable clang（minicov
  build.rs 硬编码 `cfg.compiler("clang")`，gcc 无 wasm32 后端）→ wasi-sdk（192MB
  tarball、无 sudo、标准 clang）；阅卷期用 llvm-tools 组件（rustup、零下载、与 rustc
  LLVM 精确匹配）。两者均无 sudo，dependency-upgrade spec 无需改动（wasi-sdk 作直装
  工具入 check:outdated section 3，llvm-tools 随钉版走）。旧「纯 llvm-tools 无 clang」
  结论错在漏了 minicov build.rs 编 C runtime 这步，已推翻。
