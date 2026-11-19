# Design

## Context

rust 半（`scripts/run/test_rs.sh`）与 python 半（`scripts/run/test_py.sh`）已确立
「脚本承载命令细节 + 薄调用 + 工具链探测 + 前后对称清理 + `set -euo pipefail`」的
同构模式。typescript 半的测试命令当前散在 `ci.yml` 的 node job（native 覆盖率链、
typecheck、dts 检查、test:wasm、cross）与 wasm job（build:wasm、test:wasm、
chromium、test:browser）内联。本 change 把 node job 的单端测试面收进
`scripts/run/test_ts.sh`，复用既有模式。动机见 proposal.md - Why。

关键既有约束（来自 ci-matrix spec 铁律七与 LL）：native 胶水覆盖率的
show-env/clean/build/test/report 必须同进程；napi `--platform` 把对象建进
`target/<triple>/`，report 须带 `--target`；`#[napi]` 宏属性行由 `coverage_gate.py`
按模式豁免；vitest 的覆盖率阈值真相源在 `vitest.*.config.ts` 的 `thresholds`。

## Goals / Non-Goals

**Goals:**

- node job 测试面本地单命令（`pnpm test:ts`）复现，与 CI 物理同源。
- 覆盖率开关下沉到 typescript 级脚本，消灭裸跑假绿（#182 类漂移）。
- CI 接线闸门升到根级，锁住「根 `test:*` 必被 CI 调用」。

**Non-Goals:**

- 不改 wasm job 结构（只删冗余 `--coverage` flag）。
- 不动 cross 比对步骤（仍内联 node job，归决策二另立 change）。
- 不建根 `pnpm test` 总聚合、不改 config.yaml 规则（延后项）。

## Decisions

### D1 脚本命名 `test_ts.sh` / 入口 `test:ts`

按语言划分，与 `check:ts` 同族、与 `test:rs`/`test:py` 对齐。备选 `test:node`
被否：该入口含 wasm 测试，`node` 名不符实，且 CI job 名描述运行时矩阵、不必与
脚本名强绑。

### D2 `--coverage` 下沉到 `typescript/package.json` 而非 `test_ts.sh`

把 `--coverage` 写进 `test:native`/`test:wasm`/`test:browser` 脚本体，使任何调用方
默认带覆盖率。备选「只写进 `test_ts.sh`」被否：本地裸跑
`pnpm -C typescript test:wasm` 仍会漏覆盖率，#182 根因（tasks.md 手抄漏 flag）未根治。阈值数值仍在
vitest config，脚本只负责开关采集。逃生门：vitest 支持 `--coverage.enabled=false`
显式关闭，快循环时显式声明，默认态恒为 CI 口径。

### D3 native 池参数留 `test_ts.sh`，不随 `--coverage` 下沉

`--pool=threads --execArgv="" --no-file-parallelism` 是 llvm-cov 插桩链专属：
threads 池主进程退出才 flush profraw、worker 拒绝 `--expose-gc`、串行化防多 worker
共享同一 `.node` 的 Rust static live_count 竞态。这些只在 `test_ts.sh` 的 show-env
环境成立。若烤进包级 `test:native`，裸跑（无 llvm-cov）时 `gc()` 缺失致 memory
测试失败，且快循环白背串行化。故 `test_ts.sh` 调 `test:native` 时追加这三个 flag，
`--coverage` 由包级脚本自带。

### D4 前后对称清理，顺序不变式

pre 块：`clean_stray_profraw.py` → `cargo llvm-cov clean --workspace`（防陈旧插桩
二进制污染）。post 块：`clean_stray_profraw.py` → `cargo llvm-cov clean --workspace`
（drain 顶后置块最前，使「本轮断链」检测不被后置命令推后；drain 须在 report/gate
之后，否则坏链降级为「empty report」）。node 链插桩对象落 host `target/`（napi
不带 `--target` 编到 host target/debug，与 py 链同），故用 `clean --workspace`
而非 rs 链专用的 `rm -rf target/llvm-cov-target`。

### D5 typecheck 进脚本无条件跑

放弃 ci.yml 的 `if: matrix.node-version == '26'`。进脚本后 5 个 matrix 格各跑一遍
tsc（每格十几秒，成本可忽略），换取本地/CI 同口径。备选「脚本读 `NODE_VERSION`
环境变量保留特判」被否：多一层 CI 特判破坏口径统一，本地无该变量自然全跑，
反而不一致。

### D6 dts 防 `any` 搬入 `check_dts_any.mjs`

维持闸门重排档 T3 已定裁决：新建 `typescript/scripts/check_dts_any.mjs`，由
`test_ts.sh` 在 build 后调用。备选「grep 直接写进 sh」被否：.mjs 报错信息更可控、
可扩展检查更多 dts 文件、不依赖 Git Bash 的 grep。检查逻辑不变：`dist/index.browser.d.mts`
与 `dist/index.node.d.mts` 含 `: any` 即非零退出。

### D7 `check_ci.py` 根级映射形态

根 `test:*` 的「被 CI 调用」判定映射为 `scripts/run/test_<name>.sh` 出现在 ci.yml：
`test:rs`→`test_rs.sh`、`test:py`→`test_py.sh`、`test:ts`→`test_ts.sh`。多段名
（如 `test:rs:cov`）取首段对应脚本或按现有 rs 入口处理。typescript 级旧规则
（`typescript test:<name>` 字面匹配）退役。治理单测放 `scripts/tests/`，覆盖
「删一条调用→红」「旧字面缺失不误报」两态，经 `pnpm check:meta` 执行。

## Risks / Trade-offs

- [本地缺 wasm 工具链时 `test:ts` 报错，门槛高于纯 node 测试] → 探测块集中打印
  四条安装命令，报错即行动指南；CI 自带安装步骤不受影响。
- [`--coverage` 下沉后单独跑测试恒付 v8 覆盖率开销] → JS 侧插桩开销温和；
  需快循环时用 `--coverage.enabled=false` 显式关闭，默认态换口径统一值得。
- [typecheck 每格跑，node job 总时长略增] → 十几秒量级，相对 native 编译可忽略。
- [`check_ci.py` 改口径若映射写错，可能漏放行或误报] → D7 的治理单测锁两态，
  回归由 CI 兜底。
- [wasm job 与 node job 都跑 `test:wasm`，看似重复] → 有意分工：wasm job 验 OS
  codegen 矩阵，node job 验 node 版本轴；vitest 秒级，成本可接受，维持现状。

## Migration Plan

纯增量：新增脚本与入口、ci.yml 步骤替换、文档同步。回滚 = revert 本 change 的
commit，ci.yml 恢复内联步骤即可，无数据/接口迁移。

## Open Questions

（无——命名、范围、清理顺序、覆盖率下沉、池参数归属、typecheck 条件、dts 形态、
check_ci 映射均已在 proposal 已定裁决中拍板。）
