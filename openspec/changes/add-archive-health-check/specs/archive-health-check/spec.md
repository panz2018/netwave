# Spec Delta: archive-health-check

## ADDED Requirements

### Requirement: 归档前全项目只读体检

每次 OpenSpec change 归档前，MUST 执行一次全项目只读体检，扫描范围 =
本 change 改动面之外的全部存量（改动面违规由 review 三轴负责）。体检
MUST 覆盖且仅覆盖固定五维度（见「五维度清单」scenario），每维度 MUST
给出结论（无发现写"已查，无"），五维查完即终止，MUST NOT 追加范围外
扫描。体检 MUST NOT 修改任何既有文件（唯一例外 = 三级去重中向现有
Plan/ 文件追加补充条目，见「三级去重与归属一处」）；修复动作一律等
人工点名后走正常授权流程。体检 MUST NOT 进 CI 或 `pnpm check`。

#### Scenario: 归档触发体检

- **WHEN** 任一 change 完成归档流程
- **THEN** 归档前执行五维度只读体检，每维度有明确结论，五维结论齐全
  才算体检完成

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
  Plan/ 条目

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

- **WHEN** 体检发现某违规由本次 change 引入
- **THEN** 该违规不进体检输出，按 review 三轴"命中即打回"处理（补实现
  或撤 Requirement）

### Requirement: 三级去重与归属一处

体检的每条新发现 MUST 依次过三级去重，命中即按对应规则处置：

1. 命中 lessons-learned INDEX 既有条目 → 不报；
2. 命中 `Plan/` 现有文件中的条目 → 不写入新文档；
3. 对 `Plan/` 现有条目构成补充 → 直接写入该旧 Plan/ 文件（归属一处，
   届时与该条目一起处理），不另立新条目。

仅三级均未命中的全新发现写入 `Plan/体检-<日期>.md`。若全部发现均命中
第二/三级，本次体检 MUST NOT 产生新文件。

#### Scenario: 命中账本不报

- **WHEN** 新发现与 lessons-learned INDEX 某条目情形相同
- **THEN** 该发现不出现在任何输出中

#### Scenario: 补充并入旧 Plan 文件

- **WHEN** 新发现与 `Plan/` 某现有条目同主题且构成补充
- **THEN** 内容追加进该旧 Plan/ 文件对应节，`Plan/体检-<日期>.md`
  不出现该条

#### Scenario: 全新发现落新文件

- **WHEN** 发现未命中账本与任何 Plan/ 条目
- **THEN** 写入 `Plan/体检-<日期>.md`（当日文件已存在则追加），条目
  附文件+行号+证据

### Requirement: 体检输出格式与上限

体检输出（`Plan/体检-<日期>.md`）MUST 满足：每条发现附仓库内文件路径+
行号+证据，无证据不写；每条分级为"硬"（违反现行 spec/铁律/闸门口径
矛盾）或"待拍板"（低效、疑似不再需要等判断类）；按维度分组呈现，
MUST NOT 做跨维度重排序；每维度 ≤5 条、全文 ≤15 条，超出部分只报计数
（如"另有 N 条低优先级，可加扫"）。单维度报告 MUST 控制在一页内
（约 400 词以内）。

#### Scenario: 无证据不写

- **WHEN** 某疑似问题给不出文件+行号+证据
- **THEN** 该条不写入体检输出

#### Scenario: 上限截断报计数

- **WHEN** 某维度发现超过 5 条
- **THEN** 只写按严重度排序的前 5 条，其余以计数一行呈现

### Requirement: 硬伤阻塞归档

体检输出中若存在"硬"级发现（违反现行 spec/铁律或闸门口径矛盾），
归档 MUST 暂停，直至该硬伤被人工明确豁免或当场修复后才继续归档；
"待拍板"级发现 MUST NOT 阻塞归档。

#### Scenario: 硬伤卡归档

- **WHEN** 体检报出至少一条"硬"级发现
- **THEN** 归档暂停，向人呈报该条目；人工豁免或修复完成后才继续归档

#### Scenario: 待拍板不卡

- **WHEN** 体检输出只含"待拍板"级发现
- **THEN** 归档照常进行，发现项留在 Plan/ 等人工圈定

### Requirement: 体检执行机制

体检 MUST 按维度派发 fresh-context 子代理并行执行（每子代理只携带本
维度清单与证据标准，轴间上下文互不污染）；执行环境无子代理能力时
MUST 降级为逐维度顺序执行，每维度扫完先固化结论再扫下一维度。体检
开始前 MUST 完成前置校验（本 change 目录、`openspec/specs/`、
`openspec/specs/lessons-learned/INDEX.md`、`Plan/` 存在且可读），校验
失败即停并报错，MUST NOT 带病开扫。闸门（`pnpm check` 系列）已机械
强制的违规 MUST NOT 重复报出。

#### Scenario: 无子代理降级顺序

- **WHEN** 执行环境不提供 fresh-context 子代理
- **THEN** 按五维度顺序执行，结论逐维固化，体检照常完成，不报错终止

#### Scenario: 前置校验失败即停

- **WHEN** 前置校验发现必需路径缺失或不可读
- **THEN** 体检终止并报告缺失项，不派发任何维度扫描

#### Scenario: 闸门已覆盖不报

- **WHEN** 某违规已被 `pnpm check` 系列门禁机械强制
- **THEN** 体检不重复报该类问题
