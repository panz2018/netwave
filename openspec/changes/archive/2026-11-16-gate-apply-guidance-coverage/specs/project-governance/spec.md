# Spec Delta

## ADDED Requirements

### Requirement: 元规则 apply guidance 收尾覆盖门禁

`openspec/config.yaml` 的 `operations.apply.guidance` 每条 MUST 携带一个
锚点词（该条的机器可查标识）。在途 change（`openspec/changes/<name>/`，
不含 `archive/`）的 `tasks.md` MUST 逐条覆盖全部 guidance 锚点：每条锚点
至少出现在一个打勾任务行（`- [ ]` 或 `- [x]`）中。判定只查存在性、不数
次数——锚点在正文其他位置重复出现不影响判定；散文行（非打勾任务行）含
锚点不算覆盖。人工裁决跳过某条 guidance 时，MUST 写成打勾任务行并含该
锚点、"跳过"字样与 ISO 日期（`YYYY-MM-DD`），此为合法出口——闸门只拦
静默漏抄，不推翻人工裁决。本规则 MUST 门禁化：`scripts/check_proposal.py`
（命令 `pnpm check:meta`）执行上述校验，缺哪条锚点即红并指名该条；
已归档 change 不回溯校验——历史不改写。无在途 change 时视为通过。

#### Scenario: 静默漏抄即红

- **WHEN** 在途 change 的 `tasks.md` 没有任何打勾任务行含某条 guidance
  的锚点词
- **THEN** `pnpm check:meta` 失败（`scripts/check_proposal.py` 命中报告，
  `::error::` 指明 change 名与缺失的锚点词）

#### Scenario: 明示跳过合法

- **WHEN** `tasks.md` 某打勾任务行同时含某锚点、"跳过"字样与 ISO 日期
  （如 `- [ ] 7.3 apply 态体检：经人工裁决跳过（2026-11-16）`）
- **THEN** `pnpm check:meta` 通过——该条视为已覆盖，裁决留痕在任务行内

#### Scenario: 散文提及不算覆盖

- **WHEN** 某锚点词只出现在 `tasks.md` 的非打勾行（标题、说明散文、
  Workflow follow-up 圆点）
- **THEN** `pnpm check:meta` 失败——覆盖判定只认打勾任务行

#### Scenario: 多次提及不加分也不报错

- **WHEN** 同一锚点在打勾任务行出现多次（一条 guidance 拆成多条任务，
  或锚点词在别处被顺带提及）
- **THEN** `pnpm check:meta` 通过——判定为存在性，非计数相等

#### Scenario: 归档不回溯

- **WHEN** change 归档进 `openspec/changes/archive/`
- **THEN** 其 `tasks.md` 退出扫描范围，闸门不因旧文件缺锚点任务而红
