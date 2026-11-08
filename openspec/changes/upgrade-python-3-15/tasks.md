# Tasks

本 change 无新增数值实现（proposal Non-goals：不改数值行为与容差），
故无 red-before-green 新测试；验收靠既有闸门（design Decision 9）。
跨端对拍任务见第 5 组。

## 1. 全局 CLI 与工具链升级（spec「升级流程固定顺序」第 1 步）

- [ ] 1.1 node 26.12.1→26.13.0：`nvm install 26.13.0 --reinstall-packages-from=26.12.1`，验证 `openspec`、`markdownlint-cli2`、`pnpm` 在新版本可用（`ls /config/.nvm/versions/node/26.13.0/bin`）。验证: 三条命令均有版本输出。
- [ ] 1.2 pnpm 12.5.1→12.18.0（corepack，带 `COREPACK_ENABLE_DOWNLOAD_PROMPT=0`）、uv 0.13.5→0.13.7、rustup 1.29.2→1.29.3、openspec 1.15.0→1.16.1、markdownlint-cli2 0.23.3→0.24.0。验证: 各 `--version` 输出目标版。
- [ ] 1.3 rustup 升版后补装（spec「工具链升版后补装」Scenario）：确认 `1.99.1` 工具链的 rustfmt/clippy 组件与 `wasm32-unknown-unknown` target 在位，`cargo install --locked cargo-llvm-cov` 重装。验证: `rustup component list --installed`、`rustup target list --installed`、`cargo llvm-cov --version`。
- [ ] 1.4 wasm-pack 0.15.0→0.15.1：重跑 `scripts/install_wasm_pack.sh`。验证: `wasm-pack --version`。

## 2. cp315 可装性事实核查（design Risks 前两条的触发点）

- [ ] 2.1 `uv python install 3.15` 后，在临时环境确认 numpy 2.5.4 与 maturin 1.16.0 有 cp315 wheel 可装（非源码编译）。装不上 = 阻碍性问题，停止并报告（design Decision 6）。验证: `uv pip install --python 3.15 numpy maturin` 成功且非 sdist 构建。
- [ ] 2.2 核实 numpy crate 0.30 对 pyo3 的依赖范围（crates.io API 或 `cargo add --dry-run`），确认 pyo3 0.30 + numpy 0.30 可共存。解析不出 = 阻碍性问题，停止并报告。验证: 给出依赖范围原文。

## 3. Python 绑定升级与适配

- [ ] 3.1 `python/Cargo.toml`：pyo3 0.29→0.30（`abi3-py310` feature 不动）、numpy 0.29→0.30、pyo3-stub-gen 0.23→0.23.2。验证: `cargo tree -p netwave-python` 中 pyo3 与 numpy 同 0.30 线且无重复版本。
- [ ] 3.2 以编译报错驱动适配 pyo3 0.30 breaking changes（`FromPyObject` 默认不再生成、abi3 feature 逻辑、`PyBuffer` 弃用方法等；已扫 `python/src/lib.rs` 仅用 pyclass/pymethods + stub-gen）。工作量大小不构成停止理由；仅确认上游 bug 或真不兼容时报告。验证: `cargo build -p netwave-python` 通过、`clippy` 无新告警。
- [ ] 3.3 `python/` 下 `maturin develop` 后用 pytest 跑全量（3.15 解释器）。验证: pytest 全绿、覆盖率仍达铁律七阈值。
- [ ] 3.4 依赖刷新：`uv lock --upgrade --project python` 与根工程 `uv lock --upgrade`（maturin 1.16、pytest 9.2、numpy 2.5.4、pluggy/coverage 随动）。验证: lock diff 仅含预期包，无 JS/cargo 传递依赖混入。

## 4. 钉版点改齐（集中一笔 commit）

- [ ] 4.1 `python/.python-version` 与根 `.python-version`：3.14→3.15。
- [ ] 4.2 `.github/workflows/ci.yml`：python 矩阵最新格 3.14→3.15（3.10 底线格不变，不留 3.14 过渡格）。验证: `python3 scripts/versions/check_versions.py` 矩阵覆盖律通过。
- [ ] 4.3 根 `package.json`：`packageManager`→`pnpm@12.18.0`，`pnpm install` 刷新 `pnpm-lock.yaml`（仅 pnpm 元数据变化，不刷依赖版本）。验证: `pnpm -v` 与 `packageManager` 一致。
- [ ] 4.4 `python/Cargo.lock` 随 3.1 更新入库。验证: `git status` 钉版文件集合 = design Migration 第 5 步所列，无遗漏。

## 5. 全闸门与跨端对拍

- [ ] 5.1 清脏工作树：删 `python/netwave/_netwave.pyi`、`python/netwave/*.so`、`typescript/dist/` 等历史生成物（LL-047）。验证: `git status --ignored` 确认产物已清。
- [ ] 5.2 按序重建各端产物（maturin develop → stub_gen → napi build → wasm build）。验证: 三端类型产物齐备。
- [ ] 5.3 cross-binding 跨绑定对拍：`pnpm check:cross` 全绿（四端数值一致、容差不变、`check_vocab_types.py` 三端成员集合互等）。验证: 退出码 0，manifest 容差 key 零改动。
- [ ] 5.4 `pnpm check` 全绿（含 `check:md`、`check:meta` 四律、`check:py`）。验证: 退出码 0。

## 6. 文档同步与收尾

- [ ] 6.1 grep 全仓 `3.14` 残留清除（散文不复制数字，按 spec「散文不复制版本号」以文件指针措辞）。验证: `grep -rn '3\.14' --exclude-dir=target --exclude-dir=node_modules .` 无本升级相关残留。
- [ ] 6.2 `Plan/软件升级.md`：删除「Python 3.15 + pyo3 0.30 升级」整节与落地形态汇总中的对应行（apply 钩子：结论入本 change）。删后跑 `pnpm check:md`。验证: 退出码 0。
- [ ] 6.3 扫 `openspec/specs/` 全目录做三态时效检查（更新/新增/退役），结论写进本文件完成记录。验证: 结论清单存在。
- [ ] 6.4 retro：本次踩坑按性质归位——版本级 bug 进 `Plan/` blocked 计划（若出现），非版本性坑进 `openspec/specs/lessons-learned/` 对应分片 + INDEX。验证: 账本有对应条目或明确记「无新坑」。
- [ ] 6.5 闸门全绿后输出「分组→文件→commit 标题」全景表等人工点名（钉版一笔、代码适配一笔、文档一笔），不自行 `git commit`。验证: 全景表已给出且未提交。

## Workflow follow-up

- 本 change 归档前：确认 Plan/ 相关条目已清空（6.2）、specs 三态结论已留痕（6.3）。
- 归档后另开例行刷新普通 PR：JS（vitest/playwright/biome/tsdown/@napi-rs/cli 等）
  与 cargo 传递依赖刷新（design Decision 4）。

## 完成记录

（执行时填写：5.3/5.4 输出摘要、6.3 三态结论、6.4 账本条目编号、6.5 全景表。）
