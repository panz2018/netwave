# Design

## Context

动机见 [proposal.md](proposal.md#why)。当前同一语义（手动立即释放）的四个名字与
其所在层：

| 层                  | 现名                        | 用户可见                              |
| ------------------- | --------------------------- | ------------------------------------- |
| core Rust           | `Frequency::release()`      | ❌                                    |
| node napi           | `Frequency.free()`          | ✅                                    |
| 浏览器 TS 壳        | `internals.drop(ref)`       | ✅（测试缝）                          |
| worker 命令         | `dropFrequency` / `release` | ❌（本 change 收拢为单条泛化 `call`） |
| JS 句柄函数         | `release(handle)`           | ✅（本 change 退为实例方法）          |
| wasm-bindgen 生成物 | `free()`                    | ❌（本 change 后连调用点都不存在）    |

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
- worker 协议与动词数量无关：单条泛化 `call`，加方法时 worker/壳/types 零改动
  （api-contract「worker 泛化分发与单常驻拓扑」）。
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

| 公开面                                                              | 形态               | 端          |
| ------------------------------------------------------------------- | ------------------ | ----------- |
| `Network.upload(view, nfreq, nports)`                               | 静态，返回壳实例   | 仅浏览器    |
| `new Network(view, nfreq, nports)` / `Network(data, nfreq, nports)` | 构造器             | node/Python |
| `Network.fillPattern(nfreq, nports)`                                | 静态，返回实例     | 三端        |
| `net.readElement(idx)` / `net.drop()`                               | 实例方法           | 三端        |
| `Frequency.fromF(view, unit)` / `f.drop()`                          | 静态 + 实例        | 三端        |
| `frequencyUnits()` / `liveCount()`                                  | 自由函数（无状态） | 三端        |

- **shape 显式传入**：裸 `Float64Array` 长度无法唯一分解出维度，所有
  数据入口（`upload`/构造器）MUST 显式收 `nfreq`/`nports`，
  由 core 断言 `len == nfreq*nports*nports*2`。
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
- **无 `isDropped` 见证**：释放后访问报错本身就是契约（全端一致），额外的
  `isDropped()`/`is_dropped` 属性是第二套真相源，公开面与内部面都不存在；
  释放状态由 core 内部 `dropped` 见证字段支撑，不外露。
- **释放后报错在 core 层单源**：数据访问方法（`npoints`/`read_element`）在
  core 就返回 `Err(Dropped)`，绑定层原样透传——不在各绑定里各写一份
  post-drop 判断（node 曾返回 0 即因判断只存在于 JS 层的反面教材）。错误
  类型 `Dropped` 定义在 core `lib.rs`，全资源共享（旧名 `Released` 随动词
  统一改名，铁律十二）。

### worker 泛化分发：单 `call` 模板 + 每资源 match（cfg=browser）

常驻 worker 原有两张 JS 句柄表——`hosted`（`upload` 移入的裸字节缓冲）与
`frequencies`（worker 内 wasm `Frequency` 实例），释放动词分裂为 `release`(buffer)
与 `dropFrequency`(Frequency)。本 change 把句柄表**整体下沉到 core Rust**，并
落实 api-contract「worker 泛化分发与单常驻拓扑」：JS 的
`objects.get(handle)[method](...)` 天然按名字分发，Rust 无反射，故分发落点是
core 通用 `call` + 各资源模块自己的手写 `match`。

**handle 是 `number | string`，无哨兵值**（`handle == 0` 式暗号否决——读消息
的人不该先背暗号）：

| handle                 | 指向                              | 例                         |
| ---------------------- | --------------------------------- | -------------------------- |
| 字符串 = core 模块名   | 命名空间（类工厂 + 模块自由函数） | `"network"`、`"frequency"` |
| 数字 = core 计数器句柄 | 表内实例                          | `7`                        |

| 消息                                                            | 语义                                                                                                       |
| --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `{handle:"network", method:"upload", args:[view,nfreq,nports]}` | 类工厂                                                                                                     |
| `{handle:"frequency", method:"frequencyUnits", args:[]}`        | 模块自由函数（方法名 = core 名机械 camelCase，命名空间只做路由不重命名）                                   |
| `{handle:"frequency", method:"liveCount", args:[]}`             | 诊断探针：`live_count` 定义在 `frequency.rs`、数的就是 `Frequency`，各归各的命名空间，不新造 `"system"` 槽 |
| `{handle:7, method:"readElement", args:[idx]}`                  | 实例方法                                                                                                   |
| `{handle:7, method:"drop", args:[]}`                            | 释放（分发器拦截 → `remove` → Rust `Drop`）                                                                |

```rust
// resources.rs —— 通用分发器：不认识任何资源类型，永不因加动词而改
pub trait Resource {
    fn call(&mut self, method: &str, args: &[JsValue]) -> Result<JsValue, JsValue>;
}
type NamespaceFn = fn(&str, &[JsValue]) -> Result<JsValue, JsValue>;
struct Registry {
    instances: BTreeMap<u32, Box<dyn Resource>>,
    namespaces: BTreeMap<&'static str, NamespaceFn>,
    next_handle: u32,
}
#[wasm_bindgen]
pub fn call(handle: JsValue, method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
    // 数字 → instances；method=="drop" → remove（触发 Drop）
    // 字符串 → namespaces
}

// network.rs —— 加方法 = 这里 match 加一臂，其余全零改动
impl Resource for Network {
    fn call(&mut self, method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
        match method {
            "readElement" => { /* 解 args → self.read_element */ }
            _ => Err(unknown_method(method)),
        }
    }
}
pub fn call_namespace(method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
    match method { /* "upload" | "fillPattern" 工厂 */ }
}
```

- **wasm 导出恒为一个 `call`**：逐动词入口（`network_upload`/
  `network_fill_pattern`/`network_read_element`/`frequency_from_f`/
  `frequency_npoints`）全部删除——表泛型不等于分发泛化，逐动词入口加动词必改
  worker，违反「加动词零改动」（LL-052）。
- **方案 A（手写 match）而非闭包注册表**：闭包表能自省"有哪些方法"，但 Rust 要
  把不同签名的函数套同一层 downcast 壳才能入表——为不存在的自省需求写管道是过度
  工程。`#[resource]` 属性宏（同 `#[pymethods]` 原理，编译期扫 impl 自动生成
  match）是方法面膨胀后的升级路径，届时对外协议零改动。
- **注册触发 = `#[wasm_bindgen(start)]`**（wasm 加载时自动执行一次）：`lib.rs`
  的 start 调 `network::register()`/`frequency::register()` 把命名空间挂进表——
  加新资源类型 = start 加一行 + 新模块自带 match；加新方法 = 该模块 match 加一臂。
- **`drop` 由分发器拦截**：移除条目是表的操作，故 `method=="drop"` 在分发器处
  `remove(handle)` 直接触发 Rust `Drop`，不经 JS 对象中转；资源自身的固有
  `drop()` 仍是清理单源。wasm `Frequency` 实例不浮出 JS，生成物 `free()` 连
  JS 调用点都不存在。
- **命名空间无实例语义，零特判**：命名空间表不登记 `drop`，字符串 handle 收到
  `method=="drop"` 自然落进命名空间 `match` 的未知方法兜底报错——不写一行
  "命名空间不支持 drop"专属文案（这条消息只可能来自 bug，错误精确度无用户差异）。
- **自由函数经命名空间路由，壳零计算**：`frequencyUnits`/`liveCount` 不再直出
  wasm，全部经 `{handle:"frequency", method:...}` 走 worker——名单在 Rust 里拼、
  计数在 Rust 里读，壳只发一条 `postMessage`（铁律十一：壳内不算数，无论算的是
  词汇还是数值）。例外：`FrequencyUnit` 常量对象保持主线程直 import glue——它是
  glue JS 里的普通常量对象，import 不实例化 wasm，不经 worker 中转（中转才是
  无意义的搬运）。
- **worker JS 零状态 + 零动词表**：`hosted`/`frequencies`/`nextHandle` 与逐动词
  `cmds` 表全删；worker 只剩一条固定模板——await wasm ready 后把
  `{handle, method, args}` 原样转发 core `call`（铁律八：worker 内 wasm 是唯一
  数据权威，表与分发都在 wasm 内而非 JS）。
- **主线程壳类**：`index.browser.ts` 导出 `Network`/`Frequency` 壳类，工厂/静态
  方法发字符串 handle、实例方法发数字 handle，方法体只发一条 `postMessage`
  （纯传输，铁律十一）；`FinalizationRegistry` held 为数字 handle、挂壳实例上。
- **cfg 只门控浏览器**：表与分发代码写在 core crate、只编进 wasm；node/python
  编译时不启用该 cfg，直接持对象、无句柄表。三端统一的是 `drop` 这个名字与行为
  契约，不是那张表；公开形态统一实例方法 `obj.drop()`，`{handle, method:"drop"}`
  仅是浏览器 `postMessage` 协议的内部消息形态，不上浮公开 API。

### 门禁：三端动词集合相等 + wasm 导出面钉死

新增 `scripts/check_verbs.py`（与 `check_vocab_types.py` 同范式：静态门禁与
二进制对拍器 `cross_compare.py` 职责分离）：从三份生成物提取 `Network`/
`Frequency` 类方法名（含静态与实例）与自由函数名，做 camelCase 机械映射归一后
断言等于唯一动词集；`upload` 仅浏览器；`free`/`release` 出现在任一用户可见面即红。

另钉死 wasm glue 导出面：解析 glue `.d.ts`，顶层导出集合 MUST 恰为 `call` +
`FrequencyUnit`（+ wasm-pack 生成的 init/默认导出）——多一个少一个都红。这是
「单条 `call`」不变式的机械钉子：谁再给某个函数挂上 `#[wasm_bindgen]` 直导出，
当场红，不靠 review 肉眼。

## Risks / Trade-offs

- **[改名波及冻结测试]** 内存生命周期测试是已冻结的永久回归 → 只改调用名与
  接收者形态（`f.free()`→`f.drop()`、`release(h)`→`net.drop()`），断言逻辑与
  场景结构零改动；跑全套确认绿即证明行为未变。
- **[骨架膨胀]** 本 change 从改名扩到类骨架 → 骨架只含数据入口 + 读 + 释放
  （`upload`/`fillPattern`/`readElement`/`drop`/`fromF`），任何计算/解析/端口
  语义都不进；扩大的是命名归位，不是功能面。
- **[生成物残留旧名]** `.pyi`/`.d.mts` 缓存旧签名 → 重新生成并 grep 旧名零命中
  作为验收项（LL-008 同类坑）。
- **[分发层原生不可测]** `call` 以 `JsValue` 收发，非 wasm 构建不可构造 →
  纯逻辑（`read_element`/`npoints`/表的 insert/remove）保持原生单测，`call`
  分发与命名空间路由由 worker 往返测试覆盖（`worker.test.ts`）。
- **[句柄表下沉 core 的波及]** `upload`/`readElement` 从 JS Map 读写改为 core
  句柄入口（字节移进 core `Vec<f64>`），是行为等价的搬运 → 往返测试逐 bit 对拍
  托管/未托管两路径不变即证明；wasm 体积增量（一张表 + Mutex）可忽略。
- **[Python 手动 drop 冗余]** Python 有引用计数，`drop()` 看似多余 → 幂等 +
  释放后报错封死误用；换取四端动词单一，收益已在 spec 立案。

## Migration Plan

项目未发布（无外部用户），BREAKING 改名零迁移成本：单 PR 内 core → 绑定 → 壳 →
测试 → 文档 → 生成物一次改完，`pnpm check` + 四端测试全绿即完成。回滚 = revert
该 PR。
