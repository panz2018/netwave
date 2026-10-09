# Proposal

## Why

`Frequency` 目前只有内存骨架（`from_f`/`npoints`/`drop` + 见证计数器），功能面
（`f`/`f_scaled`/`w`/`wavelength`/`unit`/`copy`/显示串）缺失，类未从包入口导出
（半公开违反铁律九/十）。api-contract 的「频率轴主数据恒为 f64 Hz」一条把
`f_scaled` 命名形态与 `Frequency` 独立类 vs `Network` 属性**显式推迟**到「首个
字符串入参入口立项时的 design.md 定案」——本 change 即该入口，必须落地定案。

## What Changes

- 新增 `Frequency` 完整功能面：`from_f`（unit 必填，enum|str、数组|标量双收）、
  `from_wavelength`（n 必填）、`f`（Hz 主数据，**拷贝**返回）、`f_scaled`、`w`、
  `npoints`/`__len__`、`unit` getter（返回 enum）/setter（enum|str，大小写不敏感，
  非法报错含原文）、`wavelength(WavelengthUnit, n)`、`copy`、`Display`/`Debug`
  统一显示串。
- 新增 `WavelengthUnit` enum（`m/cm/mm/um/nm`，穷尽 `multiplier`、`FromStr`
  大小写不敏感），照 `FrequencyUnit` 反射三端零手抄。
- 新增 `core::constants::SPEED_OF_LIGHT`（SI 精确值），Python 薄再导出
  `netwave/constants.py`、TS 命名导出。
- `Frequency` 从三端包入口正式导出（结束半公开态）。
- `f` 走**拷贝**而非零拷贝共享：依据 scikit-rf `f` 为纯 getter 无 setter
  （频率轴只读、无写回需求），小数组拷贝近乎免费，且**不触碰已冻结的内存
  生命周期测试**（`drop()` 的 `Vec::new()` 一行不改）。

## Capabilities

### New Capabilities

- `frequency-class`: `Frequency` 频率轴数据模型的功能面契约——构造
  （`from_f`/`from_wavelength`）、只读访问器（`f`/`f_scaled`/`w`/`npoints`）、
  单位读写（`unit`）、波长（`wavelength` + `WavelengthUnit`）、`copy`、跨端
  显示串，及其独立类形态与 `f` 拷贝语义。

### Modified Capabilities

- `api-contract`: 「频率轴主数据恒为 f64 Hz」一条把 `f_scaled` 形态与
  `Frequency` 类形态标为「未定、待 design.md 定案」——本 change 定案（独立类、
  `f_scaled` 为 property、`f` 拷贝），该 requirement 措辞随之落定；`unit` setter
  成为 frequency-unit 错误契约预留的「首个字符串入参公开入口」。

## Impact

- 代码：`core/src/frequency.rs`（功能方法 + `WavelengthUnit` + browser `match`
  加访问器臂）、`core/src/constants.rs`（新）、`python/src/lib.rs`（pyclass 功能
  方法 + `__len__`/`__str__`/`__repr__`）、`python/netwave/constants.py`（新）、
  `typescript/native/src/lib.rs`（napi 方法 + inspect 钩子）、浏览器 TS 壳
  async 访问器、`.pyi`/`.d.mts` 重新生成。
- 门禁：`scripts/check_vocab_types.py` 纳入 `WavelengthUnit` 三端成员集合一致；
  `scripts/check_verbs.py` 的 `FREQUENCY_VERBS` 随之扩展。
- 铁律：铁律一（f64 Hz 布局）、铁律三（λ↔f 往返容差引用 manifest、精确常量逐
  bit）、铁律九（协议钩子）、铁律十（skrf 兼容，`unit` getter 返 enum 为已立案
  偏离）、铁律十一（绑定薄壳，union 搬运在 core 绑定段）、铁律十二（跨端同名）。
- 不触碰：内存生命周期机制（`drop()`/registry/napi finalizer/见证计数器）零改动。

## Non-goals

- 不做 `f` 零拷贝共享视图（走拷贝，见上）；不给频率轴任何写回入口（skrf `f`
  只读，api-contract 禁单独频率轴 setter）。
- 不做 skrf 的 linspace/geomspace 扫频构造、`df`/`dw` 梯度、`start`/`stop`/
  `center`/`step`/`span`（含 `_scaled`）、`t`/`t_ns` 时域、`round_to`/`overlap`/
  单调检查、字符串切片 `__getitem__`、算术 dunder、`multiplier` 暴露、
  `f_Hz`/`f_kHz` 具名访问器族。
- 不改内存生命周期测试与 spec（`f` 拷贝使 `drop()` 语义不变）。
- 不做脚手架自由函数退役（`fill_pattern`/`read_element` 属 Network 数据，独立
  change）。
