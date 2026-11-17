# Tasks

## 1. 闸门实现（TDD：先 red 后 green）

- [ ] 1.1 在 `scripts/tests/test_check_proposal.py` 写失败测试（red）：缺
      `## 已定裁决` 段、段空、关键词无任务载体、收尾未打勾、明示跳过
      五种情形（`裁决段`、`双层`、`段非空`、`关键词挂钩`、`迟到追加`）。
      验证：测试运行报红，断言 `::error::` 含缺的关键词。
- [ ] 1.2 在 `scripts/check_proposal.py` 实现校验（green）：提取
      `## 已定裁决` 段关键词集合，核对每个关键词在 tasks.md 有引用任务行，
      段非空，收尾全勾态下引用任务须打勾；只扫在途 change，归档不回溯
      （正则细节见 design.md「关键词与任务行挂钩」）（`裁决段`、`双层`、
      `段非空`、`关键词挂钩`、`迟到追加`）。验证：1.1 测试转绿，`pnpm check:meta` 绿。
- [ ] 1.3 `scripts/check_proposal.py` 覆盖率维持 100%。验证：
      `pnpm coverage` 该文件 100%。

## 2. 配置与准则

- [ ] 2.1 `openspec/config.yaml` `rules.proposal` 加一条：proposal.md MUST 含
      非空 `## 已定裁决` 段，逐条带反引号关键词列决定（`裁决段`、`段非空`）。
- [ ] 2.2 `openspec/config.yaml` `rules.tasks` 加一条：每个已定裁决关键词 MUST
      在 tasks.md 有含同关键词的任务行（`裁决段`、`关键词挂钩`）。
- [ ] 2.3 `openspec/config.yaml` `operations.apply.guidance` 加一条：apply 中途
      拍板的决定当场追加进段并补任务，收尾复查引用任务已打勾（`迟到追加`）。
- [ ] 2.4 `AGENTS.md` 对话效率段收紧"拍板即记"为"写回在途 change 已定裁决段"，
      并显式声明取代旧"琐碎修复直接改不新开 change"；补"扩容优先、不强塞、
      塞不下则新开"判据（`扩容新开`、`无载体即未拍板`、`取代旧裁决`）。

## 3. spec 与账本

- [ ] 3.1 `openspec/specs/project-governance/spec.md` 新增元规则"决定捕获进
      change"，含漏抄即红/扩容新开合法/归档不回溯 Scenario（`裁决段`、`双层`、
      `段非空`、`扩容新开`、`无载体即未拍板`、`关键词挂钩`、`迟到追加`）。
- [ ] 3.2 `openspec/specs/lessons-learned/workflow.md` 新增 LL：决定不入 change
      = apply 不执行 = 永不落笔；`INDEX.md` 加对应行（`取代旧裁决`）。

## 4. 收编文档修复

- [ ] 4.1 `python/README.md` Layout 节测试清单改为指向 `tests/` 目录一句
      （`收编文档修复`）。
- [ ] 4.2 `scripts/README.md` 与 `scripts/check_ci.py` 删 `LL-037` 编号、留机制句
      "CI 不跑的测试不算闸门"（`收编文档修复`）。
- [ ] 4.3 `scripts/README.md` 脚本清单表：check 类改指针（`check:meta`/
      `check:cross`），表只留非 check 入口工具（`收编文档修复`）。

## 5. 集成闸门与收尾

- [ ] 5.1 全闸门：`pnpm check`（md/ts/rs/py/meta）全绿。验证：退出码 0，
      无 `::error::`。
- [ ] 5.2 三轴 review（governance spec「元规则 review 三轴」）：按本 change
      四件工件对照实现 diff 审 Standards/Spec/Lessons 三轴，硬伤清零才准入
      后续步骤。验证：review 结论逐条写入本文件完成记录。
- [ ] 5.3 apply 态体检（health-check spec apply 态：语义考古维 + 四维）：对
      本次 diff 触碰文件全文只读体检，发现附文件+行号+证据落 `Plan/` 等
      点名，不阻塞。验证：完成记录含逐维度结论。
- [ ] 5.4 三态时效检查：扫 `openspec/specs/` 全目录，对照本次改动产出
      更新/新增/退役三态时效结论（本 change 改 project-governance 元规则、
      lessons-learned 账本），留痕完成记录。验证：完成记录含三态清单，
      `openspec/specs/README.md` 路由无需增删（无新 capability）。
- [ ] 5.5 Plan/ 瘦身：`Plan/体检-2026-11-15.md` 中已定文档修复对应章节（已由
      本 change 第 4 节修复）当场删除，只留未执行任务。验证：`grep` 无残留
      已完成章节；`pnpm check:md` 绿。
- [ ] 5.6 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾
      体检与升级预授权」消化所报 LAG。验证：复跑至退出码 0。
