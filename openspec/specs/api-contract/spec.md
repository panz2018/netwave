# api-contract Specification

## Purpose

定义 netwave 跨语言（core/python/node/wasm）API 面的长期结构契约：三层职责划分、
类式 API 形态、显式托管与内存回收、z0 双动词、频率轴单位与结构变更语义——防止
功能缺口从各端私生长数学层撕开，是绑定层设计与 code-review 的判定依据。

## Requirements

### Requirement: 三层 API 契约（数据/计算/结构）

API 面 MUST 分三层且三端一致：① **数据层**——交错 f64 缓冲的可写视图
（Python ndarray 花式索引 / TS typed array 索引与 `subarray` / wasm
`Float64Array`），直接暴露；② **计算层**——域动词（`to_z`/`to_y`/`cascade`/
`se2gmm`/`tdr`/`renormalize` 等），唯一数值权威，全在 core；③ **结构层**——
改形状/元数据的 core 动词（`set_frequencies`/`interpolate`/`renumber`/
`add_port` 等），重分配内存。绑定层 MUST NOT 暴露 `matmul`/`solve`/`inv`/`eig`
等线代原语；计算层功能缺口 MUST 走 OpenSpec 变更进 core 后四端同步发版。

#### Scenario: 无线代原语泄漏

- **WHEN** 检查三端公开 API 面（`.pyi`、`.d.ts`、wasm-bindgen 导出）
- **THEN** 无任何矩阵乘/求逆/特征值等线代原语导出
- **AND** 数值计算只经 core 域动词发生

#### Scenario: 结构动词后旧视图作废

- **WHEN** 用户调用任一结构层动词（如 `interpolate`）后仍持有调用前的缓冲视图
- **THEN** API 文档（rustdoc/docstring/JSDoc）写明旧视图行为未定义、必须重新
  获取；wasm 端 memory.grow 后旧 `Float64Array` 被硬件强制 detach
- **AND** 结构动词在类型层面返回新对象，不提供原地修改型签名

### Requirement: 有状态对象用类、无状态变换用模块函数

持有频率轴 + S 主数据 + z0 的对象 MUST 是类：core `pub struct Network`，
Python `#[pyclass]`、Node napi struct、浏览器 wasm-bindgen struct 原生导出，
域动词是实例方法（对齐 skrf `Network` 惯例）。无状态一次性变换（如 Touchstone
文本解析）MUST 是模块级函数，不硬包成类。

#### Scenario: 三端类形态一致

- **WHEN** 三端各自实例化 `Network` 并调用同一域动词
- **THEN** 三端均为实例方法调用形态，动词名一致（TS 仅机械 camelCase）

### Requirement: 显式托管入口与显式内存回收

wasm 端数据进入 worker 线性内存 MUST 经显式命名入口 `Network.upload(view)`
——调用后原 buffer 声明失效（破坏性语义由方法名表达）；`new Network()` 走普通
结构化克隆，输入永不静默消耗。内存回收 MUST 提供显式 `release()` 立即归还
arena，GC/Drop 仅作兜底。

#### Scenario: upload 后原视图失效

- **WHEN** JS 端对某 `Float64Array` 视图调用 `Network.upload(view)`
- **THEN** 原 buffer 处于 detached 状态（`byteLength === 0`）
- **AND** 后续方法调用只传 handle，无重复上传

### Requirement: z0 双动词语义分离

参考阻抗变更 MUST 拆成两个动词：`renormalize(z0)` 属计算层，S 数据随之重算、
主数据变更；`set_z0_reference(z0)` 属结构层，只改端口参考标签、S 不动、派生量
（z/y）变。两者 MUST NOT 合并为一个名字。

#### Scenario: renormalize 改主数据

- **WHEN** 调用 `renormalize(z0_new)` 后读取 `s`
- **THEN** `s` 数值相对调用前已按新参考阻抗重算（与 skrf z0 setter 行为一致，
  golden 对拍容差引用 manifest key）

#### Scenario: set_z0_reference 不动主数据

- **WHEN** 调用 `set_z0_reference(z0_new)` 后读取 `s`
- **THEN** `s` 逐 bit 不变；读取 `z` 时派生值按新 z0 变化

### Requirement: 频率轴主数据恒为 f64 Hz

core 频率轴主数据 MUST 永远存 f64 Hz，单位歧义 MUST NOT 进入计算层
（解析 `# GHZ` 文件时在解析层换算为 Hz 入库）。派生换算值 MUST NOT 作为
第二份主数据存储，绑定层 MUST NOT 自存单位状态或自实现换算（三层契约
推论）。`unit` 的存放位置（core 元数据 vs 绑定层）、`f_scaled` 的命名与
暴露形态（property vs 方法）、`Frequency` 独立类 vs `Network` 属性属设计
决策，由阶段 1/2 的 design.md 定案（跟踪于总体计划待决细节清单），
本 spec 不提前焊死。

#### Scenario: 单位换算在解析时完成

- **WHEN** 解析 `# GHZ` 选项行的 Touchstone 文件
- **THEN** core 频率轴主数据为 Hz（文件值 × 1e9）

#### Scenario: 单位形态未定案不得实现

- **WHEN** 阶段 1/2 design.md 尚未定案 `unit`/`f_scaled` 形态，有人提议
  在绑定层实现单位换算或自存 unit
- **THEN** code-review Standards 轴拒绝（违反三层契约：绑定层不自存状态、
  不自算数值）

### Requirement: 无隐藏派生状态与频率轴原子变更

`Network` MUST NOT 缓存任何派生结果——`to_z()` 等每次基于当前主数据现算，
用户直接写视图后无需 sync 调用。改频率 MUST 是 `(freq_axis, s)` 一个原子事务，
MUST NOT 提供单独的频率轴 setter。新增频点 MUST 经
`add_frequency(f, method)` 且 `method` 为必填参数（插值 / 用户指定完整 p×p
矩阵 / 显式零填充），不存在"默认加一行"。

#### Scenario: 视图直写后派生量即时正确

- **WHEN** 用户经可写视图改写某 S 元素后调用 `to_z()`
- **THEN** 返回的 Z 基于改写后的数据，无需任何 sync/refresh 调用

#### Scenario: 加频点必须显式给来源

- **WHEN** 调用 `add_frequency` 未传 `method`
- **THEN** 调用失败（参数缺失报错），不发生隐式补零或默认插值

### Requirement: worker 泛化分发与单常驻拓扑

worker 消息协议 MUST 是 `{handle, method, args}` 泛化分发
（`objects.get(handle)[method](...)`），是与动词数量无关的固定模板——core 加
方法时三端壳与 worker 零改动；`_` 前缀逃生口方法 MUST 被自动过滤不进 worker
命令面。阶段 3–6 MUST 维持单常驻 worker 拓扑；多 worker 分桶 MUST 推迟到
阶段 6+ 且有实测需求才立项。

#### Scenario: 加动词零改动

- **WHEN** core 新增一个域动词并完成三端绑定
- **THEN** `netwave.worker.js` 分发器代码无需任何修改即可路由该动词
