# Tasks

## 1. SPEED_OF_LIGHT 常量（core + 三端）

- [x] 1.1 写失败测试：core 断言 `SPEED_OF_LIGHT == 299_792_458.0`（逐 bit，精确常量非容差），确认 red
- [x] 1.2 建 `core/src/constants.rs` 定义 `pub const SPEED_OF_LIGHT: f64 = 299_792_458.0`，rustdoc 写明 SI 精确值定义，测试转 green
- [x] 1.3 Python `python/netwave/constants.py` 薄再导出 + TS 命名导出，写测试断言三端常量逐 bit 相等

## 2. WavelengthUnit 词汇（core + 反射 + 绊线）

- [x] 2.1 写失败测试：`WavelengthUnit::iter()` 成员恰 `{m,cm,mm,um,nm}`、`multiplier` 逐值精确、`FromStr` 大小写不敏感、非法含原文，确认 red
- [x] 2.2 core 加 `WavelengthUnit` enum（穷尽 `multiplier`、`FromStr`、`from_ordinal`、反射三端属性照 `FrequencyUnit`），docs 写倍率 SI 依据，测试转 green
- [x] 2.3 `scripts/check_vocab_types.py` 纳入 `WavelengthUnit` 三端成员集合一致绊线，跑通

## 3. from_f / f / f_scaled / w（core，TDD）

- [x] 3.1 写失败测试：`from_f` 标量/数组双收、unit 必填缺失报错 、`f` 拷贝逐 bit、改返回数组不影响 core、`f_scaled=f/multiplier`、`w=2πf`（引用 manifest `core_tol`），确认 red
- [x] 3.2 core 实现 `f`（拷贝返回）、`f_scaled`、`w`、`from_f` 补 unit 必填校验，rustdoc 写明 `f` 拷贝语义与只读契约（教学式），测试转 green
- [x] 3.3 core `impl Display`/`Debug` 产 `Frequency(start-stop unit, N pts)` 与空轴串，写逐字符断言测试转 green

## 4. from_wavelength / wavelength（core，TDD）

- [x] 4.1 写失败测试：`from_wavelength` n 必填报错、`f=c/(n·λ)` （引用 manifest `core_tol`）、`wavelength` 往返回原轴、`f=0→inf` 非 NaN，确认 red
- [x] 4.2 core 实现 `from_wavelength`/`wavelength`，docs 写公式 `λ=c/(n·f)`、相折射率定义与出处、DC→inf 语义（教学式），测试转 green

## 5. unit getter/setter 与 copy（core）

- [x] 5.1 写失败测试：`unit` getter 返 enum、setter 收 enum|str 大小写不敏感、非法报错含原文、改 unit 不动 f 主数据、`copy` 独立等值，确认 red
- [x] 5.2 core 实现 `unit`/`set_unit`/`copy`，测试转 green

## 6. Python 绑定

- [x] 6.1 pyclass 补功能方法（`f`/`f_scaled`/`w`/`unit` getter+setter/`wavelength`/`copy`/`from_wavelength`）+ `__len__`/`__str__`/`__repr__`，`f` 用 `PyArray1::from_slice` 拷贝
- [x] 6.2 写 pytest：构造/访问器/错误含原文/显示串/拷贝隔离，跑 `pytest` 全绿

## 7. Node 绑定

- [x] 7.1 napi 补方法 + `toString`+inspect 钩子（生成物侧），TS 壳仅 re-export
- [x] 7.2 写 vitest native：访问器/错误/显示串/拷贝，跑 `pnpm -C typescript test:native` 全绿

## 8. 浏览器 wasm + TS 壳

- [x] 8.1 `frequency.rs` `Resource::call` 加 `f`/`fScaled`/`w`/`wavelength` 臂、`call_namespace` 加 `fromWavelength` 臂（回传 buffer/数值），worker/types/resources.rs 零改动
- [x] 8.2 浏览器 TS 壳加 async 访问器 + `async toString()`；写 vitest browser 往返测试，跑 `pnpm -C typescript test:wasm` / `test:browser` 全绿
- [x] 8.3 浏览器 docs 写明 wasm 线性内存高水位（Drop 归还进 free list 不还宿主，峰值=最大并发活对象）

## 9. 生成物与门禁

- [x] 9.1 重新生成 `.pyi`（stub_gen）与 `.d.mts`（napi dts），跑通
- [x] 9.2 `scripts/check_verbs.py` 扩展 `FREQUENCY_VERBS` 至新动词集，跑通三端动词相等

## 10. 集成对拍

- [x] 10.1 `cargo test --workspace` 全绿
- [x] 10.2 `pnpm check:cross` 全绿（λ↔f 往返四端对拍：原生逐 bit、wasm 引用 manifest `core_tol`）
- [x] 10.3 `pnpm check`（md/ts/rs/py 全闸门）全绿
