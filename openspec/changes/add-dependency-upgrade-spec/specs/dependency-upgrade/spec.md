# Spec Delta

## Purpose

定义 netwave 工具链与依赖升级的策略、版本钉死点的唯一真相源、对账闸门、
升级流程与经验回写契约，使任何一次升级都可按清单执行、可门禁校验、
踩坑后可改进。

## ADDED Requirements

### Requirement: 最新稳定版优先

全部工具链、工具与软件库 MUST 升级到最新稳定版；仅当最新稳定版导致
构建/测试失败且确认为上游 bug（非本项目用法问题）时，才允许回退次新版，
回退 MUST 在 lessons-learned 账本登记上游 issue 链接、复现证据与跟踪计划。
子项目 README 不设 Gotchas 章节，回退信息只存账本。

#### Scenario: 默认升最新稳定版

- **WHEN** 体检发现某依赖落后于最新稳定版
- **THEN** 升级目标为最新稳定版，且相关配置与文档同步更新到新版契约

#### Scenario: 回退须证据

- **WHEN** 最新稳定版构建失败且确认为上游 bug
- **THEN** 回退次新版并在 lessons-learned 账本登记 issue 链接、复现证据与跟踪计划
- **AND** 回退原因不写入任何子项目 README

### Requirement: 选线原则——钉 LTS/稳定线

有多条发布线的运行时 MUST 钉 LTS 或稳定线，MUST NOT 采用 current 最新线
（current 线随时变更、配置来回变且用户基数小）；无 LTS 概念的单线运行时
（如 CPython）取最新稳定 minor 的最新补丁版。各运行时的当前选线取值
由钉死点登记表持有，不写死在本文。

#### Scenario: Node 钉 LTS 线

- **WHEN** 为 CI 矩阵与 `engines.node` 选择 Node 版本
- **THEN** 取底线 LTS 与最新 LTS 两格，不取非 LTS 的 current 线
- **AND** current 线转入 LTS 时更新登记表的状态标注，矩阵数字不变

#### Scenario: 单线运行时取最新稳定 minor

- **WHEN** 运行时无 LTS 概念（CPython）
- **THEN** 取最新稳定 minor 的最新补丁版
- **AND** 新 minor 发布且本项目所需库全部支持后方切换，任一库不支持则维持现版并记账本

### Requirement: 登记原则

引入新工具链、工具或软件库时，同一笔改动 MUST 在钉死点登记表登记：钉在哪、
怎么升级、与谁配对联动。未登记即引入未完成。

#### Scenario: 引入新工具未登记即失败

- **WHEN** 某改动新增了钉版点（清单文件版本字段、安装脚本或全局工具依赖）
  但未更新登记表
- **THEN** 对账闸门报 FAIL，指出该钉版点未登记

### Requirement: 钉死点登记表唯一真相源

仓库全部版本钉死点 MUST 登记在机器可读登记表 `scripts/version_pins.json`，
它是"版本钉在哪"的唯一真相源；散文文档 MUST NOT 复制登记表内容。
类别覆盖：Rust 工具链 pin 与 MSRV、CI 语言矩阵数字、包管理器 pin、
lockfile、GitHub 压缩包直装工具（wasm-pack、binaryen）、cargo 子命令、
全局 CLI 检查项、CI actions、Playwright 浏览器、oracle 环境 pin。

#### Scenario: 登记条目结构完整

- **WHEN** 校验登记表任一条目
- **THEN** 条目含：名称、类别、钉版位置（文件路径或安装位置）、升级方法、
  配对约束（若有）
- **AND** 散文文档以链接或"当前稳定版"措辞引用，不复制具体版本号

### Requirement: 双向对账闸门

`scripts/check_version_pins.py` MUST 双向对账登记表与真实文件：每个登记条目
对应真实存在的钉版位置；仓库内每个钉版点都出现在登记表中；一致性规则
（如四处 `rust-version` 彼此一致、`rust-version` 不高于 `rust-toolchain.toml`
pin 的 major.minor、`packageManager` 为精确版本）任一不满足即 FAIL。
闸门 MUST 接进根 `check:meta`。

#### Scenario: 手动升版漂移当场暴露

- **WHEN** `rust-toolchain.toml` 升到新 stable 而某 `Cargo.toml` 的
  `rust-version` 仍是旧值
- **THEN** 闸门 FAIL 并指出具体文件与期望值

#### Scenario: 登记表条目指向不存在的位置

- **WHEN** 登记条目所指钉版位置在仓库或环境中不存在
- **THEN** 闸门 FAIL，报登记表漂移

### Requirement: 升级分级

升级分两档：**结构性升级**（工具链 pin、MSRV、语言矩阵格、新增/移除钉版点、
回退次新版、选线变更）MUST 走 OpenSpec change；**例行刷新**（lockfile 内
依赖 minor/patch 刷新）可走普通 PR，闸门全绿即可合并。两档验收均按
本 spec 的升级流程执行。

#### Scenario: 动 pin 走 change

- **WHEN** 升级目标是 `rust-toolchain.toml` channel、语言矩阵格或选线
- **THEN** 开 OpenSpec change，工件齐备且闸门全绿后合并

#### Scenario: 例行刷新走普通 PR

- **WHEN** 仅 `pnpm-lock.yaml` / `python/uv.lock` 内依赖 minor/patch 刷新
- **THEN** 普通 PR 通过 `pnpm check` 全绿 + `pnpm check:cross` 四端对拍即可合并

### Requirement: 升级流程固定顺序

每次升级 MUST 按序执行：全局 CLI 体检（nvm、rustup、node、npm/pnpm、uv、
OpenSpec、markdownlint-cli2 等是否落后 LTS/稳定线，落后先升）→ 工具链升级与
组件/target 补装 → 配对依赖联动（napi-cli↔napi crate、pyo3↔numpy、
wasm-pack↔binaryen 等）→ 项目依赖刷新 → 代码兼容修改 → 全闸门 + 四端对拍 →
文档同步（grep 全仓旧版本号与旧事实）。

#### Scenario: 工具链升版后补装

- **WHEN** `rust-toolchain.toml` 升到新 pin
- **THEN** 向新激活工具链补装 rustfmt/clippy 组件与 wasm32-unknown-unknown
  target，并以 `cargo install --locked` 重装 cargo 子命令（rustup 不更新它们）

#### Scenario: GitHub 直装工具落后即重跑安装脚本

- **WHEN** 体检发现已装 wasm-pack / binaryen 落后于其 GitHub 最新 release
- **THEN** 重跑对应 `scripts/install_*.sh` 升级到最新 release

#### Scenario: 升级完成判据

- **WHEN** 任一工具链或依赖升级执行完毕
- **THEN** `pnpm check` 全绿且 `pnpm check:cross` 四端对拍通过方视为完成

### Requirement: 过期体检命令

仓库 MUST 提供聚合体检命令 `pnpm check:outdated`，覆盖三段：项目依赖
（`pnpm outdated`、`cargo update --dry-run`、`uv lock --upgrade --dry-run`）、
全局 CLI（当前版本 vs 最新 LTS/稳定版）、GitHub 压缩包直装工具与 cargo
子命令（已装版本 vs 最新 release）。该命令人工触发，MUST NOT 进 CI 或
`pnpm check`（结果随上游每日变化且需联网）。

#### Scenario: 一条命令看全貌

- **WHEN** 运行 `pnpm check:outdated`
- **THEN** 输出三段各自的当前版本、最新 LTS/稳定版与是否落后
- **AND** `ci.yml` 与 `pnpm check` 均不包含该命令

### Requirement: 经验回写

升级过程中踩的坑（工具行为变化、配对失败、上游 bug、登记表漏钉版点）
MUST 当轮回写：坑记 lessons-learned 账本（scope 分片 + INDEX 条目）；
登记表漏项当轮补全。本 spec 随该循环持续改进。

#### Scenario: 漏登记当轮补全

- **WHEN** 升级过程发现某钉版点不在登记表中
- **THEN** 同一 change 内补全登记表并登记对应 LL 条目
