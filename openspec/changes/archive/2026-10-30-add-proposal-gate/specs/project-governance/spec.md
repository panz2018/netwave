# project-governance Specification Delta

## ADDED Requirements

### Requirement: 元规则 提案工件必带出处与不做清单

在途 change 的 `proposal.md` MUST 含 `## Non-goals` 与 `## Prior art` 两节
且有实质内容：Non-goals 节至少一条非空条目；Prior art 节至少一条非空条目，
且该条目含 URL、仓库内文件路径或「无现成方案」声明之一（纯套话不算出处）。
无在途 change 时视为通过。已归档 change（`openspec/changes/archive/`）不
回溯校验——历史不改写。本规则 MUST 门禁化：`scripts/check_proposal.py`
（命令 `pnpm check:meta`）扫描在途 proposal，缺节或空节即红，零豁免；
`openspec/config.yaml` 的 `rules.proposal` 与本脚本判定字面严格一致，
软提示与硬闸门不脱节。

#### Scenario: 缺节即红

- **WHEN** 在途 `openspec/changes/<name>/proposal.md` 缺 `## Non-goals`
  或 `## Prior art` 节，或节下无实质内容
- **THEN** `pnpm check:meta` 失败（`scripts/check_proposal.py` 命中报告，
  `::error::` 指明文件与缺失节名）

#### Scenario: 无先例走合法出口

- **WHEN** Prior art 节写明「无现成方案」及理由，不含 URL 或文件路径
- **THEN** `pnpm check:meta` 通过——零豁免针对的是缺节与空节，不针对
  诚实声明无先例

#### Scenario: 归档不回溯

- **WHEN** change 归档进 `openspec/changes/archive/`
- **THEN** 该 proposal 退出扫描范围，闸门不因旧文件缺新节而红
