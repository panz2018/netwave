# Design

## Context

`core/src/frequency.rs` 已有 `Frequency` 内存骨架（`from_f`/`npoints`/`drop` +
`LIVE` 见证计数器 + browser `Resource::call`/`call_namespace` 的 `npoints`/`fromF`
臂），但功能访问器缺失、类未从包入口导出。`FrequencyUnit` enum 已建成（反射三端、
`FromStr` 大小写不敏感、穷尽 `multiplier`、`from_ordinal` 供 worker 数字边界）。
Python 端已有 `Owner` pyclass + `borrow_from_array` 零拷贝范式（用于 Network）。
api-contract 把 `Frequency` 形态与 `f_scaled` 形态推迟到本 change 定案。动机见
proposal.md – Why。

## Goals / Non-Goals

**Goals:**

- 在 core 单点补齐 `Frequency` 功能面，三端经绑定宏/生成物零手抄暴露。
- `f` 拷贝语义使内存生命周期机制零改动（冻结测试不动）。
- 数值真值独立：SI 精确常量逐 bit、λ↔f 往返引用 manifest `core_tol`。

**Non-Goals:**

- 不做 `f` 零拷贝共享、不做频率轴写回（见 proposal Non-goals）。
- 不引入新依赖、不改 worker 拓扑与句柄表结构。

## Decisions

### D1：`f` 拷贝而非零拷贝共享

- **选择**：`f` 每次返回新分配的 f64 数组拷贝。
- **依据**：scikit-rf `f` 为纯 `@property` 无 setter（`frequency.py` 第 476 行），
  频率轴只读、无写回需求；频率轴量级为几千 f64，拷贝近乎免费。
- **收益**：`Frequency::drop()` 的 `self.f_hz = Vec::new()` 一行不改——无视图借走
  主数据，释放不悬垂，已冻结的 memory-lifecycle 测试名副其实。
- **备选**：零拷贝共享（`borrow_from_array` base=实例）——被否：需改 `drop()` 语义、
  重开冻结测试、且只读场景无收益（YAGNI）。
- **各端实现**：Python `PyArray1::from_slice`（新 owned ndarray）；node
  `Float64Array` 拷贝；浏览器 worker 新分配 buffer 经 transfer 回主线程。

### D2：`unit` getter 返 enum、setter 收 enum|str（union 在 core 绑定段）

- getter 直接返回 `FrequencyUnit`（pyo3/napi/wasm 反射 enum 成员）。
- setter 入参 union `FrequencyUnit | str`：字符串经 core `FromStr`（大小写不敏感、
  含原文错误）解析。union 搬运写在 core 绑定宏段（铁律十一：TS/Python 壳零改动）。
- **偏离铁律十**（skrf `unit` 返 str）：收获=IDE 词汇校验 + 零手抄，本节即立案。

### D3：`WavelengthUnit` 照 `FrequencyUnit` 反射

新 enum `{m,cm,mm,um,nm}`，穷尽 `multiplier`（加变体漏配编译失败）、`FromStr`
大小写不敏感、`from_ordinal` 供 worker 数字边界。`check_vocab_types.py` 纳入其
三端成员集合一致绊线。命名不用 `LengthUnit`（RF 语境歧义）。

### D4：派生值不落存储

`f_scaled`（`f/multiplier`）、`w`（`2πf`）、`wavelength`（`c/(n·f)`）每次现算，
MUST NOT 存第二份主数据（api-contract 派生值不入主数据）。`f_scaled` 为只读
property。

### D5：浏览器功能访问器经 worker `match` 加臂

`frequency.rs` 的 `Resource::call` 加 `f`/`fScaled`/`w`/`wavelength` 臂（回传
buffer/数值），`call_namespace` 加 `fromWavelength` 臂；浏览器 TS 壳加 async
访问器 + `async toString()`。worker/types/resources.rs 零改动（泛化分发不变）。

### D6：显示串单源

core `impl Display`（`Debug` 同输出）产 `Frequency(start-stop unit, N pts)` /
空轴 `Frequency([no freqs])`；三端协议钩子一行委托（铁律九）。

## Risks / Trade-offs

- [拷贝 vs skrf 写回习惯] → 频率轴只读是 skrf 事实语义；文档写明 `f` 返回拷贝、
  改轴走 `from_f` 重建，不提供原地写。
- [`f` 拷贝大轴性能] → 频率轴远小于 S 矩阵（铁律六针对 50MB s4p，非频率轴）；
  实测若成热点再议零拷贝（届时走独立 change + 解冻内存测试）。
- [union 入参跨端类型漂移] → `check_verbs.py` + `check_vocab_types.py` + `.pyi`/
  `.d.mts` 重新生成绊线兜底。
