# Design

## Context

见 `proposal.md` 的 Why。当前状态：坑与实现笔记散在 4 个子 README（7 节）与
CONTRIBUTING 的 Environment gotchas；反返工清单在 CONTRIBUTING；AI 行为准则在
AGENTS.md（每次对话自动注入）；硬约束在 project-governance spec。脚手架归档
后人工纠正仍反复出现，说明"写进文档"≠"被读到"。

## Goals / Non-Goals

**Goals:**

- 每类信息有唯一、受众明确的归宿；AI 侧信息集中在自动注入路径可达处。
- 纠错账本生而有用：首批条目来自已发生的纠正，非空壳。
- 迁移后全仓链接零断链、零无关链接（`pnpm check:md` + 人工抽查）。

**Non-Goals:**

- 不改 CI workflow 结构、不改任何构建/测试命令语义。
- 不引入新工具/依赖（账本机制靠现有 markdownlint/check_md.py + 约定）。
- 不动七条铁律正文与 api-contract / workspace-layout / ci-matrix /
  zero-copy-roundtrip spec。

## Decisions

1. **账本按 scope 分片 + INDEX 入口**：机制（Requirement/Scenario）进
   `spec.md` 走 openspec 生命周期；条目是只增数据，按 scope 分小文件
   （ci/core/python/typescript/docs，单文件 ≤50 行）+ `INDEX.md` 一行一条
   索引；AI 先扫 INDEX（永远便宜）再按需打开分片。备选：单文件
   ledger.md——否决，条目只增必长成巨型文件，检索与注入成本失控；条目直接
   写 spec 正文——否决，spec 是行为契约，流水会稀释权威性且归档 churn 大。
2. **条目格式固定四要素**（LL-NNN / scope / 犯过证据 / 规则+复发检测），
   编号只增不复用；scope 即分片文件名，新增条目只碰一个小文件 + INDEX 一行。
3. **AGENTS.md 加反思铁律（短指针）**：动手前扫 INDEX.md、被纠正即登记、
   review 三轴。AGENTS.md 每次注入，是 AI 侧唯一可靠触达点；正文保持数行
   （含文档地图，全文件目标 ≤60 行），细节指向 lessons-learned。备选：只放
   CONTRIBUTING——否决，CONTRIBUTING 不注入，AI 不主动读。
4. **三层归位判据（变更级别）**：宪法=契约级决定（改了它，已发布代码/跨端
   契约要跟着改）；AGENTS.md=行为准则（约束执行动作而非系统状态，含内容
   分配地图）；账本=事件级事实（某次失败换来的具体坑/决定，只增）。同一
   事实只存一层：原则→宪法，行为→AGENTS.md，事实→账本，执行→代码/门禁。
   宪法与 AGENTS.md 均有长度红线，超长即需下沉内容到下一层。
5. **环境坑全部进 ledger，不进宪法**：宪法只收架构级铁律与元规则（几乎
   永不变更）；操作性坑（utf-8、GITHUB_PATH、binaryen、限流、非交互化、
   pyo3 借用终态、maturin 缓存等）随工具链演进会失效，全部作为 LL 条目带
   scope 标签入 ledger，复发检测指向具体门禁命令。备选：升格进 governance
   spec——否决，稀释宪法层级与权威性，且与"账本为坑的唯一汇集地"矛盾。
6. **Toolchain 表留在 CONTRIBUTING 且去版本号**：任务→工具路由 + 验证命令，
   版本真相源是各锁文件/`rust-toolchain.toml`，文档不复制易变事实。
7. **可门禁化条目落 `pnpm check`**：优先扩展现有 `scripts/check_md.py`
   （如禁止子 README 出现 Implementation notes/Gotchas 标题、禁止指向
   archive/ 的链接），避免新脚本。

## Risks / Trade-offs

- [账本增长后注入成本上升] → 条目保持单行规则式；AGENTS.md 只要求扫索引，
  全文按需读取；门禁化一条即可从文字规则中退役一条。
- [迁移期间双写/漏迁] → tasks 按文件逐节迁移并当场删除源节，check_md.py
  断链校验兜底。
- [LL 命中判定主观] → 条目"复发检测方式"字段强制具体化；不可门禁化的才归
  review 人工比对。
- [governance spec 变长] → 新增 Requirement 仅一条聚合（跨平台脚本与 CI
  环境硬约束），场景化表达避免散文化。

## Migration Plan

纯文档迁移，无部署。顺序：先建账本并迁入首批条目 → 改 AGENTS.md/
CONTRIBUTING/README/子 README → 清链接 → `pnpm check:md` 全绿。回滚 = git
revert 单 PR。
