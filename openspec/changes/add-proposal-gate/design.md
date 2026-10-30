# Design

## Context

See proposal.md - Why. 骨架沿用本仓 `scripts/check_else.py`（单文件标准库
Python、docstring 写契约、`::error::` 输出、退出码 0/1）；接入点沿用
`scripts/check_ci.py` 先例（挂 `check:meta`，CI 经 `pnpm check` 覆盖）。

## Goals / Non-Goals

**Goals:**

- 机械校验在途 proposal 的 `## Non-goals` / `## Prior art` 两节存在且有实质内容。
- 软规则（config.yaml）与硬闸门（脚本）字面一致。

**Non-Goals:**

- 语义级质量判断（出处权威性、条目是否敷衍到正则测不出的程度）——归 review。

## Decisions

1. **节名取英文 `## Prior art`，Non-goals 沿用不动。**
   proposal 模板标题族（Why / What Changes / Capabilities / Impact）是
   openspec CLI 生成的英文，新节混中文破坏同文件风格；`## Non-goals` 已被
   25/25 归档验证为稳定惯例。备选：中文节名（否决，理由同上）。

2. **实质内容判定：**
   - Non-goals：节下（到下一个二级标题前）≥1 个非空行，非列表符号行也算。
   - Prior art：节下 ≥1 个非空行，且**至少一行**满足
     `https?://` ∨ 仓库内文件路径（正则 `\S+\.(rs|py|ts|md|json|yaml|yml|toml)`）
     ∨ 含「无现成方案」。
     备选：仅查非空（否决，防不住套话注水）；仅查 URL（否决，误伤本仓内部
     先例——本闸门自己的 proposal 引的就是 `scripts/check_else.py`）。

3. **扫描范围 = `openspec/changes/*/proposal.md`，排除 `archive/`；
   0 个在途 change = 通过。**
   排除归档=既成事实不回头要求（与 `check_comments.py` 动态取改动名但
   不回溯改写同理）；0 个通过保证闸门上线首日不红。

4. **零豁免。** 无 skip 标记、无白名单。诚实的「无现成方案」是合法出口
   而非豁免。备选：`<!-- proposal-gate: skip -->` 注释口子（否决——口子
   即闸门失效的开始）。

5. **config.yaml `rules.proposal` 同步改两条**：Non-goals 措辞对齐脚本
   判定；新增 Prior art 规则。软提示与硬闸门脱节会让 agent 反复被打回
   （LL-008 同源：同一事实两处不一致）。

## Risks / Trade-offs

- [套话绕过：Prior art 写一个无关文件路径凑数] → 接受：闸门定位是结构
  下限，语义质量归 review 三轴；提高机械判定精度会误伤合法内部先例。
- [标题变体漂移（`## Prior Art` 大小写、`###` 层级）] → 匹配规则：
  行首二级标题（`##` + 空格）+ 节名，大小写不敏感；`###` 不算（模板节固定二级）。
- [本 change 自举：脚本合入瞬间，自己的 proposal 必须已含两节] → 本
  proposal 已自带 Prior art / Non-goals，天然过闸；这是特性（dogfooding）。

## Migration Plan

单 PR：脚本 + package.json + config.yaml + CONTRIBUTING + Plan 删节 +
spec delta 同步合入；回滚 = revert 该 PR（无数据迁移）。

## Open Questions

（无）
