# typescript 源码化规划（待拍板，未执行）

## 背景与动机

当前 `typescript/src/` 只有手写 `.mjs`/`.cjs`/`.js` 壳文件 + 手写
`index.d.ts`，存在双份维护问题：

- `index.d.ts` 契约与 `index.node.mjs`/`index.browser.mjs` 里的 JSDoc
  各写一遍，改签名要同步两处，会漂移。
- CJS 壳（`index.node.cjs`）是 ESM 壳的手工翻译版——正是打包器要解决
  的"多格式输出"痛点。
- 目标是让 TS 消费者拿到真正的类型与可维护源码，所以不能只有壳文件，
  需要 TS 源码。

2026-09-25 评估过 [Rslib](https://rslib.rs/)（web-infra-dev/rslib）：
在"无 TS 源码"的前提下不需要它；一旦源码化，它的 ESM+CJS+`dts` 一次
输出、`target: node/web` 分壳、Worker 语法原生识别就真正对上了。

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
- 零拷贝契约（`NetwaveBuffer` 描述符、await 后重建视图）不受影响——
  打包只碰 JS 壳，不碰 `.node`/`.wasm` 二进制路径。

## 工具选型（待拍板）

| 方案 | 适用性 |
| --- | --- |
| Rslib | 一份配置出 ESM+CJS+`dts`；`target: node/web` 分开对应两个壳；Worker 原生识别 |
| tsdown (rolldown) | 同样能干，更轻；生态文档少于 Rslib |
| 裸 `tsc` 编两遍 | 仅在放弃 CJS（ESM-only）时才够简 |

**前置决策（阻塞项）**：是否砍掉 CJS 支持
（`exports["."].node.require`）。`engines: node>=22` 的包放弃 CJS 很常见：

- 砍掉 → `tsc` 单工具即可，无需引入任何打包器（最省路径）。
- 保留 → 采用 Rslib。

## 执行步骤（决策后展开）

1. 壳改写为 TS 源码（`types.ts` 收编 `index.d.ts` 契约）→
   验证：`tsc --noEmit` 通过、vitest 直接测 `.ts` 全绿。
2. 接入选定打包器，输出 `esm`（node/browser 分 target）、`cjs`（若保留）
   与 `dts`；napi/wasm glue 保持 external → 验证：`dist/` 产物与旧壳
   exports 逐一对齐（`exports.test.ts` 扩展断言）。
3. 测试入口切到源码；覆盖率 `/* v8 ignore */` 逐条保留理由 →
   验证：`test:native` / `test:wasm` 覆盖率仍 100%。
4. 跨绑定对拍回归（`scripts/cross_compare.py` 四端）→ 验证：逐 bit +
   容差 + 篡改自检全绿。
5. 更新 [typescript/README.md](../typescript/README.md) 的 Commands 与
   Gotchas；本文件按 Plan 生命周期吸收进 spec/README 后删除。

## 风险与保留意见

- wasm 路径：Rslib 的 wasm 支持针对源码 `import './x.wasm'` 语法
  （compile/preserve 模式）；本项目走 wasm-pack `--target web` 自带
  glue，打包器不应介入 wasm 加载，否则 worker 内存不可 transfer 等已
  趟平的坑（见 [typescript/README.md](../typescript/README.md) 的
  Implementation notes）会重踩。
- CI node 格子（当前注释禁用，待 typescript 人工审核恢复）届时需同步
  加入打包步骤。
