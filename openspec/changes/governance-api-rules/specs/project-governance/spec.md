# Spec Delta

## Purpose

为 governance 补三条 API 铁律（跨端协议钩子 / skrf 兼容优先 / 绑定薄壳），
并给铁律八补跨 realm 内存生命周期指针，使 code-review Standards 轴对显示串、
API 命名、壳厚度、内存回收有可判定依据。

## ADDED Requirements

### Requirement: 铁律九 跨端协议钩子

每个公开类 MUST 在全部存在该对象的端提供统一显示串，格式
`ClassName(摘要)`（如 `Frequency(1.0-5.0 GHz, 3 pts)`），各端 MUST 使用同一
字符串内容。入口按语言原生协议命名，MUST NOT 自造跨语言同名方法（Python 不
写 `toString()`，JS 不写 `__str__`）：

- Rust：`impl Display`（`{}`）+ `#[derive(Debug)]`（`{:?}`），二者输出同一串；
- Python：`__str__` 与 `__repr__` 互等（对齐 skrf 惯例），`print(f)`、REPL、
  f-string 自动触发；
- Node：`toString()` + `util.inspect.custom` 钩子，`console.log(f)` 自动触发；
- 浏览器（worker 隔离，铁律八）：`async toString()`；`console.log(f)` 无标准
  美化机制（DevTools 无页面侧钩子），惯用法 `console.log(await f.toString())`。

跨端统一惯用法 `await x.toString()` MUST 在 node 与浏览器同时成立（node 同步
字符串经 `await` 原样透传）。浏览器端模板插值 `${x}` MUST NOT 使用（Promise
经 `ToPrimitive` 抛 TypeError），docs MUST 写明。

长度协议：凡暴露 `npoints` 的公开类 MUST 提供 Python `__len__` 一行委托
`npoints`（JS/Rust 无此协议，无对等义务；skrf `Frequency.__len__` 同源）。

协议保留名（netwave 内有特殊含义、不得挪作他用）：`__str__`、`__repr__`、
`Display`、`Debug`、`toString`、`inspect.custom`、`__len__`。

#### Scenario: print 自动触发

- **WHEN** 在 Rust/Python/Node 中 `println!("{f}")` / `print(f)` / `console.log(f)`
- **THEN** 输出统一显示串 `ClassName(摘要)`，无需显式调用转换方法

#### Scenario: 跨端 await toString 一致

- **WHEN** 同一段 `await x.toString()` 分别跑在 node 与浏览器
- **THEN** 两端返回同一显示串

### Requirement: 铁律十 scikit-rf API 兼容优先

公开 API 的命名、参数、返回值与语义 MUST 默认对齐 scikit-rf 同名概念（如
`from_f`、`f`/`f_scaled`/`unit`/`npoints`/`copy`）。偏离 MUST 在对应 change
的 design.md 写明更强收获（能力增量或契约强化），否则一律兼容。语言机械映射
不算偏离：TS camelCase（`fScaled`）、Rust snake_case、worker 端 async 化
（铁律八所致）。

#### Scenario: 偏离须有立案收获

- **WHEN** 新公开 API 与 skrf 同名概念命名或语义不同
- **THEN** design.md 含"更强收获"论证，code-review Standards 轴据此判定；
  无论证即打回

### Requirement: 铁律十一 绑定薄壳

绑定层（pyo3/napi/wasm-bindgen 壳与 TS/Python 再导出壳）MUST 是薄壳：只做
类型搬运与再导出，MUST NOT 含业务逻辑、数值计算、状态存储或适配转换代码。
新增能力 MUST 在 core 添加（含为某端类型便利添加的入参重载，如 enum|str
双收、数组|标量双收），绑定端 MUST NOT 为此改动壳代码。某端缺少所需能力时，
修复位置 MUST 是 core 绑定宏段，而非 JS/Python 壳。协议钩子对契约成员的一行
委托（如 py `__len__` 调 `npoints`）属名字搬运，不算壳逻辑。

#### Scenario: 壳内逻辑即打回

- **WHEN** code-review Standards 轴在 `typescript/src/` 或 `python/netwave/`
  壳中发现数值换算、状态持有或词汇表
- **THEN** 打回，要求下沉 core；能力缺失改 core 绑定段，壳保持零改动

## MODIFIED Requirements

### Requirement: 铁律八 常驻 worker 数据权威与单点所有权

浏览器端 wasm 实例 MUST 只存在于一个常驻 worker 内：主线程 MUST NOT init wasm、
MUST NOT 持有任何数据副本。任一时刻每份数据 MUST 只有唯一所有者（单点所有权），
跨线程移动 MUST 经显式 transfer（结构化克隆 transfer list），MUST NOT 存在隐式
复制路径。计算结果 buffer MUST 以 transfer 零拷贝传出 worker；元数据（shape、
frequency 等描述符）MUST 搭结果便车随同一消息回传，不为元数据单开往返。worker
MUST 常驻至页面关闭，不做按需起停。常驻 worker 是**模块级单例**：同一页面内
无论 import 多少次库入口、创建多少库实例（句柄）， MUST 共用同一 worker。数值
容差不因本铁律改变，仍引用 manifest `core_tol`（铁律三）。跨 realm 内存生命
周期（主线程 registry 驱动 worker 释放、共享不误删、显式 `drop()` 逃生口、
node napi finalizer）的契约细节见 memory-lifecycle spec。

#### Scenario: 主线程无 wasm

- **WHEN** 真浏览器测试（vitest browser mode，Chromium）加载浏览器端入口并执行
  一次计算
- **THEN** 主线程 globalThis 上不存在已初始化的 wasm 实例/导出命名空间
- **AND** 计算在常驻 worker 内完成，结果经 transfer 回主线程

#### Scenario: 单点所有权与显式 transfer

- **WHEN** 主线程把 buffer 交给 worker（`upload`）后再读原 buffer
- **THEN** 原 buffer 已 detached（所有权已移动），不发生隐式复制
- **AND** 计算结果 buffer 为 worker 新分配并以 transfer 送回，主线程从返回值
  重建视图，数据与 worker 内计算结果一致（容差引用 manifest `core_tol`）

#### Scenario: 元数据搭结果便车

- **WHEN** 主线程 `await` 一次计算并读取结果的 shape/frequency
- **THEN** 元数据随该次计算结果同消息回传，无额外 worker 往返消息

#### Scenario: 多实例共用单一 worker

- **WHEN** 同一页面多次 import 库入口并创建多个句柄/实例后各执行一次计算
- **THEN** 页面内存活 worker 数仍为一（模块级单例），全部计算在同一 worker 内执行
- **AND** 各句柄在同一 worker 内独立寻址，互不串扰
