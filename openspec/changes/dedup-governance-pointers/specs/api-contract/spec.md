# api-contract Specification Delta

## ADDED Requirements

### Requirement: 跨端显示串与协议保留名

每个公开类的统一显示串 `ClassName(摘要)` MUST 在四端取同一字符串内容，入口
按语言原生协议命名，MUST NOT 自造跨语言同名方法。协议保留名（`__str__`、
`__repr__`、`Display`、`Debug`、`toString`、`inspect.custom`、`__len__`）
在 netwave 内有特殊含义，MUST NOT 挪作他用。各端入口形态与浏览器限制见下方
Scenario。

#### Scenario: 四端显示串同内容

- **WHEN** 同一对象在 Rust/Python/Node/浏览器分别取显示串
- **THEN** 四端输出同一 `ClassName(摘要)` 字符串，无端专属格式差异

#### Scenario: 入口按语言原生协议

- **WHEN** 检查各端显示入口
- **THEN** Rust 为 `Display`+`Debug`（同串）、Python 为互等的 `__str__`/`__repr__`、
  Node 为 `toString()`+`inspect.custom`、浏览器为 `async toString()`；
  Python 无 `toString()`、JS 无 `__str__`

#### Scenario: 浏览器 await 惯用法与模板插值禁用

- **WHEN** 检查跨端显示惯用法与 docs
- **THEN** `await x.toString()` 在 node 与浏览器同时成立（node 同步串经
  `await` 透传）；docs 写明浏览器禁用 `${x}` 插值（Promise 经 `ToPrimitive`
  抛 TypeError），惯用法 `console.log(await f.toString())`

#### Scenario: npoints 类提供 Python 长度协议

- **WHEN** 检查暴露 `npoints` 的公开类
- **THEN** 该类提供 Python `__len__` 一行委托 `npoints`（skrf 同源；JS/Rust
  无对等义务）

#### Scenario: 保留名不挪作他用

- **WHEN** code-review Standards 轴发现某协议保留名被定义为非协议语义的成员
- **THEN** 打回：保留名只承载其协议语义

## MODIFIED Requirements

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
见 `memory-lifecycle` spec。

本 Requirement 同时是 `fromX` 工厂**名单与签名**的唯一正文（governance 铁律十五
只留契约句，名单在此）：`fromData`/`from_data`、`fromText`/`from_text`、
`fromFile`/`from_file`、`fromUrl`/`from_url`、`fromF`/`from_f`、
`fromWavelength`/`from_wavelength`。新增构造入口 MUST 先在本节登记名单，
四端同名（机械映射豁免见 governance 铁律十）。

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

#### Scenario: 新构造入口先登记名单

- **WHEN** 提议新增一个 `fromX` 构造入口
- **THEN** 同一 change 内本节名单已含该名，否则 code-review Standards 轴判不完成
