# Tasks

> 顺序不变式（design.md「先建新后拆旧（构建顺序不变式）」）：先建新（组 1–5）、
> 后拆旧（组 6）。`Network`/自由函数
> 在组 6 前全程保留，新旧共存，杜绝功能真空。

## 1. core 新面：Arc 主数据、from_data 工厂、as_any 下转

- [x] 1.1 RED: 在 `core/tests/touchstone_data.rs` 新增 `from_data` 构造 + 零拷贝派生回读测试（`from_data(freq, data, z0, param)` 构造后取 `s()` 改写某元素、读 `data("S","MA")` 换算回 RI 断言与写入值一致），并在 `core/tests/resources_table.rs` 新增 `Resource::as_any` 下转 `Frequency` 的断言；`from_data`/`as_any` 此时未实现，`cargo test -p netwave` 编译失败即 RED。
- [x] 1.2 GREEN: `core/src/touchstone.rs` `s` 字段 `Vec<f64>`→`Arc<Vec<f64>>`，`from_text`/`from_data` 构造包 `Arc::new`，`s()` 仍返 `&[f64]`（`&self.s` 自动解引用）；`new`→`from_data`（:780），`from_data` rustdoc 达教学式标准（宪法元规则）。验证：1.1 的 `from_data` 构造与派生回读测试转绿，`cargo test -p netwave touchstone` 全绿。
- [x] 1.3 GREEN: `Resource` trait 加 `fn as_any(&self) -> &dyn Any`（core 内部方法、非公开面、不上浮绑定），各 `impl Resource` 补实现；browser `call_namespace` 加 `"fromData"` 臂（读 arg0 freqHandle → 资源表取 `Frequency` → `downcast_ref` → `Touchstone::from_data`）。验证：`cargo test -p netwave resources` 全绿，1.1 的 `as_any` 下转断言转绿。
- [x] 1.4 把 `core/tests/touchstone_data.rs` 其余 `Touchstone::new` 调用点（共 12 处）改名 `from_data`。验证：`cargo test -p netwave` 全绿。

## 2. node 新面：零拷贝 from_external + fromData 工厂

- [x] 2.1 RED: 重写 `typescript/test/native/native.roundtrip.test.ts` 走 `Touchstone`——`fromData(freq, data, z0, param)` 构造后取 `ts.s` 视图改写、读 `ts.data("S","MA")`/`ts.z` 换算回 RI 断言一致，并断言视图为 external（非拷贝，改写对 core 可见）；`fromData` 未实现且当前 `get_s` 是 `to_vec` 拷贝（改写不可见），`pnpm -C typescript test:native` 失败即 RED。
- [x] 2.2 GREEN: `typescript/native/src/lib.rs` `get_s` 改 `ArrayBuffer::from_external` + finalize 回调 drop `Arc` clone（napi-rs 实证模式）；`#[napi(constructor)] new`→`#[napi(factory)] fromData`（BREAKING）；`CoreTouchstone::new` 调用点（:297）改 `from_data`；`.d.mts` 再生成（类型 stub 达教学式标准）。验证：2.1 转绿，`pnpm -C typescript test:native` 全绿（含 CJS twin）。

## 3. Python 新面：from_data 工厂

- [x] 3.1 RED: 改 `python/tests/test_touchstone_class.py`（:132–:149）与 `test_roundtrip.py` 走 `Touchstone.from_data(freq, data, z0, param)` 构造，断言 `ts.s` 的 `flags.owndata is False`、改写视图后读 `ts.data("S","MA")`/`ts.z` 换算回 RI 一致；`from_data` 未实现，`pytest` 失败即 RED。
- [x] 3.2 GREEN: `python/src/lib.rs` `#[new] Touchstone(...)`→`@staticmethod from_data`（BREAKING，:367），`CoreTouchstone::new` 调用点（:380）改 `from_data`，`from_data` docstring 达教学式标准；`_netwave.pyi` stub-gen 再生成。验证：3.1 转绿，`pytest` 全绿。

## 4. 浏览器新面：fromData 工厂（壳 + worker 路由）

- [x] 4.1 RED: 在 `typescript/test/browser/browser-resident.test.ts` 新增 `Touchstone.fromData(frequency, data, z0, parameter)` 断言——返回 `Promise<Touchstone>`、`data` 进 transfer 后原 buffer `byteLength === 0`、`await ts.s` 数据正确；`fromData` 未实现，`pnpm -C typescript test:browser` 失败即 RED。
- [x] 4.2 GREEN: `typescript/src/index.browser.ts` 加 `static fromData(frequency, data, z0, parameter)`（壳内部读 `frequency.handle`，发 `{handle:"touchstone", method:"fromData", args:[...]}`，`data` 进 transfer list，返回 `Promise<Touchstone>`），JSDoc 达教学式标准。验证：4.1 转绿，`pnpm -C typescript test:browser` 全绿。

## 5. cross-binding 对拍迁移（scaffold → 真实 Touchstone）

- [x] 5.1 改 `scripts/cross_compare.py`：删 scaffold `.bin` 对比段（`core.bin`/`python.bin`/`node.bin`/`wasm.bin`），anti-tautology 自检（:120）扰动目标从 `python.bin`/`node.bin`/`wasm.bin` 改扰 `_ts_*` bin。验证：`pnpm check:cross` 全绿（Touchstone 四端逐 bit 相等），且故意扰 `_ts_*` bin 时自检仍报错（防假绿）。
- [x] 5.2 删四端 dump 脚本的 scaffold dump 行：`core/scripts/dump.rs`（`netwave::fill_pattern`→`core.bin`）、`python/scripts/dump.py`（`netwave.fill_pattern`→`python.bin`）、`typescript/scripts/dump.mjs`（node `fillPattern`→`node.bin` 与 wasm `network.fillPattern`/`readElement`→`wasm.bin`）。验证：dump 仅产 `_ts_*`/freq bin，`pnpm check:cross` 仍全绿。

## 6. 删除 Network 类与自由函数（新面全绿后，最后执行）

- [x] 6.1 core: 删 `core/src/network.rs` 整文件、`core/src/lib.rs` 的 `fill_pattern` 自由函数 + 「Temporary API notice」文档段 + `pub mod network` + `register_resources` 里的 `network::register()`；删 `core/tests/fill_pattern.rs`、`core/tests/network_skeleton.rs`；`core/tests/resources_table.rs` 去 `Network`（`network_and_frequency_host_through_the_same_table`、`fill_pattern(1,1)`、`register_namespace("network",...)` 改走 `Touchstone`/`Frequency`）。验证：`cargo test --workspace` 全绿。
- [x] 6.2 python: 删 `python/src/lib.rs` 的 `fill_pattern`/`read_element` pyfunction、`Network` pyclass+impl、`core_fill_pattern`/`CoreNetwork` import、注册行；删 `python/tests/test_memory_lifecycle.py` 的 `test_network_*` 与 `hasattr(Network,"upload")`，改 Touchstone drop 报错见证。验证：`pytest` 全绿。
- [x] 6.3 node: 删 `typescript/native/src/lib.rs` 的 `fill_pattern`/`read_element` napi、`Network` napi struct+impl、相关 import；删 `typescript/src/index.node.ts` 的 `fillPattern`/`_fillPattern`/`_readElement` 导出 + `Network` re-export；删 `typescript/src/types.ts` 的 `fillPattern`/`Network` 声明；删 `typescript/test/native/exports.test.ts` 的 `fillPattern`/`Network` 断言。验证：`pnpm -C typescript test:native` 全绿。
- [x] 6.4 浏览器: 删 `typescript/src/index.browser.ts` 的 `Network` 类（`upload`/`fillPattern`/`readElement`/`drop`）；`typescript/test/wasm/worker.test.ts` 的 `Network.*` 改 `Touchstone`、动词名单去 `upload`/`fillPattern`/`readElement`；`browser-roundtrip.test.ts` 重写走 `Touchstone`；`browser-resident.test.ts` 的 `Network.fillPattern`/`upload`/`readElement` 改 `Touchstone`（`fromBytes`/`s`/`drop`）；`browser-surface.test.ts` 期望面去 `"Network"`；`wasm/touchstone.test.ts` 承接迁移来的零拷贝/往返断言。验证：`pnpm -C typescript test:wasm`、`test:browser` 全绿。
- [x] 6.5 docs: 改写 `core/README.md`（「only public verb is `fill_pattern`」→ Touchstone 现状）、`python/README.md`（「Two verbs: `fill_pattern`...」→ 现状）、`typescript/README.md`（若提 `fillPattern`），全部达教学式标准（宪法元规则）。验证：`pnpm check:md` 全绿，三 README 无 `fill_pattern`/`Network`/`upload` 措辞。

## 7. 门禁、账本与文档收尾

- [x] 7.1 改 `scripts/check_verbs.py`：删 `NETWORK_VERBS`（:36）、`BROWSER_ONLY = {upload}`（:83 段）、三端 `Network` 类校验段（:209–:242）；新增构造入口门禁（铁律十五见证）——`core/src/**` 无 `pub fn new`、`python/src`/`typescript/native/src` 无 `#[new]`/`#[napi(constructor)]`、`typescript/src/**` 的 `constructor(` 必须带 `private`。验证：`pnpm check` 全绿，且故意在公开面加一个 `pub fn new` 时门禁报错。
- [x] 7.2 改 `openspec/specs/lessons-learned/python.md`：复发检测指针 `test_fill_pattern_view_zero_copy` 改指新零拷贝回读测试（历史事件条目本身不改写）。验证：`pnpm check:md` 全绿。
- [x] 7.3 改 `Plan/README.md`（本行状态）、`Plan/功能覆盖规划.md` 与 `Plan/总体计划.md`（`upload`/`drop` 措辞随 `fromData` 工厂校准）、`openspec/specs/project-governance/spec.md` Purpose 删铁律计数（「十一条」漂移修正为「铁律 + 元规则」）。验证：`pnpm check:md` 全绿。
- [x] 7.4 删除 `Plan/脚手架自由函数退役.md`（Plan 生命周期：决策已全部吸收进本 change 的 proposal/design/specs/tasks，执行完即删）。验证：文件不存在，`pnpm check:md` 全绿（无断链）。

## 8. 全量集成验证

- [x] 8.1 跑全量闸门：`cargo test --workspace`、`pytest`、`pnpm -C typescript test:native`/`test:wasm`/`test:browser`、`pnpm check:cross`、`pnpm check`。验证：全部退出码 0。
- [x] 8.2 全仓 grep 零命中（排除 `uv.lock`/`target/`/`dist/`/archive 历史）：`fill_pattern`、`fillPattern`、`read_element`、`readElement`、`_readElement`、`_fillPattern`、`Network`（`network` 命名空间字符串、`network.rs`、`netwave::network`）、`upload`、`Touchstone::new`、`#[new]`、`#[napi(constructor)]`。验证：零命中（浏览器壳内部 `private constructor(handle)` 不在此列——铁律十五管公开面）。
