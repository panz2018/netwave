# NetWave 项目宪法（Constitution）

> 本文件是 netwave 的**不可协商铁律**。它存在的唯一理由：智能体跨会话失忆、会合理化跳过测试、
> 无法自证浮点正确。把这些约定钉在磁盘上，任何一次会话、任何人（或 agent）动手前都必须遵守。
> **修改本文件 = 最高级别的变更**，必须显式说明理由并评估三端影响。
>
> 借鉴 spec-kit 的 constitution 概念，但不引入其 CLI；纯文档，零依赖。

## 铁律一：数据布局是契约，不是实现细节

- 核心数据**永远是 `(nfreq, nports, nports)` 交错复数扁平 f64**（complex128，`[re, im, re, im, ...]`），
  与 scikit-rf `Network.s` 的内存布局**逐字节相同**——对 skrf/numpy 的零拷贝就是同一块内存的
  reinterpret，**无需转换、无 strided 拷贝**。
- 选此顺序的理由（一开始钉死，不可后改）：
  ① Touchstone 按频率逐行存储，流式解析 = 线性拷贝无转置；
  ② 热路径（S↔Z/Y/T/ABCD、级联、mixed-mode）逐频点做 (p×p) 矩阵运算，每频点矩阵是连续块；
  ③ 沿大轴 `nfreq` 切分给 rayon，任务多且连续，负载均衡。
- 代价：单条 trace（固定 p,q 扫频）内存跨步——属显示/IO 路径，非热路径，按需给跨步视图或转置。
- 改数据布局 = 改本宪法 = **core / python / node / wasm 四端必须同一 PR 同步改、同步发版**。
- 绑定层**禁止逐元素搬运复数对象**（旧 rf-touchstone 的 `Complex[][][]` 是反面教材）。
  零拷贝是卖点，任何让零拷贝退化为逐元素拷贝的改动一律拒绝。

## 铁律二：数值 API 无失败测试不许写实现（TDD 铁律）

- 任何产生/变换复数数值的函数（S↔Z/Y/T/ABCD、级联、mixed-mode、FFT 时域、Touchstone 解析），
  **必须先有一条会失败的测试，看到它 red，再写实现**。
- "这个变换显然正确""我手动验过了"——都是合理化。**red 先于 green，没有例外。**
- 期望值来源必须是**独立真值**：skrf 预生成的 golden、教科书闭式解、物理不变量。
  **禁止用被测代码自己算期望值**（tautological test，永远抓不到 bug）。

## 铁律三：容差集中在 manifest，禁止散落

- 所有数值容差**只在 `testdata/manifest.json` 定义**，测试代码从 manifest 读取。
- 禁止在 `core/tests`、`python/tests`、`node/tests` 里各写各的 `1e-9`。三端读同一容差，精度标准不漂移。
- 默认量级（详见《测试规划.md》§6）：解析变换往返 1e-12、级联 1e-11、FFT 时域 1e-9、跨绑定对拍 bit 级。
- 放宽任何容差都要在 manifest 里注明原因（如"wasm FFT 浮点差异"）。

## 铁律四：skrf 是 oracle，但主 CI 不跑 Python

- scikit-rf 是数值权威，但**只在离线 `gen_golden.py` 里出现**，golden 结果提交进 git。
- 主 CI（`cargo test` / `pytest` / `vitest`）只读 `testdata/`，**零 Python 依赖**——快、稳、可复现。
- skrf 升级由每周 `golden-refresh` job 重生成 + diff 守护，数值漂移显式暴露，不悄悄红主 CI。

## 铁律五：域无关，z0 是端口属性

- 核心类型**不出现 `rf` 前缀**，用 `Port`/`Network`/`Circuit`/`Wave` 中性词。
- 参考阻抗 `z0` 是**端口属性**，不是全局常量——这是 RF 算法透明复用到光学的地基。
- 任何把 z0 硬编码为 50Ω、或引入 RF 专属假设的改动，都破坏核心定位，一律拒绝。

## 铁律六：大文件性能是立项理由，必须守住

- 50MB s4p 解析 < 100ms 是底线（memmap2 + rayon）。
- criterion 基准进 CI，显著劣化（>20%）即失败。
- "先实现再优化"对 netwave 不成立——大文件卡死正是重写它的动机。

## 元规则

- 本宪法优先级高于一切临时决定；spec / plan / tasks 与本宪法冲突时，**改 spec，不改宪法**（除非走正式修宪流程）。
- 每条铁律都应**可验证**：铁律二/三/六由 CI 强制，铁律一/四/五由 code-review 的 Standards 轴强制。
- **语言约定**：代码注释与代码内文档（rustdoc / docstring / JSDoc / 行内注释）一律**英文**；
  OpenSpec 工件（proposal/spec/design/tasks）与 `Plan/` 文档一律**中文**。OpenSpec 结构标题与
  SHALL/MUST 关键词保持英文。
- 修宪记录追加到本文件末尾的「修订历史」。

## 修订历史

- v1.2（2026-09-16）：元规则新增「语言约定」——代码注释/代码内文档用英文，OpenSpec 工件与
  `Plan/` 文档用中文。同步写入 `openspec/config.yaml` 的 context。
- v1.1（2026-09-16）：铁律一轴顺序由 `(nports, nports, nfreq)` 改为 `(nfreq, nports, nports)`，
  与 skrf `Network.s` 逐字节对齐，删除"转换约定"（转换退化为恒等 reinterpret）。
  理由：流式解析无转置、热路径矩阵连续、rayon 沿大轴负载均衡。四端布局同步。
- v1.0（2026-09-16）：初版，六条铁律。
