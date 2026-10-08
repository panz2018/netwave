# Spec Delta

## MODIFIED Requirements

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
