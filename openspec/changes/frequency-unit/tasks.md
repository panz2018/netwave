# Tasks

## 1. 依赖与骨架

- [ ] 1.1 在 `core/Cargo.toml` 加 `strum`（关默认 feature、开 `std`）+ 配套 `strum_macros`（同 minor），并加 `python`/`node`/`browser` feature 门控；验证：`cargo check -p netwave-core` 通过
- [ ] 1.2 建 `core/src/frequency.rs` 并在 `lib.rs` `pub mod frequency;`；验证：`cargo check` 通过

## 2. core 词汇、解析与倍率（red 先于 green）

- [ ] 2.1 先写失败测试 `core/tests/frequency_unit.rs`：断言 `FrequencyUnit::iter()` 集合恰为 `{Hz,kHz,MHz,GHz,THz}`、`as_ref()` 规范拼写、`frequency_units()` 返回同序五字符串；验证：`cargo test -p netwave-core frequency_unit` RED（编译失败即 red）
- [ ] 2.2 实现 `enum FrequencyUnit` + strum derive（`AsRefStr, EnumIter`）与 `frequency_units()` 透传使 2.1 转绿；验证：`cargo test -p netwave-core frequency_unit` GREEN
- [ ] 2.3 先写失败测试：断言 `"ghz"`/`"GHZ"`/`"GHz"` 均 `parse::<FrequencyUnit>()` 为 `GHz`、`"Hzz"` 返回 `Err` 且 `Display` 含 `"Hzz"`；验证：RED
- [ ] 2.4 定义 `enum Error { UnknownFrequencyUnit(String) }` + `Display`，手写 `impl FromStr`（`iter()`+`as_ref()` case-insensitive，失败绑原文）使 2.3 转绿；验证：`cargo test` GREEN
- [ ] 2.5 先写失败测试：断言倍率 `Hz`→1、`kHz`→1e3、`MHz`→1e6、`GHz`→1e9、`THz`→1e12 逐值精确（真值来源 SI 词头闭式定义，容差引用 manifest key `core_tol`）；验证：RED
- [ ] 2.6 实现 `const fn multiplier(self) -> f64` 穷尽 match 使 2.5 转绿；补 rustdoc（教学式：倍率即 SI 词头 $10^{3n}$、case-insensitive 依据 Touchstone `# GHZ` 现实）；验证：`cargo test` GREEN、`cargo doc` 无警告，且临时注释任一 match 分支后 `cargo check` 报非穷尽错误（反向验证穷尽性）

## 3. Python 绑定

- [ ] 3.1 先写失败测试 `python/tests/test_frequency_unit.py`：`netwave.frequency_units() == ['Hz','kHz','MHz','GHz','THz']`、`netwave.FrequencyUnit.kHz` 存在、`FrequencyUnit.Hzz` 抛 `AttributeError`；验证：`uv run pytest python/tests/test_frequency_unit.py` RED
- [ ] 3.2 core enum 加 `#[cfg_attr(feature="python", pyclass)]`、`frequency_units()` 加 `#[cfg_attr(feature="python", pyfunction)]`；`python/src/lib.rs` 加 `add_class::<FrequencyUnit>()` 与 `add_function`；验证：3.1 GREEN
- [ ] 3.3 用 pyo3-stub-gen 生成 `.pyi`（删手写 `netwave.pyi` 中手抄内容）；验证：生成的 `.pyi` 含 `FrequencyUnit` 五成员与 `frequency_units()`，`pyright` 对 `FrequencyUnit.Hzz` 报错

## 4. Node 绑定

- [ ] 4.1 先写失败测试 `typescript/test/frequency-unit.native.test.ts`：`frequencyUnits()` 返回五字符串、成员名集合 == core、`FrequencyUnit.Hzz` 编译期报错（`@ts-expect-error`）；验证：`pnpm -C typescript test:native` RED
- [ ] 4.2 core enum 与 `frequency_units()` 加 `#[cfg_attr(feature="node", napi)]`；`index.node.ts` re-export 两者；验证：4.1 GREEN，`.d.ts` 自动生成含五成员与 `frequencyUnits()`

## 5. 浏览器绑定

- [ ] 5.1 先写失败测试 `typescript/test/frequency-unit.wasm.test.ts`：同 4.1 断言（wasm 端）；验证：`pnpm -C typescript test:wasm` RED
- [ ] 5.2 core enum 与 `frequency_units()` 加 `#[cfg_attr(feature="browser", wasm_bindgen)]`；`index.browser.ts` re-export 两者；验证：5.1 GREEN，wasm `.d.ts` 自动生成含五成员与 `frequencyUnits()`

## 6. 集成与门禁

- [ ] 6.1 扩展 exports 测试：断言三端 `frequency_units()`/`frequencyUnits()` 返回集合相等且等于 core `iter()` 集合、`.pyi`/`.d.ts` 字面量集合一致；验证：`pnpm -C typescript test` + `uv run pytest` 全绿
- [ ] 6.2 加 grep 门禁：`python/`、`typescript/src/` 源码（排除构建产物）无单位字符串字面量；验证：并入 `pnpm check`，命中即退出非 0
- [ ] 6.3 落 `Plan/总体计划.md` 待决清单对应条目销账（结论入本 change 主 spec），跑 `pnpm check:md`；验证：退出 0
