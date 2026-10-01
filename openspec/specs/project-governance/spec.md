# project-governance Specification

## Purpose

定义 netwave 全部不可协商硬约束（七条铁律 + 元规则）的唯一真相源 spec：
数据布局、TDD、容差分层、skrf 边界、z0 定位、性能底线、覆盖率与文档语言
约定，供四端实现、CI 门禁与 code-review 双轴共同引用。

## Requirements

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
`cargo llvm-cov`、`pytest-cov --cov-fail-under=100`、
vitest `lines/branches: 100`。

#### Scenario: 未测代码即红

- **WHEN** 新增一行未被任何测试执行的产码
- **THEN** 对应覆盖率 job 失败（已实测：run 36304682759）

#### Scenario: 豁免逐条标注

- **WHEN** 某段代码申请覆盖率豁免
- **THEN** 豁免标记紧邻该行且附理由，无批量/整文件豁免

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
权威术语源（`/config/GitHub/knowledge/RF/` 下
《S-Parameters for Signal Integrity (2020)》与
《Touchstone File Format Specification》）为准，但 MUST
NOT 以"见某书某章"代替内容。算法处 MUST 写明公式来源、近似/适用条件、
容差依据（引用 manifest key）。全部公开 API MUST 有完整静态类型标注（Python
全量 type hints 过 mypy/pyright；TS 禁无差别 `any`）。

#### Scenario: 缺 docs 即不完成

- **WHEN** code-review Standards 轴发现公开 API 缺 docs 或类型标注
- **THEN** 该 PR 判不完成

### Requirement: 元规则 文档受众分层

文档按变更级别分三层，内容 MUST 落入对应层：① 契约级决定（改动会波及已发布
代码/跨端契约者）MUST 入 governance spec，走最高级变更；② agent 行为准则
（约束执行动作而非系统状态者）MUST 入 AGENTS.md，保持精简（准则+指针，
MUST NOT 重述 spec 正文与内容清单细节）；③ 事件级事实（踩坑、实现决策、
人工纠正）MUST 只入 lessons-learned 账本。同一事实 MUST NOT 跨层重复。各
文档的内容分配清单属第②层执行细节，只列于 AGENTS.md 文档地图，清单增删
不触发本 spec 变更。

#### Scenario: 新事实正确归层

- **WHEN** 产生一条新信息（坑/决定/准则/契约）
- **THEN** 按判据归入唯一层，其余层不出现其正文

#### Scenario: 坑只进账本

- **WHEN** 新增环境坑或实现决策记录
- **THEN** 仅出现在 lessons-learned 账本，README/CONTRIBUTING 无新增坑节

#### Scenario: 清单调整不动宪法

- **WHEN** 内容分配清单需要调整（新增目录/章节改归属）
- **THEN** 只改 AGENTS.md 文档地图，本 spec 不动

### Requirement: 元规则 知识产权合规

本项目算法与 API 借鉴第三方公开作品，知识产权合规是发布前置硬约束：
① 借鉴 MUST clean-room——只取算法思想、数学方法、接口语义与规范格式，
实现 MUST 用目标语言习惯独立重写；MUST NOT 逐行翻译或结构性照搬第三方
源码（变量命名、函数切分、注释文字、组织顺序）。② GPL 源（唯一已知：
SignalIntegrity，GPL-3.0-or-later）MUST NOT 有任何代码或逐行翻译件进入
本仓，仅 MAY 参考其输入输出定义与算法思想。③ 借鉴第三方算法的函数
MUST 在 rustdoc/docstring 标注算法出处（书目 DOI、规范节名或上游项目
URL）——出处标注是独立实现的证据链。④ 第三方代码或派生数据进入分发物
时其声明 MUST 随分发（见 license-compliance spec）。⑤ 受版权保护的书籍
MUST NOT 复制原文/图表进本仓文档，仅 MAY 引用思想与书目信息。⑥ 商标
（Touchstone®）MUST 尊重，用法见 license-compliance spec。

#### Scenario: GPL 代码混入即事故

- **WHEN** review 发现任何源自 SignalIntegrity 的代码或逐行翻译件
- **THEN** 立即移除并打回；该 LL 计入复发记录

#### Scenario: 借鉴实现标注出处

- **WHEN** 新算法函数借鉴自第三方（书/开源项目/规范）
- **THEN** 函数级 rustdoc/docstring 含出处标注，review Standards 轴
  逐条核对

#### Scenario: 参考前先查许可

- **WHEN** agent 或人准备参考某第三方项目/书籍
- **THEN** 先在账本许可表核对其 license；GPL 源只读思想不开代码
