# Spec Delta: dependency-upgrade

## MODIFIED Requirements

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

## ADDED Requirements

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

## REMOVED Requirements

### Requirement: 坏版本降级与 blocked 触发式实施

**Reason**: 坏版本与配对不兼容是同一件事——某个具体版本组合实测失败，单包 bug
只是组合里只有一个包的特例。原条款把它拆成 blocked 与 pairs 两套互不相干的机制，
并规定「blocked 与 pairs 不绑定」Scenario 禁止同次实施，导致同一份知识要建两套
数据与两套消费代码（账本 LL-076：同一知识两份清单必漂移）。

**Migration**: 由「版本限制记录数据文件」与「版本限制记录与坏版本降级」两条
Requirement 承接：只登记实测失败的具体版本组合（包数 1~N），未登记一律放行去试，
记录只增不删；降级取未登记的最高可用版本并同轮收紧钉版文件范围。原条款要求的
"带出处强制"（issue 链接或 git commit）随实测语义取消——记录本身就是实测结果，
额外出处属重复；`Plan/软件升级.md`「blocked 落地」节的 typescript 7.0.0 实例
迁入 `scripts/versions/restrictions.json`。
