# Design

## Context

动机见 `proposal.md` 的 Why。此处只列塑造方案的现状与约束：

- **铁律八**：浏览器 wasm 只存在于一个常驻 worker，主线程 MUST NOT init wasm、
  MUST NOT 持数据副本。跨边界只能传**数字 handle**，worker 靠 `handle → 对象`
  地址表路由消息——这张表（`frequencies` Map）是寻址结构，删不得。
- **wasm-bindgen 0.2.128**（`Cargo.lock` 锁定）：对每个 `#[wasm_bindgen]` class
  自动生成 `FinalizationRegistry`（构造 `register`、GC 回调 `free`）。但 worker 把
  对象塞进 `frequencies` Map 强引用 → 永不变垃圾 → 自带 registry 永不触发。
- **绑定现状**：`typescript/wasm/src/lib.rs`、`typescript/native/src/lib.rs` 目前
  只有自由函数（`fill_pattern`/`read_element`），**无任何 class**；`FrequencyUnit`
  是 core 用 `cfg_attr(all(feature = ..., not(...)))` 门控的 enum（LL-044 模板）。
  本骨架是仓内**第一个 wasm/napi class**。
- **既有 handle 表契约**：`typescript/src/netwave.worker.ts` 已有
  `hosted: Map<Handle, Float64Array>` + `release` 命令；骨架的 `frequencies` Map
  镜像其结构但持 wasm class 实例而非 `Float64Array`。
- **测试线现状**：`vitest.browser.config.ts`（playwright chromium headless，
  `include` 含 `test/browser/**`）、`vitest.native.config.ts`（`test/native/**`）。
  `check_ci.py` 要求每个 `test:<name>` 脚本在 ci.yml 出现 `typescript test:<name>`。

## Goals / Non-Goals

**Goals:**

- 用**真实 `Frequency` 骨架**实测三条断言（见 proposal），产出「机制可行 / 需回退」
  的硬证据，并固化为**永久**绊线测试（`frequency-class` 后续只加功能方法、不改测试）。
- 可观测性必须能证明「Rust `Drop` 真的跑了」，而非仅 JS 侧对象消失或 Map 删除。
- 骨架结构镜像真实 worker handle 表，使结论可平移到 `frequency-class`。

**Non-Goals:**

- 不设计功能方法面（`f`/`f_scaled`/`w`/`wavelength`/`Display` 归 `frequency-class`）；
  骨架内部化、不导出（见「骨架内部化」决策）。
- 不追求骨架代码可复用为最终实现——`frequency-class` 会扩展它，但内存管道
  （构造/`Drop`/计数器/registry/worker 地址表）一次定型、不再改。

## Decisions

### 骨架内部化（不导出公开 `Frequency`）

骨架只含内存管道，缺 `f`/`Display` 等功能面。若现在就 `export` 公开 `Frequency`，
当场违铁律九（无 `Display`）与铁律十（skrf 兼容面残缺）。故：core struct +
`Drop` + 计数器 + wasm class + worker 地址表 + registry **全部建成且测试够得着**，
但**不从包入口（`index.browser.ts`/`index.node.ts`）导出** `Frequency`。公开
`Frequency`（含铁律九/十完整面 + `drop()` 兑现）由 `frequency-class` 完成时一次性
导出。每个「公开边界」都铁律干净，绝不出现半截公开类。

- 备选：骨架即公开 + 补最小 `Display`——否决，制造「半截公开类」的铁律九/十灰色
  地带，且 `frequency-class` 还要再动导出面。
- 备选：纯 TS 壳（不建 Rust class）——否决，违铁律十一（壳内数值逻辑）且无法见证
  Rust `Drop`（假绿闸门）。

### 可观测性：core 侧 `AtomicUsize` 活对象计数（仅测试见证）

`Drop` 归还的内存进 wasm 分配器 free list、线性内存不缩，无法从宿主侧「看」到
回收。唯一能证明 Rust `Drop` 真跑的手段：core 侧 `static LIVE: AtomicUsize`，
`from_f` 时 `fetch_add(1)`、`Drop::drop` 时 `fetch_sub(1)`，经 `live_count()` 暴露。
测试经 worker 转发轮询该值。

**计数器是测试脚手架，不是内存管理**：生产 `Frequency` = 存储（`Vec<f64>`）+
`Drop`（RAII，零内存管理代码）；计数器（`new` +1 / `Drop` −1）只为证明 `Drop` 真跑。
单看 worker `frequencies.size` 只证明 Map 删除、不证明 Rust `Drop`——若 `Drop` 没跑
而 Map 删了，size 测试仍绿（假绿闸门）。故必须配 `LIVE` 计数作硬证据。

### `live_count()` 可见性：`mem-test` feature 门控

`static LIVE` 与 `live_count()` 用 `#[cfg(any(test, feature = "mem-test"))]` 门控；
wasm/napi 的 `live_count` 导出同门控（照 `FrequencyUnit` 的 `cfg_attr` 模板，
LL-044）。CI 内存测试 job 以 `--features mem-test` 构建；release 构建不开该 feature
→ 符号缺席 `.d.mts`/`.d.ts`，公开面干净。

- 后果：唯一不变式是「测试构建必须开 `mem-test`」；若忘开，测试**立刻失败**
  （符号缺失），绝不静默变绿。

### `drop()` 公开 API（铁律十偏离立案）

`drop()` 是 JS 端（浏览器 + node）的**确定性逃生口**：GC 时机不可控（页面卸载前
可能不跑），大扫频跑完想立刻回收就手动调，不等 GC。

**铁律十偏离**（skrf `Frequency` 无 `drop()`）的「更强收获」立案：GC 时机的非确定性
是 JS 平台特有约束；skrf 无 `drop()` 等价物，因为它不跑 worker-realm wasm、由 CPython
引用计数全自动回收。在浏览器双 realm 下，主线程 GC 与 worker 内存之间没有引用计数
通道，必须有一条显式 main→worker 的释放消息；`drop()` 把这条消息暴露为确定性入口，
是「平台约束所需」而非「API 冗余」。Python/Rust **不加** `drop()`（引用计数/RAII
全自动，加 = footgun 且违铁律十）。命名 `drop()`（用户拍板——「销毁即止」），不用
`release`/`free`/`delete`（`release` 已被 handle 表占用，语义不同）。

### 主线程 registry 的 held 值：只存 handle 数字

`new FinalizationRegistry(cb)`，回调 `cb` 内
`worker.postMessage({cmd:"dropFrequency", handle})`，注册用
`register(wrapper, handle, wrapper)`。held 必须是**不反向引用 wrapper**
的值（数字 handle），否则 registry 反而把 wrapper 钉活、永不回收。worker 收到
`{cmd:"dropFrequency", handle}` 后 `frequencies.get(handle).free()` +
`frequencies.delete(handle)` → Rust `Drop`。

- 备选：held 存 wrapper 自身——否决，强引用导致永不触发（正是 wasm-bindgen 在
  worker 侧被 Map 压制的同一陷阱，不能在主线程重犯）。

### node 端：napi finalizer 自动 Drop，不进 `hosted` Map

node 单 realm，napi cleanup finalizer 在 JS 对象被 GC 时自动跑 Rust `Drop`
（`typescript/native/src/lib.rs` 注释「freed at GC finalize」已证）。用户**直接持**
napi class 实例，无 Map 强引用 → 无压制 → 自带 finalizer 正常工作。故 node `Frequency`
**不进** `hosted` Map（与浏览器 worker 的压制场景相反，不能照搬）。`drop()` 在 node
可选（finalizer 已自动；`drop()` 仅供确定性提前释放）。

### 强制 GC：双端 `--expose-gc`

`FinalizationRegistry`/finalizer 回调时机由 GC 决定，不强制则测试 flaky。

- 浏览器：经 `@vitest/browser-playwright` 的 `launch` options 注入 `--expose-gc`。
- node：经 vitest `poolOptions.threads.execArgv`（或 `vmThreads`）注入 `--expose-gc`。

测试内调 `globalThis.gc()` 强制 major GC，再轮询 `live_count()` 归零（带超时兜底）。

- 备选：`setTimeout` 等自然 GC——否决，不可靠、必 flaky。

### 共享所有权验证形态

断言 2 用**同一 handle 的两个主线程 wrapper 引用**模拟「circuit 与 network 同持
`f`」：`let a = shell; let b = shell;`，释放 `a` 后 `gc()` 计数不减，再释放 `b` 并
`gc()` 计数归零。证明 GC 仅在**全部**引用消失时触发——共享场景天然安全，比「替换即删」
式手动管理强。

## Risks / Trade-offs

- [Chromium headless CI 下 `--expose-gc` 不生效或 GC 不回收] → 测试先断言
  `typeof globalThis.gc === "function"`，缺失即 fail-fast 报「环境未开 expose-gc」，
  与「机制失败」区分；轮询带超时，超时单独报「GC 时机不可测」触发 proposal 的回退
  路径（显式 `drop()` 为主、registry 仅兜底）。
- [FinalizationRegistry 回调在 `gc()` 后仍需一个微任务/宏任务才投递] → 轮询循环
  用 `await` 让出事件循环（`await new Promise(r => setTimeout(r, 0))` 若干轮），
  而非同步忙等。
- [骨架与真实 worker 结构漂移，结论不可迁移] → worker 命令面（`newFrequency`/
  `dropFrequency`/`liveCount`）与 handle 表语义严格镜像
  `typescript/src/netwave.worker.ts` 现有 `upload`/`release` 契约。
- [`mem-test` feature 在测试构建被漏开 → 假绿] → `live_count` 符号缺失即测试
  编译/调用失败（fail-fast），不会静默通过；CI 内存 job 显式 `--features mem-test`。
- [骨架被误当公开 API 使用] → 不从包入口导出 + `mem-test` 门控 `live_count`；
  `check_vocab_types.py` 不纳入骨架（无功能面可校验），`frequency-class` 导出时再接入。

## Migration Plan

无生产部署（骨架不导出）。生命周期：写失败测试（red）→ 建 core 骨架 + wasm/napi
class + worker 地址表 + 主线程 registry（green）→ 双端 `--expose-gc` 跑三条断言 →
`test:memory` 接进 CI（LL-037）→ 实测结论写回 `Plan/频率类设计.md`。回滚 = 删骨架
与测试（无公开 API 可回滚）。

## Open Questions

- `frequency-class` 导出公开 `Frequency` 时，`drop()` 是否同时进 `.pyi`（Python）
  ——按本设计 Python 不加 `drop()`，仅 JS 端；属 `frequency-class` 实现期确认，
  不影响本 change 的内存管道定型。
