# typescript 源码化规划（工具链已拍板 2026-09-25，源码改写未执行）

## 背景与动机

当前 `typescript/src/` 只有手写 `.mjs`/`.cjs`/`.js` 壳文件 + 手写
`index.d.ts`，存在双份维护问题：

- `index.d.ts` 契约与 `index.node.mjs`/`index.browser.mjs`
  里的 JSDoc 各写一遍，改签名要同步两处，会漂移。
- CJS 壳（`index.node.cjs`）是 ESM 壳的手工翻译版——正是打包器要解决的"多格式输出"痛点。
- 目标是让 TS 消费者拿到真正的类型与可维护源码，所以不能只有壳文件，需要 TS 源码。

2026-09-25 评估过
[Rslib](https://rslib.rs/)（web-infra-dev/rslib）：在"无 TS 源码"的前提下不需要它；一旦源码化，它的 ESM+CJS+`dts`
一次输出、`target: node/web` 分壳、Worker 语法原生识别就真正对上了。

## 目标结构

```text
src/
  types.ts          # NetwaveBuffer 等公共类型（契约单一来源）
  index.node.ts     # node 壳：import napi glue（external）
  index.browser.ts  # browser 壳：import wasm-pack glue（external）
  worker.ts
  standalone.ts
```

关键约束：

- napi 生成的 `index.node.generated.mjs` 与 wasm-pack glue 保持
  **external**（不进 bundle）；打包器只编译本项目自己的壳，与 Rslib 的
  `external`/`autoExternal` 模型吻合。
- `index.d.ts` 改为从源码生成，手写契约并入 `types.ts`。
- 现有 `publish_shell.mjs` 发布逻辑保持不变（壳文件重写规则见
  [typescript/README.md](../typescript/README.md)）。
- 零拷贝契约（`NetwaveBuffer`
  描述符、await 后重建视图）不受影响——打包只碰 JS 壳，不碰 `.node`/`.wasm`
  二进制路径。

## 工具选型（2026-09-25 已拍板）

| 环节                        | 定稿                                                                                                                   | 理由                                                                                                            |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 包管理                      | pnpm（不动）                                                                                                           | workspace 主场，已定                                                                                            |
| 测试/覆盖率                 | Vitest（不动，100% 阈值）                                                                                              | wasm/ESM 场景唯一顺手                                                                                           |
| lint+format (JS/TS/JSON)    | **Biome**（全仓库）                                                                                                    | 单二进制替代 ESLint+Prettier 三件套；薄壳用不上插件生态；与 Rust 工具气质一致                                   |
| format (Markdown)           | **Prettier `proseWrap: "preserve"`**（全仓库 `*.md`，忽略 `.claude/`；2026-09-26 由 `always` 改回：中文+行内代码碎断） | 统一列表/标题结构、不重排段落换行；markdownlint 关掉与 Prettier 冲突的规则只留内容性规则                        |
| 打包                        | **tsdown**（Rslib 降备选）                                                                                             | 只需"TS→ESM+CJS+dts+IIFE + external glue"，Rslib 差异化能力（MF/样式/wasm 源码集成）全用不上，tsdown 配置量最小 |
| `.node`/`.wasm` 二进制+glue | napi build / wasm-pack（不动，external）                                                                               | 打包器不介入二进制管线                                                                                          |

**CJS 去留（已拍板：保留）**：`build:native` 本就跑两遍 napi 各出 ESM/CJS
glue，tsdown `format: ["esm","cjs"]` 顺手出 CJS，成本近零；Jest 默认 CJS、老工具
`require()` 场景仍在，防御性保留，等真实用户反馈再议砍除。

tsdown 产物清单：`index.node.mjs` / `index.node.cjs` / `index.browser.mjs` /
`index.d.ts` / `standalone.js`（IIFE，HTML `<script>` 直接导入）/
`netwave.worker.js`。

## 执行步骤

0. （已落地 2026-09-25）接入 `typescript/tsconfig.json`
   （strict+allowJs+noEmit）、根 `biome.jsonc`、根 `.prettierrc.json`
   （proseWrap preserve，只管 `*.md`）、markdownlint 关冲突规则、
   CI 加 biome/prettier/tsc 步骤 → 验证：`biome check .`、
   `prettier --check "**/*.md"`、`tsc --noEmit`、markdownlint、check_md 全绿。
1. 壳改写为 TS 源码（`types.ts` 收编 `index.d.ts` 契约）→
   验证：`tsc --noEmit` 通过、vitest 直接测 `.ts` 全绿。
2. 接入 tsdown，输出 esm（node/browser 分 target）、cjs 与 dts；
   napi/wasm glue 保持 external → 验证：`dist/` 产物与旧壳 exports
   逐一对齐（`exports.test.ts` 扩展断言）。
3. 测试入口切到源码；覆盖率 `/* v8 ignore */` 逐条保留理由 → 验证：`test:native`
   / `test:wasm` 覆盖率仍 100%。
4. 跨绑定对拍回归（`scripts/cross_compare.py`
   四端）→ 验证：逐 bit + 容差 + 篡改自检全绿。
5. 更新 [typescript/README.md](../typescript/README.md)
   的 Commands 与 Gotchas；本文件按 Plan 生命周期吸收进 spec/README 后删除。

## 风险与保留意见

- wasm 路径：打包器的 wasm 源码集成（compile/preserve 等模式）一律不启用，保持 wasm-pack
  `--target web`
  自带 glue；打包器不应介入 wasm 加载，否则 worker 内存不可 transfer 等已趟平的坑（见
  [typescript/README.md](../typescript/README.md) 的Implementation
  notes）会重踩。
- CI
  node 格子（当前注释禁用，待 typescript 人工审核恢复）届时需同步加入打包步骤。
