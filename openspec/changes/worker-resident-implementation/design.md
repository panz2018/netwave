# Design

## Context

worker 常驻架构定案见 `Plan/typescript源码化规划.md`（本 change 实施后整删）与
账本 LL-001/LL-030/LL-031；契约现状见 `zero-copy-roundtrip spec`（仍含分流与
浏览器 `_`）与 `api-contract spec`（已钉单常驻 worker 与泛化分发）。现有代码：
`typescript/src/index.browser.ts` 在主线程 init wasm 并导出 `_` 同步逃生口；
`src/worker.ts` 是命令分发器但 cmd 表直接 import 主线程壳（架构错位——worker
常驻后 wasm 只能在 worker 内 init，分发器必须改为直接持有 wasm glue）；
`src/standalone.ts` 走主线程壳。测试仅 node 模拟 worker。

## Goals / Non-Goals

**Goals:**

- 浏览器壳、worker、standalone 三线重写为常驻 worker 架构；主线程零 wasm。
- upload/release 句柄 API 签名定案（本 design 拍板，随实现落地）。
- governance / zero-copy-roundtrip 主 spec 按 delta 改写并 `openspec validate` 绿。
- 真浏览器测试线（vitest browser mode + playwright + Chromium）进 `pnpm test`。
- TS7 dts 重测拿到可行动结论；语言约束提级进 AGENTS.md 与账本。

**Non-goals:**

- 见 proposal Non-goals（多 worker 分桶、npm bundler、wthreads、node/Python 面
  改动、崩溃恢复）。

## Decisions

### 常驻 worker 所有权模型与句柄 API

- 浏览器壳内部经 `getWorker()` 懒起**唯一**常驻 worker（`type: "module"`，
  URL 相对壳模块解析），首次 `await` 计算/上传时起，常驻至页面关闭
  （不显式 terminate）。单例注册表挂在 `globalThis`：已存在则直接返回，
  不存在才 `new Worker(...)`——无论 import 多少次、页面加载几份库副本，
  运行时保证只有一个 worker（铁律八），不是警告而是结构上不可能起第二个。

  ```js
  const getWorker = () =>
    (globalThis.__netwaveWorker ??= new Worker(
      new URL("./netwave.worker.js", import.meta.url),
      { type: "module" },
    ));
  ```

- wasm 只在 worker 内 init；`index.browser.ts` 删除全部 wasm import 与 `_` 同步
  导出，只剩"起 worker + 发消息 + 收结果"的纯传输壳。
- **worker 单例语义**：单例由 `getWorker()` 强制，不靠模块单例巧合也不靠
  警告：注册表在 `globalThis`，跨模块副本也共享——多次 import、多句柄、
  standalone + npm 包混用、微前端重复打包，均复用同一 worker（铁律八）。
  已知代价：两份副本版本不同时，后加载的副本实际跑在先加载副本的 worker 上
  （版本错位），README 声明"同页面只应加载一份库"；用户经 `netwave/worker`
  子路径显式自建 worker 属高级用法，不在单例管辖内（那是用户自己的容器，
  壳不注册）。
- **句柄 API 签名**（钉进 `types.ts`，公开契约单一来源）：
  - `upload(view: Float64Array): Promise<Handle>`——view 的 buffer 进 transfer
    list，调用后原视图 detached；`Handle = number`，worker 内单调递增分配。
  - `release(handle: Handle): Promise<void>`——worker 内 drop 该 Network，句柄
    作废；再经该句柄调用 MUST reject（错误信息含句柄号）。
  - 计算动词：`await toY(handle): Promise<NetwaveBuffer>`——输入是句柄（数据
    已在 worker，无输入移动）；返回值 `NetwaveBuffer` 字段见下方定义——
    元数据搭结果便车，shape/frequency 随结果同消息回传，主线程从返回值重建视图。

    ```ts
    interface NetwaveBuffer {
      buffer: ArrayBuffer;
      byteOffset: number;
      length: number;
      shape: [number, number, number];
      frequency: Float64Array;
    }
    ```

  - 未托管输入的便捷路径：`await toY(float64View)` 重载——buffer 边界拷贝进
    worker（不进 transfer list，输入不消耗），签名与句柄路径同一动词。
- **消息协议**沿用 api-contract spec 泛化分发 `{id, cmd, args}`；worker 回传
  `{id, result, transfer}` 或 `{id, error}`。`_` 前缀方法在 worker 端 cmd 表
  天然不存在（浏览器壳不再导出 `_`，worker glue 的 `_` 不进 cmd 表），满足
  "`_` 不进 worker 命令面"。
- **结果 buffer 来源**：worker 内计算结果从 wasm 线性内存拷入新 ArrayBuffer 后
  transfer 回主线程（线性内存不可 transfer，会 detach wasm 实例——现有
  `worker.ts` 已确立此姿势，保留）。
- 备选（每计算起临时 worker）被否：违背常驻定案且每次重付 wasm init 成本。

### worker 端 glue 错位修正

- `worker.ts` 不再 import `index.browser.ts`（旧结构让 worker 依赖主线程壳的
  wasm 实例，架构上不可能常驻）。新结构：`worker.ts` 直接 import wasm glue
  （`../dist/wasm-web/netwave_wasm.js`）并 init，维护 `handle -> Network` 表；
  `index.browser.ts` 与 `worker.ts` 共享的只有 `types.ts`（协议类型）。
- cmd 表显式静态：`upload / release / fillPattern / readElement / toY(未来动词)`，
  加动词只改表。

### standalone.js 自起常驻 worker

- `standalone.ts` 不再触碰 wasm：其公开面与 `index.browser.ts` 同一套 async
  动词，内部复用同一 worker 起法；备选内联起法（Blob/data URL）仅在跨域场景
  需要时启用；具体方式实现时按 tsdown 产物形态定，优先相对 URL 构造
  （Pages 场景已同源，见上方代码块）。
- 零配置体验不变：用户 `<script type="module">` import standalone.js 后直接
  `await` 动词即可。

### 真浏览器测试线

- vitest browser mode + `@vitest/browser` playwright provider，仅 Chromium；
  新增 `vitest.browser.config.ts`，并入 `pnpm test` 聚合入口；不引入
  `@playwright/test`。
- 测试代码与 node 套件同一套契约断言（upload/release/往返/元数据便车），
  浏览器特异断言新增：主线程 `globalThis` 无 wasm 实例（LL-030 复发检测）、
  worker 消息计数（元数据便车无额外往返）、`_` 导出不存在。
- playwright 浏览器二进制首次联网下载，执行前预告耗时；provider 配置
  `headless: true` 进 CI。
- 覆盖率：浏览器套件用 vitest browser 覆盖率（v8），并入铁律七 100% 闸门；
  结构性不可达路径逐条 `/* v8 ignore */` + 理由。

### TS7 dts 重测分支

- `pnpm add -D typescript@7` → `pnpm build:shells` + `pnpm typecheck` +
  发布壳 dts hub 复验（`.d.mts` 与 `exports.types` 对齐）。
- 兼容：保留 7，不留尾巴。不兼容：`pnpm add -D typescript@6` 回退钉版，
  "待 tsgo 支持 dts 后重测"写入 `Plan/总体计划.md`「待办/待核实」，结论记
  账本（ci 分片）。

### 语言约束提级

- AGENTS.md「通用原则」顶部新增两条：①**对话镜像用户语言**——用户用什么语言
  提问就必须用什么语言回答，不得凭模型偏好选语言（最基本的尊重）；②**文档
  按目录分语言**——仅 `openspec/` 与 `Plan/` 用中文，其余一切（docs、代码
  注释、rustdoc/docstring/JSDoc、README 等）用英文。
- 账本 docs 分片新增 LL（对话未镜像用户语言 / 文档语言错配被人工纠正），
  INDEX 同步。不做脚本门禁（误报率高）。

## Risks / Trade-offs

- [浏览器测试线首次进 CI 不稳定（playwright 下载/沙箱）] → 仅 Chromium +
  headless；失败先查 provider 配置再查代码，不稳定则本 change 内修，不留
  flaky 豁免。
- [句柄 API 是新增公开面，未来动词扩展可能撞签名] → 重载只加"未托管输入
  便捷路径"，句柄路径不动；types.ts 单一来源 + exports 测试兜底。
- [standalone 内联 worker 与发布产物路径耦合] → publish_shell.mjs 已有路径
  重写机制，扩展它而非新造第二步。
- [TS7 不兼容拖住变更] → 分支处理已定：钉 6 不阻塞归档。
