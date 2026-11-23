# ci-matrix Delta

## Modified Requirements

### Requirement: typescript 覆盖率 flag 下沉至包级脚本

`typescript/package.json` 的 `test:native` 与 `browser/package.json` 的
`test:unit`、`test:e2e` 三条脚本 MUST 各自内置 `--coverage`，使任一调用方
（本地裸跑、tasks.md、CI、根聚合入口）单独执行时默认带覆盖率采集；`ci.yml`
与 `scripts/run/test_ts.sh` MUST NOT 再对这三条脚本追加 `--coverage` flag
（重复追加即口径冗余）。覆盖率阈值数值仍由 `vitest.*.config.ts` 的 `thresholds`
唯一定义，本条不新增数值。native 插桩链专属
的池参数（`--pool=threads`、`--execArgv=""`、`--no-file-parallelism`）MUST 留在
`test_ts.sh` 调用处，MUST NOT 烤入包级脚本（裸跑无 llvm-cov 环境时烤入会使
`gc()` 缺失而失败）。

容差：脚本字符串存在性闸门，无数值阈值；阈值数值以 vitest 配置为唯一定义处。

#### Scenario: 单独执行也带覆盖率

- **WHEN** 开发者直接运行 `pnpm -C browser test:unit`（不带任何 flag）
- **THEN** vitest 以覆盖率模式执行并按对应 vitest 配置阈值阅卷，
  分支缺口即非零退出——裸跑假绿不可复现

#### Scenario: ci.yml 不再手抄 coverage flag

- **WHEN** 检查 `ci.yml` 的 node job 与 browser job 测试步骤
- **THEN** 无 `test:native --coverage` / `test:unit --coverage` /
  `test:e2e --coverage` 之类内联 `--coverage` 追加——覆盖率开关只在
  各包 `package.json`（typescript 的 test:native、browser 的 test:unit/test:e2e）
  定义一处

### Requirement: 全项目 wasm 测试根聚合入口

根 `package.json` MUST 提供 `test:browser` 入口（原 `test:wasm`，随浏览器端
独立成包更名），薄调用浏览器端测试脚本，使本地单命令复现全项目浏览器端测试面
（browser 产物构建、node 驱动单元套件、真浏览器 e2e 套件、browser rust 覆盖率
链），且 MUST `set -euo pipefail` 并纳入 `pnpm test` 聚合链。脚本对工具与浏览器
MUST 只探测存在性、缺失即非零退出并打印安装命令，MUST NOT 发起网络安装。
`ci.yml` 的 browser job（原 wasm job）测试步骤 MUST 缩成一行调该脚本，前置安装
步保留。

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
- **THEN** 测试步骤为单行调用浏览器端测试脚本，无内联的产物构建 /
  `test:unit` / `test:e2e` 命令；前置工具安装步仍在调脚本之前

#### Scenario: 根 test:wasm 纳入本地聚合

- **WHEN** 检查根 `package.json` 的 `test` 聚合脚本
- **THEN** 聚合链含 `pnpm test:browser`，本地 `pnpm test` 覆盖到真浏览器套件

#### Scenario: node 版本轴 wasm 验证保留

- **WHEN** 检查 `scripts/run/test_ts.sh`
- **THEN** 仍含 browser 产物构建与 node 驱动单元套件，node 矩阵继续验浏览器
  产物跨 node 版本可加载；browser 产物构建在浏览器脚本与 `test_ts.sh` 各自
  幂等执行、互不依赖（无跨 job `needs` 依赖）
