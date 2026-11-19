# Proposal

## Why

`Plan/闸门重排-2026-11-12.md` 收尾遗留三项未执行：根 `pnpm test` 总聚合入口缺失、
`openspec/config.yaml` 缺两条引用聚合入口的规则、`check:cross` 命名挂在 `check:*`
家族却实际跑四端代码（分类异类）。三项互相依赖（T5 规则文本要引用聚合入口与
cross 入口名），且 `check_ci.py` 已规定每个根 `test:*` 必须经
`scripts/run/test_<name>.sh` 接进 CI——`test:cross` 一旦存在就须配同名脚本，
改名与接线成本本就同源，故一个 change 一并收口。

## What Changes

- 根 `package.json` 新增 `test` 聚合入口，顺序 `test:rs` → `test:py` → `test:ts` →
  `test:cross`（本地专用，不进 CI）。
- **BREAKING** `check:cross` 改名 `test:cross`：值改为薄调新建的
  `scripts/run/test_cross.sh`；全仓活文件（约 16 个）一次改全，archive 区冻结不动。
- 新建 `scripts/run/test_cross.sh`，与 `test_rs/py/ts.sh` 同构（`set -euo pipefail`、
  工具/产物存在性探测、行动化报错）；承载原 ci.yml node job 内联前置
  （`uv sync`、`maturin develop`、`LD_LIBRARY_PATH` 导出、`stub_gen`）+ 四端 dump +
  阅卷 + 词汇类型 + 动词集合闸门。
- `ci.yml` node job 内联前置段缩成一行 `bash scripts/run/test_cross.sh`。
- `openspec/config.yaml` 加两条规则：tasks 规则（验证命令 MUST 引用根聚合入口，
  禁手抄 CI 内联参数）、apply guidance（三轴 review 之前 MUST `pnpm test` 全绿）。
- 删除 `Plan/闸门重排-2026-11-12.md`（四项全部有归宿，bench 延后裁决写入本档
  `## 已定裁决`）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ci-matrix`：新增 `test:cross` 根聚合入口 Requirement（薄调 `test_cross.sh`、
  本地与 CI 同脚本、产物缺失行动化报错）与根 `test` 聚合入口 Requirement
  （本地专用、顺序 rs→py→ts→cross）；`check:cross` 相关口径改名为 `test:cross`。
- `dependency-upgrade`：「升级执行权限划分」「升级流程固定顺序」两条 Requirement
  的验收 scenario 由 `pnpm check:cross` 改为 `pnpm check` + `pnpm test`
  （全量测试含四端对拍，单测问题不再漏检）。
- `project-governance`：「元规则 review 三轴」Requirement 正文里
  `pnpm check:cross` 改名 `pnpm test:cross`。

## Impact

- 配置：根 `package.json`（加 `test`、`check:cross`→`test:cross`）、
  `.github/workflows/ci.yml`（node job 内联段缩一行）、`openspec/config.yaml`（两条规则）。
- 脚本：新建 `scripts/run/test_cross.sh`；`scripts/tests/test_check_ci.py` 补 `test:cross` 接线覆盖。
- 改名波及活文件：`CONTRIBUTING.md`、`oracle/README.md`、`scripts/README.md`、
  `scripts/check_verbs.py`、`scripts/check_vocab_types.py`、`typescript/scripts/dump.mjs`、
  `openspec/specs/dependency-upgrade/spec.md`、`openspec/specs/project-governance/spec.md`、
  lessons-learned 四份分片（ci/core/python/typescript）、`Plan/测试规划.md`。
- 删除：`Plan/闸门重排-2026-11-12.md`。
- 铁律：触及 CI 构建不变式（LL-034）与覆盖率/对拍闸门口径，无产品代码/数值路径改动。

## Non-goals

- bench 不进聚合：基线持久化未落地、现仅测噪声，本轮不动，完工后再议。
- `pnpm test` 不进 CI：CI 各 `test_*.sh` 分布在不同 job 无法同场聚合，`pnpm test`
  仅本地便利入口。
- 不改 cross 对拍的数值对拍逻辑与容差（仅改名与接线，答卷字段零改动）。
- 不动 archive 区已冻结的历史 change 工件。

## Prior art

- `scripts/run/test_rs.sh` / `test_py.sh` / `test_ts.sh`：同构脚本模板（存在性探测、
  `set -euo pipefail`、行动化报错、profraw 清扫），`test_cross.sh` 直接复用该模式。
- `scripts/check_ci.py`：根 `test:*` → `scripts/run/test_<name>.sh` 接线闸门，
  决定 `test:cross` 必须配同名脚本。
- `openspec/specs/ci-matrix/spec.md`「本地与 CI 同脚本」条款：`test_cross.sh` 同构先例。

## 专家增补

- `scripts/tests/test_check_ci.py` 现有测试只覆盖 `test:rs/py/ts` 接线；顶尖专家会补
  `test:cross` → `scripts/run/test_cross.sh` 的接线断言，防改名后接线漏网假绿。
- 会在 `test_cross.sh` 探测段对 napi/wasm 产物缺失打印"先跑 `pnpm test:ts`"的具体
  命令而非泛泛报错，与 `test_rs.sh` 缺 `cargo-llvm-cov` 时打印安装命令同口径。

## 已定裁决

- `改名乙`：`check:cross` 整体改名 `test:cross`，全仓活文件一次改全，archive 冻结不动。
- `聚合含cross`：根 `pnpm test` = `test:rs` → `test:py` → `test:ts` → `test:cross`。
- `单change承载`：一个 change `add-test-aggregate-and-rename-cross` 装下聚合、改名、T5 规则。
- `脚本同构`：`test_cross.sh` 与 `test_rs/py/ts.sh` 同格式，CI 内联前置整体搬入脚本。
- `产物探测报错`：`test_cross.sh` 探测 napi/wasm 产物，缺失即非零退出并提示先跑 `pnpm test:ts`，不重复构建逻辑。
- `Plan整档删除`：`Plan/闸门重排-2026-11-12.md` 整档删除，bench 延后裁决留痕本段。
- `pnpm test本地专用`：`pnpm test` 不进 CI，CI 保持逐 `test_*.sh` 分 job 调用不变。
- `升级验收用pnpm test`：dependency-upgrade 验收判据由 `pnpm check:cross` 改为
  `pnpm check` + `pnpm test`（全量测试含四端对拍），单测问题不再漏检。
- `本次归档跳过体检`：health-check spec 的 archive 态体检仅本次 change 归档时
  一次性跳过，规则本体不删不改；apply 态体检照常执行。
