# Proposal

## Why

Python 3.15 已是稳定版，本项目所需库全部声明支持（numpy 2.5.4
`requires-python>=3.12`、pyo3 0.30.0 起支持 3.15 final
[PyO3#6517](https://github.com/PyO3/pyo3/pull/6517)、maturin 1.16.0、
pytest 9.2.0、ruff 0.17.4、scikit-rf 2.2.0），按

> [dependency-upgrade spec](../../../specs/dependency-upgrade/spec.md)
> 「选线原则——单线运行时取最新稳定 minor」应切 3.15；当前两份
> `.python-version` 钉 3.14，体检持续报 LAG。

原暂缓理由（治理机制未落地）已由人工裁决解除：前置条件不阻塞升级
（2026-11-07 拍板"所谓的前置条件并不阻碍，不用理会"）。

## What Changes

- 运行时 3.14→3.15：`python/.python-version`、根 `.python-version`、
  `ci.yml` python 矩阵最新格（3.10 底线格不变）。
- pyo3 0.29→0.30、numpy crate 同 major 联动 0.29→0.30、
  `pyo3-stub-gen` 0.23.1→0.23.2（配套版本，兼容 pyo3 <0.31）；
  breaking changes 以编译报错驱动逐项适配。
- Python 侧依赖刷新：maturin 1.15→1.16、pytest 9.1→9.2、
  numpy PyPI 2.5.3→2.5.4、pluggy/coverage 随动（`uv lock --upgrade`）。
- 全局 CLI 全升（spec「升级流程固定顺序」第 1 步）：node 26.12.1→26.13.0
  （以 `nvm install --reinstall-packages-from` 迁移全局包）、
  pnpm 12.5.1→12.18.0、uv 0.13.5→0.13.7、rustup 1.29.2→1.29.3、
  openspec 1.15.0→1.16.1、markdownlint-cli2 0.23.3→0.24.0、
  wasm-pack 0.15.0→0.15.1。
- `packageManager` 随 pnpm 升到 `pnpm@12.18.0`（根 `package.json`）。
- rustup 升版后按 spec「工具链升版后补装」补组件/target 并重装
  cargo 子命令；wasm-pack 重跑 `scripts/install_wasm_pack.sh`。
- 适配完成后 grep 全仓 `3.14` 残留清除，retro 回写 lessons-learned。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——本 change 是 `dependency-upgrade` spec 既有流程的执行任务，
不改任何 spec 级行为：选线原则、矩阵覆盖律、升级流程均已存在且
措辞不含具体版本号。故 `skip_specs: true`。执行中若发现主 spec
残留数字或缺漏，当场补 delta。）

## Non-goals

- 不抬 Python 底线：`requires-python` 维持 `>=3.10`，
  abi3 维持 `abi3-py310`（一个 wheel 覆盖 3.10–3.15），不切 abi3-py315。
- 不动 Node 矩阵（`ci.yml` node 格 22/26 不变）、不动 MSRV
  （`rust-version` 1.99 与 `rust-toolchain.toml` 不变）。
- 不采纳 pyo3 0.30 新特性（`PyFrozenDict`、`PyContext` 等），只做
  兼容迁移；不改任何数值行为与容差（manifest `core_tol` 等不动，
  铁律三）。
- 不建 oracle uv 环境（`oracle/golden/` 属测试体系地基任务，回归
  `Plan/测试规划.md` 自己的清单，不搭本 change 的车）。
- 不刷新 JS 与 cargo 传递依赖（vitest/playwright/biome、cargo
  lockfile 传递项）——属例行刷新，另开普通 PR（spec「升级分级」）。
- 不为 3.15 新增测试：无新行为即无新断言，验收靠现成闸门。
- 不提交 `python/netwave/_netwave.pyi`（gitignore 的生成物，
  由 `stub_gen` 现生成、`check_vocab_types.py` 消费）。
- 不实施过期检查门禁化、pairs JSON 化（各自独立待拍板/待触发）。

## Impact

- 钉版点（集中一笔 commit，回滚 = 单条 `git revert`）：
  `python/.python-version`、`.python-version`、`.github/workflows/ci.yml`、
  `python/Cargo.toml`（pyo3/numpy/pyo3-stub-gen）、`package.json`
  （`packageManager`）、`python/uv.lock`、`uv.lock`。
- 代码适配（另开 commit）：`python/src/lib.rs`、
  `python/src/bin/stub_gen.rs` 视编译报错而定；core/typescript/wasm
  零改动预期。
- 文档（另开 commit）：`Plan/软件升级.md`「Python 3.15」节删除
  （apply 钩子）；`openspec/specs/lessons-learned/` 回写踩坑。
- 本机环境：nvm 新 node 版本 + 全局包迁移、uv、rustup 工具链与
  target/组件、cargo 子命令、GitHub 直装工具。
- 受影响的铁律：铁律三（容差集中在 manifest——本次零改动，四端对拍
  容差不变）、铁律七（覆盖率 100%——3.15 下 `check:py` 仍须达标）、
  铁律四（主 CI 零 Python——`ci.yml` 只改矩阵格，不新增 scikit-rf
  依赖）。

## Prior art

- 仓库内既有流程：
  [dependency-upgrade spec](../../../specs/dependency-upgrade/spec.md)
  「运行时大版本升级流程」「升级流程固定顺序」「工具链升版后补装」
  三条 Requirement 即本 change 的执行依据，不新造流程。
- 仓库内既有坑账本：`openspec/specs/lessons-learned/ci.md` LL-047
  （本地模拟 CI 前先删各端历史产物，别信脏工作树）。
- 上游现成方案：PyO3 官方
  [migration guide](https://pyo3.rs/latest/migration.html) 与
  pyo3 0.30.0 CHANGELOG（3.15 final 支持、MSRV 1.85、弃 Python 3.8）；
  nvm 官方 `--reinstall-packages-from` 迁移全局包。

## 专家增补

- 执行第一步先核 cp315 wheel 实际可装：`requires-python` 声明支持 ≠
  发布了 cp315 预编译 wheel，`uv python install 3.15` 后立刻
  `uv lock --upgrade --project python` + `maturin develop` 验证
  numpy/maturin 装得上，装不上即阻碍性问题当场报告。
- rustup 升 1.29.3 后 `cargo install --locked` 重装 `cargo-llvm-cov`
  并补 `wasm32-unknown-unknown` target——rustup 不随版本带这些，
  漏了覆盖率闸门与 wasm 构建当场红（spec「工具链升版后补装」）。
- 本地跑 `pnpm check:cross` 前先删各端历史产物（`.so`、`.pyi`、
  `typescript/dist/`）再按序重建，避免脏工作树让本地绿、CI 红（LL-047）。
- 闸门全绿后给「分组→文件→commit 标题」全景表等人工点名，不自行
  `git commit`（用户提交规则）。
- numpy crate 0.30 对 pyo3 的依赖范围提案时未能当场核实（GitHub 索引
  不可用），列为执行第一步事实核查：`cargo update` 解析不出
  pyo3 0.30 + numpy 0.30 共存即阻碍性问题，当场报告。
