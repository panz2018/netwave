# Proposal

## Why

2026-09-28/29 讨论定案：浏览器端数据、状态与计算全部常驻单个 Web Worker 内的
wasm 实例（worker 常驻架构），主线程不再持有 wasm 实例与数据副本——这是无
SharedArrayBuffer 环境（GitHub Pages 无 COOP/COEP）下跨线程消息传递的渐近最优：
数据仅经显式 `upload` transfer 进入 worker 一次，之后命令移动、数据不动。
该结论目前只存在于对话，必须固化为规划文档防止漂移；同时 tsdown 的 dts 管线对
TypeScript 7（native tsgo）的兼容性未实测，需以最小验证拿结论。

## What Changes

- `Plan/typescript源码化规划.md` 并入"worker 常驻架构"章节（不新建 Plan 文件）：
  - worker 常驻架构契约：数据权威在常驻 worker 的 wasm 内；`upload` 显式
    transfer 托管、
    驻留反复可用；结果一律 transfer 传出、worker 不留副本；主线程无 wasm 实例、
    无双份数据；worker 常驻至页面关闭
  - 计算与元数据读取一律异步进 worker；元数据搭结果便车回传，主线程从返回值
    同步读描述符
  - **BREAKING（规划层面，未发布故无实际破坏）**：浏览器端 `_` 前缀同步计算
    逃生口废止；node 端保留 `_` 同步函数（napi core 在进程内，理由成立）
  - worker 异常终止数据丢失为已接受行为，API 不承诺恢复，不引入 IndexedDB
  - Worker 池：未来再讨论（前置门槛 = 数据分片归属）
  - wasm target 从"待拍板"改"已定 web"（bundler 形态待真实 npm bundler 用户
    需求出现再增量添加）
  - 真浏览器测试线（随 worker 实现落地）：vitest browser mode + playwright
    provider + 仅 Chromium，
    不引入 `@playwright/test`
  - standalone.js 形态：内部自起常驻 worker，Pages 用户零配置
- tsdown 最小兼容验证（仅拿结论，不做正式接入）：安装 tsdown，对现有壳跑一次
  构建，dts 产物与手写 `index.d.ts` 逐 export 对拍；不兼容则记录并钉
  `typescript@6` 供 dts 管线的回退方案
- lessons-learned 账本登记：LL-001 加修订标注（"小数据不起 worker"分流废止，
  浏览器端 `_` 废止、node 保留）；新增 LL 条目（主线程 wasm 实例退役、同步
  元数据读取改异步）；INDEX.md 同步

## Capabilities

### New Capabilities

（无——本次不新建 spec。）

### Modified Capabilities

（无——主 spec 修订推迟到 worker 实现落地的后续 change，本次主 spec 不动，
避免 spec 描述未实现的契约。governance 升格条目与 zero-copy-roundtrip 第
1/2/6 条改写在 Plan 文档中定案并留待实现 change 同步。）

本 change 为规划文档 + 工具验证，无 spec 级行为变更，`.openspec.yaml` 设
`skip_specs: true`。

## Non-goals

- 不改 `openspec/specs/` 主 spec（governance / zero-copy-roundtrip 修订随实现
  change 走）
- 不改 `typescript/src/` 壳代码与测试（源码化步骤 1–5 属既有规划，另行执行）
- 不做 tsdown 正式接入与 CI 步骤替换（源码化步骤 2–3）
- 不实现 worker 常驻架构本身（实现随后续规划推进；本次只固化契约与规划）
- 不定 upload/句柄 API 签名、不做 Worker 池设计、不做 IndexedDB 持久化
- 不引入 `@playwright/test`、不配多浏览器矩阵

## Impact

- `Plan/typescript源码化规划.md`：新增 worker 常驻架构章节，wasm target 节改写
  为已定案
- `openspec/specs/lessons-learned/typescript.md` + `INDEX.md`：LL-001 修订标注
  - 新增 LL 条目
- `typescript/package.json` / `pnpm-lock.yaml`：新增 devDependency `tsdown`
  （验证用；若 dts 不兼容则同时钉 `typescript@6` 回退并记录）
- 受影响的既有规划文本：《typescript源码化规划.md》"待拍板 wasm target"节、
  LL-001（账本）；主 spec 与现有代码零改动
- 铁律关联：铁律一（数据布局是契约——worker 内布局不变）、铁律七（覆盖率——
  真浏览器测试线（随 worker 实现落地）为新增门禁面）；不修改铁律本身
