# ci-matrix Delta Spec

## ADDED Requirements

### Requirement: typescript 测试根聚合入口

根 `package.json` MUST 提供 `test:ts` 入口，薄调用 `scripts/run/test_ts.sh`，
使本地单命令复现 CI node job 的单端测试面（build:wasm、native 覆盖率链、typecheck、
dts 防 `any`、test:wasm），且 MUST `set -euo pipefail`。本地跑绿 MUST 等价于
CI node job 同口径通过；CI MUST NOT 为 node job 保留独立的 profraw drain 步骤
（清扫已内置于脚本）。

容差：存在性与退出码闸门，无数值阈值；native 胶水覆盖率地板数值沿用铁律七与
`coverage_gate.py` 现有定义，本条不新增数值。

#### Scenario: typescript 入口本地全链绿

- **WHEN** 开发者在仓库根运行 `pnpm test:ts` 且工具齐备
- **THEN** 脚本依次执行工具链探测、profraw 前置清扫、
  `cargo llvm-cov clean --workspace`、build:wasm、native 覆盖率链（show-env、
  `NODE_OPTIONS=--expose-gc`、build:native:debug、test:native、report 带 host
  triple、`coverage_gate.py` 地板阅卷，且 show-env/clean/build/test/report 共享
  脚本单进程）、typecheck、dts 防 `any` 检查、test:wasm、profraw 后置清扫、再次
  `clean --workspace`，native 报告产出并经地板阅卷，脚本 exit 0

#### Scenario: typescript 入口缺工具报错可行动

- **WHEN** 本地缺 `cargo-llvm-cov`、`wasm-pack`、`wasm-opt` 或
  `wasm32-unknown-unknown` 目标之一时运行 `pnpm test:ts`
- **THEN** 脚本在任何 build/测试执行前以非零码退出，stderr 打印对应安装命令
  （`scripts/install_cargo_llvm_cov.sh` / `scripts/install_wasm_pack.sh` /
  `scripts/install_binaryen.sh` / `rustup target add wasm32-unknown-unknown`），
  不发起网络安装

#### Scenario: typescript 入口注入残留即红

- **WHEN** 仓库根存在人为放置的 `stray.profraw` 时运行 `pnpm test:ts`
- **THEN** 脚本以非零码失败并列出该文件名，且该文件已从磁盘删除

### Requirement: typescript 覆盖率 flag 下沉至包级脚本

`typescript/package.json` 的 `test:native`、`test:wasm`、`test:browser` 三条脚本
MUST 各自内置 `--coverage`，使任一调用方（本地裸跑、tasks.md、CI、根聚合入口）
单独执行时默认带覆盖率采集；`ci.yml` 与 `scripts/run/test_ts.sh` MUST NOT 再
对这三条脚本追加 `--coverage` flag（重复追加即口径冗余）。覆盖率阈值数值仍由
`vitest.*.config.ts` 的 `thresholds` 唯一定义，本条不新增数值。native 插桩链专属
的池参数（`--pool=threads`、`--execArgv=""`、`--no-file-parallelism`）MUST 留在
`test_ts.sh` 调用处，MUST NOT 烤入包级脚本（裸跑无 llvm-cov 环境时烤入会使
`gc()` 缺失而失败）。

容差：脚本字符串存在性闸门，无数值阈值；阈值数值以 vitest 配置为唯一定义处。

#### Scenario: 单独执行也带覆盖率

- **WHEN** 开发者直接运行 `pnpm -C typescript test:wasm`（不带任何 flag）
- **THEN** vitest 以覆盖率模式执行并按 `vitest.wasm.config.ts` 阈值阅卷，
  分支缺口即非零退出——裸跑假绿不可复现

#### Scenario: ci.yml 不再手抄 coverage flag

- **WHEN** 检查 `ci.yml` 的 node job 与 wasm job 测试步骤
- **THEN** 无 `test:native --coverage` / `test:wasm --coverage` /
  `test:browser --coverage` 之类内联 `--coverage` 追加——覆盖率开关只在
  `typescript/package.json` 定义一处

### Requirement: CI 接线闸门根级口径

`scripts/check_ci.py` MUST 以根 `package.json` 为真相源：每条 `test:*` 脚本
（含 `test:rs:cov` 这类多段名）的调用形态 MUST 映射为对应的
`scripts/run/test_<name>.sh` 出现在 `ci.yml`，缺失即非零退出并指名缺失项；
原 typescript 级旧规则（要求 `typescript test:<name>` 字面出现在 ci.yml）MUST
退役（node job 改调根脚本后旧规则会误报）。该闸门的回归 MUST 由 `scripts/tests/`
下的治理单测兜底，经 `pnpm check:meta` 在 lint job 执行。

容差：存在性与退出码闸门，无数值阈值。

#### Scenario: 删一条调用即红

- **WHEN** 从 `ci.yml` 删除某条 `scripts/run/test_*.sh` 调用后运行
  `pnpm check:meta`
- **THEN** `check_ci.py` 以非零码退出并指名该 `test:*` 未被 CI 调用——
  CI 不跑的测试不算闸门（LL-037）

#### Scenario: 旧 typescript 级规则退役不误报

- **WHEN** node job 改调 `scripts/run/test_ts.sh` 后 ci.yml 不再出现
  `typescript test:native` 字面
- **THEN** `check_ci.py` 不再因该字面缺失而报错——typescript 级旧规则已退役，
  改由根级映射判定
