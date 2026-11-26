# Design

## Context

见 proposal.md - Why。当前 core 通过 `#[cfg_attr(feature="browser", wasm_bindgen)]`
把枚举、句柄表（`resources.rs`）、两处 `call_namespace` dispatch 与 start 钩子
直接编进 core，browser crate（`netwave-browser`，cdylib）仅 `extern crate netwave`
把 core 的 wasm 导出带进二进制。本设计描述如何把这些符号反向搬入 browser crate，
使 core 退化为零绑定依赖的纯数学库。

关键约束：browser crate 是 `crate-type = ["cdylib"]`（wasm-pack 要求，加 rlib
会留孤儿产物）；wasm-bindgen 属性宏必须贴在类型定义处，proc macro 不能跨 crate
施加到 `use`；`from_ordinal = iter().nth()`，故枚举 ordinal = 变体声明下标。

## Goals / Non-Goals

**Goals:**

- core 源码零 `wasm_bindgen`/`js_sys`/`web_sys`，依赖树只剩数学库。
- 搬迁后 wasm 公开导出面（worker 协议、JS 可见名字）逐字节不变——纯放置重构。
- wasm rust 覆盖率地板从 99 提到 100。

**Non-Goals:**

- 不改 worker JS 协议、不动 types.ts 公开类型面（设计级边界，proposal 已列范围）。
- 不引入新 crate（句柄表直接进 browser，不抽 wasm-runtime）。

## Decisions

### D1：枚举 JS 导出用构建期生成，不用 wasm glue

`gen_constants.mjs` 改名 `gen_values.mjs`（命令 `gen:values`），新增从 core enum
抽变体名+ordinal 的段，输出单文件 `values.generated.mjs`/`.d.mts`（含
`SPEED_OF_LIGHT` + `FrequencyUnit` + `WavelengthUnit`）。ordinal 按变体声明顺序
赋值，与 core `from_ordinal = iter().nth()` 一致。

- **备选 A**：core 保留 `cfg_attr(browser, wasm_bindgen)`——达不到 core 零 wasm 目标，否。
- **备选 B**：browser 定义镜像 enum + `#[wasm_bindgen]` + `From` 转换——ordinal
  两处定义需测试钉死，且仍是 wasm glue 导出（与"主线程直读常量不实例化 wasm"
  的 spec 例外精神冲突），否。
- **选 C（构建期生成）**：复用本仓已确立的 `SPEED_OF_LIGHT` 抽取模式，单一真相源
  在 core enum，主线程 import 不碰 wasm。

### D2：句柄表 + dispatch 直接进 browser crate

`resources.rs` → `browser/src/resources.rs`；frequency/touchstone 的
`impl Resource` + `call_namespace` + `register` + helpers →
`browser/src/frequency_glue.rs` / `browser/src/touchstone_glue.rs`；
start 钩子 → `browser/src/lib.rs`。
句柄表测试改成 `resources.rs` 底部 `#[cfg(test)] mod tests`（cdylib 跑不了集成
测试，单元测试不受 crate-type 限制）。

- **备选**：抽中立 `wasm-runtime` crate——单一消费者，是没要求的抽象，否。

### D3：from_url 的 fetch 后端进 browser，global 参数注入

core 删 `browser-http` feature 与 web-sys/wasm-bindgen-futures 依赖；browser
`fromUrl` arm 自调 `web_sys::fetch`（逻辑原样搬，仍走浏览器原生 fetch）拿文本后
调 core `Touchstone::from_text`。fetch 的 global scope 做成参数：生产传
`js_sys::global()`，测试传无 fetch 能力的假 scope，使「无 fetch scope」臂可被
单元测试命中——这是地板 99→100 的前提。core native `from_url`(reqwest) 不动。

### D4：core `url_filename` 改 pub

纯字符串逻辑（剥 query/fragment、取末段），属名字管道职责，与已 pub 的
`filename_from_path`/`name_from_filename` 同类。browser `fromUrl` arm 复用之。

## Risks / Trade-offs

- [搬迁遗漏导致 wasm 导出面漂移] → `check_verbs.py` 钉死 `{call, register_resources}`
  - 新增校验 `values.generated.mjs` 含两枚举；e2e 全绿兜底。
- [覆盖率链 `.ll` grep 路径改错致链静默失效] → test.sh 已有"无匹配 .ll 即 exit 1"
  守卫；改后跑 `pnpm test:browser` 验证 lcov 含 `browser/src/` 路径行且命中 > 0。
- [枚举 ordinal 抽取与 core 漂移] → spec scenario「browser 枚举 ordinal 与 core
  一致」+ 单测比对生成物与 `from_ordinal`。
- [cdylib 单元测试形式改变句柄表测试覆盖] → 单元测试编译为独立 test binary，
  覆盖等价；`pnpm test:browser` 全链验证。

## Migration Plan

按 proposal「已定裁决」分四段，每段独立验证、独立回滚：

1. 句柄表 + dispatch + start 钩子 + cov-drive 进 browser（验证：`pnpm test:browser`
   绿、core grep 不到 `wasm_bindgen`）。
2. 枚举改构建期生成（验证：`check_verbs.py` 绿、e2e 绿）。
3. from_url/fetch 进 browser + global 注入（验证：fetch 臂单测命中、wasm 地板 100）。
4. 删 core 绑定依赖与 feature（验证：`cargo tree -p netwave` 只剩数学库）。

回滚：每段是独立 commit，git revert 单段即可。

## Open Questions

无——所有设计决策已在 proposal「已定裁决」拍板。
