# Spec Delta

## Purpose

统一显式内存回收方法名：`api-contract` 原写 `release()`，与已定案的
memory-lifecycle spec 冲突；本 delta 将方法名对齐为 `drop()`，消除两份主
spec 打架。

## MODIFIED Requirements

### Requirement: 显式托管入口与显式内存回收

wasm 端数据进入 worker 线性内存 MUST 经显式命名入口 `Network.upload(view)`
——调用后原 buffer 声明失效（破坏性语义由方法名表达）；`new Network()` 走普通
结构化克隆，输入永不静默消耗。内存回收 MUST 提供显式 `drop()` 立即归还
arena，GC/Drop 仅作兜底。`drop()` 的跨 realm 语义（浏览器 registry 驱动
worker 释放、node napi finalizer、共享不误删）见 memory-lifecycle spec。

#### Scenario: upload 后原视图失效

- **WHEN** JS 端对某 `Float64Array` 视图调用 `Network.upload(view)`
- **THEN** 原 buffer 处于 detached 状态（`byteLength === 0`）
- **AND** 后续方法调用只传 handle，无重复上传

#### Scenario: drop 立即回收不依赖 GC

- **WHEN** JS 端调用 `drop()` 且不强制 GC
- **THEN** 对应 arena 内存立即归还（确定性，不等 GC）
