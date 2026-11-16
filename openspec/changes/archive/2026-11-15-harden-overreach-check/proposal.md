# Proposal

## Why

LL-098 已规定"提交前逐行回看 `git diff`、对不上即越权停手"，但事故实际发生在
某一轮内部、根本没走到提交那一步——检查时点钉在"提交前"，触发条件在事故场景里
从未满足。同时该条"复发检测"仍写"核对 commit diff 是否 ⊆ 该轮点名范围"，而"该轮
点名范围"只存在于对话原话、不可追溯，规则正文与检测口径漂移。本 change 把检查
时点提前到每轮必到的"写总结前"，并把点名范围具体化为可追溯工件，使已有规则真正
可执行，而非再加一条重复的软约束。

## What Changes

- 修订 LL-098 规则③：检查时点由"提交前"改为"写总结前"，触发条件为"本轮发生过
  写操作"（只读问答轮免检）。
- 修订 LL-098 复发检测行：点名范围具体化为"apply 态 = 本 change 的 `tasks.md`，
  对话态 = 人工该轮原话点名的文件"，消除"该轮点名范围"的不可追溯表述。
- 给 LL-098 补"不可门禁化原因"留痕：点名清单非机器可读输入，脚本无法独立判定
  范围外文件（满足 lessons-learned spec「不可门禁化留痕」Scenario）。
- 具体化 `openspec/config.yaml` apply review 步措辞：在已有"对照本 change 工件审
  实现 diff"那条上补"diff 文件集逐文件对上 `tasks.md`，对不上即越权、停手还原"，
  不新增步骤、不另起条目。
- `AGENTS.md`「动词复述」条加指针"收尾对账见 LL-098"，使前闸（动手前复述）与
  后闸（写总结前对账）在常驻准则里互相可见。

## Capabilities

### New Capabilities

（无新增能力。）

### Modified Capabilities

（无 spec 级 Requirement 变更：本 change 改的是 lessons-learned 账本条目 LL-098
的正文措辞、`openspec/config.yaml` 的 apply 流程钩子措辞与 `AGENTS.md` 指针，
lessons-learned spec 的 Requirement（登记/扫描/三轴/门禁化/退役机制）本身不变，
故 `.openspec.yaml` 设 `skip_specs: true`，不产出 specs delta。）

## Impact

- `openspec/specs/lessons-learned/workflow.md`：LL-098 规则③与复发检测行措辞。
- `openspec/config.yaml`：`operations.apply.guidance` 中 review 那条措辞。
- `AGENTS.md`：「动词复述」条加一句指针。
- `Plan/防越权机制-2026-11-14.md`：归档时整档删除（结论吸收进账本与 config）。
- 不涉及产品代码、API、依赖、CI 构建顺序；无 BREAKING。

## Non-goals

- 不新增常驻规则条目（基线=只修订 LL-098，遵守 governance 元规则「最小规则原则」
  与 LL-076）。
- 不做脚本硬闸（`check_tasks_diff.py` 之类）：点名清单非机器可读输入，且 agent
  可中途改 `tasks.md` 自证合法，性价比不成立。
- 不为越权单列 LL 触发词或新增 scope 列（`INDEX.md` 三列格式不动）。
- 不永久删除或放宽 archive 态 health-check 规则（本会话仅一次性跳过，规则原地
  保留）。

## Prior art

- 仓库内 `openspec/specs/lessons-learned/workflow.md` LL-098（本 change 修订对象）。
- 仓库内 `openspec/specs/project-governance/spec.md`「元规则 最小规则原则」「元规则
  review 三轴」（约束本 change 不得新增重复条目、须门禁化优先）。
- 仓库内 `openspec/specs/lessons-learned/spec.md`「可门禁化条目转 check 脚本」
  Scenario「不可门禁化留痕」（要求补留痕句）。

## 专家增补

- 给 `AGENTS.md`「动词复述」条加"收尾对账见 LL-098"指针：前闸与后闸在常驻准则
  互不可见时，动手只看见前闸、易忘后闸；加指针使两道闸互相引用，属加指针非加规则。
- 同步修订 `openspec/specs/lessons-learned/workflow.md` LL-098 复发检测行口径
  （见 What Changes 第 2 条）：规则正文时点提前后，检测方式若仍写"提交前"即两份
  表述漂移（LL-076），须同轮改到一致。
