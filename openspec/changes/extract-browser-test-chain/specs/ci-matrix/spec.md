# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: 全项目 wasm 测试根聚合入口`
- TO: `### Requirement: 全项目浏览器测试根聚合入口`

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
  （`rustup component add llvm-tools` / `scripts/install_wasi_sdk.sh` /
  `scripts/install_wasm_bindgen_cli.sh`），不发起自动安装

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

### Requirement: typescript 测试根聚合入口

根 `package.json` MUST 提供 `test:ts` 入口，薄调用 `scripts/run/test_ts.sh`，
使本地单命令复现 CI node job 的单端测试面（browser 产物构建、native 覆盖率链、
typecheck、dts 防 `any`、node 驱动浏览器单元套件），且 MUST `set -euo pipefail`。
本地跑绿 MUST 等价于 CI node job 同口径通过；CI MUST NOT 为 node job 保留独立的
profraw drain 步骤（清扫已内置于脚本）。

容差：存在性与退出码闸门，无数值阈值；native 胶水覆盖率地板数值沿用铁律七与
`coverage_gate.py` 现有定义，本条不新增数值。

#### Scenario: typescript 入口本地全链绿

- **WHEN** 开发者在仓库根运行 `pnpm test:ts` 且工具齐备
- **THEN** 脚本依次执行工具链探测、profraw 前置清扫、
  `cargo llvm-cov clean --workspace`、browser 产物构建（命令
  `pnpm -C browser build:browser`）、native 覆盖率链（show-env、
  `NODE_OPTIONS=--expose-gc`、build:native:debug、test:native、report 带 host
  triple、`coverage_gate.py` 地板阅卷，且 show-env/clean/build/test/report 共享
  脚本单进程）、typecheck、dts 防 `any` 检查、node 驱动浏览器单元套件（命令
  `pnpm -C browser test:unit`，纯 TS v8，不产 wasm lcov）、再次
  `clean --workspace`，native 报告产出并经地板阅卷，脚本 exit 0

#### Scenario: typescript 入口缺工具报错可行动

- **WHEN** 本地缺 `cargo-llvm-cov`、`wasm-pack`、`wasm-opt` 或
  `wasm32-unknown-unknown` 目标之一时运行 `pnpm test:ts`
- **THEN** 脚本在任何 build/测试执行前以非零码退出，stderr 打印对应安装命令
  （`scripts/install_cargo_llvm_cov.sh` / `scripts/install_wasm_pack.sh` /
  `scripts/install_binaryen.sh` / `rustup target add wasm32-unknown-unknown`），
  不发起网络安装

#### Scenario: typescript 入口不含 wasm 覆盖率工具探测

- **WHEN** 检查 `scripts/run/test_ts.sh`
- **THEN** 不含 llvm-tools 三件套（`llc`/`llvm-profdata`/`llvm-cov`）、wasi-sdk
  clang、`wasm-bindgen` 的探测——插桩 wasm 只由 `browser/scripts/test.sh`
  （浏览器 job）编译，node 入口不编插桩 wasm

#### Scenario: typescript 入口注入残留即红

- **WHEN** 仓库根存在人为放置的 `stray.profraw` 时运行 `pnpm test:ts`
- **THEN** 脚本以非零码失败并列出该文件名，且该文件已从磁盘删除

### Requirement: 根 test 总聚合入口

根 `package.json` MUST 提供 `test` 入口，按 `test:rs` → `test:py` → `test:ts` →
`test:browser` → `test:cross` 顺序串联五个单端入口，使开发者一条命令跑全量本地
测试。该入口 MUST 为本地专用，CI MUST NOT 新增 `pnpm test` 步骤（CI 各 `test_*.sh`
分布在不同 job 无法同场聚合，逐 job 调用保持不变）。

容差：存在性与退出码闸门，无数值阈值；各单端入口的阈值沿用各自 Requirement
与 `coverage_gate.py` 现有定义，本条不新增数值。

#### Scenario: 一条命令跑全量

- **WHEN** 开发者在仓库根运行 `pnpm test` 且工具与产物齐备
- **THEN** 依次执行 `test:rs`、`test:py`、`test:ts`、`test:browser`、`test:cross`，
  任一失败即非零退出，全通过则 exit 0

#### Scenario: CI 不聚合 pnpm test

- **WHEN** 查看 ci.yml 任一 job 的步骤序列
- **THEN** 不出现 `pnpm test` 调用，各 `test_*.sh` 仍按 job 分别调用
