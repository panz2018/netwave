# Proposal

## Why

`api-contract` 把"频率轴主数据恒为 f64 Hz"钉为铁律，但明确把 `unit` 的存放位置、
`f_scaled` 形态、`FrequencyUnit` 的词汇与倍率定义推给阶段 1/2 design.md（见
[api-contract 频率轴主数据恒为 f64 Hz](../../specs/api-contract/spec.md)）。这块悬空
会让绑定层各自长出单位表，撕开漂移面。本 change 定案 `FrequencyUnit` 的单一真相源
形态：词汇、倍率、跨端暴露与错误契约，杜绝 py/ts 手抄。

## What Changes

- core 新增 `FrequencyUnit` enum（`Hz`/`kHz`/`MHz`/`GHz`/`THz`），词汇唯一源头，
  strum derive 生成 `as_ref`/`iter`/`FromStr`。
- 倍率以穷尽 `match` 落地（Rust 内部查表，键=变体、值=倍率），被 `Frequency.f_scaled`
  消费，不作为公开函数、不在 py/ts 出现。
- THz 入表（当前支持）；Touchstone 文件头不支持 THz 属阶段 2 解析层约束，与本词汇定义无关。
- py/ts 绑定零手抄：pyo3 `add_class` 一行 + napi/wasm-bindgen feature 门控 + re-export
  一行；成员与字符串靠运行时反射与构建期生成的 `.d.ts`/`.pyi` 自我发现。
- core 提供 `frequency_units()` 透传（`iter().map(as_ref)`，零词汇内容），三端同名
  导出（JS camelCase `frequencyUnits()`），作为 py/ts 列出全部单位的唯一自我发现通道。
- 错误契约：core `Error::UnknownFrequencyUnit` → Python `ValueError` / Node+浏览器
  `TypeError`（各端内置异常类，不自定义异常层级；映射随首个字符串入参入口落地）。
- 落盘一律规范字符串（`as_ref`），数字 enum 只活在单次页面 `postMessage`，永不持久化。

## Capabilities

### New Capabilities

- `frequency-unit`: 频率单位词汇表（enum 单源）、倍率权威（穷尽 match）、跨端零手抄暴露
  形态、未知单位错误契约、传输/存储表示分离。

### Modified Capabilities

- `api-contract`: 将"频率轴主数据恒为 f64 Hz"里悬空的 `unit` 存放位置与 `FrequencyUnit`
  形态收敛为已定案（引用 `frequency-unit` 为词汇权威），删除"本 spec 不提前焊死"中已被
  本 change 定案的部分。

## Impact

- 代码：`core/src/frequency.rs`（新增 enum + 倍率 match + `Error`）、`core/Cargo.toml`
  （新增 strum 依赖 + `python`/`node`/`browser` feature）、`python/src/lib.rs`
  （`add_class`）、`typescript` 两份 glue re-export。
- 依赖：新增 `strum`（+ 配套 `strum_macros`，同 minor），按仓库策略钉最新。
- 文档：`Plan/总体计划.md` 待决清单对应条目销账；`api-contract` spec 收敛。
- 绑定产物：`.pyi`（pyo3-stub-gen）、node/wasm `.d.ts`（构建期自动生成）。

## Non-goals

- 不实现 `Frequency` 类本体（阶段 1）——本 change 只定 `FrequencyUnit` 词汇与契约形态。
- 不做 `f_scaled` 的 property/方法命名与 `Frequency` 独立类 vs `Network` 属性归属
  （阶段 1/2 design.md）。
- 不做 Touchstone `#` 行单位白名单拒绝（阶段 2 解析层）。
- 不自定义跨端异常类层级（用各端内置异常）。
- 不引入 py/ts 侧任何单位表、倍率或校验逻辑。
