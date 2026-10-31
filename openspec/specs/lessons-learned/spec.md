# lessons-learned Specification

## Purpose

定义 netwave 的纠错账本机制：人工纠正即时登记为 LL-NNN 条目、动手前强制扫描、
review 第三轴复发检测、可门禁化条目转 check 脚本——使同一错误跨会话永不再犯。

## Requirements

### Requirement: 账本为坑与实现决策的唯一汇集地

全仓的环境坑、实现决策记录、人工纠正教训 MUST 只存于
`openspec/specs/lessons-learned/`；各子 README MUST NOT 再设 Implementation
notes / Gotchas 节，只保留本目录的编译/测试命令。账本 MUST 按 scope 分片为
小文件（`ci.md`/`core.md`/`python.md`/`typescript.md`/`docs.md`/`workflow.md`，
单文件 SHOULD ≤50 行）+ `INDEX.md` 一行一条索引（LL 编号 | scope | 一句话规则），
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

### Requirement: 账本条目退役

账本 MUST 可退出，防"只增不减"膨胀成第二套规则堆。一条 LL 满足以下
任一判据方可退役（正文删除或迁出，事故证据靠 git log 追溯）：

1. **已铁律化/契约化**：规则结论已被 governance spec 或某能力 spec 完整
   覆盖。退役前 MUST 做覆盖度核对——spec 缺的细节（理由、代价、边界）
   MUST 先并入该 spec 对应 Requirement 的正文或 rationale，再删账本正文；
   被 spec 正文指名"唯一正文见账本"的条目 MUST NOT 退役（否则 spec 断链）。
2. **已门禁化**：规则已被某脚本/CI 闸门/编译器强制。退役前 MUST 两步走
   证明——先构造一条违规样例、跑出该闸门红，再删账本正文；证明不了的
   降级为"待落门禁"，门禁落地前不退役。
3. **一次性事实失效**：仅对某次迁移或已淘汰工具版本有效。容器/CI 平台类
   坑属环境类条件、任何等价环境都会复发，MUST NOT 判为一次性。

退役执行纪律：去向标签是初判不是结论，每条退役 MUST 经人逐条确认；
确认记录与"LL→去向"映射表 MUST 留痕于当次 change 的 design.md（不留
常驻副本）；删除正文的同一 change MUST 同步删除 `INDEX.md` 对应行，
INDEX MUST NOT 留墓碑行（编号只增不复用，历史引用靠 git log 与
design.md 映射）。每轮退役后 MUST 跑 `pnpm check:md`。

本条为治理机制约束，无数值容差；可测性由 review Standards 轴与
`scripts/check_md.py` 承担。

#### Scenario: 铁律化退役先并细节

- **WHEN** 某条 LL 申请以判据 1 退役
- **THEN** 附覆盖对照（目标 spec 节锚点 + 逐点比对），spec 缺的细节
  已在同一 change 并入该 spec；账本正文指名被 spec 引为唯一正文者打回

#### Scenario: 门禁化退役先跑红

- **WHEN** 某条 LL 申请以判据 2 退役
- **THEN** 附违规样例在该门禁下变红的证据；无证据即降级"待落门禁"，
  正文保留

#### Scenario: 容器类坑不算一次性

- **WHEN** 某条 LL 被标"一次性"而其条件是容器/CI 平台/通用工具行为
- **THEN** 打回：等价环境必复发，判据 3 不成立，保留账本

#### Scenario: 退役同步 INDEX 不留墓碑

- **WHEN** 某条 LL 正文被删除
- **THEN** `INDEX.md` 对应行同轮删除，无"已退役"占位行；去向只记于
  当次 change 的 design.md

#### Scenario: 未经确认不得退役

- **WHEN** 退役清单中某条无逐条确认记录
- **THEN** 该条不执行删除；批量标签（"约 N 条"）不构成确认
