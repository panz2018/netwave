# Proposal: governance-api-rules

## Why

`Frequency` 功能面设计冻结后暴露三处契约缺口：跨端显示串无统一协议（各端
`print`/`console.log` 输出形态无约束）、skrf 兼容无判据（偏离无立案门槛）、
绑定壳无厚度约束（能力易私长进 JS/Python 壳）。同时 `api-contract` 与已归档
的 `memory-lifecycle` 对显式回收方法名说法不一致（`release()` vs `drop()`），
两份主 spec 打架，review 无据可依。

## What Changes

- 宪法新增**铁律九 跨端协议钩子**：每公开类跨端统一显示串
  `ClassName(摘要)`，入口按语言原生协议命名（Rust `Display`/`Debug`、
  Python `__str__`/`__repr__`、Node `toString()`+inspect、浏览器
  `async toString()`）；`npoints` 公开类配 Python `__len__` 一行委托；
  协议保留名字典入 spec。
- 宪法新增**铁律十 scikit-rf API 兼容优先**：公开 API 命名/参数/返回值/
  语义默认对齐 skrf，偏离须在 design.md 立案更强收获；语言机械映射
  （TS camelCase、Rust snake_case、worker async 化）不算偏离。
- 宪法新增**铁律十一 绑定薄壳**：绑定层只做类型搬运与再导出，能力缺失
  修 core 绑定宏段，壳零改动；协议钩子一行委托不算壳逻辑。
- 宪法**铁律八补跨 realm 生命周期指针**：正文末尾指向 `memory-lifecycle`
  spec（registry 驱动 worker 释放、`drop()` 逃生口、napi finalizer），
  细节不搬入，避免双真相源。
- `api-contract` **显式回收方法名对齐**：`release()` 改为 `drop()`，
  与 `memory-lifecycle` 定案一致；全仓 grep 清旧副本。

## Capabilities

### New Capabilities

（无——三条新铁律均入既有 governance capability。）

### Modified Capabilities

- `project-governance`: 新增铁律九/十/十一；铁律八补跨 realm 生命周期
  指针（指向 memory-lifecycle spec）。
- `api-contract`: 「显式托管入口与显式内存回收」Requirement 的 `release()`
  更名 `drop()` 并指向 memory-lifecycle spec。

## Impact

- `openspec/specs/project-governance/spec.md`（sync 时应用 delta）
- `openspec/specs/api-contract/spec.md`（sync 时应用 delta）
- 后续实现 change `frequency-class` 以铁律九/十/十一为 code-review
  Standards 轴判据；`memory-lifecycle` 已冻结测试不受影响。
- 零代码改动：纯契约文档变更。

## Non-goals

- 文档引用格式、注释元规则、AGENTS.md 交流语言与对话效率准则——
  归姊妹 change `governance-doc-rules`。
- `f_scaled`/`Frequency` 形态写入 api-contract——等 `frequency-class`
  落地成为既成事实后吸收。
- api-contract 中「阶段 N」旧措辞清理——归 `governance-doc-rules`
  的注释/文档门禁一并处理。
