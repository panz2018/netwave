# project-governance Specification Delta

## MODIFIED Requirements

### Requirement: 元规则 代码只写使用信息

代码与配置面向最终用户。`.rs`/`.py`/`.ts` 的注释与 rustdoc/docstring/JSDoc，
以及 `.yml`/`.yaml`/`.toml` 配置的注释，MUST 只描述当前契约（做什么、为什么、
触发条件），MUST NOT 含任何开发过程信息。本规则分两层，分工明确：

- **固定形态层（门禁强制）**：`scripts/check_comments.py`（命令 `pnpm check:meta`）
  扫描上述六类后缀的注释，命中下列**封闭的固定形态标记集**即红——这些标记
  机械可判、零语义歧义：
  1. `LL-` 编号；
  2. CI run 号（`CI run` 后接六位以上数字）；
  3. 动词+日期归因（`Re-enabled` 后接日期、`重新启用` 后接日期、`已标定`）；
  4. 改动名（`openspec/changes/` 含 archive 下现存目录名，动态生成）；
  5. 指向开发文档的指针（`spec: <capability>`、铁律编号、`openspec/`、`Plan/`）；
  6. 讨论代号（`design decision` 后接数字、`design D` 后接数字）。
     路线图数字代号（中文「阶段」后接数字、英文 `stage`/`phase` 后接数字、
     表示"未成形的临时骨架"或"某功能稍后到来"的英文词）沿用既有模式，一并命中即红。
     标准契约用语 `Deprecated: use X instead` 中的 `deprecated` 不属被禁标记。
- **语义层（AI 审查承担）**：历史归因、口径变更叙述等需理解上下文才能判定的
  考古文字（如中文"某口径已废止""原方案被推翻"式叙述、契约声明与历史归因的
  区分）**不进任何门禁词表**，改由两个 AI 审查环节承担：diff 行内的语义考古
  归「元规则 review 三轴」Standards 轴，被触碰文件的全文归 health-check spec
  的 apply 态体检。门禁只守固定形态，语义判断不交给词表硬匹配。

**文件级豁免**（白名单，白名单之外零豁免）：`pnpm-lock.yaml`（生成物）、
`openspec/changes/archive/` 下的 `.openspec.yaml`（冻结历史）、既有构建目录
（`target`/`target-wasm`/`node_modules`/`.venv`/`dist`/`coverage` 等）、
`openspec/config.yaml`（其路径引用是流程指令的功能语义，非开发过程泄漏）。
历史靠 git log 追溯，不靠注释或配置注释。

#### Scenario: 代码注释写开发文档指针即红

- **WHEN** `.rs`/`.py`/`.ts`/`.yml`/`.yaml`/`.toml` 注释或 rustdoc/docstring/
  JSDoc 出现 `spec: <capability>`、`LL-` 编号、铁律编号、`openspec/` 或
  `Plan/` 指针
- **THEN** `pnpm check:meta` 失败（`scripts/check_comments.py` 命中报告）

#### Scenario: 代码注释写改动名或阶段代号即红

- **WHEN** 上述六类文件注释出现 `openspec/changes/` 下任一目录名、
  中文「阶段」后接数字、或英文 `stage`/`phase` 后接数字
- **THEN** `pnpm check:meta` 失败（`scripts/check_comments.py` 命中报告）

#### Scenario: 配置注释写固定形态标记即红

- **WHEN** `.yml`/`.yaml`/`.toml` 注释出现 `LL-` 编号、`CI run` 后接数字、
  `Re-enabled`/`重新启用` 后接日期、`已标定`、`design decision` 后接数字、
  `spec: <capability>`、铁律编号、`openspec/` 或 `Plan/` 指针
- **THEN** `pnpm check:meta` 失败（`scripts/check_comments.py` 命中报告）

#### Scenario: 配置文件豁免白名单不误报

- **WHEN** `pnpm-lock.yaml`、`openspec/config.yaml`、archive 下 `.openspec.yaml`
  或构建目录内的配置文件含上述固定形态标记
- **THEN** `pnpm check:meta` 通过——这些文件在文件级豁免白名单内

#### Scenario: 裸日期不误伤夹具

- **WHEN** 注释或测试夹具出现无动词前缀的裸日期（如版本串含
  `2026-10-13`）
- **THEN** `pnpm check:meta` 通过——日期归因只在动词（`Re-enabled`/`重新启用`）
  后接日期时命中，裸日期不触发

#### Scenario: 语义考古交 AI 审查不进门禁

- **WHEN** 常驻文档或配置注释含需理解语义才能判定的历史归因（如中文"某口径
  已废止"式叙述）
- **THEN** `pnpm check:meta` 与 `pnpm check:md` 均不因该语义内容报错——
  此类考古由 code-review 的 AI 审查承担，门禁词表不覆盖

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
