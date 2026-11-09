# Design

## Context

动机见 proposal.md - Why。当前状态：`biome.jsonc` 的 `files.includes` 用
`!**/*.yaml`、`!**/*.yml` 把 YAML 排除在 biome 之外，注释声称"YAML 由 pnpm
约定（单引号）"；但仓库没有任何命令检查 YAML 格式，该约定无执法者。
`pnpm check:ts`（`biome check .`）与 `pnpm check:md`（markdownlint +
prettier + `scripts/check_md.py`）是两条独立闸门，构成归属重叠时的拦截网。

## Goals / Non-Goals

**Goals:**

- YAML 有格式化执法者，纳入 biome 认领，`package.json` 与 CI 命令零改动。
- 归属不变式（每类文件唯一认领者）在 ci-matrix spec 成文。

**Non-Goals:**

- 设计级边界：不改 biome 的全局格式选项（indent/lineWidth 等），
  只动 `files.includes` 与注释；不为归属不变式编写执法脚本；
  不调整 `.prettierrc.json`。

## Decisions

1. **引号风格用 biome 默认（double），不加 `yaml.formatter.quoteStyle`**。
   备选：显式设 `"single"` 以贴合旧散文约定——否决：实测全仓 41 个 YAML
   无引号型标量（`.github/workflows/ci.yml` 中的 `'linux-x64'` 是矩阵
   表达式字符，非风格性引号），单引号约定既无存量也无执法价值，加配置
   反而多一条要维护的规则（最小规则原则）。
2. **不新增归属检查脚本**。备选：`scripts/check_format_ownership.py` 断言
   biome 与 Prettier 认领范围不相交——否决：biome 不感知 Prettier，该脚本
   只能静态解析两边配置；而重叠一旦生效，现有双闸门必有一道红（biome 与
   Prettier 对 Markdown 存在真实分歧——dry-run 实测 36 个文件的列表续行
   缩进差异——即为反证），第三脚本仅在"同时改两边配置使输出一致"的极端
   场景有增量价值，不值得其维护成本。
3. **归属条文写进 ci-matrix 而非 workspace-layout 或新能力目录**。备选：
   workspace-layout（管仓库结构与脚本分层，但现有条文聚焦
   `scripts/versions/`，不贴）；新开能力目录（为一条 Requirement 开目录过
   重）——ci-matrix 已收闸门类要求（覆盖率门槛、治理脚本单测进 CI），
   同类相聚。
4. **`.vscode/extensions.json` 补 `biomejs.biome`**。现有推荐列表有
   `davidanson.vscode-markdownlint` 却无 biome，编辑器层与闸门层不对齐；
   补一项即对齐，无配置冲突。

## Risks / Trade-offs

- [biome 对个别 YAML 产生未预期重排（如 GitHub Actions 的 `on:` 键、
  长字符串折行）] → apply 期先跑 `pnpm fix:ts` 再 `git diff` 逐文件核对，
  意外重排超出一处即停下汇报；dry-run 已实测 41 文件零改动、`ci.yml`
  解析通过作为基线证据。
- [双闸门执法依赖"两工具对 md 有分歧"这一事实，若 biome 未来追平
  Prettier，Scenario「Markdown 认领不重叠」的拦截力减弱] → proposal
  Non-goals 已写明再评估触发器（biome md formatter 出试验期且兼容率
  提升），届时重开议题而非现在预防。
- [pnpm-lock.yaml 等生成物被误纳入格式化] → 排除项保留 `!**/pnpm-lock.yaml`
  与既有生成物目录排除，本次只移除 `*.yaml`/`*.yml` 两条通配。

## Migration Plan

单步配置变更，无部署顺序：改 `biome.jsonc` → 跑 `pnpm check:ts` 验证
（预期零 diff）→ 提交。回滚 = revert 该提交，无数据或 API 影响。
