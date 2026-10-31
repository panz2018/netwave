# project-governance Specification Delta

## ADDED Requirements

### Requirement: 元规则 最小规则原则

规矩文档（`AGENTS.md`、本 spec、`openspec/config.yaml`、lessons-learned 账本）
MUST 以"能完整表达预期行为的**最小信息集**"为编写目标，而非穷举规则清单；
约束形态上**动作边界**（拦住不可逆后果的硬闸，如未点名禁止执行、不主动
commit）优于**过程管束**（规定如何思考与问答的软约束），前者少而硬地保留，
后者默认不写入常驻文档。细则见下方三个 Scenario；`AGENTS.md` 只留对应
准则句与指向本 Requirement 的指针。本条外部依据的出处链接只存立案
change 的 Prior art，不入宪法正文。

#### Scenario: 已有门禁不再重述

- **WHEN** 某规则已被 `scripts/` 闸门或 CI 步骤强制，而常驻文档写出其
  全部判据与格式细节
- **THEN** review Standards 轴判冗余，要求压成"必跑命令"一句 + 指针

#### Scenario: 新增规则先查重

- **WHEN** 准备向 `AGENTS.md` 或本 spec 新增一条规则
- **THEN** 先确认既有门禁/规则未覆盖；已覆盖则只改指针，不新增正文

#### Scenario: 仪式不入常驻

- **WHEN** 提议向常驻准则添加固定问答格式、档位表或打勾自检清单
- **THEN** 默认拒绝；确有必要时须先门禁化（可机检），否则只允许进
  `Plan/` 临时文档

### Requirement: 元规则 review 三轴

合并前 review MUST 三轴并行，逐轴给出结论：

- **Standards**：对照本 spec 全部铁律与元规则 + 代码坏味道；
- **Spec**：对照本 change 的 `specs/` delta 逐条核实现是否落地；
- **Lessons**：对照 lessons-learned 账本 INDEX 逐条核对，命中即打回，
  并按该条目的复发检测方法复验。

任一轴命中违规即打回，不得以"其余轴通过"抵销。跨绑定改动另跑
`pnpm check:cross`；CI 全绿是合并前置条件。三轴的执行者是 agent，
人只看结论表。

#### Scenario: 命中账本即打回

- **WHEN** Lessons 轴发现改动命中 INDEX 某条目的情形
- **THEN** 打回该改动，按该条目登记的检测方法复验后重新 review

#### Scenario: 轴间不可抵销

- **WHEN** 某轴判违规而其余轴通过
- **THEN** 仍打回——三轴是并列闸门，不是加权评分

#### Scenario: spec 与实现脱节即打回

- **WHEN** Spec 轴发现 delta 中某 Requirement 在代码无对应落地
- **THEN** 判不完成，要求补实现或撤该 Requirement

## MODIFIED Requirements

### Requirement: 元规则 文档受众分层

全部规矩文档的受众 MUST 是 AI：`AGENTS.md`（行为准则）、lessons-learned
账本与 INDEX（错误记忆）、本 spec（契约）、`openspec/config.yaml`
（工件规则与流程钩子）、各子项目 README（本目录命令）构成 **AI 必读区**；
人只看区只有两项——根 README（项目是什么）与 AI 呈上的决策表/全景表。
人 MUST NOT 被要求阅读细节或撰写账本；人的职责 = 决策方向与点名执行。

内容按变更级别归层，每条事实 MUST 只存一份正文：① 契约级决定（改动波及
已发布代码/跨端契约）MUST 入本 spec，走最高级变更；② agent 行为准则
（约束执行动作而非系统状态）MUST 入 `AGENTS.md`，保持精简（准则 + 指针，
MUST NOT 重述 spec 正文与内容清单细节）；③ 事件级事实（踩坑、实现决策、
人工纠正）MUST 只入 lessons-learned 账本。同一事实 MUST NOT 跨层重复。

Plan/ 生命周期（只放未执行任务、结论吸收后删除、终态整目录清空）的
**唯一正文 MUST 是 `openspec/config.yaml`** 的 `operations` 段——规则正文
随执行钩子存放，注入链最短；`AGENTS.md` 与 `CONTRIBUTING.md` 对此 MUST
只留指针，MUST NOT 重述正文。

各文档的内容分配清单属第②层执行细节，只列于 `AGENTS.md` 文档地图（按
两区组织），清单增删不触发本 spec 变更。

#### Scenario: 新事实正确归层

- **WHEN** 产生一条新信息（坑/决定/准则/契约）
- **THEN** 按判据归入唯一层，其余层不出现其正文

#### Scenario: 坑只进账本

- **WHEN** 新增环境坑或实现决策记录
- **THEN** 仅出现在 lessons-learned 账本，README/CONTRIBUTING 无新增坑节

#### Scenario: 清单调整不动宪法

- **WHEN** 内容分配清单需要调整（新增目录/章节改归属）
- **THEN** 只改 AGENTS.md 文档地图，本 spec 不动

#### Scenario: 规矩文档不要求人读细节

- **WHEN** 某文档条目把人类设为读者或执行者（要求人扫清单、写记录、
  逐条核对）
- **THEN** 判违规：改写为 AI 的执行动作，人侧只保留决策与点名

#### Scenario: Plan 生命周期正文唯一

- **WHEN** 检查 `AGENTS.md`、`CONTRIBUTING.md`、`openspec/config.yaml`
  三处关于 Plan/ 生命周期的表述
- **THEN** 仅 `config.yaml` 有正文，另两处为指针，无第二份正文
