# frequency-unit Delta

## MODIFIED Requirements

### Requirement: 跨端零手抄暴露

`FrequencyUnit` MUST 从 core enum 自我发现地暴露到三端，三端 MUST NOT 手写成员
列表、倍率或校验逻辑：Python 由 `python/build.rs` 在构建期读 core enum 定义生成带
`#[pyclass]` 的枚举（机械提取，非手抄表）；Node 与浏览器由构建期生成的 `.d.ts`
提供成员名。py/ts 用户以 `FrequencyUnit.kHz` 形态访问，IDE MUST 能对不存在的成员
（如 `FrequencyUnit.Hzz`）报类型错误。core enum 与 python 生成 enum 是两个 Rust
类型，绑定层内部 MUST 经 core 已有的 `as_ref()`/`FromStr` 转换，该转换 MUST NOT
出现在 Python 用户可见面。浏览器端成员是 glue JS 数字常量对象，从 glue 直接
re-export（import 常量不实例化 wasm，铁律八不破）。

#### Scenario: 三端成员集合相等

- **WHEN** 分别反射 Python `netwave.FrequencyUnit`、node 与浏览器壳 re-export 的
  `FrequencyUnit` 成员集合
- **THEN** 三者成员名集合与 core enum 变体集合相等；任一构建产物过期即 CI 红

#### Scenario: 非法成员 IDE 报错

- **WHEN** 在 py/ts 写 `FrequencyUnit.Hzz`
- **THEN** 类型检查器（pyright / tsc）报"成员不存在"错误
