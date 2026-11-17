# Proposal

## Why

`openspec/config.yaml` 的 `operations.apply.guidance` 规定了 apply 收尾必做的
五步（Plan/ 瘦身、specs 三态时效、三轴 review、apply 态体检、check:outdated
消化），LL-104 要求写 `tasks.md` 时逐条映射为收尾任务——但该防复发判据
（"收尾任务数 = guidance 条数"）仍靠 review 自觉，且实测不成立：一条
guidance 可拆成多条任务、流程固定动作另计，条数天然对不上（催生 LL-104 的
change 自身 guidance 五条对收尾四任务）。漏抄只能靠人工追问发现，须机器强制。

## What Changes

- `openspec/config.yaml`：`operations.apply.guidance` 每条加一个锚点词
  （`Plan/`、`三态时效`、`三轴`、`体检`、`check:outdated`），锚点即该条的
  机器可查标识；`rules.tasks` 加一条：写 `tasks.md` 时收尾任务 MUST 逐条
  覆盖 guidance 锚点，明示跳过者写成打勾任务行（含锚点 + 跳过 + 裁决日期）。
- `scripts/check_proposal.py`：新增"guidance 锚点覆盖"校验——对在途 change
  的 `tasks.md`，逐条 guidance 检查是否存在含该锚点的打勾任务行
  （`- [ ]` / `- [x]`），只查存在性不数次数，缺哪条报哪条；只扫在途
  change，归档不回溯（与既有三节门禁同口径）。
- `openspec/specs/lessons-learned/workflow.md`：LL-104 复发检测句从"review
  Standards 轴数条数"改为"由 `scripts/check_proposal.py` 机器强制"。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `project-governance`: 新增元规则——在途 change 的 `tasks.md` 收尾任务 MUST
  逐条覆盖 `openspec/config.yaml` apply guidance 锚点，门禁化于
  `scripts/check_proposal.py`，明示跳过为合法出口。

## Impact

- `openspec/config.yaml`（guidance 加锚点 + rules.tasks 加一条）
- `scripts/check_proposal.py`（新增校验，TDD：先 red 后 green）
- `scripts/tests/test_check_proposal.py`（新建或扩展单测）
- `openspec/specs/lessons-learned/workflow.md`（LL-104 复发检测句改口径）
- CI 无需改：`check_proposal.py` 已在 `pnpm check:meta` 内、`check:meta`
  已在 CI 闸门链

## Non-goals

- 不改 `operations.apply.guidance` 五步的语义与顺序，只加锚点词。
- 不校验任务正文质量（锚点在即视为覆盖，语义归 review）。
- 不回溯校验已归档 change（`openspec/changes/archive/` 不改写历史）。
- 不动 `check_ci.py`、`check_py.py` 等其他闸门脚本。

## Prior art

- 同仓先例：`scripts/check_proposal.py` 既有"三节存在性"门禁（governance
  spec「元规则 提案工件必带三节」）——本 change 复用同一脚本、同一
  "存在性硬校验 + 归档不回溯"口径，仅新增一类判据。
- 同仓先例：`scripts/check_py.py` 规则 4（LL-105 落闸门，随 change
  `drain-stray-profraw-in-tests` 落地）——LL 转机器闸门的既有路径。

## 专家增补

- 锚点词选定后 MUST 用在途真实 change 实测一轮再定稿，防 LL-108 同族
  （夹具臆造致闸门假绿）：`tasks.md` 夹具取自本 change 自身与
  `openspec/changes/archive/2026-11-15-drain-stray-profraw-in-tests/tasks.md`
  的真实收尾行。
- 跳过声明的日期格式钉死为 ISO（`2026-11-16`），与 health-check spec 的
  `Plan/体检-<日期>.md` 命名同族，防"跳过"无日期成免死金牌。
