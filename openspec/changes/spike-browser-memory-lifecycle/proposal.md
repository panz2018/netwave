# Proposal

## Why

`Plan/频率类设计.md` 的「内存管理（待 spike 验证后冻结）」节给出了一套**双 realm
内存架构**（主线程 `FinalizationRegistry` 驱动 worker 释放 + worker `frequencies`
地址表 + 显式 `drop()` 逃生口），但整套结论目前只有 wasm-bindgen 0.2.128 源码与
逻辑推演支撑，**未经实测**。其中两条是行为问题、不能靠读源码拍板：

1. worker 内被 `frequencies` Map 强引用的 wasm 对象，wasm-bindgen 自带的
   `FinalizationRegistry` 是否真的**永不触发**（强引用压制 GC）；
2. 主线程自建 `FinalizationRegistry` 在壳被 GC 时，能否**可靠**经
   `postMessage` 让 worker 跑 Rust `Drop`。

铁律八的内存扩展（跨 realm 生命周期）MUST NOT 在未验证时进宪法。本 change 是一次
**一次性 spike**（throwaway，Q14 已定），用最小可运行原型实测上述机制，作为「冻结
内存设计 / 升铁律八内存扩展」的前置闸门。

## What Changes

- 新增一次性 spike 原型（**不进主代码、不进主构建、不进发布产物**）：
  - 最小 `#[wasm_bindgen]` class（镜像真实 `Frequency` 的 worker handle 表结构），
    core 侧 `AtomicUsize` 活对象计数（`new` +1 / `Drop` −1）经 wasm→worker→主线程暴露；
  - 常驻 worker 的 `frequencies` 地址表 + `drop` 命令处理；
  - 主线程 `FinalizationRegistry`（held 只存 handle 数字，不反向引用 wrapper）；
  - 显式 `drop()` 路径。
- 新增真浏览器绊线测试（vitest browser mode + Chromium，复用
  `typescript/vitest.browser.config.ts` 的测试线），经 playwright launch args 开
  `--expose-gc`，用 `globalThis.gc()` 强制 GC，轮询活对象计数：
  1. **registry 驱动 free**：丢弃主线程壳最后一个引用 → `gc()` → 计数归零；
  2. **共享不误删**：同 handle 两个 JS 引用，释放其一计数不减，释放其二并 `gc()` 归零；
  3. **显式 drop 即时**：调 `drop()` 后不 `gc()`，计数立即减。
- spike 结论（通过/失败/回退）写回 `Plan/频率类设计.md` 对应节，作为冻结或重写
  内存架构的依据。

## Capabilities

### New Capabilities

无。本 change 是 throwaway spike，不引入任何 durable 系统行为。

### Modified Capabilities

无。本 change **不改任何生产代码或 spec 级行为**——内存架构的 durable 规则按
`Plan/频率类设计.md` 明确推迟到 spike 通过后的后续 change（`governance-api-rules`
补铁律八内存扩展、`frequency-class` 落实现）。spike 只产出「机制是否可行」的实测
证据与写回 Plan 的结论，无 spec delta，故 `.openspec.yaml` 设 `skip_specs: true`。

## Non-goals

- **不实现真实 `Frequency` 类**：spike 用最小原型 class，真 `Frequency` 在
  `frequency-class` change 里另起（Q14）。
- **不进主代码 / 主构建 / 发布产物**：spike 代码隔离在一次性目录，验证完即弃，
  不接进 `pnpm check` / CI 主矩阵（LL-037 不适用——它不是长期 `test:*` 脚本）。
- **不改铁律八 / 不升宪法**：铁律八内存扩展是 spike 通过后的**独立后续**动作，
  本 change 只负责产出验证证据。
- **不验证 node / Python 端内存**：node 的 GC 策略不算数（Q9），Python/Rust 走
  引用计数/RAII 无需验证；spike 只针对浏览器双 realm 这一唯一存疑路径。
- **不做性能/吞吐测量**：只验「Drop 是否被触发、时机是否可测」，不测分配速率。

## Impact

- 受影响铁律：**铁律八**（常驻 worker 数据权威与单点所有权）——本 spike 是其内存
  扩展的前置验证，但本 change 本身不改铁律八正文。
- 受影响文档：`Plan/频率类设计.md`（写回 spike 结论）。
- 新增一次性文件：spike 原型（Rust wasm class + worker + 主线程 registry）与真浏览器
  绊线测试，置于一次性目录，验证后删除。
- 依赖：复用既有 `typescript` 测试线（vitest browser mode + playwright chromium）；
  `--expose-gc` 经 playwright launch options 注入，无新增运行时依赖。
