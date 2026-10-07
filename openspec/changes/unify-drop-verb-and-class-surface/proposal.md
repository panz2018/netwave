# Proposal

## Why

同一个语义——「手动立即释放一块内存」——目前在四端有四个名字：core
`Frequency::release()`、node napi `free()`、浏览器 TS 壳 `drop()`、worker 命令
`dropFrequency`；托管缓冲区句柄的释放又叫 `release(handle)`。名字漂移意味着用户
学一个概念要记四个词，且 code-review 无法用一条机械规则判定"漏绑/错名"。本次把
该语义在全部公开面统一为 `drop()`，并把「API 名字单源、禁别名壳」升为铁律，
使这类漂移从此在 CI 与 review 两轴可门禁化。

类形态是统一面的落点：脚手架的自由函数 + 裸数字 handle 使释放只能是函数形态
`drop(handle)`，违反已拍板的「公开形态统一实例方法 `obj.drop()`」。本次顺带
落地 `Network`/`Frequency` 类骨架：数据入口返回实例，读取与释放都是实例方法，
handle 退回 `@internal` 协议细节。

## What Changes

- **BREAKING** core `Frequency::release()` 重命名为 `Frequency::drop()`；
  `impl Drop::drop` 一行委托该固有方法（清理逻辑仍只有一份实现）。
- **BREAKING** node napi 绑定 `free()` 重命名为 `drop()`（不保留 `free` 别名）。
- **BREAKING** 脚手架自由函数面收进类骨架：`Network`/`Frequency` 类落地——
  浏览器 `Network.upload(view)` 静态返回壳实例，node/Python 构造器
  `Network(data)` 即数据入口，`Network.fillPattern(nfreq, nports)` 三端静态，
  实例方法 `readElement(idx)`/`drop()` 三端；`Frequency.fromF(view, unit)`
  三端静态（core `from_f` 机械映射，临时名 `newFrequency` 退役）。无状态自由
  函数 `frequencyUnits()`/`liveCount()` 保持不包类。
- **BREAKING** 公开面 `release(handle)` 退役：浏览器主线程持壳类实例，释放
  形态统一 `obj.drop()`；worker 命令 `release`/`dropFrequency` 收拢为单一
  `drop(handle)`（仅存在于 `postMessage` 内部协议）；错误文案
  `unknown or released handle` → `unknown or dropped handle`。
- **BREAKING** 常驻 worker 两张 JS 句柄表 `hosted`（裸字节缓冲）+ `frequencies`
  （wasm `Frequency` 实例）**整体下沉 core Rust**（cfg 门控 browser feature）：
  core 内唯一一张资源表（`handle → Resource` enum，句柄由 core 单一计数器递增）；
  释放命令收拢为**单一 `drop(handle)`**（废止 `dropFrequency`），core 侧
  `remove` 直接触发 Rust `Drop`；worker JS 零状态纯转发，未来 Network/Circuit
  只加 enum 变体，表数量恒为 1。
- 公开形态统一为实例方法 `obj.drop()`；数字 handle 是 `@internal` 协议细节，
  `drop(handle)` 仅作为 worker `postMessage` 命令形态，不上浮公开 API
  （node/python 直接持对象，无 handle）。
- Python 端 `Frequency` 公开面新增 `drop()`（推翻 memory-lifecycle spec 现行
  「Python MUST NOT 加 `drop()`」），与 JS 端同语义：幂等、释放后访问报错、
  不调用则引用计数自动兜底。
- 新增铁律「API 名字单源，禁别名壳」：公开名在 core/py/node/browser MUST 同一
  个名字，统一 MUST 靠直接命名实现，MUST NOT 用转发到另一名字的别名壳凑统一；
  改名 MUST 连实现带名字一起改，MUST NOT 留旧名兼容别名。
- 新增元规则「冻结非不可变」：已归档/已冻结/已完成 MUST NOT 作为拒绝修正已知
  缺陷的理由，发现即当轮修正（走 spec delta + 同步更新冻结测试断言）。
- `scripts/cross_compare.py` 纳入三端公开动词集合相等断言，名字漂移 CI 直接红。
- 登记 LL：node 曾暴露 `free()` 偏离 memory-lifecycle spec 的 `drop()` 措辞。

## Capabilities

### New Capabilities

（无——本次全部为既有 capability 的 Requirement 修订。）

### Modified Capabilities

- `project-governance`：新增铁律「API 名字单源，禁别名壳」（含机械映射豁免与
  工具链生成物豁免）。
- `memory-lifecycle`：显式释放 Requirement 从「JS-only `drop()`」改为「全端
  `drop()`」；删除 Python/Rust 禁令；node `free()` 措辞改 `drop()`；「主线程
  registry 驱动 worker 释放」改为句柄表下沉 core（cfg=browser）+ worker JS
  零状态纯转发 + 单一 `drop` 命令（废止 `dropFrequency` 与 `hosted`/
  `frequencies` 两表）。
- `api-contract`：「显式托管入口与显式内存回收」明确 `upload` 为浏览器专属
  入口（worker 边界），node/Python 以构造器为数据入口；回收为实例方法
  `drop()`，公开面无 `drop(handle)`；`Network`/`Frequency` 类骨架随本 change
  落地。
- `zero-copy-roundtrip`：「只有名字里明说移交/消耗的 API 才 transfer 输入」中
  点名的 `upload`/`release` 改为 `upload`/`drop`。

## Non-goals

- 不加 Python `with` 上下文管理器（`__enter__`/`__exit__`）——v1 只有一个
  `drop()`，将来有真实需求再立项。
- 不改 wasm-bindgen 为导出类自动生成的 `free()`（工具链焊死、用户不可见）；
  句柄表下沉 core 后 wasm `Frequency` 不再浮出 JS，该生成物连 JS 调用点都不存在。
- 不加任何兼容性别名（`free`/`release` 均不留 deprecated 转发）。
- 不动 `Frequency` 功能方法面（`f`/`f_scaled`/`w`/`wavelength`/`from_wavelength`/
  `WavelengthUnit`/`SPEED_OF_LIGHT`）——归 `frequency-class` change。
- 不加整块取回出口（如 `net.toBuffer()`）——整块回传属计算动词零拷贝契约，
  随 Touchstone 核心立项；骨架期测试用 `readElement` 抽查，不提前造注定被
  计算动词取代的出口。
- 不改内存生命周期的**回收语义**（registry 驱动、共享不误删、见证计数器语义
  不变）；本 change 改的是**表结构与动词命名**（两表→单表、多动词→`drop`），
  回收时机与见证机制不变；冻结测试只改调用名与协议名，断言意图不动。

## Impact

- 代码：`core/src/frequency.rs`、core 新增 `network.rs`（骨架）与资源表模块
  （cfg=browser：`Resource` enum 句柄表，注册焊死工厂入口，`drop(handle)` =
  `remove` 触发 `Drop`）、`typescript/native/src/lib.rs`（`Network` napi 类）、
  `typescript/src/{index.browser,index.node,types,netwave.worker}.ts`（壳类 +
  worker 零状态转发）、`python/src/lib.rs`（`Network`/`Frequency` pyclass 首次
  导出含 `drop()`）。
- 测试：`typescript/test/native/{memory-lifecycle,native.roundtrip}.test.ts`、
  `typescript/test/wasm/{memory-lifecycle,browser-roundtrip,browser-surface,worker}.test.ts`、
  `typescript/test/browser/browser-resident.test.ts`（改名，断言逻辑不变）。
- 生成物：`.pyi`（stub_gen）与 `.d.mts`（napi dts）重新生成。
- 文档：`openspec/specs/{project-governance,memory-lifecycle,api-contract,
  zero-copy-roundtrip}/spec.md`、`Plan/总体计划.md`（公开面收敛与 Network 骨架
  部分销账）、`Plan/频率类设计.md`（待裁决条目销账）、
  `openspec/specs/lessons-learned/`（新增 LL + INDEX）、
  `typescript/README.md` / `python/README.md` 若有动词示例。
- 门禁：`scripts/cross_compare.py`（三端动词集合相等）、`pnpm check` 全量绿。
- 受影响铁律：铁律八（worker 命令名）、铁律九（协议钩子不受影响，机械映射豁免）、
  铁律十（`drop` 非 skrf 概念，属 JS 平台特有约束的已立案偏离）、铁律十一
  （薄壳——本次新增的铁律是其名字维度的补集）。
