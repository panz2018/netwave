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
| JS 句柄函数         | `release(handle)`           | ✅（本 change 退为实例方法）                 |
| wasm-bindgen 生成物 | `free()`                    | ❌（本 change 后连调用点都不存在）           |

另一层结构问题：脚手架公开面是自由函数 + 裸数字 handle（`upload(view) -> number`、
`readElement(target, idx)`、`release(handle)`），数字无法挂方法，释放只能写成函数
形态 `drop(handle)`，与已拍板的「公开形态统一实例方法 `obj.drop()`」相冲。

约束：wasm-bindgen 为每个 `#[wasm_bindgen]` class 自动生成的释放方法名固定为
`free()`（工具链焊死，见 memory-lifecycle spec「Rust `Drop` 经见证计数器可证」
引用的 wasm-bindgen 0.2.128 源码事实）；该生成物只存在于 worker realm 内部，
用户不可见。

## Goals / Non-Goals

**Goals:**

- 用户可见面「手动释放」只有一个名字：`drop`，且形态统一为实例方法 `obj.drop()`。
- 清理逻辑在 Rust 只有一份实现，手动路径与 RAII 路径共用。
- `Network`/`Frequency` 类骨架三端落地，数字 handle 退回 `@internal`。
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

### Python：`Network`/`Frequency` pyclass 首次导出，含 `drop()`

`python/src/lib.rs` 现只注册 `FrequencyUnit`/`frequency_units`。本 change 注册
`Network`（构造器收数据 + `readElement`/`drop`）与 `Frequency`（`from_f` +
`drop`）两个 pyclass，`#[pymethods]` 内直接命名（pyo3 无名字映射需求，零壳）。
释放后访问数据抛 `PyValueError`。

### 类骨架：数据入口返回实例，读取与释放都是实例方法

公开面归位表（名字全由 core 单源，TS 仅机械 camelCase）：

| 公开面                                     | 形态               | 端          |
| ------------------------------------------ | ------------------ | ----------- |
| `Network.upload(view)`                     | 静态，返回壳实例   | 仅浏览器    |
| `new Network(view)` / `Network(data)`      | 构造器             | node/Python |
| `Network.fillPattern(nfreq, nports)`       | 静态，返回实例     | 三端        |
| `net.readElement(idx)` / `net.drop()`      | 实例方法           | 三端        |
| `Frequency.fromF(view, unit)` / `f.drop()` | 静态 + 实例        | 三端        |
| `frequencyUnits()` / `liveCount()`         | 自由函数（无状态） | 三端        |

- **`upload` 浏览器专属**：只有浏览器存在 worker 线性内存边界，才需要"显式移交"
  入口；node/Python 构造器即数据入口，MUST NOT 另造 `upload`（铁律十二管"同一
  语义同名"，不管"别的平台没有的边界硬造入口"）。
- **`newFrequency` 退役**：core 构造函数已叫 `from_f`，浏览器走 `Frequency.fromF`
  （机械映射），临时名 `newFrequency` 与 `dropFrequency` 一起消失。
- **裸视图读入口删除**：`readElement(target, idx)` 的"未托管视图"分支取消——
  要读就先 `upload` 或 `new Network(view)`，读取只走实例方法。
- **`internals` 测试缝退役**：壳实例本身就是可 GC 对象，`FinalizationRegistry`
  直接挂壳实例，不再需要单独的 ref 包装测试缝。
- **不加整块取回出口**（`toBuffer()` 等）：整块回传属计算动词零拷贝契约，随
  Touchstone 核心立项；骨架期测试用 `readElement` 抽查。

### worker 资源表：下沉 core（cfg=browser）+ worker JS 零状态

常驻 worker 原有两张 JS 句柄表——`hosted`（`upload` 移入的裸字节缓冲）与
`frequencies`（worker 内 wasm `Frequency` 实例），释放动词分裂为 `release`(buffer)
与 `dropFrequency`(Frequency)。本 change 把句柄表**整体下沉到 core Rust**：

```rust
// core，cfg 门控 browser feature
pub enum Resource { Network(Network), Frequency(Frequency) }
static RESOURCES: Mutex<BTreeMap<u32, Resource>>; // 句柄计数器同表递增

// 注册焊死在工厂入口，无专门注册函数；JS 侧只见数字句柄
#[wasm_bindgen]
pub fn network_upload(view: &[f64]) -> u32 {
    let h = next_handle();
    RESOURCES.lock().insert(h, Resource::Network(Network::from_f64(view)));
    h
}
```

- **单一一张表**：`handle → Resource` enum，句柄由 core 单一计数器递增、全局
  唯一，单表查找无歧义；未来 Circuit 等只加 enum 变体，表数量恒为 1。
- **单一 `drop(handle)`**：core 侧 `remove(handle)` 直接触发 Rust `Drop`（RAII），
  不经 JS 对象中转——wasm `Frequency` 实例不再浮出 JS，连生成物 `free()` 的
  JS 调用点都不存在（工具链生成物豁免因此自动满足）。
- **worker JS 零状态**：`hosted`/`frequencies`/`nextHandle` 全删；命令表
  （`networkUpload`/`networkFillPattern`/`networkReadElement`/`frequencyFromF`/
  `drop`/`frequencyUnits`/`liveCount`）退化为把参数/句柄原样转发给 core 的
  `#[wasm_bindgen]` 入口，零分派零状态（铁律八：worker 内 wasm 是唯一数据权威，
  表也应在 wasm 内而非 JS）；cmd 名是 core snake 名的机械 camelCase（铁律九豁免）。
- **主线程壳类**：`index.browser.ts` 导出 `Network`/`Frequency` 壳类，实例持
  数字 handle，方法体只发 `postMessage`（纯传输，铁律十一）；
  `FinalizationRegistry` held 为数字 handle、挂壳实例上。
- **cfg 只门控浏览器**：表代码写在 core crate、只编进 wasm；node/python 编译时
  不启用该 cfg，直接持对象、无句柄表，不会被拖去实现注册表。三端统一的是
  `drop` 这个名字与行为契约，不是那张表；公开形态统一实例方法 `obj.drop()`，
  `drop(handle)` 仅是浏览器 `postMessage` 协议的内部命令形态，不上浮公开 API。

### 门禁：三端动词集合相等

`scripts/cross_compare.py` 扩展：提取 core `pub fn` / pyo3 `#[pymethods]` /
napi `#[napi]` / 浏览器 TS 壳导出的公开动词集合，做 camelCase 机械映射归一后
断言相等；`free`/`release` 出现在任一用户可见面即红。

## Risks / Trade-offs

- **[改名波及冻结测试]** 内存生命周期测试是已冻结的永久回归 → 只改调用名与
  接收者形态（`f.free()`→`f.drop()`、`release(h)`→`net.drop()`），断言逻辑与
  场景结构零改动；跑全套确认绿即证明行为未变。
- **[骨架膨胀]** 本 change 从改名扩到类骨架 → 骨架只含数据入口 + 读 + 释放
  （`upload`/`fillPattern`/`readElement`/`drop`/`fromF`），任何计算/解析/端口
  语义都不进；扩大的是命名归位，不是功能面。
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
