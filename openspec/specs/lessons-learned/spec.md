# lessons-learned Specification

## Purpose

定义 netwave 的纠错账本机制：人工纠正即时登记为 LL-NNN 条目、动手前强制扫描、
review 第三轴复发检测、可门禁化条目转 check 脚本——使同一错误跨会话永不再犯。

## Requirements

### Requirement: 账本为坑与实现决策的唯一汇集地

全仓的环境坑、实现决策记录、人工纠正教训 MUST 只存于
`openspec/specs/lessons-learned/`；各子 README MUST NOT 再设 Implementation
notes / Gotchas 节，只保留本目录的编译/测试命令。账本 MUST 按 scope 分片为
小文件（`ci.md`/`core.md`/`python.md`/`typescript.md`/`docs.md`，单文件
SHOULD ≤50 行）+ `INDEX.md` 一行一条索引（LL 编号 | scope | 一句话规则），
AI 检索 MUST 先扫 INDEX 再按需打开对应 scope 文件。每条条目 MUST 含四要素：
编号 `LL-NNN`、scope 标签、犯过证据（commit/session 可追溯）、规则与复发
检测方式。

#### Scenario: 子 README 无坑节

- **WHEN** `pnpm check:md` 的链接/结构校验或人工 review 检查四个子 README
- **THEN** 无 Implementation notes / Gotchas 标题；对应内容在账本中可按
  scope 检索到

#### Scenario: 条目格式完整

- **WHEN** 新增任一 LL 条目
- **THEN** 四要素齐备且 INDEX.md 同步增一行，缺任一项 review 判不完成

#### Scenario: 检索先索引后分片

- **WHEN** agent 或人需要查坑
- **THEN** 读 INDEX.md 定位 scope，再打开对应小文件，无需读全量条目

### Requirement: 被纠正即登记

AI 被人工纠正的当轮 MUST 登记：先在账本（扫 INDEX.md 后开对应 scope 分片）
检索同类条目——已有则该轮回复 MUST 引用编号并说明未遵守的原因；没有则 MUST
新增 LL-NNN 条目到对应分片并同步 INDEX.md。登记 MUST NOT 推迟到归档 retro。

#### Scenario: 同类纠正命中旧条目

- **WHEN** 人工指出的问题与既有 LL 条目同类
- **THEN** 当轮回复引用该 LL 编号，且该命中计入复发记录

#### Scenario: 新错误即时入账

- **WHEN** 人工指出的问题无同类条目
- **THEN** 当轮账本对应 scope 分片出现新 LL 条目（含四要素）且 INDEX 同步，
  不等待归档

### Requirement: review 第三轴 Lessons

code-review MUST 由两轴扩为三轴：Standards × Spec × Lessons。Lessons 轴
MUST 逐条对照账本（INDEX + 相关 scope 分片）检查本次改动是否命中既有条目；
命中即打回，并按"复发检测方式"验证修复。

#### Scenario: 命中旧错即打回

- **WHEN** 改动违反任一既有 LL 条目的规则
- **THEN** Lessons 轴标记该 LL 编号并打回，修复后按条目检测方式复验

### Requirement: 可门禁化条目转 check 脚本

每条 LL 条目登记与 review 时 MUST 回答"能否门禁化"：能转为脚本/CI 检查的
条目 MUST 落进 `pnpm check`（或 CI 步骤），条目注明对应门禁命令；不能门禁化
的 MUST 保留文字规则并注明原因。文字规则数量 SHOULD 随时间递减。

#### Scenario: 门禁化后引用命令

- **WHEN** LL 条目完成门禁化（如 utf-8 读取、断链校验）
- **THEN** 条目"复发检测方式"写明具体 check 命令，CI 红即视为复发拦截

#### Scenario: 不可门禁化留痕

- **WHEN** 条目判定无法门禁化（如命名审美、契约理解类）
- **THEN** 条目写明原因，保留文字规则供 review 第三轴人工/agent 比对
