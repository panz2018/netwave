# Tasks

## 1. 依赖与骨架

- [x] 1.1 在 `core/Cargo.toml` 加 `strum`（0.28 默认仅 `std`，需显式开 `derive`；配套 `strum_macros` 由其引入、不单列依赖），加 `python`/`node`/`browser` feature 门控与 optional 依赖 `pyo3`（与 `python/Cargo.toml` 钉同 minor）/`napi`+`napi-derive`（core 挂 `#[napi]` 需 derive 宏，feature 对齐 native 的 `napi9`）/`wasm-bindgen`；`python`、`typescript/native`、`typescript/wasm` 的 `netwave` 依赖转发对应 feature；验证：`cargo check -p netwave` 与 `cargo check --workspace` 通过（core 包名是 `netwave`，非 `netwave-core`）
- [x] 1.2 建 `core/src/frequency.rs` 并在 `lib.rs` `pub mod frequency;`；验证：`cargo check` 通过

## 2. core 词汇、解析与倍率（red 先于 green）

- [x] 2.1 先写失败测试 `core/tests/frequency_unit.rs`：断言 `FrequencyUnit::iter()` 集合恰为 `{Hz,kHz,MHz,GHz,THz}`、`as_ref()` 规范拼写、`frequency_units()` 返回同序五字符串；验证：`cargo test -p netwave --test frequency_unit` RED（编译失败即 red）
- [x] 2.2 实现 `enum FrequencyUnit` + strum derive（`AsRefStr, EnumIter`）与 `frequency_units()` 透传使 2.1 转绿；验证：`cargo test -p netwave --test frequency_unit` GREEN（实测 3 passed；strum 0.28 的 `AsRefStr` 生成 `as_ref(&self) -> &str` 非 `'static`，透传签名定为 `Vec<String>`）
- [x] 2.3 先写失败测试：断言 `"ghz"`/`"GHZ"`/`"GHz"` 均 `parse::<FrequencyUnit>()` 为 `GHz`、`"Hzz"` 返回 `Err` 且 `Display` 含 `"Hzz"`；验证：RED
- [x] 2.4 定义 `enum Error { UnknownFrequencyUnit(String) }` + `Display`，手写 `impl FromStr`（`iter()`+`as_ref()` case-insensitive，失败绑原文）使 2.3 转绿；验证：`cargo test` GREEN
- [x] 2.5 先写失败测试：断言倍率 `Hz`→1、`kHz`→1e3、`MHz`→1e6、`GHz`→1e9、`THz`→1e12 逐值 `==` 精确相等（真值来源：SI 词头闭式定义 $10^{3n}$，f64 精确可表示；精确常量比较不适用容差，见 LL-042）；验证：RED
- [x] 2.6 实现 `const fn multiplier(self) -> f64` 穷尽 match 使 2.5 转绿；补 rustdoc（教学式：倍率即 SI 词头 $10^{3n}$、case-insensitive 依据 Touchstone `# GHZ` 现实）；验证：`cargo test` GREEN（6 passed）、`cargo doc` 无代码警告（`kHz` 小写为 SI 正确拼写，`#[allow(non_camel_case_types)]` 附理由），且临时注释 `GHz` 分支后 `cargo check` 报 E0004 非穷尽（反向验证穷尽性，已恢复）

## 3. Python 绑定

- [x] 3.1 先写失败测试 `python/tests/test_frequency_unit.py`：`netwave.frequency_units() == ['Hz','kHz','MHz','GHz','THz']`、`netwave.FrequencyUnit.kHz` 存在、`FrequencyUnit.Hzz` 抛 `AttributeError`；验证：`uv run pytest python/tests/test_frequency_unit.py` RED
- [x] 3.2 core enum 加 `#[cfg_attr(feature="python", pyclass(skip_from_py_object))]`（enum 不接受任意对象强转，避免绕过 FromStr 校验；否则 pyo3 0.29 的 Clone-FromPyObject deprecation 警告触发 clippy `-D warnings`）、`frequency_units()` 加 `#[cfg_attr(feature="python", pyfunction)]`；`python/src/lib.rs` 加 `add_class::<FrequencyUnit>()` 与 `add_function`；验证：3.1 GREEN（3 passed）。构建坑：`uv run` 隐式 sync 会用缓存旧 wheel 覆盖 maturin 装的新产物，须 `uv run --no-sync maturin develop` + `uv run --no-sync pytest`（LL-023 变体，已补账本）
- [x] 3.3 接入 pyo3-stub-gen 终态：mixed layout 隔离（`[lib] name = "_netwave"` + `module-name = "netwave._netwave"` + 手写 `netwave/__init__.py` 包壳），避免与 core 的 `libnetwave.rlib` 撞名（E0464），doctest 不关；core 挂 `#[cfg_attr(feature="pyo3-stub-gen", gen_stub_pyclass_enum/gen_stub_pyfunction(module="netwave._netwave"))]`，`stub_gen` bin（feature `stub-gen` 门控）生成后 relocate 到单文件 `netwave/_netwave.pyi`；`#[pyo3(name="_netwave")]` 对齐 init 符号；验证：生成的 `.pyi` 含五成员与 `frequency_units()`，`pyright` 对 `FrequencyUnit.Hzz` 报错、`frequency_units()` 通过（实测 1 error 命中 Hzz）

## 4. Node 绑定

- [x] 4.1 先写失败测试 `typescript/test/native/frequency-unit.test.ts`（必须落在 `test/native/`，vitest include 只收该目录）：`frequencyUnits()` 返回五字符串、成员名集合 == core、`FrequencyUnit.Hzz` 编译期报错（`@ts-expect-error`）；验证：`pnpm -C typescript test:native` RED
- [x] 4.2 core enum 与 `frequency_units()` 加 `#[cfg_attr(feature="node", napi)]`；`index.node.ts` re-export 两者；验证：4.1 GREEN（16 passed），`.d.ts` 自动生成含五成员与 `frequencyUnits()`（napi enum 成员为非枚举 own property，成员集合断言用 `getOwnPropertyNames`）

## 5. 浏览器绑定

- [x] 5.1 先写失败测试 `typescript/test/wasm/frequency-unit.test.ts`（落在 `test/wasm/`，`test:wasm` 与 `test:browser` 两套均收集）：同 4.1 断言，浏览器端 `await frequencyUnits()`；验证：`pnpm -C typescript test:wasm` RED
- [x] 5.2 core enum 与 `frequency_units()` 加 `#[cfg_attr(feature="browser", wasm_bindgen)]`；`index.browser.ts` 从 glue re-export `FrequencyUnit`（glue JS 数字常量对象，import 常量不实例化 wasm，铁律八不破）；`frequencyUnits()` 走常驻 worker：`netwave.worker.ts` cmds 表加 `frequencyUnits` 行调 wasm，`index.browser.ts` 导出 async `frequencyUnits()`（同 `fillPattern` 形态，主线程不执行 wasm）；验证：5.1 GREEN，wasm `.d.ts` 自动生成含五成员与 `frequencyUnits()`（实测 `test:wasm` 12 passed、`test:browser` 真 Chromium 15 passed；worker 分发判据由 `typeof result === "object"` 改为 `"buffer" in result`，否则 `string[]` 结果被误当 buffer 转 transfer 报错；wasm-bindgen enum 对象含反向映射数字键（`"1":"kHz"`），成员集合断言过滤 `^\d+$` 键；环境坑：wasm32 std 缺失，从同版本 stable 复制入 1.98.1 rustlib；真浏览器需 `LD_LIBRARY_PATH=/config/.pw-libs/root/usr/lib/aarch64-linux-gnu`）

## 6. 集成与门禁

- [x] 6.1 扩展 exports 测试：断言三端 `frequency_units()`/`frequencyUnits()` 返回集合相等且等于 core `iter()` 集合、`.pyi`/`.d.ts` 字面量集合一致；验证：`pnpm -C typescript test` + `uv run pytest` 全绿（实测 native 20、wasm 12、browser 15、python 5 全绿；新增 `test/native/vocabulary-consistency.test.ts` 解析三端生成物（`_netwave.pyi`/`index.node.generated.d.mts`/`netwave_wasm.d.ts`）成员集合互等且等于 CANONICAL；顺带修复 task 4.2 遗留的类型门禁漏洞：napi build 缺 `--dts` 致 node glue 无类型、`FrequencyUnit` 退化为 `any`、`@ts-expect-error` 失效——补 `--dts index.node.generated.d.mts/.d.cts` 与 `--no-const-enum`（const enum 不能作值引用），`index.node.ts` 的 `buf.buffer` 加 `as ArrayBuffer`（napi external Buffer 恒为普通 ArrayBuffer））
- [x] 6.2 加 grep 门禁：`python/`、`typescript/src/` 源码无单位字符串字面量；豁免两类——构建产物（`.pyi`/`.d.ts`）与测试目录（`python/tests/`、`typescript/test/`：测试以字面量断言契约，属绊线，core 改名时绊红测试即其职责）；验证：并入 `pnpm check`，命中即退出非 0；反向验证：临时在 `python/src/lib.rs` 加 `"kHz"` 字面量，门禁必须红（新增 `scripts/check_vocab.py`，纯 stdlib，扫 `python/src`/`python/netwave`/`python/scripts`/`typescript/src` 的源码后缀，正则 `[引号](Hz|kHz|MHz|GHz|THz)[引号]` 整词匹配；经 `check:meta` 并入 `pnpm check`（CI 第 52 行 `pnpm check` 覆盖）；反向验证：注入 `const _TRIP: &str = "kHz";` 门禁红、还原后绿；顺带修三处工具链坑：① `cargo clippy --workspace` 特性统一致 core 同函数同时挂 `#[napi]`+`#[wasm_bindgen]` 冲突（napi 宏拒绝），改 `all(feature="node", not(feature="browser"))`/`all(feature="browser", not(feature="node"))` 互斥门控（真实构建只开一端，各端仍生效；仅统一 clippy 下该函数留裸）；② napi build 缺 `--dts`/`--no-const-enum`（见 6.1）；③ 生成的 `.pyi` 被 ruff isort 判违规，`ruff.toml` `extend-exclude = ["**/*.pyi"]` 豁免生成物）
- [x] 6.3 落 `Plan/总体计划.md` 销账：`Frequency`/单位显示形态条目中 `unit` 存放与
      词汇权威部分标记已由本 change 定案（`f_scaled` 形态仍留待阶段 1/2）；绑定壳省力化
      条目中 pyo3-stub-gen 子项标记已提前兑现；跑 `pnpm check:md`；验证：退出 0（`check:md` 退出 0，链接+锚点校验通过）
