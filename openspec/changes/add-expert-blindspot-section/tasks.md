# Tasks: add-expert-blindspot-section

- [ ] 1. red：临时造缺 `## 专家增补` 节的 fixture proposal，跑
      `python3 scripts/check_proposal.py` 确认报 `::error::` 缺节（先写复现）
- [ ] 2. green：`scripts/check_proposal.py` 扩展——`REQUIRED` 增
      `专家增补`；该节空/「无」放行；非空逐行查具体指涉
      （`CITATION` ∨ 反引号 token），无指涉行 `::error::` 带行号；
      删除 fixture
- [ ] 3. 验证注水分支：fixture 非空泛谈行 → 红；含反引号标识符行 → 绿；
      空节 → 绿（三分支各跑一次后删 fixture）
- [ ] 4. `openspec/config.yaml` `rules.proposal` 增同口径软提示一条
- [ ] 5. 闸门全绿：`pnpm check:meta`、`pnpm check:md`（退出码 0）
- [ ] 6. 波及面核对：`scripts/README.md` 若列有 check_proposal 职责描述则
      同步一句专家增补节；`openspec/specs/README.md` 路由无需改（governance
      已在路由内），核对留痕于本文件完成记录
