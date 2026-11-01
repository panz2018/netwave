# Proposal: add-expert-blindspot-section

## Why

方案讨论存在"专家盲点"返工根因：人圈定的范围来自人已想到的东西，agent
按范围执行永远补不了"没人想到"的缺口。既有机制（实证原则 / 查现成做法 /
独立真值 + review 三轴 + CI）全部面向"别做错"，没有一条面向"主动补想少
的"。已定裁决（2026-10-31，Plan/方案讨论纪律.md #4-#7）：保留专家盲点
追问①"顶尖专家会做哪些我没要求的事"，落点两处——讨论过程（软约束，
AGENTS.md 另行直改）与 proposal.md 固定小节（硬闸门，本 change）。

## What Changes

- `openspec/config.yaml` `rules.proposal` 新增一条：proposal.md 必须含
  `## 专家增补` 节，**内容可为空**（空或"无"合法）。
- `scripts/check_proposal.py` 门禁扩展：在途 proposal 缺 `## 专家增补` 节
  即红；节非空时每条增补须含具体指涉（反引号标识符 / 仓库内文件路径 /
  URL），纯泛谈行视为注水即红。
- governance spec 把既有元规则 Requirement「提案工件必带出处与不做清单」
  改名合并为「提案工件必带三节」（Non-goals / Prior art / 专家增补），与
  config.yaml、check_proposal.py 三者同口径（软提示与硬闸门不脱节）。
  不另起新 Requirement——同一门禁的多节要求合为一条，避免重复正文。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `project-governance`: 元规则「提案工件必带出处与不做清单」改名合并为
  「提案工件必带三节」——proposal 必带 `## 专家增补` 节（存在性硬、
  内容可空、非空须具体），门禁化于 `check_proposal.py`。

## Impact

- `openspec/config.yaml`（rules.proposal 加一条软提示）
- `scripts/check_proposal.py`（REQUIRED 扩展 + 注水判定；`pnpm check:meta`
  命令不变）
- `openspec/specs/project-governance/spec.md`（archive 时 sync delta）
- 既有在途 proposal：本 change 自身即首个受检对象；归档 change 不回溯
- 不涉及：产品代码、CI 步骤顺序、AGENTS.md（讨论位软约束另行直改，
  见 Non-goals）

## Non-goals

- 不改全局 grilling skill（`/config/.agents/skills/grilling/SKILL.md`）——
  上游一更新即丢失，且不得在他人项目乱改（已定裁决）。
- 不改 AGENTS.md——讨论过程追问①属软约束，一句话直改，不占本 change。
- 不强制增补内容非空——空节合法，闸门只查存在性与非空时的具体性。
- 不校验增补的语义质量（是否真是专家级）——语义归 review，闸门只判结构。

## Prior art

- `scripts/check_proposal.py`——本仓既有 Non-goals / Prior art 双节门禁，
  专家增补节沿用同一框架与"空/声明合法出口"惯用法（无现成方案的诚实
  出口同构）。
- 同生态：spec-driven 提案模板普遍含 Risks / Open Questions 类自由节
  （如 OpenSpec CLI 自带 proposal 模板），本仓以门禁化方式偏离——
  理由：不可核验的提醒位会静默失效。

## 专家增补

- `check_proposal.py` 的 `section_body` 对空节返回空列表而非 None，
  实现"存在但可空"判定时注意与既有"空节即红"分支（Non-goals /
  Prior art）区分，否则新节会被旧逻辑误杀或旧节被新逻辑放水。
