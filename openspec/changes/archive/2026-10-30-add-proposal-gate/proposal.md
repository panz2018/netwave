# Proposal: add-proposal-gate

## Why

「方案必须附现成出处、必须写清不做清单」目前一半靠 `openspec/config.yaml`
软规则（Non-goals，25/25 归档 proposal 已遵守但无机械强制），一半只在
`Plan/方案讨论纪律.md` 的纸面纪律里（Prior art，25 份归档 proposal 零落地）。
软规则挡不住偷懒：同一事实两处不一致正是账本反复记录的复发模式。本 change
把两条纪律焊成 CI 闸门，缺节即红。

## What Changes

- 新增 `scripts/check_proposal.py`：扫描在途 `openspec/changes/*/proposal.md`
  （排除 `archive/`——已归档是既成事实，不拿新规矩回头要求旧文件），断言
  每份含 `## Non-goals` 与 `## Prior art` 两节且有实质内容（判定见下方
  Prior art 节与 design.md）；无在途 change 时通过。
- 接入根 `package.json` 的 `check:meta`（CI 经 `pnpm check` 自动覆盖，
  ci.yml 不动）。
- `openspec/config.yaml` 的 `rules.proposal` 同步：Non-goals 措辞对齐、
  新增 Prior art 规则，与脚本判定字面严格一致（软提示与硬闸门不脱节）。
- `CONTRIBUTING.md` Quality gates 节加一行该闸门说明。
- `Plan/方案讨论纪律.md`：「两层分治与工件门禁」节结论已被闸门承接，
  按 Plan 生命周期删除该节（去向：本 change 的 spec 与脚本）。

## Prior art

- 本仓 `scripts/check_else.py`：同族单文件 Python 闸门骨架——docstring 写
  规则契约、`SKIP_DIRS` 排除构建产物、`::error::` 行输出、退出码 0/1；
  本脚本直接沿用该骨架。
- 本仓 `scripts/check_ci.py`：「软规则门禁化」先例（LL-037 把"test:* 必接
  CI"从文字变闸门），本 change 复刻其路径：脚本 + 挂 `check:meta` + 账本
  留痕。
- 本仓 `openspec/specs/project-governance/spec.md`「元规则 代码只写使用信息」：
  spec 正文点名脚本、Scenario 断言 `pnpm check:meta` 失败的既有契约写法，
  新 Requirement 沿用此格式。
- [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) CLI 1.13+：
  `openspec validate` 校验 change 结构（工件齐备、delta 格式），但不管
  Non-goals/Prior art 内容节——本闸门补其差集，不与其重叠。

## Non-goals

- 不校验 `design.md` / `tasks.md` / delta specs 的结构——只查 `proposal.md`，
  其余工件质量留 review 三轴。
- 不做出处权威性/内容质量校验——闸门只查结构存在 + 实质内容（含 URL、
  仓库内文件路径或「无现成方案」声明之一）；"业界通常如此"式套话过不了
  正则，但"链接是否权威"属语义判断，归 review。
- 零豁免——不设 skip 标记、白名单；真无先例走「无现成方案，理由 X」合法出口。
- 不修改任何已归档 proposal（含本 change 归档后的自己）——历史不改写。
- 不做 Rust/TS 侧对应门禁——`check_else.py` docstring 已说明该生态由编译器
  穷尽 match / review 覆盖，本闸门同理只管 Markdown 工件。
- 不实现 `Plan/方案讨论纪律.md`「专家盲点追问」节——其 4 个开放问题未拍板，
  是否加 `## Blind spots` 节另待裁决轮。

## Capabilities

### New Capabilities

（无——不新建 capability）

### Modified Capabilities

- `project-governance`：新增元规则 Requirement「提案工件必带出处与不做清单」
  （沿用「代码只写使用信息」的"规则 + 点名脚本 + Scenario 断言 check:meta
  失败"格式）

## Impact

- 新增 `scripts/check_proposal.py`（预计 50 行上下，含 docstring）
- `package.json`：`check:meta` 追加一段
- `openspec/config.yaml`：`rules.proposal` 两条（Non-goals 对齐 + Prior art 新增）
- `CONTRIBUTING.md`：Quality gates 加一行
- `Plan/方案讨论纪律.md`：删「两层分治与工件门禁」节
- 不改动：ci.yml、任何产品代码、已归档 change
