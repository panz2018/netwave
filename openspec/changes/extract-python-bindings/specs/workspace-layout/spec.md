# workspace-layout Delta

## RENAMED Requirements

- FROM: `### Requirement: core 零绑定依赖，browser 自持全部 wasm 代码`
- TO: `### Requirement: core 零绑定依赖，browser 与 python 各持全部绑定代码`

## MODIFIED Requirements

### Requirement: core 零绑定依赖，browser 与 python 各持全部绑定代码

core MUST 是纯数学库：源码与 `Cargo.toml` MUST NOT 含任何绑定符号或绑定依赖/feature
（wasm-bindgen/js-sys/web-sys/wasm-bindgen-futures/pyo3/pyo3-stub-gen 及其 feature）。
browser 绑定代码 MUST 全住 `browser/` crate；python 绑定代码（pyclass/pyfunction 属性、
stub-gen 注解、构建期生成的枚举 pyclass、绑定测试）MUST 全住 `python/` crate。两端对
core 的依赖 MUST 零绑定 feature（python 可开 `native-http` 功能 feature，它是 HTTP
能力非绑定），使 core 可作为零绑定依赖库独立发布。各端 dump/测试入口脚本 MUST 住各自
`scripts/`；门禁与测试消费 browser 构建产物 MUST 从 `browser/dist/` 读取，MUST NOT 依赖
typescript/dist 的发布副本。

#### Scenario: core grep 不到 wasm 符号

- **WHEN** grep `core/src/` 全目录的 `wasm_bindgen`、`js_sys`、`web_sys`
- **THEN** 零命中

#### Scenario: core grep 不到 python 绑定符号

- **WHEN** grep `core/src/` 全目录的 `pyo3`、`pyclass`、`pyfunction`、`pymodule`
- **THEN** 零命中

#### Scenario: core 依赖树只剩数学库

- **WHEN** 在仓库根运行 `cargo tree -p netwave`（默认 feature，不开 native-http）
- **THEN** 依赖只剩 num-complex、strum、thiserror（+ 其传递依赖），无任何
  wasm-bindgen/js-sys/web-sys/pyo3

#### Scenario: browser 零 feature 依赖 core

- **WHEN** 读取 `browser/Cargo.toml`
- **THEN** `netwave` 依赖不带任何 feature

#### Scenario: python 仅以功能 feature 依赖 core

- **WHEN** 读取 `python/Cargo.toml`
- **THEN** `netwave` 依赖的 feature 集合不含 `python`/`pyo3-stub-gen`（绑定 feature），
  至多含 `native-http`（HTTP 功能）

#### Scenario: 句柄表与绑定测试住 browser

- **WHEN** 检查 `browser/src/` 与 `browser/` 测试目录
- **THEN** 句柄表、frequency/touchstone dispatch、start 钩子、coverage 驱动
  入口与句柄表测试均在 `browser/` 内，core 不再持有

#### Scenario: pyclass 与 python 测试入口住 python

- **WHEN** 检查 `python/src/`、`python/build.rs` 与 `python/scripts/`
- **THEN** pyclass/pyfunction 属性、stub-gen 注解、构建期生成的枚举 pyclass
  （`python/build.rs`）与 python 测试入口脚本（`python/scripts/test.sh`）、
  构建步骤（`python/scripts/build.sh`）均在 `python/` 内，core 与根 `scripts/run/`
  不再持有

#### Scenario: browser 产物消费读源头目录

- **WHEN** 检查 `scripts/run/test_cross.sh` 探针、`scripts/check_verbs.py`、
  `scripts/check_vocab_types.py` 引用的 browser 产物路径
- **THEN** 全部指向 `browser/dist/`，无一处读 typescript/dist 下的 browser
  产物副本；browser 端 dump 脚本位于 `browser/scripts/`
