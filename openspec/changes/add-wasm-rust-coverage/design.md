# Design

## Context

见 proposal.md「Why」。当前 wasm 的 rust 表面是 core 里 browser-gated 的
`#[wasm_bindgen]` 代码，native/python 覆盖率链跑 host target 测不到。/tmp spike
已端到端验证（真 `typescript/wasm` + core browser-gated）：stable 1.100（LLVM 23）

- `RUSTC_BOOTSTRAP=1` + `-Zno-profiler-runtime` 编插桩 wasm，minicov runtime
  自包含（wasm 无外部 import），Node 侧调 dump 拷出 profraw，`llvm-profdata merge`
- `.ll`→`.o` + `llvm-cov report` 出含 `core/src/*.rs` 的报告。

工具分两段（实测）：编译期 minicov `build.rs` 硬编码用 clang 编其 wasm32 C
runtime（gcc 无 wasm32 后端），需 wasi-sdk 自带的标准 clang；阅卷期
`llc`/`llvm-profdata`/`llvm-cov` 取自钉版 rust 工具链自带的 `llvm-tools` 组件
（本机实测该组件已装且 `llc` 能把 `.ll` 编成宿主 `.o`）。两者均无 sudo。

约束：仓库钉 stable（`rust-toolchain.toml` channel 1.100），LL-020 禁源码级
nightly-only；`test_ts.sh` 是平台无关单一真相源，5 个 node matrix cell 都跑它；
生产 `build:wasm` 产物不得被覆盖率钩子污染。

## Goals / Non-Goals

**Goals:**

- 在 stable + vitest node 驱动下采集 core browser-gated rust 行覆盖率，独立地板 100。
- 生产 wasm 产物零污染；与 native 链同处 `test_ts.sh` 一条进程内（环境变量不跨进程）。

**Non-Goals:**

- 浏览器 Worker 侧 rust 覆盖率（另立 spike）。
- 不引入 nightly 工具链或源码 nightly feature。

## Decisions

### D1：`RUSTC_BOOTSTRAP=1` 解锁 `-Zno-profiler-runtime`，而非装 nightly

wasm32 sysroot 不带 `profiler_builtins`（实测），`-Cinstrument-coverage` 硬链它报
E0463；`-Zno-profiler-runtime`（runtime 由 minicov 提供）跳过链接，但该 flag
nightly-only。用 `RUSTC_BOOTSTRAP=1` 在钉死 stable 上解锁——二进制仍是 stable，
不装 nightly、不进日常路径。备选：装 nightly 工具链（违钉版策略，否）；放弃
wasm rust 覆盖（丢度量，否）。LL-020 禁的是源码 `#[coverage(off)]` 属性，本处
解锁编译 flag、不写 nightly feature，经裁决认定不同性质。

### D2：dump 钩子放 vitest `setupFiles` 的 worker 内 `afterAll`

minicov 计数器每 wasm 实例私有、存于该 worker 线程内存，且 minicov 无 atexit
（不同于 native 的 libc atexit 自动倒），必须显式调 `__cov_dump()`。globalSetup
teardown 跑主进程，读不到 worker wasm 内存。故 dump + `fs.writeFileSync` 放
setupFiles 注册的 `afterAll`（worker 上下文）。备选：globalSetup（读不到内存，
技术不成立）；写进各测试文件（污染测试代码，否）。

### D3：独立 target dir + `#[cfg(feature = "coverage")]` 门控 dump

插桩 wasm 走独立 target dir（如 `target-wasm-cov`），绝不覆盖生产
`CARGO_TARGET_DIR=../target-wasm` 产物。`__cov_dump`/`__cov_ptr`/`__cov_len`
用 `coverage` feature 门控，生产构建不含这些导出。与 native 链 `--no-cfg-coverage`
思路一致（覆盖率专用代码不进发布物）。

### D4：手动 llvm 链，不用 cargo-llvm-cov 包 wasm

cargo-llvm-cov 不处理 wasm 符号问题（实证：其 README 仅指向 wasm-bindgen guide，
object_files 收集器不认 `.wasm`、不编 `.ll`）。故手动三步：先
`llvm-profdata merge -sparse` 合并 profraw，再用 `llc --march=<宿主架构>` 把
`.ll`（由 `--emit=llvm-ir` 产出）编成宿主 `.o`，最后 `llvm-cov report --codecov`。
spike 已跑通此链（真 core `.ll`→5.5MB 宿主 `.o`）。备选：cargo-llvm-cov
show-env/report 包一层（核心步骤仍须手动喂 `.o`，无收益，否）。

### D5：编译期用 wasi-sdk clang、阅卷期用 llvm-tools 组件（工具分离）

编译期：minicov `build.rs` 第 6 行硬编码 `cfg.compiler("clang")`，以 freestanding
（`-nostdlibinc`）编 10 个 wasm32 C 文件。gcc 无 wasm32 后端（实测报
`failed to find tool "clang"`），故必须一个能编 wasm32 的 clang。用 **wasi-sdk**
自带的标准 clang：`scripts/install_clang.sh` 下 192MB tarball 解压到
`~/.local/opt/wasi-sdk`（仿 install_binaryen.sh，零 sudo），`test_ts.sh` 插桩构建段
设 `CC=<wasi-sdk>/bin/clang`。wasi-sdk 作直装工具纳入 check:outdated section 3
（同 binaryen/wasm-pack）。

阅卷期：`llc`/`llvm-profdata`/`llvm-cov` 是 rustup `llvm-tools` 组件自带的二进制，
装在 `$(rustc --print sysroot)/lib/rustlib/<host>/bin/`（用户目录，零 sudo）。把
`llvm-tools` 写进 `rust-toolchain.toml` 的 `components`，rustup 激活钉版工具链时
自动装（同 rustfmt/clippy），无需额外安装步。llvm-tools 与插桩用的 rustc 同属
同一份 LLVM，profraw/IR 格式不可能错配；它随 `rust-toolchain.toml` 钉版走，
**不进 check:outdated**。

实测排除的备选：apt clang（需 sudo、人工升级破坏升级机制，否）；zig cc
（零下载但 zig 给 wasm32 对象打非标准 ELF machine 0xb7≠EM_WASM 247，rust-lld
无视其对象致符号未定义，否）；LLVM 官方 tarball（近 2GB 太重，否）。

### D6：profraw 带 module_signature 命名 + merge

threads 池多 worker 各产一份 profraw，用 `minicov::module_signature()`（或 pid）
命名防覆盖，`llvm-profdata merge -sparse *.profraw` 合并。spike 已验单份 merge；
多份是 llvm-profdata 标准用法。

## Risks / Trade-offs

- [wasm-bindgen 胶水 + minicov dump 共存] → 已验（2026-11-20）：真 `typescript/wasm` 以 wasi-sdk clang 编插桩 wasm、node 加载调 dump 倒出 187KB profraw。
- [core browser-gated 代码能否达 100% 未知] → 地板 100，未达行先列「真不可达」清单人工确认才可豁免，否则补单测（裁决 `地板100先列清单`）。
- [llvm-tools 组件未装致 `llc`/`llvm-cov` 缺失] → 写进 `rust-toolchain.toml` 的 `components`，rustup 激活工具链时自动装；本地/CI 一致。
- [wasi-sdk clang 未装致插桩构建失败] → `test_ts.sh` 探测 wasi-sdk clang，缺失时提示跑 `scripts/install_clang.sh` 并以非零退出；CI node job 加安装步。
- [wasm `.ll` 带 `target triple = "wasm32"`，`llc` 默认想编 wasm 对象] → 加 `--march=<宿主架构>` 强制出宿主 `.o`（spike 已验）。
- [wasi-sdk clang major 与 rustc LLVM major 错配] → wasi-sdk 34=clang 23.1、钉版 rustc=LLVM 23，同 major；且 clang 仅编 minicov freestanding C runtime，不碰 IR/profraw 格式（那由 rustc/llvm-tools 同份 LLVM 负责），错配面极窄。
- [RUSTC_BOOTSTRAP 被误用于日常构建] → 仅在 `test_ts.sh` 覆盖率段局部 export，作用域限该脚本进程；生产 build:wasm 不设。

## Migration Plan

纯新增覆盖率链，无数据/接口迁移。回滚：移除 `test_ts.sh` 的 wasm 覆盖率段、
`rust-toolchain.toml` 的 `llvm-tools` component、`scripts/install_clang.sh` 与
ci.yml 的 clang 安装步即恢复原状；`typescript/wasm` 的 `coverage` feature
默认关，不影响生产构建。
