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

## 铁律三：容差集中在 manifest，精度分层是契约

- 所有数值容差**只在 `testdata/manifest.json` 定义**（含 `l1_l2_tol` 键，收纳 L1/L2 测试的
  默认容差），测试代码从 manifest 读取。禁止在 `core/tests`、`python/tests`、`node/tests`
  里各写各的 `1e-9`。三端读同一容差，精度标准不漂移。
- **精度分层契约**——浮点末位误差不可消除，"何时允许 bit 级断言"在此钉死：
  ① **bit 级断言只允许出现在同机同架构的 L4 原生三端互比**（core/python/node 加载同一份
     编译产物，指令序列相同，结果逐 bit 相同是可证明的；绑定层的 stride/转置/字节序错误
     是天文数字级偏差，bit 级断言正是抓这种胶水 bug 的）；
  ② **一切跨平台/跨实现的比较必须走 manifest 容差**（golden 在不同 CPU 上重读、
     wasm vs 原生）：IEEE 754 单次运算正确舍入且确定性，但 SIMD 分发路径不同
     （AVX2 vs 无 SIMD/simd128）导致加法顺序不同，末位 ulp 差异必然存在；
     wasm 对拍用**相对容差**，绝对容差在大值上误报；
  ③ **Touchstone 写出→读回是 bit 级**：写出契约为 shortest-roundtrip 格式化
     （ryu 类算法——能读回原值的最短十进制表示，往返无损可证明）。
     定长 15 位做不到 bit 级，旧"≥15 位有效数字"表述作废。
- 默认量级（详见《测试规划.md》§6）：解析变换往返 1e-12、级联 1e-11、FFT 时域 1e-9。
- 放宽任何容差都要在 manifest 里注明原因（如"wasm FFT 浮点差异"）。

## 铁律四：skrf 是 oracle，但主 CI 不跑 Python

- scikit-rf 是数值权威，但**只在离线 `gen_golden.py` 里出现**，golden 结果提交进 git。
- 主 CI（`cargo test` / `pytest` / `vitest`）只读 `testdata/`，**零 Python 依赖**——快、稳、可复现。
- skrf 升级由每周 `golden-refresh` job 重生成 + diff 守护，数值漂移显式暴露，不悄悄红主 CI。

## 铁律五：域无关，z0 是端口属性

- 核心类型**不出现 `rf` 前缀**，用 `Port`/`Network`/`Circuit`/`Wave` 中性词。
- 参考阻抗 `z0` 是**端口属性**，不是全局常量——这是 RF 算法透明复用到光学的地基。
- `z0` **支持复数**（对齐 skrf；Touchstone 选项行的 `R` 参考阻抗原生支持标量/每端口列表/复数）。
- 任何把 z0 硬编码为 50Ω、或引入 RF 专属假设的改动，都破坏核心定位，一律拒绝。

## 铁律六：大文件性能是立项理由，必须守住

- 50MB s4p 解析 < 100ms 是底线（memmap2 + rayon，原生端 Python/Node；
  浏览器 wasm 单线程回退场景单独定标，见总体计划 §2.3）。
- criterion 基准进 CI，显著劣化（>20%）即失败。
- "先实现再优化"对 netwave 不成立——大文件卡死正是重写它的动机。

## 元规则

- 本宪法优先级高于一切临时决定；spec / plan / tasks 与本宪法冲突时，**改 spec，不改宪法**（除非走正式修宪流程）。
- 每条铁律都应**可验证**：铁律二/三/六由 CI 强制，铁律一/四/五由 code-review 的 Standards 轴强制。
- **语言约定**：代码注释与代码内文档（rustdoc / docstring / JSDoc / 行内注释）一律**英文**；
  OpenSpec 工件（proposal/spec/design/tasks）与 `Plan/` 文档一律**中文**。OpenSpec 结构标题与
  SHALL/MUST 关键词保持英文。
- **单一真相源**：本宪法是全部硬约束的唯一正文。`AGENTS.md` 只放通用行为准则（Karpathy 四原则）
  与指向本文件的指针，**不得重述铁律正文**；`openspec/config.yaml` 的 context 同样只放指针与
  OpenSpec 工件专属规则（rules）。改铁律只改本文件一处。
- **教学式文档与类型标注**：每个公开函数/结构体/类必须有 docs（rustdoc / docstring / JSDoc），
  跨模块逻辑与非直观实现必须有行内注释，目标是**不懂 RF 的读者仅凭代码内文档即可看懂程序
  为何如此编写**：
  - 术语定义与公式**直接写进 docs**（自包含）：编写时以权威术语源为准——
    `S-Parameters for Signal Integrity (2020)` 与 `Touchstone File Format Specification`
    （位于 `/config/GitHub/knowledge/RF/`，各目录内 `术语表.md` 带行号路由）——
    但**不得以"见某书某章"代替内容**；读者没有这些书，必须把定义/公式总结成文档正文本身。
  - 算法处须写明：公式来源、近似/适用条件、容差依据（引用 manifest key）。
  - 文风：清楚、可读、简洁——解释"为什么"，不复述代码在做什么；宁少勿滥。
  - 全部公开 API 必须有完整静态类型标注（Rust 天然强制；Python 绑定必须全量 type hints，
    过 mypy/pyright；TS 绑定禁止无差别 `any`）。
  - 验收：code-review Standards 轴检查；公开 API 缺 docs/类型视为不完成。
- 修宪记录追加到本文件末尾的「修订历史」。

## 修订历史

- v1.5（2026-09-17）：铁律三重写为「精度分层契约」——bit 级断言限同机同架构 L4 原生三端；
  跨平台/跨实现（含 wasm）走 manifest 相对容差；Touchstone 写出契约定为 shortest-roundtrip
  （round-trip bit 级，废除"≥15 位有效数字"）；manifest 新增 `l1_l2_tol` 收纳 L1/L2 容差。
  铁律五补「z0 支持复数」表态。配套修订：总体计划 §2.5/§6/§7、测试规划 §4–§6/§10、
  功能覆盖规划（含修正 `R` 选项误标为"频率重采样"的事实错误）。
- v1.4（2026-09-17）：元规则新增「教学式文档与类型标注」——公开 API 必须有自解释 docs
  （术语/公式**直接写成文档正文**，权威术语源仅作编写依据，禁止"见某书某章"式引用，
  解释为何如此编写，清楚可读简洁）+ 完整静态类型标注（Python 全量 type hints，
  TS 禁无差别 `any`）。
- v1.4（2026-09-17）：铁律六底线明确适用于原生端（Python/Node），浏览器 wasm 单线程回退场景
  单独定标（见总体计划 §2.3）。不改变原生端约束，仅补充适用范围。
- v1.3（2026-09-17）：元规则新增「单一真相源」——AGENTS.md 只放通用行为准则与指针，
  不得重述铁律正文；config.yaml context 改指针。配套：新建仓库根 `AGENTS.md`（四原则壳），
  `openspec/config.yaml` context 由约束摘要改为三行指针。
- v1.2（2026-09-16）：元规则新增「语言约定」——代码注释/代码内文档用英文，OpenSpec 工件与
  `Plan/` 文档用中文。同步写入 `openspec/config.yaml` 的 context。
- v1.1（2026-09-16）：铁律一轴顺序由 `(nports, nports, nfreq)` 改为 `(nfreq, nports, nports)`，
  与 skrf `Network.s` 逐字节对齐，删除"转换约定"（转换退化为恒等 reinterpret）。
  理由：流式解析无转置、热路径矩阵连续、rayon 沿大轴负载均衡。四端布局同步。
- v1.0（2026-09-16）：初版，六条铁律。
