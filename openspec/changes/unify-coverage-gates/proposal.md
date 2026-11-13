# Proposal

## Why

CI 当前在 linux-x64 格把 core 测试跑两遍（`cargo test --workspace` +
`cargo llvm-cov -p netwave` 各执行一次同一批测试），冗余真实存在；覆盖率
只量 core 且只在 linux-x64 一格出数，python/native 的 rust 胶水行
（`resolve_freq_unit` 类 match 臂、drop 守卫、unsafe 零拷贝块）从未被任何
工具度量过。cargo-llvm-cov 官方对四平台均有预编译产物、并提供 `exec` 子命令
包住外部测试驱动采集覆盖率，能力已具备，现在把它接进 CI。

## What Changes

- rust job：删除 `cargo test --workspace` 步骤，与覆盖率步骤合并为一条
  （`cargo llvm-cov -p netwave --codecov` +
  `cargo build --workspace --all-targets` 编译看门闸 + `coverage_gate.py`
  阅卷），并删除 `if: matrix.target == 'linux-x64'`，core 覆盖率四平台
  全部产出、各自阅卷。
- python job / node job：测试链外裹 `cargo llvm-cov exec`，pytest / vitest
  照常驱动（测试代码零改动），同步采集 python/native 两 crate 的 rust 胶水行
  覆盖率，报告剔除 core 路径后独立阅卷。
- 覆盖率报告统一命名并落 `coverage/` 目录（`coverage/coverage-core.json`、
  `coverage/coverage-python.json`、`coverage/coverage-native.json`，目录已被
  现成 `.gitignore` 覆盖），CI 以 upload-artifact 留存供核对。
- 地板分两阶段：首轮四平台 core 与双胶水统一地板 0（只打印数字与缺行
  清单不判红；core 虽 linux-x64 已标定，但四格共用一条阅卷命令且其余三格
  为新域），四平台 core 与胶水数字人工核对、结构性不可达行逐条豁免后，
  同一 change 内三域地板统一翻至 100。
- **BREAKING**（口径变更，非 API 变更）：ci-matrix spec 铁律七"绑定 crate
  不进 llvm-cov job 属工具作用域分离"条款废止，改为"绑定 crate 的 rust 行
  由其语言 job 内 `cargo llvm-cov exec` 采集，core 与胶水各自独立地板"；
  "五格构建矩阵"中"每格 MUST 执行 `cargo test`"改为新命令口径。
- 登记 LL（口径漂移假绿类 + 本轮决策）并同步波及文档（LL-034）。

## Capabilities

### New Capabilities

- 无（全部落在既有 ci-matrix 能力范围内）。

### Modified Capabilities

- `ci-matrix`：铁律七覆盖率门槛——命令字面（合并命令、四平台、胶水扩面、
  报告命名与 `coverage/` 落盘、upload-artifact）、"工具作用域分离"条款
  废止换"各语言 job 内 exec 采集 + 独立地板"、"先标定后启用"两阶段条款；
  五格构建矩阵"每格 MUST 执行 `cargo test`"改为"llvm-cov 执行测试 +
  workspace 编译看门闸"（含"源码无 doctest"前提声明）。

## Impact

- `.github/workflows/ci.yml`：rust / python / node 三个 job 的测试步骤重写；
  wasm / lint / bench job 零改动。
- `openspec/specs/ci-matrix/spec.md`：两处 Requirement 措辞修订（S6 收口）。
- `scripts/coverage_gate.py`：零代码改动（现收"文件路径 + 地板"两参数，
  多报告 = 多次调用）；`scripts/tests/` 补多报告调用口径的单测。
- `openspec/specs/lessons-learned/`：新增 LL 条目 + INDEX 同步。
- 波及文档（LL-034）：`Plan/覆盖率统一-2026-11-12.md`、
  `Plan/闸门重排-2026-11-12.md`（T1/T2/T4 标延后、T1/T2 构成更新）、
  CONTRIBUTING.md、scripts/README.md、`Plan/测试规划.md`。
- 不新增根 package.json 脚本（聚合入口 `test:*` 延后至闸门重排档点名，
  本次 CI 内联命令；spec 铁律七钉的命令字面与内联一致，无接线冲突）。

## Non-goals

- wasm 端 rust 胶水覆盖率（插桩计数倒出未验证，spike 另立项，本 change
  不碰 wasm job）。
- 根 package.json 聚合入口 `test:*` 与 ci.yml 改调根脚本、`check_ci.py`
  根级接线闸门升级（闸门重排档 T1/T2/T4，人工定夺延后）。
- `coverage_gate.py` 代码改造（多报告由多次调用承担）。
- bench 基线持久化（闸门重排档决策五，本轮不管）。

## Prior art

- cargo-llvm-cov「Get coverage of external tests」（show-env / exec 流程）：
  <https://github.com/taiki-e/cargo-llvm-cov>（README Platform Support 节确认
  四平台预编译产物与 `x86_64-pc-windows-msvc` 支持）。
- 仓库内现成件：`scripts/install_cargo_llvm_cov.sh`（官方预编译直装）、
  `scripts/coverage_gate.py`（codecov.json OR 语义阅卷）、
  `python/Cargo.toml` 的 `cfg(coverage)` 适配。
- 偏离说明：官方 WASM 覆盖率方案基于 wasm-bindgen-test，本仓库 wasm 为
  vitest 驱动，倒出机制未验证——故 wasm 排除出本 change（见 Non-goals）。

## 专家增补

- `scripts/tests/` 补 `coverage_gate.py` 多报告调用口径单测：闸门脚本自身
  回归目前无测试兜底（`check:py` 地板仅覆盖 `scripts/versions` 域）。
- node 端 vitest 多进程各写 profraw，`LLVM_PROFILE_FILE` 须含 `%p` 防互相
  覆盖——apply 首步本地 spike 验证 `cargo llvm-cov exec` 默认值是否已带。
- napi build 对 show-env 注入的 `RUSTFLAGS` 透传属未验证事实，apply 首步
  本地 spike 一并确认，不通则改用 napi 配置的 cargo 参数注入。
- spec 修订附"源码无 doctest"前提（grep `core/src`、`python/src`、
  `typescript/*/src` 无代码围栏实证）：`cargo test` 退役后 doctest 无人执行，
  该前提写入 spec 防将来新增 doctest 示例静默漏测。

## 受影响铁律

- 铁律七（覆盖率门槛生效，ci-matrix spec）：命令字面、工具作用域分离条款、
  地板启用方式——本 change 内修订。
- 铁律六（性能阈值）：不受影响（bench job 零改动）。
- LL-034（波及面同步）/ LL-057（codecov OR 语义防假红）：沿用现行机制。
