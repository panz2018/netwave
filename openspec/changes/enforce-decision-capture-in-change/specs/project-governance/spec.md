# Spec Delta

## ADDED Requirements

### Requirement: 元规则 决定捕获进 change

讨论中拍板的每个决定 MUST 当场写入在途 change（`openspec/changes/<name>/`，
不含 `archive/`）的 `proposal.md` 之 `## 已定裁决` 段，逐条以反引号包裹的
关键词标识；该段 MUST 存在且非空。每个关键词 MUST 在 `tasks.md` 至少有一个
含同关键词的任务行，使决定具备 apply 执行载体。本规则 MUST 门禁化于
`scripts/check_proposal.py`（命令 `pnpm check:meta`），缺则红并指名缺的关键词；
已归档 change 不回溯校验。本规则取代旧裁决"琐碎文档修复直接改、不新开 change"。

#### Scenario: 决定无任务载体即红

- **WHEN** 在途 change 的 `proposal.md` 某关键词在 `tasks.md` 没有任何含
  同关键词的任务行
- **THEN** `pnpm check:meta` 失败（`scripts/check_proposal.py` 命中报告，
  `::error::` 指明 change 名与缺载体的关键词）

#### Scenario: 已定裁决段缺失或空即红

- **WHEN** 在途 change 的 `proposal.md` 没有 `## 已定裁决` 段，或该段无任何
  反引号关键词条目
- **THEN** `pnpm check:meta` 失败——该段必须存在且非空，不设"写无"出口

#### Scenario: 扩容或新开合法

- **WHEN** 决定与当前在途 change 不同主题域，或当前无在途 change
- **THEN** 先尝试扩容当前 change；不强塞，塞不下则新开 change 承载——两种落笔
  方式均合法，闸门只要求最终每个关键词在其所属 change 内有任务载体

#### Scenario: apply 中途追加决定

- **WHEN** apply 进行中拍板了新决定
- **THEN** 当场追加进 `## 已定裁决` 段并补对应任务行；收尾复查每个关键词任务
  已打勾，未打勾即红——防迟到决定蒸发

#### Scenario: 归档不回溯

- **WHEN** change 归档进 `openspec/changes/archive/`
- **THEN** 其 `proposal.md`/`tasks.md` 退出扫描范围，闸门不因旧文件缺已定裁决
  段而红——历史不改写
