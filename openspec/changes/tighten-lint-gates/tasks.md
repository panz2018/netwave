# Tasks

## 1. 存量清零（先于钩子，保证钩子上线首日不误拦）

- [ ] 1.1 `存量清零`：修 `browser/scripts/dump.mjs`——删未用导入 `mkdirSync`、
      import 排序（`node:fs` 在 `node:http` 前），验证：`pnpm check:ts` 该文件零诊断
- [ ] 1.2 `存量清零`：修 `browser/vitest.e2e.config.ts` 两处非空断言
      （`covDir!`/`covOut!` 改分支入口显式判空 fail-fast），验证：`pnpm check:ts`
      该文件零诊断
- [ ] 1.3 `warn阻断闸门`：根 `package.json` 的 `check:ts` 加
      `--error-on-warnings`，验证：`pnpm check:ts` 退出码 0（1.1/1.2 已清零）；
      临时注入一个 warn 复测退出码非 0 后还原
- [ ] 1.4 `覆盖率补测`：给 `scripts/check_proposal.py` 的
      `_checked_item_texts` 未覆盖分支（125/129 行）在
      `scripts/tests/test_check_proposal.py` 补夹具（red 先行：先跑
      `pnpm check:py` 记录 FAIL，补后回 100%），验证：`pnpm check:py` 退出码 0

## 2. pre-commit 钩子与自动安装

- [ ] 2.1 `pre-commit钩子`：新建 `.githooks/pre-commit`（可执行），内容为
      原样调用 `pnpm check`；`只拦不修`——失败仅报错并提示 `pnpm fix` 与
      `-n` 绕过后果（CI lint job 仍红），不自动修复、不动暂存区
- [ ] 2.2 `prepare自动安装`：根 `package.json` 加 `prepare` 脚本，前置
      `git rev-parse --git-dir` 判空短路后执行 `git config core.hooksPath .githooks`；
      验证：重跑 `pnpm install` 后 `git config core.hooksPath` 返回 `.githooks`
- [ ] 2.3 钩子端到端验证：临时注入 biome error 后 `git commit` 被拦（退出码
      非 0），还原后提交通过；`CI保持原样`——核对 `.github/workflows/ci.yml`
      零改动（git diff 无该文件）

## 3. 账本与文档

- [ ] 3.1 `账本记LL`：lessons-learned `workflow.md` 新增条目"提交前必跑
      `pnpm check`，已由 pre-commit 钩子强制"（附 CI run #235 证据），
      `INDEX.md` 补路由行
- [ ] 3.2 `文档波及两处`：`CONTRIBUTING.md` 开发流程处补一句钩子说明
      （`pnpm install` 经 `prepare` 自动装、跑 `pnpm check`、`-n` 可绕、CI 兜底）
- [ ] 3.3 `spec落ci-matrix`：apply 时按本 change delta 同步主 spec
      `openspec/specs/ci-matrix/spec.md`（sync specs）

## 4. apply 收尾（config.yaml guidance 八锚点）

- [ ] 4.0 `单change承载`：收尾核对钩子+warn 升级+存量清零+覆盖率补测四项
      全部落在本 change 的 diff 内交付，无拆散遗漏
- [ ] 4.1 `Plan/`：删除 `Plan/biome警告升级为错误.md`（结论已被本 change
      吸收），删后跑 `pnpm check:md`
- [ ] 4.2 `三态时效`：扫 `openspec/specs/` 全目录，对照本 change 产出
      更新/新增/退役三态结论留痕（预期：仅 ci-matrix 更新，无新增/退役）
- [ ] 4.3 `pnpm test` 全绿（先于 review，排除实现断裂）
- [ ] 4.4 `旧名清零`：本次删除 `Plan/biome警告升级为错误.md`，全仓 grep
      该文件名旧引用（排除 archive/target/dist/node_modules/.venv）确认零残留
- [ ] 4.5 `引用归位`：对 git diff --name-status HEAD 的 R/D 项（预期含
      `Plan/biome警告升级为错误.md`）grep 全仓 spec/文档描述该文件位置职责的
      散文并更新；完成记录列出 R/D 清单（MUST 在 commit 前跑）
- [ ] 4.6 `三轴`：按 governance spec review 三轴对照本 change 工件审实现
      diff，diff 文件集逐文件对上 tasks.md，硬伤清零才准入后续
- [ ] 4.7 `体检`：被触碰文件全文只读体检（health-check spec apply 态）
- [ ] 4.8 `迟到追加`：复查 proposal.md `## 已定裁决` 每个关键词载体任务
      已打勾，未打勾即红
- [ ] 4.9 `check:outdated`：跑 `pnpm check:outdated` 并按 dependency-upgrade
      spec 消化所报 LAG，复跑至退出码 0（SUMMARY 归零）
- [x] 4.10 `跳过归档体检`：本 change 归档时跳过 health-check spec 的 archive
      态只读体检——人工点名跳过 2026-11-26（apply 态体检见 4.7，照常执行）
