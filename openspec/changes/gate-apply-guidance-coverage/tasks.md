# Tasks

## 1. config.yaml：guidance 加锚点 + rules.tasks 加一条

- [ ] 1.1 `openspec/config.yaml` 的 `operations.apply.guidance` 五条各嵌入
      design「锚点词选定」的锚点词（①`Plan/` ②`三态时效` ③`三轴` ④`体检`
      ⑤`check:outdated`），锚点用反引号包裹置于条目内，不改五步语义与
      顺序。验证：`grep -c` 逐锚点在 guidance 段命中恰一次；五步文字语义
      未变（diff 仅新增反引号锚点）；`pnpm check:md` 绿。
- [ ] 1.2 `openspec/config.yaml` 的 `rules.tasks` 加一条：写 `tasks.md` 时
      收尾打勾任务 MUST 逐条覆盖 apply guidance 锚点，明示跳过者写成含
      锚点 + "跳过" + ISO 日期的打勾行（与 `scripts/check_proposal.py` 新
      校验同口径）。验证：该条与脚本判定字面一致；`pnpm check:md` 绿。

## 2. check_proposal.py：guidance 锚点覆盖校验（red 先于 green）

- [ ] 2.1 red：新建 `scripts/tests/test_check_proposal.py`（若已存在则扩展），
      夹具取自真实 tasks.md 收尾行（本 change 自身 +
      `openspec/changes/archive/2026-11-15-drain-stray-profraw-in-tests/tasks.md`
      的 7.x 行，防 LL-108 臆造夹具），断言：①五锚点齐全 → 通过；②缺
      `体检` 锚点 → 失败且报出 `体检`；③锚点只在散文行（非打勾行）→ 失败；
      ④打勾行含锚点 + 跳过 + ISO 日期 → 通过；⑤同一锚点出现多次 → 通过
      （存在性非计数）。验证：`uv run pytest scripts/tests -k guidance` 因
      实现未落地而失败（`AttributeError`/断言失败），退出码非 0。
- [ ] 2.2 green：在 `scripts/check_proposal.py` 实现
      `check_guidance_coverage(change_dir) -> list[str]`——从
      `openspec/config.yaml` 读 guidance 锚点常量（①–⑤），扫
      `tasks.md` 中以 `- [ ]`/`- [x]` 开头的行，逐锚点判存在性；跳过出口
      要求同行含锚点 + `跳过` + `\d{4}-\d{2}-\d{2}`；缺项返回缺失锚点列表。
      接入 `main` 对在途 change（排除 `archive/`）调用，缺项以 `::error::`
      输出 change 名 + 缺失锚点并非零退出；无在途 change 视为通过。验证：
      2.1 命令转绿；`python3 scripts/check_proposal.py` 对本 change 自身
      tasks.md 退出码 0（自证：本文件收尾组含五锚点）。

## 3. 账本同步（LL-104 改口径）

- [ ] 3.1 `openspec/specs/lessons-learned/workflow.md` 的 LL-104 复发检测句
      从"review Standards 轴核对 tasks.md 收尾任务数是否等于 config.yaml
      apply guidance 条数"改为"由 `scripts/check_proposal.py` 机器强制
      （guidance 锚点逐条覆盖，缺项即红；明示跳过写打勾行含 ISO 日期即
      放行）"，规则句保留。验证：该条不再含"任务数是否等于"字样；
      `pnpm check:md` 绿；INDEX 无需改（编号不变）。

## 4. 集成闸门与收尾

- [ ] 4.1 全闸门：`pnpm check`（md/ts/rs/py/meta）全绿。验证：退出码 0，
      无 `::error::` 输出。
- [ ] 4.2 三轴 review（governance spec「元规则 review 三轴」）：按本 change
      四件工件对照实现 diff 审 Standards/Spec/Lessons 三轴，硬伤清零才准入
      后续步骤。验证：review 结论逐条写入本文件完成记录，无未闭环硬伤。
- [ ] 4.3 apply 态体检（health-check spec apply 态：语义考古维 + 四维）：对
      本次 diff 触碰文件全文只读体检，发现附文件+行号+证据落 `Plan/` 等
      点名，不阻塞。验证：完成记录含逐维度结论（无发现写"已查，无"）。
- [ ] 4.4 三态时效检查：扫 `openspec/specs/` 全目录，对照本次改动产出
      更新/新增/退役三态时效结论（本 change 改 project-governance 元规则、
      lessons-learned 账本），留痕完成记录。验证：完成记录含三态清单，
      `openspec/specs/README.md` 路由无需增删（无新 capability）。
- [ ] 4.5 Plan/ 瘦身：本 change 结论若涉及 `Plan/` 对应章节则当场删除，
      只留未执行任务。验证：`grep` 无残留已完成章节；`pnpm check:md` 绿。
- [ ] 4.6 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾
      体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍，含全局
      CLI/直装工具的机器级升级；登记回退不阻塞，设计级适配/契约破损/流程
      走不通才停下报告；下限变更等人工发起）。消化后 MUST 复跑
      `pnpm check:outdated` 至退出码 0（SUMMARY 归零）才算本项完成。

## Workflow follow-up

- 按 openspec 流程 archive 本 change（delta 同步进
  `openspec/specs/project-governance/spec.md` 的 ADDED requirement），归档前
  执行 Plan/ 瘦身与三态时效检查。
- **本 change 跳过 health-check spec 的 archive 态体检**（人工裁决
  2026-11-16）：归档完成后的全项目存量只读体检本轮不执行；apply 态体检
  （task 4.3）照常执行。跳过仅限本 change，不改变 health-check spec 对后续
  change 的默认要求；本声明持久保留，不作为一次性跳过删除。
- 提交全景表（分组 → 文件 → commit 标题）交人工点名，agent 不自行 commit。

## 完成记录

（apply 阶段填写：逐任务验证证据、三轴 review 结论、体检逐维度结论、三态
时效清单、check:outdated 归零证据。）
