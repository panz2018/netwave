# project-governance Specification Delta

## ADDED Requirements

### Requirement: 元规则 提案工件必带专家增补节

在途 change 的 `proposal.md` MUST 含 `## 专家增补` 节。存在性硬、内容可空：
节缺失即红；节为空或仅写「无」合法（诚实无增补是合法出口）。节非空时
每条增补 MUST 含具体指涉——反引号标识符、仓库内文件路径或 URL 之一，
指不到本任务具体文件/接口/测试名的泛谈行视为注水即红。无在途 change 时
视为通过。已归档 change 不回溯校验——历史不改写。本规则 MUST 门禁化：
`scripts/check_proposal.py`（命令 `pnpm check:meta`）扫描在途 proposal，
零豁免；`openspec/config.yaml` 的 `rules.proposal` 与本脚本判定字面严格
一致，软提示与硬闸门不脱节。增补的语义质量（是否真是专家级发现）归
review，不属门禁。

#### Scenario: 缺节即红

- **WHEN** 在途 `openspec/changes/<name>/proposal.md` 缺 `## 专家增补` 节
- **THEN** `pnpm check:meta` 失败（`::error::` 指明文件与缺失节名）

#### Scenario: 空节合法

- **WHEN** `## 专家增补` 节为空或仅写「无」
- **THEN** `pnpm check:meta` 通过——闸门查存在性，不强制有内容

#### Scenario: 注水即红

- **WHEN** `## 专家增补` 节非空，且某条增补不含反引号标识符、仓库内
  文件路径或 URL（泛谈无具体指涉）
- **THEN** `pnpm check:meta` 失败——每条增补须指到本任务的具体文件 /
  接口 / 测试名

#### Scenario: 归档不回溯

- **WHEN** change 归档进 `openspec/changes/archive/`
- **THEN** 该 proposal 退出扫描范围，闸门不因旧文件缺新节而红
