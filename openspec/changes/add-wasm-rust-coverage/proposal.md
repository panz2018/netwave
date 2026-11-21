# Proposal

## Why

`typescript/wasm` 的 rust 行覆盖率当前不采集——ci-matrix spec 明写「vitest 驱动下插桩计数倒出未验证」。但 wasm 的整个 rust 表面就是 core 里 `#[cfg(feature = "browser")]` 门控的 `#[wasm_bindgen]` 代码（`core/src/frequency.rs`、`touchstone.rs`、`resources.rs` 共 19 处导出），native/python 覆盖率链跑 host target，**永远测不到这些 browser-gated 分支**。这是一块无人度量的 rust 代码。/tmp spike 已端到端证明 vitest 驱动下倒出 profraw 可行，故补上这块覆盖率。

## What Changes

- 新增 wasm rust 行覆盖率链：minicov runtime + `RUSTC_BOOTSTRAP=1` 解锁 `-Zno-profiler-runtime`，在钉死 stable 上编插桩 wasm，vitest node 驱动跑测试后由 worker 内 `afterAll` 钩子调 `__cov_dump()` 倒 profraw，`llvm-profdata merge` + clang 把 `.ll` 编成宿主 `.o` + `llvm-cov report --codecov` 出报告。
- 度量对象为 core browser-gated 代码，独立出 `coverage/coverage-wasm.json` + 地板 100（结构性不可达须先列清单人工确认才可豁免，否则补单测）。
- 新增工具 clang（`KyleMayes/install-llvm-action@v2`，追最新），纳入 CI 安装、`test_ts.sh` 探测、`check:outdated` section 3。
- ci-matrix spec「暂不采集」那句改为「已采集」并补对应 Scenario。
- 浏览器侧维持 TS-only v8 覆盖率不变；`typescript/wasm` 生产产物零污染（dump 导出 feature 门控、插桩走独立 target dir）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ci-matrix`: 覆盖率条款中「typescript/wasm crate 的 rust 行覆盖率暂不采集」改为以 minicov + `RUSTC_BOOTSTRAP` 外部驱动采集，新增 wasm rust 覆盖率链、clang 工具安装/探测/新鲜度、独立地板与豁免清单的 Requirement 与 Scenario。

## Impact

- 代码：`typescript/wasm/Cargo.toml`（minicov 依赖 + `coverage` feature）、`typescript/wasm/src/lib.rs`（`#[cfg(feature = "coverage")]` 门控的 `__cov_dump`/`__cov_ptr`/`__cov_len` 导出）。
- 测试脚本：`scripts/run/test_ts.sh`（新增 wasm 插桩构建 + dump + merge + report + gate 段，前后各加 `clean_stray_profraw.py` 与 `cargo llvm-cov clean --workspace`）。
- vitest：`typescript/vitest.wasm.config.ts`（加 `setupFiles`）、新增 setup 文件注册 worker 内 `afterAll` dump。
- CI：`.github/workflows/ci.yml` node job 加 `install-llvm-action` 安装步。
- 工具链：`scripts/versions/check_outdated.py` section 3 加 clang 探测。
- spec：`openspec/specs/ci-matrix/spec.md`。
- 受影响铁律：LL-092（外部驱动胶水覆盖率三坑）、LL-093（胶水报告须验命中）、LL-020（nightly-only 禁用——本 change 经裁决认定解锁编译 flag 不属此列）、LL-034（波及面同步）。

## Non-goals

- 不做浏览器侧（chromium Worker）的 rust 覆盖率——profraw 在 worker 线程 wasm 内存，须 postMessage 回主线程落盘，未验证，另立 spike。
- 不改 `typescript/wasm` 生产发布产物（dump 导出 feature 门控、插桩走独立 target dir，发布路径零污染）。
- 不动 native/python/core 既有覆盖率链与地板。
- 不在本 change 引入 nightly 工具链或源码级 nightly feature。

## Prior art

- wasm-bindgen 官方覆盖率方案（minicov + `-Zno-profiler-runtime` + profraw 倒出）：https://wasm-bindgen.github.io/wasm-bindgen/wasm-bindgen-test/coverage.html
- NEAR/Hacken wasmcov（宿主侧调 `capture_coverage` 倒 profraw + `.ll`→`.o` 阅卷）：https://github.com/hknio/wasmcov
- minicov（no_std LLVM profiling runtime）：https://github.com/Amanieu/minicov
- 仓库内 native glue 外部驱动覆盖率链（show-env + vitest + report）：`scripts/run/test_ts.sh`、账本 LL-092
- clang 跨平台安装 action：https://github.com/KyleMayes/install-llvm-action

## 专家增补

- 前置验证：正式落地前先在 /tmp 用真 `typescript/wasm`（wasm-bindgen 胶水 + minicov `coverage` feature）+ vitest worker 跑最小 spike，确认 `__cov_dump` 导出与 wasm-bindgen 胶水共存可加载、worker 内 dump 成立——spike 用的是手写 toy crate，未覆盖此点。
- profraw 命名带 minicov `module_signature`（`minicov::module_signature()`）防多 worker 覆盖，落 `scripts/run/test_ts.sh`。
- clang 版本兼容登记：若追最新的 clang 与 rustc LLVM major 不兼容致 `.ll`→`.o` 失败，按 `install_binaryen.sh` 既有哲学「latest by default, roll back only on a real bug」处理，不预先钉版。

## 已定裁决

- `RUSTC_BOOTSTRAP放行`：用 `RUSTC_BOOTSTRAP=1` 解锁 nightly-only 编译 flag `-Zno-profiler-runtime`，判定不违反 LL-020（LL-020 禁的是源码 nightly-only 属性，本处解锁编译 flag、不写 nightly feature）。
- `全矩阵采集`：全部 5 个 node matrix cell 都跑 wasm rust 覆盖率，不分平台门控。
- `仅node侧`：只做 node 驱动 wasm 套件的 rust 覆盖率，浏览器侧维持 TS-only。
- `install-llvm-action`：clang 用 `KyleMayes/install-llvm-action@v2` 一 step 跨四平台安装，追最新不缓存；assets.json 缺版本则用 `force-url`。
- `手动llvm链`：报告走手动 `llvm-profdata merge` + clang `.ll`→`.o` + `llvm-cov report --codecov`，不用 cargo-llvm-cov 包 wasm。
- `度量core-browser`：wasm 报告度量 core browser-gated 代码，`--ignore-filename-regex` 剔 python/native。
- `clang追最新`：clang 纳入 `check:outdated` section 3，追最新判 LAG（同 binaryen/wasm-pack），不钉 major。
- `地板100先列清单`：wasm rust 覆盖率地板 100，豁免前必须先列「真不可达」清单人工确认，否则补单元测试。
- `spec同步改`：ci-matrix spec「暂不采集」那句必须改为已采集并补 Scenario（LL-034）。
- `dump放setupFiles`：dump 钩子放 vitest `setupFiles` 的 worker 内 `afterAll`，不放 globalSetup（主进程读不到 worker wasm 内存）。
- `独立target加feature门控`：插桩走独立 target dir，`__cov_dump` 用 `#[cfg(feature = "coverage")]` 门控，生产产物零污染。
- `profraw带签名合并`：profraw 按 minicov module_signature 命名防覆盖，`llvm-profdata merge -sparse *.profraw` 合并。
- `前后双清理`：wasm 覆盖率链前后各加 `clean_stray_profraw.py` + `cargo llvm-cov clean --workspace`。
