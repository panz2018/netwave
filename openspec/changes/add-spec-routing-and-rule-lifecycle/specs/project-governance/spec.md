# project-governance Specification Delta

## ADDED Requirements

### Requirement: 元规则 规则生命周期

每条规则从诞生到退出 MUST 走归层路由与退役判据，防止规则堆只增不减：

- **归层路由**（新增规则先定落点，单一正文）：跨端产品契约→本 spec 铁律段；
  文档/流程/法务元约束→本 spec 元规则段；能力专属契约→对应能力 spec；
  环境坑、实现决策、人工纠正→lessons-learned 账本；agent 行为准则→
  `AGENTS.md`（只放准则句与指针）。写规则前先查既有覆盖，禁就近塞入。
- **退役判据**（满足任一即可退出，退出时正文内容不得蒸发）：① 被更高层
  规则完整覆盖（核对覆盖度，缺的细节先并入该高层规则 rationale）；② 被
  门禁/编译器/固化脚本承载（先证明违规样例变红）；③ 契约废止或一次性事实
  失效。退役动作与去向 MUST 留痕于当次 change 工件。
- **编号纪律**：铁律与 LL 编号是名字，退役后不复用、不重排（沿用
  「铁律编号是名字，编号退役不复用」，账本侧见 lessons-learned spec
  「账本条目退役」）。
- **分片阈值**：任一常驻规则文件超过 1000 行或超过 40 条 Requirement 时，
  MUST 触发拆分评审（评而不必拆，结论留痕）。本 spec 维持单文件双段
  （铁律段/元规则段），拆分与否只由本条阈值触发评审决定。

本条为治理机制约束，无数值容差；可测性由 review Standards 轴与
`scripts/check_md.py`（路由一致性）承担。

#### Scenario: 新增规则先归层

- **WHEN** 准备新增一条规则（铁律/元规则/能力契约/账本条目/行为准则）
- **THEN** 先按路由表确定唯一落点并核对既有覆盖；已覆盖只改指针，
  未覆盖才新增正文；落点与规则性质不符即 review 打回

#### Scenario: 退役附证据与去向

- **WHEN** 某条规则申请退役
- **THEN** 附三类判据之一的证据（覆盖对照 / 违规样例红 / 废止声明），
  且正文去向写明（并入 rationale / 迁出 / 删除靠 git log），编号不复用；
  无证据即打回

#### Scenario: 超阈值触发拆分评审

- **WHEN** 某常驻规则文件行数超 1000 或 Requirement 数超 40
- **THEN** 下一次触碰该文件的 change MUST 含拆分评审结论（拆或维持，
  留痕 design.md），不得无视

### Requirement: 元规则 spec 路由单入口

`openspec/specs/README.md` MUST 是全部 spec 的唯一路由入口：宪法按任务
路由（改代码/API/CI 读铁律段、改文档/流程/法务读元规则段）、账本先扫
INDEX、每个能力 spec 一行"何时读"条件。`AGENTS.md` 对此 MUST 只留一句
硬护栏指针（"动手前先读 `openspec/specs/README.md`"），MUST NOT 重述
路由清单；`openspec/specs/` 下新增或删除能力目录 MUST 同一 change 内
同步更新 README。本条为治理机制约束，无数值容差；一致性由
`scripts/check_md.py` SPECS ROUTER 规则门禁强制。

#### Scenario: 路由与目录双向一致

- **WHEN** `openspec/specs/` 存在某能力目录而 README 无对应行，
  或 README 某行指向不存在的目录
- **THEN** `pnpm check:md` 失败（SPECS ROUTER 命中报告）

#### Scenario: 行为准则不重述路由清单

- **WHEN** 检查 `AGENTS.md` 的文档阅读入口相关内容
- **THEN** 只含指向 specs/README.md 的指针句，无逐 spec 路由清单正文

## MODIFIED Requirements

### Requirement: 元规则 文档受众分层

全部规矩文档的受众 MUST 是 AI：`AGENTS.md`（行为准则 + 指针）、
`openspec/specs/README.md`（spec 路由单入口，见「元规则 spec 路由单入口」）
构成 **AI 必读区**；其余 spec（本 spec、lessons-learned 账本、各能力 spec）、
`openspec/config.yaml`（工件规则与流程钩子）与各子项目 README（本目录命令）
MUST 经 README 路由按需读取。人只看区只有两项——根 README（项目是什么）
与 AI 呈上的决策表/全景表。人 MUST NOT 被要求阅读细节或撰写账本；
人的职责 = 决策方向与点名执行。

内容按变更级别归层，每条事实 MUST 只存一份正文：① 契约级决定（改动波及
已发布代码/跨端契约）MUST 入本 spec，走最高级变更；② agent 行为准则
（约束执行动作而非系统状态）MUST 入 `AGENTS.md`，保持精简（准则 + 指针，
MUST NOT 重述 spec 正文与内容清单细节）；③ 事件级事实（踩坑、实现决策、
人工纠正）MUST 只入 lessons-learned 账本。同一事实 MUST NOT 跨层重复。

Plan/ 生命周期（只放未执行任务、结论吸收后删除、终态整目录清空）的
**唯一正文 MUST 是 `openspec/config.yaml`** 的 `operations` 段——规则正文
随执行钩子存放，注入链最短；`AGENTS.md` 与 `CONTRIBUTING.md` 对此 MUST
只留指针，MUST NOT 重述正文。

各文档的内容分配清单属第②层执行细节，只列于 `openspec/specs/README.md`
（按两区组织），清单增删不触发本 spec 变更。

#### Scenario: 新事实正确归层

- **WHEN** 产生一条新信息（坑/决定/准则/契约）
- **THEN** 按判据归入唯一层，其余层不出现其正文

#### Scenario: 坑只进账本

- **WHEN** 新增环境坑或实现决策记录
- **THEN** 仅出现在 lessons-learned 账本，README/CONTRIBUTING 无新增坑节

#### Scenario: 清单调整不动宪法

- **WHEN** 内容分配清单需要调整（新增目录/章节改归属）
- **THEN** 只改 `openspec/specs/README.md`，本 spec 与 `AGENTS.md` 不动

#### Scenario: 规矩文档不要求人读细节

- **WHEN** 某文档条目把人类设为读者或执行者（要求人扫清单、写记录、
  逐条核对）
- **THEN** 判违规：改写为 AI 的执行动作，人侧只保留决策与点名

#### Scenario: Plan 生命周期正文唯一

- **WHEN** 检查 `AGENTS.md`、`CONTRIBUTING.md`、`openspec/config.yaml`
  三处关于 Plan/ 生命周期的表述
- **THEN** 仅 `config.yaml` 有正文，另两处为指针，无第二份正文

#### Scenario: 必读区收敛为两文件

- **WHEN** 检查 `AGENTS.md` 文档阅读入口与 `openspec/specs/README.md`
- **THEN** 必读区只有 AGENTS.md 与 specs/README.md 两项，其余 spec 的
  阅读时机只出现在 README 路由行，不散现于 AGENTS.md
