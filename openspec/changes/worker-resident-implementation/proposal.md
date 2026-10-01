# Proposal

## Why

worker 常驻架构已定案（见 `Plan/typescript源码化规划.md` 与账本 LL-001/LL-030/
LL-031），但主 spec 与代码仍是旧契约：`zero-copy-roundtrip spec` 保留"小数据主线程
分流 + Worker 池"条款与浏览器 `_` 逃生口，浏览器壳在主线程 init wasm，主线程可持
数据副本，存在权威歧义。定案不落进代码与 spec，账本防复发检测（LL-030 要求真浏览器
测试断言主线程不 init wasm）就一直空转。

## What Changes

- 浏览器壳重写：主线程不再 init wasm，数据/状态/计算全常驻单个 worker 内 wasm；
  单点所有权，数据移动仅经显式 transfer，计算结果 buffer transfer 传出，元数据
  搭结果便车回传；worker 常驻至页面关闭。
- **BREAKING** 浏览器端 `_` 前缀同步计算函数直接删除（不加 deprecated）；node 端
  保留（napi core 在进程内，同步直通永远可行）。
- `standalone.js` 改为内部自起常驻 worker，Pages / `<script type="module">`
  零配置体验不变。
- governance spec 升格契约："单点所有权 + 移动仅经显式 transfer + 常驻 worker 为
  数据权威 + 主线程无 wasm"。
- zero-copy-roundtrip spec 按定案改写：分流废止、浏览器 `_` 废止、元数据搭结果便车。
- 真浏览器测试线落地：vitest browser mode + playwright provider + 仅 Chromium，
  同一套测试代码与 `pnpm test` 入口；不引入 `@playwright/test`。
- TS7 dts 兼容性重测：tsdown dts × TypeScript 7（tsgo）兼容则升回 7；不兼容则
  钉 `typescript@6`，"待 tsgo 支持 dts 后重测"移入 `Plan/总体计划.md` 待办。
- 语言约束提级：AGENTS.md 顶部通用原则新增两条——①对话必须用用户提问所用
  的语言回答（镜像用户语言，不得凭模型偏好选语言）；②文档按目录分语言：
  仅 `openspec/` 与 `Plan/` 用中文，其余一切（docs、代码注释、README 等）
  用英文；账本新增对应 LL 条目。

## Capabilities

### New Capabilities

（无——本变更全部落在既有 capability 上。）

### Modified Capabilities

- `project-governance`: 新增契约级 Requirement"常驻 worker 数据权威与单点所有权"
  （单点所有权、移动仅经显式 transfer、常驻 worker 为数据权威、主线程无 wasm）。
- `zero-copy-roundtrip`: 改写"异步与 Worker 边界契约"——删除按规模分流与 Worker 池
  条款、删除浏览器端 `_` 逃生口、元数据读取改异步并搭结果便车回传；新增/改写
  对应 Scenario（含"主线程不 init wasm"浏览器断言）。

## Impact

- 代码：`typescript/src/index.browser.ts`、`src/worker.ts`、`src/standalone.ts`、
  `src/types.ts`（公开契约单一来源）；node 壳不动。
- 测试：`typescript/test/` 新增浏览器套件（vitest browser mode + playwright +
  Chromium）；`vitest.config` 增浏览器配置并入 `pnpm test`；覆盖率 100% 闸门
  （铁律七）覆盖新浏览器路径。
- 依赖：devDependencies 新增 vitest browser provider（playwright）；typescript
  版本视 TS7 dts 重测结果决定钉 6 或升 7。
- 文档：governance / zero-copy-roundtrip 主 spec、AGENTS.md、lessons-learned
  账本（LL-001 修订标注 + 新增语言 LL）、`Plan/typescript源码化规划.md`（实施后
  整删）、`Plan/总体计划.md`（接收未来项：多 worker 分桶、npm bundler 支持、
  TS7 dts 重测[仅不兼容时]）。
- 受影响铁律：铁律一（数据布局不动，worker 内存内 reinterpret 不变）、铁律二
  （TDD：浏览器 worker 行为先写失败测试）、铁律三（容差仍走 manifest）、
  铁律七（新浏览器产码覆盖率 100%）。

## Non-goals

- 不做多 worker 分桶/池（api-contract spec 强制阶段 3–6 单常驻 worker；分桶移入
  总体计划待决清单，门槛 = 数据分片归属 + 实测需求）。
- 不做 npm bundler（Vite/webpack）支持（按需触发，移入总体计划待办）。
- 不引入 `@playwright/test`；不做多浏览器矩阵（待浏览器特异 bug 出现再加）。
- 不做 wthreads 多线程 wasm / SharedArrayBuffer 原地写（阶段 3 可选增强）。
- 不改 node 端 API 面（`_` 保留）、不改 Python 端、不改 core Rust 数值逻辑。
- 不做 IndexedDB 等 worker 崩溃数据恢复（worker 异常终止数据丢失为已接受行为）。
