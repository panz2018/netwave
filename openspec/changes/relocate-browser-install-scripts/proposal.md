# Proposal

## Why

`browser/` 子项目独立成包后，两个只服务 browser 覆盖率链的安装脚本
（`install_wasi_sdk.sh`、`install_wasm_bindgen_cli.sh`）仍散落在仓库根 `scripts/`，
且 `typescript/` 里残留着 wasm 构建迁走前的死目录与死 `.gitignore` 条目。按
「删掉 `browser/` 后必须跟着删的文件就是 browser 资产」判据，这些该归位或清理。
本 change 是 `Plan/browser资产彻底归位.md` 的第一批（T1-T3）。

## What Changes

- `scripts/install_wasi_sdk.sh` → `browser/scripts/install_wasi_sdk.sh`（脚本自身
  零改动，无相对路径假设）。
- `scripts/install_wasm_bindgen_cli.sh` → `browser/scripts/install_wasm_bindgen_cli.sh`，
  同批改脚本内读 workspace 根 lockfile 的相对路径 `../Cargo.lock` →
  `../../Cargo.lock`（搬后 `../` 会错指到 `browser/`，不改则 CI browser job 挂）。
- 引用面同步：`browser/scripts/test.sh` 探测提示路径、`.github/workflows/ci.yml`
  browser job 安装步命令、`openspec/specs/ci-matrix/spec.md` 内三处 requirement
  的路径字符串。
- `scripts/README.md` 删除两脚本对应表格行；新建 `browser/README.md`，承接两脚本
  说明并记录 browser 包常用命令（英文书写）。
- `typescript/.gitignore` 删除 `target-wasm/`、`target-wasm-cov/` 两条死规则；
  本地删除对应两个未跟踪死目录（不进 git）。

## Capabilities

### New Capabilities

（无新增 capability。）

### Modified Capabilities

- `ci-matrix`：三条 requirement 正文/Scenario 内的安装脚本路径字符串随搬迁更新
  （「全项目浏览器测试根聚合入口」「覆盖率门槛生效（铁律七）」「wasm 覆盖率链的
  编译与阅卷工具均无需 sudo」）。行为契约不变，仅路径事实更新。

## Impact

- 移动：`scripts/install_wasi_sdk.sh`、`scripts/install_wasm_bindgen_cli.sh`。
- 改动：`browser/scripts/test.sh`、`.github/workflows/ci.yml`、`scripts/README.md`、
  `typescript/.gitignore`、`openspec/specs/ci-matrix/spec.md`（经 delta）。
- 新增：`browser/README.md`。
- 本地清理（不进 git）：`typescript/target-wasm/`、`typescript/target-wasm-cov/`。
- 不受影响（实证）：`scripts/tests/test_test_browser_wiring.py` L116-117 用文件名
  正则 `install_wasi_sdk\.sh`（不带路径前缀），探测提示改新路径后断言仍命中。

## Non-goals

- 不迁 `scripts/tests/test_test_browser_wiring.py`（wiring 测试归属与语言属
  `Plan/browser资产彻底归位.md` §4，本批不做）。
- 不改 `build:browser` → `build` 命令名（属 §6，单独批次）。
- 不做全仓 wasm 穷举扫描兜底（属 §8，收尾批次）。
- 不动 `core/` 内任何 wasm 相关内容。

## Prior art

- 同生态无现成方案：本改动是本仓库特有的资产归位，非通用机制。
- 仓库内先例：`openspec/changes/archive/**` 中 `extract-browser-test-chain`
  已确立「browser 测试资产随链路归位迁入 `browser/`」的同判据搬迁模式。

## 专家增补

- 搬迁后本地冒烟验证探测提示：`bash browser/scripts/install_wasi_sdk.sh` 与
  `bash browser/scripts/install_wasm_bindgen_cli.sh` 至少跑到探测/usage 段，确认
  `../../Cargo.lock` 修正生效（`install_wasm_bindgen_cli.sh` 能读到版本）。
- `install_wasm_bindgen_cli.sh` L28 的 `$(dirname "$0")/../Cargo.lock` 是搬迁唯一
  隐藏坑，资深工程师会在搬的同一笔里改 `../../Cargo.lock` 并跑一次脚本验证版本
  解析非空，而非留给 CI 兜底。

## 已定裁决

- `搬迁范围`：本 change 只装 T1-T3（两脚本搬迁 + typescript wasm 残留清理），
  wiring 迁移/改名/全仓扫描均移出本批。
- `Cargo.lock修正`：`install_wasm_bindgen_cli.sh` 读根 lockfile 的相对路径随搬迁
  同批改为 `../../Cargo.lock`，不拆独立提交。
- `README承接`：新建 `browser/README.md` 记录 browser 包常用命令并承接两脚本说明，
  `scripts/README.md` 删对应两行。
- `提交粒度`：T1（typescript 清理）独立一笔；T2+T3（两脚本搬迁，波及同批相邻文件）
  合并一笔，避免 ci.yml/README/spec 的半搬中间态。
- `change承载`：单开本 change 装 T1-T3，命名 `relocate-browser-install-scripts`。
- `归档体检跳过`：本 change 归档时跳过 health-check spec 的 archive 态只读体检
  （全项目存量维），仅指 archive 态，不含 apply 态被触碰文件体检（后者照常执行）。
