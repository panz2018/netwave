# touchstone-core Specification Delta

## MODIFIED Requirements

### Requirement: 排版变体解析——行尾/换行/空白/记数法/负零/大端口

解析器 MUST 在下列排版变体下解析成功且数值 bit 级正确（精确比较逐 bit `==`，
不引用容差）：CRLF 行尾；文件无尾换行；token 间异常空白（tab、连续多空格、
行首缩进）；数据 token 用科学计数法（`1e-3`、`1E+2` 等形式）；`-0.0` 读入
保留负零符号位；端口数至 32（stride = `1 + 2×32²` = 2049）端到端解析。
变体 MUST 由 unit 层内联文本覆盖，MUST NOT 为此新增 `oracle/samples/`
样本文件。

#### Scenario: CRLF 与无尾换行解析成功

- **WHEN** 解析行尾为 `\r\n` 且末行无换行符的 2 端口文本
- **THEN** 解析成功，频点与 S 数值和同内容 LF 版本逐 bit 相同

#### Scenario: 异常空白与科学计数法 token 解析

- **WHEN** 解析数据行含 tab、连续多空格、行首缩进，且数值以科学计数法书写
  （如 `1.0e+0  -3e-1`）的文本
- **THEN** 解析成功，数值与十进制等值书写逐 bit 相同

#### Scenario: 负零读入保留符号位

- **WHEN** 解析数据含 `-0.0` 的文本
- **THEN** 存储值 `to_bits()` 等于 `(-0.0f64).to_bits()`（符号位保留），
  不被归一为 `+0.0`

#### Scenario: 32 端口端到端解析

- **WHEN** 以 nports=32 解析一个频点（2049 个数字 token）的合法文本
- **THEN** 解析成功，`nports` = 32，S 缓冲长度 = 2048（交错 re/im），
  频点按选项行单位换算入 Hz 轴
