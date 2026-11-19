# Tasks

## 1 改名 `check:cross` → `test:cross`

- [x] 1..1 `改名乙`：根 `package.json` 把 `check:cross` 脚本键改名为 `test:cross`，
      值改为 `bash scripts/run/test_cross.sh`。验证：`pnpm run` 列表含 `test:cross`
      无 `check:cross`。
- [x] 1..2 `改名乙`：全仓活文件 `check:cross`→`test:cross` 一次改全
      （`CONTRIBUTING.md`、`oracle/README.md`、`scripts/README.md`、
      `scripts/check_verbs.py`、`scripts/check_vocab_types.py`、
      `typescript/scripts/dump.mjs`、`openspec/specs/dependency-upgrade/spec.md`、
      `openspec/specs/project-governance/spec.md`、
      `openspec/specs/lessons-learned/{ci,core,python,typescript}.md`、
      `Plan/测试规划.md`），archive 区不动。验证：
      `grep -rn check:cross --include='*' . | grep -v openspec/changes/archive` 为空。

## 2 新建 `scripts/run/test_cross.sh`

- [x] 2..1 `脚本同构`：新建 `scripts/run/test_cross.sh`，`set -euo pipefail`、
      `cd "$(dirname "$0")/../.."`，承载 `uv sync --project python`、
      `maturin develop`、`LD_LIBRARY_PATH` 导出、`stub_gen`、四端 dump、
      `compare_cross.py` 阅卷、`check_vocab_types.py`、`check_verbs.py`。验证：
      `bash -n scripts/run/test_cross.sh` 通过。
- [x] 2..2 `产物探测报错`：脚本 dump 前探测 napi 原生产物与 wasm 产物存在性
      （先 `ls typescript/native`、`ls typescript/wasm` 实证产物名再写条件），
      缺则 stderr 打印 `pnpm test:ts` 并非零退出，不重复构建逻辑。验证：
      临时移走产物后跑脚本即红且提示含 `pnpm test:ts`。

## 3 CI 接线

- [x] 3..1 `脚本同构`：`.github/workflows/ci.yml` node job 把内联 cross 前置块
      （uv sync/maturin/LD_LIBRARY_PATH/stub_gen/check:cross）缩成一行
      `bash scripts/run/test_cross.sh`。验证：`python3 scripts/check_ci.py` 绿
      （`test:cross`→`test_cross.sh` 接线被识别）。
- [x] 3..2 `pnpm test本地专用`：确认 ci.yml 不新增 `pnpm test` 步骤，各 `test_*.sh`
      仍分 job 调用。验证：`grep -n 'pnpm test$' .github/workflows/ci.yml` 为空。

## 4 根 `pnpm test` 聚合入口

- [x] 4..1 `聚合含cross`：根 `package.json` 加 `"test"` 脚本，顺序
      `test:rs`→`test:py`→`test:ts`→`test:cross`。验证：`pnpm test` 全链 exit 0。

## 5 config.yaml 两条规则

- [x] 5..1 `单change承载`：`openspec/config.yaml` tasks 规则加一条——验证命令 MUST
      引用根聚合入口（`pnpm check`/`pnpm test`/`pnpm test:cross`），禁手抄 CI 内联参数。
- [x] 5..2 `单change承载`：`openspec/config.yaml` apply guidance 加一条——三轴 review
      之前 MUST `pnpm test` 全绿；锚点与现有"三轴→体检→check:outdated"核对不互斥
      （LL-089）。验证：人工核对顺序 + `pnpm check:md` 绿。

## 6 升级验收判据改全量

- [x] 6..0 `升级验收用pnpm test`：`openspec/specs/dependency-upgrade/spec.md` 主 spec
      同步——「升级执行权限划分」「升级流程固定顺序」验收 scenario 由
      `pnpm check:cross` 改为 `pnpm check` + `pnpm test`（与本 change delta 一致）。
      验证：主 spec 内 `check:cross` 清零 + `pnpm check:md` 绿。

## 7 测试覆盖

- [x] 7..1 `改名乙`：`scripts/tests/test_check_ci.py` 补 `test:cross`→
      `scripts/run/test_cross.sh` 接线断言。验证：`uv run pytest scripts/tests/test_check_ci.py` 绿。

## 8 Plan 收尾

- [x] 8..1 `Plan整档删除`：删除 `Plan/闸门重排-2026-11-12.md`（四项全部有归宿，
      bench 延后裁决已留痕本 change `## 已定裁决`）。验证：文件不存在 + `pnpm check:md` 绿。
- [x] 8..2 `Plan/` 收尾对账：grep `Plan/` 与本 change 相关条目，确认无残留已完成规划。

## 9 三态时效与 review

- [x] 9.1 `三态时效`：扫 `openspec/specs/` 全目录，对照本 change 产出更新/新增/退役
      三态时效结论留痕本文件（更新=ci-matrix/dependency-upgrade/project-governance，
      新增=无，退役=无）。
- [x] 9.2 `三轴`：按 governance spec「元规则 review 三轴」对照本 change 工件审实现
      diff，diff 文件集逐文件对上本 tasks.md，硬伤清零才准入后续步骤。
- [x] 9.3 `体检`：三轴 review 之后、check:outdated 之前，对被触碰文件全文做只读体检
      （health-check spec apply 态），发现落 `Plan/` 等点名，不阻塞。
- [x] 9.4 `迟到追加`：apply 中途拍板的决定当场追加进 proposal.md `## 已定裁决` 段并补
      对应任务行，收尾复查每个关键词载体任务已打勾。
- [x] 9.5 `本次归档跳过体检`：本 change 归档时一次性跳过 health-check spec 的
      archive 态体检（仅本次，规则本体不删不改；apply 态体检照常）。
- [x] 9.6 `check:outdated`：跑 `pnpm check:outdated` 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化所报 LAG，消化后复跑至退出码 0（SUMMARY 归零）。
