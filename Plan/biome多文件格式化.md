# biome 多文件格式化能力（待拍板）

## 背景

升级 `@biomejs/biome` 到 2.6.6 时发现：biome 2.x 自带 Markdown 与 YAML
格式化器（除原有的 JS/TS/JSON 外）。这跟仓库现有的工具分工冲突——

- Markdown 由 Prettier 负责（`.prettierrc.json`）
- YAML 由 pnpm 约定（单引号等）

biome 的 Markdown 列表续行缩进、YAML 引号风格与上述两者不一致，
同一文件被两个工具抢着格式化会产生来回 diff。

## 当前处置（已落地）

在 `biome.jsonc` 的 `files.includes` 排除 `*.md`、`*.yaml`、`*.yml`，
让每类文件保持单一归属：md=Prettier、yaml=pnpm、js/ts/json=biome。
对应提交 `fix(tools): biome 2.x 排除 md/yaml`。

## 待决问题

是否反过来让 biome 统一接管 md/yaml（去掉 Prettier，全仓一个格式化工具）？

- 收益：工具链更少、配置更集中。
- 代价：md/yaml 全仓重新格式化产生大 diff；需重定 Prettier 现有规则到
  biome 等价配置；`.prettierrc.json` 与 `check:md` 流程要改。
- 现状倾向：维持排除（最小改动），等 biome 的 md/yaml 输出与团队习惯
  进一步对齐后再议。

## 决定后归位

- 若维持排除：本文件删除，规则已在 `biome.jsonc` 注释 + 提交历史。
- 若改由 biome 接管：迁入 ci-matrix / workspace-layout spec，更新
  `check:md` 与 `check:ts` 命令，删本文件。
