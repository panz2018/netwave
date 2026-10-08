# zero-copy-roundtrip Specification

## Purpose

定义四端（core/python/node/wasm）零拷贝 buffer 往返验证契约：绑定层拿到的视图与
core 持有的缓冲是同一块内存，视图改写对 core 立即可见。这是 netwave 零拷贝卖点的
最小可验证形态，也是 cross-binding 对拍的最早形态。

## Requirements

### Requirement: core 提供交错复数 f64 缓冲

core MUST 暴露一个临时脚手架函数，分配并返回形状为 `(nfreq, nports, nports)` 的
交错复数 f64（complex128，`[re, im, re, im, ...]`）缓冲，并写入可预测图案
（pattern）供四端断言。该函数是脚手架期临时 API，真实数据模型落地后被替换，
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

### Requirement: 异步与 Worker 边界契约（常驻 worker 架构）

跨线程/异步面 MUST 遵守以下契约：

1. **JS 公开计算面单一 async**：core 内部全部同步；JS 绑定层计算动词**不加后缀、
   直接返回 `Promise`**，用户唯一写法是 `await toY(x)`，不存在同步/异步双版本选择。
   同步直通逃生口 `_toY(x)` **仅 node 端保留**（napi core 在进程内，同步直通永远
   可行；`@internal`、签名不承诺稳定）；**浏览器端 `_` 同步计算函数废止**——主线程
   无 wasm，同步计算无处发生（铁律八）。属性/元数据读取从已 resolve 的结果描述符上
   同步读；未持有结果时元数据读取 MUST 异步进 worker。Python 端不受影响
   （同步 + `allow_threads`）。不提供 callback 风格。
2. **计算全进常驻 worker，分流废止**：浏览器端所有计算 MUST 经同一常驻 worker 内
   wasm 执行，MUST NOT 按输入规模分流（"小数据主线程算"废止）。worker 由库的
   async 壳内部托管、常驻至页面关闭；`standalone.js` 内部自起常驻 worker，
   Pages / `<script type="module">` 零配置体验不变。Node 端计算在进程内 napi
   core 执行，大计算入口防阻塞走 napi AsyncTask（绑定高级能力立项时落地）。
3. **结果 buffer 一律 transfer，输入移动仅经显式 transfer**：计算结果 buffer 是新
   分配的、无主的，MUST 以 transfer 零拷贝送回；纯计算动词 MUST NOT 消耗调用方的
   输入 buffer——输入要么已通过 `upload` 显式托管在常驻 worker（托管后反复可用），
   要么边界拷贝进入 worker；只有名字里明说"移交/消耗"（如 `upload`/`drop`）的
   API 才 transfer 调用方的输入（调用后原视图 detached）。元数据（shape、
   frequency 等）MUST 搭结果便车随计算结果同消息回传，MUST NOT 为元数据单开
   worker 往返。
4. **`await` 后必须重建视图**：计算动词返回值 MUST 自带新 buffer（或新
   offset/length），用户从返回值重建 `Float64Array`，不依赖旧视图
   （wasm memory.grow 会 detach 旧视图）。该姿势同时容纳 transfer 所有权转移与
   未来 SAB 原地写两种底层机制，升级不改接口。
5. **SAB 可选升级**：用户分配 SharedArrayBuffer 则零拷贝共享（需 COOP/COEP，
   库运行时按 `buffer instanceof SharedArrayBuffer` 自动检测），普通 ArrayBuffer
   则按上条拷贝/transfer——各路径接口签名完全一致，API 不因底层机制演进而破坏。
   SAB 原地写时结果只从返回值读，不承诺输入 buffer 内容不变。
6. **Worker 容器归宿主 JS**：预置 `netwave.worker.js` 是**单一命令分发器**
   （显式静态表 `cmds = { toY, toZ, ... }`，零数值逻辑，加函数只改表不加文件），
   由库的 async 壳内部托管，普通用户不直接接触；高级用户可经 `netwave/worker`
   子路径自建 Worker。拓扑为单常驻 worker（api-contract spec"worker 泛化分发与
   单常驻拓扑"），多 worker 分桶推迟到有实测需求再立项。多线程 wasm（wthreads +
   SharedArrayBuffer + `+atomics,+bulk-memory`）属后续性能优化立项。worker 异常终止数据
   丢失为已接受行为，不引入持久化恢复。
7. **tree-shaking**：包入口 MUST NOT 用 `export *`（打包器保守处理会整模块
   保留），MUST 显式具名导出；Worker 分发 MUST NOT 用动态属性访问命名空间。
   wasm 二进制不受 JS 摇树，体积靠 Rust 侧 `lto = true` + wasm-opt 控制。

#### Scenario: Worker 往返——输入不消耗、结果零拷贝

- **WHEN** 主线程对同一已 `upload` 托管的输入先后两次 `await toZ(x)` 跨常驻
  worker 执行
- **THEN** 两次调用后托管句柄仍有效，worker 内数据未变（输入未被消耗）
- **AND** 两次结果 buffer 均以 transfer 零拷贝送回，主线程从返回值重建的
  `Float64Array` 数据正确（容差引用 manifest `core_tol`）

#### Scenario: 浏览器无同步计算逃生口

- **WHEN** 浏览器端代码尝试调用 `_toY(x)`
- **THEN** 该导出不存在（浏览器入口无 `_` 前缀同步计算函数）
- **AND** node 端 `_toY(x)` 仍可用且与 `await toY(x)` 结果逐 bit 一致
  （同进程同 core，铁律三原生互比）

#### Scenario: 元数据搭结果便车无额外往返

- **WHEN** 浏览器端 `await toY(x)` 后从结果描述符读 shape/frequency
- **THEN** 元数据随计算结果同消息回传；测试以 worker 消息计数断言该读取
  未产生新消息

### Requirement: cross-binding 往返对拍

四端 MUST 对同一输入图案执行"取视图 → 改元素 → 回读"往返，结果一致。原生三端
（core/python/node）同机同架构 MUST 逐 bit 一致；wasm 跨实现 MUST 用相对容差
（引用 manifest key `core_tol`，本阶段该 key 在 manifest 中登记为占位）。
浏览器端 wasm 往返 MUST 在真浏览器（vitest browser mode，Chromium）经常驻
worker 执行，不再以 node 模拟代替浏览器路径的验收。

#### Scenario: 四端往返一致

- **WHEN** 四端以相同 `(nfreq, nports)` 与相同写入值执行往返
- **THEN** core/python/node 三端回读结果逐 bit 相同
- **AND** wasm 回读与原生结果相对误差 < manifest `core_tol`
- **AND** 任一视图改写后，其余端重新获取视图读取到改写后的值

#### Scenario: 浏览器往返经常驻 worker

- **WHEN** 真浏览器测试执行 upload → 计算 → 回读往返
- **THEN** 全程只有一个常驻 worker 存活，主线程无 wasm 实例
- **AND** 回读结果与原生结果相对误差 < manifest `core_tol`
