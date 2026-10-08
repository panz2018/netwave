# Spec Delta

## MODIFIED Requirements

### Requirement: 频率轴主数据恒为 f64 Hz

core 频率轴主数据 MUST 永远存 f64 Hz，单位歧义 MUST NOT 进入计算层
（解析 `# GHZ` 文件时在解析层换算为 Hz 入库）。派生换算值 MUST NOT 作为
第二份主数据存储，绑定层 MUST NOT 自存单位状态或自实现换算（三层契约
推论）。`unit` 的存放位置已定案：core 以 `FrequencyUnit` enum 作元数据
（词汇与倍率权威见 `frequency-unit` capability），绑定层不自存。形态
已定：`Frequency` 为独立类（非 `Network` 属性），`f_scaled` 为只读
property，`f` 为拷贝语义访问器（非零拷贝共享视图，依据 scikit-rf `f`
纯 getter 只读）。

#### Scenario: 单位换算在解析时完成

- **WHEN** 解析 `# GHZ` 选项行的 Touchstone 文件
- **THEN** core 频率轴主数据为 Hz（文件值 × 1e9）

#### Scenario: 单位形态未定案不得实现

- **WHEN** 有人以「形态尚未定案」为由，提议在绑定层实现单位换算或
  自存 unit
- **THEN** code-review Standards 轴拒绝：形态已由本 spec 定死，该前提
  不成立；且绑定层自存状态/自算数值违反三层契约
