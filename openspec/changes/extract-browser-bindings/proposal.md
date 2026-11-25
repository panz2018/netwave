# Proposal

## Why

core 是纯数学库，但 wasm/browser 绑定代码（句柄表、字符串 dispatch、start 钩子、
fetch 后端、枚举的 `#[wasm_bindgen]` 属性）全部住在 core 里，使 core 反向依赖
wasm-bindgen/js-sys/web-sys。这违反「下游只依赖上游公开 API、绝不把代码塞进上游」
的分层原则，也阻断 core 作为零绑定依赖库独立发布到 crates.io。改名与拆包已由
change `extract-browser-package` 完成，本 change 把残留的 browser 绑定代码从 core
彻底搬入 browser crate，使 core 不再含任何 wasm 符号。

## What Changes

- **BREAKING**（内部 crate 边界，非公开 API）：core 删除 `browser`/`browser-http`/
  `cov-drive` feature 与 wasm-bindgen/js-sys/web-sys/wasm-bindgen-futures 依赖；
  `core/src/resources.rs`、两处 `call_namespace`/`register()`、`#[wasm_bindgen(start)]`
  钩子、browser `fetch_text`、枚举上的 `#[cfg_attr(feature="browser", wasm_bindgen)]`
  全部移出 core。
- browser crate 自持句柄表（`browser/src/resources.rs`）、frequency/touchstone 的
  dispatch glue、start 钩子、cov-drive 驱动入口与句柄表测试。
- `FrequencyUnit`/`WavelengthUnit` 的 JS 导出从 wasm glue 改为构建期生成：
  `gen_constants.mjs` 改名 `gen_values.mjs`（命令 `gen:values`），新增枚举抽取段，
  输出单文件 `values.generated.mjs`/`.d.mts`（含 `SPEED_OF_LIGHT` + 两枚举）。
- browser `fromUrl` arm 自调 `web_sys::fetch` + core `Touchstone::from_text`；
  fetch global 做成参数注入，使「无 fetch scope」臂可 mock。
- wasm rust 覆盖率地板 99 → 100（fetch 臂经依赖注入消解后不再是真不可达）。
- core `url_filename` 改 pub（纯字符串逻辑，名字管道职责）。

## Capabilities

### New Capabilities

<!-- 无新增 capability，本 change 全部落在既有 capability 的 requirement 修订。 -->

### Modified Capabilities

- `api-contract`: wasm 导出面与词汇常量来源拆成两条独立 requirement——wasm glue
  导出钉 `{call, register_resources}`，词汇常量（`FrequencyUnit`/`WavelengthUnit`）
  来源改钉「构建期生成物、主线程直读、不实例化 wasm」。
- `ci-matrix`: browser rust 覆盖率链度量对象从 `core/src/` browser-gated 代码改为
  `browser/src/`；地板 99 → 100，删除「fetch 臂真不可达故地板 99」豁免理由。
- `workspace-layout`: browser 子项目自我完整 requirement 扩充——句柄表、dispatch、
  start 钩子、绑定测试均在 `browser/`；core MUST NOT 含任何 wasm 符号或绑定依赖。

## Impact

- 代码：core 的 `lib.rs`、`resources.rs`、`frequency.rs`、`touchstone.rs`、
  `core/Cargo.toml`、`core/tests/resources_table.rs`；browser 的 `lib.rs`、
  `resources.rs`、`frequency_glue.rs`、`touchstone_glue.rs`、`Cargo.toml`、
  `gen_values.mjs`、`test.sh`、`package.json`、`tsdown.config.ts`、
  `index.browser.ts`；`typescript/scripts/merge_browser.mjs`、
  `scripts/check_verbs.py`。
- spec：`api-contract`、`ci-matrix`、`workspace-layout`。
- 不变式：worker generic dispatch（动词名表从 core 移到 browser，worker JS 仍零状态）、
  加方法改一处、绑定 crate 独立度量。
- 受影响铁律：铁律十一（绑定薄壳——能力下沉位置从 core 绑定宏段改为 browser crate）、
  铁律十二（API 名字单源——`fromUrl`/`from_url` 仍同名，仅实现体归属变）。

## Non-goals

- 不动 python/node 绑定（pyclass/napi `cfg_attr` 属性、core 的 pyo3/napi optional
  依赖）——属 Plan 阶段 C，另开 change。本 change 后 core 仍挂 pyo3/napi optional
  feature，但默认不编译、不含 wasm 符号。
- 不改 npm 发包形态（单包 vs 多包）——留待 Plan 第 6 节发包项单独拍板。
- 不改 worker JS 协议、types.ts 公开类型面、`_` 前缀逃生口过滤逻辑。
- 不改 native（reqwest）的 `from_url` 实现。

## Prior art

- 仓库内现成方案：`browser/scripts/gen_constants.mjs` 已确立「core 单源 + 构建期
  机械抽取过界到 JS」模式（从 `core/src/constants.rs` 抽 `SPEED_OF_LIGHT`），本
  change 的枚举导出直接复用并合并该脚本，非新造机制。
- 仓库内现成方案：python/node 已用 newtype 包装把绑定属性收敛到胶水 crate（见
  `openspec/specs/workspace-layout/spec.md` 的绑定放置契约），本 change 对 browser
  采用对称的「胶水代码住 browser crate」放置。

## 专家增补

- 顶尖专家会顺手把 `url_filename` 的可见性提升做成可测公开函数并补单测，而非
  仅 `pub` 了事——本 change 在 `core/src/touchstone.rs` 的 `url_filename` 改 pub
  同时确认其已有/补上 query/fragment 剥离的单测。
- 顶尖专家会在搬句柄表后立刻用 `cargo tree -p netwave` 断言 core 依赖树只剩
  num-complex/strum/thiserror（+ native-http），把「core 零 wasm」做成可门禁化的
  回归断言，落 `browser/scripts/test.sh` 或 CI 步骤。

## 已定裁决

- `范围只清browser`：本 change 只清 browser 绑定，python/node（阶段 C）另开 change。
- `gen_values合并`：`gen_constants.mjs` 改名 `gen_values.mjs`、命令 `gen:values`，
  加枚举抽取段，输出单文件 `values.generated.mjs`/`.d.mts`（常量+两枚举合一）。
- `resources进browser`：句柄表 `resources.rs` 直接进 `browser/src/resources.rs`，
  不抽中立 wasm-runtime crate。
- `core删browser-http`：core 删 browser-http feature，browser `fromUrl` arm 自调
  web_sys::fetch + core `from_text`。
- `wasm地板100`：wasm rust 覆盖率地板 99 → 100，fetch global 参数注入消解不可达臂。
- `api-contract拆两条`：wasm 导出面与词汇常量来源拆成两条独立 requirement。
- `句柄表测试单元测试`：句柄表测试改成 `browser/src/resources.rs` 底部单元测试，
  不动 crate-type。
- `url_filename改pub`：core `url_filename` 改 pub（纯字符串逻辑，名字管道职责）。
- `cov-drive进browser`：`drive_copy_arms()`/`cov-drive` 随 dispatch 进 browser。
- `browser零feature依赖`：`browser/Cargo.toml` 改 `netwave = { path = "../core" }`
  零 feature。
- `check_verbs导出集合`：`check_verbs.py` 的 `WASM_GLUE_EXPORTS` 改为只含
  `call` 与 `register_resources`，新增校验 `values.generated.mjs` 含两枚举。
- `覆盖率链grep路径`：覆盖率链 `.ll` grep 从 `core/src/...` 改 `browser/src/...`。
- `index-browser-import源`：`index.browser.ts` 从 `values.generated.mjs` import
  常量+两枚举；worker JS / types.ts 零改动。
- `promise在browser`：fromUrl 的 Promise 包装 + fetch 全在 browser arm；core native
  `from_url`(reqwest) 不动。
