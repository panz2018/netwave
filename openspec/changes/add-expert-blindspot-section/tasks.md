# Tasks: add-expert-blindspot-section

- [x] 1. red：临时造缺 `## 专家增补` 节的 fixture proposal，跑
      `python3 scripts/check_proposal.py` 确认报 `::error::` 缺节（先写复现）
- [x] 2. green：`scripts/check_proposal.py` 扩展——`REQUIRED` 增
      `专家增补`；该节空/「无」放行；非空逐行查具体指涉
      （`CITATION` ∨ 反引号 token），无指涉行 `::error::` 带行号；
      删除 fixture
- [x] 3. 验证注水分支：fixture 非空泛谈行 → 红；含反引号标识符行 → 绿；
      空节 → 绿（三分支各跑一次后删 fixture）
- [x] 4. `openspec/config.yaml` `rules.proposal` 增同口径软提示一条
- [x] 5. 闸门全绿：`pnpm check:meta`、`pnpm check:md`（退出码 0）
- [x] 6. 波及面核对：`scripts/README.md` 若列有 check_proposal 职责描述则
      同步一句专家增补节；`openspec/specs/README.md` 路由无需改（governance
      已在路由内），核对留痕于本文件完成记录

## 完成记录

- fixture `zz-fixture-blindspot` 已删；三分支实测：缺节红 / 泛谈红 /
  反引号与「无」绿；`pnpm check:meta`、`pnpm check:md` 退出 0。
- 实现修正：逐行判定改按逻辑条目（bullet+续行合并），red 阶段实测
  换行续行会被逐行误杀。
- spec 三态时效：更新=project-governance（delta 已备，archive 时 sync）；
  新增=无；退役=无。
- Plan/ 同步：`Plan/方案讨论纪律.md` 删 #4–#7 行（结论存本 change
  design.md Decisions）；AGENTS.md「对话效率」增专家盲点追问条（D2 讨论位）。
