# Design: governance-api-rules

## 显示串为何各端原生协议而非统一 `toString()`

跨语言强行统一 `toString()` 会让 Python 出现无人调用的死重方法（Python 的
显示协议是 `__str__`/`__repr__`）。故按语言原生协议命名、只统一**字符串
内容**：`ClassName(摘要)`。跨端统一惯用法 `await x.toString()` 在 node 成立
靠同步字符串经 `await` 原样透传，浏览器成立靠 `async toString()`。

代价（已知并接受）：浏览器端 `${f}` 模板插值抛 TypeError（Promise 经
`ToPrimitive`），docs 须写明；若日后碍事，可在浏览器壳缓存显示元数据改回
同步，属实现层可逆决策，不动契约。

## 铁律八为何只加指针不抄正文

memory-lifecycle 已是独立主 spec（5 需求/9 场景、三端实测冻结）。铁律八正文
若摘录 registry/`drop()`/finalizer 要点，即制造第二真相源，必随演进漂移。
指针一句使 review 能从铁律八跳到权威细节，无双写。

## `release()` → `drop()` 的取舍

- 冲突事实：`api-contract` 写 `release()`，memory-lifecycle 定 `drop()`。
- 选 `drop()` 为唯一名：memory-lifecycle 是三端实测全绿的既成契约，
  `drop()` 有确定性回收测试背书；`release()` 从未实现。
- 命名顾虑：clippy 对 `pub fn drop` 有告警（与 `Drop::drop` 混淆），
  故 Rust 侧确定性释放动词沿用已落地的 `free()`，`drop()` 仅存在于 JS 面
  （memory-lifecycle 已定案，本 change 不重开）。

## 铁律十"机械映射不算偏离"的边界

TS camelCase、Rust snake_case、worker async 化是语言/架构强制，不逐条立案。
需立案的是**语义或词汇层**偏离：如 `unit` getter 返回 enum 而非 skrf 的 str、
`from_f` 的 `unit` 必填、`wavelength(unit, n)` 带介质参数——这些在
`frequency-class` 的 design.md 逐条写更强收获。

## 文档语言

本 change 全部为 governance 工件，中文；引用 memory-lifecycle 用相对路径
标题跳转，不写绝对路径。
