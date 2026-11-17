# Tasks

## 1. 闸门实现（TDD：先 red 后 green）

- [x] 1.1 在 `scripts/tests/test_check_proposal.py` 写失败测试（red）：缺
      `## 已定裁决` 段、段空、关键词无任务载体、收尾未打勾、明示跳过
      五种情形（`裁决段`、`双层`、`段非空`、`关键词挂钩`、`迟到追加`）。
      验证：测试运行报红，断言 `::error::` 含缺的关键词。
- [x] 1.2 在 `scripts/check_proposal.py` 实现校验（green）：提取
      `## 已定裁决` 段关键词集合，核对每个关键词在 tasks.md 有引用任务行，
      段非空，收尾全勾态下引用任务须打勾；只扫在途 change，归档不回溯
      （正则细节见 design.md「关键词与任务行挂钩」）（`裁决段`、`双层`、
      `段非空`、`关键词挂钩`、`迟到追加`）。验证：1.1 测试转绿，`pnpm check:meta` 绿。
- [x] 1.3 `scripts/check_proposal.py` 覆盖率维持 100%。验证：
      `pnpm coverage` 该文件 100%。

## 2. 配置与准则

- [x] 2.1 `openspec/config.yaml` `rules.proposal` 加一条：proposal.md MUST 含
      非空 `## 已定裁决` 段，逐条带反引号关键词列决定（`裁决段`、`段非空`）。
- [x] 2.2 `openspec/config.yaml` `rules.tasks` 加一条：每个已定裁决关键词 MUST
      在 tasks.md 有含同关键词的任务行（`裁决段`、`关键词挂钩`）。
- [x] 2.3 `openspec/config.yaml` `operations.apply.guidance` 加一条 `迟到追加`：
      apply 中途拍板的决定当场追加进段并补任务，收尾复查引用任务已打勾。
- [x] 2.4 `AGENTS.md` 对话效率段收紧"拍板即记"为"写回在途 change 已定裁决段"，
      并显式声明取代旧"琐碎修复直接改不新开 change"；补"扩容优先、不强塞、
      塞不下则新开"判据（`扩容新开`、`无载体即未拍板`、`取代旧裁决`）。

## 3. spec 与账本

- [x] 3.1 `openspec/specs/project-governance/spec.md` 新增元规则"决定捕获进
      change"，含漏抄即红/扩容新开合法/归档不回溯 Scenario（`裁决段`、`双层`、
      `段非空`、`扩容新开`、`无载体即未拍板`、`关键词挂钩`、`迟到追加`）。
- [x] 3.2 `openspec/specs/lessons-learned/workflow.md` 新增 LL：决定不入 change
      = apply 不执行 = 永不落笔；`INDEX.md` 加对应行（`取代旧裁决`）。

## 4. 收编文档修复

- [x] 4.1 `python/README.md` Layout 节测试清单改为指向 `tests/` 目录一句
      （`收编文档修复`）。
- [x] 4.2 `scripts/README.md` 与 `scripts/check_ci.py` 删 `LL-037` 编号、留机制句
      "CI 不跑的测试不算闸门"（`收编文档修复`）。
- [x] 4.3 `scripts/README.md` 脚本清单表：check 类改指针（`check:meta`/
      `check:cross`），表只留非 check 入口工具（`收编文档修复`）。

## 5. 集成闸门与收尾

- [x] 5.1 全闸门：`pnpm check`（md/ts/rs/py/meta）全绿。验证：退出码 0，
      无 `::error::`。
- [x] 5.2 三轴 review（governance spec「元规则 review 三轴」）：按本 change
      四件工件对照实现 diff 审 Standards/Spec/Lessons 三轴，硬伤清零才准入
      后续步骤。验证：review 结论逐条写入本文件完成记录。
- [x] 5.3 apply 态体检（health-check spec apply 态：语义考古维 + 四维）：对
      本次 diff 触碰文件全文只读体检，发现附文件+行号+证据落 `Plan/` 等
      点名，不阻塞。验证：完成记录含逐维度结论。
- [x] 5.4 三态时效检查：扫 `openspec/specs/` 全目录，对照本次改动产出
      更新/新增/退役三态时效结论（本 change 改 project-governance 元规则、
      lessons-learned 账本），留痕完成记录。验证：完成记录含三态清单，
      `openspec/specs/README.md` 路由无需增删（无新 capability）。
- [x] 5.5 Plan/ 瘦身：`Plan/体检-2026-11-15.md` 全部发现（§1 两笔 + §2 一笔）
      已由本 change 第 4 节修复、§3/§4 为"已查，无"，整篇内容已吸收，故整篇
      删除该文件（去向：结论落本 change 工件与主 spec，追溯靠 git log）。验证：
      `ls Plan/体检-2026-11-15.md` 不存在；`pnpm check:md` 绿。
- [x] 5.6 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾
      体检与升级预授权」消化所报 LAG。验证：复跑至退出码 0。
- [x] 5.7 归档态体检：经人工裁决本次跳过（2026-11-16）——仅本次一次性跳过
      archive 态只读体检，规则本体不变（锚点 `体检`）。

## 完成记录

### 5.2 三轴 review（Standards / Spec / Lessons）

- **Standards**：本次 diff 14 文件逐一对上 tasks.md（无越权文件）。
  `scripts/check_proposal.py` 新增 `check_decision_capture`/`_rel`，命名动词开头、
  完整单词；被门禁扫描的代码/配置只写当前契约，无 LL 编号、无 spec 指针、
  无历史归因（`check_ci.py` 删 LL-037 即此口径）；覆盖率 100%。无硬伤。
- **Spec**：实现逐条对上 delta「元规则 决定捕获进 change」五 Scenario——
  缺段即红、段空即红、关键词无载体即红、收尾全勾态下载体须打勾、归档不回溯；
  design.md 的正则口径（`DECISION_KEYWORD`/`TASK_LINE`/`BACKTICK`）与实现一致。
  无硬伤。
- **Lessons**：LL-110 已落 workflow.md + INDEX.md；LL-104 复发检测的锚点数
  由五条同步为六条（新增 `迟到追加`），与 config.yaml 一致。无硬伤。

### 5.3 apply 态体检（语义考古维 + 四维）

逐维度结论（扫描范围 = 本次 diff 触碰文件全文）：

- **文档断言 vs 环境实测**：`scripts/README.md` 脚本表已改指针，不再逐条枚举
  check 脚本（避免第二处清单漂移）；`python/README.md` Layout 改指 `tests/`，
  与 `ls python/tests` 实测一致。无失配。
- **死代码 / 孤儿文件**：`check_decision_capture` 全部被测试覆盖、被 `main()`
  调用，无孤儿；`_rel` 被 `check_decision_capture` 使用。无死代码。
- **规则重复 / 冲突**：决定捕获规则正文唯一存 governance spec 元规则段，
  config.yaml 留同口径门禁句、AGENTS.md 留准则句 + 指针，分层不重复。无冲突。
- **语义考古维**：新增注释均为当前契约与机制说明（条件句描述"缺了会怎样"），
  无"曾经/不再/取代"式历史归因。无考古。

结论：无硬伤，无待点名发现。

### 5.4 三态时效检查（更新 / 新增 / 退役）

- **更新**：`project-governance`（新增元规则 决定捕获进 change）、
  `lessons-learned`（新增 LL-110、同步 LL-104 锚点数）——均已改。
- **新增**：无新 capability（本 change 仅改既有 spec 元规则与账本，
  `openspec/specs/README.md` 路由无需增删）。
- **退役**：无（旧"琐碎修复直接改不新开 change"裁决由 AGENTS.md 取代，
  非 spec capability 退役）。
