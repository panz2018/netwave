# Tasks

## 1 唯一实现先红后绿

- [ ] 1.1 改 `scripts/tests/test_drain_profraw.py`：`drain_stray_profraw`
      改测 `scripts/versions/lib/repository.py` 新位置（red：函数未迁移即失败）；
      补 CLI 冒烟测——subprocess 真跑 `python3 scripts/run/clean_stray_profraw.py`
      于 tmp 工作区，验证 stray 删除、target 内幸存、干净 exit 0、残留 exit 1
      并列出文件名（`单测随迁移`）
- [ ] 1.2 `drain_stray_profraw` 函数迁入 `scripts/versions/lib/repository.py`
      （复用同库 `SKIP_DIRS`，仅标准库，Python 3.10 兼容），新建薄 CLI 壳
      `scripts/run/clean_stray_profraw.py`（import + main，先删后报红 exit 1，
      报错列出文件名与个数），跑 `pnpm check:py` 使 1.1 转绿
      （`清扫唯一实现python`）
- [ ] 1.3 `scripts/tests/conftest.py` 与 `python/conftest.py` 删本地
      `drain_stray_profraw` 副本，改 import `lib.repository` 共享函数，
      fixture 语义不变（pre/post 先删后报红）（`清扫属测试进脚本`）
- [ ] 1.4 `typescript/test/global-drain-profraw.ts` 删复制的遍历逻辑，改
      spawnSync 调 `python3 scripts/run/clean_stray_profraw.py`（cwd=仓库根），
      报错文案指名缺 python3 时安装（`清扫唯一实现python`）

## 2 test_rs.sh 与根入口

- [ ] 2.1 新建 `scripts/run/test_rs.sh`：`set -euo pipefail`（`严格失败语义`）；
      开头 `command -v cargo-llvm-cov` 探测，缺则 stderr 打印
      `bash scripts/install_cargo_llvm_cov.sh` 并 exit 1，不自动安装
      （`缺工具报错不自动装`）；前后各调一次
      `python3 scripts/run/clean_stray_profraw.py`（`清扫属测试进脚本`）；
      中段 `mkdir -p coverage`、`cargo llvm-cov -p netwave --codecov`（输出
      `coverage/coverage-core.json`）、
      `python3 scripts/coverage_gate.py coverage/coverage-core.json 100`、
      `cargo build --workspace --all-targets`（`build看门闸入rs`）；
      core 测试仅此一处（`合并rs与rs-cov`）；目录与命名按
      `scripts/run/test_rs.sh`（`脚本目录scripts-run`）
- [ ] 2.2 根 `package.json` 加且仅加一行
      `"test:rs": "bash scripts/run/test_rs.sh"`（`脚本承载命令`、
      `范围只建test-rs`——不建其余 `test:*`）

## 3 ci.yml 切换

- [ ] 3.1 rust job：llvm-cov 步骤与前后两道 drain 块塌为一步
      `bash scripts/run/test_rs.sh`（upload-artifact 步骤保留），不为 rust job
      补 pnpm/Node 环境（`ci直调脚本不补pnpm`、`不合并ci-job`——job 拓扑不动）
- [ ] 3.2 python / node job 共四道 drain 步骤体改调
      `python3 scripts/run/clean_stray_profraw.py`（`清扫唯一实现python`）；
      人工核对根 `test:rs` 已接进 ci.yml（根级机器闸门归 Plan T4，本 change
      留痕不扩范围）

## 4 文档与 spec 同步（LL-034）

- [ ] 4.1 `openspec/specs/ci-matrix/spec.md`：按本 change specs delta 同步
      「五格构建矩阵」「覆盖率中间产物不跨轮残留」全文，新增「rust 测试根聚合
      入口」（`文档spec同步`）
- [ ] 4.2 `scripts/README.md`：第 20 行"清扫不是脚本"旧事实改写为唯一脚本
      现状 + 新增 `run/` 目录条目（含 Windows 本地需 python3 的「未验证」
      前置说明）；`CONTRIBUTING.md` 本地测试入口表述同步
      （`文档spec同步`）
- [ ] 4.3 `Plan/闸门重排-2026-11-12.md`：删除本 change 已承载的 T1（rust 半）
      与 profraw 去向章节，保留未执行任务（T2 其余、T3、T4、T5、T6 与
      决策二/三/四待拍板项）（`Plan/`）

## 5 验收与收尾

- [ ] 5.1 验收三判据（`验收三判据`）：①`pnpm test:rs` 本地全绿；
      ②`pnpm check` 全绿；③仓库根放 `stray.profraw` 后跑 `pnpm test:rs`
      报红并删除该文件
- [ ] 5.2 三轴 review：按 governance spec「元规则 review 三轴」
      （Standards/Spec/Lessons）对照本 change 工件审实现 diff，逐文件对上
      tasks.md，硬伤清零（`三轴`）
- [ ] 5.3 三态时效：扫 openspec/specs/ 全目录，对本次改动产出
      "更新/新增/退役"结论留痕本文件（ci-matrix 更新；无新增/退役能力）
      （`三态时效`）
- [ ] 5.4 体检：对触碰文件全文只读体检（health-check spec apply 态），
      发现附文件+行号+证据落 Plan/ 等点名（`体检`）
- [ ] 5.5 迟到追加：复查 proposal.md `## 已定裁决` 每关键词载体任务已打勾
      （`迟到追加`）
- [ ] 5.6 归档：本 change 完成后的归档流程中，archive 态只读体检跳过
      2026-11-17（`归档体检一次性跳过`——仅本 change 一次性，config.yaml
      archive guidance 与 health-check spec 规则本体不变）
- [ ] 5.7 跑 `pnpm check:outdated` 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化 LAG，复跑至 SUMMARY 归零
      （`check:outdated`）
