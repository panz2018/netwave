# 清除考古文字、堵造考古源头、关闭审查缝隙，并统一治理脚本覆盖率配置

## Why

考古文字（历史归因、开发文档指针、口径变更叙述）在本仓反复出现、清不干净，
实证有三个叠加根因：

1. **扫描面真空**：「代码只写使用信息」只覆盖 `.rs`/`.py`/`.ts`，CI 与配置
   （`.yml`/`.yaml`/`.toml`）无门禁——`ci.yml` 135 行注释含 `LL-011`/`LL-034`/
   `LL-047`、CI run 号 `43603143333`、`Re-enabled 2026-09-26`、`design decision 7`；
   `rust-toolchain.toml` 注释指向 `workspace-layout spec`。
2. **治理规则自相矛盾（造考古的源头）**：`AGENTS.md`「改动要有去向」要求
   常驻文档新增规则**附 LL 编号或 spec 指针**，而「代码只写使用信息」禁止
   注释含同类指针——每次改 CI 都在合规地往配置注释里塞编号。
3. **审查缝隙**：review 三轴只审 diff，archive 态体检明文只扫"改动面之外"，
   于是"被触碰但不在 diff 内"的旧行两边都不管——旧考古永久隐身。

本 change 一次性清存量、上门禁、堵源头、关缝隙，并把治理脚本覆盖率范围与
阈值统一进 `pyproject.toml`（命令行列文件清单易漏）。

## What Changes

- `scripts/check_comments.py` 扫描面从 `.rs`/`.py`/`.ts` 扩至
  `.yml`/`.yaml`/`.toml`；模式清单定为**封闭的固定形态集**（机械可判、
  零语义歧义）：`LL-` 编号、CI run 号、动词+日期归因（`Re-enabled <日期>`、
  `重新启用 <日期>`、`已标定`）、动态 change 目录名、开发文档指针
  （`spec: <capability>`/铁律编号/`openspec/`/`Plan/`）、`design decision N`/`design D\d`。
- 豁免集：`pnpm-lock.yaml`、`openspec/changes/archive/**` 下的 `.openspec.yaml`、
  既有构建目录（`target`/`node_modules`/`.venv` 等）、`openspec/config.yaml`
  整体豁免（其路径引用是流程指令的功能语义，非泄漏）。
- 中文语义考古词（`废止`/`推翻`/`原口径`/`不再是`）**不进门禁词表**——
  `scripts/check_md.py` 不新增考古词模式；语义层考古改由 AI 全面审查承担，
  职责写进治理 spec 两处（「代码只写使用信息」条 + 「review 三轴」条）。
- 存量清理：`ci.yml` 全部考古注释、`rust-toolchain.toml` 注释改写为只陈述
  当前契约；6 个能力 spec 正文的 11 处"废止/推翻"式叙述直接改写主 spec
  正文（措辞改写、无契约行为变化，逐条留痕 tasks.md）；全仓 15 处命中中
  另 3 处经判定为当前契约表述保留不改，1 处由治理 spec delta 新文替换。
- 治理 spec「元规则 代码只写使用信息」扫描范围随之扩至
  `.yml`/`.yaml`/`.toml`，Requirement 措辞与 Scenario 同步。
- **堵源头**：`AGENTS.md`「改动要有去向」改写——规则出处落 commit message 与
  lessons-learned 账本，不落被门禁扫描文件的注释（消除根因 2）。
- **关缝隙**：`archive-health-check` spec 改名 `health-check`，体检扩成同一机制
  两种触发——apply 态（三轴 review 后、`check:outdated` 前，扫 diff 触碰文件
  全文）+ archive 态（现状不变）；维度加"语义考古"维（两态通用），`Plan/`
  维仅 archive 态；apply 态每次必跑，全豁免时记"已查，无适用文件"留痕；
  只读纪律、三级去重、落 Plan/ 等点名两态一致（消除根因 3）。
- **专职步骤显式化**：`openspec/config.yaml` 的 apply guidance 加一步"被触碰
  文件全文体检"；治理 spec「review 三轴」加 Scenario 明确"审 diff"与"审全文"
  两步分工不可互替。
- **覆盖率配置统一**：根 `pyproject.toml` 加 `[tool.coverage]`，范围 =
  `scripts/versions` 域 + `scripts/coverage_gate.py` + `scripts/check_comments.py`，
  阈值 100；`package.json` 的 `check:py` 删 `--cov=`/`--cov-fail-under=`，
  成单一真相源。
- `scripts/coverage_gate.py` 的 floor 参数能力与地板 0 单测保留——它是通用
  阈值工具，0 只是合法输入值，不随本次清理阉割。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `project-governance`：「元规则 代码只写使用信息」扫描范围从 `.rs`/`.py`/`.ts`
  扩至 `.yml`/`.yaml`/`.toml`，模式定为封闭固定形态集并规定豁免；语义考古
  职责划入 review 三轴（diff 行）与 apply 态全文体检（被触碰文件），
  「review 三轴」加"专职全文考古步骤"Scenario。
- `health-check`（由 `archive-health-check` 改名）：体检扩成两态触发
  （apply 态扫 diff 触碰文件全文 / archive 态扫改动面之外存量），加语义考古
  维，边界条款改准"diff 行归三轴、被触碰文件全文归 apply 态体检"。
- `ci-matrix`：「治理脚本单测进 CI」——覆盖率范围与阈值移入根
  `pyproject.toml` 单一真相源，地板范围扩至 `coverage_gate.py` 与
  `check_comments.py`。

## Impact

- 门禁脚本：`scripts/check_comments.py`（扩面+扩模式+豁免表）。
- 配置文件存量：`.github/workflows/ci.yml`、`rust-toolchain.toml`。
- 主 spec 正文措辞：`api-contract`、`ci-matrix`、`memory-lifecycle`、
  `oracle-harness`、`workspace-layout`、`zero-copy-roundtrip` 共 11 处
  考古叙述改写；`touchstone-core` 与 `project-governance` 的 3 处命中
  经判定为当前契约表述，保留不改（判定留痕 tasks.md）。
- 治理与流程：`AGENTS.md`「改动要有去向」措辞、`openspec/config.yaml`
  （apply guidance 加 apply 态体检一步、archive guidance 的 spec 名指针更新）、
  `openspec/specs/README.md` 路由行改名。
- 覆盖率：根 `pyproject.toml`（`[tool.coverage]`）、根 `package.json`
  （`check:py` 删 `--cov` 参数）、`scripts/tests/`（阅卷人补测 2 条）。
- 命令面：`pnpm check:meta` / `pnpm check:md` 入口与退出码契约不动；
  `check:py` 命令简化但名称与退出码契约不变。
- 不改动：`scripts/check_md.py`（不加中文考古词表）、`coverage_gate.py`
  本体逻辑。

## Non-goals

- 不在 `openspec/config.yaml` 加**清理**步骤（自动改写文件的流程步骤）——
  存量清理仍须人工点名；本 change 加的是**审查**步骤（只读出发现），两者
  边界见 design.md D12。
- 不给 `check_md.py` 新增中文考古词模式——语义考古交 AI 审查，不靠词表硬匹配。
- 不清理 `openspec/changes/archive/**` 与 lessons-learned 账本——冻结历史证据。
- 不改 `coverage_gate.py` 的 floor 能力与地板 0 单测。
- 不改任何命令名、CI 步骤顺序与退出码契约。

## Prior art

- 仓库内既有门禁先例：`scripts/check_comments.py` 的 `DEV_DOC_POINTERS`、
  `ARCHAEOLOGY`、动态 change 名生成（本 change 在其上扩面+扩模式）。
- 仓库内既有豁免先例：`scripts/check_md.py` 对 archive 与 lessons-learned
  账本的豁免（`ledger` 变量、`in_archive` 判定），本 change 沿用同口径。
- 治理 spec 既有 Scenario「治理 spec 反例不触发自身门禁」已定"描述被禁词用
  描述性表达"口径，本 change 直接复用。

## 专家增补

- 顺序上先让新门禁变红再清存量：先提交扩面+扩模式使 `ci.yml` 全部存量报红，
  逐条清到绿——"门禁确实抓到了"可被 CI 记录证明，符合 governance
  「元规则 规则生命周期」退役判据②（先证明违规样例变红）。
- 改写语义守恒：spec 正文删考古归因时保留当前契约结论（如 `upload` 那条改写成
  "当前无 `upload` 概念"，结论留、归因删），避免文档反而丢信息。
- 误报回归锁：把 `touchstone-core/spec.md` 的"不再是合法选项行"（描述输入行为
  结果，非考古）与 `api-contract/spec.md` 的契约声明式 `废止` 写成
  `scripts/tests/` 的"必须不触发"负向用例，锁死误报回归。
- `deprecated` 一词不进任何模式——`Deprecated: use X instead` 是标准契约用语。
- 覆盖率范围迁移必须整体搬、不留命令行残留：`pyproject.toml` 与 `check:py`
  两处并存即两份清单漂移（账本 LL-076 同因），`ci-matrix` delta 的
  「覆盖率配置单一真相源」Scenario 负责执法。
- apply 态体检的位置钉死在三轴 review 之后、`check:outdated` 之前，且
  "是否豁免"由机械规则（触碰文件是否全在豁免目录）判定，不留"这次不算"
  的临场判断空间。
