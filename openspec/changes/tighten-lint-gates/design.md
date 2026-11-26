# Design

## Context

见 proposal.md - Why。现状约束：闸门命令唯一口径在根 `package.json`
（CI lint job 与本地共用）；git 钩子默认在 `.git/hooks/` 不随 clone 分发；
本机 biome 2.6.9 实测支持 `--error-on-warnings`；热缓存全量 `pnpm check`
实测约 16s（md 4.6s + biome 0.03s + fmt/clippy ~1s + py 4.8s + meta 5s），
clippy 冷缓存耗时未实测。

## Goals / Non-Goals

**Goals:**

- 钩子与 CI 共用同一条命令口径（`pnpm check`），零复制、零漂移。
- 钩子安装对使用者透明（`pnpm install` 即生效）。

**Non-Goals:**

- 不做暂存文件级增量检查、不做钩子内并行化提速（全量秒级已够）。
- 不引入 husky/lefthook 等钩子管理依赖。

## Decisions

- **钩子内容 = `pnpm check` 一条命令**：备选是逐条调 biome/fmt/ruff 子命令，
  否决——复制 `package.json` 口径即漂移源（tasks 规则同旨）。钩子头部注释
  说明用途与 `-n` 后果，失败文案提示 `pnpm fix`。
- **`prepare` 脚本前置 `.git` 判断**：`pnpm install` 在无 `.git` 的环境
  （发布包安装、缓存构建）会因 `git config` 失败而中断安装，故
  `prepare` 用 `git rev-parse --git-dir` 判空短路。备选：裸跑
  `git config`，否决——CI/发布链路可能因此红。
- **warn 阻断走 CLI 开关而非 biome.jsonc severity**：`--error-on-warnings`
  一行改动封死现在与将来全部 warn 规则；逐条 severity 只挡点名规则，
  biome 升级新增 warn 规则会再漏（Plan 立项文件实测的口径分裂即此）。
- **非空断言修复 = 显式判空收窄类型**：`vitest.e2e.config.ts` 的
  `covDir!`/`covOut!` 所在分支由环境变量开关守卫，改为在分支入口显式
  `if (!covDir) throw`（配置加载期 fail-fast），TS 自然收窄，不碰覆盖率
  链行为。

## Risks / Trade-offs

- [冷缓存 clippy 使个别提交等分钟级] → 已拍板接受（正确性优先）；
  紧急时 `git commit -n` + CI 兜底。
- [`prepare` 在 pnpm workspace 各子包 install 时重复执行] → `git config`
  幂等，重复无害。
- [钩子拦下 agent 的提交循环造成困惑] → 失败文案直接给出 `pnpm fix`
  与 `-n` 两条出路；账本 LL 记录机制存在。

## Migration Plan

存量清零（biome 4 处 + 覆盖率补测）先行，`pnpm check` 全绿后再引入钩子，
保证钩子上线首日不误拦干净提交。回滚 = 删 `prepare`/钩子文件，无数据迁移。

## Open Questions

（无）
