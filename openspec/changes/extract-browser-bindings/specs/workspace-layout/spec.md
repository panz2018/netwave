## ADDED Requirements

### Requirement: core 零绑定依赖，browser 自持全部 wasm 代码

core MUST 是纯数学库：源码 MUST NOT 含任何 `wasm_bindgen`/`js_sys`/`web_sys`
符号，`Cargo.toml` MUST NOT 含 wasm-bindgen/js-sys/web-sys/wasm-bindgen-futures
依赖或 `browser`/`browser-http`/`cov-drive` feature。句柄表、字符串 dispatch、
`#[wasm_bindgen(start)]` 注册钩子、browser fetch 后端与绑定测试 MUST 全部住在
`browser/` crate。browser 对 core 的依赖 MUST 零 feature（仅消费 core 纯数学
公开 API），使 core 可作为零绑定依赖库独立发布。

#### Scenario: core grep 不到 wasm 符号

- **WHEN** grep `core/src/` 全目录的 `wasm_bindgen`、`js_sys`、`web_sys`
- **THEN** 零命中

#### Scenario: core 依赖树只剩数学库

- **WHEN** 在仓库根运行 `cargo tree -p netwave`（默认 feature，不开 native-http）
- **THEN** 依赖只剩 num-complex、strum、thiserror（+ 其传递依赖），无任何
  wasm-bindgen/js-sys/web-sys

#### Scenario: browser 零 feature 依赖 core

- **WHEN** 读取 `browser/Cargo.toml`
- **THEN** `netwave` 依赖不带任何 feature

#### Scenario: 句柄表与绑定测试住 browser

- **WHEN** 检查 `browser/src/` 与 `browser/` 测试目录
- **THEN** 句柄表、frequency/touchstone dispatch、start 钩子、cov-drive 驱动
  入口与句柄表测试均在 `browser/` 内，core 不再持有
