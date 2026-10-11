# Spec Delta

## MODIFIED Requirements

### Requirement: 有状态对象用类、无状态变换用模块函数

持有频率轴 + S 主数据 + z0 的对象 MUST 是类，且数据状态类唯一为
`Touchstone`（`Network` 已退役，其全部状态——`frequency`/`s`/`z0`/`nports`/
元数据——由 `Touchstone` 承载）：core `pub struct Touchstone`，Python
`#[pyclass]`、Node napi struct、浏览器 wasm-bindgen struct 原生导出，域动词是
实例方法（对齐 skrf 惯例）。解析虽是一次性动作，但其产物（频率轴/S 主数据/z0/
元数据）是长活状态，归"状态类"而非模块级函数（touchstone-core capability 落地）。
仅**无状态**一次性变换（纯输入→纯输出、无留存数据）MUST 是模块级函数，不硬包成类。

#### Scenario: 三端类形态一致

- **WHEN** 三端各自经 `Touchstone` 工厂实例化并调用同一域动词
- **THEN** 三端均为实例方法调用形态，动词名一致（TS 仅机械 camelCase）

#### Scenario: Touchstone 是状态类非模块函数

- **WHEN** 检查三端导出面中 Touchstone 解析能力的形态
- **THEN** 解析入口是 `Touchstone` 类工厂（`fromText`/`fromFile`/`fromUrl`），
  解析结果由实例属性承载；不存在返回裸数据元组的模块级解析函数

### Requirement: 无隐藏派生状态与频率轴原子变更

`Touchstone` MUST NOT 缓存任何派生结果——`z`/`y`/`g`/`h`/`data` 等每次基于当前
主数据 `s` 现算，用户直接写视图后无需 sync 调用。改频率 MUST 是
`(freq_axis, s)` 一个原子事务，MUST NOT 提供单独的频率轴 setter，也 MUST NOT 有
原地 `add_frequency` 式增量动词（`add_frequency` 从未实现，本 change 从契约删除）。
新增频点 MUST 经**重建**：读当前轴 `f`/`f_scaled`/`wavelength` 拼新轴 →
`from_f`/`from_wavelength` 造新 `Frequency` → 连同扩展后的 `s` 经
`from_data`/`fromData` 造新 `Touchstone`；新频点的 p×p 矩阵来源 MUST 显式给出
（插值 / 用户指定完整 p×p 矩阵 / 显式零填充），不存在"默认加一行"。

#### Scenario: 视图直写后派生量即时正确

- **WHEN** 用户经可写视图 `ts.s` 改写某 S 元素后读 `ts.z`
- **THEN** 返回的 Z 基于改写后的数据，无需任何 sync/refresh 调用

#### Scenario: 加频点必须显式给来源

- **WHEN** 经 `from_f` + `from_data` 重建加频点但未显式给出新频点矩阵来源
- **THEN** 调用失败（参数缺失报错），不发生隐式补零或默认插值

### Requirement: worker 泛化分发与单常驻拓扑

worker 消息协议 MUST 是 `{handle, method, args}` 泛化分发
（`objects.get(handle)[method](...)`），是与动词数量无关的固定模板——core 加
方法时三端壳与 worker 零改动。`handle` MUST 是 `number | string`：数字 =
core 计数器分配的实例句柄；字符串 = core 模块命名空间名（类工厂与模块自由
函数经 `{handle:"touchstone"|"frequency", method:<core 名机械 camelCase>}` 路由，
命名空间只做路由不重命名方法）——MUST NOT 用哨兵值（如 `handle==0`）表达
"构造"语义。wasm 导出 MUST 恒为单条通用 `call(handle, method, args)`，
MUST NOT 存在逐动词导出入口；Rust 无反射，名字→函数的分派 MUST 由各资源
模块手写 `match` 实现并在 `#[wasm_bindgen(start)]` 注册命名空间——加方法 =
该模块 `match` 加一臂，worker/壳/types 零改动。`_` 前缀逃生口方法 MUST 被
自动过滤不进 worker 命令面。自常驻 worker 落地起至绑定高级能力立项前 MUST
维持单常驻 worker 拓扑；多 worker 分桶 MUST 推迟到绑定高级能力立项之后且
有实测需求才立项。

自由函数（如 `frequencyUnits`/`liveCount`）MUST 经命名空间 handle 走 worker
（名单在 Rust 拼、计数在 Rust 读），主线程壳 MUST NOT 在 JS 里派生名单或自存
计数（铁律十一：壳零计算）；二者同归 `"frequency"` 命名空间（`live_count` 定义
在 `frequency.rs`、数的就是 `Frequency`），MUST NOT 为诊断函数新造 `"system"` 槽。
**例外**：`FrequencyUnit` 常量对象 MUST 由主线程直 import glue——它是 glue JS 的
普通常量对象，import 不实例化 wasm，经 worker 中转反而是无意义搬运（铁律八防的
是"主线程执行 wasm"，读常量不碰 wasm）。

#### Scenario: 加动词零改动

- **WHEN** core 新增一个域动词并完成三端绑定
- **THEN** `netwave.worker.js` 分发器代码无需任何修改即可路由该动词

#### Scenario: 构造经命名空间 handle 而非哨兵

- **WHEN** 浏览器壳调用 `Touchstone.fromData(frequency, data, z0, parameter)`
- **THEN** 发出的消息是 `{handle:"touchstone", method:"fromData", args:[...]}`
- **AND** 协议中不存在以 `handle==0` 等哨兵值表达构造的形态

#### Scenario: wasm 导出面恰为 call + 常量枚举

- **WHEN** 解析 wasm glue `.d.ts` 的顶层导出集合
- **THEN** 导出恰为 `call` + `FrequencyUnit` + `register_resources`（+ wasm-pack
  生成的 init/默认导出；`register_resources` 是 `#[wasm_bindgen(start)]` 注册
  钩子，wasm-bindgen 无视 Rust 可见性必按名导出——它是注册入口不是动词，钉死
  的本意是"无逐动词入口"）
- **AND** 无任何逐动词入口（`touchstone_from_data`/`frequency_npoints` 等）
- **AND** 无任何自由函数直导出（`frequency_units`/`live_count` 经命名空间路由）
- **AND** `check_verbs.py` 钉死该集合，多一个少一个即红

#### Scenario: 词汇常量主线程直读不经 worker

- **WHEN** 浏览器主线程 import `FrequencyUnit`
- **THEN** 不实例化 wasm、不产生 worker 消息（普通常量对象直读）
- **AND** `frequencyUnits()` 名单仍来自该枚举、由 Rust 拼接经 worker 返回，
  壳内无 `Object.keys` 等派生计算

## REMOVED Requirements

### Requirement: 显式托管入口与显式内存回收

**Reason**: `Network.upload` 随 `Network` 类退役，`upload` 概念全仓废止；数据
入口统一为四端同名 `fromData`/`from_data` 工厂（铁律十五）。原 requirement 的
scenario 名（`upload 后原视图失效`、`node/Python 无 upload`）承载已废止的
`upload` 语义，改名 scenario 无法在 MODIFIED 下存活，故以 REMOVED+ADDED 整体
替换。

**Migration**: 浏览器 `Network.upload(view, nfreq, nports)` →
`Touchstone.fromData(frequency, data, z0, parameter)`（`data` 进 transfer list，
shape 由 `frequency`/`z0` 推导）；node/Python 构造器 → `fromData`/`from_data`
工厂。`drop()` 语义不变。新契约见下方「显式数据入口与显式内存回收」。

## ADDED Requirements

### Requirement: 显式数据入口与显式内存回收

wasm 端数据进入 worker 线性内存 MUST 经显式命名工厂
`Touchstone.fromData(frequency, data, z0, parameter)`——`frequency` 收 `Frequency`
对象（壳内部读其 handle 发 worker，用户不手写 handle），`data` 经 transfer 移入
worker（调用后原 buffer 声明失效，破坏性语义由 transfer 表达），返回主线程
`Touchstone` 壳实例（壳内数字 handle，真数据与句柄表在 worker 内 core）。
`fromData` 是四端统一的数据入口（node/Python 同名工厂，浏览器经 transfer 移入
worker）；`upload` 概念全仓废止——浏览器无 `upload`，node/Python 亦无。内存回收
MUST 提供显式实例方法 `drop()` 立即归还 arena，GC/Drop 仅作兜底；公开面 MUST NOT
存在 `drop(handle)` 函数形态（数字 handle 是 `@internal` 协议细节）。`drop()` 的
跨 realm 语义（浏览器 registry 驱动 worker 释放、node napi finalizer、共享不误删）
见 [memory-lifecycle spec](../memory-lifecycle/spec.md)。

#### Scenario: fromData 后原视图失效

- **WHEN** 浏览器端对某 `Float64Array` 数据调用
  `Touchstone.fromData(frequency, data, z0, parameter)`（`data` 进 transfer list）
- **THEN** 原 buffer 处于 detached 状态（`byteLength === 0`）
- **AND** 后续读取走壳实例属性 `ts.s`，不再传 handle

#### Scenario: drop 立即回收不依赖 GC

- **WHEN** 任一端调用实例 `drop()` 且不强制 GC
- **THEN** 对应 arena 内存立即归还（确定性，不等 GC）

#### Scenario: 全端无 upload

- **WHEN** 检查四端公开导出面
- **THEN** 无 `upload`；数据入口是 `fromData`/`from_data` 工厂，实例上亦无 `upload`
