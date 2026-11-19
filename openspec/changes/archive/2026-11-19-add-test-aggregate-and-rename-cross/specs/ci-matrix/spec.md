# ci-matrix Delta Spec

## ADDED Requirements

### Requirement: cross-binding 测试根聚合入口

根 `package.json` MUST 提供 `test:cross` 入口，薄调用 `scripts/run/test_cross.sh`，
使本地单命令复现 CI node job 的跨绑定对拍面，且 MUST `set -euo pipefail`。
该脚本 MUST 承载原 ci.yml node job 内联的全部前置，CI MUST NOT 再保留这段内联前置
（缩成一行 `bash scripts/run/test_cross.sh`）。本地跑绿 MUST 等价于 CI node job
同口径通过。脚本 MUST 在 dump 前探测四端产物存在性，缺则行动化报错而非自行构建。

容差：存在性与退出码闸门，无数值阈值；四端数值容差沿用 `oracle/manifest.json`
现有定义，本条不新增数值。

#### Scenario: cross 入口本地全链绿

- **WHEN** 开发者在仓库根运行 `pnpm test:cross` 且四端产物齐备
- **THEN** 脚本依次执行 `uv sync`、`maturin develop`、`stub_gen`、四端 dump、
  `compare_cross.py` 阅卷、词汇类型与动词集合闸门，全部通过则 exit 0

#### Scenario: cross 入口缺产物报错可行动

- **WHEN** napi 原生产物或 wasm 产物缺失时运行 `pnpm test:cross`
- **THEN** 脚本在 dump 执行前以非零码退出，stderr 打印 `pnpm test:ts`，
  不发起构建或网络安装

#### Scenario: 本地与 CI 同脚本

- **WHEN** 对比本地 `pnpm test:cross` 与 ci.yml node job 的 cross 步骤
- **THEN** 两端都只调用 `scripts/run/test_cross.sh`，uv sync/maturin/stub_gen/
  LD_LIBRARY_PATH/dump/阅卷的参数只在该脚本内定义一处

### Requirement: 根 test 总聚合入口

根 `package.json` MUST 提供 `test` 入口，按 `test:rs` → `test:py` → `test:ts` →
`test:cross` 顺序串联四个单端入口，使开发者一条命令跑全量本地测试。该入口 MUST
为本地专用，CI MUST NOT 新增 `pnpm test` 步骤（CI 各 `test_*.sh` 分布在不同 job
无法同场聚合，逐 job 调用保持不变）。

容差：存在性与退出码闸门，无数值阈值；各单端入口的阈值沿用各自 Requirement
与 `coverage_gate.py` 现有定义，本条不新增数值。

#### Scenario: 一条命令跑全量

- **WHEN** 开发者在仓库根运行 `pnpm test` 且工具与产物齐备
- **THEN** 依次执行 `test:rs`、`test:py`、`test:ts`、`test:cross`，任一失败即
  非零退出，全通过则 exit 0

#### Scenario: CI 不聚合 pnpm test

- **WHEN** 查看 ci.yml 任一 job 的步骤序列
- **THEN** 不出现 `pnpm test` 调用，各 `test_*.sh` 仍按 job 分别调用
