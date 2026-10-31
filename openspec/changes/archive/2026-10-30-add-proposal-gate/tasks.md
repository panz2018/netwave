# Tasks: add-proposal-gate

- [x] 1. 实现 `scripts/check_proposal.py`（骨架抄 `check_else.py`：docstring
      写契约、`::error::` 输出、退出码 0/1；判定规则见 design.md 决策 2–4：
      排除 archive、0 个在途通过、Prior art 须含 URL/文件路径/「无现成
      方案」之一、二级标题（`##` + 空格）大小写不敏感。闸门脚本按 scripts/ 惯例无
      单测，以现场 red/green 为验收）
- [x] 2. red：临时删本 change `proposal.md` 的 `## Prior art` 节，跑
      `python3 scripts/check_proposal.py`，确认退出 1 且 `::error::` 指明
      缺失节名（先让它红）
- [x] 3. green：恢复该节复跑 → 退出 0；再临时造一个空 `Prior art` 节
      （标题下无内容）→ 仍退出 1；删除临时状态复跑 → 退出 0
- [x] 4. 接入 `package.json` 的 `check:meta`（追加
      `python3 scripts/check_proposal.py`），跑 `pnpm check:meta` 全绿
- [x] 5. 同步 `openspec/config.yaml` `rules.proposal`：Non-goals 措辞对齐 +
      新增 Prior art 规则（字面与脚本判定一致，见 design.md 决策 5）
- [x] 6. `CONTRIBUTING.md` Quality gates 节加一行 check_proposal 说明
- [x] 7. `Plan/方案讨论纪律.md` 删「两层分治与工件门禁」节（去向：本 change
      spec + 脚本），同步检查该文件其余节对已删节的引用
- [x] 8. 跑 `pnpm check:md` 退出 0（本次动了 CONTRIBUTING、Plan、change
      工件多处 Markdown）
