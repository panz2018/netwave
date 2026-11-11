# Spec Delta

## ADDED Requirements

### Requirement: 字节边界动词与文本动词对称

数据进出 core 的字节边界 MUST 由 `from_bytes`（参数
`bytes, nports?, path?, encoding?`）与 `to_bytes`（参数
`parameter, format, encoding?`）承担，参数形状与字符串边界
`from_text`/`to_text` 对称（`encoding` 用全称，不用缩写）。
`from_bytes` 解码后 MUST 复用 `from_text` 的解析路径、`to_bytes` MUST 复用
`to_text` 的渲染后编码——同一实现两入口，非两套代码。三端绑定同名透传
（机械 camelCase：`fromBytes`/`toBytes`）。判定为字节级/字符串逐字精确，
无浮点容差（编解码为精确映射，无 SIMD 数值路径，原生三端 bit 级断言，
`core_tol` 不适用）。

#### Scenario: 字节往返 bit 级闭环

- **WHEN** `from_bytes(b)` 成功后 `to_bytes(parameter, format, encoding)`
  以与来源相同编码写出，再喂 `from_bytes`
- **THEN** 两次对象 `s` 数据与 `comments` 逐 bit/逐字相同（显式同编码
  往返字节级闭环；缺省写 UTF-8 读 latin-1 的不对称按编码契约 Requirement
  的写缺省 Scenario 判）

#### Scenario: 乱码字节报错不 panic

- **WHEN** 喂含 `0x00`、UTF-16 残留（ASCII 间夹 `0x00`）、半截多字节序列
  的乱码字节流调 `from_bytes`
- **THEN** 报 `TouchstoneError`（语法/stride/编码类，消息点名 offending
  输入），任何输入 MUST NOT panic

#### Scenario: 缺省猜测与显式指定同果

- **WHEN** 同一 latin-1 字节流分别经缺省 `encoding`（猜测命中 latin-1）
  与显式 `encoding="ISO-8859-1"` 调 `from_bytes`
- **THEN** 两对象 `s`/`comments`/`version`/`z0` 逐 bit/逐字相同（同一
  解码实现的两条入口，非两套代码）

### Requirement: 编码白名单与读猜写定

`encoding` 参数白名单 MUST 为 `{UTF-8, ISO-8859-1}`，名单外（UTF-16、
ASCII、乱码名）报错并携带原词；匹配做归一化并接受常见别名（见 Scenario，
为 Python `codecs.lookup` 全量别名集的**有意子集**）。读缺省 = 猜：UTF-8
严格语法校验失败退 ISO-8859-1；写缺省 = 定 UTF-8。显式 `encoding` = 指令：
解码失败报错、MUST NOT 静默换编码兜底。latin-1 编解码 MUST 在 core 完成
（JS `TextEncoder` 只会编 UTF-8）。独立真值：latin-1 映射以 ISO-8859-1
标准（U+0000–U+00FF 一一映射）为准，UTF-8 语法以 Unicode 标准 UTF-8
编码表为准。与 scikit-rf 的两条**有意偏差**随本 Requirement 记录（见末两
Scenario，出处 `skrf/io/touchstone.py` L261–267、`skrf/network.py` L2631）。

#### Scenario: latin-1 字节经缺省猜测链解析成功

- **WHEN** 以缺省 `encoding` 调 `from_bytes` 喂含 µ（字节 `0xB5`）注释的
  latin-1 编码合法 Touchstone 字节流
- **THEN** UTF-8 校验失败退 ISO-8859-1，解析成功，`comments` 含字符 µ
  （与 UTF-8 文件解出的同一个 `char`）

#### Scenario: BOM 在 UTF-8 路径剥离

- **WHEN** 喂开头带 `EF BB BF` 的 UTF-8 字节流，分别经缺省 `encoding` 与
  显式 `encoding="UTF-8"` 调 `from_bytes`
- **THEN** 两次均剥 BOM、选项行识别成功、解析结果相同；显式
  `encoding="ISO-8859-1"` 时 BOM 不剥，首行变为 `ï»¿# …` 不再是合法选项行，
  报语法类错误（`ï»¿` 不被吞掉——剥离只属 UTF-8 路径）

#### Scenario: 显式 UTF-8 解码失败不兜底

- **WHEN** 喂 latin-1 字节（含 `0xB5`）且显式 `encoding="UTF-8"`
- **THEN** 报编码解码错误（消息点名 UTF-8 解码失败），MUST NOT 退
  latin-1 静默成功

#### Scenario: 白名单外编码名报错

- **WHEN** `encoding` 传 `"UTF-16"`、`"ASCII"` 或乱码名
- **THEN** 报编码不支持错误，消息携带原词
- **AND** 归一化（大小写不敏感、去连字符/下划线/空格）后 `"utf8"`、
  `"latin1"`、`"Latin-1"`、`"ISO_8859_1"` 正常受理；归一化后仍不在名单的
  冷门别名（`"latin"`、`"L1"`、`"cp819"`）同样报错——有意不追求
  Python `codecs.lookup` 的别名全量

#### Scenario: 写缺省 UTF-8 与 latin-1 越界报错

- **WHEN** 对 `comments` 含 µ 的对象调 `to_bytes(S, RI)`（缺省编码）
- **THEN** 返回字节流中 µ 为 `0xC2 0xB5`（UTF-8）
- **WHEN** 同对象调 `to_bytes(S, RI, "ISO-8859-1")`
- **THEN** µ 编为单字节 `0xB5`
- **WHEN** `comments` 含超出 U+00FF 的字符（如 ℃）且 `encoding` 为
  `"ISO-8859-1"`
- **THEN** 报错并携带该字符，不产出截断/替换字节的字节流

#### Scenario: 写缺省与 skrf 有意不同

- **WHEN** 读 latin-1 文件后以缺省编码 `to_bytes` 写回
- **THEN** µ 字节从 `0xB5` 变 `0xC2 0xB5`（netwave 写缺省 UTF-8；skrf
  `write_touchstone` 默认 ISO-8859-1）——字节级不闭环属预期，要闭环
  显式传 `encoding`

#### Scenario: 显式 UTF-8 剥 BOM 与 skrf 有意不同

- **WHEN** 对照 skrf：显式 `encoding="utf-8"` 喂带 BOM 文件，skrf 不剥
  BOM（仅猜测路径 `utf-8-sig` 剥）致选项行识别失败
- **THEN** netwave 显式 UTF-8 同样剥 BOM、解析成功——有意偏离，行为更一致
