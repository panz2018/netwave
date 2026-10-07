# Proposal

## Why

仓库活文档（`openspec/specs/`、`Plan/`）与代码注释里散布「阶段 N」路线图代号、
指向 `总体计划.md`/`design.md` 等可能已进历史、难以定位的临时文档指针，以及
`spec:`/`LL-\d+`/铁律编号等开发过程引用。这些内容对最终用户毫无意义、对开发者
又常指向已归档/将删除的文档而断链，违反「持久文档禁写临时名称」与「引用自解释」
原则（LL-032 存量）。本次一次性把全部旧式引用清理为内容本身命名，并把受众分层
原则钉进宪法、门禁化，杜绝复发。

## What Changes

- **受众分层原则入宪法**：改写 governance 元规则为两条腿——① 代码（`.rs`/`.py`/`.ts`
  的注释与 rustdoc/docstring/JSDoc）MUST 只含最终用户使用信息，MUST NOT 含任何开发
  过程信息（阶段词、改动名、讨论代号）且 MUST NOT 指向开发文档（`openspec/`、`Plan/`、
  `spec:`/`LL-\d+`/铁律编号）；② 开发者文档（`openspec/specs/`、`AGENTS.md`、
  `CONTRIBUTING.md`、`Plan/`）的引用 MUST 自解释（标题跳转、不依赖已归档或将删除的
  文档定位）。**BREAKING**：推翻现行元规则中「稳定契约指针（铁律编号、LL 编号、
  `spec: <capability>`）允许保留」的豁免。
- **活 spec 去阶段词**：`api-contract`/`ci-matrix`/`frequency-unit`/`project-governance`/
  `zero-copy-roundtrip` 五份主 spec 正文的路线图数字代号全部改写为内容命名；
  区间契约（如原以路线图数字区间表达的「单常驻 worker 拓扑」条款）改写为内容
  锚点区间（「自常驻 worker 落地起至绑定高级能力立项前」）。
- **spec 删 Plan/ 依赖指针**：spec 正文不再引用 `总体计划.md`/`design.md` 等规划文档
  定位，改为自包含表述（「属未定设计决策，立项时 design.md 定案」）。
- **账本去阶段词**：`lessons-learned/core.md`、`docs.md` 的「阶段 N」改写为内容命名
  （docs.md 的违规证据转述为「路线图数字代号」，不再原样引用触发词）。
- **Plan/ 路线图去数字**：`总体计划.md`「分阶段路线图」标题改「路线图」、条目改内容
  命名有序列表、「阶段模型铁则」改写；`Plan/` 其余文档的 `#分阶段路线图` 锚点与
  阶段号引用同步改。
- **归档目录改名**：脚手架归档目录原名带路线图数字代号，改为
  `openspec/changes/archive/2026-09-27-monorepo-scaffold/`，全仓引用同步指新名。
- **archive 内容去阶段词**：`openspec/changes/archive/**` 的「阶段 N」全部改写为
  内容命名（其余历史叙述不动）。
- **governance 反例词去触发**：governance 元规则正文中作为反例出现的字面触发词
  （`skeleton`、`arrives with` 等）改写为描述性表达，使门禁可零豁免扫描。
- **门禁按受众拆两脚本**：`scripts/check_comments.py` 收窄为只管代码注释（禁阶段词 +
  禁开发文档指针 `spec:`/`LL-\d+`/铁律编号/`openspec/`/`Plan/`）；Markdown 的词表
  检查（阶段词、改动名、引用自解释）并入 `scripts/check_md.py`，与既有链接/锚点校验
  合成「开发者文档面」单一门禁。两脚本撤除对 governance/lessons-learned/archive 的
  豁免，扫描范围扩至 `Plan/` 与 `openspec/changes/archive/`；放行指向现存归档目录的
  完整路径。`STAGE_WORDS` 加 `阶段\s*[0-9]`。
- **代码存量清指针**：`core/src/frequency.rs`、`typescript/src/index.node.ts`、
  `typescript/src/types.ts` 的 `spec:`/`LL-\d+` 注释引用删除，改为自包含使用描述。

## Capabilities

### New Capabilities

（无——受众分层原则并入既有 `project-governance` 元规则，不新建 capability。）

### Modified Capabilities

- `project-governance`: 元规则「注释只写当前事实」改写为受众分层（代码=纯使用信息、
  禁开发文档指针；开发者文档=引用自解释），推翻稳定契约指针豁免；门禁化范围随之扩展
  （撤 governance/ledger/archive 豁免、扫 Plan/、代码面禁开发指针）。
- `api-contract`: 「频率轴主数据恒为 f64 Hz」「worker 泛化分发与单常驻拓扑」等
  requirement 正文去阶段词、去 `总体计划` 指针，区间契约改内容锚点。
- `ci-matrix`: Purpose 与 criterion/覆盖率/零 Python 等 requirement 正文去
  脚手架期数字代号措辞，改内容命名。
- `frequency-unit`: 「未知单位错误契约」requirement 正文去路线图数字代号措辞。
- `zero-copy-roundtrip`: 「core 提供交错复数 f64 缓冲」「异步与 Worker 边界契约」
  requirement 正文去路线图数字代号措辞，改内容命名。

## Non-goals

- 不改任何数值计算、API 签名、绑定机制或 CI job 拓扑——纯文档措辞与门禁脚本清理。
- 不改 `AGENTS.md`（受众分层由 governance 承载，AGENTS「项目铁律」指针已覆盖，
  避免同一事实跨层重复）。
- 不改 `package.json` 的 `scripts` 命令名与聚合结构（`check:meta`/`check:md` 名字不变，
  只换内部实现）。
- 不改归档目录的日期前缀与除脚手架归档目录（原名带路线图数字代号，
  本次改名）外的其余归档名（已自解释）。
- 不重写 archive 文档中除「阶段 N」外的历史叙述（冻结内容仅去阶段词）。

## Impact

- 文档：`openspec/specs/**`（5 份主 spec + governance + lessons-learned 两份账本）、
  `openspec/changes/archive/**`（含目录改名）、`Plan/**`（6 份）。
- 代码：`core/src/frequency.rs`、`typescript/src/index.node.ts`、`typescript/src/types.ts`
  （仅注释）。
- 工具：`scripts/check_comments.py`（收窄+扩扫描）、`scripts/check_md.py`（并入词表检查）。
- 门禁：`pnpm check:meta`（代码面）、`pnpm check:md`（文档面）行为变化；全仓
  `grep -rn "阶段\s*[0-9]"` 与代码面 `grep "spec:\|LL-[0-9]"` 须零命中。
- 受影响铁律：铁律七（docs 教学式标准 / 零手抄）——代码 docs 面向最终用户的定位不变，
  本次强化其「不含开发信息」边界。
