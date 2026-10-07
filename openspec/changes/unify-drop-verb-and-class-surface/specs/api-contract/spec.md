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
