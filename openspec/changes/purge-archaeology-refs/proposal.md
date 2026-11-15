# 清除常驻文档与配置中的考古文字，并把门禁扩面到配置文件

## Why

代码注释"只写当前契约、不写开发过程"这条规矩目前只覆盖 `.rs`/`.py`/`.ts`，
CI 与配置文件（`.yml`/`.yaml`/`.toml`）是门禁真空区，已积累大量开发过程泄漏：
`ci.yml` 有 135 行注释，含 `LL-011`/`LL-034`/`LL-047` 编号、CI run 号
`43603143333`、`Re-enabled 2026-09-26` 日期、`design decision 7` 讨论代号；
`rust-toolchain.toml` 注释指向 `workspace-layout spec`。这些指针要求读者打开
规划文档才能理解配置，且随归档与改名而失效。存量规模大，单开本 change 一次性
清理并上门禁防复发。

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
- `scripts/coverage_gate.py` 的 floor 参数能力与地板 0 单测保留——它是通用
  阈值工具，0 只是合法输入值，不随本次清理阉割。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `project-governance`：「元规则 代码只写使用信息」扫描范围从 `.rs`/`.py`/`.ts`
  扩至 `.yml`/`.yaml`/`.toml`，模式定为封闭固定形态集并规定豁免；新增
  "语义考古由 AI 审查承担"的职责划分（「代码只写使用信息」条与「review 三轴」
  条各落一处）。

## Impact

- 门禁脚本：`scripts/check_comments.py`（扩面+扩模式+豁免表）。
- 配置文件存量：`.github/workflows/ci.yml`、`rust-toolchain.toml`。
- 主 spec 正文措辞：`api-contract`、`ci-matrix`、`memory-lifecycle`、
  `oracle-harness`、`workspace-layout`、`zero-copy-roundtrip` 共 11 处
  考古叙述改写；`touchstone-core` 与 `project-governance` 的 3 处命中
  经判定为当前契约表述，保留不改（判定留痕 tasks.md）。
- 命令面不变：`pnpm check:meta` / `pnpm check:md` 入口与退出码契约不动。
- 不改动：`scripts/check_md.py`（不加中文考古词表）、`coverage_gate.py`、
  `openspec/config.yaml`。

## Non-goals

- 不在 `openspec/config.yaml` 的 apply/sync/archive 加人工清理步骤——防复发
  只走门禁（流程步骤是软约束会被跳过；最小规则原则：动作边界优于过程管束）。
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
