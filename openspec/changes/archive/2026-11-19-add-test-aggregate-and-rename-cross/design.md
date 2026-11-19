# Design

## 方案概述

一个 change 收口三件互相依赖的事：根 `pnpm test` 聚合、`check:cross`→`test:cross`
改名、`openspec/config.yaml` 两条规则。核心是把 ci.yml node job 内联的 cross 前置
整体搬进新建的 `scripts/run/test_cross.sh`，使其与 `test_rs/py/ts.sh` 同构，
再由 `check_ci.py` 闸门强制接线。

## 关键决策

### 决策一：`test_cross.sh` 的产物探测而非自构建

`test_cross.sh` 只做 `uv sync` + `maturin develop` + `stub_gen` + 四端 dump + 阅卷，
dump 前探测 napi 原生产物（`typescript/native/*.node`）与 wasm 产物
（`typescript/wasm/*`）是否存在，缺则非零退出并打印 `pnpm test:ts`。
构建逻辑（wasm-pack、napi build）唯一承载在 `test_ts.sh`，不重复。
`pnpm test` 顺序 `rs→py→ts→cross` 保证聚合链跑到 cross 时产物已由 ts 段产出。

理由：与 `test_rs.sh` 缺 `cargo-llvm-cov` 时"探测+打印安装命令"同构；
避免 wasm/napi 构建逻辑两处漂移。

### 决策二：CI 内联前置整体下沉

ci.yml node job 现有内联块（`uv sync --project python`、`maturin develop`、
`LD_LIBRARY_PATH` 导出、`stub_gen`、`pnpm check:cross`）整体搬进 `test_cross.sh`，
CI 步骤缩成 `bash scripts/run/test_cross.sh`。`LD_LIBRARY_PATH`（stub_gen 动态链接
uv 的 libpython）在脚本内用 `uv run python -c "import sysconfig..."` 探测设置。

理由：满足 ci-matrix spec「本地与 CI 同脚本」不变式，参数单点定义。

### 决策三：改名波及面单 change 改全

`check:cross`→`test:cross` 触及约 16 个活文件（含两份 spec 的 requirement 正文，
已在 specs delta 以 MODIFIED 承载）。archive 区冻结不动。`check_ci.py` 的
`test:*`→`test_<seg>.sh` 映射天然覆盖 `test:cross`→`test_cross.sh`，无需改闸门逻辑，
只需补测试断言。

## 波及文件清单

- 配置：`package.json`、`.github/workflows/ci.yml`、`openspec/config.yaml`
- 脚本：新建 `scripts/run/test_cross.sh`、`scripts/tests/test_check_ci.py`
- 改名活文件：`CONTRIBUTING.md`、`oracle/README.md`、`scripts/README.md`、
  `scripts/check_verbs.py`、`scripts/check_vocab_types.py`、`typescript/scripts/dump.mjs`、
  `openspec/specs/dependency-upgrade/spec.md`、`openspec/specs/project-governance/spec.md`、
  `openspec/specs/lessons-learned/{ci,core,python,typescript}.md`、`Plan/测试规划.md`
- 删除：`Plan/闸门重排-2026-11-12.md`

## 风险与回退

- [改名漏改活文件致 `pnpm check:cross` 旧名失效] → 改完全仓 `grep -rn check:cross`
  排除 archive 须为空；`pnpm test:cross` 跑绿自证。
- [test_cross.sh 探测路径与实际产物名不符] → apply 时先 `ls typescript/native`、
  `ls typescript/wasm` 实证产物名再写探测条件。
- [config.yaml 新规则锚点与现有 apply guidance 互斥（LL-089）] → 新 guidance
  "三轴 review 之前 pnpm test 全绿"插在任务完成与三轴 review 之间，
  与现有"三轴→体检→check:outdated"顺序不冲突，人工核对锚点。
