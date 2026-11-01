# Design: add-expert-blindspot-section

## Decisions

- **D1（#4）**：专家盲点四问只留①"顶尖专家会做哪些我没要求的事"，弃
  ②原始素材、③方法工具、④独立证明——后三条与既有机制重复（实证原则 /
  查现成做法 / 独立真值 + review 三轴 + CI）。
- **D2（#5）**：落点两处：讨论过程每轮追问（软约束，AGENTS.md
  「对话效率」直改，不在本 change）+ proposal.md `## 专家增补` 固定节
  （硬闸门，本 change）。讨论是决策主战场，proposal 节是决策的执行记录。
- **D3（#6）**：空节合法——专家增补是提醒位不是必答题；非空时每条须含
  具体指涉（反引号标识符 / 仓库内文件路径 / URL），指不到即注水红。
- **D4（#7）**：取消"建议增补（不在本次授权内）"特殊措辞——讨论与提问
  天然不是执行动作，不涉越权，无需标签自保；授权边界由 AGENTS.md
  动词铁律与动词复述条统一管。
- **D5**：不改全局 grilling skill——上游更新即丢失、不得在他人项目乱改；
  项目内要求落 AGENTS.md（netwave 生效）。

## Changes

- `scripts/check_proposal.py`：`REQUIRED` 扩为三节；`## 专家增补` 走独立
  判定分支——空/「无」放行，非空逐行查具体指涉（复用 `CITATION` 正则，
  扩展反引号 token 匹配）。Non-goals / Prior art 判定不动。
- `openspec/config.yaml`：`rules.proposal` 增加与脚本同口径一条。
- 判定顺序：缺节 → 红；空节 → 绿；非空含无指涉行 → 红（`::error::`
  指明文件与行号）。

## Migration

无数据迁移。闸门落地当日：本 change 自身 proposal 已含合规节，其余在途
为零，`pnpm check:meta` 绿；归档 change 不回溯。
