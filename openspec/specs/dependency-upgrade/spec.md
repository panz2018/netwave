# dependency-upgrade Specification

## Purpose

定义 netwave 工具链与依赖升级的策略、钉版事实的唯一真相源、规则驱动
一致性闸门、升级流程与经验回写契约，使任何一次升级都可按清单执行、
可门禁校验、踩坑后可改进。

## Requirements

### Requirement: 最新稳定版优先

全部工具链、工具与软件库 MUST 升级到最新稳定版；仅当最新稳定版导致
构建/测试失败且确认为上游 bug（非本项目用法问题）时，才允许回退，
回退按「坏版本降级与 blocked 触发式实施」执行（降到相邻较低稳定版 +
当轮立 `Plan/` 计划 + 强制开 change 实现黑名单机制）。lessons-learned
只记非版本性的坑（工具行为变化、流程坑等），版本级 bug 证据以该次
`Plan/` 计划文件与跟踪 issue 为准。子项目 README 不设 Gotchas 章节，
回退信息不入 README。

#### Scenario: 默认升最新稳定版

- **WHEN** 体检发现某依赖落后于最新稳定版
- **THEN** 升级目标为最新稳定版，且相关配置与文档同步更新到新版契约

#### Scenario: 回退须证据

- **WHEN** 最新稳定版构建失败且确认为上游 bug
- **THEN** 降到相邻较低稳定版，当轮在 `Plan/` 记录坏版本、原因与跟踪
  issue 链接，跟踪计划随 issue
- **AND** 回退原因不写入任何子项目 README

### Requirement: 选线原则——钉 LTS/稳定线

有多条发布线的运行时 MUST 钉 LTS 或稳定线，MUST NOT 采用 current 最新线
（current 线随时变更、配置来回变且用户基数小）；无 LTS 概念的单线运行时
（如 CPython）取最新稳定 minor 的最新补丁版。各运行时的当前选线取值
由承载它的钉版文件持有（CI 矩阵格、`.python-version`、`engines.node`），
本 spec 不写死数字。

#### Scenario: Node 钉 LTS 线

- **WHEN** 为 CI 矩阵与 `engines.node` 选择 Node 版本
- **THEN** 取底线 LTS 与最新 LTS 两格，不取非 LTS 的 current 线
- **AND** current 线转入 LTS 时只改 `ci.yml` 矩阵格与 `engines.node`，
  本 spec 措辞不随版本号变化

#### Scenario: 单线运行时取最新稳定 minor

- **WHEN** 运行时无 LTS 概念（CPython）
- **THEN** 取最新稳定 minor 的最新补丁版
- **AND** 新 minor 发布且本项目所需库全部支持后方切换，任一库不支持则维持现版并记账本

### Requirement: 钉版事实以钉版文件为唯一真相源

仓库不设版本钉死点清单文件。"某个版本钉在哪、当前钉的是哪个版本"的唯一
真相源是**承载该版本的仓库文件本身**（如 `rust-toolchain.toml`、
`.python-version`、`pyproject.toml`、`package.json`、`.github/workflows/ci.yml`、
各 lockfile）。散文文档与 spec MUST NOT 复制具体版本号，MUST 以文件路径指针
引用；一致性由规则驱动闸门校验，不依赖人工维护的登记表。

#### Scenario: 散文不复制版本号

- **WHEN** 任一散文文档（README、spec、账本）需要提及当前钉版值
- **THEN** 以文件路径指针或"当前稳定版"措辞引用，不写死数字

#### Scenario: 清单文件不得复活

- **WHEN** 改动新增一份"把所有钉版点列一遍"的清单文件
- **THEN** review Standards 轴打回——真相源是钉版文件本身，第二份清单必漂移

### Requirement: 规则驱动一致性闸门

`scripts/versions/check_versions.py` MUST 按结构性规则（四律）扫描仓库
manifest，MUST NOT 读取任何登记表。规则是**通用律**而非具体文件清单：
新增子工程自动纳入覆盖，无需登记任何条目。任一规则不满足即 FAIL 并点名
具体文件与期望值。闸门 MUST 接进根 `check:meta`。

#### Scenario: MSRV 律

- **WHEN** 闸门扫描 root `Cargo.toml` `members` 列出的 workspace 成员
- **THEN** 每个成员 MUST 携带 `rust-version`，全部值彼此相等且不高于
  `rust-toolchain.toml` channel 的 major.minor；channel MUST 是精确版本

#### Scenario: Python 工程律

- **WHEN** 闸门发现含 `[project]` 的 `pyproject.toml`
- **THEN** 该文件 MUST 声明 `requires-python`，且同目录 MUST 存在
  `.python-version`

#### Scenario: packageManager 律

- **WHEN** 闸门发现声明 `packageManager` 的 `package.json`
- **THEN** 值 MUST 是精确 pnpm 版本（拒绝范围与 `latest`），且全仓值
  彼此相等

#### Scenario: 矩阵覆盖律

- **WHEN** 闸门发现仓库内任一 `.python-version` 钉版
- **THEN** 其值 MUST 出现在 CI workflow 的 python 矩阵格中

#### Scenario: 手动升版漂移当场暴露

- **WHEN** `rust-toolchain.toml` 升到新 stable 而某 `Cargo.toml` 的
  `rust-version` 仍是旧值
- **THEN** 闸门 FAIL 并指出具体文件与期望值

#### Scenario: 新子工程漏声明当场暴露

- **WHEN** 新增一个含 `[project]` 的 `pyproject.toml` 而同目录无
  `.python-version`
- **THEN** `pnpm check:meta` FAIL 并点名该目录——无需事先登记

#### Scenario: 成员丢 MSRV 钉静默逃逸

- **WHEN** 某 workspace 成员的 `Cargo.toml` 删掉了 `rust-version` 字段
- **THEN** 闸门 FAIL 并指出该成员——删字段不能逃逸对账

#### Scenario: 换网自证（正反夹具）

- **WHEN** 以临时夹具运行闸门：一份缺 `rust-version` 的 `Cargo.toml`、
  一份缺 `.python-version` 的 `pyproject.toml` 目录
- **THEN** 两种夹具均 FAIL；未改动的真实仓库 PASS

### Requirement: 坏版本降级与 blocked 触发式实施

坏版本黑名单机制当前不实现（无数据文件、无闸门消费）。当升级确认某上游
版本带 bug（非本项目用法问题）时，MUST 按序执行：

1. 降到**相邻较低稳定版**——取该依赖当前版本之下第一个可用稳定版；
   级差（major/minor/patch）依该次故障实际影响范围判断，spec 不写死算法。
2. 当轮在 `Plan/` 新建计划文件，写明：碰到什么问题、哪个版本坏、
   坏在哪、临时降级取值、以及 blocked 机制的实施范围。
3. 强制开 OpenSpec change 实现 blocked 机制（数据文件 + 闸门与体检消费），
   该 change 完成前，降级只靠人工执行第 1 步。

`Plan/` 中的 blocked 计划与 pairs 计划是两个独立待触发项，MUST NOT 绑定
同一次 change 实施——两者语义无关，各自需要时各自实施。

#### Scenario: 遇坏版本即降级并立计划

- **WHEN** 升级确认最新稳定版因上游 bug 构建或测试失败
- **THEN** 降到相邻较低稳定版使闸门通过，同一轮在 `Plan/` 新建 blocked
  实施计划文件，写明原因与故障细节

#### Scenario: blocked 与 pairs 不绑定

- **WHEN** 实施 blocked 机制的 change 开出
- **THEN** pairs（必须同升）机制不因该 change 一并实施，反之亦然

#### Scenario: 机制未实现期不空转义务

- **WHEN** 仓库当前无 blocked 数据文件与消费代码
- **THEN** 闸门与体检不因缺黑名单而 FAIL，降级义务按本 Requirement 人工履行

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
文档同步（grep 全仓旧版本号与旧事实）。配对联动清单以本节散文为当前唯一载体；
其 JSON 化（数据文件 + 闸门读表、禁硬编码）为待触发项，见 `Plan/软件升级.md`。

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

### Requirement: 运行时大版本升级流程

运行时大版本升级（Python 稳定 minor 切换、Node LTS 线切换）MUST 按序：先核实
本项目所需全部库声明支持目标版本（支持矩阵记入 change）→ 本地新环境全量测试
变绿 → 一次改齐全部钉版点（运行时 pin、CI 矩阵格、必要时底线声明、oracle
环境）→ 代码兼容修改 → 全闸门 + 四端对拍。Node 换线另须以
`--reinstall-packages-from` 迁移全局 npm 包。

#### Scenario: Python 稳定 minor 切换

- **WHEN** Python 升到新稳定 minor
- **THEN** 同一 change 内改 `python/.python-version`、根 `.python-version`、
  CI python 矩阵最新格、oracle 环境 lock；本地以新 minor 全量测试绿后才动 CI

#### Scenario: Node LTS 线切换

- **WHEN** CI 矩阵的最新 LTS 格需切到新线
- **THEN** 更新 CI 矩阵与 `engines.node`，并以 `--reinstall-packages-from`
  迁移全局 npm 包；`engines.node` 底线仅当旧底线 EOL 才抬

### Requirement: 体检按发现覆盖全部环境

体检 MUST 按发现（非硬编码名单）覆盖仓库全部依赖环境：每个 uv 工程
（`uv.lock`）、每个运行时 pin（`.python-version`）、pnpm workspace（`-r`）、
cargo workspace。新环境落地后自动纳入，无需改脚本。

#### Scenario: oracle 环境自动覆盖

- **WHEN** `oracle/golden/uv.lock` 存在
- **THEN** 体检自动对其执行 dry-run 升级检查；其 `.python-version`（若有）
  自动与最新稳定 minor 比对

### Requirement: 过期体检命令

仓库 MUST 提供聚合体检命令 `pnpm check:outdated`，覆盖四段：项目依赖
（`pnpm outdated`、`cargo update --dry-run`、`uv lock --upgrade --dry-run`）、
全局 CLI（当前版本 vs 最新 LTS/稳定版）、GitHub 压缩包直装工具与 cargo
子命令（已装版本 vs 最新 release）、CI actions（workflow 内 `uses:` 的
action 当前 tag vs 最新 release tag）。体检按发现覆盖环境（见「体检按发现
覆盖全部环境」），全局 CLI 与直装工具的探针集为体检程序内常量（新增探针
改一处）。坏版本黑名单机制当前不实现，体检按最新稳定版报告 target；机制
落地后由体检消费黑名单（见「坏版本降级与 blocked 触发式实施」）。该命令
人工触发，MUST NOT 进 CI 或 `pnpm check`（结果随上游每日变化且需联网）。

#### Scenario: 一条命令看全貌

- **WHEN** 运行 `pnpm check:outdated`
- **THEN** 输出四段各自的当前版本、最新 LTS/稳定版与是否落后
- **AND** `ci.yml` 与 `pnpm check` 均不包含该命令

#### Scenario: CI actions 落后即报

- **WHEN** workflow 中某 action 钉的 major tag 落后于该 action 的最新 major
  release
- **THEN** 体检输出该 action 的当前 tag 与最新 tag，标记落后

### Requirement: 经验回写

升级过程中踩的坑 MUST 当轮回写并按性质归位：版本级 bug（哪个版本坏、
为什么）按「坏版本降级与 blocked 触发式实施」处理——当轮在 `Plan/` 新建
计划文件记录版本、原因与跟踪链接；非版本性的坑（工具行为变化、配对失败
模式等）记 lessons-learned 账本（scope 分片 + INDEX 条目）。钉版点漏声明
由规则驱动闸门当场拦截，当轮补声明即可，无人工登记环节。本 spec 随该
循环持续改进。

#### Scenario: 版本级 bug 归登记表

- **WHEN** 升级确认某上游版本带 bug 需回退
- **THEN** 当轮在 `Plan/` 新建 blocked 实施计划文件记录版本与原因及跟踪
  issue，lessons-learned 只记其中非版本性的教训（如升级流程坑），
  不重复版本清单

#### Scenario: 漏登记当轮补全

- **WHEN** 升级过程发现某钉版点缺声明（如新子工程缺 `.python-version`）
- **THEN** 同一 change 内补全该点声明并登记对应 LL 条目——规则闸门
  当场拦截，无人工登记环节

#### Scenario: 非版本性坑归账本

- **WHEN** 升级踩到工具行为变化或配对失败模式
- **THEN** 当轮登记 LL 条目（分片 + INDEX），不写入 spec 或 README
