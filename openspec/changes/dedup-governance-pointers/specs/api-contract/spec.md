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

### Requirement: fromX 构造入口名单

本 Requirement 是 `fromX` 工厂**名单**的唯一正文（governance 铁律十五只留
契约句，名单在此）：`fromData`/`from_data`、`fromText`/`from_text`、
`fromFile`/`from_file`、`fromUrl`/`from_url`、`fromF`/`from_f`、
`fromWavelength`/`from_wavelength`。名单内入口 MUST 四端同名（机械映射
豁免见 governance 铁律十）。

#### Scenario: 新构造入口先登记名单

- **WHEN** 提议新增一个 `fromX` 构造入口
- **THEN** 同一 change 内本节名单已含该名，否则 code-review Standards 轴判不完成

#### Scenario: 名单与实现同步

- **WHEN** 某 `fromX` 入口改名或废除
- **THEN** 本节名单在同一 PR 内同步更新，无已消失入口残留、无未实现入口空挂
