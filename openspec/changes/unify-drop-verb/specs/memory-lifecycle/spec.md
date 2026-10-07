# Spec Delta

## REMOVED Requirements

### Requirement: 显式 `drop()` 确定性即时（JS-only）

**Reason**: 该 Requirement 把 `drop()` 限定为 JS 专属并明文禁止 Python/Rust 提供，
与「同一语义全端同一个名字」的治理目标相冲（手动释放与自动回收共存不构成
footgun：`drop()` 幂等、释放后访问必报错）。其全部约束由新 Requirement
「显式 `drop()` 确定性即时（全端）」覆盖。

**Migration**: 调用方无需改动（旧面本就没有 Python `drop()`）；Python 端新增
`Frequency.drop()`，node 端 `free()` 改名 `drop()`。

## ADDED Requirements

### Requirement: 显式 `drop()` 确定性即时（全端）

Python/node/浏览器三端 MUST 提供 `drop()` 作确定性手动释放口：调用后 MUST **不**
依赖 GC 即时触发 Rust `Drop`。`drop()` MUST 幂等（重复调用无害），释放后访问数据
MUST 报错（Python `ValueError` / JS `Error`，消息含对象标识），不调用则由自动回收
（Python 引用计数 / JS GC finalizer / Rust RAII）兜底——手动与自动两种用法共存且
结果一致。`drop()` 是铁律十（skrf 兼容）的**已立案偏离**：其「更强收获」为 GC
时机非确定性是 JS 平台特有约束、而跨端统一动词的可记忆性收益覆盖 Python 端
冗余（幂等 + 释放后报错已封死误用 footgun）。Rust 侧 `Drop`（RAII）与同名固有
方法 `drop()` 共用一份清理实现（固有方法优先解析，`Drop::drop` 一行委托）。

#### Scenario: drop 不依赖 GC 即时回收

- **WHEN** 任一端调 `drop()` 后**不**强制 GC
- **THEN** `live_count()` 立即减（确定性，不等 GC）

#### Scenario: Python 手动 drop 与自动回收共存

- **WHEN** Python 端对 `Frequency` 调 `drop()` 后再访问 `f`/`npoints`
- **THEN** 抛 `ValueError`；不调 `drop()` 时引用计数归零自动回收，`live_count()`
  同样归零

#### Scenario: 重复 drop 幂等

- **WHEN** 对同一对象二次调 `drop()`
- **THEN** 不报错、`live_count()` 不二次递减

## MODIFIED Requirements

### Requirement: node napi finalizer 自动回收（单 realm）

node 端 `Frequency` MUST 由 napi cleanup finalizer 在 JS 对象被 GC 时自动跑 Rust
`Drop`（单 realm，无压制）。node `Frequency` MUST NOT 进入 `hosted` Map（用户直接
持 napi 实例，无 Map 强引用 → 自带 finalizer 正常工作，与浏览器 worker 压制场景相反）。
node MUST 暴露 `drop()` 作确定性提前释放（与浏览器同名；napi 侧 MUST NOT 以
`free()` 命名——wasm-bindgen 生成物名不上浮用户可见面）。

#### Scenario: node 壳 GC 自动 Drop

- **WHEN** 丢弃 node `Frequency` 实例唯一引用并强制 GC（`--expose-gc`）
- **THEN** `live_count()` 归零（napi finalizer 触发 Rust `Drop`）

#### Scenario: node 对象不进 hosted Map

- **WHEN** 检查 node 端 `Frequency` 的持有方式
- **THEN** 不经 `hosted` Map 强引用（否则重蹈 worker 压制陷阱）

#### Scenario: node 手动释放命名统一

- **WHEN** 检查 node `Frequency` 公开面
- **THEN** 有 `drop()`、无 `free()`

### Requirement: 主线程 registry 驱动 worker 释放（浏览器双 realm）

浏览器端 `Frequency` 真数据活在常驻 worker（铁律八），主线程仅持数字 handle 壳。
主线程 MUST 自建 `FinalizationRegistry`，其 held 值 MUST 是**不反向引用 wrapper**
的数字 handle；壳被 GC 时回调 MUST 经 `postMessage {cmd:"drop", handle}` 通知
worker，worker MUST 在**单一 `resources` 表**中 `resources.get(handle)` 取出资源
（wasm `Frequency` 调其生成物 `free()` 触发 Rust `Drop`，裸字节缓冲直接删除）+
`resources.delete(handle)`。worker MUST NOT 再分 `hosted`/`frequencies` 两张表——
所有句柄资源进同一张 `resources` 表，释放动词唯一为 `drop`（句柄全局唯一，单表
查找无歧义）。worker 的 `resources` 表 MUST NOT 被删除（跨边界只传数字 handle，
worker 靠它路由消息）。

#### Scenario: 壳被 GC 触发 worker 释放

- **WHEN** 丢弃主线程壳最后一个引用并强制 GC
- **THEN** registry 回调 → worker `drop` 命令 → `resources` 取出并释放 + `delete`
  → `live_count()` 归零

#### Scenario: held 不钉活 wrapper

- **WHEN** 检查 registry 的 held 值
- **THEN** held 为数字 handle，不含对 wrapper 的强引用（否则 wrapper 永不回收）

#### Scenario: 单一资源表路由所有句柄

- **WHEN** buffer 句柄与 Frequency 句柄混在同一 `resources` 表并分别 `drop`
- **THEN** 单一 `drop` 命令按句柄正确释放对应资源，互不串扰（句柄全局唯一）
