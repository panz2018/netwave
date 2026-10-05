# Proposal

## Why

`Plan/频率类设计.md` 的「内存管理」节给出一套**双 realm 内存架构**（主线程
`FinalizationRegistry` 驱动 worker 释放 + worker `frequencies` 地址表 + 显式
`drop()` 逃生口），目前只有 wasm-bindgen 0.2.128 源码与逻辑推演支撑，**未经实测**。
其中两条是行为问题、不能靠读源码拍板：

1. worker 内被 `frequencies` Map 强引用的 wasm 对象，wasm-bindgen 自带的
   `FinalizationRegistry` 是否真的**永不触发**（强引用压制 GC）；
2. 主线程自建 `FinalizationRegistry` 在壳被 GC 时，能否**可靠**经 `postMessage`
   让 worker 跑 Rust `Drop`。

铁律八的内存扩展（跨 realm 生命周期）MUST NOT 在未验证时进宪法。本 change 用
**真实 `Frequency` 骨架**（而非一次性原型）把这套机制**实测并固化为永久绊线测试**：
骨架只含内存管道（构造分配 + `Drop` + 测试见证计数器），不含任何功能方法
（`f`/`f_scaled`/`w`/`wavelength`/`Display` 归 `frequency-class`）。这样内存测试
从一开始就测**真实 `Drop` 路径**，`frequency-class` 后续只往骨架上加功能方法、
**内存测试永不重写**——避免「先测假类、实现时再合并」的二次维护与假绿风险。

## What Changes

- **core `Frequency` 骨架**（`core/src/frequency.rs`）：struct 持 `Vec<f64>`（Hz
  存储）+ `FrequencyUnit`；`from_f` 分配、`impl Drop`（RAII，生产零内存管理代码）；
  `#[cfg(any(test, feature = "mem-test"))]` 门控的 `static LIVE: AtomicUsize`
  （`new` +1 / `Drop` −1）+ `live_count()`——**仅测试见证**，非内存管理。
- **wasm 绑定**（`typescript/wasm/src/lib.rs`）：`#[wasm_bindgen]` class（骨架
  内部化，**不从包入口导出**）+ `live_count()`，均 `mem-test` feature 门控
  （LL-044：release 构建符号缺席，公开面干净）。
- **napi 绑定**（`typescript/native/src/lib.rs`）：`#[napi]` class + `live_count()`，
  同 `mem-test` 门控；node 端 napi cleanup finalizer 自动 `Drop`（壳 GC 即释放，
  不进 `hosted` Map）。
- **常驻 worker**（`typescript/src/netwave.worker.ts`）：`frequencies` 地址表
  （`Map<Handle, Frequency>`）+ `newFrequency`/`dropFrequency`/`liveCount` 命令，镜像既有
  `upload`/`release` 契约。
- **主线程 registry**（`typescript/src/index.browser.ts`）：`FinalizationRegistry`
  （held 只存 handle 数字，不反向引用 wrapper），回调发
  `{cmd:"dropFrequency", handle}` 消息；显式 `drop()` 公开 API（确定性逃生口）。
- **永久绊线测试**（真浏览器 + node，`--expose-gc`）：三条断言（registry 驱动
  free / 共享不误删 / 显式 drop 即时），轮询 `live_count()` 归零，fail-fast 区分
  「环境未开 expose-gc」与「机制失败」。新增 `test:memory` 脚本当轮接进 CI（LL-037）。

## Capabilities

### New Capabilities

- `memory-lifecycle`：跨 realm（浏览器双 realm + node 单 realm）`Frequency` 内存
  生命周期契约——Rust `Drop` 经见证计数器可证、主线程 registry 驱动 worker 释放、
  共享所有权不误删、显式 `drop()` 确定性即时。durable 行为，非 spike。

### Modified Capabilities

无 spec 级行为改动。`frequency-unit`（词汇/倍率）不受影响；本 change 只新增
`Frequency` 骨架的内存契约。铁律八内存扩展（跨 realm 生命周期）作为**宪法级**
规则不在本 change——待本 change 实测全绿后随 `governance-api-rules` 或独立最高级
变更补入（未验证的内存规则不进宪法）。

## Non-goals

- **不实现功能方法**：`f`/`f_scaled`/`w`/`wavelength`/`Display`/`from_wavelength`/
  `set_unit` 等全归 `frequency-class`。本骨架是「能分配、能 Drop、能被见证」的最小
  class，**不从包入口导出**（半截公开类违铁律九/十，故内部化，仅测试 harness
  够得着）。
- **不升铁律八 / 不改宪法**：铁律八内存扩展是本 change 实测全绿后的**独立后续**
  （`governance-api-rules`），本 change 只产出实测证据与永久测试。
- **不验证 Python/Rust 端内存**：Python 走 pyo3 引用计数、Rust 走 RAII，全自动
  无需验证；`drop()` 也不加到这两端（footgun 且违铁律十）。
- **不做性能/吞吐测量**：只验「`Drop` 是否被触发、时机是否可测」，不测分配速率。
- **不暴露 `live_count()` 于发布产物**：`mem-test` feature 门控，release 构建符号
  缺席（`.d.mts`/`.d.ts` 无此成员）。

## Impact

- 受影响铁律：**铁律八**（常驻 worker 数据权威）——本 change 是其内存扩展的实测
  验证与永久测试落地；**铁律十**（skrf 兼容）——`drop()` 公开是偏离，deviation
  立案见 design（JS GC 时机非确定性的平台特有逃生口，skrf 无对应物因其不跑
  worker-realm wasm）；**铁律十一**（薄壳）——registry/worker 仅做 handle 路由，
  零数值逻辑。铁律九/十/十一正文由 `governance-api-rules` 定义，本 change 引用其
  编号（依赖：`governance-api-rules` 先行批准）。
- 受影响文档：`Plan/频率类设计.md`（「内存测试」节改写为永久内存测试 + 实测结论
  写回）。
- 新增文件：core 骨架 + wasm/napi class 绑定 + worker 地址表 + 主线程 registry +
  `test/browser/`、`test/native/` 永久测试 + `specs/memory-lifecycle/spec.md` delta。
- 依赖：复用既有测试线（vitest browser + playwright chromium、vitest native）；
  `--expose-gc` 经 playwright launch options（浏览器）与 `poolOptions.execArgv`
  （node）注入，无新增运行时依赖。
