# Spec Delta

## ADDED Requirements

### Requirement: 坏版本黑名单

登记表条目 MUST 支持可选字段 `blocked`：已知坏版本清单，每项含精确版本号
`version`、必填原因 `reason`、可选跟踪链接 `issue`。`version` MUST 是精确版本号
（拒绝范围、通配、比较符写法），结构非法即闸门 FAIL。`ci-actions` 条目 MUST NOT
挂 `blocked`（一条扛全部 action，分不清哪个 action 坏），违规即闸门 FAIL。
`blocked` 的语义是**现行禁令**而非历史档案：版本自身 bug 的禁令 MUST 永久有效
（发布版不可变，条目防回踩而非挡升级）；配对不兼容的禁令在对方升级兼容或
被移除时 MUST 删除，同一笔改动把兼容性结论挪进配对条目 `verified`。
黑名单由体检层（联网，可枚举段过滤改报 target，lockfile 段不碰）与
闸门层（离线，仓库内可读当前钉版值命中即 FAIL，`machine:` 条目跳过）消费，
细则见本 Requirement 各 Scenario。

#### Scenario: 体检跳过已知坏版本

- **WHEN** 某全局 CLI 的最新 release 在其登记条目的 `blocked` 清单中
- **THEN** 体检不推荐该版本，改报次新可用版为 target 并注明 blocked 原因

#### Scenario: 全部候选被堵

- **WHEN** 某工具的可用版本全部在 `blocked` 清单中
- **THEN** 体检报 `no known good target`，保持落后标记，不推荐任何版本

#### Scenario: 当前钉版踩中黑名单

- **WHEN** 仓库内某可读钉版值（如 `packageManager`、`.python-version`、
  workflow 全 pin 的 action tag）命中该条目的 `blocked`
- **THEN** `pnpm check:meta` FAIL 并指出该钉版停在已知坏版本及原因

#### Scenario: machine 条目闸门跳过

- **WHEN** 带 `blocked` 的条目钉版位置为 `machine:`（如全局 CLI、cargo 子命令）
- **THEN** 离线闸门跳过其黑名单检查，由联网体检探测已装版本消费

#### Scenario: 配对禁令随兼容而解除

- **WHEN** 配对不兼容禁令的对方版本升级到兼容版（或对方被移除）
- **THEN** 删除该 `blocked` 项，同一笔改动把兼容性结论写入配对条目 `verified`

#### Scenario: 自身 bug 禁令不随升级删除

- **WHEN** 某工具已升级到修复版，其条目仍留有旧坏版本的 `blocked` 记录
- **THEN** 闸门通过——条目防的是回踩，升级修复版不要求删除禁令

#### Scenario: ci-actions 不支持黑名单

- **WHEN** `ci-actions` 条目出现 `blocked` 字段
- **THEN** 闸门 FAIL，报该类别不支持黑名单

## MODIFIED Requirements

### Requirement: 最新稳定版优先

全部工具链、工具与软件库 MUST 升级到最新稳定版；仅当最新稳定版导致
构建/测试失败且确认为上游 bug（非本项目用法问题）时，才允许回退次新版，
回退 MUST 在登记表对应条目挂 `blocked`（精确版本号 + 原因 + issue 链接），
lessons-learned 只记非版本性的坑（工具行为变化、流程坑等），版本级 bug
证据以登记表条目为准。子项目 README 不设 Gotchas 章节，回退信息不入 README。

#### Scenario: 默认升最新稳定版

- **WHEN** 体检发现某依赖落后于最新稳定版
- **THEN** 升级目标为最新稳定版，且相关配置与文档同步更新到新版契约

#### Scenario: 回退须证据

- **WHEN** 最新稳定版构建失败且确认为上游 bug
- **THEN** 回退次新版并在登记表对应条目登记 `blocked`（version + reason +
  issue 链接），跟踪计划随 issue
- **AND** 回退原因不写入任何子项目 README

### Requirement: 钉死点登记表唯一真相源

仓库全部版本钉死点 MUST 登记在机器可读登记表 `scripts/versions.json`，
它是"版本钉在哪"的唯一真相源；散文文档 MUST NOT 复制登记表内容。
类别覆盖：Rust 工具链 pin 与 MSRV、CI 语言矩阵数字、包管理器 pin、
lockfile、GitHub 压缩包直装工具（wasm-pack、binaryen）、cargo 子命令、
全局 CLI 检查项、CI actions、Playwright 浏览器、oracle 环境 pin。

#### Scenario: 登记条目结构完整

- **WHEN** 校验登记表任一条目
- **THEN** 条目含：名称、类别、钉版位置（文件路径、`machine:` 安装位置，
  或 `discovered:` 发现规则——位置由闸门发现扫描提供，条目 MUST NOT
  手抄文件清单）、升级方法、配对约束（若有）、坏版本清单（若有）
- **AND** 散文文档以链接或"当前稳定版"措辞引用，不复制具体版本号

### Requirement: 双向对账闸门

`scripts/check_versions.py` MUST 双向对账登记表与真实文件：每个登记条目
对应真实存在的钉版位置（`machine:` 条目只查登记存在；`discovered:` 条目的
位置即发现规则本身）；仓库内每个钉版点都出现在登记表中；一致性规则
（每个 workspace 成员 `Cargo.toml` 必须携带 `rust-version` 且全部彼此一致、
`rust-version` 不高于 `rust-toolchain.toml` pin 的 major.minor、
`packageManager` 为精确版本）任一不满足即 FAIL。
闸门 MUST 接进根 `check:meta`。

#### Scenario: 手动升版漂移当场暴露

- **WHEN** `rust-toolchain.toml` 升到新 stable 而某 `Cargo.toml` 的
  `rust-version` 仍是旧值
- **THEN** 闸门 FAIL 并指出具体文件与期望值

#### Scenario: 成员丢 MSRV 钉静默逃逸

- **WHEN** 某 workspace 成员的 `Cargo.toml` 删掉了 `rust-version` 字段
- **THEN** 闸门 FAIL 并指出该成员——删字段不能逃逸对账

#### Scenario: 登记表条目指向不存在的位置

- **WHEN** 登记条目所指钉版位置在仓库或环境中不存在
- **THEN** 闸门 FAIL，报登记表漂移

### Requirement: 过期体检命令

仓库 MUST 提供聚合体检命令 `pnpm check:outdated`，覆盖四段：项目依赖
（`pnpm outdated`、`cargo update --dry-run`、`uv lock --upgrade --dry-run`）、
全局 CLI（当前版本 vs 最新 LTS/稳定版）、GitHub 压缩包直装工具与 cargo
子命令（已装版本 vs 最新 release）、CI actions（workflow 内 `uses:` 的
action 当前 tag vs 最新 release tag）。体检 MUST 读取登记表并应用坏版本
黑名单（消费规则见坏版本黑名单 Requirement）。该命令人工触发，MUST NOT
进 CI 或 `pnpm check`（结果随上游每日变化且需联网）。

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
为什么）记登记表条目 `blocked`（version + reason + issue）；非版本性的坑
（工具行为变化、配对失败模式、登记表漏钉版点）记 lessons-learned 账本
（scope 分片 + INDEX 条目），登记表漏项当轮补全。本 spec 随该循环持续改进。

#### Scenario: 漏登记当轮补全

- **WHEN** 升级过程发现某钉版点不在登记表中
- **THEN** 同一 change 内补全登记表并登记对应 LL 条目

#### Scenario: 版本级 bug 归登记表

- **WHEN** 升级确认某上游版本带 bug 需回退
- **THEN** 当轮在登记表对应条目挂 `blocked`，lessons-learned 只记其中
  非版本性的教训（如升级流程坑），不重复版本清单
