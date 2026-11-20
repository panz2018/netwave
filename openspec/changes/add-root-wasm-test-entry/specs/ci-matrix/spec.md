# Spec Delta

## ADDED Requirements

### Requirement: 全项目 wasm 测试根聚合入口

根 `package.json` MUST 提供 `test:wasm` 入口，薄调用 `scripts/run/test_wasm.sh`，
使本地单命令复现全项目 wasm 测试面（`build:wasm`、node 驱动 wasm 套件、真浏览器
套件），且 MUST `set -euo pipefail` 并纳入 `pnpm test` 聚合链。脚本对工具与浏览器
MUST 只探测存在性、缺失即非零退出并打印安装命令，MUST NOT 发起网络安装。
`ci.yml` 的 wasm job 测试步骤 MUST 缩成一行调该脚本，前置安装步保留。

容差：存在性与退出码闸门，无数值阈值；wasm 壳覆盖率阈值数值以
`typescript/vitest.wasm.config.ts` 的 `thresholds` 为唯一定义处，本条不复制数值。

#### Scenario: wasm 入口本地全链绿

- **WHEN** 开发者在仓库根运行 `pnpm test:wasm` 且工具与 chromium 齐备
- **THEN** 脚本依次执行工具链探测、`build:wasm`、node 驱动 wasm 套件、真浏览器套件，
  两套件均按各自 vitest 配置阈值阅卷通过，脚本 exit 0

#### Scenario: wasm 入口缺工具或缺浏览器报错可行动

- **WHEN** 本地缺 `wasm-pack`、`wasm-opt`、`wasm32-unknown-unknown` 目标或 chromium
  之一时运行 `pnpm test:wasm`
- **THEN** 脚本在任何 build/测试执行前以非零码退出，stderr 打印对应安装命令
  （`scripts/install_wasm_pack.sh`、`scripts/install_binaryen.sh`、
  `rustup target add wasm32-unknown-unknown`、`pnpm -C typescript exec playwright install --only-shell chromium`），不发起网络安装

#### Scenario: ci.yml wasm job 不再内联测试命令

- **WHEN** 检查 `ci.yml` 的 wasm job 测试步骤
- **THEN** 测试步骤为单行 `bash scripts/run/test_wasm.sh`，无内联的 `build:wasm` /
  `test:wasm` / `test:browser` 命令；前置工具安装步仍在调脚本之前

#### Scenario: 根 test:wasm 纳入本地聚合

- **WHEN** 检查根 `package.json` 的 `test` 聚合脚本
- **THEN** 聚合链含 `pnpm test:wasm`，本地 `pnpm test` 覆盖到真浏览器套件

#### Scenario: node 版本轴 wasm 验证保留

- **WHEN** 检查 `scripts/run/test_ts.sh`
- **THEN** 仍含 `build:wasm` 与 node 驱动 wasm 套件，node 矩阵继续验 wasm 产物跨
  node 版本可加载；`build:wasm` 在 `test_wasm.sh` 与 `test_ts.sh` 各自幂等执行、互不依赖
