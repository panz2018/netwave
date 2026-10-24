# Design

## Context

See proposal.md - Why. 现状钉死点盘点（实施时的起点，最终以登记表为准）：
`rust-toolchain.toml`（pin）、`core/Cargo.toml` / `python/Cargo.toml` /
`typescript/native/Cargo.toml` / `typescript/wasm/Cargo.toml`（`rust-version`）、
根 `package.json`（`packageManager`、devDependencies）、`typescript/package.json`
（`engines.node`、devDependencies）、`pnpm-lock.yaml`、`python/pyproject.toml` +
`python/uv.lock` + `python/.python-version`、`oracle/`（skrf 环境 pin，随
`upgrade-python-3-15` 建立）、`scripts/install_wasm_pack.sh` /
`install_binaryen.sh`（GitHub release 直装）、CI 的 `cargo install cargo-llvm-cov`、
`.github/workflows/ci.yml` 的 actions 版本与矩阵数字、Playwright Chromium。
散文侧：AGENTS.md「依赖版本策略」、CONTRIBUTING.md「Toolchain freshness」、
workspace-layout「版本底线」、ci-matrix「语言版本矩阵」。

## Goals / Non-Goals

**Goals:**

- 登记表 + 闸门让"手动升版后某处漏改"当场可见（已知漂移类问题）。
- 升级流程、分级、选线、登记、回退证据一次定清，之后升级直接引用 spec。
- 文档迁移后版本类事实单源：数字只在登记表与清单文件，散文只写规则与链接。

**Non-Goals:**

- 不做自动化升级执行（无人值守自动升版）——体检只报告，升级动作仍由人触发。
- 不实现 Python 3.15/pyo3 兼容（另 change）；不改 core 数值与 API。
- 闸门不联网：对账只读仓库内文件；联网检查全部归 `check:outdated`。

## Decisions

- **登记表形态选 JSON（`scripts/version_pins.json`）而非 spec 内 Markdown 表**：
  闸门解析 JSON 稳定，解析 Markdown 脆弱；且 spec 表格 + 真实文件会变成第二个
  漂移对。代价是人读要开文件——用 `check:outdated` 顺带打印登记表摘要弥补。
  条目结构：`{name, category, pin_location, upgrade_method, paired_with[], notes?}`；
  类别枚举固定（toolchain/msrv/lang-matrix/pkg-manager/lockfile/github-tarball/
  cargo-subcommand/global-cli/ci-actions/browser-runtime/oracle-env）。
- **闸门"仓库内钉版点全覆盖"用白名单扫描实现**：完全自动发现钉版点不可靠，
  改为闸门内置一组机械检查（四个 `Cargo.toml` 的 `rust-version` 一致性、
  `rust-version` ≤ pin 的 major.minor、`packageManager` 精确版本、
  `.python-version` 与 `requires-python` 关系、登记表条目路径存在性），
  并规定新增钉版形态时同步扩展闸门检查项（登记原则的闸门侧）。
  备选"AST 全仓扫描"否决：过度设计，白名单已覆盖已知全部形态。
- **`check:outdated` 为纯标准库 Python 脚本**（`scripts/check_outdated.py`），
  与 `check_md.py` 等惯例一致；pnpm/cargo/uv 子命令以 subprocess 调用，
  全局 CLI 用 `--version` 探测 + 联网查最新 LTS/稳定版（endoflife.date API、
  npm registry、crates.io、GitHub releases API，带 `GITHUB_TOKEN` 时优先用）；
  CI actions 段解析 workflow 的 `uses:` 行（owner/repo@tag）查 GitHub releases
  最新 major tag。备选"bash 脚本"否决：四段输出结构化需求下 Python 更整齐。
- **全局 CLI 检查项进登记表但 `pin_location` 标注为 machine**：闸门对
  machine 类条目只校验"登记表有此项"，不校验本机版本（版本检查归
  `check:outdated`）——闸门保持离线，本机差异不阻塞他人。
- **ci-matrix 措辞去数字**：矩阵格语义（底线/最新、平台 ABI 格）是 CI 结构，
  留在 ci-matrix；数字进登记表。两 spec 以链接相连，升级只动登记表 + ci.yml。
- **workspace-layout「版本底线」整体 REMOVED 而非留摘要**：摘要=第二真相源；
  `packageManager`/`uv.lock` 存在性校验移交 `check_version_pins.py`，
  行为断言不丢失。
- **TS7 重测放本 change**：当前已是 TS7 最新稳定版 7.0.2（7.1 仅 beta/dev，
  按选线原则不采），重测=重跑 `build:shells` + `typecheck` + 全量测试确认
  tsdown dts × TS7 兼容仍成立；失败则钉 `typescript@6` + 记账本 + 登记
  `paired_with: tsdown`。

## Risks / Trade-offs

- [登记表与闸门检查项本身漂移] → 双向对账 + 登记原则把"扩展闸门"纳入引入
  新钉版形态的完成判据；archive 时 retro 三问兜底。
- [`check:outdated` 依赖外部 API 可用性] → 单段失败降级为警告并标注，不影响
  其余段输出；该命令不在 CI，失败不阻塞任何闸门。
- [Rust MSRV 1.99 抬升后消费者被迫升级] → MSRV 底线本就是"当前 stable"
  （既有契约），且 pin 已升 1.99.1，本任务只是补齐滞后。
- [ci-matrix 去数字后读者要跳转登记表] → 可接受：单源收益大于一次跳转成本。

## Migration Plan

1. 落地登记表 + 闸门 + 体检命令，`check:meta` 接入后先跑通（此时登记表
   如实记录现状，含 MSRV 滞后项——闸门一致性规则按"rust-version ≤ pin"
   设计，滞后不 FAIL，仅当互相矛盾才 FAIL）。
2. 同 change 内做 MSRV 收尾（四处 1.98→1.99）与 TS7 重测，闸门全绿。
3. 文档迁移（AGENTS.md、CONTRIBUTING.md 删节留指针；两 spec delta 随归档
   sync）。回滚策略：全部改动为配置/文档/脚本，git revert 即可。

## Open Questions

- 无。
