# health-check Specification Delta

## RENAMED Requirements

- FROM: `### Requirement: 归档完成后全项目只读体检`
- TO: `### Requirement: 两态只读体检（apply 被触碰文件 / archive 全项目存量）`

## MODIFIED Requirements

### Requirement: 两态只读体检（apply 被触碰文件 / archive 全项目存量）

体检是同一套只读机制的两种触发，覆盖三个互不重叠的范围——diff 行归
review 三轴，被触碰文件的全文归 apply 态体检，改动面之外的存量归
archive 态体检：

- **archive 态**：每次 OpenSpec change 归档完成（sync 核对与目录移动完成）
  后，MUST 执行一次全项目只读体检，扫描范围 = 本 change 改动面之外的
  全部存量。
- **apply 态**：每次 apply 的三轴 review 之后、`pnpm check:outdated` 之前，
  MUST 执行一次只读体检，扫描范围 = 本次 diff 触碰过的文件全文（含不在
  diff 内的旧行）。每次 apply MUST 执行本步；若被触碰文件全部落在豁免
  范围（`Plan/`、`openspec/changes/archive/`、本 change 工件自身），
  MUST 记一行"已查，无适用文件"留痕，MUST NOT 以"本次不算"跳过。

两态体检 MUST 覆盖固定维度清单（见「五维度清单」与「语义考古维」两个
scenario），每维度 MUST 给出结论（无发现写"已查，无"），维度查完即终止，
MUST NOT 追加范围外扫描。体检扫描阶段 MUST NOT 修改任何被检文件；发现由
主代理汇总后写入 Plan/（Plan/ 是体检的输出载体，不受扫描只读约束）；
修复动作一律等人工点名后走正常授权流程。体检 MUST NOT 进 CI 或
`pnpm check`。

#### Scenario: 归档完成后触发体检

- **WHEN** 任一 change 归档完成（sync 核对与目录移动完成）
- **THEN** 随即执行 archive 态只读体检，每维度有明确结论，维度结论齐全
  才算体检完成；体检是归档的收尾附加，其发现不追溯影响归档结果

#### Scenario: apply 态触发被触碰文件体检

- **WHEN** 任一 change 的 apply 完成三轴 review，进入收尾序列
- **THEN** 随即对 diff 触碰过的每个文件的全文执行只读体检（豁免目录除外），
  位置在三轴 review 之后、`pnpm check:outdated` 之前；被触碰文件全部豁免时
  记"已查，无适用文件"，本步仍留执行痕迹

#### Scenario: 五维度清单

- **WHEN** 执行体检确定扫描范围
- **THEN** 逐维覆盖且仅覆盖：①文档断言 vs 环境实测——常驻文档
  （`AGENTS.md`、各 spec、各 README、`openspec/config.yaml`）中的事实性
  断言逐条以只读命令核实；②死代码/孤儿文件——无引用的模块、脚本、
  配置项、Plan/ 条目；③规则重复/冲突——`AGENTS.md`、governance spec、
  `openspec/config.yaml` 之间同一规则多处正文或互相矛盾；④可门禁化 LL
  未落闸门——lessons-learned 账本中登记了检测方法却未进 `pnpm check:meta`
  的条目（判据同 governance spec「元规则 review 三轴」的可门禁化落闸
  条款，本 spec 不重述）；⑤Plan/ 过期——已完成未删、与主 spec 冲突的
  Plan/ 条目。其中维度⑤仅 archive 态适用（`Plan/` 是目录级对象，
  apply 态的单文件范围不含）

#### Scenario: 语义考古维（两态通用）

- **WHEN** 执行任一态体检
- **THEN** 除五维度外 MUST 另查语义考古维——被检文件全文中需理解上下文
  才能判定的历史归因与口径变更叙述（门禁词表不覆盖的语义层考古，判据见
  governance spec「元规则 代码只写使用信息」语义层），命中即列为发现并
  附文件+行号+证据；`openspec/changes/archive/`、lessons-learned 账本
  与 `Plan/` 不入本维

#### Scenario: 只读边界

- **WHEN** 体检过程中发现可修复的问题
- **THEN** 不修改该文件，写入体检输出（或按去重规则并入对应 Plan/
  条目），标注建议处置；仅人工点名后才执行修复

#### Scenario: 当场实证

- **WHEN** 某发现可用只读命令当场验证（如 `command -v`、grep 引用计数、
  `node -v`）
- **THEN** 体检时 MUST 当场执行该命令并在条目中记录"已实证"及命令输出
  摘要；无法只读验证的标"待人工确认"

#### Scenario: 本次改动违规走三轴不进体检

- **WHEN** 某违规位于本次 diff 改动的行内
- **THEN** 该违规不进体检输出，按 review 三轴"命中即打回"处理（补实现
  或撤 Requirement）；被触碰文件中不在 diff 内的旧行违规归 apply 态体检
