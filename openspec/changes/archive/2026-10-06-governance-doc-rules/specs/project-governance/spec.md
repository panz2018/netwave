# Spec Delta

## Purpose

修订「教学式文档与类型标注」元规则（引用格式与路径归属三条线分离），新增
元规则「注释只写当前事实」并门禁化，使文档引用与注释内容有可判定依据。

## ADDED Requirements

### Requirement: 元规则 注释只写当前事实

代码注释与文档 MUST 只描述当前契约（做什么、为什么、触发条件）；MUST NOT
写改动名（`openspec/changes/` 下的目录名）、路线图阶段词（`stage N`、
`phase-N`、`skeleton`、`arrives with`）、讨论代号、`replaces X`/`no longer`/
`deviation filed` 等考古叙述——历史靠 git log 追溯，不靠注释。稳定契约指针
（铁律编号、LL 编号、`spec: <capability>`）不属考古，允许保留。本规则 MUST
门禁化：脚本扫描 `.rs`/`.py`/`.ts` 注释与 `openspec/specs/**/*.md`，改动名
由 `openspec/changes/`（含 archive）目录名动态生成，命中即红；治理 spec 本文、
lessons-learned 账本与 archive 豁免（引用反例作证据）。

#### Scenario: 注释写改动名即红

- **WHEN** 代码注释或主 spec 出现 `openspec/changes/` 下任一目录名
- **THEN** `pnpm check:meta` 失败（`scripts/check_comments.py` 命中报告）

#### Scenario: 契约指针不误伤

- **WHEN** 注释含铁律编号、LL 编号或现存 spec 能力名指针
- **THEN** 门禁通过（稳定契约指针不属考古叙述）

## MODIFIED Requirements

### Requirement: 元规则 教学式文档与类型标注

每个公开函数/结构体/类 MUST 有 docs（rustdoc/docstring/JSDoc），跨模块逻辑
与非直观实现 MUST 有行内注释，目标：不懂 RF 的读者仅凭代码内文档即可看懂
程序为何如此编写。术语定义与公式 MUST 直接写进 docs（自包含）——编写以
权威术语源为准，但 MUST NOT 以"见某书某章"代替内容。算法处 MUST 写明公式
来源、近似/适用条件、容差依据（引用 manifest key）。全部公开 API MUST 有
完整静态类型标注（Python 全量 type hints 过 mypy/pyright；TS 禁无差别
`any`）。

代码内文档引用权威书目 MUST 用「书名 + 可访问链接」，引用格式唯一真相源为
根 README 的 References 节；MUST NOT 在代码内文档写本地绝对路径（外部读者
不可访问）。权威术语源的机器限定查阅入口（本机镜像绝对路径 + 许可红线）
唯一落根 CONTRIBUTING.md「Local reference mirrors (this machine only)」表，
换机以路径存在性 `ls` 自检；本 spec 只留指针不留路径。

#### Scenario: 缺 docs 即不完成

- **WHEN** code-review Standards 轴发现公开 API 缺 docs 或类型标注
- **THEN** 该 PR 判不完成

#### Scenario: 代码内文档禁本地路径

- **WHEN** rustdoc/docstring/JSDoc 出现本机绝对路径引用
- **THEN** code-review Standards 轴打回，改用 README References 的书名+链接
  格式
