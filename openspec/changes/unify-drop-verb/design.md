# Design

## Context

动机见 [proposal.md](proposal.md#why)。当前同一语义（手动立即释放）的四个名字与
其所在层：

| 层                  | 现名                        | 用户可见                                     |
| ------------------- | --------------------------- | -------------------------------------------- |
| core Rust           | `Frequency::release()`      | ❌                                           |
| node napi           | `Frequency.free()`          | ✅                                           |
| 浏览器 TS 壳        | `internals.drop(ref)`       | ✅（测试缝）                                 |
| worker 命令         | `dropFrequency` / `release` | ❌（本 change 收拢为单一 `drop`，转发 core） |
| JS 句柄函数         | `release(handle)`           | ✅                                           |
| wasm-bindgen 生成物 | `free()`                    | ❌（只活在 worker 内）                       |

约束：wasm-bindgen 为每个 `#[wasm_bindgen]` class 自动生成的释放方法名固定为
`free()`（工具链焊死，见 memory-lifecycle spec「Rust `Drop` 经见证计数器可证」
引用的 wasm-bindgen 0.2.128 源码事实）；该生成物只存在于 worker realm 内部，
用户不可见。

## Goals / Non-Goals

**Goals:**

- 用户可见面「手动释放」只有一个名字：`drop`。
- 清理逻辑在 Rust 只有一份实现，手动路径与 RAII 路径共用。
- 名字漂移可门禁化：三端公开动词集合相等断言进 CI。

**Non-Goals:**

- 不改内存生命周期行为（registry 驱动、共享不误删、见证计数器语义不变）。
- 不加 Python `with` 支持、不加任何兼容别名（见 proposal Non-goals）。

## Decisions

### Rust core：固有方法 `drop()` + `Drop::drop` 委托

```rust
impl Frequency {
    pub fn drop(&mut self) { /* 现 release() 的函数体，原样搬 */ }
}
impl Drop for Frequency {
    fn drop(&mut self) {
        self.drop(); // 固有方法优先于 trait 方法解析，不递归
    }
}
```

Rust 方法解析规则中固有方法（inherent method）优先于 trait 方法（[Rust
Reference — method call expressions](https://doc.rust-lang.org/reference/expressions/method-call-expr.html)），
故 `self.drop()` 命中上面的 `pub fn drop`，无递归。备选（保留 `release()` 内部名
＋绑定层 `js_name`/`pyo3` 改名）被否：那正是新铁律十二禁止的"名字映射壳"。

字段 `dropped: bool` 与 `live_count()` 见证语义不变。

### node napi：方法直接命名 `drop`

`typescript/native/src/lib.rs` 的 wrapper `struct Frequency(CoreFrequency)` 自身
**没有** `impl Drop`（回收由 napi cleanup finalizer 调 core 的 `Drop`），故 Rust
侧无 `Drop::drop` 遮蔽问题，方法可直接叫 `drop`：

```rust
#[napi]
pub fn drop(&mut self) {
    self.0.drop();
}
```

### Python：`Frequency` pyclass 首次导出，含 `drop()`

`python/src/lib.rs` 现只注册 `FrequencyUnit`/`frequency_units`。本 change 注册
`Frequency` pyclass，`#[pymethods]` 内直接命名 `drop`（pyo3 无名字映射需求，
零壳）。释放后 `f`/`f_scaled`/`npoints` 抛 `PyValueError`。

### JS 句柄动词：`release(handle)` → `drop(handle)`

`typescript/src/{index.browser,index.node,types}.ts` 的 `release` 导出改名 `drop`；
worker 命令表 `release` → `drop`；错误文案 `unknown or released handle` →
`unknown or dropped handle`。`upload` 保持原名（破坏性语义由 `upload` 自身表达，
见 api-contract spec「显式托管入口与显式内存回收」）。

`internals.drop`（浏览器测试缝）已含 `drop`，不改名。

### worker 资源表：下沉 core（cfg=browser）+ worker JS 零状态

常驻 worker 原有两张 JS 句柄表——`hosted`（`upload` 移入的裸字节缓冲）与
`frequencies`（worker 内 wasm `Frequency` 实例），释放动词分裂为 `release`(buffer)
与 `dropFrequency`(Frequency)。本 change 把句柄表**整体下沉到 core Rust**：

```rust
// core，cfg 门控 browser feature
pub enum Resource { Buffer(Vec<f64>), Frequency(Frequency) /* 未来 Network 等 */ }
static RESOURCES: Mutex<BTreeMap<u32, Resource>>; // 句柄计数器同表递增
```

- **单一一张表**：`handle → Resource` enum，句柄由 core 单一计数器递增、全局
  唯一，单表查找无歧义；未来 Network/Circuit 只加 enum 变体，表数量恒为 1。
- **单一 `drop(handle)`**：core 侧 `remove(handle)` 直接触发 Rust `Drop`（RAII），
  不经 JS 对象中转——wasm `Frequency` 实例不再浮出 JS，连生成物 `free()` 的
  JS 调用点都不存在（工具链生成物豁免因此自动满足）。
- **worker JS 零状态**：`hosted`/`frequencies`/`nextHandle` 全删；`upload`/
  `newFrequency`/`drop` 等命令退化为把参数/句柄原样转发给 core 的
  `#[wasm_bindgen]` 入口，零分派零状态（铁律八：worker 内 wasm 是唯一数据权威，
  表也应在 wasm 内而非 JS）。
- **cfg 只门控浏览器**：表代码写在 core crate、只编进 wasm；node/python 编译时
  不启用该 cfg，直接持对象、无句柄表，不会被拖去实现注册表。三端统一的是
  `drop` 这个名字与行为契约，不是那张表；公开形态统一实例方法 `obj.drop()`，
  `drop(handle)` 仅是浏览器 `postMessage` 协议的内部命令形态，不上浮公开 API。

### 门禁：三端动词集合相等

`scripts/cross_compare.py` 扩展：提取 core `pub fn` / pyo3 `#[pymethods]` /
napi `#[napi]` / 浏览器 TS 壳导出的公开动词集合，做 camelCase 机械映射归一后
断言相等；`free`/`release` 出现在任一用户可见面即红。

## Risks / Trade-offs

- **[改名波及冻结测试]** 内存生命周期测试是已冻结的永久回归 → 只改调用名
  （`f.free()`→`f.drop()`、`release(h)`→`drop(h)`），断言逻辑与场景结构零改动；
  跑全套确认绿即证明行为未变。
- **[生成物残留旧名]** `.pyi`/`.d.mts` 缓存旧签名 → 重新生成并 grep 旧名零命中
  作为验收项（LL-008 同类坑）。
- **[worker 命令名与壳不同步]** 壳发 `drop` 而 worker 表仍是 `release` → 运行期
  "unknown command"；同一 PR 内两处同改 + 往返测试覆盖。
- **[句柄表下沉 core 的波及]** `upload`/`readElement` 从 JS Map 读写改为 core
  句柄入口（字节移进 core `Vec<f64>`），是行为等价的搬运 → 往返测试逐 bit 对拍
  托管/未托管两路径不变即证明；wasm 体积增量（一张表 + Mutex）可忽略。
- **[Python 手动 drop 冗余]** Python 有引用计数，`drop()` 看似多余 → 幂等 +
  释放后报错封死误用；换取四端动词单一，收益已在 spec 立案。

## Migration Plan

项目未发布（无外部用户），BREAKING 改名零迁移成本：单 PR 内 core → 绑定 → 壳 →
测试 → 文档 → 生成物一次改完，`pnpm check` + 四端测试全绿即完成。回滚 = revert
该 PR。
