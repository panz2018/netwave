# project-governance Delta Spec

## MODIFIED Requirements

### Requirement: 元规则 review 三轴

合并前 review MUST 三轴并行，逐轴给出结论：

- **Standards**：对照本 spec 全部铁律与元规则 + 代码坏味道；其中
  「元规则 代码只写使用信息」的**语义层考古**（历史归因、口径变更叙述、
  契约声明与历史归因的区分）由本轴 AI 审查承担——门禁只拦固定形态标记，
  需理解上下文才能判定的考古文字在本轴逐行核查本次 diff；`openspec/`
  下的 archive、lessons-learned 账本与 `Plan/` 不在本轴考古审查范围
  （冻结历史与临时笔记）。diff 之外的全文考古由「diff 审后专职全文考古
  步骤」收口（见下方 Scenario 与 health-check spec）。
- **Spec**：对照本 change 的 `specs/` delta 逐条核实现是否落地；
- **Lessons**：对照 lessons-learned 账本 INDEX 逐条核对，命中即打回，
  并按该条目的复发检测方法复验。

任一轴命中违规即打回，不得以"其余轴通过"抵销。跨绑定改动另跑
`pnpm test:cross`；CI 全绿是合并前置条件。三轴的执行者是 agent，
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

#### Scenario: 语义考古由 Standards 轴打回

- **WHEN** Standards 轴发现本次 diff 改动的行内含门禁词表未覆盖的语义考古
  （历史归因、口径变更叙述）
- **THEN** 该轴判违规打回，要求改写为只陈述当前契约——不因"门禁未报"而放行

#### Scenario: diff 审后专职全文考古步骤

- **WHEN** 三轴 review（审 diff）完成
- **THEN** MUST 另有一道专职步骤对 diff 触碰文件的**全文**做语义考古审查
  （机制与只读纪律见 health-check spec 的 apply 态体检）——三轴审 diff
  确认本次变更准确有效，专职步骤收口"被触碰但不在 diff 内"的旧考古，
  两步分工不可互相替代

#### Scenario: 冻结历史与临时笔记不入考古审查

- **WHEN** Standards 轴审查范围涉及 `openspec/changes/archive/`、
  lessons-learned 账本或 `Plan/`
- **THEN** 不对这些位置做语义考古打回——冻结历史证据与在途临时笔记豁免
