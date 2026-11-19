# Proposal

## Why

typescript 侧的测试命令目前全部内联手抄在 `ci.yml` 的 node job 与 wasm job 里，
本地没有单命令复现 CI 测试面的入口，tasks.md 只能手抄 CI 参数——抄漏 `--coverage`
就看不见分支缺口（CI run 43141529804 的 8 个失败 job 即此根因，本地已复现）。
rust 半（`test:rs` → `scripts/run/test_rs.sh`）与 python 半（`test:py` →
`scripts/run/test_py.sh`）已按「命令细节唯一真相源 = 脚本文件」落地，typescript 半
仍缺同构入口，是 CI 命令全景里最后一处口径裂缝。

## What Changes

- 根 `package.json` 新增 `test:ts` 入口，薄调用新建 `scripts/run/test_ts.sh`，
  承载 node job 的单端测试面（build:wasm → native 覆盖率链 → typecheck →
  dts 防 `any` → test:wasm），本地与 CI 调同一脚本文件。
- `scripts/run/test_ts.sh` 开头做工具链存在性探测（cargo-llvm-cov、wasm-pack、
  wasm-opt、wasm32-unknown-unknown 目标），缺则打印对应安装命令并非零退出，
  不自动安装；前后各一组 profraw 清扫 + `cargo llvm-cov clean --workspace`，
  顺序与 test_rs/test_py 同构。
- `typescript/package.json` 的 `test:native`、`test:wasm`、`test:browser` 三条
  脚本各自烤入 `--coverage`，使单独执行也必带覆盖率，从根上消灭裸跑假绿。
- `ci.yml`：node job 的测试步骤收敛为 `bash scripts/run/test_ts.sh`（工具链安装
  步骤、coverage artifact 上传、cross 比对步骤留内联）；wasm job 删除两处冗余
  `--coverage` flag（覆盖率已下沉至 typescript 级脚本）。
- 新建 `typescript/scripts/check_dts_any.mjs`，把 node job 内联的 dts 防 `any`
  grep 搬入，由 `test:ts` 在 build 后调用。
- `scripts/check_ci.py` 从 typescript 级旧口径升级为根级口径：根 `package.json`
  每条 `test:*` 的调用形态映射为 `scripts/run/test_<name>.sh` 出现在 ci.yml，
  typescript 级旧规则退役（node job 改调根脚本后旧规则会误报），并在
  `scripts/tests/` 补该闸门的治理单测。

## Capabilities

### New Capabilities

（无新增能力；本改动落在既有 ci-matrix 能力下。）

### Modified Capabilities

- `ci-matrix`: 新增「typescript 测试根聚合入口」要求（`test:ts` → `test_ts.sh`
  本地与 CI 同脚本、工具链探测、前后对称清理、`--coverage` 下沉至 typescript 级
  脚本）；`check_ci.py` 接线闸门口径从 typescript 级升到根级。

## Impact

- 代码/配置：`package.json`、`typescript/package.json`、`scripts/run/test_ts.sh`
  （新建）、`typescript/scripts/check_dts_any.mjs`（新建）、`scripts/check_ci.py`、
  `.github/workflows/ci.yml`。
- 测试：`scripts/tests/` 新增 `check_ci.py` 治理单测。
- 文档（LL-034 波及同步）：`CONTRIBUTING.md`、`scripts/README.md`、
  `typescript/README.md`、`oracle/README.md`、`openspec/specs/ci-matrix/spec.md`、
  `Plan/测试规划.md`、`Plan/闸门重排-2026-11-12.md`、`Plan/覆盖率统一-2026-11-12.md`。
- 不改动产品代码、公开 API、数据布局；功能只增不减。

## Non-goals

- 不建根 `pnpm test` 总聚合入口（延后，归闸门重排档 T1 余量）。
- 不改 `check:cross` 命名、不接线 cross 前置（决策二，另立 change）。
- 不动 `openspec/config.yaml` 的 tasks/apply 规则（T5，延后）。
- 不拆 wasm job 为独立脚本（wasm job 只删冗余 `--coverage` flag，保持薄调用）。
- 不动 bench（决策五已定：基线持久化未落地，本轮不管）。

## Prior art

- 仓库内同构先例：`scripts/run/test_rs.sh`、`scripts/run/test_py.sh`（薄调用 +
  工具链探测 + 前后对称清理 + `set -euo pipefail`），本 change 的 `test_ts.sh`
  直接复用其结构。
- 仓库内接线闸门先例：`scripts/check_ci.py`（typescript 级旧规则），本 change
  升级为根级口径。
- 立项根因与决策记录：`Plan/闸门重排-2026-11-12.md`（T1/T2/T3/T4/T6 与决策三/四/六/七）。

## 专家增补

- 顶尖工程师会在此改动补 `scripts/tests/` 下 `check_ci.py` 新口径的治理单测，
  把「从 ci.yml 删一条 `test:*` 调用 → `pnpm check:meta` 红」从人工验证变成常驻
  测试（参照 `scripts/tests/` 既有 check 脚本单测先例），防 T4 口径退化无人守。
- 顶尖工程师会把 `--coverage` 下沉到 `typescript/package.json` 而非只写进
  `test_ts.sh`，使任何调用方（本地裸跑、tasks.md、CI）默认同口径，杜绝 #182 类
  手抄漂移复发（`vitest.native.config.ts`/`vitest.wasm.config.ts` 的
  `thresholds` 仍为覆盖率阅卷真相源）。

## 已定裁决

- `test:ts`：根入口命名 `test:ts`（与 `check:ts` 同族、按语言划分），承载脚本
  `scripts/run/test_ts.sh`。
- `test_ts.sh 范围`：node job 单端测试面 = build:wasm → native 覆盖率链 →
  typecheck → dts 防 `any` → test:wasm；不含 browser、不含 cross。
- `工具链探测`：脚本开头探测 cargo-llvm-cov、wasm-pack、wasm-opt、
  wasm32-unknown-unknown 目标，缺则打印安装命令并非零退出，不自动安装。
- `前后对称清理`：pre 端 drain 先于 `cargo llvm-cov clean --workspace`，post 端
  drain 在 report/gate 之后再 `clean --workspace`，顺序不变式与 test_rs/test_py 一致。
- `coverage 下沉`：`--coverage` 烤入 `typescript/package.json` 的 `test:native`、
  `test:wasm`、`test:browser`，`test_ts.sh` 内不再出现 `--coverage` 字样。
- `native 池参数留脚本`：`--pool=threads --execArgv="" --no-file-parallelism`
  属插桩链专属，留在 `test_ts.sh` 调用处，不烤入 typescript 级脚本。
- `typecheck 无条件跑`：typecheck 进 `test_ts.sh`，放弃 ci.yml 的
  `if: matrix.node-version == '26'` 特判，5 格各跑一遍换本地/CI 同口径。
- `dts 检查形态`：dts 防 `any` 搬入 `typescript/scripts/check_dts_any.mjs`，
  由 `test:ts` 在 build 后调用（维持闸门重排档 T3 已定裁决）。
- `不探测 node_modules`：`test_ts.sh` 假定 `pnpm install` 已跑，缺依赖由 pnpm/vitest
  自报错，脚本不探测、不代跑安装。
- `check_ci 根级口径`：`scripts/check_ci.py` 换根级接线闸门（根 `test:*` 映射
  `scripts/run/test_<name>.sh` 须出现在 ci.yml），typescript 级旧规则退役，
  `scripts/tests/` 补治理单测。
- `wasm job 只删 flag`：wasm job 仅删两处冗余 `--coverage`，不拆独立脚本。
- `延后项`：根 `pnpm test` 总聚合、T5 config.yaml 规则、`check:cross` 改名/接线
  均延后，记回 `Plan/闸门重排-2026-11-12.md`。
- `归档体检一次性跳过`：本 change 归档流程中的 archive 态只读体检跳过
  （仅本次一次性，config.yaml archive guidance 与 health-check spec 规则本体
  不变；人工裁决 2026-11-18）。
- `native report 排除 python`：`test_ts.sh` 的 native 覆盖率 report 的
  `--ignore-filename-regex` 同时排除 `core` 与 `python` 路径——`cargo llvm-cov report`
  扫描 `target/` 下所有对象的 covmap section，本地共享 `target/` 若被上一轮
  `maturin develop` 插桩会把 `python/src/lib.rs` 以 0% 纳入 native 报告；CI node job
  全新 checkout 不产 python 对象，该排除在 CI 端为 no-op，仅修本地污染并使脚本对
  步骤顺序鲁棒（native 报告语义 = native 胶水，python 行归 `coverage-python.json`）。
