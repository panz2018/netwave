# Spec Delta

## REMOVED Requirements

### Requirement: 元规则 注释只写当前事实

**Reason**: 规则按受众重写为「代码只写使用信息」与「开发者文档引用自解释」
两条腿，原条文中的「稳定契约指针（铁律编号、LL 编号、`spec: <capability>`）
允许保留」豁免被推翻——代码面向最终用户，不得含开发文档指针。
**Migration**: 见本 delta 新增的两条 Requirement；代码注释中的 `spec:`/`LL-\d+`/
铁律编号引用删除并改为自包含使用描述，开发者文档引用改为标题跳转自解释形式。

## ADDED Requirements

### Requirement: 元规则 代码只写使用信息

代码注释与文档 MUST 只描述当前契约（做什么、为什么、触发条件）；MUST NOT
写改动名（`openspec/changes/` 下的目录名）、路线图阶段词（英文 `stage`/`phase`
后接数字、表示"未成形的临时骨架"或"某功能稍后到来"的英文词）、讨论代号、
"取代 X"/"不再是"/"已立案偏差"等考古叙述——历史靠 git log 追溯，不靠注释。

本规则按受众分两条腿门禁化，两脚本零豁免：

- **代码面**（`scripts/check_comments.py`，命令 `pnpm check:meta`）：扫描
  `.rs`/`.py`/`.ts` 的注释与 rustdoc/docstring/JSDoc。代码面向最终用户，
  MUST NOT 含任何开发过程信息——除上述考古词外，MUST NOT 含指向开发文档的
  指针（`spec: <capability>`、`LL-\d+`、铁律编号、`openspec/`、`Plan/`）。
  改动名由 `openspec/changes/`（含 archive）现存目录名动态生成。
- **文档面**（`scripts/check_md.py`，命令 `pnpm check:md`）：扫描全部
  Markdown（`openspec/specs/**/*.md`、`Plan/**/*.md`、
  `openspec/changes/archive/**/*.md`、根与子 README）。开发者文档的引用
  MUST 自解释（见「元规则 开发者文档引用自解释」）；考古词命中即红。

治理 spec 本文、lessons-learned 账本与 archive 均不再豁免：治理 spec 正文中
作为反例出现的触发词 MUST 改写为描述性表达（不含字面触发词），使门禁可零
豁免扫描全仓。

#### Scenario: 代码注释写开发文档指针即红

- **WHEN** `.rs`/`.py`/`.ts` 注释或 rustdoc/docstring/JSDoc 出现
  `spec: <capability>`、`LL-\d+`、铁律编号、`openspec/` 或 `Plan/` 指针
- **THEN** `pnpm check:meta` 失败（`scripts/check_comments.py` 命中报告）

#### Scenario: 文档面阶段词命中即红

- **WHEN** 任一 Markdown（含 `openspec/specs/`、`Plan/`、
  `openspec/changes/archive/`）出现「阶段」后接数字或英文 `stage`/`phase`
  后接数字
- **THEN** `pnpm check:md` 失败（`scripts/check_md.py` 命中报告）

#### Scenario: 归档指针指向不存在目录即红

- **WHEN** Markdown 出现行内代码形态的 `openspec/changes/archive/<name>/`
  完整路径而该目录不存在
- **THEN** `pnpm check:md` 失败（改名后残留旧路径被捕获）

#### Scenario: 治理 spec 反例不触发自身门禁

- **WHEN** 治理 spec 正文描述被禁止的考古词
- **THEN** 以描述性语言表达（如"英文阶段词后接数字"），不含字面触发词，
  `pnpm check:md` 通过

### Requirement: 元规则 开发者文档引用自解释

开发者文档（`openspec/specs/`、`AGENTS.md`、`CONTRIBUTING.md`、`Plan/`）中
的引用 MUST 一眼可懂、不依赖读者再去定位可能已归档或终将删除的文档：跨文档
引用 MUST 用标题跳转链接（`[标题](文件.md#锚点)`）而非章节序号或代号；指向
归档的引用 MUST 是完整路径且该目录 MUST 现存（改名时全仓同步更新）；MUST NOT
以「见某规划文档第 N 节」「跟踪于某待决清单」等需二次定位的表述替代可直接
读出的结论。代码注释 MUST NOT 含此类引用（属代码面禁区，见「元规则 代码只
写使用信息」）。

#### Scenario: 引用需二次定位即打回

- **WHEN** code-review Standards 轴发现开发者文档用章节序号、讨论代号或
  "见某规划文档"式表述指代结论，而结论未就地写出
- **THEN** 判不完成，要求改写为自包含表述或标题跳转链接

#### Scenario: 归档改名后引用同步

- **WHEN** `openspec/changes/archive/` 下目录改名
- **THEN** 全仓指向该目录的完整路径引用同步更新为新名，`pnpm check:md`
  链接校验无断链
