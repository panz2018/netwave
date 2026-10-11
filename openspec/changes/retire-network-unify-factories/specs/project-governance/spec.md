# Spec Delta

## ADDED Requirements

### Requirement: 铁律十五 构造入口用 fromX 工厂，公开面禁裸构造器

四端用户面全部类的构造入口 MUST 是 `fromX` 静态工厂（`fromData`/`from_data`、
`fromText`/`from_text`、`fromFile`/`from_file`、`fromUrl`/`from_url`、
`fromF`/`from_f` 等），且在 core/Python/node/浏览器四端 MUST 公开可达且同名
（机械 camelCase/snake_case 映射豁免）。裸 `new`/构造器 MUST NOT 出现在任何端
公开面：Rust core MUST NOT 有 `pub fn new`，Python MUST NOT 有 `#[new]`，node
MUST NOT 有 `#[napi(constructor)]`，浏览器壳 MUST NOT 有公开 `constructor`。
浏览器壳内部 `private constructor(handle)` 是壳持 handle 的传输细节、非构造入口，
不受本铁律管辖。本铁律由常驻 worker 下构造器物理上无法 async（铁律八）推广而来：
既然浏览器端数据入口只能是工厂，四端统一即只能是工厂。管辖范围 = 四端用户面
全部类（机制规则不点名），内部 Rust 结构（`Registry` 等资源表）不受管辖。

#### Scenario: 裸构造器即打回

- **WHEN** code-review Standards 轴在任一端公开面发现 `pub fn new`/`#[new]`/
  `#[napi(constructor)]`/公开 `constructor`
- **THEN** 打回：要求改名为 `fromX` 静态工厂并四端同步

#### Scenario: 构造入口四端同名

- **WHEN** `check_verbs.py` 提取四端某类的构造入口名
- **THEN** 四端集合逐名相等（机械 camelCase/snake_case 映射后比较），且无裸
  构造器名（`new`/`constructor`）出现在公开面

#### Scenario: 壳内私有 handle 构造器豁免

- **WHEN** 检查浏览器壳 `constructor`
- **THEN** 仅存在 `private constructor(handle)`（内部传输细节），无公开构造器；
  用户构造一律经 `fromX` 工厂

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
node napi finalizer）的契约细节见 [memory-lifecycle spec](../memory-lifecycle/spec.md)。

#### Scenario: 主线程无 wasm

- **WHEN** 真浏览器测试（vitest browser mode，Chromium）加载浏览器端入口并执行
  一次计算
- **THEN** 主线程 globalThis 上不存在已初始化的 wasm 实例/导出命名空间
- **AND** 计算在常驻 worker 内完成，结果经 transfer 回主线程

#### Scenario: 单点所有权与显式 transfer

- **WHEN** 主线程经 `fromData` 把 buffer 交给 worker（`data` 进 transfer list）
  后再读原 buffer
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

### Requirement: 铁律十二 API 名字单源，禁别名壳

公开 API 的名称（方法/函数/属性）在 core/Python/node/浏览器 MUST 是同一个名字。
统一 MUST 靠**直接命名实现**达成：core 里该函数就叫这个名字，绑定宏原样搬运同名
方法——MUST NOT 在任何层添加转发到另一名字的别名函数/属性来"凑"统一。改名 MUST
连实现带名字一起改（重命名），MUST NOT 保留旧名作兼容别名（无 deprecated 转发、
无 `free() { this.drop() }` 式垫片）。

机械映射不算违反（沿用铁律九/十既有豁免）：TS camelCase（`fScaled` ↔
`f_scaled`）、Rust/Python snake_case、语言原生协议钩子（`__str__`/`toString`/
`inspect.custom`）、worker 隔离导致的 async 化（铁律八）。

工具链生成物名字不受本铁律管辖（如 wasm-bindgen 为导出类自动生成的 `free()`），
但生成物 MUST NOT 出现在用户可见面：用户可见面只允许那个唯一的名字。

本铁律是铁律十一（绑定薄壳）在名字维度的补集：铁律十一禁壳内有逻辑，本铁律禁
壳内有第二个名字。

#### Scenario: 别名壳即打回

- **WHEN** code-review Standards 轴在任一端发现转发定义：Rust `fn free` 体内
  调 `self.drop()`，或 TS `drop()` 体内 `return this.free()`
- **THEN** 打回：要求把实现直接命名为统一名并删除转发

#### Scenario: 改名不留旧别名

- **WHEN** 公开 API 改名（如 `release`→`drop`）
- **THEN** 同一 PR 内旧名在全部端、测试、文档与生成物（`.pyi`/`.d.mts`）中
  消失，无兼容别名残留

#### Scenario: 三端动词集合相等即绿

- **WHEN** CI 运行 `scripts/check_verbs.py` 提取三端公开动词集合
- **THEN** 三端集合逐名相等（机械 camelCase 映射后比较），任一名字漂移即失败

#### Scenario: 生成物不上浮公开面

- **WHEN** 检查浏览器/node 用户可见导出面
- **THEN** 不含 wasm-bindgen 生成物名（`free`）；该名字仅存在于 worker 内部
  对生成物的调用点

#### Scenario: 统一形态为实例方法

- **WHEN** 检查三端手动释放的调用形态
- **THEN** 公开形态统一为实例方法 `obj.drop()`（浏览器主线程持 `Touchstone`/
  `Frequency` 壳实例，壳内是数字 handle）；`drop(handle)` 仅作为 worker 内部
  `postMessage` 命令形态存在，MUST NOT 上浮为公开 API
