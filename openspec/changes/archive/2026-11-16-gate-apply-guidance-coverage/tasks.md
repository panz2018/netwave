# Tasks

## 1. config.yaml：guidance 加锚点 + rules.tasks 加一条

- [x] 1.1 `openspec/config.yaml` 的 `operations.apply.guidance` 五条各嵌入
      design「锚点词选定」的锚点词（①`Plan/` ②`三态时效` ③`三轴` ④`体检`
      ⑤`check:outdated`），锚点用反引号包裹置于条目内，不改五步语义与
      顺序。验证：`grep -c` 逐锚点在 guidance 段命中恰一次；五步文字语义
      未变（diff 仅新增反引号锚点）；`pnpm check:md` 绿。
- [x] 1.2 `openspec/config.yaml` 的 `rules.tasks` 加一条：写 `tasks.md` 时
      收尾打勾任务 MUST 逐条覆盖 apply guidance 锚点，明示跳过者写成含
      锚点 + "跳过" + ISO 日期的打勾行（与 `scripts/check_proposal.py` 新
      校验同口径）。验证：该条与脚本判定字面一致；`pnpm check:md` 绿。

## 2. check_proposal.py：guidance 锚点覆盖校验（red 先于 green）

- [x] 2.1 red：新建 `scripts/tests/test_check_proposal.py`（若已存在则扩展），
      夹具取自真实 tasks.md 收尾行（本 change 自身 +
      `openspec/changes/archive/2026-11-15-drain-stray-profraw-in-tests/tasks.md`
      的 7.x 行，防 LL-108 臆造夹具），断言：①五锚点齐全 → 通过；②缺
      `体检` 锚点 → 失败且报出 `体检`；③锚点只在散文行（非打勾行）→ 失败；
      ④打勾行含锚点 + 跳过 + ISO 日期 → 通过；⑤同一锚点出现多次 → 通过
      （存在性非计数）。验证：`uv run pytest scripts/tests -k guidance` 因
      实现未落地而失败（`AttributeError`/断言失败），退出码非 0。
- [x] 2.2 green：在 `scripts/check_proposal.py` 实现
      `check_guidance_coverage(change_dir) -> list[str]`——从
      `openspec/config.yaml` 读 guidance 锚点常量（①–⑤），扫
      `tasks.md` 中以 `- [ ]`/`- [x]` 开头的行，逐锚点判存在性；跳过出口
      要求同行含锚点 + `跳过` + `\d{4}-\d{2}-\d{2}`；缺项返回缺失锚点列表。
      接入 `main` 对在途 change（排除 `archive/`）调用，缺项以 `::error::`
      输出 change 名 + 缺失锚点并非零退出；无在途 change 视为通过。验证：
      2.1 命令转绿；`python3 scripts/check_proposal.py` 对本 change 自身
      tasks.md 退出码 0（自证：本文件收尾组含五锚点）。

## 3. 账本同步（LL-104 改口径）

- [x] 3.1 `openspec/specs/lessons-learned/workflow.md` 的 LL-104 复发检测句
      从"review Standards 轴核对 tasks.md 收尾任务数是否等于 config.yaml
      apply guidance 条数"改为"由 `scripts/check_proposal.py` 机器强制
      （guidance 锚点逐条覆盖，缺项即红；明示跳过写打勾行含 ISO 日期即
      放行）"，规则句保留。验证：该条不再含"任务数是否等于"字样；
      `pnpm check:md` 绿；INDEX 无需改（编号不变）。

## 4. 集成闸门与收尾

- [x] 4.1 全闸门：`pnpm check`（md/ts/rs/py/meta）全绿。验证：退出码 0，
      无 `::error::` 输出。
- [x] 4.2 三轴 review（governance spec「元规则 review 三轴」）：按本 change
      四件工件对照实现 diff 审 Standards/Spec/Lessons 三轴，硬伤清零才准入
      后续步骤。验证：review 结论逐条写入本文件完成记录，无未闭环硬伤。
- [x] 4.3 apply 态体检（health-check spec apply 态：语义考古维 + 四维）：对
      本次 diff 触碰文件全文只读体检，发现附文件+行号+证据落 `Plan/` 等
      点名，不阻塞。验证：完成记录含逐维度结论（无发现写"已查，无"）。
- [x] 4.4 三态时效检查：扫 `openspec/specs/` 全目录，对照本次改动产出
      更新/新增/退役三态时效结论（本 change 改 project-governance 元规则、
      lessons-learned 账本），留痕完成记录。验证：完成记录含三态清单，
      `openspec/specs/README.md` 路由无需增删（无新 capability）。
- [x] 4.5 Plan/ 瘦身：本 change 结论若涉及 `Plan/` 对应章节则当场删除，
      只留未执行任务。验证：`grep` 无残留已完成章节；`pnpm check:md` 绿。
- [x] 4.6 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾
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

### 4.2 三轴 review（Standards / Spec / Lessons）

diff 文件集 = `openspec/config.yaml`、`scripts/check_proposal.py`、
`scripts/tests/test_check_proposal.py`、`openspec/specs/lessons-learned/workflow.md`、
本 `tasks.md`，逐文件对上任务 1.1/1.2/2.1/2.2/3.1，无越权文件。

- Standards：新增 `#` 注释只写当前契约，无 LL 编号 / spec 指针 / 历史归因
  （`check_comments` 绿）；函数 `check_guidance_coverage`、`guidance_anchors`
  动词开头、完整单词；锚点单一来源 = config.yaml，脚本运行时解析，无第二清单。
- Spec：delta 五场景逐条对上实现——存在性覆盖、散文不算覆盖（只扫
  `- [ ]`/`- [x]` 行）、明示跳过合法（同行含锚点+跳过+ISO 日期）、多次不加分
  （存在性非计数）、归档不回溯（`main` 排除 `archive/`）。一致，无偏差。
- Lessons：LL-104 复发检测句已改指 `check_proposal.py` 机器强制；夹具取自
  真实 tasks.md 收尾行（LL-108）；锚点运行时读 config 防漂移（LL-076）。
- 受控取证：临时删除本 tasks.md 的 `体检` 锚点行 → `check_proposal.py` 退出码
  1 并 `::error::` 指名 `体检`，还原后转绿——闸门真拦，非假绿。

硬伤：无。

### 4.3 apply 态体检（语义考古维 + 四维）

逐维度结论（对 diff 触碰文件全文）：

- 语义考古维：已查，无。新增注释均为当前契约与机制说明，无"曾经/不再/取代"
  式表述。
- 文档断言 vs 环境实测：已查，无。config.yaml 五锚点与脚本 `guidance_anchors()`
  解析结果一致（`test_anchors_mirrored_in_config_yaml` 锁定）。
- 死代码 / 孤儿文件：已查，无。新增函数均被 `main` 与单测调用。
- 规则重复 / 冲突：已查，无。锚点唯一来源 config.yaml，脚本运行时读，无第二处
  清单；`rules.tasks` 新增条与 `check_proposal.py` 判定同口径。
- 可门禁化 LL 未落闸门：本 change 即落 LL-104 闸门，无新增未落项。

### 4.4 三态时效检查（openspec/specs/ 全目录）

- 更新：`project-governance`（本 change delta 新增元规则「apply guidance 收尾
  覆盖门禁」，归档时 sync 进主 spec）；`lessons-learned/workflow.md`（LL-104
  复发检测句改口径，已改）。
- 新增：无新 capability（复用 project-governance）。
- 退役：无。
- `openspec/specs/README.md` 路由：无需增删（无新 capability 目录）。

### 4.5 Plan/ 瘦身

本 change 结论对应 `Plan/体检-2026-11-15.md` 第 4 节（LL-104 落闸门）。该报告
系已归档 change `drain-stray-profraw-in-tests` 的体检产物，且仍含未修的 #1–#3
文档旧账，删除整份或删其第 4 节均超出本 change 授权——提请人工点名后再处理，
本步不擅删。

### 4.6 check:outdated

首跑报 4 LAG（cargo 2 / pnpm 1 / cli 1），按预授权逐项消化：

- cargo：`clap` 4.6.7→4.6.8、`clap_lex` 1.1.1→1.1.2（`cargo update`）。
- pnpm：`@biomejs/biome` 2.6.7→2.6.8（`pnpm update`）。
- cli：`rustc` 1.99.1→1.100（`rust-toolchain.toml` channel 改钉，rustup 自动
  装 1.100 工具链 + rustfmt/clippy 组件 + wasm32-unknown-unknown target）。
  该钉版属上限（dependency-upgrade spec「工具链与运行时钉版切换」= 上限升级，
  直接执行不开 change）；`rust-toolchain.toml` 原注释误称"floor / 走 OpenSpec
  change"，与 spec 矛盾，已一并改为上限口径。
- 验收：`pnpm check` 全绿（255 测试、覆盖率 100%）、`pnpm check:cross` 四端
  对拍全过（core==python==node bit-exact，wasm within tol）、
  `check_versions.py` 绿（rust-version 1.99 不变、toolchain 1.100）。
- 复跑 `pnpm check:outdated`：`SUMMARY: 0 LAG (all current)`，退出码 0。
