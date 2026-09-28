# Proposal

## Why

阶段 0 复盘发现两类结构性问题：其一，文档按"文件"而非"受众"组织——
`CONTRIBUTING.md` 里塞满了 AI 执行约束（闸门、坑、反返工清单），人类贡献者
读到的有效信息被稀释，而 AI 又不会主动去翻散落在 4 个子 README 里的
Implementation notes / Gotchas（无人阅读即等于不存在）；其二，AI 被人工纠正后
没有反思机制，同类错误跨会话重复犯（阶段 0 同类纠正出现 2 次以上：关闸门求绿、
CI push-and-pray、自造命名等）。本 change 按受众重划文档归属，并建立
lessons-learned 纠错账本，使"被纠正一次"变成"永不再犯"。

## What Changes

- 新建 `openspec/specs/lessons-learned/` 纠错账本：机制 spec + `INDEX.md`
  一行一条索引 + 按 scope 分片小文件（ci/core/python/typescript/docs/
  testdata，单文件 ≤50 行）；条目固定四要素（LL-NNN / scope / 犯过证据 /
  规则+复发检测）；首批收录阶段 0 人工纠正 + CONTRIBUTING 环境坑 + 4 个子
  README 的 Implementation notes / Gotchas（共 7 节）全部内容。
- `AGENTS.md` 新增反思铁律：动手前扫账本索引；被人工纠正当轮登记（已有同类
  条目 = 承认未遵守，无 = 新增 LL）；可门禁化的条目落进 `pnpm check`。
- `CONTRIBUTING.md` review 步骤由两轴扩为三轴（Standards × Spec × Lessons）。
- 环境坑（corepack 假死、Windows GITHUB_PATH、binaryen 整树、
  api.github.com 限流、utf-8 读取、pyo3 venv 三件套）全部入 lessons-learned
  账本（scope: ci/docs/python），不升格进宪法——宪法只留架构级铁律与元规则，
  操作性坑会随工具链演进失效，不得稀释宪法权威性。
- `CONTRIBUTING.md` 瘦身为纯人类开发者文档：保留 Quick start、Toolchain 表
  （任务→工具路由，版本现场查不写死）、六步循环人类视角、PR 约定；迁入根
  README 的 Repository layout 并扩展至全部顶层目录（含各目录一句话作用）。
- 根 `README.md` 删除 Repository layout 节，只留用户视角（是什么/为什么/License）。
- 各子 README（core/python/typescript/testdata）删除 Implementation notes 与
  Gotchas 节，只留本目录命令；内容迁入 lessons-learned 账本。
- 全仓清理历史遗留的无关链接（每篇文档只链自身作用域直接相关的文档）。
- `project-governance` spec 的「修订历史」节直接删除（不另建文件；
  追溯靠 `git log`，变更理由写进 Requirement 正文或 commit message）——
  spec 正文只留现行约束，降低每次必读的注入成本。
- 受影响铁律编号：无直接涉及（数据布局/精度/零拷贝等不动）；涉及治理原则
  "单一真相源"与"文档归位"的落点重划。

## Capabilities

### New capabilities

- `lessons-learned`: 纠错账本能力——条目格式、编号规则、登记时机（被纠正即
  登记）、复发检测（review 第三轴 + 可门禁化条目转 check 脚本）、账本为坑与
  实现决策的唯一汇集地。

### Modified capabilities

- `project-governance`: 新增元规则「文档受众分层」（README / CONTRIBUTING /
  specs / 账本各自承载内容与链接纪律）；复盘回写去向由"子 README Gotchas"
  改为"lessons-learned 账本"。

## Non-goals

- 不改 CI workflow 结构与任何构建/测试命令语义。
- 不引入新工具或依赖；账本机制靠现有校验脚本与文档约定。
- 不动七条铁律正文及 api-contract / workspace-layout / ci-matrix /
  zero-copy-roundtrip spec。
- 不建 `docs/agent-ops.md`（已否决：无独立受众价值）。

## Impact

- 文档：根 `README.md`、`CONTRIBUTING.md`、`AGENTS.md`、四个子 README、
  `openspec/specs/project-governance/spec.md`、新建
  `openspec/specs/lessons-learned/spec.md`。
- 门禁：`scripts/check_md.py` 或新增脚本承接可门禁化 LL 条目；`pnpm check:md`
  作用范围不变。
- 代码：不动。CI workflow：不动（仅文档引用的目标位置变化）。
- 无 BREAKING：纯文档/治理重构，无对外 API 与构建行为变化。
