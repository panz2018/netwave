# Proposal

## Why

脚手架已归档，`openspec/` 按 AGENTS.md 约定成为唯一事实源，但全部硬约束
（七条铁律 + 元规则）仍留在 `Plan/constitution.md`——一个生命周期终点为"删除"
的目录里。宪法不迁入 openspec，Plan/ 就永远删不掉，"唯一真相源"就是空话。

## What Changes

- 新建能力 spec `project-governance`：将宪法七条铁律与元规则转写为可验证的
  Requirement/Scenario（内容语义不变，仅从"宪法文体"转写为"spec 文体"），
  迁入后成为全部硬约束的唯一正文。
- 修订 `openspec/config.yaml` 的 `context`：指针从 `Plan/constitution.md`
  改指 `openspec/specs/project-governance/spec.md`。
- 全仓引用改写：`AGENTS.md`、`core/README.md`、`python/README.md`、
  `typescript/README.md`、`testdata/README.md`、`scripts/README.md`、
  `CONTRIBUTING.md`、`Plan/` 各文档中的 constitution 链接统一改指新位置；
  代码注释中的 `constitution rule N` 措辞改为 `governance spec rule N`
  （英文注释，仅改指向，不改语义）。
- 删除 `Plan/constitution.md`；其「修订历史」整段迁入新 spec 末尾
  （历史记录保持原样，不做文体转写）。
- 同步更新 `Plan/README.md` 与 `AGENTS.md` 的 Plan/ 生命周期条款：
  终态从"constitution 届时迁入 openspec/project.md"改为"已迁入
  `openspec/specs/project-governance/`"。

## Capabilities

### New Capabilities

- `project-governance`: 项目硬约束（数据布局 / TDD / 容差分层 / skrf 边界 /
  z0 端口属性 / 性能底线 / 覆盖率 / 语言与文档元规则）的唯一真相源 spec。

### Modified Capabilities

（无——ci-matrix / workspace-layout / zero-copy-roundtrip 的需求本身不变，
只是它们引用的宪法位置变了。）

## Non-goals

- 不修改任何铁律的语义与量级（改铁律 = 最高级变更，走独立修宪流程）。
- 不新增/删除 Plan/ 中除 constitution 之外的文档。
- 不改测试代码逻辑（注释指向除外）。

## Impact

- 文档：上列全部 README/AGENTS/CONTRIBUTING/Plan 文件。
- 代码：仅注释措辞（`core/src/lib.rs`、`core/tests/fill_pattern.rs`、
  `python/tests/test_roundtrip.py` 等），零逻辑改动。
- 工具链：`openspec/config.yaml` context 指针；`scripts/check_md.py`
  链接校验须零断链通过。
- 流程：`/opsx:*` 自动注入的 context 指针随之更新，agent 行为不变。
