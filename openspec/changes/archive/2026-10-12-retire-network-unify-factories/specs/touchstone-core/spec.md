# Spec Delta

## MODIFIED Requirements

### Requirement: 解析覆盖 1.0/1.1 且 z0 恒实数

解析器 MUST 支持 Touchstone 1.0 与 1.1：`#` 选项行 `R` 标量（1.0）或每端口
实数（1.1）归一成每端口 f64 数组存 `z0`（唯一权威，不存原始 R）。规范禁止
复数参考阻抗（v1.1 R 为 real positive numbers；v2.x 明文 complex not
supported），z0 MUST NOT 接受复数。`z0` 入参形状 MUST 恰为标量或长度
`1`/`nports` 的实数数组，其余长度 MUST 报错。version 来源分入口：解析入口
从文件记录——按 `#` 行 `R` 的**形态**判定（标量 token→`"1.0"`、每端口
token→`"1.1"`，即使数值全同仍为 `"1.1"`）；`fromData` 工厂才由 z0 **数值**
推导（全端口同值→`"1.0"`，存在不同值→`"1.1"`）；公开面 version 为字符串。参数域 S/Z/Y/G/H
大小写不敏感读入（`to_ascii_uppercase` 归一），写出/enum/错误消息一律
标准大写。G/H 域仅 2 端口，违者报错。频点边界 MUST 纯由 nports 决定：
数字 token 流按 stride = `1 + 2×nports²` 消费，总数不整除 MUST 报
`TouchstoneError`（行只是排版，频点数 = token 总数 ÷ stride，不看行数）。
噪声参数不识别不跳过：噪声行混入必破坏 stride 整除性 → 自然报错
（与 SignalIntegrity/旧库同策，不做"频率回落判噪声"启发式）。
**`#` 选项行本身必填**（规范原文 "each Touchstone data file shall contain
an option line"）：整行缺失 MUST 报错，MUST NOT 静默套全默认；**行内**
缺个别关键词才按规范缺省补齐（GHz / S / **MA** / R 50——format 缺省是
MA 不是 RI，规范原文 "The default value is MA"）。

#### Scenario: 缺 # 选项行报错

- **WHEN** 解析无任何 `#` 行的文本
- **THEN** 报 `TouchstoneError`（消息点名缺失的 option line），不静默按
  GHz/S/RI/50 入库

#### Scenario: 行内缺关键词按规范缺省补齐

- **WHEN** 解析 `#`（空选项行）开头的文本
- **THEN** 按 GHz / S / MA / R 50 解析成功（数据对 MA 反变换验证）

#### Scenario: v1.1 每端口 z0 解析

- **WHEN** 解析 `# GHZ S MA R 50 45 50 50` 的 4 端口文件
- **THEN** `z0` = `[50.0, 45.0, 50.0, 50.0]`，`version` = `"1.1"`

#### Scenario: z0 长度非法报错

- **WHEN** `fromData` 工厂收到长度既非 1 也非 `nports` 的 z0 数组
- **THEN** 报错（三端映射 PyErr/napi Error/throw），构造失败

#### Scenario: 噪声数据报错

- **WHEN** 解析 2 端口文件且网络数据段后跟噪声行（每行 5 项）
- **THEN** token 总数不满足 stride = 9 的整除性，报 `TouchstoneError`
  （消息含实际 token 数与 stride 期望），不静默吞数据

### Requirement: 写出接口——文本与落盘两动词、扩展名 parameter+nports 单源

`writeTouchstone(parameter, format)` MUST 返回 Touchstone 文本（全平铺必填、
无 opts 包、无 `version` 选项——写出直接用存储的 version 字段：解析入口
从文件记录，`fromData` 工厂构造时由 z0 推导，不在写出时重推；无 `rRef`——
z0 唯一权威），
数字格式化 MUST shortest-roundtrip（写出→读回逐 bit 一致，测试规划既定）。
2 端口写出 MUST 按 v1.x legacy 列序（`N11, N21, N12, N22`）在 I/O 边界
换回（见「2 端口列序」需求），内部 row-major 不外泄。
`writeFile(path, parameter, format)` 实现分层：原生端（Rust/Python/node）
core 内 std::fs 落盘（node async / Python 同步放 GIL / Rust 同步）；
浏览器 wasm core MUST NOT 导出 `writeFile`，该动词只存在于 TS 壳（async，
worker 渲染 + 克隆回传 + Blob 下载）。文件名规则 MUST 由 core 私有
`write_path(path?, parameter)` 单源拼出，扩展名恒 = `.{P}Np`（P = 真实写出的
parameter（写出动词实参，扩展名与文件内容同域）、
N = 真实 nports，双双由对象说了算；四形态：空→`name`+`.{P}Np`；
目录→目录+`name`+`.{P}Np`；目录+名→补 `.{P}Np`；带扩展名→按文法剥旧
扩展名重拼正确扩展名）——扩展名的域字母与 n 写错在机制上不可能。
原生端目录歧义以 `is_dir()` 实测判定（末段是已存在目录→拼默认名）。
`path` 原生端必填、浏览器端可选。

#### Scenario: 扩展名自动纠正

- **WHEN** 对 2 端口对象调用 `writeFile("/tmp/x.s3p", 'S', 'RI')`
- **THEN** 实际落盘名为 `x.s2p`（旧扩展名剥除、真实 nports 重拼）

#### Scenario: 写出往返一致

- **WHEN** `writeTouchstone(p, f)` 输出文本再经 `fromText` 读回
- **THEN** `f = RI` 时 `s` 逐 bit 相等（shortest-roundtrip 十进制保证）；
  `f = MA/DB` 时 `s` 在 manifest `core_tol` 容差内相等（极坐标↔直角为
  超越函数换算，逐 bit 物理不可能，容差即标准）；`z0`/`parameter`/
  `version` 元数据恒一致
  （同机逐 bit；跨实现比较引用 manifest `core_tol`）

#### Scenario: 浏览器 writeFile 经 worker 且文本在 core

- **WHEN** 浏览器壳调用 `writeFile(path?, parameter, format)`
- **THEN** 主线程零 wasm 执行（铁律八）：worker 消息路由 core 渲染文本 +
  `write_path` 定名，响应 `{text, filename}` 结构化克隆回主线程（浏览器无目录，
  filename 即下载文件名），壳仅做
  Blob + `URL.createObjectURL` + `<a download>` 平台胶

## REMOVED Requirements

### Requirement: Touchstone 三端类形态与构造即解析

**Reason**: 纯数据构造器 `new Touchstone(...)` 退役、数据入口改 `fromData`/
`from_data` 工厂（铁律十五），原 scenario 名「三工厂构造即完成」已不反映四工厂
事实；改名 scenario 无法在 MODIFIED 下存活，故以 REMOVED+ADDED 整体替换。

**Migration**: `new Touchstone(frequency, data, z0, parameter)` →
`Touchstone.from_data(...)`（Rust/Python）/ `Touchstone.fromData(...)`（JS）；
`fromText`/`fromFile`/`fromUrl` 用法不变。新契约见下方「Touchstone 三端类形态
与工厂构造即解析」。

## ADDED Requirements

### Requirement: Touchstone 三端类形态与工厂构造即解析

`Touchstone` MUST 作为主类从三端包入口导出（Python `netwave.Touchstone`、
node/浏览器壳 re-export），是"持有解析结果的状态类"（api-contract 修订条款）。
四工厂 `fromText(text, nports?, path?)` / `fromFile(path)` / `fromUrl(url)` /
`fromData(frequency, data, z0, parameter)`（Python/Rust `from_data`，可选 name、
comments）MUST 构造即解析/校验完成，MUST NOT 存在二段式 `load_file` /
`read_touchstone` 动词，MUST NOT 存在裸构造器 `new Touchstone(...)`（数据入口
唯一为 `fromData`/`from_data` 工厂，见 project-governance 铁律十五）。
`parameter`（S/Z/Y/G/H）在 `fromData` 工厂与写出接口 MUST 必填无默认（默认 S
会把 Z 数据静默当 S 存）。`frequency` MUST 收 `Frequency` 对象（频率轴唯一
权威）。公开属性面：`s`/`z`/`y`/`g`/`h`/`f`/`z0`/`nports`/`name`/`comments`/
`version`/`parameter` + 访问器 `data(parameter, format)`（双参必填，无默认——调
`data()` 就必须说清要什么域什么格式，零拷贝默认走 `s` 属性）；MUST NOT 存在
`format` 属性、`filename` 属性（文件来源名统一用 `name`，写出路径是私有方法
`write_path`）、`port_names`、`validate()`、`resistance`/`reference` 冗余存储。

#### Scenario: 四工厂构造即完成

- **WHEN** 三端各自经 `fromText`/`fromFile`/`fromUrl`/`fromData` 构造并立即读 `s`
- **THEN** 无需任何后续 load/read 调用即得完整数据；三端动词名一致
  （TS 机械 camelCase，Python snake_case）

#### Scenario: parameter 缺失即报错

- **WHEN** `fromData` 工厂调用未传 `parameter`
- **THEN** 三端同一位置报参数缺失错误，不发生默认 S 的静默存储
