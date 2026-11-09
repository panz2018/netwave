# Proposal

## Why

biome 2.x 自带 YAML 格式化器（官方称解析器 100% 通过官方测试套件、格式化
100% 兼容 Prettier），而仓库的 YAML 目前处于格式化真空——"pnpm 约定单引号"
只是散文，没有任何闸门执法。把 YAML 交给 biome 认领，成本经实测为零
（全仓 41 个 YAML dry-run 无一文件改动），顺带补上无人执法的空白，并让
"每类文件只有一个格式化工具认领"这条归属不变式从注释升级为 spec 条文。

## What Changes

- `biome.jsonc`：移除 `!**/*.yaml`、`!**/*.yml` 两条排除，YAML 纳入
  `pnpm check:ts` / `pnpm fix:ts` 的 biome 管辖；引号风格用 biome 默认
  （double），不加 `quoteStyle` 覆盖；顶部注释同步改写——"YAML 由 pnpm
  约定（单引号）"自此成为过时事实，改为记录 yaml=biome 归属与实测零 diff。
- ci-matrix spec：新增一条 Requirement，规定格式化归属唯一
  （md = markdownlint + Prettier，yaml/js/ts/json = biome），执法复用
  现有双闸门（`check:ts` 与 `check:md` 重叠即红），不新增脚本。
- `.vscode/extensions.json`：推荐列表补 biome 官方扩展（现有列表有
  markdownlint 而无 biome，编辑器层与闸门层不对齐）。
- `Plan/biome多文件格式化.md`：结论全部吸收，随本 change 归档删除。
- 不改动：根 `package.json`、`.github/workflows/ci.yml`（现有闸门链已覆盖）。

## Capabilities

### New Capabilities

（无——不引入新能力目录。）

### Modified Capabilities

- `ci-matrix`：新增 Requirement「格式化归属单一来源」——每类文件的格式化
  工具唯一认领，重叠由现有 `check:ts` / `check:md` 双闸门拦截。

## Impact

- 配置：`biome.jsonc`（排除名单与注释）、`.vscode/extensions.json`。
- 闸门：`pnpm check:ts` 覆盖面扩至 YAML（命令本身不变）；`pnpm check:md`
  不变；`package.json` 与 CI 零改动。
- 文件：YAML 预期零 diff（dry-run 实测）；若个别文件出现意外重排，
  以 apply 期实际输出为准汇报。
- 文档：`Plan/biome多文件格式化.md` 删除；spec 路由表无结构变化
  （ci-matrix 目录已存在）。
- 无产品代码、无公开 API、无数据布局变化，不直接涉及铁律编号。

## Non-goals

- Markdown 不换 biome：biome 官方自报 md 格式化仅约 92% 兼容 Prettier
  （官方 2.6 发布说明，URL 见 Prior art），本地 dry-run 实测 36 个文件
  存在列表续行缩进分歧；md 维持 Prettier 归属。再评估触发器：biome 的
  markdown formatter 离开试验期且兼容率在 release notes 中显著提升时，
  重开归属议题。
- 不新增归属检查脚本：重叠一旦发生，现有双闸门必有一道红（biome 与
  Prettier 对 md 存在真实分歧即为反证），第三脚本只在"同时改两边配置"
  的极端场景有额外价值，违反最小规则原则。
- 不加 `yaml.formatter.quoteStyle: "single"`：维持 biome 默认，仓库现有
  YAML 无引号型标量，实测零冲突。
- 不移除 Prettier 依赖：其仍负责 `**/*.md`。

## Prior art

- <https://github.com/biomejs/biome/releases/tag/@biomejs/biome@2.6.6> ——
  biome 官方 2.6 发布说明（YAML/Markdown 格式化能力与兼容率声明出处）。
- <https://biomejs.dev/introduction/language-support> —— biome 语言支持
  矩阵与 Markdown 嵌入格式化选项。
- 仓库内先例：`biome.jsonc` 顶部注释（2026-09-25 定案 js/ts/json=biome、
  排除 md/yaml 的原始裁决）、`.prettierrc.json`（md 归属 Prettier 的
  现行配置）。

## 专家增补

- 把归属不变式写进 `openspec/specs/ci-matrix/spec.md` 成文法条，而非只
  活在 `biome.jsonc` 注释里——注释无执法力，spec 条文才能被 review
  Standards 轴引用。
- `.vscode/extensions.json` 补 `biomejs.biome` 推荐，防止各人本地缺扩展、
  保存时不触发格式化而与闸门输出打架。
- 在 Non-goals 写明再评估触发器（biome 的 markdown formatter 出试验期且
  兼容率在官方 release notes <https://github.com/biomejs/biome/releases>
  中提升时重开 `biome.jsonc` 的 md 排除议题），防止"以后再说"变成永远不说。
