# Proposal

## Why

现有闸门（`pnpm check` 机械判据、review 三轴、`check:outdated`）都只覆盖
"可机械判定"或"本次改动面"：常驻文档里的死条款与环境漂移、无引用的孤儿
文件、规则跨文件重复冲突、账本里可门禁化却未落闸门的条目、Plan/ 过期条目
等**存量问题**没有任何自动发现通道，过去全靠人工指出（案例：`AGENTS.md`
corepack 死条款由另一项目核对时才发现，见 `Plan/工具链核对.md`）。本
change 把"全项目只读体检"挂到 archive 钩子，让 AI 在每次归档时自发现
存量不足，人只圈定执行，减少人肉审查负担。

## What Changes

- `openspec/config.yaml` 的 `operations.archive.guidance` 新增一条：只写
  触发句 + 指针（归档完成后执行 `archive-health-check` spec 规定的五维
  只读体检），不复述规则本体——config.yaml 每次注入，复述即双正文漂移，
  出处信息浪费 token，追溯靠 git log。
- 体检五维度：①文档断言 vs 环境实测 ②死代码/孤儿文件 ③规则重复/冲突
  ④可门禁化 LL 未落闸门 ⑤Plan/ 过期；每维度必须给结论（无发现写"已查，
  无"），查完即终止。
- 动作边界 = 两段式：扫描阶段只读、不改任何被检文件，凡只读命令可当场
  验证的必须当场跑并标"已实证"；发现由主代理汇总后写入 `Plan/`（Plan/ 是
  体检的输出载体，不受扫描只读约束）；修复永远等人工点名。
- 三级去重：命中 lessons-learned INDEX 不报；命中现有 Plan/ 条目不写新
  文档；对 Plan 条目有补充由主代理直接写进旧 Plan 文件（归属一处，届时
  一起处理）；仅全新发现写入 `Plan/体检-<日期>.md`。子代理只返回发现。
- 输出约束：每维度 ≤2 条（各维独立执行，五维天然 ≤10），不设全文上限
  （跨维截断与禁止跨维重排序矛盾），超出本维报计数；每条附文件+行号+证据，
  无证据不写；发现分级"硬/待拍板"；按维度分组、不做跨维度重排序。
- 硬伤醒目标注：体检不阻塞归档——归档本职（sync 核对与目录移动）先完成，
  体检为收尾附加；"硬"级（违反现行 spec/铁律或闸门口径矛盾）在汇报置顶
  并在写入 Plan/ 时标注"硬"供优先处置，"待拍板"级正常列出。本次 change
  引入的违规不进体检报告，直接走三轴打回。
- 机制移植自 `code-review` skill：每维度 fresh-context 子代理并行（无子
  代理能力则降级为逐维度顺序执行）、单报告字数上限、硬违规 vs 判断题
  分级、闸门已覆盖项不报、前置校验失败即停；Fowler 坏味道基线不搬
  （diff 尺度检查表，不适配全项目存量扫描）。
- 无人工点名入口：整体体检只在归档自动执行；平时的改动面审查走
  `/code-review` skill（diff 尺度），不重复建设。
- 审查时点补全（同一 change 顺带接线，各审自己那一步的产出）：
  `rules.proposal` 新增"全部工件完成后 MUST 工件自洽审"（proposal↔delta↔
  design↔tasks 互查矛盾/超限/与 governance 口径冲突，硬伤清零才算提案完成）；
  `rules.tasks` 与 `operations.apply.guidance` 双写"apply 倒数第二步（
  `check:outdated` 之前）MUST 按 governance「元规则 review 三轴」对照工件审
  实现 diff，硬伤清零才准入最后一项 `check:outdated`"。

## Capabilities

### New Capabilities

- `archive-health-check`: 归档完成后全项目只读体检——触发时机、五维度清单、
  扫描只读边界与当场实证、三级去重、输出格式与上限、硬伤醒目标注。

### Modified Capabilities

（无——不改既有 spec 的 Requirement；`config.yaml` 既有 archive"Plan/
瘦身"条只覆盖本 change 相关条目，新条覆盖全项目存量，两条并存互不修改。
propose/apply 出口的审查要求属流程 guidance/rules，其判据真相源仍是
governance spec「元规则 review 三轴」，本 change 只接线不重述。）

## Impact

- 配置：`openspec/config.yaml`（`operations.archive.guidance` 新增一条；
  `rules.proposal` 新增工件自洽审一条；`rules.tasks` 与
  `operations.apply.guidance` 各新增三轴审 diff 一条）。
- 文档产物约定：`Plan/体检-<日期>.md` 新文件形态（消化完删除，符合
  Plan/ 生命周期终态）。
- 代码：零改动——不新增门禁脚本、不进 CI、不进 `pnpm check`。
- 受影响元规则：governance spec「元规则 最小规则原则」（复用既有 archive
  钩子、不造第二套判定、不新增命令）与「元规则 规则生命周期」（新能力
  归层为能力 spec，`config.yaml` 只留注入用 guidance）。

## Non-goals

- 不做人工点名触发的整体体检入口——平时整体检查已做得足够多，diff 审查
  走 `/code-review` skill 即可。
- 不修复任何东西——扫描阶段只读，发现只落 Plan/；修复永远等人工点名后走
  正常授权流程。
- 不搬 Fowler 坏味道基线——diff 尺度检查表用于全项目会爆量，per-change
  坏味道已由三轴 Standards 轴覆盖。
- 不进 CI、不进 `pnpm check`——体检是 LLM 判断类审查，不是机械门禁。
- 不做跨维度全局重排序——维度分组呈现，防一个维度的噪音淹没另一维度硬伤。
- 条款不写出处——config.yaml 每次全量注入，出处无人阅读纯耗 token；追溯
  靠 git log 与本 change 归档工件。
- 不做时间戳/缓存/定时任务——触发频率由归档节奏天然决定。

## Prior art

- 仓库内现成实现：`openspec/config.yaml` 的 `operations.archive.guidance`
  钩子机制已存在（archive 时自动注入），本 change 复用接线而非新造钩子；
  `openspec/specs/lessons-learned/INDEX.md` 与 `Plan/` 现有文件即三级去重
  的比对对象，不造第二套账本。
- `/config/.agents/skills/code-review/SKILL.md`——双轴并行子代理、字数上限、
  硬违规 vs 判断题分级、"闸门已强制的不报"、不跨轴重排、前置校验即停等
  机制直接移植；其 diff 尺度与坏味道基线部分偏离不用（理由见 Non-goals）。

## 专家增补

- `scripts/check_md.py` 的 SPECS ROUTER 门禁随新能力 spec 目录
  `archive-health-check` 落地同轮更新 `openspec/specs/README.md` 路由表，
  防路由缺项打红（LL-034 波及面同步）。
- 体检五维度中④"LL 未落闸门"与 `openspec/specs/project-governance/spec.md`
  「元规则 review 三轴」的"可门禁化 LL 落闸门"判据同源，条款措辞直接引用
  该 Requirement 名而非重述判据，防两处正文漂移。
- `Plan/体检-<日期>.md` 文件名带日期而非滚动覆盖，使"消化一条删一条"有
  明确文件生命周期，与 `openspec/config.yaml` archive"Plan/ 瘦身"检查的
  grep 对象兼容。
