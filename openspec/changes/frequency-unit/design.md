# Design

## Context

`api-contract` 钉死"频率轴主数据恒为 f64 Hz"，把 `unit` 存放位置与 `FrequencyUnit`
形态推给本 change（见 proposal.md - Why）。约束来自 governance 铁律：绑定层不自存状态、
不自算数值（三层契约）；worker 消息面 `{handle, method, args}` 决定跨边界单位是裸
传输值；可门禁化的规则落进 `pnpm check`。当前 core 仅有 `fill_pattern` 脚手架，无
`Frequency`/`FrequencyUnit`。

## Goals / Non-Goals

- Goals：`FrequencyUnit` 词汇与倍率在 core 单点定义；py/ts 零手抄自我发现；未知单位
  错误契约固定；传输/存储表示分离。
- Non-Goals：`Frequency` 类本体、`f_scaled` 命名、Touchstone `#` 行白名单——见
  proposal.md - Non-goals，本 change 不触碰。

## Decisions

### 词汇源头用 enum + strum，不用字符串数组或字典

`enum FrequencyUnit { Hz, kHz, MHz, GHz, THz }` 加 `#[derive(AsRefStr, EnumIter, EnumString)]`
加 `#[strum(ascii_case_insensitive)]`。变体名即规范拼写，字符串"Hz"全仓只出现一次
（enum 定义处）。`iter()`/`as_ref()`/`FromStr` 由 strum 生成，替代手写
`ALL`/`as_str`/`FromStr`。

- 备选：`const [&str; 5]` 数组——词汇与 enum 成两份，漂移面，否。
- 备选：`HashMap`/`phf` 字典——Rust `const` 造不了 `HashMap`，引 `phf` 不值，否。

### 倍率用穷尽 match，不用公开函数

`const fn multiplier(self) -> f64 { match self { Hz=>1.0, kHz=>1e3, ... } }`。match
是倍率表的 Rust 形态（键=变体、值=倍率），穷尽性保证加变体漏配倍率编译失败。strum
只能生成字符串/遍历，生成不了数值，故倍率必须手写 match。倍率不公开给 py/ts，仅
`Frequency.f_scaled` 内部消费（YAGNI：无"裸问倍率"场景）。

### TS 用数字 enum，不用 string_enum

`#[napi]`/`#[wasm_bindgen]` 默认数字 enum。理由：wasm-bindgen 不支持 string_enum，
两端若一端字符串一端数字则 worker 跨端值不对称。数字是名义类型（TS 5.0+ 禁裸 number
赋值），typing 强度不降；数字不落盘（见传输/存储分离），无中间插值错位风险。

- 备选：napi `string_enum`——JS 值 `"kHz"` 更可读，但与 wasm 端不对称，否。

### 绑定层 feature 门控，core enum 本体挂属性

core enum 用 `#[cfg_attr(feature = "python", pyclass)]` 等直接挂三端属性，glue 仅
`add_class`/re-export 一行。

- 备选：`python/src/lib.rs` 另包 `PyFrequencyUnit`——变体重抄第二遍，漂移温床，否。

### 错误用各端内置异常

core `enum Error { UnknownFrequencyUnit(String) }` + `impl From<Error> for PyErr`
（→`PyValueError`）；node `env.throw_type_error`；wasm-bindgen 对 `Result<T, E: Debug>`
自动 throw。不自定义异常层级（YAGNI，将来需精确捕获再走 OpenSpec 变更升格）。

## Risks / Trade-offs

- [strum 是新增 proc-macro 依赖] → 关默认 feature 只开 `std`；`strum` 与 `strum_macros`
  钉同 minor；按仓库策略钉最新，构建失败才回退并记 lessons-learned。
- [数字 enum 若被误落盘，中间插变体致旧数据错位] → spec 明令数字不落盘；exports 测试
  断言成员名集合（非值），落盘路径只走 `as_ref` 字符串。
- [`.pyi`/`.d.ts` 构建产物过期] → exports 测试断言三端成员集合与 core 相等，CI 红。
- [穷尽 match 与 enum 分处，改 enum 忘改 match] → 穷尽匹配编译器强制，漏即编译失败。

## Migration Plan

阶段 0 脚手架期引入：加 strum 依赖 → 写 enum + match + Error → 三端 glue 注册 →
生成 `.pyi`/`.d.ts` → exports 测试 + cross_compare 对拍。无存量数据，无回滚负担；
若 strum 与工具链冲突，回退到手写 `as_ref`/`iter`（保留 enum 单源不变）。

## Open Questions

- `Frequency` 类持 `unit` 的字段形态（`FrequencyUnit` vs `Option<FrequencyUnit>`）——
  随 `Frequency` 本体在阶段 1 design.md 定，不影响本 change 的 enum 契约。
