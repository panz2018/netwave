# Design

## Context

见 proposal.md - Why。约束来自 governance spec「元规则 最小规则原则」（动作边界
优于过程管束、新增规则先查重、仪式不入常驻）与 lessons-learned spec「可门禁化
条目转 check 脚本」「账本条目退役」。本 change 不写产品代码，只改三处常驻文档
措辞，故无数据模型、依赖、迁移复杂度。

## Goals / Non-Goals

**Goals:**

- 让 LL-098 的 diff 对账检查在每轮必到的节点触发，而非仅提交前。
- 让"点名范围"在 apply 态有可追溯落盘对照物（`tasks.md`）。
- 补齐 lessons-learned spec 要求的"不可门禁化原因"留痕。

**Non-Goals:**

- 不引入脚本闸门、不引入新 scope/触发词列、不新增常驻条目（见 proposal Non-goals）。
- 不改 lessons-learned spec 的 Requirement 本体（账本机制不变，仅条目内容变）。

## Decisions

### D1：修订 LL-098 而非新增条目

人工提议的"写总结前再查越权"实质已被 LL-098 ③ 覆盖。新增重复条目同时违反
governance「最小规则原则」Scenario「新增规则先查重」与 LL-076（同一知识两份清单
必漂移）。故选修订既有③的时点词，不另起条目。备选（新增独立 LL）否决：纯噪音。

### D2：检查时点"提交前"→"写总结前"，触发条件=本轮写过文件

事故发生在轮内、未到提交，"提交前"触发条件在事故场景永不满足。"写总结前"是每轮
必达节点。只读问答轮无 diff 可审，免检不削弱防护（LL-098 本就管写操作）。

### D3：点名范围具体化为可追溯工件

apply 态点名范围 = 本 change 的 `tasks.md`（提案定稿、人工批准、落盘可追溯）；
对话态 = 人工该轮原话点名的文件。原"该轮点名范围"措辞不可追溯，是检测口径漏洞。

### D4：放弃脚本硬闸（check_tasks_diff.py）

脚本判"范围外"需机器可读的点名清单。`tasks.md` 虽落盘，但：① 现有 tasks 不声明
文件路径，要改全部历史格式；② apply 流程强制产生 tasks 未列的副作用（`fix:md`
改格式、`check:outdated` 改 lockfile、Plan/ 删除、INDEX 同步、spec sync），严格
比对天天误红，需维护豁免白名单；③ agent 可中途改 `tasks.md` 使自身 diff 合法——
要堵还得加"tasks 批准后冻结"，规则又长回去。结论：脚本形态要么误红成噪音闸、
要么可自证绕过，零门禁价值。留 review 轴 + 人工提交授权兜底。

### D5：skip_specs 而非编造 lessons-learned delta

本 change 改的是账本条目正文（LL-098）、config 流程钩子措辞、AGENTS.md 指针。
lessons-learned spec 的 Requirement（登记/扫描/三轴/门禁化/退役）本身不变——
LL-098 是账本内容，不是 spec Requirement。无 spec 级行为变更，按 propose 指引
设 `skip_specs: true`，不编造 Requirement 凑校验。

### LL→去向映射（退役纪律留痕）

本 change 不退役任何 LL，仅修订 LL-098 正文。`Plan/防越权机制-2026-11-14.md`
终态整档删除，结论去向：LL-098（账本）+ `config.yaml` apply review 步 +
`AGENTS.md` 指针。该 Plan 内"LL-098 未提交"系过时事实，随整档删除消失，不单独修。

## Risks / Trade-offs

- [后闸仍是软约束，靠 agent 自觉] → 唯一硬闸是人工提交授权（commit 须人工点名）；
  后闸把"范围外文件"在人工看到前由 agent 自查还原，是减损而非拦截，与 D4 一致。
- [时点提前增加每轮开销] → 仅"本轮写过文件"才触发，只读轮免检；`git diff --stat`
  本地毫秒级，可忽略。
- [apply 态以 tasks.md 为准，但 tasks 可能写得粗] → review 轴判定时以"diff 文件
  能否追溯到某条任务意图"为准，非严格路径相等；粗 tasks 由 review 三轴 Spec 轴兜。

## Migration Plan

无部署/回滚：纯文档措辞修订，git revert 即回退。落地顺序见 tasks.md。

## Open Questions

无。所有影响范围与口径的决策已在 D1–D5 定。
