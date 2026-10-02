# Spec Delta

## Purpose

定义频率单位的词汇表、倍率权威、跨端零手抄暴露形态与未知单位错误契约，使
`Hz`/`kHz`/`MHz`/`GHz`/`THz` 在 core 单点定义、py/ts 仅靠反射与生成物自我发现，
杜绝绑定层手抄单位表导致的漂移。

## ADDED Requirements

### Requirement: 频率单位词汇单源

频率单位词汇 MUST 在 core 以单一 enum 定义，变体恰为 `Hz`/`kHz`/`MHz`/`GHz`/`THz`
（SI 词头倍率 $10^0/10^3/10^6/10^9/10^{12}$，规范拼写即变体名）。该 enum MUST 是
全仓唯一词汇源头：任何 py/ts 源码、`.pyi`、`.d.ts` MUST NOT 出现手抄的单位字符串列表。
THz MUST 入表；Touchstone 文件头是否接受 `THZ` 属解析层约束，与本词汇定义无关。

#### Scenario: 词汇集合恰为五单位

- **WHEN** 反射 core 导出的 `FrequencyUnit` 成员集合
- **THEN** 成员名集合恰为 `{Hz, kHz, MHz, GHz, THz}`，无多无少

#### Scenario: 绑定层无手抄词汇

- **WHEN** grep `python/`、`typescript/src/` 源码（排除构建产物 `.pyi`/`.d.ts`）
- **THEN** 无任何单位字符串字面量列表（`"kHz"` 等仅出现在 core 与构建期生成物）

### Requirement: 倍率权威与穷尽性

每个单位的倍率（换算到 Hz 的乘数）MUST 在 core 以穷尽匹配定义，值恰为
$10^{0}/10^{3}/10^{6}/10^{9}/10^{12}$（SI 词头定义，精确无近似）。新增 enum 变体
而未配倍率 MUST 导致编译失败（穷尽匹配强制）。倍率 MUST NOT 作为公开函数暴露给
py/ts，仅供 `Frequency.f_scaled` 内部消费。跨端倍率一致性容差引用 manifest key
`core_tol`（真值来源：SI 词头闭式定义，非 skrf golden）。

#### Scenario: 倍率值精确

- **WHEN** 查询各变体倍率
- **THEN** `Hz`→1、`kHz`→1e3、`MHz`→1e6、`GHz`→1e9、`THz`→1e12，逐值精确

#### Scenario: 加变体漏配倍率编译失败

- **WHEN** 向 enum 新增变体 `PHz` 而不补其倍率分支
- **THEN** core 编译报错（非穷尽匹配），CI 无法通过

### Requirement: 跨端零手抄暴露

`FrequencyUnit` MUST 经绑定宏从 core enum 自我发现地暴露到三端：Python 由 pyo3
反射成员、Node 与浏览器由构建期生成的 `.d.ts` 提供成员名。三端 MUST NOT 手写成员
列表、倍率或校验逻辑。py/ts 用户以 `FrequencyUnit.kHz` 形态访问，IDE MUST 能对
不存在的成员（如 `FrequencyUnit.Hzz`）报类型错误。

#### Scenario: 三端成员集合相等

- **WHEN** 分别取 Python `vars(FrequencyUnit)` 键集合、node 与 wasm `.d.ts` 成员集合
- **THEN** 三者与 core enum 变体集合相等；任一构建产物过期即 CI 红

#### Scenario: 非法成员 IDE 报错

- **WHEN** 在 py/ts 写 `FrequencyUnit.Hzz`
- **THEN** 类型检查器（pyright / tsc）报"成员不存在"错误

### Requirement: 未知单位错误契约

core 解析未知单位字符串（`FromStr` 失败）MUST 返回 `Error::UnknownFrequencyUnit`，
错误消息含非法输入原文。该错误映射到各端 MUST 用内置异常类：Python `ValueError`、
Node `TypeError`、浏览器 `TypeError`。MUST NOT 自定义跨端异常类层级。

#### Scenario: 解析非法单位报错并含原文

- **WHEN** 以 `"Hzz"` 触发单位解析
- **THEN** 抛错且消息含 `"Hzz"`；Python 端为 `ValueError`、JS 端为 `TypeError`

### Requirement: 传输与存储表示分离

`FrequencyUnit` 在跨边界传输（worker `postMessage` 结构化克隆）时 MUST 以数字 enum
表示，数字 MUST NOT 持久化到任何文件/缓存/JSON。落盘与序列化 MUST 使用规范字符串
（`as_ref()` 输出，如 `"GHz"`），读回 MUST 经 `FromStr` 校验。大小写解析 MUST
case-insensitive（`"ghz"`/`"GHZ"`/`"GHz"` 均解析为 `GHz`），规范拼写唯一。

#### Scenario: 落盘用字符串读回校验

- **WHEN** 单位随元数据序列化到磁盘再读回
- **THEN** 磁盘存 `"GHz"` 字符串；读回经 `FromStr` 还原为 `GHz`，非法值报错

#### Scenario: 大小写不敏感解析

- **WHEN** 以 `"ghz"` 或 `"GHZ"` 解析
- **THEN** 均成功还原为规范变体 `GHz`
