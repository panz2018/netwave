# biome 警告升级为错误（待执行）

## 背景（为什么有这条）

biome 的 `recommended` 预设里，部分规则（如 `lint/style/noNonNullAssertion`、
`lint/complexity/useOptionalChain`）严重级别是 **warn**，不是 error。
`biome check .`（= `pnpm check:ts`）只有 error 才让退出码变非 0，所以这类
警告**不挡闸门**：编辑器里 Biome 插件实时标黄提示，`pnpm check` 却全绿。

实测证据（2026-11-22）：`typescript/vitest.browser.config.ts` 第 35、58 行
两处非空断言 `covDir!` / `covOut!` 触发 `noNonNullAssertion`，单独跑该文件
`biome check` 退出码 0、输出 `Found 2 warnings`——警告被闸门放行。

## 目标

让 biome 警告也变成阻断项，**当场必须修**，不再出现"编辑器报警、闸门放行"
的口径分裂。

## 待执行任务（之后再改，本文件只立项）

1. **配置层**：在 `biome.jsonc` 的 `linter.rules` 下把警告提升为 error。
   二选一（执行时定）：
   - 全局：`linter.rules.*.noNonNullAssertion` 等逐条 `"severity": "error"`；
     或 biome 2.x 的 `linter.rules` 段对目标规则统一设 error。
   - 命令行：`check:ts` 加 `--error-on-warnings`（若该版本 biome 支持），
     使任何 warning 都让退出码非 0。
   - 出处：[biome linter rules](https://biomejs.dev/linter/rules/)。
2. **存量清零**：配置改完后 `pnpm check:ts` 会因现有警告变红，须当场修：
   - `typescript/vitest.browser.config.ts:35` `covDir!`、`:58` `covOut!`
     ——把 `chainOn` 收窄成类型守卫（或显式判空），让 TS 自行确认非空，
     去掉 `!`。
   - 全仓复跑 `pnpm check:ts`，把其余被升级为 error 的 warning 一并清零。
3. **闸门验证**：`pnpm check` 全绿（退出码 0）才算完成；改任何 `.md` 后跑
   `pnpm check:md`。

## 波及面（执行时同步核对）

- `package.json` 的 `check:ts` / `fix:ts`（若走命令行开关路线）。
- `biome.jsonc` 配置本体。
- lessons-learned 账本：记一条"biome warn 不挡闸门，已升级为 error"防复发。

## 注意

- 这是**风格闸门收紧**，不改产品逻辑；改 `vitest.browser.config.ts` 时只动
  非空断言写法，不碰覆盖率链行为。
- 升级后可能一次性暴露较多存量 warning，按文件逐个清零，不批量 `--write`
  盲改（避免误伤）。
