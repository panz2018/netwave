# Design

## Context

See proposal.md - Why。当前钉版事实：两份 `.python-version` = 3.14；
`ci.yml` python 矩阵 = 3.10 底线格 + 3.14×3（OS 变体）；
`python/Cargo.toml` = pyo3 0.29（`abi3-py310`）/ numpy 0.29 /
pyo3-stub-gen 0.23.1；`packageManager` = pnpm@12.5.1；
`rust-toolchain.toml` = 1.99.1、MSRV 1.99（pyo3 0.30 要求 MSRV 1.85，
余量充足）。`scripts/versions/restrictions.json` 已落地且为空数组，
`check_outdated.py` 已消费。

本 change 是 `dependency-upgrade` spec 流程的执行任务，全部决策经
2026-11-07 grilling 逐条拍板（裁决记录见下 Decisions），无遗留歧义。

## Goals / Non-Goals

**Goals:**

- 运行时切到 3.15 且全部钉版点一次改齐（矩阵覆盖律当场可验）。
- pyo3 0.30 兼容迁移后四端对拍数值与容差零变化。
- 回滚 = 单条 `git revert`（钉版集中一笔 commit）。

**Non-Goals:**

- 设计层面不引入新机制：blocked/pairs/门禁化均不在本 change（见
  proposal.md Non-goals）。
- 不改 `dependency-upgrade` spec 措辞（`skip_specs`；发现残留数字
  当场补 delta 属例外）。

## Decisions

1. **前置不阻塞**（人工裁决原话"所谓的前置条件并不阻碍，不用理会"）：
   过期检查门禁化未拍板、oracle uv 环境未建成均不拦本次升级。
   备选：等机制齐再升——被否，门禁化与升级无技术耦合，oracle 属
   测试体系地基。
2. **oracle 条目移出**：原"oracle 3.15 重建 lock"删除，oracle uv 环境
   回归 `Plan/测试规划.md`。备选：顺手建 oracle——被否，两件事混做
   出问题难归因。
3. **全局 CLI 全升**（含 `packageManager`→pnpm@12.18.0）：spec 固定
   顺序第 1 步"落后先升"，挑着升会让前后环境混杂难归因。
4. **依赖只升 Python 必需**（maturin/pytest/numpy PyPI + pluggy、
   coverage 随动）：JS 与 cargo 传递依赖另开例行刷新 PR，避免
   vitest/biome 跨 minor 行为变化与 pyo3 适配混在一起。
5. **CI 矩阵不留 3.14 过渡格**：`3.10` + `3.15`×3。备选（三格过渡）
   被否——矩阵覆盖律只要求 `.python-version` 值在矩阵中，留旧格
   只是多养 CI。
6. **适配处置**（人工裁决原话"适配工作量大不是不升级的借口，降级的
   理由只有 bug 或者不兼容，不过如果遇到阻碍性的问题就随时报告"）：
   工作量本身不停；仅当确认上游 bug 或真不兼容时提出降级（届时按
   spec「坏版本降级」登记 `restrictions.json` 并另议）；阻碍性问题
   随时报告。
7. **nvm 迁移用 `--reinstall-packages-from`**：nvm 换补丁版同样丢
   全局包（openspec 曾因此消失），spec 虽只在换线强制，实际行为要求
   每次升 node 都迁移。
8. **`.pyi` 不提交**：`python/netwave/_netwave.pyi` 是 gitignore
   生成物；本地验证按 LL-047——先删各端历史产物（`.so`/`.pyi`/
   `typescript/dist/`），再 `maturin develop` → `stub_gen` →
   `pnpm check:cross`。
9. **不新增测试**：无新行为即无新断言；验收 = `pnpm check` 全绿 +
   `pnpm check:cross` 容差不变（矩阵覆盖律自动拦 3.15 漏改）。
10. **commit 分组**：钉版点集中一笔（回滚单动作）；代码适配、
    Plan 删节/账本回写各自另开；闸门绿后给全景表等点名，不自行提交。
11. **change 形态**：`upgrade-python-3-15` + `skip_specs: true`，
    已核实主 spec 无 `3.14` 残留数字。

## Risks / Trade-offs

- [cp315 wheel 实际未发布] → 执行第一步 `uv python install 3.15` 后
  立即验证 numpy/maturin 可装；装不上当场报告（阻碍性问题，Q6 裁决）。
- [numpy crate 0.30 与 pyo3 0.30 依赖范围未核实] → `cargo update`
  解析失败即当场报告，不猜。
- [pyo3 0.30 breaking 波及面超预期]（`FromPyObject` 默认不再生成、
  abi3 feature 逻辑、`PyBuffer` 弃用方法）→ 已扫 `python/src/lib.rs`
  仅用 pyclass/pymethods + stub-gen，高风险 API 未直接使用；若编译
  暴露更多，按 Decision 6 处置。
- [stub-gen 0.23.2 输出漂移] → `check_vocab_types.py` 在 `check:cross`
  末尾断言三端成员集合互等，漂移当场红。
- [pnpm 12.5→12.18 跨多版本行为变化] → `packageManager` 钉版使 CI
  与本地同版；`pnpm install` 后 lockfile diff 逐行看。
- [rustup 升级漏装组件/target] → 列入 tasks 显式步骤（spec Scenario），
  不靠记忆。

## Migration Plan

1. 全局 CLI 体检落后项先升（node 经 nvm `--reinstall-packages-from`、
   pnpm、uv、rustup + 组件/target/cargo 子命令、openspec、
   markdownlint-cli2、wasm-pack 重装脚本）。
2. cp315 wheel 可装性验证（风险 1、2 的触发点）。
3. 本地：`uv python install 3.15` → 升 pyo3/numpy/stub-gen →
   编译报错适配 → `maturin develop` → pytest 全绿。
4. 依赖刷新：`uv lock --upgrade`（python 工程 + 根工程）。
5. 钉版改齐：两份 `.python-version`、`ci.yml` 矩阵格、
   `packageManager`。
6. 清脏工作树 → 重建各端产物 → `pnpm check` + `pnpm check:cross`
   全绿（容差不变）。
7. grep 全仓 `3.14` 残留清除；`Plan/软件升级.md` 对应节删除；
   retro 回写 lessons-learned。
8. 闸门绿 → 提交全景表等点名。先本地验证再动 CI（LL-004）。

回滚：`git revert` 钉版 commit（版本钉全在钉版文件）。

## Open Questions

（无——grilling 已清空决策树；执行期事实核查见 Risks 前两条。）
