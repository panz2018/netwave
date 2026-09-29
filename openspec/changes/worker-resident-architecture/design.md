# Design

## Context

见 `proposal.md` - Why。现状：`typescript/src/` 为手写无类型壳（阶段 0），
`index.browser.mjs` 在主线程 init wasm，`netwave.worker.js` 为命令分发器但仅
node 模拟测试覆盖；LL-001 记录的"小数据主线程算、大数据才 offload"分流与
本轮定案的方案一冲突。tsdown 未安装，`typescript@7.0.2` 已在 lock。

## Goals / Non-Goals

**Goals:**

- 方案一契约、web target 定案、API 面（浏览器废 `_`、node 保留）、测试线选型
  全部固化进 `Plan/typescript源码化规划.md`（单文档承载，不新建 Plan 文件）
- tsdown × TypeScript 7 dts 兼容性拿到可行动的结论（兼容 / 不兼容+回退方案）
- LL 账本反映本轮纠正，防旧模式回流

**Non-Goals:**

- 设计 upload/句柄 API 签名与 worker 池拓扑（阶段 3 实现时定，见 proposal
  Non-goals）
- 主 spec 修订与壳代码改动（随后续实现 change）

## Decisions

1. **规划承载：并入现有 Plan 文档而非新建**——worker 常驻架构与源码化步骤同属
   TypeScript 绑定演进，拆两文件会造成交叉引用网；单文档内"worker 常驻架构"为
   独立章节，wasm target 节由"待拍板"改写为"已定案 web"。备选（新建
   `Plan/worker常驻架构规划.md`）被否：用户 2026-09-29 拍板合并。
2. **主 spec 修订推迟**——governance（单点所有权/常驻 worker 权威/主线程无
   wasm）与 zero-copy-roundtrip（第 1/2/6 条）的 Requirement 文本改动写入 Plan
   定案节，实际修订随实现 change 同步进主 spec。理由：主 spec 只描述已验证
   现实，避免门禁校验未实现契约。
3. **`_` 逃生口两端不对称保留**——浏览器端直接废止（主线程无 wasm，同步计算
   无处发生）；node 端保留（napi core 在进程内，同步直通永远可行且为私有面，
   不污染公开 API）。备选（两端一起废止求对称）被用户否决：node 保留成本为零。
4. **tsdown 验证取最小面**——`pnpm add -D tsdown` + 一次构建 + dts 与手写
   `index.d.ts` 逐 export diff。不接 vitest 产物测试、不动 CI。结论三分：
   兼容（记录，正式接入留给源码化步骤 2）/ dts 不兼容（钉 `typescript@6` 供
   dts 并记入 Plan）/ 构建失败（记录 blocker，tsdown 降回 Rslib 备选重评）。
5. **账本登记方式**——LL-001 保留原文并加"2026-09-29 修订"标注（分流废止、
   浏览器 `_` 废止、node 保留），不删原文（账本只增不改史）；新增 LL 条目
   覆盖"主线程 wasm 实例退役""同步元数据改异步、元数据搭结果便车"；
   INDEX.md 一行一条同步更新。

## Risks / Trade-offs

- [Plan 文档膨胀为巨型文档] → 章节化组织；执行完成的章节按 Plan 生命周期当场
  删除（config.yaml apply guidance 已强制）
- [主 spec 与 Plan 短期不一致（spec 仍写分流/双实例）] → 不一致窗口 = 方案一
  实现 change 落地前；Plan 为未执行任务的唯一存放处，属既定生命周期内的正常
  状态；review 时以 Plan 定案节为准
- [tsdown 验证污染 lock] → 验证若失败可 `pnpm remove tsdown` 回退，lock 变化
  随 change 提交可控
- [node 保留 `_` 导致跨端 API 不对称被误用] → `_` 为 `@internal` 私有面，
  公开 API 两端签名一致（全 async），误用不破坏可移植性
