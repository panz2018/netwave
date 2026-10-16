# Spec Delta

## ADDED Requirements

### Requirement: 多 # 选项行——第一个生效且完整校验，后续整行忽略

按 Touchstone File Format Specification v2.1 Option Line 节原文 "Each
Touchstone data file shall contain an option line (additional option lines
after the first one shall be ignored)"：解析器 MUST 以**第一个** `#` 行为唯一
生效选项行并完整校验；其后所有 `#` 行 MUST 整行跳过——不解析、不校验、不
合并、不覆盖（即使后续行含非法 token、非法域或复数 R 也 MUST NOT 报错）。
复数参考阻抗（如 `R (10+10j)`）出现在**生效的**选项行时 MUST 报
`TouchstoneError` 且消息点名 offending token（规范禁止复数参考阻抗：v1.1 R
为 real positive numbers）。本规则对 v1.0/v1.1 生效；v2.x 不在本 change 范围。

#### Scenario: 双选项行第一个生效

- **WHEN** 解析 `# GHZ S MA R 50` 后跟 `# MHZ S RI R 75` 的 1 端口文本
- **THEN** 按第一行解析：`z0` = `[50.0]`，数据按 MA 反变换（0.5∠-30°），
  第二行的 MHz/RI/75 MUST NOT 生效

#### Scenario: 非法第二选项行仍被忽略

- **WHEN** 解析首个选项行合法、第二选项行含非法域与复数 R
  （`# GHZ Q RI R (10+10j)`）的文本
- **THEN** 解析成功，不报错——第二行整行跳过，校验只作用于第一行

#### Scenario: 生效选项行复数 R 报错并点名 token

- **WHEN** 解析 `# GHZ S RI R (10+10j)` 开头的文本
- **THEN** 报 `TouchstoneError`，消息含原文 token `(10+10j)`

### Requirement: 排版变体解析——行尾/换行/空白/记数法/负零/大端口

解析器 MUST 在下列排版变体下解析成功且数值 bit 级正确（精确比较逐 bit `==`，
不引用容差）：CRLF 行尾；文件无尾换行；token 间异常空白（tab、连续多空格、
行首缩进）；数据 token 用科学计数法（`1e-3`、`1E+2` 等形式）；`-0.0` 读入
保留负零符号位；端口数至 32（stride = `1 + 2×32²` = 2049）端到端解析。
变体 MUST 由 unit 层内联文本覆盖，MUST NOT 为此新增 testdata 文件。

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
