# Spec Delta

## MODIFIED Requirements

### Requirement: 未知单位错误契约

core 解析入口 MUST 是手写 `impl FromStr`（strum `EnumString` 生成的 `ParseError`
不含输入原文，故弃用），失败 MUST 返回 `Error::UnknownFrequencyUnit`，错误消息
含非法输入原文。该错误映射到各端 MUST 用内置异常类：Python `ValueError`、
Node `TypeError`、浏览器 `TypeError`；MUST NOT 自定义跨端异常类层级。本 change 无
字符串入参公开入口，跨端映射属**契约冻结**（本 spec 定死映射关系，review 据此
判定，不得偏离），实现随首个字符串入参公开入口落地时执行；本 change 在 core 层
验证错误含原文。

#### Scenario: 解析非法单位报错并含原文

- **WHEN** `"Hzz".parse::<FrequencyUnit>()` 失败
- **THEN** 返回 `Error::UnknownFrequencyUnit` 且错误消息含 `"Hzz"`
