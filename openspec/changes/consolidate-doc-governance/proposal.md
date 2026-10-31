# Proposal

## Why

规矩文档正在自我膨胀：同一事实存 2-3 份正文（Plan/ 生命周期三处、review 三轴两处、
"动词即授权"三处），且受众分层的设计前提是"人也读这些细节"——实际人不读不写，
全部规矩的受众是 AI。规则越多，AI 遵守每条的能力越低（官方实证：最小信息集优于
穷举清单），本仓 63 次人工纠正里"越权执行"与"绕回已定裁决"两类恰恰都靠加规则
没能治住。现在把受众、正文归属、退役机制一次收敛，让护栏少而硬。

## What Changes

- **受众重定义**：全部规矩文档受众 = AI；人的职责 = 决策方向 + 点名执行，
  不读细节、不写账本。文档地图由"人类开发/子目录/用户"三层改为
  **AI 必读区 / 人只看区**两区。
- **AGENTS.md 新增硬护栏正文**（动词=授权全集、"研究/探讨/该不该"只出文字、
  "实施"≠改代码、已定裁决=已授权、闸门自动跑、不确定必须问、找事实归 agent
  拍板归人），吸收并取代原「指令动作穷尽」条目。
- **governance spec 新增元规则「最小规则原则」**：规矩文档追求最小信息集、
  通用指令优于手写步骤、可门禁化的文字规则退役、程序性仪式不入常驻准则，
  附 Anthropic 一手出处链接。
- **governance spec 新增元规则「review 三轴」**：Standards × Spec × Lessons
  宪法化（原正文在 CONTRIBUTING，执行者是 AI，归 AI 必读区）。
- **governance spec 改写元规则「文档受众分层」**：三层受众改为两区；
  Plan/ 生命周期正文唯一落 `openspec/config.yaml`（执行钩子所在），
  AGENTS.md 与 CONTRIBUTING 只留指针。
- **CONTRIBUTING.md 变薄门面**：只留目录一览 + 人可能亲手敲的命令速查；
  六步循环与 review 三轴迁 governance spec，工具链表压成指针
  （版本以 lockfile / `rust-toolchain.toml` 现查为准）。
- **AGENTS.md 瘦身**：「Plan/ 生命周期」「文档书写规范」两节退役为指针
  （后者已由 `check_md.py` 门禁化）；「反思铁律」「对话效率」压成短句 + 账本指针。
- **`Plan/方案讨论纪律.md` 删已转正部分**：硬护栏与最小规则原则两节改为指针，
  只留 8 项待讨论清单。
- **账本 LL-070 只留事故证据**：规则正文归 AGENTS.md 硬护栏，消除三处副本。
- **新建 `Plan/账本退役审计.md`**：登记 INDEX 72 条逐条标去向的待办与判据
  （已铁律化 / 已门禁化 / 一次性环境事实三类退出扫描面），本次不执行。

## Capabilities

### New Capabilities

（无——本次全部落在既有 capability 的 Requirement 层面）

### Modified Capabilities

- `project-governance`: 新增元规则「最小规则原则」与「review 三轴」；
  改写元规则「文档受众分层」为两区受众并钉死 Plan/ 生命周期正文归属。

## Impact

- 文档：`AGENTS.md`、`CONTRIBUTING.md`、`openspec/specs/project-governance/spec.md`、
  `openspec/config.yaml`、`Plan/方案讨论纪律.md`、
  `openspec/specs/lessons-learned/`（workflow 分片 LL-070 + INDEX 该行措辞）
- 代码/CI：无改动。铁律全部不动，门禁脚本不动；`check_md.py`、`check_comments.py`、
  `check_proposal.py` 需对新文档文本通过（零豁免扫描）
- 不受影响：根 README、各子项目 README、其余 spec capability
- 偏离说明：本地参考镜像表**不迁** `license-compliance`——治理 spec
  「教学式文档与类型标注」已把它钉在 CONTRIBUTING，迁移需连带改两处 spec，
  零收益（见 design.md）

## Non-goals

- 不执行 INDEX 72 条退役审计（只立 `Plan/账本退役审计.md` 待办，下次讨论）
- 不拍板 `Plan/方案讨论纪律.md` 里的 8 项细节（琐碎改动豁免、动词复述兜底、
  专家盲点追问落点与防注水、关闭口令形态等）
- 不动任何铁律（数据布局、TDD、容差、worker、覆盖率、API 命名等）
- 不改任何门禁脚本、CI 步骤、产品代码
- 不删除 CONTRIBUTING 的本地参考镜像表与许可红线（受众改为 AI，位置不变）
- 不改根 README 与子项目 README

## Prior art

- Anthropic, _Effective context engineering for AI agents_ — 主张"minimal set of
  information"与"do the simplest thing that works"，并明确否定把边缘情况一长串
  塞进提示词（"stuff a laundry list of edge cases… We do not recommend this"）：
  <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
- Anthropic, _Building effective agents_ — 最成功实现用简单可组合模式而非复杂框架：
  <https://www.anthropic.com/research/building-effective-agents>
- Anthropic, _Claude 4 best practices_ — "Prefer general instructions over
  prescriptive steps"：
  <https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices>
- 仓内既有同类收敛先例：`openspec/specs/project-governance/spec.md`
  「元规则 文档受众分层」（分层归位机制已存在，本次改其受众前提与层数）
