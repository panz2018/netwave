# Spec Delta

## Purpose

定义 `Frequency` 在浏览器双 realm 与 node 单 realm 下的内存生命周期契约：Rust
`Drop` 经见证计数器可证、主线程 `FinalizationRegistry` 驱动 worker 释放、共享所有权
不误删、显式 `drop()` 确定性即时、node napi finalizer 自动回收。使跨 realm 内存
管理有可实测、可回归的硬约束，杜绝「Map 删了但 Rust `Drop` 没跑」的假绿。

## ADDED Requirements

### Requirement: Rust `Drop` 经见证计数器可证

`Frequency` 的内存释放 MUST 由 Rust `Drop`（RAII）完成，生产代码 MUST NOT 含任何
手动内存管理逻辑。为可实测，core MUST 提供活对象计数（构造 +1 / `Drop` −1）与
`live_count()`；该计数器常驻编译（`Frequency` 为大数据对象，一次 atomic 增减相对
其分配可忽略，不设 feature 门控），仅作只读诊断探针，不持数据、无副作用。
真值来源：wasm-bindgen
0.2.128 源码（每个 `#[wasm_bindgen]` class 自动生成 `FinalizationRegistry`，构造
`register`、GC 回调 `free`）+ 本 spec 的实测断言。本契约无数值容差（断言为计数
归零，非数值比较）。

#### Scenario: 计数器见证 Drop 真跑

- **WHEN** 构造一个 `Frequency` 后将其唯一引用丢弃并强制 GC，轮询 `live_count()`
- **THEN** 计数从 1 归零（证明 Rust `Drop` 执行，而非仅 JS 侧对象消失）

### Requirement: 主线程 registry 驱动 worker 释放（浏览器双 realm）

浏览器端 `Frequency` 真数据活在常驻 worker（铁律八），主线程仅持数字 handle 壳。
主线程 MUST 自建 `FinalizationRegistry`，其 held 值 MUST 是**不反向引用 wrapper**
的数字 handle；壳被 GC 时回调 MUST 经 `postMessage {cmd:"dropFrequency", handle}`
通知 worker，worker MUST 执行 `frequencies.get(handle).free()` +
`frequencies.delete(handle)` 触发 Rust `Drop`。worker 的 `frequencies` 地址表
MUST NOT 被删除（跨边界只传数字 handle，worker 靠它路由消息）。

#### Scenario: 壳被 GC 触发 worker 释放

- **WHEN** 丢弃主线程壳最后一个引用并强制 GC
- **THEN** registry 回调 → worker `free()` + `delete` → `live_count()` 归零

#### Scenario: held 不钉活 wrapper

- **WHEN** 检查 registry 的 held 值
- **THEN** held 为数字 handle，不含对 wrapper 的强引用（否则 wrapper 永不回收）

### Requirement: 共享所有权不误删

同一 handle 被多个主线程引用（如 circuit 与 network 同持 `f`）时，worker 对象
MUST 在**全部**引用消失前保持存活。释放部分引用 MUST NOT 触发释放；仅当最后一个
引用被 GC 时 MUST 触发 worker 释放。

#### Scenario: 释放其一计数不减

- **WHEN** 同 handle 两个引用，释放其一并强制 GC
- **THEN** `live_count()` 不减（对象仍活）

#### Scenario: 释放其二归零

- **WHEN** 再释放最后一个引用并强制 GC
- **THEN** `live_count()` 归零

### Requirement: 显式 `drop()` 确定性即时（JS-only）

JS 端（浏览器 + node）MUST 提供 `drop()` 作确定性逃生口：调用后 MUST **不**依赖
GC 即时触发 Rust `Drop`。`drop()` 是铁律十（skrf 兼容）的**已立案偏离**——其
「更强收获」为：JS GC 时机非确定性是平台特有约束，skrf 无对应物因其不跑
worker-realm wasm（见 design「`drop()` 公开 API」）。Python/Rust MUST NOT 加
`drop()`（引用计数/RAII 全自动，加 = footgun 且违铁律十）。

#### Scenario: drop 不依赖 GC 即时回收

- **WHEN** 调 `drop()` 后**不**强制 GC
- **THEN** `live_count()` 立即减（确定性，不等 GC）

#### Scenario: Python/Rust 无 drop

- **WHEN** 检查 Python 与 Rust 的 `Frequency` 公开面
- **THEN** 无 `drop()` 方法（自动回收，手动 drop 是 footgun）

### Requirement: node napi finalizer 自动回收（单 realm）

node 端 `Frequency` MUST 由 napi cleanup finalizer 在 JS 对象被 GC 时自动跑 Rust
`Drop`（单 realm，无压制）。node `Frequency` MUST NOT 进入 `hosted` Map（用户直接
持 napi 实例，无 Map 强引用 → 自带 finalizer 正常工作，与浏览器 worker 压制场景相反）。
`drop()` 在 node 可选（finalizer 已自动，`drop()` 仅供确定性提前释放）。

#### Scenario: node 壳 GC 自动 Drop

- **WHEN** 丢弃 node `Frequency` 实例唯一引用并强制 GC（`--expose-gc`）
- **THEN** `live_count()` 归零（napi finalizer 触发 Rust `Drop`）

#### Scenario: node 对象不进 hosted Map

- **WHEN** 检查 node 端 `Frequency` 的持有方式
- **THEN** 不经 `hosted` Map 强引用（否则重蹈 worker 压制陷阱）
