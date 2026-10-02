# Tasks

## 1. 依赖与骨架

- [ ] 1.1 在 `core/Cargo.toml` 加 `strum`（关默认 feature、开 `std`）+ 配套 `strum_macros`（同 minor），并加 `python`/`node`/`browser` feature 门控；验证：`cargo check -p netwave-core` 通过
- [ ] 1.2 建 `core/src/frequency.rs` 并在 `lib.rs` `pub mod frequency;`；验证：`cargo check` 通过

## 2. core 词汇与倍率（red 先于 green）

- [ ] 2.1 先写失败测试 `core/tests/frequency_unit.rs`：断言 `FrequencyUnit::iter()` 集合恰为 `{Hz,kHz,MHz,GHz,THz}`、`as_ref()` 规范拼写、`"ghz"`/`"GHZ"`/`"GHz"` 均 `FromStr` 为 `GHz`、`"Hzz"` 返回 `Err` 且消息含 `"Hzz"`；验证：`cargo test -p netwave-core frequency_unit` RED（编译失败即 red）
- [ ] 2.2 实现 `enum FrequencyUnit` + strum derive（`AsRefStr, EnumIter, EnumString` + `ascii_case_insensitive`）使 2.1 转绿；验证：`cargo test -p netwave-core frequency_unit` GREEN
- [ ] 2.3 先写失败测试：断言倍率 `Hz`→1、`kHz`→1e3、`MHz`→1e6、`GHz`→1e9、`THz`→1e12 逐值精确（真值来源 SI 词头闭式定义，容差引用 manifest key `core_tol`）；验证：RED
- [ ] 2.4 实现 `const fn multiplier(self) -> f64` 穷尽 match 使 2.3 转绿；验证：`cargo test` GREEN，且临时注释任一 match 分支后 `cargo check` 报非穷尽错误（反向验证穷尽性）
- [ ] 2.5 定义 `enum Error { UnknownFrequencyUnit(String) }` + `Display`，接 `FromStr` 错误路径；补 rustdoc（教学式：写明倍率即 SI 词头 $10^{3n}$、case-insensitive 依据 Touchstone `# GHZ` 现实）；验证：`cargo test` GREEN + `cargo doc` 无警告

## 3. Python 绑定

- [ ] 3.1 先写失败测试 `python/tests/test_frequency_unit.py`：`netwave.FrequencyUnit.kHz.multiplier == 1e3`、`vars(FrequencyUnit)` 键集合 == core 集合、`FrequencyUnit.Hzz` 抛 `AttributeError`、非法字符串解析抛 `ValueError`；验证：`uv run pytest python/tests/test_frequency_unit.py` RED
- [ ] 3.2 core enum 加 `#[cfg_attr(feature="python", pyclass)]` + `#[cfg_attr(feature="python", pymethods)]`（`multiplier` getter 转发、`__str__`/`__repr__`）+ `impl From<Error> for PyErr`（→`PyValueError`）；`python/src/lib.rs` 加 `add_class::<FrequencyUnit>()`；验证：3.1 GREEN
- [ ] 3.3 用 pyo3-stub-gen 生成 `.pyi`（删手写 `netwave.pyi` 中手抄内容）；验证：生成的 `.pyi` 含 `FrequencyUnit` 五成员，`pyright` 对 `FrequencyUnit.Hzz` 报错

## 4. Node 绑定

- [ ] 4.1 先写失败测试 `typescript/test/frequency-unit.native.test.ts`：`FrequencyUnit.kHz.multiplier === 1e3`、成员名集合 == core、`FrequencyUnit.Hzz` 编译期报错（`@ts-expect-error`）；验证：`pnpm -C typescript test:native` RED
- [ ] 4.2 core enum 加 `#[cfg_attr(feature="node", napi)]` + getter 转发 + `env.throw_type_error` 错误映射；`index.node.ts` re-export；验证：4.1 GREEN，`.d.ts` 自动生成含五成员

## 5. 浏览器绑定

- [ ] 5.1 先写失败测试 `typescript/test/frequency-unit.wasm.test.ts`：同 4.1 断言（wasm 端）；验证：`pnpm -C typescript test:wasm` RED
- [ ] 5.2 core enum 加 `#[cfg_attr(feature="browser", wasm_bindgen)]` + getter 转发（`Result<_, Error: Debug>` 自动 throw `TypeError`）；`index.browser.ts` re-export；验证：5.1 GREEN，wasm `.d.ts` 自动生成含五成员

## 6. 集成与门禁

- [ ] 6.1 扩展 exports 测试：断言三端 `FrequencyUnit` 成员名集合相等且等于 core `iter()` 集合、`.pyi`/`.d.ts` 字面量集合一致；验证：`pnpm -C typescript test` + `uv run pytest` 全绿
- [ ] 6.2 扩展 `scripts/cross_compare.py`：`# GHZ` 样本四端解析后频率轴逐值对拍（容差引用 manifest key `core_tol`）；验证：`python3 scripts/cross_compare.py` 退出 0
- [ ] 6.3 落 `Plan/总体计划.md` 待决清单对应条目销账（结论入本 change 主 spec），跑 `pnpm check:md`；验证：退出 0
