# Spec Delta

## ADDED Requirements

### Requirement: 格式化归属单一来源

每类源文件的格式化 MUST 由唯一工具认领：Markdown 归 markdownlint +
Prettier，YAML、JavaScript、TypeScript、JSON 归 biome。认领关系 MUST 在
`biome.jsonc` 的 `files.includes` 与 Prettier 的管辖范围中互斥表达——
任一文件类型不得同时被两个格式化工具认领（两工具对同一文件输出不一致时
来回格式化产生 ping-pong diff）。本要求 MUST NOT 依赖新增专用检查脚本
执法：现有双闸门（`pnpm check:ts` 跑 biome、`pnpm check:md` 跑 Prettier）
已构成拦截网——认领一旦重叠，两工具输出分歧必使其中一道闸门红。

#### Scenario: YAML 纳入 biome 认领

- **WHEN** 运行 `pnpm check:ts`
- **THEN** 仓库内 YAML 文件（`pnpm-lock.yaml` 等生成物除外）经 biome
  格式检查，未经格式化的 YAML 使闸门 FAIL——YAML 自此有执法者，不再是
  仅靠散文约定的真空

#### Scenario: Markdown 认领不重叠

- **WHEN** 有人从 `biome.jsonc` 的 `files.includes` 移除 Markdown 排除项
- **THEN** `pnpm check:ts` 因 biome 与 Prettier 对既有 Markdown 的格式
  分歧（列表续行缩进等）报 FAIL，重叠在合并前即被拦截——归属不变式由
  现有闸门兜底，无需第三工具

#### Scenario: 归属变更留痕

- **WHEN** 任何改动调整某类文件的格式化认领工具
- **THEN** 该改动 MUST 经 openspec change 提案并更新本 Requirement，
  `biome.jsonc` 注释与 spec 条文不得各说各话
