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

`enum FrequencyUnit { Hz, kHz, MHz, GHz, THz }` 加 `#[derive(AsRefStr, EnumIter)]`。
变体名即规范拼写，字符串"Hz"全仓只出现一次（enum 定义处）。`iter()`/`as_ref()`
由 strum 生成，替代手写 `ALL`/`as_str`。

strum `EnumString` 弃用：其生成的 `ParseError` 不含输入原文，不满足错误契约。
`FromStr` 手写（`iter()`+`as_ref()` case-insensitive 匹配，失败当场绑原文进
`Error::UnknownFrequencyUnit`），匹配零词汇重复。

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

### 绑定层 feature 门控，core 本体挂属性

core enum 与 `frequency_units()` 用 `#[cfg_attr(feature = "python", pyclass)]` 等
直接挂三端属性，定义均在 `core/src/frequency.rs`（与 enum 同文件同域）；napi/
wasm-bindgen 链接期自动收集注册，绑定 crate 零代码；py 仅 `add_class`/
`add_function` 各一行。JS 名由宏自动 camelCase（`frequencyUnits()`）。

挂属性需 core 新增 optional 依赖 `pyo3`/`napi`/`wasm-bindgen`（feature 开启时才
链接）；core 的 optional pyo3 与 `python/Cargo.toml` 的 pyo3 MUST 钉同 minor
（两份 pyo3 实例是 links/类型冲突坑，配对依赖一起升铁律），三个 glue crate 的
`netwave` 依赖转发对应 feature。

- 备选：`python/src/lib.rs` 另包 `PyFrequencyUnit`——变体重抄第二遍，漂移温床，否。
- 备选：透传函数写在绑定 crate 各写一份——同一逻辑三处，否。

### `.pyi` 直接接入 pyo3-stub-gen 终态（提前于既有阈值）

既有倾向是"动词 <10 个时手写壳最省，pyo3-stub-gen 等动词 ≥10 再上"。本 change
拍板提前接入：既然 `.pyi` 零手抄已是契约（词汇单源 Requirement），手写 `.pyi` 就
是明知漂移面而为之，早晚要换不如现在换，免二次迁移。代价：stub-gen 在 abi3 下需
import 已构建扩展模块才能生成，构建顺序变为 `maturin develop` → 生成 `.pyi`；
`pyproject.toml` 的 `include` 改指向生成物。同步销账总体计划待决清单中该子项。

- 备选：手写 `.pyi` + exports 测试断言集合相等——省一个工具链，但词汇仍是两份
  （手写即手抄），与零手抄契约相抵触，否。

### 浏览器端：成员常量从 glue re-export，函数走常驻 worker

铁律八要求主线程不 init wasm、不执行 wasm。`FrequencyUnit` 经 wasm-bindgen 后在
glue JS 里是普通数字常量对象：`import` 常量不触发 wasm 实例化，从 glue 直接
re-export 不破铁律。`frequencyUnits()` 是编译进 wasm 的函数，主线程调用即执行
wasm，故 MUST 走常驻 worker 命令（同 `fillPattern` 形态：`netwave.worker.ts` cmds
表加行，壳导出 async 函数）。数字 enum 跨边界值与 worker 消息面天然一致（传输用
数字，不落盘）。

- 备选：主线程直调 glue——主线程被迫 init wasm，违反铁律八，否。
- 备选：成员也走 worker——成员是编译期常量，异步化徒增往返，否。

### 错误用各端内置异常，随入口落地

core `enum Error { UnknownFrequencyUnit(String) }` + `impl From<Error> for PyErr`
（→`PyValueError`）；node `env.throw_type_error`；wasm-bindgen 对 `Result<T, E: Debug>`
自动 throw。不自定义异常层级（YAGNI，将来需精确捕获再走 OpenSpec 变更升格）。
本 change 无字符串入参公开入口（解析在 core 内部），跨端映射属契约冻结（spec 定死
映射关系），实现随测试基础设施 / Touchstone 核心首个字符串入参入口落地，避免无人可调的死代码（铁律七）。

### 精确常量比较不引用容差

倍率 $10^{3n}$ 是精确常量（f64 精确可表示），跨端对拍逐 bit `==`；manifest
`core_tol` 只约束**计算后数值**的跨平台相对容差，两者是不同性质的比较，不得混用
（规则已登记 LL-042，后续同类需求沿用）。

## Risks / Trade-offs

- [strum 是新增 proc-macro 依赖] → 关默认 feature 只开 `std`；`strum` 与 `strum_macros`
  钉同 minor；按仓库策略钉最新，构建失败才回退并记 lessons-learned。
- [数字 enum 若被误落盘，中间插变体致旧数据错位] → spec 明令数字不落盘；exports 测试
  断言成员名集合（非值），落盘路径只走 `as_ref` 字符串。
- [`.pyi`/`.d.ts` 构建产物过期] → exports 测试断言三端成员集合与 core 相等，CI 红。
- [pyo3-stub-gen 在 abi3 下需 import 已构建扩展模块] → 构建顺序固定
  `maturin develop` → 生成 `.pyi`；失败即 CI 红，无静默旧产物（产物由生成链产生，
  不存在手抄旧副本）。
- [穷尽 match 与 enum 分处，改 enum 忘改 match] → 穷尽匹配编译器强制，漏即编译失败。

## Migration Plan

脚手架期引入：加 strum 依赖 → 写 enum + match + FromStr + Error +
`frequency_units()` → 三端 glue 注册 → 生成 `.pyi`/`.d.ts` → exports 测试 +
cross_compare 对拍。无存量数据，无回滚负担；若 strum 与工具链冲突，回退到手写
`as_ref`/`iter`（保留 enum 单源不变）。

## Open Questions

- `Frequency` 类持 `unit` 的字段形态（`FrequencyUnit` vs `Option<FrequencyUnit>`）——
  随 `Frequency` 本体在测试基础设施 design.md 定，不影响本 change 的 enum 契约。
