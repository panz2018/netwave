# Proposal

## Why

提交 `f0465d6` 新增的 `browser/scripts/dump.mjs` 与 `browser/vitest.e2e.config.ts`
带着 biome 违规（未用导入、import 未排序）连提多个 commit 推上远端，CI run #235
的 lint job 红（`pnpm check` → `check:ts` 退出码 1）。同轮排查又发现本地
`pnpm check` 还有第二处红：`check:py` 因 `scripts/check_proposal.py` 覆盖率
99.82%（100% 地板）失败——它是 `9dc6fa1` 引入的回归，被 biome 先红短路掩盖。
"改完没跑全量 `pnpm check` 就提交"这类事故账本已记 LL-036/LL-102 同族三次，
靠自觉拦不住；同时 biome 的 warn 级诊断（如 `noNonNullAssertion`）不挡闸门，
造成"编辑器报警、闸门放行"的口径分裂。

## What Changes

- 新增仓库内 `pre-commit` 钩子（`.githooks/pre-commit`），提交前原样跑全量
  `pnpm check`，失败即拦下并提示跑 `pnpm fix`（只拦不自动改）。
- `package.json` 新增 `prepare` 脚本，`pnpm install` 时自动
  `git config core.hooksPath .githooks`，钩子在每台机器/每个 agent 环境零手工生效。
- `check:ts` 加 `--error-on-warnings`，biome 的 warn 级诊断从此阻断闸门。
- 存量清零：修 `browser/scripts/dump.mjs`（删未用导入 `mkdirSync`、import 排序）
  与 `browser/vitest.e2e.config.ts`（两处非空断言 `covDir!`/`covOut!` 改显式判空）。
- 补 `scripts/tests/test_check_proposal.py` 夹具覆盖 `_checked_item_texts`
  未触达分支（125/129 两行），使 `check:py` 回 100%。
- 账本新增一条 workflow scope LL：提交前必跑 `pnpm check`，已由 pre-commit
  钩子强制。吸收并删除 `Plan/biome警告升级为错误.md`；`CONTRIBUTING.md` 补一句
  钩子说明。

## Capabilities

### New Capabilities

（无——不新开能力，钩子与 warn 阻断都属既有 lint 门槛的收紧。）

### Modified Capabilities

- `ci-matrix`: 新增 Requirement——提交前钩子强制全量 `pnpm check`（经
  `prepare` 自动安装、只拦不修、CI lint job 保持兜底）；`check:ts` 的 biome
  warn 级诊断 MUST 阻断闸门。

## Impact

- 配置：`.githooks/pre-commit`（新）、`package.json`（`prepare`、`check:ts`）。
- 代码：`browser/scripts/dump.mjs`、`browser/vitest.e2e.config.ts`、
  `scripts/tests/test_check_proposal.py`。
- 文档：`CONTRIBUTING.md`、lessons-learned `workflow.md` + `INDEX.md`、
  删除 `Plan/biome警告升级为错误.md`。
- CI：`.github/workflows/ci.yml` 不改——lint job 继续作为钩子被
  `git commit -n` 绕过时的兜底。
- 不触碰产品代码、公开 API、数据布局；无跨端影响。

## Non-goals

- 不把完整 `pnpm check` 拆成暂存文件级增量检查（全量秒级已够，实现最小）。
- 钩子不做自动修复（不 `--write`、不动暂存区），防止提交混入未确认改动。
- 不改 CI lint job 的步骤序列与命令口径。
- 不逐条在 `biome.jsonc` 里把规则 severity 设为 error（走命令行开关一次封死）。

## Prior art

- 仓库内既有闸门：根 `package.json` 的 `check`/`fix` 脚本族与 CI lint job
  （`.github/workflows/ci.yml`）——钩子直接复用 `pnpm check`，零新口径。
- biome 官方 `--error-on-warnings` 开关：
  <https://biomejs.dev/reference/cli/#biome-check>（本机 biome 2.6.9
  `biome check --help` 实测支持）。
- git 原生 `core.hooksPath`（<https://git-scm.com/docs/git-config#Documentation/git-config.txt-corehooksPath>），
  不引入 husky/lefthook 等额外依赖。

## 专家增补

- 钩子失败输出末尾附 `pnpm fix` 提示与 `-n` 绕过后果（CI lint job 仍红），
  降低使用者困惑——落点 `.githooks/pre-commit` 报错文案。
- `prepare` 脚本在 CI 上同样执行 `git config core.hooksPath`，CI 不 commit
  故无害；但浅克隆/无 `.git` 场景（如 `pnpm fetch` 缓存构建）`git config`
  会失败——落点 `package.json` `prepare`，命令前置 `git rev-parse --git-dir`
  判空短路。
- 补测夹具须对真实输出实测（LL-108 同族）：`scripts/tests/test_check_proposal.py`
  新用例先本地跑出 red（覆盖率缺行消失）再收进 `check:py`。

## 已定裁决

- `pre-commit钩子`：采用仓库内 `.githooks/pre-commit` + `core.hooksPath`
  方案（不只补账本纪律），提交前原样跑全量 `pnpm check`，接受冷缓存偶发
  分钟级等待（热缓存实测约 16s）。
- `只拦不修`：钩子失败仅报错并提示 `pnpm fix`，MUST NOT 自动修复或改动暂存区。
- `prepare自动安装`：根 `package.json` 新增 `prepare` 脚本执行
  `git config core.hooksPath .githooks`，随 `pnpm install` 生效，不靠文档手工步骤。
- `warn阻断闸门`：`check:ts` 加 `--error-on-warnings`（命令行开关路线，
  不走 biome.jsonc 逐条 severity）。
- `存量清零`：修 `browser/scripts/dump.mjs`（未用导入 + import 排序）与
  `browser/vitest.e2e.config.ts`（两处非空断言改显式判空）。
- `覆盖率补测`：给 `scripts/check_proposal.py` 的 `_checked_item_texts`
  未覆盖分支（125/129 行）补测试夹具，`check:py` 回 100%。
- `CI保持原样`：`.github/workflows/ci.yml` 不改，lint job 继续兜底
  `git commit -n` 绕过场景。
- `spec落ci-matrix`：闸门口径收紧的 Requirement 落 `ci-matrix` delta，不新开 spec。
- `账本记LL`：新增 workflow scope 账本条目"提交前必跑 pnpm check，已由
  pre-commit 钩子强制"（附 CI run #235 证据）。
- `文档波及两处`：`CONTRIBUTING.md` 补钩子说明一句；
  `Plan/biome警告升级为错误.md` 被本 change 吸收后同轮删除。
- `单change承载`：钩子 + warn 升级 + 存量清零 + 覆盖率补测四项合入本 change
  `tighten-lint-gates`，不拆分。
- `跳过归档体检`：本 change 归档时跳过 health-check spec 的 archive 态只读
  体检（archive guidance 第 2 条）；apply 态被触碰文件体检（tasks 4.7）不受
  影响照常执行。
