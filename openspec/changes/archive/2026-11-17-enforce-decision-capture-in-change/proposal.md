# Proposal

## Why

讨论中拍板的决定若没写进 change 的工件，apply 阶段看不见、archive 后蒸发，
等于永不落笔、永不完成（本会话实证：`Plan/体检-2026-11-15.md` 的 Q2/Q3/Q4
已拍板却因无 change 载体而悬空）。需要一个机制强制"每个决定都有 change 载体"，
并把它门禁化，使决定不再跨上下文丢失。

## What Changes

- `openspec/config.yaml`：`rules.proposal` 新增——proposal.md MUST 含 `## 已定裁决`
  段，逐条以反引号关键词列出本次讨论拍板的每个决定，段必须非空；
  `rules.tasks` 新增——每个关键词 MUST 在 `tasks.md` 有含同关键词的任务行；
  `operations.apply.guidance` 新增——apply 中途拍板的决定当场追加进段并补任务，
  收尾复查每个关键词任务已打勾。
- `scripts/check_proposal.py`：新增校验——在途 change 的 proposal.md 有非空
  `## 已定裁决` 段、每个关键词有对应任务行、收尾时该任务已打勾，缺则红并指名。
- `openspec/specs/project-governance/spec.md`：新增元规则"决定捕获进 change"。
- `AGENTS.md`：收紧"拍板即记"为"写回在途 change 的已定裁决段"，并明确取代
  旧裁决"琐碎修复直接改不新开 change"。
- `openspec/specs/lessons-learned/workflow.md` + `INDEX.md`：新增 LL 登记本教训。
- 收编 `Plan/体检-2026-11-15.md` 已定的文档修复（Q2/Q3/Q4）为本 change 任务，
  使其有执行载体。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `project-governance`: 新增元规则——讨论拍板的每个决定 MUST 当场写入在途
  change 的 `## 已定裁决` 段并以反引号关键词标识，每个关键词在 `tasks.md`
  有对应任务行；落不进当前 change 先尝试扩容、不强塞，塞不下则新开 change；
  门禁化于 `scripts/check_proposal.py`。

## Impact

- `openspec/config.yaml`（rules.proposal / rules.tasks / operations.apply.guidance）
- `scripts/check_proposal.py`（新增校验，TDD：先 red 后 green）+ `scripts/tests/test_check_proposal.py`
- `openspec/specs/project-governance/spec.md`（新增元规则）
- `AGENTS.md`（收紧准则 + 取代旧裁决）
- `openspec/specs/lessons-learned/workflow.md` + `INDEX.md`（新增 LL）
- `python/README.md`、`scripts/README.md`、`scripts/check_ci.py`（收编的文档修复）
- `Plan/体检-2026-11-15.md`（修复完成后瘦身删除对应章节）

## Non-goals

- 不强制"决定列得全"——闸门只查已声明关键词的结构与挂钩，看不到对话，
  漏列由 AGENTS.md 准则兜，不设第二道机器闸。
- 不改 openspec CLI 本身，只用其 config/rules/guidance 扩展点。
- 不引入 `#[coverage(off)]` 式新豁免，不动覆盖率闸门逻辑。

## Prior art

- 同仓 `gate-apply-guidance-coverage`（已归档）：guidance 锚点 + `check_proposal.py`
  存在性校验的同族门禁模式，本 change 复用其"关键词 + 只查存在性"判据。
- `openspec/config.yaml` 现有 `rules.proposal` 的 Non-goals/Prior art/专家增补
  三段强制结构，本 change 的 `## 已定裁决` 段与之同口径（段必存在、可机器判）。

## 专家增补

- 顶尖专家会要求 `check_proposal.py` 的新校验先写失败测试再实现（TDD），
  落 `scripts/tests/test_check_proposal.py`，覆盖：缺段、空段、关键词无任务、
  收尾未打勾、明示跳过五种情形。
- 会要求 `## 已定裁决` 段格式与 `tasks.md` 关键词挂钩规则在 design.md 给出
  精确正则/字段定义，避免 `check_proposal.py` 与散文口径漂移。
- 会要求元规则在 `project-governance/spec.md` 配可测 Scenario（漏抄即红、
  扩容/新开合法、归档不回溯），与既有元规则写法一致。

## 已定裁决

- `裁决段`：决定写进 proposal 的 `## 已定裁决` 段，每条带反引号关键词，
  再在 `tasks.md` 转成含同关键词的任务行（出处：本会话 grilling Q1）。
- `双层`：双层保障——`scripts/check_proposal.py` CI 闸门 + `AGENTS.md`
  准则（出处：grilling Q2）。
- `段非空`：`## 已定裁决` 段必须存在且非空，不设"写无"出口
  （出处：grilling Q3）。
- `扩容新开`：决定落不进当前 change 时先尝试扩容、不强塞，塞不下则新开
  change（出处：grilling Q4 + 用户补充）。
- `无载体即未拍板`：无在途 change 时拍板的决定，必须先开 change 承载，
  否则视为未拍板（出处：grilling Q5）。
- `取代旧裁决`：本机制取代旧裁决"琐碎文档修复直接改、不新开 change"
  （出处：grilling Q6）。
- `关键词挂钩`：决定用反引号关键词与任务行挂钩，闸门精确核对漏哪个报哪个
  （出处：grilling Q7）。
- `迟到追加`：apply 中途拍板的决定当场追加进段并补任务，收尾复查引用
  任务已打勾（出处：grilling Q8）。
- `收编文档修复`：收编 `Plan/体检-2026-11-15.md` 已定文档修复——
  `python/README.md` Layout 改指向 `tests/`、`scripts/README.md` 与
  `scripts/check_ci.py` 删 `LL-037` 留机制句、`scripts/README.md` 脚本表改指针
  （出处：grilling Q1-Q4 体检修复轮）。
