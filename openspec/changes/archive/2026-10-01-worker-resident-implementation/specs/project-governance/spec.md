# Spec Delta

## ADDED Requirements

### Requirement: 铁律八 常驻 worker 数据权威与单点所有权

浏览器端 wasm 实例 MUST 只存在于一个常驻 worker 内：主线程 MUST NOT init wasm、
MUST NOT 持有任何数据副本。任一时刻每份数据 MUST 只有唯一所有者（单点所有权），
跨线程移动 MUST 经显式 transfer（结构化克隆 transfer list），MUST NOT 存在隐式
复制路径。计算结果 buffer MUST 以 transfer 零拷贝传出 worker；元数据（shape、
frequency 等描述符）MUST 搭结果便车随同一消息回传，不为元数据单开往返。worker
MUST 常驻至页面关闭，不做按需起停。常驻 worker 是**模块级单例**：同一页面内
无论 import 多少次库入口、创建多少库实例（句柄）， MUST 共用同一 worker。数值
容差不因本铁律改变，仍引用 manifest `core_tol`（铁律三）。

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
