# Spec Delta

## ADDED Requirements

### Requirement: 提交前钩子强制全量 lint 闸门

仓库 MUST 提供版本化的 git `pre-commit` 钩子，经 `core.hooksPath` 指向仓库内
钩子目录，并由根 `package.json` 的安装期脚本在依赖安装时自动配置，使人与
agent 环境零手工步骤生效。钩子 MUST 原样调用根聚合入口 `pnpm check`（命令
口径唯一承载在 `package.json`，钩子内 MUST NOT 复制其子命令），失败时以非 0
退出码拦下提交并提示修复入口；钩子 MUST NOT 自动修复文件或改动暂存区。
CI lint job 保持原样，作为钩子被绕过时的兜底。

- 容差：存在性与退出码闸门，无数值阈值——钩子文件存在、`pnpm check` 失败
  即提交被拦，无时间上限（冷缓存耗时不设门槛）。

#### Scenario: 带 lint 违规的提交被钩子拦下

- **WHEN** 工作区存在使 `pnpm check` 退出码非 0 的改动（如 biome error）
- **AND** 执行 `git commit`（未加 `-n`）
- **THEN** 提交被拦下、退出码非 0，输出指向 `pnpm check` 失败与修复入口

#### Scenario: 依赖安装自动启用钩子

- **WHEN** 在干净 clone 上执行 `pnpm install`
- **THEN** `git config core.hooksPath` 返回仓库内钩子目录，后续
  `git commit` 触发钩子

#### Scenario: 钩子被绕过时 CI 兜底

- **WHEN** 以 `git commit -n` 绕过钩子提交带病改动并推送
- **THEN** CI lint job 因 `pnpm check` 失败而 FAIL（既有口径不变）

### Requirement: biome warn 级诊断阻断闸门

`check:ts` MUST 使 biome 的 warn 级诊断（如 `noNonNullAssertion`）导致退出码
非 0，消除"编辑器报警、闸门放行"的口径分裂；存量 warn MUST 清零后该口径
方可生效。

- 容差：退出码闸门——任一 warn 级诊断出现即 `pnpm check:ts` 非 0，无数量阈值。

#### Scenario: warn 级诊断使闸门红

- **WHEN** 任一受 biome 检查的文件存在 warn 级诊断
- **THEN** `pnpm check:ts` 退出码非 0，`pnpm check` 链随之失败

#### Scenario: 存量清零后闸门绿

- **WHEN** 本 change 修复全部已知 warn 存量（`browser/scripts/dump.mjs`、
  `browser/vitest.e2e.config.ts`）
- **THEN** `pnpm check:ts` 退出码 0，输出无 warn 级诊断
