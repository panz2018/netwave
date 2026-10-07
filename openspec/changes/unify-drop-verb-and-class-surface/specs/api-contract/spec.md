# Spec Delta

## MODIFIED Requirements

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

#### Scenario: 加动词零改动

- **WHEN** core 新增一个域动词并完成三端绑定
- **THEN** `netwave.worker.js` 分发器代码无需任何修改即可路由该动词

#### Scenario: 构造经命名空间 handle 而非哨兵

- **WHEN** 浏览器壳调用 `Network.upload(view, nfreq, nports)`
- **THEN** 发出的消息是 `{handle:"network", method:"upload", args:[...]}`
- **AND** 协议中不存在以 `handle==0` 等哨兵值表达构造的形态

#### Scenario: 逐动词 wasm 入口不存在

- **WHEN** grep wasm glue `.d.ts` 与 worker 源码
- **THEN** 除单条 `call`（与词汇/常量导出）外无任何逐动词入口
  （`network_upload`/`frequency_npoints` 等）
