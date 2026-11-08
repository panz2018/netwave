# Spec Delta: dependency-upgrade

## ADDED Requirements

### Requirement: 升级执行权限划分

升级分两类：**上限升级**（lockfile 依赖刷新含 major、工具链与运行时
pin 切换、CI 矩阵最新格、直装工具、全局 CLI、CI actions）MUST 由
agent 直接执行，MUST NOT 要求开 OpenSpec change；验收按触及面选闸门
（见「按触及面选验收闸门」），实测失败按「版本限制记录与坏版本降级」
回退并当轮登记。**下限变更**（MSRV `rust-version`、`engines.node`、
CI 底线矩阵格、新增/移除钉版点）由人工发起，agent MUST NOT 自动执行。
有自动生效仓库 pin 者以 pin 为准升级，其余在本机执行、回退靠重装
（机制见各 scenario）。追溯靠 git log，坏版本事实靠
`scripts/versions/restrictions.json`（仓库内组合）与账本（机器级工具）。

#### Scenario: 上限升级直接执行不开 change

- **WHEN** 体检报出任一上限 LAG（lockfile、pin、矩阵最新格、工具）
- **THEN** agent 直接执行升级 + 全闸门 + 四端对拍，不开 OpenSpec change，
  提交信息注明升级内容与体检出处

#### Scenario: 无仓库 pin 的全局 CLI 与直装工具机器级升级

- **WHEN** 体检报出无仓库 pin 的全局 CLI 或 GitHub 压缩包直装工具落后
  （npm、openspec、uv、rustup、wasm-pack、binaryen、cargo-llvm-cov 等）
- **THEN** agent 在本机直接升级到最新（`npm install -g` / `cargo install`
  / 重下 tarball），不停下等点名；实测坏则重装回退到上一可用版并当轮
  记账本

#### Scenario: node 升级保打开即用

- **WHEN** 体检报出 node 落后（node 无自动生效的仓库 pin，当前版本以
  机器 `node --version` 为准）
- **THEN** agent 执行 `nvm install <最新> --reinstall-packages-from=<旧版>`
  并 `nvm alias default <最新>`，使新终端打开即用最新版且全局 npm 包
  （openspec、markdownlint-cli2 等）随版本迁移不丢失；仅 install 不
  alias、或不带 `--reinstall-packages-from` 均不算升级完成

#### Scenario: 自动生效 pin 的 CLI 以 pin 为准

- **WHEN** 体检报出的 CLI 在仓库有自动生效的 pin（pnpm
  `packageManager` 由 corepack 读、rustc `rust-toolchain.toml` 由 rustup
  读）
- **THEN** 其当前版本以仓库 pin 为准（非机器全局安装版），升级 =
  改仓库 pin 文件（进 git、跨机器一致）而非重装全局；机器 active
  版本与 pin 不一致时向 pin 对齐

#### Scenario: 按触及面选验收闸门

- **WHEN** 升级一项依赖/工具后确定验收范围
- **THEN** 触及四端绑定或数值路径者跑 `pnpm check` + `pnpm check:cross`
  四端对拍；纯 lint/文档/CLI 工具（不碰绑定与数值）只跑 `pnpm check`，
  不跑 `check:cross`

#### Scenario: 下限变更人工发起

- **WHEN** MSRV、`engines.node` 或 CI 底线矩阵格需要抬升（如旧底线 EOL）
- **THEN** 由人工点名发起，agent 不自动执行；发起后的执行仍按本 spec
  升级流程验收

### Requirement: apply 末尾体检与升级预授权

每次 OpenSpec apply 全部任务完成后，最后一项 MUST 是跑 `pnpm check:outdated`
并消化所报 LAG（双写接线 = `openspec/config.yaml` 的
`operations.apply.guidance` + `rules.tasks`）。体检报出的**一切 LAG** MUST
预授权：agent 无需再次确认，直接执行升级 + 全闸门 + 四端对拍，按
「升级执行权限划分」与「版本限制记录与坏版本降级」走完流程，不阻塞、
不等点名；多条 LAG 逐条（或按生态分组）升级并各带一次闸门，使红可定位
到具体版本；先升仓库内项再升全局 CLI。仅本需求场景所列情况（设计级
适配、契约文件破损）MUST 停下报告。下限变更不在预授权范围，MUST 等
人工发起。消化完成 MUST 以 `pnpm check:outdated` 复跑归零为准
（见「消化闸门复验」）。提交权不变：仓库内升级改动在提交全景表单列一组。

#### Scenario: apply 末尾体检

- **WHEN** 任一 change 的全部任务完成
- **THEN** 最后一项跑 `pnpm check:outdated`，所报 LAG 按预授权流程消化
  （升级完成或登记回退），不影响本 change 已完成的工作
- **AND** 消化后复跑 `pnpm check:outdated`，退出码非 0（仍有残留
  LAG）即本项未完成，继续消化或登记直至归零

#### Scenario: LAG 直接执行

- **WHEN** 体检报出任一 LAG（含工具链 pin、CI 矩阵最新格、运行时 minor
  切换、lockfile major）
- **THEN** agent 直接执行升级并跑全闸门 + 四端对拍，绿后汇报，红则回退
  并当轮登记，不再询问、不阻塞

#### Scenario: 设计级适配等点名

- **WHEN** 升级引起的代码适配触及公开 API 或需要设计决策
- **THEN** agent 停下报告，可先降级到可用版保绿，不自主改公开 API

#### Scenario: 契约文件破损中止

- **WHEN** 体检发现 `restrictions.json` 破损（抛契约异常）
- **THEN** 中止升级步骤并报告先修，不得基于失真判定基准执行升级

#### Scenario: 下限等点名

- **WHEN** 升级涉及 MSRV、`engines.node` 或 CI 底线矩阵格
- **THEN** agent 只报告不动手，等人工点名

#### Scenario: 无可用版本即保留现状继续

- **WHEN** 某包从最新往下每个版本都命中已登记组合（无 free version）
- **THEN** 保留当前可用版本、报 `no free version`，继续处理其余 LAG，
  不阻塞、不停下等确认

#### Scenario: 先仓库后全局的升级顺序

- **WHEN** 一次体检同时报出仓库内 LAG 与全局 CLI LAG
- **THEN** 先在当前稳定工具链上升级仓库内项（lockfile、pin、CI action）
  并跑全闸门验绿，再逐个升级全局 CLI，每升一个重跑全闸门复验；
  某工具弄红即重装回退该工具，仓库改动不受牵连

#### Scenario: 无闸门覆盖的全局 CLI 冒烟验收

- **WHEN** 升级的全局 CLI 不被 `pnpm check` 实际执行（如 openspec）
- **THEN** 以冒烟测试验收：命令能跑、`--version` 报出版本、核心子命令
  正常执行；不为其另造 CI 闸门

## MODIFIED Requirements

### Requirement: 过期体检命令

仓库 MUST 提供聚合体检命令 `pnpm check:outdated`，覆盖四段：项目依赖
（`pnpm outdated`、`cargo update --dry-run`、`uv lock --upgrade --dry-run`）、
全局 CLI（当前版本 vs 最新 LTS/稳定版）、GitHub 压缩包直装工具与 cargo
子命令（已装版本 vs 最新 release）、CI actions（workflow 内 `uses:` 的
action 当前 tag vs 最新 release tag）。体检按发现覆盖环境（见「体检按发现
覆盖全部环境」），全局 CLI 与直装工具的探针集为体检程序内常量（新增探针
改一处）。**每一段**报出 latest/target 前 MUST 消费版本限制记录判定
（见「版本限制记录数据文件」），MUST NOT 有绕过过滤的段；运行时/工具 pin
以生态前缀名参与组合判定。该命令由 apply 末尾自动触发（见「apply 末尾
体检与升级预授权」），MUST NOT 进 CI 或 `pnpm check`（结果随上游每日
变化且需联网）。体检 MUST NOT 报下限声明（`rust-version`、`engines.node`、CI
底线矩阵格）为 LAG——下限不在升级目标内，变更由人工发起。报告末尾 MUST
打印 SUMMARY 行汇总各段 LAG 计数（见「报告末尾总览 LAG 计数」）；本命令
本身即闸门，残留 LAG 即非零退出（见「消化闸门复验」）。不可达源（重试一次仍失败）
MUST 报 SKIP，MUST NOT 计入 FAILED、
MUST NOT 影响退出码；FAILED 仅保留给不依赖网络运气的真错误（本地探针
命令无法执行、契约文件破损等），任一 FAILED MUST 以非零退出码结束。

#### Scenario: 一条命令看全貌

- **WHEN** 运行 `pnpm check:outdated`
- **THEN** 输出四段各自的当前版本、最新 LTS/稳定版与是否落后
- **AND** `ci.yml` 与 `pnpm check` 均不包含该命令

#### Scenario: 报告末尾总览 LAG 计数

- **WHEN** 体检跑完四段
- **THEN** 末尾打印一行 `SUMMARY: <N> LAG (<分段计数>)`，N 为各段落后项总数
  （pnpm 表数据行、cargo `Updating … -> …` 行、uv 变更行、运行时 pin、
  全局 CLI、直装工具、CI actions 各按 LAG 标记计数）
- **AND** 无落后时打印 `SUMMARY: 0 LAG (all current)`，使截断视图也能一眼
  看出是否整段被漏看

#### Scenario: 消化闸门复验

- **WHEN** 运行 `pnpm check:outdated`（含 apply 末尾消化 LAG 后的复跑）
- **THEN** SUMMARY 仍有残留 LAG 即以非零退出码结束，强制"消化完成 = 归零"；
  SUMMARY 为 0 时退出码 0
- **AND** SKIP（源不可达）不计入 LAG，断网时退出码仍为 0（见「断网不算失败」）

#### Scenario: CI actions 落后即报

- **WHEN** workflow 中某 action 钉的 major tag 落后于该 action 的最新 major
  release
- **THEN** 体检输出该 action 的当前 tag 与最新 tag，标记落后

#### Scenario: target 命中已登记坏组合即换版本

- **WHEN** 任一段（包管理器 dry-run、运行时 pin、全局 CLI、直装工具、
  CI actions）报出的最新版与对端当前版本凑成已登记组合
- **THEN** 该行不推荐最新稳定版，改推荐"与对端搭配后未登记的最高可用版本"
  （可能低于最新稳定版，也可能最新稳定版本身未命中即照报），并注明该组合的
  登记原因
- **AND** 只调整本行这一个包的 target，对端行不受影响

#### Scenario: 运行时 pin 参与组合判定

- **WHEN** 运行时 pin 的当前值与某库当前锁定版本凑成已登记组合
- **THEN** 运行时行不报向该新版的 LAG，改报未登记的最高可用 target 并
  注明 SKIP 原因；对端升到组合外版本后精确匹配不再命中，LAG 自然回归

#### Scenario: 出错不得静默

- **WHEN** 体检某源重试一次后仍不可达（registry / API 不可达、限流）
- **THEN** 该源各行报 SKIP 并点名源名，其余源照常跑完，退出码不受该源
  影响；本地探针无法执行或契约文件破损等真错误仍计入 FAILED 并以非零
  退出码结束
- **AND** 命令不存在"无论结果如何退出码恒为 0"的行为，也不得把 FAILED
  降级为 SKIP

#### Scenario: 断网不算失败

- **WHEN** 全部网络源不可达（如整机断网）
- **THEN** 全部相关行报 SKIP，退出码为 0

### Requirement: 版本限制记录数据文件

仓库 MUST 以 `scripts/versions/restrictions.json` 作为坏版本事实的唯一载体。
一条记录 MUST 由一句 `reason` 与该原因下所有实测失败的版本组合清单构成；
每个组合 MUST 由 1~N 个包名各自对应一个**具体版本号**构成（N 不限：N=1 表示
该包自身 bug，N≥2 表示联动 bug）。包名 MUST 带生态前缀（`npm:` / `cargo:` /
`pypi:`）以区分跨生态同名包。版本号 MUST 是实测过的具体版本，MUST NOT 写版本
范围，MUST NOT 登记未经实测的版本或组合。运行时/工具 pin 参与组合时以生态
前缀名登记（如 `pypi:python`、`cargo:rustc`），版本值取该 pin 自身粒度
（如 CPython 的 minor）。记录 MUST NOT 含"修复于哪个版本"、可用状态或重试
标记——未登记的版本与组合一律视为可试。记录 MUST 只增不删。

#### Scenario: 单包 bug 与多包联动同构

- **WHEN** 登记一个包自身带 bug 的版本，或登记两个及以上包凑在一起才坏的版本组合
- **THEN** 两者写成同一种记录（`reason` + 组合清单），仅组合内包数不同

#### Scenario: 运行时不兼容登记为全参与方组合

- **WHEN** 实测确认某运行时版本与某库版本不兼容
- **THEN** 登记组合把全部参与方写全（如 `pypi:python` 与 `pypi:numpy`
  各带实测版本号），MUST NOT 只登记运行时一条
- **AND** 对端升到组合外的版本后精确匹配不再命中，无需清理记录

#### Scenario: 未实测的交叉组合不算坏

- **WHEN** 同一原因下登记了 `A 1.0 × B 2.0` 与 `A 1.1 × B 2.1`，当前锁定
  `A 1.0 × B 2.1`
- **THEN** 判定为未登记（放行去试），不得把组合清单按交叉相乘理解

#### Scenario: 记录只增不删

- **WHEN** 某已登记组合在新版本下已不复现
- **THEN** 该记录仍保留不删——日后因其他问题回退进同一区间时，记录继续
  避免重复试验；历史追溯靠 git log

#### Scenario: 包名必须带生态前缀

- **WHEN** 记录的包名缺少 `npm:` / `cargo:` / `pypi:` 前缀
- **THEN** 读记录时视为格式错误并抛异常，不得静默当作某个生态处理

#### Scenario: 全局工具坏版本记账本不入本文件

- **WHEN** 全局 CLI 或直装工具（node、openspec、wasm-pack 等，不在本仓
  lockfile/pin 内）某版本实测坏
- **THEN** 该坏版本事实记 lessons-learned 账本，MUST NOT 写进
  `restrictions.json`——本文件只承载仓库内 lockfile/pin 能凑成的组合，
  机器级工具版本不由体检 peers 追踪，写入也永不命中

### Requirement: 运行时大版本升级流程

运行时大版本升级（Python 稳定 minor 切换、Node LTS 线切换）MUST 按实测
流程：直接切到目标版本 → 同一轮一次改齐全部钉版点（运行时 pin、CI 矩阵
最新格、oracle 环境；MUST NOT 留半切状态）→ 全闸门 + 四端对拍 → 绿即
完成，红则按「版本限制记录与坏版本降级」登记失败组合并回退。MUST NOT
预先调研库支持矩阵——兼容性只认实测结果，不认声明。Node 换线另须以
`--reinstall-packages-from` 迁移全局 npm 包。下限声明（`engines.node`、
MSRV）不在本流程范围，由人工发起抬升。

#### Scenario: Python 稳定 minor 切换

- **WHEN** Python 最新稳定 minor 前进一格
- **THEN** agent 同轮改 `python/.python-version`、根 `.python-version`、
  CI python 矩阵最新格、oracle 环境 lock，跑全闸门 + 四端对拍；实测失败
  则登记组合并回退，不预先调研支持矩阵

#### Scenario: Node LTS 线切换

- **WHEN** 最新 LTS 前进到新线
- **THEN** 更新 CI 矩阵最新格，并以 `--reinstall-packages-from` 迁移全局
  npm 包；MUST NOT 抬 `engines.node` 底线——底线仅当旧底线 EOL 时由
  人工发起抬升

## REMOVED Requirements

### Requirement: 升级分级

**Reason**: 旧分级要求一切结构性升级（工具链 pin、语言矩阵格、选线）
MUST 开 OpenSpec change，但此类升级没有可留痕的设计决策——兼容性由全
闸门 + 四端对拍验证，不兼容由 `restrictions.json` 登记回退，change 仪式
只带来摩擦不带来信息。

**Migration**: 由新需求「升级执行权限划分」替代：体检所报上限升级由
agent 直接执行；下限变更由人工发起。
