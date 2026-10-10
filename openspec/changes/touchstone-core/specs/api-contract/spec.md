# Spec Delta

## MODIFIED Requirements

### Requirement: 有状态对象用类、无状态变换用模块函数

持有频率轴 + S 主数据 + z0 的对象 MUST 是类：core `pub struct Network`，
Python `#[pyclass]`、Node napi struct、浏览器 wasm-bindgen struct 原生导出，
域动词是实例方法（对齐 skrf `Network` 惯例）。持有 Touchstone 解析结果的
对象 MUST 是类 `Touchstone`（三端同形态导出）——解析虽是一次性动作，但其
产物（频率轴/S 主数据/z0/元数据）是长活状态，归"状态类"而非模块级函数
（touchstone-core capability 落地）。仅**无状态**一次性变换（纯输入→纯输出、
无留存数据）MUST 是模块级函数，不硬包成类。

#### Scenario: 三端类形态一致

- **WHEN** 三端各自实例化 `Network` 并调用同一域动词
- **THEN** 三端均为实例方法调用形态，动词名一致（TS 仅机械 camelCase）

#### Scenario: Touchstone 是状态类非模块函数

- **WHEN** 检查三端导出面中 Touchstone 解析能力的形态
- **THEN** 解析入口是 `Touchstone` 类工厂（`fromText`/`fromFile`/`fromUrl`），
  解析结果由实例属性承载；不存在返回裸数据元组的模块级解析函数
