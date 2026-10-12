# Design

## Context

动机见 [proposal.md](proposal.md)。本设计只讲「怎么做」。当前状态（已核实，
出处见各源文件行号与 [proposal.md](proposal.md) 的已核实事实段）：

- `Touchstone` 已含 `Network` 全部状态（`frequency` + `s` + `z0` + 元数据），
  `Network` 是其真子集。
- core `Touchstone::s()` 返 `&self.s`（`&[f64]` 借用，零拷贝）；Python `s` 经
  `borrow_from_array` 已是零拷贝活证据；node `s` 当前 `to_vec()` 拷贝；浏览器
  `s` 经克隆 + 结构化克隆过界（无共享内存）。
- 浏览器 `Touchstone` 构造器 private（「Construction IS parsing」），数据入口只有
  解析工厂 `fromText`/`fromFile`/`fromUrl`，无裸数据构造器。
- `upload` 是 `Network` 专属概念，`Touchstone` 浏览器数据入口是 `fromBytes`（transfer）。

约束：铁律八（常驻 worker，构造器无法 async）、铁律十一（绑定薄壳零计算）、
铁律十二（名字单源）、新增铁律十五（构造入口一律 `fromX` 工厂，公开面禁裸构造器）。

## Goals / Non-Goals

**Goals:**

- node `Touchstone.s` 改零拷贝（`Arc` + `from_external`），与 Python 对齐。
- 四端统一数据入口 `from_data`/`fromData` 工厂（含 core `new` 改名）。
- 零拷贝证据从 `read_element` 迁到「派生数据回读」（纯用既有面）。
- 先建新、后拆旧，全程无功能真空。

**Non-Goals:**

- 不新增任何 `Touchstone` 公开属性/函数（改名非净增；`fromData` 顶替 `new`/`upload`）。
- 浏览器 `s` 不做共享内存（无 SAB 前提，维持 transfer/克隆回传）。
- 不给 `Touchstone` 加活对象计数器（封存见证 = 访问报错）。
- 不碰 `Frequency` 的零拷贝/生命周期机制（已合规，仅去 `Network` 引用）。

## Decisions

### `Arc<Vec<f64>>` 落 `Touchstone.s` 字段，node 走 `from_external`

`Vec<f64>` → `Arc<Vec<f64>>`，`from_text`/`from_data` 构造时 `Arc::new`，
`s()` 仍返 `&[f64]`（`&self.s` 自动解引用，core 内部零改动）。node `get_s` 改
`ArrayBuffer::from_external`：clone 一份 `Arc` 塞进 finalize 回调，JS 侧
`Float64Array` 视图底层直接指向 core 堆内存，GC 时 finalize drop 该 `Arc` clone。

- 为何 `Arc` 而非 `Pin`/裸指针：napi-rs `from_external` 需要一个能在 finalizer
  里安全 drop 的 owned 句柄；`Arc` clone 是 Send + 引用计数，天然满足「多视图
  共享 + 最后一个释放」。
- 备选（否决）：node 维持拷贝——违背用户拍板「node 也要零拷贝」。
- Python 端不动：`borrow_from_array` 的 base object = pyclass 本身已保活。

### `Resource` trait 加 core 内部 `as_any`，browser `fromData` 臂下转 `Frequency`

浏览器 `fromData(frequency, data, z0, parameter)` 的 worker 侧要从 arg 0 的
freqHandle 取出已托管的 `Frequency` 实例。资源表存 `Box<dyn Resource>`，取具体
类型需 `as_any`：给 `Resource` trait 加 `fn as_any(&self) -> &dyn Any`（core
内部方法，非公开面、不上浮绑定），`call_namespace` 的 `"fromData"` 臂
`downcast_ref::<Frequency>()` 拿到 `&Frequency` 后调 `Touchstone::from_data`。

- 为何 `as_any` 而非给 `Resource` 加 `as_frequency()`：`Any` 下转是标准做法，
  新增资源类型零改 trait；点名方法每加一类型即污染 trait。
- 用户层从头到尾只传 `Frequency` 对象，handle 是壳内部读 `frequency.handle` 的
  传输细节，绝不要求用户手写 handle（与 Python/node 同签名）。

### `fromData` 工厂返回 `Promise`，绕开 JS 构造器不能 async

浏览器 `static fromData(...)` 内部读 `frequency.handle` + `data`/`z0`/`parameter`
发一条 `{handle:"touchstone", method:"fromData", args:[...]}`，`data` 进 transfer
list，返回 `Promise<Touchstone>`。工厂天然可 async，无需「未就绪壳」两阶段构造。

- 备选（否决）：private 构造器 + async init 方法——两阶段状态机是 footgun，
  且违背「构造即解析完成」的既有 `Touchstone` 不变式。

### 零拷贝证据 = 派生数据回读（不新增 `read_element`）

删 `read_element` 后，「同一块内存」用既有派生面证明：取零拷贝视图 `ts.s` →
改写元素 → 读 `ts.data("S","MA")`（或 `ts.z`，core 从活 `s` 现算）→ 换算回 RI
与写入值比对。比单纯重读 `s` 更强：连「core 计算读穿到该内存」一并证。
Python/node 双端各跑；`cross_compare.py` 的「改元素→回读」段据此改写，输入换真实
Touchstone。

### 先建新后拆旧（构建顺序不变式）

实现严格分四阶段（见 tasks）：① 建零拷贝新面（core `Arc` + `new`→`from_data` +
browser `"fromData"` 臂 + `as_any`；node `from_external`；四端工厂）→ ② 新面测试
全绿，`Network`/自由函数**仍在**，新旧共存 → ③ 确认新面完全接管后才删 `Network`
类与 `fill_pattern`/`read_element` → ④ 收尾（dump/cross_compare/check_verbs/spec/
README/Plan）。

- 为何：先删旧会造成功能真空（数据入口/零拷贝证据断档），RED 测试无处挂。

### Python 端反 skrf 直觉的偏离（铁律十五 vs 铁律十）

铁律十要求 skrf 兼容（`skrf.Network(...)` 直接构造），铁律十五要求禁裸构造器。
冲突时取铁律十五：Python 用户不能再 `Touchstone(...)`，须写 `from_data`/`from_file`。
更强收获 = 四端接口完全统一（浏览器 worker async 约束推广全端），且 `fromX` 语义
自解释（「从数据造」vs「从文件造」）。属铁律十既有 worker 豁免的延伸，账本已立案。

## Risks / Trade-offs

- [`Arc` 改 `s` 字段波及所有构造点] → `from_text`/`from_data` 集中包 `Arc::new`，
  `s()` 签名不变（`&[f64]`），下游读方零改动；编译器逐个构造点报错兜底。
- [node `from_external` finalize 生命周期错则 use-after-free] → 采用 napi-rs 官方
  实证模式（finalize 回调 drop `Arc` clone），测试断言视图改写后派生回读一致 +
  强制 GC 后进程不崩。
- [anti-tautology 自检失效（scaffold bin 删除后仍扰旧名）] → 必做连带：
  `cross_compare.py:120` 扰动目标从 `python.bin`/`node.bin`/`wasm.bin` 改扰
  `_ts_*` bin，否则自检假绿。
- [改名 BREAKING 波及测试/文档面广] → 全仓 grep 清单（`Touchstone::new`/`#[new]`/
  `#[napi(constructor)]`/`Network`/`upload`/`fill_pattern` 等）作验收闸门，零命中才算完。
- [先删后建真空] → 「先建新后拆旧（构建顺序不变式）」+ tasks 里 GREEN 测试先于删除任务。

## Migration Plan

无数据迁移（纯 API 重构）。用户侧迁移：`new Touchstone(f, data, z0, p)` →
`Touchstone.from_data(...)`/`fromData(...)`；`Network` 全部用法 → `Touchstone`；
`upload(buf)` → `fromData(freq, buf, z0, p)`。回滚 = revert 本 change 提交（无
持久化状态变更）。
