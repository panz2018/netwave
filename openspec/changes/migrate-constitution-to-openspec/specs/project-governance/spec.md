# Spec Delta

## Purpose

定义 netwave 全部不可协商硬约束（七条铁律 + 元规则）的唯一真相源 spec：
数据布局、TDD、容差分层、skrf 边界、z0 定位、性能底线、覆盖率与文档语言
约定，供四端实现、CI 门禁与 code-review 双轴共同引用。

## ADDED Requirements

### Requirement: 铁律一 数据布局是契约

核心数据 MUST 永远是 `(nfreq, nports, nports)` 交错复数扁平 f64
（complex128，`[re, im, re, im, ...]`），与 scikit-rf `Network.s` 的内存
布局逐字节相同；对 skrf/numpy 的零拷贝即同一块内存的 reinterpret，无需
转换、无 strided 拷贝。钉死此顺序的理由：Touchstone 按频率逐行存储
（流式解析线性拷贝无转置）、热路径逐频点 (p×p) 矩阵运算（每频点矩阵连续）、
rayon 沿大轴 `nfreq` 切分负载均衡。代价（单条 trace 跨步）属显示/IO 路径，
非热路径。绑定层 MUST NOT 逐元素搬运复数对象。

#### Scenario: 布局逐字节一致

- **WHEN** 任一绑定层取 core 缓冲视图
- **THEN** 视图内存与 skrf `Network.s` 同形状下逐字节相同（reinterpret，零转换）

#### Scenario: 布局变更四端同步

- **WHEN** 有人提议更改数据布局
- **THEN** 该变更等同修改本 spec（最高级变更），core/python/node/wasm 必须
  同一 PR 同步改、同步发版，否则 code-review Standards 轴拒绝

### Requirement: 铁律二 TDD——无失败测试不许写实现

任何产生/变换复数数值的函数（S↔Z/Y/T/ABCD、级联、mixed-mode、FFT 时域、
Touchstone 解析）MUST 先有一条会失败的测试（red），看到 red 后才写实现
（green）。期望值来源 MUST 是独立真值：skrf 预生成 golden、教科书闭式解、
物理不变量；MUST NOT 用被测代码自己算期望值（tautological test）。

#### Scenario: red 先于 green

- **WHEN** 提交包含新数值实现的 PR
- **THEN** 其提交历史中存在先于实现、且当时确实失败的测试提交

#### Scenario: 期望值独立

- **WHEN** code-review Standards 轴审查数值测试
- **THEN** 每条断言的期望值可追溯到 golden / 闭式解 / 物理不变量三者之一，
  无一条从被测函数输出反推

### Requirement: 铁律三 容差集中在 manifest，精度分层是契约

所有数值容差 MUST 只在 `testdata/manifest.json` 定义（含 `core_tol` 键收纳
unit/property 层默认容差），测试代码从 manifest 读取；测试源码 MUST NOT 出现
字面量容差。精度分层：① bit 级断言只允许出现在同机同架构的 cross-binding
原生三端互比（core/python/node 加载同一编译产物）；② 一切跨平台/跨实现比较
（golden 异机重读、wasm vs 原生）MUST 走 manifest 相对容差；③ Touchstone
写出→读回 MUST 是 bit 级（shortest-roundtrip 格式化，能读回原值的最短十进制
表示）。默认量级：解析变换往返 1e-12、级联 1e-11、FFT 时域 1e-9（以
manifest 实际值为准）。放宽任何容差 MUST 在 manifest 注明原因。

#### Scenario: 测试代码无字面量容差

- **WHEN** 检查 core/python/typescript 测试源码
- **THEN** 数值比较的容差全部来自 manifest 读取，无硬编码 `1e-9` 类字面量

#### Scenario: wasm 对拍走相对容差

- **WHEN** cross-binding 对拍比较 wasm 与原生结果
- **THEN** 使用 manifest `core_tol` 相对容差（非 bit 级、非绝对容差）；
  原生三端同机互比 MUST bit 级

### Requirement: 铁律四 skrf 是 oracle 但主 CI 零 Python

scikit-rf 是数值权威，MUST 只出现在离线 `gen_golden.py`，golden 结果提交进
git。主 CI（cargo test / pytest / vitest）MUST 只读 `testdata/`，零 skrf
依赖。skrf 升级由每周 `golden-refresh` job 重生成 + diff 守护，数值漂移显式
暴露（golden-refresh 属阶段 1，本 spec 钉契约、落地见总体计划）。

#### Scenario: 主 CI 无 skrf

- **WHEN** 检查 `.github/workflows/ci.yml` 全部 job
- **THEN** 无任何安装或调用 scikit-rf 的步骤

### Requirement: 铁律五 域无关，z0 是端口属性

核心类型 MUST NOT 出现 `rf` 前缀，使用 `Port`/`Network`/`Circuit`/`Wave`
中性词。参考阻抗 `z0` MUST 是端口属性而非全局常量，且 MUST 支持复数
（对齐 skrf；Touchstone 选项行 `R` 原生支持标量/每端口列表/复数）。

#### Scenario: z0 不作全局常量

- **WHEN** code-review Standards 轴审查核心类型
- **THEN** 无硬编码 50Ω、无 RF 专属假设；z0 挂在 Port 上且类型为复数

### Requirement: 铁律六 大文件性能底线

50MB s4p 解析 < 100ms 是底线（memmap2 + rayon，原生端 Python/Node；浏览器
wasm 单线程回退场景阶段 3 实测定标后回写本 spec）。criterion 基准 MUST 进
CI，显著劣化（>20%）MUST 失败。

#### Scenario: 基准回归即红

- **WHEN** criterion 结果相对基线劣化超过 20%
- **THEN** bench job 失败（`scripts/bench_gate.py`）

### Requirement: 铁律七 覆盖率 100% 硬约束

四端（core/python/node/wasm）产码行覆盖率 MUST 100%，CI 低于 100% 即失败，
unit 层零豁免。唯一例外为结构性不可达代码（`unreachable!()`、平台专属分支、
防御性 error 转换），MUST 逐条显式标注豁免并写明理由（Rust
`#[coverage(off)]`、Python `# pragma: no cover`、TS/JS
`/* v8 ignore start/stop */`），MUST NOT 整文件/整目录批量豁免。100% 是下限
不是目标：数值正确性由 golden/property/cross-binding 三层负责。CI 强制：
`cargo llvm-cov`、`pytest-cov --cov-fail-under=100`、vitest `lines/branches:
100`。

#### Scenario: 未测代码即红

- **WHEN** 新增一行未被任何测试执行的产码
- **THEN** 对应覆盖率 job 失败（2026-09-27 已实测：run 36304682759）

#### Scenario: 豁免逐条标注

- **WHEN** 某段代码申请覆盖率豁免
- **THEN** 豁免标记紧邻该行且附理由，无批量/整文件豁免

### Requirement: 元规则 优先级与单一真相源

本 spec 优先级高于一切临时决定；spec/plan/tasks 与本 spec 冲突时改
spec/plan/tasks，不改铁律（修铁律走独立最高级变更并评估三端影响）。铁律
正文 MUST 只存于本 spec：`AGENTS.md` 只放通用行为准则与指针，不得重述铁律
正文；`openspec/config.yaml` context 只放指针与工件专属规则。语言约定：代码
注释与代码内文档（rustdoc/docstring/JSDoc）一律英文；OpenSpec 工件与规划
文档中文，结构标题与 SHALL/MUST 保持英文。

#### Scenario: 铁律正文唯一存放

- **WHEN** 检查 AGENTS.md 与 openspec/config.yaml
- **THEN** 二者对铁律只有链接/指针与工件规则，无铁律正文重述

### Requirement: 元规则 教学式文档与类型标注

每个公开函数/结构体/类 MUST 有 docs（rustdoc/docstring/JSDoc），跨模块逻辑
与非直观实现 MUST 有行内注释，目标：不懂 RF 的读者仅凭代码内文档即可看懂
程序为何如此编写。术语定义与公式 MUST 直接写进 docs（自包含）——编写以
权威术语源（`/config/GitHub/knowledge/RF/` 下 `S-Parameters for Signal
Integrity (2020)` 与 `Touchstone File Format Specification`）为准，但 MUST
NOT 以"见某书某章"代替内容。算法处 MUST 写明公式来源、近似/适用条件、
容差依据（引用 manifest key）。全部公开 API MUST 有完整静态类型标注（Python
全量 type hints 过 mypy/pyright；TS 禁无差别 `any`）。

#### Scenario: 缺 docs 即不完成

- **WHEN** code-review Standards 轴发现公开 API 缺 docs 或类型标注
- **THEN** 该 PR 判不完成

## 修订历史

（自 `Plan/constitution.md` v1.0–v1.7 原样迁入，历史记录不改写：）

- v1.7（2026-09-19）：新增铁律七「测试覆盖率 100% 是硬约束」——四端产码行覆盖 100%、unit 零豁免、不可达代码逐条标注豁免；由 CI 强制。
- v1.6（2026-09-17）：测试分层去编号——废除 L1–L4，改用 unit/property/golden/cross-binding；manifest 键 `l1_l2_tol` 改名 `core_tol`（纯改名不改语义）。全 Plan/ 文档 "§X.Y" 式章节引用改为 Markdown 标题跳转链接。
- v1.5（2026-09-17）：铁律三重写为「精度分层契约」——bit 级断言限同机同架构原生三端；跨平台/跨实现走 manifest 相对容差；Touchstone 契约定为 shortest-roundtrip；manifest 新增 `l1_l2_tol`。铁律五补「z0 支持复数」。
- v1.4（2026-09-17）：元规则新增「教学式文档与类型标注」。
- v1.4（2026-09-17）：铁律六底线明确适用于原生端（Python/Node），浏览器 wasm 单独定标。
- v1.3（2026-09-17）：元规则新增「单一真相源」——AGENTS.md 只放准则与指针；config.yaml context 改指针。
- v1.2（2026-09-16）：元规则新增「语言约定」。
- v1.1（2026-09-16）：铁律一轴顺序改为 `(nfreq, nports, nports)`，与 skrf `Network.s` 逐字节对齐。
- v1.0（2026-09-16）：初版，六条铁律。
