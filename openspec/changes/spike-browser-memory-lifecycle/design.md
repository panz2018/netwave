# Design

## Context

动机见 `proposal.md` 的 Why。此处只列塑造方案的现状与约束：

- **铁律八**：浏览器 wasm 只存在于一个常驻 worker，主线程 MUST NOT init wasm、
  MUST NOT 持数据副本。跨边界只能传**数字 handle**，worker 靠 `handle → 对象`
  地址表路由消息——这张表（`frequencies` Map）是寻址结构，删不得。
- **wasm-bindgen 0.2.128**（`Cargo.lock` 锁定）：对每个 `#[wasm_bindgen]` class
  自动生成 `FinalizationRegistry`（构造 `register`、GC 回调 `free`）。但 worker 把
  对象塞进 `frequencies` Map 强引用 → 永不变垃圾 → 自带 registry 永不触发。
- **测试线现状**：`typescript/vitest.browser.config.ts` 已用 vitest browser mode +
  `@vitest/browser-playwright`，Chromium headless，`include` 含
  `test/browser/**/*.test.ts`。worker 模块在 worker context 内运行。
- **既有 handle 表契约**：`typescript/src/netwave.worker.ts` 已有
  `hosted: Map<Handle, Float64Array>` + `release` 命令；spike 镜像其结构但持
  wasm class 实例而非 `Float64Array`。

## Goals / Non-Goals

**Goals:**

- 用最小可运行原型**实测**三条断言（见 proposal），产出「机制可行 / 不可行 / 需回退」
  的硬证据。
- 可观测性必须能证明「Rust `Drop` 真的跑了」，而非仅 JS 侧对象消失。
- spike 结构镜像真实 worker handle 表，使结论可平移到 `frequency-class`。

**Non-Goals:**

- 设计级补充：不追求 spike 代码可复用、不写泛型/抽象、不补测试覆盖率门槛
  （浏览器 100% 覆盖门槛只作用于 `src/index.browser.ts`，spike 不在其内）。
- 其余 Non-goals 见 proposal，不重述。

## Decisions

### D1 — 可观测性：core 侧 `AtomicUsize` 活对象计数

`Drop` 归还的内存进 wasm 分配器 free list、线性内存不缩，无法从宿主侧「看」到
回收。唯一能证明 Rust `Drop` 真跑的手段：core 侧全局 `static LIVE: AtomicUsize`，
`new` 时 `fetch_add(1)`、`Drop::drop` 时 `fetch_sub(1)`，经一个
`#[wasm_bindgen] live_count() -> usize` 暴露。测试经 worker 转发轮询该值。

- 备选：测 `memory.buffer.byteLength`——否决，线性内存只增不减，测不出。
- 备选：worker `frequencies.size` 单独作证据——保留为**双证**（JS 侧地址表长度），
  但它只证明 Map 删除，不证明 Rust `Drop`，故必须配 `LIVE` 计数。

### D2 — 强制 GC：playwright launch args `--expose-gc`

`FinalizationRegistry` 回调时机由 GC 决定，不强制则测试 flaky。经
`@vitest/browser-playwright` 的 `launch` options 注入 `--expose-gc`，测试内调
`globalThis.gc()` 强制 major GC，再轮询 `live_count()` 归零（带超时兜底）。

- 备选：`setTimeout` 等自然 GC——否决，不可靠、必 flaky。
- 备选：node 模拟 worker——否决（Q9：node GC 策略不算数，且非真双 realm）。

### D3 — 主线程 registry 的 held 值：只存 handle 数字

`new FinalizationRegistry((handle) => worker.postMessage({cmd:"drop", handle}))`，
`register(wrapper, handle, wrapper)`。held 必须是**不反向引用 wrapper** 的值
（数字 handle），否则 registry 反而把 wrapper 钉活、永不回收。worker 收到
`{cmd:"drop", handle}` 后 `frequencies.get(handle).free()` + `frequencies.delete(handle)`。

- 备选：held 存 wrapper 自身——否决，强引用导致永不触发（正是 wasm-bindgen 在
  worker 侧被 Map 压制的同一陷阱，不能在主线程重犯）。

### D4 — throwaway 隔离位置

spike 代码置于 `typescript/spike-memory/`（一次性目录），独立最小
`#[wasm_bindgen]` crate 或复用 wasm crate 的独立 feature 门，配独立 vitest 配置
（仅 `include` spike 测试 + `--expose-gc`）。**不进** `pnpm check` / CI 主矩阵 /
`files` 发布清单。验证完按 Plan 生命周期删除该目录。

- 备选：塞进 `test/browser/`——否决，会被主浏览器测试线的 100% 覆盖门槛与 CI 扫到，
  污染生产闸门。

### D5 — 共享所有权验证形态

断言 2 用**同一 handle 的两个主线程 wrapper 引用**模拟「circuit 与 network 同持
`f`」：`let a = shell; let b = shell;`（或两 wrapper 持同 handle），释放 `a` 后
`gc()` 计数不减，再释放 `b` 并 `gc()` 计数归零。证明 GC 仅在**全部**引用消失时触发。

## Risks / Trade-offs

- [Chromium 在 headless CI 下 `--expose-gc` 不生效或 GC 不回收] → 测试先断言
  `typeof globalThis.gc === "function"`，缺失即 fail-fast 报「环境未开 expose-gc」，
  与「机制失败」区分开；轮询带超时，超时单独报「GC 时机不可测」触发 proposal 的回退
  路径（显式 `drop()` 为主、registry 仅兜底）。
- [FinalizationRegistry 回调在 `gc()` 后仍需一个微任务/宏任务才投递] → 轮询循环
  用 `await` 让出事件循环（`await new Promise(r => setTimeout(r, 0))` 若干轮），
  而非同步忙等。
- [spike 与真实 worker 结构漂移，结论不可迁移] → spike 的 worker 命令面
  （`new`/`drop`/`liveCount`）与 handle 表语义严格镜像
  `typescript/src/netwave.worker.ts` 现有 `upload`/`release` 契约。
- [throwaway 代码被误并入主构建] → 独立目录 + 不进 `files`/CI + 验证完即删；
  tasks 末条强制删除并跑 `pnpm check:md`。

## Migration Plan

无生产部署。spike 生命周期：搭原型 → 跑三条断言 → 结论写回
`Plan/频率类设计.md` → 删除 `typescript/spike-memory/` → `pnpm check:md`。
回滚 = 直接删目录（无主代码改动可回滚）。

## Open Questions

- 真实 `Frequency` 是否需要把 `live_count()` 作为长期诊断 API 暴露，还是仅 spike
  临时用——属 `frequency-class` 实现期决定，不影响本 spike 与任务拆分，延后。
