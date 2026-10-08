# api-contract Specification

## Purpose

定义 netwave 跨语言（core/python/node/wasm）API 面的长期结构契约：三层职责划分、
类式 API 形态、显式托管与内存回收、z0 双动词、频率轴单位与结构变更语义——防止
功能缺口从各端私生长数学层撕开，是绑定层设计与 code-review 的判定依据。

## Requirements

### Requirement: 三层 API 契约（数据/计算/结构）

API 面 MUST 分三层且三端一致：① **数据层**——交错 f64 缓冲的可写视图
（Python ndarray 花式索引 / TS typed array 索引与 `subarray` / wasm
`Float64Array`），直接暴露；② **计算层**——域动词（`to_z`/`to_y`/`cascade`/
`se2gmm`/`tdr`/`renormalize` 等），唯一数值权威，全在 core；③ **结构层**——
改形状/元数据的 core 动词（`set_frequencies`/`interpolate`/`renumber`/
`add_port` 等），重分配内存。绑定层 MUST NOT 暴露 `matmul`/`solve`/`inv`/`eig`
等线代原语；计算层功能缺口 MUST 走 OpenSpec 变更进 core 后四端同步发版。

#### Scenario: 无线代原语泄漏

- **WHEN** 检查三端公开 API 面（`.pyi`、`.d.ts`、wasm-bindgen 导出）
- **THEN** 无任何矩阵乘/求逆/特征值等线代原语导出
- **AND** 数值计算只经 core 域动词发生

#### Scenario: 结构动词后旧视图作废

- **WHEN** 用户调用任一结构层动词（如 `interpolate`）后仍持有调用前的缓冲视图
- **THEN** API 文档（rustdoc/docstring/JSDoc）写明旧视图行为未定义、必须重新
  获取；wasm 端 memory.grow 后旧 `Float64Array` 被硬件强制 detach
- **AND** 结构动词在类型层面返回新对象，不提供原地修改型签名

### Requirement: 有状态对象用类、无状态变换用模块函数

持有频率轴 + S 主数据 + z0 的对象 MUST 是类：core `pub struct Network`，
Python `#[pyclass]`、Node napi struct、浏览器 wasm-bindgen struct 原生导出，
域动词是实例方法（对齐 skrf `Network` 惯例）。无状态一次性变换（如 Touchstone
文本解析）MUST 是模块级函数，不硬包成类。

#### Scenario: 三端类形态一致

- **WHEN** 三端各自实例化 `Network` 并调用同一域动词
- **THEN** 三端均为实例方法调用形态，动词名一致（TS 仅机械 camelCase）

### Requirement: 显式托管入口与显式内存回收

wasm 端数据进入 worker 线性内存 MUST 经显式命名入口
`Network.upload(view, nfreq, nports)`——shape 显式传入（裸 `Float64Array`
长度无法唯一分解出维度），调用后原 buffer 声明失效（破坏性语义由方法名表达），
返回主线程 `Network` 壳实例（壳内数字 handle，真数据与句柄表在 worker 内 core）。`upload` 是
浏览器专属入口（只有浏览器存在 worker 线性内存边界）；node/Python MUST NOT
另造 `upload`——构造器 `Network(data)` 即数据入口，`new Network()` 走普通
结构化克隆，输入永不静默消耗。内存回收 MUST 提供显式实例方法 `drop()` 立即
归还 arena，GC/Drop 仅作兜底；公开面 MUST NOT 存在 `drop(handle)` 函数形态
（数字 handle 是 `@internal` 协议细节）。`drop()` 的跨 realm 语义（浏览器
registry 驱动 worker 释放、node napi finalizer、共享不误删）见
[memory-lifecycle spec](../memory-lifecycle/spec.md)。

#### Scenario: upload 后原视图失效

- **WHEN** 浏览器端对某 `Float64Array` 视图调用
  `Network.upload(view, nfreq, nports)`
- **THEN** 原 buffer 处于 detached 状态（`byteLength === 0`）
- **AND** 后续读取走壳实例方法 `net.readElement(idx)`，不再传 handle

#### Scenario: drop 立即回收不依赖 GC

- **WHEN** 任一端调用实例 `drop()` 且不强制 GC
- **THEN** 对应 arena 内存立即归还（确定性，不等 GC）

#### Scenario: node/Python 无 upload

- **WHEN** 检查 node/Python 公开导出面
- **THEN** 无 `upload`；数据入口是构造器，实例上亦无 `upload`

### Requirement: z0 双动词语义分离

参考阻抗变更 MUST 拆成两个动词：`renormalize(z0)` 属计算层，S 数据随之重算、
主数据变更；`set_z0_reference(z0)` 属结构层，只改端口参考标签、S 不动、派生量
（z/y）变。两者 MUST NOT 合并为一个名字。

#### Scenario: renormalize 改主数据

- **WHEN** 调用 `renormalize(z0_new)` 后读取 `s`
- **THEN** `s` 数值相对调用前已按新参考阻抗重算（与 skrf z0 setter 行为一致，
  golden 对拍容差引用 manifest key）

#### Scenario: set_z0_reference 不动主数据

- **WHEN** 调用 `set_z0_reference(z0_new)` 后读取 `s`
- **THEN** `s` 逐 bit 不变；读取 `z` 时派生值按新 z0 变化

### Requirement: 频率轴主数据恒为 f64 Hz

core 频率轴主数据 MUST 永远存 f64 Hz，单位歧义 MUST NOT 进入计算层
（解析 `# GHZ` 文件时在解析层换算为 Hz 入库）。派生换算值 MUST NOT 作为
第二份主数据存储，绑定层 MUST NOT 自存单位状态或自实现换算（三层契约
推论）。`unit` 的存放位置已定案：core 以 `FrequencyUnit` enum 作元数据
（词汇与倍率权威见 `frequency-unit` capability），绑定层不自存。`f_scaled`
的命名与暴露形态（property vs 方法）、`Frequency` 独立类 vs `Network` 属性
属未定设计决策，MUST 在首个字符串入参入口立项时的 design.md 定案，
本 spec 不提前焊死。

#### Scenario: 单位换算在解析时完成

- **WHEN** 解析 `# GHZ` 选项行的 Touchstone 文件
- **THEN** core 频率轴主数据为 Hz（文件值 × 1e9）

#### Scenario: 单位形态未定案不得实现

- **WHEN** `f_scaled` 形态尚未在立项 design.md 定案，有人提议
  在绑定层实现单位换算或自存 unit
- **THEN** code-review Standards 轴拒绝（违反三层契约：绑定层不自存状态、
  不自算数值）

### Requirement: 跨端词汇零手抄

跨端共享的枚举词汇与常量表 MUST 在 core 定义一次，经绑定宏反射（pyo3 `add_class`、
napi/wasm-bindgen 生成 `.d.ts`）或 core 透传函数自我发现地暴露到三端。py/ts 源码
与手写声明文件 MUST NOT 手抄成员列表、字符串表或数值表；新增词汇 MUST 只改 core
一处，三端经重新构建自动一致。

#### Scenario: 加词汇只改 core

- **WHEN** 新增一个枚举变体
- **THEN** 改动仅发生在 core enum（及其穷尽数值匹配）；三端重新构建后成员集合
  自动一致，绑定壳零改动

### Requirement: 无隐藏派生状态与频率轴原子变更

`Network` MUST NOT 缓存任何派生结果——`to_z()` 等每次基于当前主数据现算，
用户直接写视图后无需 sync 调用。改频率 MUST 是 `(freq_axis, s)` 一个原子事务，
MUST NOT 提供单独的频率轴 setter。新增频点 MUST 经
`add_frequency(f, method)` 且 `method` 为必填参数（插值 / 用户指定完整 p×p
矩阵 / 显式零填充），不存在"默认加一行"。

#### Scenario: 视图直写后派生量即时正确

- **WHEN** 用户经可写视图改写某 S 元素后调用 `to_z()`
- **THEN** 返回的 Z 基于改写后的数据，无需任何 sync/refresh 调用

#### Scenario: 加频点必须显式给来源

- **WHEN** 调用 `add_frequency` 未传 `method`
- **THEN** 调用失败（参数缺失报错），不发生隐式补零或默认插值

### Requirement: worker 泛化分发与单常驻拓扑

worker 消息协议 MUST 是 `{handle, method, args}` 泛化分发
（`objects.get(handle)[method](...)`），是与动词数量无关的固定模板——core 加
方法时三端壳与 worker 零改动。`handle` MUST 是 `number | string`：数字 =
core 计数器分配的实例句柄；字符串 = core 模块命名空间名（类工厂与模块自由
函数经 `{handle:"network"|"frequency", method:<core 名机械 camelCase>}` 路由，
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

- **WHEN** 浏览器壳调用 `Network.upload(view, nfreq, nports)`
- **THEN** 发出的消息是 `{handle:"network", method:"upload", args:[...]}`
- **AND** 协议中不存在以 `handle==0` 等哨兵值表达构造的形态

#### Scenario: wasm 导出面恰为 call + 常量枚举

- **WHEN** 解析 wasm glue `.d.ts` 的顶层导出集合
- **THEN** 导出恰为 `call` + `FrequencyUnit` + `register_resources`（+ wasm-pack
  生成的 init/默认导出；`register_resources` 是 `#[wasm_bindgen(start)]` 注册
  钩子，wasm-bindgen 无视 Rust 可见性必按名导出——它是注册入口不是动词，钉死
  的本意是"无逐动词入口"）
- **AND** 无任何逐动词入口（`network_upload`/`frequency_npoints` 等）
- **AND** 无任何自由函数直导出（`frequency_units`/`live_count` 经命名空间路由）
- **AND** `check_verbs.py` 钉死该集合，多一个少一个即红

#### Scenario: 词汇常量主线程直读不经 worker

- **WHEN** 浏览器主线程 import `FrequencyUnit`
- **THEN** 不实例化 wasm、不产生 worker 消息（普通常量对象直读）
- **AND** `frequencyUnits()` 名单仍来自该枚举、由 Rust 拼接经 worker 返回，
  壳内无 `Object.keys` 等派生计算
