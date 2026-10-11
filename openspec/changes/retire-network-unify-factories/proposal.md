# Proposal

## Why

`Network` 是 `Touchstone` 的真子集（`core/src/touchstone.rs:197` 字段已含
`frequency`/`s`/`z0`/`nports` 全部状态），脚手架自由函数 `fill_pattern`/
`read_element` 与 `Network` 类是早期占位、真实数据模型落地后已无生产消费者。
保留两套数据状态类会持续撕开"功能缺口从各端私生长数学层"的口子（api-contract
Purpose 所防）。同时，浏览器常驻 worker 下构造器物理上无法 async（铁律八），
数据入口只能是工厂——既然一端只能工厂，四端统一就只能全工厂。

## What Changes

- **BREAKING**：删除 `Network` 类（core + Python + node + 浏览器四端）与
  `fill_pattern`/`read_element` 两个自由函数，数据状态类唯一为 `Touchstone`。
- **BREAKING**：数据入口统一为 `fromData`/`from_data` 静态工厂，四端同名
  （core `Touchstone::new`、Python `#[new]`、node `#[napi(constructor)]` 全部
  改名；浏览器新增 `static fromData`）。与 `fromText`/`fromFile`/`fromUrl`
  凑成对称四件套。
- **BREAKING**：`upload` 概念全仓删除，浏览器数据入口改 `fromData` 工厂经
  transfer 移入 worker。
- node `Touchstone.s` 改零拷贝（`Arc<Vec<f64>>` + `ArrayBuffer::from_external`
  - finalize drop Arc）；Python `s` 已零拷贝，不动；浏览器无共享内存维持克隆。
- 零拷贝写回证据从 `read_element` 迁到既有派生面（改 `ts.s` 视图 → 读
  `ts.data("S","MA")`/`ts.z` 换算回 RI 比对）。
- 新增铁律：四端用户面全部类的构造入口一律 `fromX` 静态工厂且四端公开同名，
  公开面禁裸 `new`/构造器（壳内 private handle 构造器除外）。
- 门禁化：`check_verbs.py` 加构造入口断言（core 无 `pub fn new`、绑定无
  `#[new]`/`#[napi(constructor)]`、壳 `constructor(` 必带 `private`）。

## Capabilities

### New Capabilities

（无——本 change 全部落在既有 capability 上。）

### Modified Capabilities

- `api-contract`：「有状态对象用类」把 `Network` 改 `Touchstone`；「显式托管
  入口与显式内存回收」`Network.upload`→`fromData` 工厂 transfer 入 worker；
  「worker 泛化分发」scenario 的 `Network.upload`/`"network"` 命名空间举例改写；
  「无隐藏派生状态」的 `Network` 措辞归 `Touchstone`。
- `touchstone-core`：「三端类形态与构造即解析」的纯数据构造器 `new Touchstone(...)`
  → `fromData`/`from_data` 工厂（含 `parameter` 必填、z0 推导 version 等 scenario
  的构造器措辞）。
- `project-governance`：新增铁律（构造入口 `fromX` 工厂四端公开同名、公开面禁
  裸构造器）；铁律八 scenario 去 `upload` 举例；铁律十二 scenario 的 `Network`
  壳措辞改 `Touchstone`；Purpose 删铁律计数（「十一条」早已漂移）。
- `zero-copy-roundtrip`：删「core 提供交错复数 f64 缓冲」scaffold requirement；
  「三绑定暴露零拷贝视图」repaint 到 `Touchstone.s`（node external、Python 已零
  拷贝）；wasm scenario 改断言 transfer 数据正确性（常驻 worker 后主线程无 wasm，
  「视图 buffer 即 wasm Memory.buffer」物理不可能）。
- `memory-lifecycle`：去 `Network` 引用（registry/共享所有权 requirement 的
  `Network`/`Frequency` 措辞归 `Frequency`/`Touchstone`）；`drop()` requirement
  明确 `Frequency` 以 `live_count()` 见证、`Touchstone` 以访问报错见证。

> `lessons-learned` 是分片账本（`python.md` 等非 `spec.md`），delta 机制无法
> 指向分片；LL-016 复发检测指针 `test_fill_pattern_view_zero_copy` 的改指是账本
> 编辑，列入 tasks（apply 期直接改分片，历史事件条目本身不改写），不作 spec delta。
> `project-governance` 的 Purpose 铁律计数修正同理：delta 机制不改 Purpose，
> 列入 tasks 直接改主 spec。

## Impact

- **代码**：`core/src/{lib,network,touchstone}.rs`、`core/tests/*`、
  `python/src/lib.rs`、`python/tests/*`、`typescript/native/src/lib.rs`、
  `typescript/src/{index.node,index.browser,types}.ts`、`typescript/test/**`、
  四端 dump 脚本。
- **门禁/脚本**：`scripts/check_verbs.py`（删 Network 段 + 加构造入口断言）、
  `scripts/cross_compare.py`（删 scaffold `.bin` 对比、anti-tautology 自检改扰
  `_ts_*` bin）。
- **铁律**：铁律八（worker async 约束推广）、铁律十（skrf 兼容——Python 端
  `Touchstone(...)`→`from_file`/`from_data` 属已立案偏离）、铁律十二（名字单源）。
- **兼容性**：BREAKING 版本，捆绑发布。Rust core `new` 一并改名（四端彻底统一）。
- **立项方式**：元规则「修铁律走独立最高级变更」——本铁律新增由退役直接触发
  （`Network` 删后全仓构造入口才恰好只剩工厂），捆绑进本 change，三端影响即本
  proposal「Impact」全表。

## Non-goals

- 不新增任何 `Touchstone` 公开属性/函数（零拷贝证据全复用既有 `s` +
  `z`/`y`/`g`/`h`/`data` + `fromData` 工厂；旧版 `toBuffer()`/`buffer` setter 作废）。
- 不动 `Frequency` 类（其构造入口 `from_f`/`from_wavelength` 已合规）。
- 不做计算层域动词（`cascade`/`se2gmm`/`tdr` 等）——属独立 capability 立项。
- 不引入多 worker 分桶、SAB 原地写、wthreads 多线程 wasm——属后续性能优化立项。
- 不改 `Touchstone` 解析语义（格式覆盖、z0 规则、列序、写出规则均不变，仅构造
  入口改名）。
