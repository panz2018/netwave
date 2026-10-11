# Spec Delta

## MODIFIED Requirements

### Requirement: 主线程 registry 驱动 worker 释放（浏览器双 realm）

浏览器端 `Touchstone`/`Frequency` 真数据活在常驻 worker（铁律八），主线程仅持
`Touchstone`/`Frequency` 壳类实例（壳内数字 handle，`@internal`）。主线程 MUST
自建 `FinalizationRegistry`，其 held 值 MUST 是**不反向引用壳实例**的数字 handle；
壳被 GC 时回调 MUST 经 `postMessage {handle, method:"drop", args:[]}` 通知
worker，worker MUST 零状态纯转发——句柄注册、查表、分发、释放 MUST 全部发生在
**core 内唯一一张资源表**（cfg 门控 browser feature：数字 handle →
`Box<dyn Resource>` 实例表，字符串 handle → 命名空间表（类工厂 + 模块自由
函数），各资源在自己的模块里手写 `match` 分发并在 `#[wasm_bindgen(start)]`
注册）；`{handle, method:"drop"}` MUST 在 core 侧 `remove(handle)` 直接触发
Rust `Drop`，MUST NOT 经 JS 对象中转。worker JS MUST NOT 存在任何句柄 `Map`、
`nextHandle` 计数器或逐动词命令表（现有 `hosted`/`frequencies` 两表与逐动词
`cmds` 表废止，wasm 导出恒为单条泛化 `call`，见 api-contract「worker 泛化分发与
单常驻拓扑」）；释放动词唯一为 `drop`（句柄全局唯一，单表查找无歧义）；
`postMessage` 协议名 `dropFrequency`/`newFrequency` MUST NOT 存在。句柄表本身
MUST NOT 被删除（跨边界只传 handle，core 靠它路由消息）。

#### Scenario: 壳被 GC 触发 worker 释放

- **WHEN** 丢弃主线程壳最后一个引用并强制 GC
- **THEN** registry 回调 → worker 转发 core `call(handle, "drop", [])` → core
  资源表 `remove` 触发 Rust `Drop` → `live_count()` 归零

#### Scenario: held 不钉活 wrapper

- **WHEN** 检查 registry 的 held 值
- **THEN** held 为数字 handle，不含对 wrapper 的强引用（否则 wrapper 永不回收）

#### Scenario: 表数量恒为一

- **WHEN** 未来 Circuit 等新增句柄资源类型
- **THEN** 只在新资源自己的模块加 `match` 与命名空间注册，资源表模块与释放
  动词均零修改

#### Scenario: worker JS 零状态

- **WHEN** 检查 worker JS 源码
- **THEN** 无任何句柄 `Map`、`nextHandle` 计数器与逐动词命令表；注册、查表与
  分发全在 core，wasm `Frequency` 实例不浮出 JS（生成物 `free()` 无 JS 调用点）

#### Scenario: dropFrequency 消失

- **WHEN** grep worker 命令面与壳
- **THEN** 无 `dropFrequency`，释放消息唯一形态 `{handle, method:"drop"}`

### Requirement: 共享所有权不误删

同一 handle 被多个主线程引用（如两个 `Touchstone` 壳同持一个 `Frequency`）时，
worker 对象 MUST 在**全部**引用消失前保持存活。释放部分引用 MUST NOT 触发释放；
仅当最后一个引用被 GC 时 MUST 触发 worker 释放。

#### Scenario: 释放其一计数不减

- **WHEN** 同 handle 两个引用，释放其一并强制 GC
- **THEN** `live_count()` 不减（对象仍活）

#### Scenario: 释放其二归零

- **WHEN** 再释放最后一个引用并强制 GC
- **THEN** `live_count()` 归零

### Requirement: 显式 `drop()` 确定性即时（全端）

`drop()` 在全端同名（铁律十二），但**见证不同**：`Frequency` 以 `live_count()`
归零为确定性即时见证（下述）；`Touchstone` 的 `drop()` 只封存实例（访问报错），
物理回收随最后持有者散场，见下方「`Touchstone` `drop()` 实例封存即时」。

`Frequency` 在 Python/node/浏览器三端 MUST 提供 `drop()` 作确定性手动释放口：
调用后 MUST **不**依赖 GC 即时触发 Rust `Drop`，以 `live_count()` 归零为见证。
`drop()` MUST 幂等（重复调用无害），释放后访问数据 MUST 报错（Python
`ValueError` / JS `Error`，消息含对象标识），不调用则由自动回收（Python 引用计数
/ JS GC finalizer / Rust RAII）兜底——手动与自动两种用法共存且结果一致。`drop()`
是铁律十（skrf 兼容）的**已立案偏离**：其「更强收获」为 GC 时机非确定性是 JS
平台特有约束、而跨端统一动词的可记忆性收益覆盖 Python 端冗余（幂等 + 释放后报错
已封死误用 footgun）。Rust 侧 `Drop`（RAII）与同名固有方法 `drop()` 共用一份清理
实现（固有方法优先解析，`Drop::drop` 一行委托）。本 requirement 的见证计数器
`live_count()` 为 `Frequency` 专属；`Touchstone` 的 `drop()` 语义见下方
「`Touchstone` `drop()` 实例封存即时」requirement。

#### Scenario: drop 不依赖 GC 即时回收

- **WHEN** 任一端对 `Frequency` 调 `drop()` 后**不**强制 GC
- **THEN** `live_count()` 立即减（确定性，不等 GC）

#### Scenario: Python 手动 drop 与自动回收共存

- **WHEN** Python 端对 `Frequency` 调 `drop()` 后再访问 `f`/`npoints`
- **THEN** 抛 `ValueError`；不调 `drop()` 时引用计数归零自动回收，`live_count()`
  同样归零

#### Scenario: 重复 drop 幂等

- **WHEN** 对同一 `Frequency` 二次调 `drop()`
- **THEN** 不报错、`live_count()` 不二次递减

## ADDED Requirements

### Requirement: `Touchstone` `drop()` 实例封存即时，物理回收随最后持有者散场

`Touchstone` 在 Python/node/浏览器三端 MUST 提供 `drop()`：调用后实例立即**封存**
——后续访问数据（`s`/`z`/`data` 等）MUST 报错（Python `ValueError` / JS `Error`，
消息含对象标识），`drop()` MUST 幂等。与 `Frequency` 不同，`Touchstone` 的物理
内存 MUST NOT 依赖 `drop()` 即时归还：`drop()` 仅置封存标志、不清 buffer（pyclass
owns 主数据，已借出的零拷贝视图经 base 引用保活，无悬垂）；物理回收随最后一个
持有者散场（Python 引用计数 / node napi finalizer / 浏览器 worker 表 `remove` 触发
Rust `Drop`）。`Touchstone` MUST NOT 新增活对象计数器——其封存见证是「访问报错」，
非计数归零。

#### Scenario: Touchstone drop 后访问报错

- **WHEN** 任一端对 `Touchstone` 调 `drop()` 后读 `s`（或 `z`/`data`）
- **THEN** 抛错（Python `ValueError` / JS `Error`，消息含对象标识），不返回数据

#### Scenario: 已借出视图在 drop 后仍有效不悬垂

- **WHEN** Python 端先取 `ts.s` 零拷贝视图，再对 `ts` 调 `drop()`，然后读该视图
- **THEN** 视图仍可读（base 引用保活 buffer，无悬垂）；仅经 `ts` 的再次访问报错

#### Scenario: Touchstone 重复 drop 幂等

- **WHEN** 对同一 `Touchstone` 二次调 `drop()`
- **THEN** 不报错
