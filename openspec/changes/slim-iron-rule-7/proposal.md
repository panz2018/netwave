# Proposal

## Why

铁律七「覆盖率 100% 硬约束」里塞了 llvm-cov 的工具机制解释：`--codecov` 走
cargo-llvm-cov 行合并器的 OR 语义、默认 `llvm-cov report` 按实例分别计数、
"实测 `--codecov` 950/950=100%，同数据 `report` 恒差 6 行"。按
[文档受众分层元规则](../../specs/project-governance/spec.md#requirement-元规则-文档受众分层)，
这类"工具行为 + 实测证据"属第③层事件级事实，MUST 只入 lessons-learned 账本；
宪法只该留契约句与指针。

更关键的是**这段内容账本里已经有了**：`openspec/specs/lessons-learned/core.md`
的 LL-057 完整持有同一事实，且比宪法版本更详尽（额外含 `--fail-under-lines`
不读 codecov 输出的上游源码实证与阈值实测）。也就是说宪法当前违反"同一事实
MUST NOT 跨层重复"——本次是删重复副本，不是搬家，账本一个字不用新写。

## What Changes

- **宪法瘦身（MODIFIED）**：`project-governance` 铁律七删除工具机制解释段
  （OR 合并语义原理、按实例计数机制、950/950 与恒差 6 行的实测数字），
  改为契约句 + 指向 LL-057 的指针。
- **保留的契约（逐字不动）**：覆盖率按 crate/包归属各自度量、MUST NOT 用默认
  `report` 路径做 100% 闸门、MUST NOT 用 `--workspace` 把绑定 crate 的 core
  副本并入 core 度量；三个 Scenario（未测代码即红 / 豁免逐条标注 / 跨 crate
  重复计数即红）原样保留。
- **账本零改动**：LL-057 已完整覆盖被删内容，不新增、不改写、INDEX 不动。
- **落点判定收口（Q5）**：迁出细节只有两个既有去向——工具原理/踩坑→
  lessons-learned 账本，配置级细节→CONTRIBUTING.md；**不新建 `docs/` 目录**。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `project-governance`: 铁律七「覆盖率 100% 硬约束」Requirement 修改——度量
  归属与两条禁令保留为契约，工具合并语义与实测证据移出宪法、只存账本 LL-057。

## Impact

- 文档：`openspec/specs/project-governance/spec.md`（随归档 sync）。
- 不涉及：账本（LL-057 现成）、`AGENTS.md`、`CONTRIBUTING.md`、根
  `package.json`、CI、`scripts/coverage_gate.py`、任何 core/绑定代码与
  容差 manifest——闸门命令与判定逻辑一行不改，只改宪法正文的表述层次。
- 变更级别：governance 文档类（内容归位），不改覆盖率契约语义、不改阈值、
  不改 CI 行为。

## Non-goals

- 不做宪法拆分（治理 spec 与工程契约分两本）——铁律编号被账本/review 三轴/
  config.yaml/各 change 大量引用，编号迁移是最高级变更，另立项。
- 不新建 `docs/` 目录，不改 AGENTS.md 文档地图。
- 不改覆盖率阈值、闸门命令、豁免机制或任何 CI 步骤。
- 不新写/不改写 lessons-learned 账本条目（LL-057 已完整）。
- 不动铁律七的三个 Scenario 与其余铁律正文。
