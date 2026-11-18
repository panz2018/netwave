# Proposal

## Why

根 `package.json` 没有任何测试入口（只有 `check:*` 静态检查），rust 测试与
覆盖率链只存在于 ci.yml 内联，本地无同口径聚合命令；tasks.md 手抄 CI 参数
抄漏 `--coverage` 即本地假绿（CI run 43141529804 八 job 同根因，
`Plan/闸门重排-2026-11-12.md` §1）。profraw 清扫逻辑现存四份重复实现
（根 conftest、python conftest、vitest ts、ci.yml 内联 ×4），剪枝清单与
`SKIP_DIRS` 分叉即参数漂移病根复发。

## What Changes

- 根 `package.json` 新增 `test:rs` 薄调用入口：`bash scripts/run/test_rs.sh`。
- 新建 `scripts/run/test_rs.sh`：core 覆盖率全链（llvm-cov → gate 100 →
  build 看门闸）+ 前后 profraw 清扫 + `target/llvm-cov-target/` 前后整目录
  删除 + 缺工具探测报错，本地与 CI 同一脚本。
- 新建 `scripts/run/clean_stray_profraw.py`：profraw 清扫唯一 CLI 壳；
  实现函数 `drain_stray_profraw` 迁入 `scripts/versions/lib/repository.py`
  （与 `SKIP_DIRS` 同家），根 conftest、python conftest、
  `typescript/test/global-drain-profraw.ts`、ci.yml 全部 drain 步骤改为消费
  这一份实现。
- ci.yml：rust job 的 llvm-cov 步骤与前后两道 drain 块塌为一步
  `bash scripts/run/test_rs.sh`；python / node job 共四道 drain 块改调
  `python3 scripts/run/clean_stray_profraw.py`。
- ci-matrix spec：profraw 清理要求改为统一调唯一脚本；rust job 口径与
  "命令细节唯一真相源"措辞更新（package.json 与 CI 都只调用
  `scripts/run/*.sh`）。
- 文档同步：`scripts/README.md`（"清扫不是脚本"旧事实改写 + `run/` 条目）、
  `CONTRIBUTING.md` 本地测试入口表述、`Plan/闸门重排-2026-11-12.md`
  已定裁决章节删除。

## Capabilities

### New Capabilities

- 无（不新增能力域）。

### Modified Capabilities

- `ci-matrix`：rust 测试入口从 ci.yml 内联改为根聚合入口 `test:rs` 调
  `scripts/run/test_rs.sh`；profraw 清理从"各 harness/CI 各自实现"改为
  "唯一脚本 `scripts/run/clean_stray_profraw.py`，四端消费"。

## Impact

- `.github/workflows/ci.yml`（rust job 塌一步、python/node job 四道 drain 块换命令）
- `package.json`（+1 行 `test:rs`）
- `scripts/run/`（新目录：`test_rs.sh`、`clean_stray_profraw.py`）
- `scripts/versions/lib/repository.py`（+`drain_stray_profraw` 函数）
- `scripts/tests/conftest.py`、`python/conftest.py`、
  `typescript/test/global-drain-profraw.ts`（删重复实现，改消费唯一实现）
- `scripts/tests/test_drain_profraw.py`（改测新位置 + CLI 冒烟测）
- `openspec/specs/ci-matrix/spec.md`、`scripts/README.md`、
  `CONTRIBUTING.md`、`Plan/闸门重排-2026-11-12.md`
- 铁律七（覆盖率门槛）口径不变，仅执行载体变化；LL-103 教训本体不变。

## Non-goals

- 不建 `test:py` / `test:ts` / `test:wasm` / `test:cross` / `test` 总入口
  （归 `Plan/闸门重排-2026-11-12.md` 其余任务，后续点名）。
- 不合并 CI job（维持语言 × 平台矩阵；"每 OS 单 job"变体若要做另立 Plan/ 条目）。
- 不改覆盖率阈值、豁免规则与报告命名（铁律七口径不动）。
- 不做 bench 相关改动（决策五：bench 未完工，本轮不动）。
- `check:cross` 不改名（决策二不在本 change 范围）。

## Prior art

- 仓库内既有模式：`scripts/install_cargo_llvm_cov.sh` 等 `install_*.sh`
  已是"脚本承载命令、调用方一行"的先例；`scripts/versions/lib/repository.py`
  的 `SKIP_DIRS` 已是剪枝清单单一来源，本 change 把清扫函数并入同家。
- GitHub Actions runner-images 官方 README（ubuntu / macOS / Windows2022 /
  Windows2025）实证 Python 与 Bash 均四平台预装：
  [Windows2025-Readme.md](https://github.com/actions/runner-images/blob/main/images/windows/Windows2025-Readme.md)
  等，故选 Python 不引入 CI 安装步骤。

## 专家增补

- 为唯一实现补单测迁移：`scripts/tests/test_drain_profraw.py` 改测
  `lib/repository.py` 新位置并补 `clean_stray_profraw.py` 的 subprocess
  冒烟测——防"唯一实现"自身无执法。
- `scripts/check_ci.py` 现只扫 typescript 级 `test:*`，根级 `test:rs` 不在其
  扫描范围——"CI 不跑的测试不算闸门"（LL-037）对根入口暂靠人工核对；
  根级接线闸门升级归 `Plan/闸门重排-2026-11-12.md` T4，本 change 不扩范围，
  仅在本条留痕防遗忘。
- `test_rs.sh` 开头探测 `cargo-llvm-cov`，缺则打印
  `bash scripts/install_cargo_llvm_cov.sh` 并非零退出——本地缺工具时报错
  可行动，不静默假绿。

## 已定裁决

- `范围只建test-rs`：本次只建 `test:rs` 一个入口，其余 `test:*` 留待后续点名。
- `合并rs与rs-cov`：`test:rs` 与 `test:rs:cov` 合并为单一入口，core 测试只跑一遍。
- `脚本承载命令`：命令细节放 `scripts/run/test_rs.sh`，`package.json` 只留薄调用，防参数抄漏。
- `脚本目录scripts-run`：新脚本放 `scripts/run/`，避开 `scripts/tests/` 撞名；脚本名 `test_rs.sh`。
- `清扫属测试进脚本`：profraw 前后清扫属于测试的一部分，进 `test_rs.sh` 与 CI，不留开关。
- `清扫唯一实现python`：唯一实现 = `drain_stray_profraw` 函数进 `scripts/versions/lib/repository.py`，CLI 壳 `scripts/run/clean_stray_profraw.py`，四端（CI 步骤、`test_rs.sh`、两个 conftest、vitest ts）全消费。
- `build看门闸入rs`：`test_rs.sh` 含 `cargo build --workspace --all-targets`，本地与 CI 同口径。
- `缺工具报错不自动装`：`test_rs.sh` 探测 cargo-llvm-cov，缺则打印安装命令并非零退出，不自动安装。
- `严格失败语义`：脚本 `set -euo pipefail`；清扫先删后报红 exit 1。
- `ci直调脚本不补pnpm`：ci.yml rust job 直接 `bash scripts/run/test_rs.sh`，不为其补 pnpm/Node 环境；清扫调裸 `python3`（零第三方依赖，四平台预装）。
- `不合并ci-job`：CI 维持语言 × 平台矩阵不合并；"每 OS 单 job"变体另立 Plan/ 条目另行讨论。
- `验收三判据`：①本地 `pnpm test:rs` 全绿；②`pnpm check` 全绿（含 `check:md`，不单列）；③人为放 `stray.profraw` 再跑 `test:rs` 能报红并删除。
- `单测随迁移`：`scripts/tests/test_drain_profraw.py` 改测 `lib/repository.py` 新位置并补 CLI 壳 subprocess 冒烟测。
- `文档spec同步`：ci-matrix spec、`scripts/README.md`、`CONTRIBUTING.md`、
  `Plan/闸门重排-2026-11-12.md` 随本 change 同步（LL-034）；LL-103 账本不动。
- `插桩目录前后删除`：`test_rs.sh` 在 llvm-cov 步骤前后各执行一次
  `rm -rf target/llvm-cov-target`，不依赖 `cargo llvm-cov clean`（LL-101
  静默 no-op，旧插桩二进制按旧行号污染报告；前置删防污染、后置删不留旧
  向量，前置已删故后置零成本；人工裁决 2026-11-17）。
- `归档体检一次性跳过`：本 change 归档流程中的 archive 态只读体检跳过
  （仅本次一次性，config.yaml archive guidance 与 health-check spec
  规则本体不变；人工裁决 2026-11-17）。
