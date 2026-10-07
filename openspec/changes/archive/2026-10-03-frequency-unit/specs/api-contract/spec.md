# Spec Delta

## ADDED Requirements

### Requirement: 跨端词汇零手抄

跨端共享的枚举词汇与常量表 MUST 在 core 定义一次，经绑定宏反射（pyo3 `add_class`、
napi/wasm-bindgen 生成 `.d.ts`）或 core 透传函数自我发现地暴露到三端。py/ts 源码
与手写声明文件 MUST NOT 手抄成员列表、字符串表或数值表；新增词汇 MUST 只改 core
一处，三端经重新构建自动一致。

#### Scenario: 加词汇只改 core

- **WHEN** 新增一个枚举变体
- **THEN** 改动仅发生在 core enum（及其穷尽数值匹配）；三端重新构建后成员集合
  自动一致，绑定壳零改动

## MODIFIED Requirements

### Requirement: 频率轴主数据恒为 f64 Hz

core 频率轴主数据 MUST 永远存 f64 Hz，单位歧义 MUST NOT 进入计算层
（解析 `# GHZ` 文件时在解析层换算为 Hz 入库）。派生换算值 MUST NOT 作为
第二份主数据存储，绑定层 MUST NOT 自存单位状态或自实现换算（三层契约
推论）。`unit` 的存放位置已定案：core 以 `FrequencyUnit` enum 作元数据
（词汇与倍率权威见 `frequency-unit` capability），绑定层不自存。`f_scaled`
的命名与暴露形态（property vs 方法）、`Frequency` 独立类 vs `Network` 属性
属设计决策，由测试基础设施 / Touchstone 核心的 design.md 定案（跟踪于总体计划待决细节清单），
本 spec 不提前焊死。

#### Scenario: 单位换算在解析时完成

- **WHEN** 解析 `# GHZ` 选项行的 Touchstone 文件
- **THEN** core 频率轴主数据为 Hz（文件值 × 1e9）

#### Scenario: 单位形态未定案不得实现

- **WHEN** 测试基础设施 / Touchstone 核心 design.md 尚未定案 `f_scaled` 形态，有人提议
  在绑定层实现单位换算或自存 unit
- **THEN** code-review Standards 轴拒绝（违反三层契约：绑定层不自存状态、
  不自算数值）
