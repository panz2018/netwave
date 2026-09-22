# Spec Delta

## Purpose

定义四端（core/python/node/wasm）零拷贝 buffer 往返验证契约：绑定层拿到的视图与
core 持有的缓冲是同一块内存，视图改写对 core 立即可见。这是 netwave 零拷贝卖点的
最小可验证形态，也是 cross-binding 对拍的最早形态。

## ADDED Requirements

### Requirement: core 提供交错复数 f64 缓冲

core MUST 暴露一个临时脚手架函数，分配并返回形状为 `(nfreq, nports, nports)` 的
交错复数 f64（complex128，`[re, im, re, im, ...]`）缓冲，并写入可预测图案
（pattern）供四端断言。该函数是阶段 0 临时 API，阶段 2 被真实数据模型替换，
不属于长期契约。

#### Scenario: 缓冲布局逐字节符合铁律一

- **WHEN** core 以 `nfreq=2, nports=2` 生成缓冲
- **THEN** 缓冲长度 = 2×2×2×2×8 = 128 字节（前三因子 nfreq×nports×nports
  = 8 个复数，第四因子 2 = 每复数 re/im 两分量，末因子 8 = f64 字节数）
- **AND** 第 f 个频点的 2×2 矩阵在内存中连续（每频点 4 复数×16 字节 =
  64 字节块）
- **AND** 每个元素先 re 后 im，各占 8 字节小端 f64

### Requirement: 三绑定暴露零拷贝视图

python/node/wasm 三端 MUST 各暴露一个函数，返回 core 所分配缓冲的**视图**而非拷贝：
Python 为 `PyArray`（numpy ndarray，dtype=complex128，shape=(nfreq,nports,nports)）；
Node 为 `ArrayBuffer`/`Float64Array`（经 napi External 后端）；wasm 为
`Float64Array`（指向 wasm 线性内存）。

#### Scenario: Python 视图零拷贝且可写回 core

- **WHEN** Python 端调用绑定函数取得 ndarray，写入 `arr[0,0,1] = 1+2j`
- **THEN** 再次从 core 读取同一位置返回 `1+2j`（同一块内存，非拷贝）
- **AND** ndarray 的 `flags.owndata` 为 False（借用 core 内存）

#### Scenario: Node 视图零拷贝且可写回 core

- **WHEN** Node 端取得 `Float64Array` 视图，写入 `view[2] = 3.5`
- **THEN** 再次从 core 读取对应 re 分量返回 `3.5`
- **AND** 视图底层 byteOffset 指向 core 分配的 External 内存

#### Scenario: wasm 视图零拷贝且可写回 core

- **WHEN** wasm 端取得 `Float64Array` 视图，写入某元素
- **THEN** 再次经 wasm 函数从 core 线性内存读取返回写入值
- **AND** 视图 `buffer` 即 wasm `Memory.buffer`

### Requirement: 异步与 Worker 边界契约（阶段 0 定契约，实现在阶段 3/6）

跨线程/异步面 MUST 遵守以下契约（阶段 0 写入 API 文档与类型骨架，不做实现）：

1. **JS 公开计算面单一 async**（2026-09-22 修订，取代"同步动词为权威 +
   `Async` 后缀"）：core 内部全部同步；JS 绑定层计算动词**不加后缀、直接返回
   `Promise`**，用户唯一写法是 `await toY(x)`，不存在同步/异步双版本选择；
   同步直通版降级为 `_` 前缀逃生口（`_toY(x)`，外部可调用、`.d.ts` 标
   `@internal`、签名不承诺稳定），仅供明确知道自己在做什么的高级用户，
   文档只列不荐；属性/元数据读取（`shape`/`frequency` 等）保持同步；
   Python 端不受影响（同步 + `allow_threads`）。不提供 callback 风格。
2. **Worker 分流库内自动**：`await toY(x)` 内部按输入规模分流——小数据直接调
   同步核心并立即 resolve（不起 Worker）；大数据进 Worker 池（浏览器）/ napi
   AsyncTask（Node）。分流阈值与 Worker 池大小由 benchmark 定（阶段 3/6），
   用户代码两种分支完全相同。
3. **结果 buffer 一律 transfer，输入永不静默消耗**：计算结果 buffer 是新分配的、
   无主的，MUST 以 transfer 零拷贝送回；纯计算动词 MUST NOT 消耗调用方的输入
   buffer——输入要么已通过 `upload` 显式托管在 Worker（托管后反复可用），要么
   边界拷贝进入；只有名字里明说"移交/消耗"（如 `upload`/`takeOwnership`）的
   API 才 transfer 调用方的输入（调用后原视图 detached）。
4. **`await` 后必须重建视图**：计算动词返回值 MUST 自带新 buffer（或新
   offset/length），用户从返回值重建 `Float64Array`，不依赖旧视图
   （wasm memory.grow 会 detach 旧视图）。该姿势同时容纳 transfer 所有权转移与
   未来 SAB 原地写两种底层机制，升级不改接口。
5. **SAB 可选升级**：用户分配 SharedArrayBuffer 则零拷贝共享（需 COOP/COEP，
   库运行时按 `buffer instanceof SharedArrayBuffer` 自动检测），普通 ArrayBuffer
   则按上表拷贝/transfer——各路径接口签名完全一致，API 不因底层机制演进而破坏。
   SAB 原地写时结果只从返回值读，不承诺输入 buffer 内容不变。
6. **Worker 容器归宿主 JS**：预置 `netwave.worker.js` 是**单一命令分发器**
   （显式静态表 `cmds = { toY, toZ, ... }`，零数值逻辑，加函数只改表不加文件），
   由库的 async 壳内部托管，普通用户不直接接触；高级用户可经 `netwave/worker`
   子路径自建 Worker。多线程 wasm（wthreads + SharedArrayBuffer +
   `+atomics,+bulk-memory`）属阶段 3；Node 防阻塞走 napi AsyncTask 属阶段 6。
7. **tree-shaking**：包入口 MUST NOT 用 `export *`（打包器保守处理会整模块
   保留），MUST 显式具名导出；Worker 分发 MUST NOT 用动态属性访问命名空间。
   wasm 二进制不受 JS 摇树，体积靠 Rust 侧 `lto = true` + wasm-opt 控制。

#### Scenario: Worker 往返——输入不消耗、结果零拷贝（阶段 6 实测，阶段 0 仅契约文本评审）

- **WHEN** 主线程对同一输入 buffer 先后两次 `await toZ(x)` 跨 Worker 执行
- **THEN** 两次调用后主线程原输入 buffer 仍有效且数据未变（输入未被消耗）
- **AND** 两次结果 buffer 均以 transfer 零拷贝送回，主线程从返回值重建的
  `Float64Array` 数据正确

#### Scenario: async 面分流测试（阶段 3/6 实现，阶段 0 仅契约文本评审）

- **WHEN** 小数据 `await toY(x)`（低于阈值）
- **THEN** Promise 立即 resolve，结果与 `_toY(x)` 数值一致，未起 Worker
- **AND** 大数据 `await toY(x)`（超过阈值）经 Worker 执行，结果与 `_toY(x)`
  数值一致（原生逐 bit / wasm 容差，沿用 manifest 规则）
- **AND** 阈值上下各取一点，分流行为正确翻转；`_toY` 自身有绑定往返测试
  （铁律七对 `_` 前缀无豁免）

### Requirement: cross-binding 往返对拍

四端 MUST 对同一输入图案执行"取视图 → 改元素 → 回读"往返，结果一致。原生三端
（core/python/node）同机同架构 MUST 逐 bit 一致；wasm 跨实现 MUST 用相对容差
（引用 manifest key `core_tol`，本阶段该 key 在 manifest 中登记为占位）。

#### Scenario: 四端往返一致

- **WHEN** 四端以相同 `(nfreq, nports)` 与相同写入值执行往返
- **THEN** core/python/node 三端回读结果逐 bit 相同
- **AND** wasm 回读与原生结果相对误差 < manifest `core_tol`
- **AND** 任一视图改写后，其余端重新获取视图读取到改写后的值
