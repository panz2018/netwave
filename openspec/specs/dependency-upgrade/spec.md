# dependency-upgrade Specification

## Purpose

定义 netwave 工具链与依赖升级的策略、钉版事实的唯一真相源、规则驱动
一致性闸门、升级流程与经验回写契约，使任何一次升级都可按清单执行、
可门禁校验、踩坑后可改进。

## Requirements

### Requirement: 最新稳定版优先

全部工具链、工具与软件库 MUST 升级到最新稳定版；仅当最新稳定版导致
构建/测试失败且确认为上游 bug（非本项目用法问题）时，才允许回退，回退按
「版本限制记录与坏版本降级」执行（降到未登记的最高可用版本 + 当轮登记记录 +
同轮收紧承载钉版文件的版本要求）。lessons-learned 只记非版本性的坑（工具行为
变化、流程坑等），版本级坏版本事实以 `scripts/versions/restrictions.json` 与
当轮实测为准。子项目 README 不设 Gotchas 章节，回退信息不入 README。

#### Scenario: 默认升最新稳定版

- **WHEN** 体检发现某依赖落后于最新稳定版
- **THEN** 升级目标为最新稳定版，且相关配置与文档同步更新到新版契约

#### Scenario: 回退须证据

- **WHEN** 最新稳定版构建或测试失败且确认为上游 bug
- **THEN** 降到未登记的最高可用版本使构建通过，同一轮把该失败组合登记进
  `scripts/versions/restrictions.json`
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

### Requirement: 版本限制记录数据文件

仓库 MUST 以 `scripts/versions/restrictions.json` 作为坏版本事实的唯一载体。
一条记录 MUST 由一句 `reason` 与该原因下所有实测失败的版本组合清单构成；
每个组合 MUST 由 1~N 个包名各自对应一个**具体版本号**构成（N 不限：N=1 表示
该包自身 bug，N≥2 表示联动 bug）。包名 MUST 带生态前缀（`npm:` / `cargo:` /
`pypi:`）以区分跨生态同名包。版本号 MUST 是实测过的具体版本，MUST NOT 写版本
范围，MUST NOT 登记未经实测的版本或组合。记录 MUST NOT 含"修复于哪个版本"、
可用状态或重试标记——未登记的版本与组合一律视为可试。记录 MUST 只增不删。

#### Scenario: 单包 bug 与多包联动同构

- **WHEN** 登记一个包自身带 bug 的版本，或登记两个及以上包凑在一起才坏的版本组合
- **THEN** 两者写成同一种记录（`reason` + 组合清单），仅组合内包数不同

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

### Requirement: 版本限制记录与坏版本降级

升级或实测确认某版本/组合因上游 bug 不可用时，MUST 按序执行：降到未登记的
最高可用版本（方向不限，可能是相邻较低稳定版，也可能最新稳定版本身未登记）；
同一轮把失败组合登记进 `scripts/versions/restrictions.json`；同一轮收紧承载该
依赖的钉版文件（`package.json` / `Cargo.toml` / `pyproject.toml`）中声明的版本
要求，使其不再覆盖已登记版本，并刷新对应 lockfile 使锁定版本落在新范围内。
收紧 MUST 沿用原有范围写法只抬高下界，MUST NOT 新增或删除上界。该记录 MUST NOT
接进 `pnpm check`、`pnpm check:meta` 或 CI 闸门——正确性由下游构建与测试保证。

#### Scenario: 收紧范围只抬下界

- **WHEN** 已登记 `npm:tsdown` 的 `0.23.0`，承载文件写的是 `^0.23.0`
  （本 Scenario 数值为示例，实际取值以承载钉版文件与实测为准）
- **THEN** 改为 `^0.23.2`（抬高下界），MUST NOT 写成 `>=0.23.2`
  （那会新增未实测的放行面），也 MUST NOT 钉死为单一版本

#### Scenario: 无更高版本可抬时降线

- **WHEN** 已登记版本就是该包最新稳定版，抬高下界会排除全部可用版本
- **THEN** 降到上一稳定线（如 `^7` → `^6`），caret 自带的同 major 上界属既有
  写法惯例，不视为新增未实测限制

#### Scenario: 记录不进闸门

- **WHEN** 某包当前锁定版本命中已登记组合
- **THEN** `pnpm check` 与 CI 不因该记录 FAIL；问题由下游构建/测试暴露

#### Scenario: 漏改范围由下游暴露

- **WHEN** 登记记录后忘记收紧某钉版文件的版本要求
- **THEN** 不设专门机器校验；lockfile 刷新解析到坏版本时构建或测试失败即暴露

### Requirement: 限制记录读取的错误语义

读取 `scripts/versions/restrictions.json` MUST 区分三种情况：文件不存在 =
无记录，正常继续；文件存在但内容不合契约（非法 JSON、缺 `reason`、缺组合清单、
包名缺生态前缀、版本号非具体版本）= MUST 抛出异常中断，MUST NOT 静默跳过或
降级为警告；记录引用的包在当前仓库中已不存在 = 跳过该条判定、记录原样保留
（该依赖将来被加回时约束重新生效）。

#### Scenario: 文件缺失等于无约束

- **WHEN** `scripts/versions/restrictions.json` 不存在
- **THEN** 体检照常完成四段报告，不因缺文件报错

#### Scenario: 格式错误当场抛异常

- **WHEN** 记录文件非法 JSON 或缺必填字段
- **THEN** 读取处抛出异常、traceback 可见、脚本中断，不得继续输出"看起来正常"
  的体检结果

#### Scenario: 包已不在仓库则跳过并保留记录

- **WHEN** 记录引用的包在仓库所有 manifest/lockfile 中都找不到
- **THEN** 跳过该条判定，不报错也不删除记录

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
组件/target 补装 → 项目依赖刷新（刷新时按「版本限制记录」跳过已登记版本）→
代码兼容修改 → 全闸门 + 四端对拍 → 文档同步（grep 全仓旧版本号与旧事实）。
配对联动 MUST NOT 以本 spec 散文为凭：依赖间版本关系只认两类依据——上游官方
声明（由包管理器/编译器自身强制，本仓不重复登记）与本仓实测记录
（`scripts/versions/restrictions.json`）。

#### Scenario: 工具链升版后补装

- **WHEN** `rust-toolchain.toml` 升到新 pin
- **THEN** 向新激活工具链补装 rustfmt/clippy 组件与 wasm32-unknown-unknown
  target，并以 `cargo install --locked` 重装 cargo 子命令（rustup 不更新它们）

#### Scenario: GitHub 直装工具落后即重跑安装脚本

- **WHEN** 体检发现已装 wasm-pack / binaryen 落后于其 GitHub 最新 release
- **THEN** 重跑对应 `scripts/install_*.sh` 升级到最新 release

#### Scenario: 无依据的配对规矩不得作为升级约束

- **WHEN** 升级规划需要判断两个依赖是否必须同升
- **THEN** 只认上游官方文档声明或本仓实测记录；两者皆无则视为无约束，
  按各自最新稳定版处理
- **AND** 若事后实测发现不兼容，按「版本限制记录」登记，而非回头补写散文规矩

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
改一处）。体检给出的升级 target MUST 消费版本限制记录（见「版本限制记录
数据文件」）。该命令人工触发，MUST NOT 进 CI 或 `pnpm check`（结果随上游
每日变化且需联网）。体检 MUST NOT 隐藏错误：任何失败段 MUST 报告并以非零
退出码结束，MUST NOT 降级为警告后仍返回成功。

#### Scenario: 一条命令看全貌

- **WHEN** 运行 `pnpm check:outdated`
- **THEN** 输出四段各自的当前版本、最新 LTS/稳定版与是否落后
- **AND** `ci.yml` 与 `pnpm check` 均不包含该命令

#### Scenario: CI actions 落后即报

- **WHEN** workflow 中某 action 钉的 major tag 落后于该 action 的最新 major
  release
- **THEN** 体检输出该 action 的当前 tag 与最新 tag，标记落后

#### Scenario: target 命中已登记坏组合即换版本

- **WHEN** 某包的最新稳定版与对端当前锁定版本凑成已登记组合
- **THEN** 该行不推荐最新稳定版，改推荐"与对端搭配后未登记的最高可用版本"
  （可能低于最新稳定版，也可能最新稳定版本身未命中即照报），并注明该组合的
  登记原因
- **AND** 只调整本行这一个包的 target，对端行不受影响

#### Scenario: 出错不得静默

- **WHEN** 体检某段联网失败（registry / API 不可达、限流）
- **THEN** 该段报告失败原因，其余段照常跑完，命令以非零退出码结束
- **AND** 命令不存在"无论结果如何退出码恒为 0"的行为

### Requirement: 经验回写

升级过程中踩的坑 MUST 当轮回写并按性质归位：版本级坏版本（哪个版本、哪个组合
不可用）按「版本限制记录与坏版本降级」登记进 `scripts/versions/restrictions.json`
（含具体版本与一句原因）；非版本性的坑（工具行为变化、配对失败模式等）记
lessons-learned 账本（scope 分片 + INDEX 条目）。钉版点漏声明由规则驱动闸门当场
拦截，当轮补声明即可，无人工登记环节。本 spec 随该循环持续改进。

#### Scenario: 版本级 bug 归登记表

- **WHEN** 升级实测确认某版本或某版本组合不可用
- **THEN** 当轮登记进 `scripts/versions/restrictions.json`，lessons-learned
  只记其中非版本性的教训（如升级流程坑），不重复版本清单

#### Scenario: 漏登记当轮补全

- **WHEN** 升级过程发现某钉版点缺声明（如新子工程缺 `.python-version`）
- **THEN** 同一 change 内补全该点声明并登记对应 LL 条目——规则闸门
  当场拦截，无人工登记环节

#### Scenario: 非版本性坑归账本

- **WHEN** 升级踩到工具行为变化或配对失败模式
- **THEN** 当轮登记 LL 条目（分片 + INDEX），不写入 spec 或 README
