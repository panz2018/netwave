# Design

## Context

`scripts/check_comments.py` 现有执法只针对**注释行**的"陈旧引用"模式集（LL
编号、开发文档指针、阶段代号等），由 `is_comment()` 过滤后逐行匹配。CJK 检查
的执法面不同——要覆盖全部行（含 `ci.yml` 的 `run:` 步骤体），且豁免逻辑
（形状核验、白名单）与既有模式集无关。动机见 proposal.md「Why」。

## Goals / Non-Goals

**Goals:**

- CJK 检查作为 `check_comments.py` 内一条独立检查，复用其文件遍历
  （`iter_scanned_files`）与豁免目录机制，不新建脚本、不加新命令。
- 形状豁免自带核验：引用不成立的中文不放行，杜绝"编个形状骗过闸门"。

**Non-Goals:**

- 不改 `is_comment()` 与既有陈旧引用模式集的行为（CJK 走独立全行循环）。
- 不做 Markdown CJK 检查（归 `scripts/check_md.py`，另议）。

## Decisions

- **全行独立循环 vs 复用注释循环**：CJK 检查在 `main()` 内对每个扫描文件另起
  一次全行遍历，不复用 `is_comment()` 过滤的既有循环。理由：执法面不同（全行
  vs 注释行），混在一个循环会让"陈旧引用"规则误扩到非注释行。备选（给既有循环
  加"全行模式"开关）被否——增加既有逻辑分支风险。
- **形状核验补前缀**：正则匹配 `「(?P<title>[^」]+)」\(specs/(?P<cap>[^)]+\.md)\)`，
  核验时拼 `openspec/` 前缀读文件、`title in 文件内容` 判真。理由：形状不含
  `openspec/` 字样，避开既有"禁 `openspec/` 指针"铁律；核验仍指向真实文件。
- **白名单按路径前缀**：`scripts/check_*.py`（glob）与 `scripts/tests/` 下
  文件在 CJK 检查里 `continue` 跳过。理由：范围锁死门禁自身与自测，业务代码
  即使误写中文仍红。备选（整 `scripts/` 豁免）被否——会盖住 `scripts/versions/`
  业务代码的真违规。
- **报错含命中字符**：报告格式 `CJK '<char>' <path>:<line>`，取该行第一个
  CJK 字符。理由：一眼定位。

## Risks / Trade-offs

- [形状豁免被滥用：有人给真违规行硬凑一个真存在的 spec 标题引用] → 形状要求
  标题真实存在，凑标题需真去 spec 里写该标题（会被 review 发现）；且引用是
  可 grep 审计的显式标记，非静默。
- [全行扫描误伤含中文的数据夹具] → 实测扫描面内无此类夹具；若将来出现，
  走形状豁免或白名单，不留隐式豁免。
- [`scripts/tests/` 白名单过宽] → 该目录只放门禁自测，业务测试在
  `python/tests`、`core/tests`、`typescript/test`，不在白名单内。
