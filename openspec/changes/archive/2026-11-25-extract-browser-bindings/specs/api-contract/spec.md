## MODIFIED Requirements

### Requirement: worker 泛化分发与单常驻拓扑

worker 消息协议 MUST 是 `{handle, method, args}` 泛化分发
（`objects.get(handle)[method](...)`），是与动词数量无关的固定模板——core 加
方法时三端壳与 worker 零改动。`handle` MUST 是 `number | string`：数字 =
句柄表分配的实例句柄；字符串 = 模块命名空间名（类工厂与模块自由函数经
`{handle:"touchstone"|"frequency", method:<core 名机械 camelCase>}` 路由，
命名空间只做路由不重命名方法）——MUST NOT 用哨兵值（如 `handle==0`）表达
"构造"语义。wasm 导出 MUST 恒为单条通用 `call(handle, method, args)`，
MUST NOT 存在逐动词导出入口；Rust 无反射，名字→函数的分派 MUST 由各资源
模块手写 `match` 实现并在 `#[wasm_bindgen(start)]` 注册命名空间——加方法 =
该模块 `match` 加一臂，worker/壳/types 零改动。句柄表、dispatch `match` 与
start 钩子 MUST 住在 browser crate，MUST NOT 出现在 core。`_` 前缀逃生口方法
MUST 被自动过滤不进 worker 命令面。自常驻 worker 落地起至绑定高级能力立项前
MUST 维持单常驻 worker 拓扑；多 worker 分桶 MUST 推迟到绑定高级能力立项之后
且有实测需求才立项。

自由函数（如 `frequencyUnits`/`liveCount`）MUST 经命名空间 handle 走 worker
（名单在 Rust 拼、计数在 Rust 读），主线程壳 MUST NOT 在 JS 里派生名单或自存
计数（铁律十一：壳零计算）；二者同归 `"frequency"` 命名空间（`live_count`
数的就是 `Frequency`），MUST NOT 为诊断函数新造 `"system"` 槽。
**例外**：`FrequencyUnit` 常量对象 MUST 由主线程直 import 构建期生成物——它是
普通 JS 常量对象，import 不实例化 wasm，经 worker 中转反而是无意义搬运
（铁律八防的是"主线程执行 wasm"，读常量不碰 wasm）。

#### Scenario: 加动词零改动

- **WHEN** core 新增一个域动词并完成三端绑定
- **THEN** `netwave.worker.js` 分发器代码无需任何修改即可路由该动词

#### Scenario: 构造经命名空间 handle 而非哨兵

- **WHEN** 浏览器壳调用 `Touchstone.fromData(frequency, data, z0, parameter)`
- **THEN** 发出的消息是 `{handle:"touchstone", method:"fromData", args:[...]}`
- **AND** 协议中不存在以 `handle==0` 等哨兵值表达构造的形态

#### Scenario: wasm 导出面恰为 call + 注册钩子

- **WHEN** 解析 wasm glue `.d.ts` 的顶层导出集合
- **THEN** 导出恰为 `call` + `register_resources`（+ wasm-pack 生成的 init/默认
  导出；`register_resources` 是 `#[wasm_bindgen(start)]` 注册钩子，wasm-bindgen
  无视 Rust 可见性必按名导出——它是注册入口不是动词，钉死的本意是"无逐动词
  入口"；`FrequencyUnit`/`WavelengthUnit` 由构建期生成物提供，不经 wasm glue）
- **AND** 无任何逐动词入口（`touchstone_from_data`/`frequency_npoints` 等）
- **AND** 无任何自由函数直导出（`frequency_units`/`live_count` 经命名空间路由）
- **AND** `check_verbs.py` 钉死该集合，多一个少一个即红

#### Scenario: 词汇常量主线程直读不经 worker

- **WHEN** 浏览器主线程 import `FrequencyUnit`
- **THEN** 从构建期生成物直读，不实例化 wasm、不产生 worker 消息（普通常量
  对象直读）
- **AND** `frequencyUnits()` 名单仍来自该枚举、由 Rust 拼接经 worker 返回，
  壳内无 `Object.keys` 等派生计算

#### Scenario: 句柄表与 dispatch 住 browser crate

- **WHEN** grep `core/src/` 全目录
- **THEN** `wasm_bindgen`、句柄表、`call_namespace` dispatch 零命中
- **AND** 这些符号全部定义在 `browser/src/`

### Requirement: 跨端词汇零手抄

跨端共享的枚举词汇与常量表 MUST 在 core 定义一次，经绑定宏反射（pyo3 `add_class`、
napi 生成 `.d.ts`）或构建期机械抽取（browser 端从 core enum 抽成员名与 ordinal，
落 `values.generated.mjs`）或 core 透传函数自我发现地暴露到三端。py/ts 源码
与手写声明文件 MUST NOT 手抄成员列表、字符串表或数值表；新增词汇 MUST 只改 core
一处，三端经重新构建自动一致。

#### Scenario: 加词汇只改 core

- **WHEN** 新增一个枚举变体
- **THEN** 改动仅发生在 core enum（及其穷尽数值匹配）；三端重新构建后成员集合
  自动一致，绑定壳零改动

#### Scenario: browser 枚举 ordinal 与 core 一致

- **WHEN** 比对构建期生成物 `values.generated.mjs` 的枚举成员 ordinal 与 core
  `from_ordinal` 的映射
- **THEN** 二者逐成员一致（生成物按变体声明顺序抽取，core `from_ordinal` 等于
  `iter().nth()`）
