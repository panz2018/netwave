# frequency-class Specification

## Purpose

定义 `Frequency` 频率轴数据模型的功能面契约：构造、只读访问器、单位读写、波长
换算、拷贝与跨端显示串，及其独立类形态与 `f` 拷贝语义，使频率轴在 core 单点
定义、三端一致暴露、可实测可回归。

## Requirements

### Requirement: Frequency 独立类三端导出

`Frequency` MUST 作为独立类从三端包入口导出（Python `netwave.Frequency`、node
与浏览器壳 re-export），结束半公开态。它持有频率轴（f64 Hz 主数据）与单位元
数据，是 api-contract「有状态对象用类」在频率轴维度的落地。`Frequency` MUST
NOT 退化为 `Network` 的属性。

#### Scenario: 三端可构造独立实例

- **WHEN** 在 Python/node/浏览器分别经 `Frequency.fromF([1,2,5], "GHz")` 构造
- **THEN** 三端均返回 `Frequency` 实例，可独立于 `Network` 存在与使用

### Requirement: from_f 构造（unit 必填）

`Frequency.from_f(f, unit)` MUST 从频率数组或标量构造，`unit` MUST 必填（enum
或字符串，缺失即报错，不默认 Hz）。输入 MUST 数组与标量双收（标量视作单点）。
入库值 MUST 为 `f × multiplier(unit)` 的 f64 Hz（铁律一布局）。独立真值：SI
词头闭式倍率（精确，逐 bit，引用 frequency-unit 倍率权威，非 manifest 容差）。

#### Scenario: 标量与数组双收

- **WHEN** `from_f(2.5, "GHz")` 与 `from_f([1.0,2.0,5.0], "GHz")`
- **THEN** 分别得单点轴 `[2.5e9]` 与三点轴 `[1e9,2e9,5e9]`（逐 bit）

#### Scenario: unit 缺失报错

- **WHEN** `from_f([1,2], unit=None)`（Python）或省略 unit（TS）
- **THEN** 报错（Python `TypeError`/`ValueError`、TS `TypeError`），不默认 Hz

### Requirement: from_wavelength 构造（n 必填）

`Frequency.from_wavelength(wl, wl_unit, n)` MUST 从波长构造频率轴，`n`（相折射
率 phase index，n=c/v_p=√ε_eff）MUST 必填——介质上默认 n=1 物理必错，静默错比
报错恶劣。频率 MUST 由 `f = SPEED_OF_LIGHT / (n × λ)` 计算，λ 先经 `wl_unit`
倍率换算为米。独立真值：SI 定义 c 精确 + 闭式 λ↔f 关系。

#### Scenario: 波长构造频率

- **WHEN** `from_wavelength([60.0], WavelengthUnit.mm, n=2.2)`
- **THEN** `f ≈ 299792458/(2.2×0.060)` Hz（引用 manifest `core_tol` 相对容差）

#### Scenario: n 缺失报错

- **WHEN** `from_wavelength([60.0], WavelengthUnit.mm)` 省略 n
- **THEN** 报错，不默认 n=1

### Requirement: f 访问器为拷贝语义

`f.f` MUST 返回频率轴 f64 Hz 的**拷贝**（非零拷贝共享视图）。依据：scikit-rf
`f` 为纯 getter 无 setter（频率轴只读、无写回需求），小数组拷贝近乎免费，且
拷贝使 `drop()` 的即时释放语义不变、不触碰已冻结的内存生命周期测试。拷贝值
MUST 与 core 主数据逐 bit 相等（同机同架构，铁律三原生互比）。

#### Scenario: f 返回正确拷贝

- **WHEN** `from_f([1,2,5],"GHz").f`
- **THEN** 返回 `[1e9,2e9,5e9]`，逐 bit 等于 core 主数据

#### Scenario: 改返回数组不影响 core

- **WHEN** Python 端取 `arr = f.f` 后写 `arr[0]=0`
- **THEN** 再读 `f.f[0]` 仍为 `1e9`（拷贝隔离，频率轴只读）

### Requirement: f_scaled 与 w 派生访问器

`f.f_scaled` MUST 为只读 property，返回 `f / multiplier(unit)`（当前单位下的
频率）；`f.w` MUST 返回角频率 `ω = 2πf`（rad/s）。两者 MUST NOT 落第二份主数
据存储（api-contract 派生值不入主数据）。独立真值：闭式换算；跨平台比较引用
manifest `core_tol`，同机互比逐 bit。

#### Scenario: f_scaled 随 unit 变

- **WHEN** unit 为 GHz 时读 `f_scaled`
- **THEN** 返回 `[1.0,2.0,5.0]`（引用 manifest `core_tol`）

#### Scenario: w 等于 2πf

- **WHEN** 读 `w`
- **THEN** 每元素 `== 2π×f`（引用 manifest `core_tol`）

### Requirement: unit getter 返 enum、setter 收 enum|str

`f.unit` getter MUST 返回 `FrequencyUnit` enum（非字符串——铁律十偏离，收获=
IDE 词汇校验 + 零手抄，design.md 立案）。setter MUST 收 enum 或字符串，大小写
不敏感（`"mhz"`/`"MHz"` 等价），非法字符串 MUST 报错且消息含原文（frequency-unit
错误契约的「首个字符串入参公开入口」）。改 unit MUST 只改元数据、不动 f 主数据。

#### Scenario: setter 大小写不敏感

- **WHEN** `f.unit = "mhz"` 后读 `f.unit`
- **THEN** 得 `FrequencyUnit.MHz`，`f_scaled` 随之按 1e6 换算

#### Scenario: 非法 unit 报错含原文

- **WHEN** `f.unit = "Hzz"`
- **THEN** Python `ValueError` / TS `TypeError`，消息含 `"Hzz"`

### Requirement: wavelength 方法（f=0→inf）

`f.wavelength(wl_unit, n)` MUST 返回 `λ = SPEED_OF_LIGHT / (n × f)` 并以
`wl_unit` 表达，`n` 必填。`f=0`（DC 合法频点）MUST 返回 `inf`（skrf/numpy
语义）。独立真值：闭式 λ↔f 关系 + SI 精确 c；往返对拍引用 manifest `core_tol`。

#### Scenario: 波长往返频率

- **WHEN** `from_f([1,2,5],"GHz").wavelength(WavelengthUnit.mm, n=2.2)` 再
  `from_wavelength(结果, mm, n=2.2)`
- **THEN** 频率轴回到 `[1e9,2e9,5e9]`（引用 manifest `core_tol`）

#### Scenario: DC 波长为 inf

- **WHEN** 频率轴含 0，调 `wavelength(...)`
- **THEN** 对应元素为 `inf`，不报错、不为 NaN

### Requirement: WavelengthUnit 词汇单源

波长单位词汇 MUST 在 core 以单一 enum `WavelengthUnit` 定义，变体恰为
`m/cm/mm/um/nm`（倍率 $10^{0}/10^{-2}/10^{-3}/10^{-6}/10^{-9}$，SI 词头精确），
穷尽 `multiplier`（加变体漏配编译失败），`FromStr` 大小写不敏感。经绑定宏反射
三端零手抄（照 `FrequencyUnit` 形态）。作用域限波长 API，MUST NOT 命名
`LengthUnit`（RF 语境 length=线长歧义）。

#### Scenario: 三端成员集合相等

- **WHEN** 反射三端 `WavelengthUnit` 成员集合
- **THEN** 恰为 `{m,cm,mm,um,nm}`，与 core enum 相等；构建产物过期即 CI 红

### Requirement: copy 与跨端统一显示串

`f.copy()` MUST 返回频率轴与 unit 都相同的独立实例。`Frequency` MUST 提供跨端
统一显示串 `Frequency(start-stop unit, N pts)`（空轴 `Frequency([no freqs])`），
经铁律九协议钩子触发：Rust `Display`/`Debug`、Python `__str__`/`__repr__`、
node `toString`+inspect、浏览器 `async toString()`。三端字符串内容逐字符相等。

#### Scenario: 显示串逐字符一致

- **WHEN** `from_f([1,2,5],"GHz")` 在三端打印
- **THEN** 均为 `Frequency(1.0-5.0 GHz, 3 pts)`（逐字符）

#### Scenario: 空轴显示串

- **WHEN** 空频率轴打印
- **THEN** 为 `Frequency([no freqs])`

### Requirement: SPEED_OF_LIGHT 常量三端导出

`SPEED_OF_LIGHT` MUST 在 core `pub mod constants` 定义为 SI 精确值
`299_792_458.0`（m/s），经 Python 薄再导出子模块 `netwave.constants` 与 TS 命名
导出暴露三端。该常量 MUST NOT 出现在绑定层手抄数值表（铁律十一/十二）。跨端
比较逐 bit 相等（精确常量，非 manifest 容差，LL-042）。

#### Scenario: 三端常量逐 bit 相等

- **WHEN** 读三端 `SPEED_OF_LIGHT`
- **THEN** 均为 `299792458.0`，逐 bit 相等
