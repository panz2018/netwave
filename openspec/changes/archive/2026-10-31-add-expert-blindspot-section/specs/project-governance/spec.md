# project-governance Specification Delta

## RENAMED Requirements

- FROM: `### Requirement: 元规则 提案工件必带出处与不做清单`
- TO: `### Requirement: 元规则 提案工件必带三节`

## MODIFIED Requirements

### Requirement: 元规则 提案工件必带三节

在途 change 的 `proposal.md` MUST 含 `## Non-goals`、`## Prior art`、
`## 专家增补` 三节。前两节 MUST 有实质内容：Non-goals 至少一条非空条目；
Prior art 至少一条非空条目且含 URL、仓库内文件路径或「无现成方案」声明
之一（纯套话不算出处）。`## 专家增补` 存在性硬、内容可空：节缺失即红，
节为空或仅写「无」合法（诚实无增补是合法出口）；非空时每条增补 MUST 含
具体指涉——反引号标识符、仓库内文件路径或 URL 之一，泛谈无具体指涉视为
注水即红。无在途 change 时视为通过。已归档 change
（`openspec/changes/archive/`）不回溯校验——历史不改写。本规则 MUST 门禁化：
`scripts/check_proposal.py`（命令 `pnpm check:meta`）扫描在途 proposal，
缺节即红，零豁免；`openspec/config.yaml` 的 `rules.proposal` 与本脚本判定
字面严格一致，软提示与硬闸门不脱节。增补的语义质量（是否真是专家级发现）
归 review，不属门禁。

#### Scenario: 缺节即红

- **WHEN** 在途 `openspec/changes/<name>/proposal.md` 缺 `## Non-goals`、
  `## Prior art` 或 `## 专家增补` 任一节，或前两节下无实质内容
- **THEN** `pnpm check:meta` 失败（`scripts/check_proposal.py` 命中报告，
  `::error::` 指明文件与缺失节名）

#### Scenario: 无先例走合法出口

- **WHEN** Prior art 节写明「无现成方案」及理由，不含 URL 或文件路径
- **THEN** `pnpm check:meta` 通过——零豁免针对的是缺节与空节，不针对
  诚实声明无先例

#### Scenario: 专家增补空节合法

- **WHEN** `## 专家增补` 节为空或仅写「无」
- **THEN** `pnpm check:meta` 通过——闸门查存在性，不强制有内容

#### Scenario: 专家增补注水即红

- **WHEN** `## 专家增补` 节非空，且某条增补不含反引号标识符、仓库内
  文件路径或 URL（泛谈无具体指涉）
- **THEN** `pnpm check:meta` 失败——每条增补须指到本任务的具体文件 /
  接口 / 测试名

#### Scenario: 归档不回溯

- **WHEN** change 归档进 `openspec/changes/archive/`
- **THEN** 该 proposal 退出扫描范围，闸门不因旧文件缺新节而红
