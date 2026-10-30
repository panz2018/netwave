# project-governance Specification Delta

## MODIFIED Requirements

### Requirement: 铁律一 数据布局是契约

核心数据 MUST 永远是 `(nfreq, nports, nports)` 交错复数扁平 f64
（complex128，`[re, im, re, im, ...]`），与 scikit-rf `Network.s` 的内存
布局逐字节相同；对 skrf/numpy 的零拷贝即同一块内存的 reinterpret，无需
转换、无 strided 拷贝。绑定层 MUST NOT 逐元素搬运复数对象。钉死此顺序的
理由与代价分析属实现决策，只存账本 `LL-072`，本 spec 不重述。

#### Scenario: 布局逐字节一致

- **WHEN** 任一绑定层取 core 缓冲视图
- **THEN** 视图内存与 skrf `Network.s` 同形状下逐字节相同（reinterpret，零转换）

#### Scenario: 布局变更四端同步

- **WHEN** 有人提议更改数据布局
- **THEN** 该变更等同修改本 spec（最高级变更），core/python/node/wasm 必须
  同一 PR 同步改、同步发版，否则 code-review Standards 轴拒绝

### Requirement: 铁律三 容差集中在 manifest，精度分层是契约

跨端阅卷的数值容差 MUST 只在 `oracle/manifest.json` 定义（`core_tol` 键），
阅卷源码 MUST NOT 出现字面量容差。core 内部 unit/property 测试容差为测试
自述常量（`const`），与 oracle 零依赖——容差集中治理的边界是跨端阅卷层，
不含 core 自校验层。放宽任何容差 MUST 在 manifest 注明原因。精度分层
（bit 级适用范围、跨平台相对容差、写出读回 bit 级）与默认量级属阅卷机制，
唯一正文见 `oracle-harness` spec「精度分层」，本 spec 不重述。

#### Scenario: 测试代码无字面量容差

- **WHEN** 检查 oracle 阅卷脚本
- **THEN** 数值比较的容差全部来自 manifest 读取，无硬编码 `1e-9` 类字面量

#### Scenario: core 自校验容差为自述常量

- **WHEN** 检查 core 的 unit/property 测试源码
- **THEN** 容差以测试内 `const` 常量声明并注明适用层；core 测试不读
  `oracle/manifest.json`，对 oracle 零依赖

#### Scenario: wasm 对拍走相对容差

- **WHEN** cross-binding 对拍比较 wasm 与原生结果
- **THEN** 使用 manifest `core_tol` 相对容差（非 bit 级、非绝对容差）；
  原生三端同机互比 MUST bit 级

### Requirement: 铁律四 skrf 是 oracle 但主 CI 零 Python

scikit-rf 是数值权威，MUST 只出现在 `oracle/` 子项目内，各端主测试路径
（cargo test / pytest / vitest）MUST 零 skrf 依赖。golden 数据 MUST NOT
提交进 git——由 oracle 在 CI 现算，只活在 gitignore 的 `oracle/tmp/golden/`
（阅后即焚）。skrf 版本 MUST 由 `oracle/uv.lock` 钉死，升级 = 显式改 lock
的 PR。CI 侧 job 编排与落地时序属 CI 机制，唯一正文见 `ci-matrix` spec
「主 CI 零 Python 运行时依赖」与 `oracle-harness` spec，本 spec 不重述。

#### Scenario: 主 CI 无 skrf

- **WHEN** 检查 `.github/workflows/ci.yml` 的 cargo test / pytest / vitest
  步骤
- **THEN** 无任何安装或调用 scikit-rf 的步骤（skrf 亦只出现在 oracle 阅卷
  步骤，各端步骤保持零 skrf）

#### Scenario: golden 不入库

- **WHEN** `git ls-files` 检查受版本控制的文件
- **THEN** 无任何 golden 数值 `.bin` 被跟踪；golden 只存在于
  `oracle/tmp/golden/`（gitignore）

### Requirement: 铁律六 大文件性能底线

原生端（Python/Node）解析 50MB s4p MUST < 100ms；浏览器 wasm 单线程回退
场景待 wasm 性能定标实测定标后回写本 spec。基准回归阈值与 CI job 编排属
CI 机制，唯一正文见 `ci-matrix` spec「criterion 基准进 CI」，本 spec 不重述。

#### Scenario: 基准回归即红

- **WHEN** criterion 结果相对基线劣化超过 `ci-matrix` 规定的阈值
- **THEN** bench job 失败（`scripts/bench_gate.py`）

### Requirement: 铁律七 覆盖率 100% 硬约束

四端（core/python/node/wasm）产码行覆盖率 MUST 100%，CI 低于 100% 即失败，
unit 层零豁免。唯一例外为结构性不可达代码，MUST 逐条显式标注豁免并写明理由，
MUST NOT 整文件/整目录批量豁免。100% 是下限不是目标：数值正确性由
golden/property/cross-binding 三层负责。覆盖率 MUST 按 crate/包归属各自度量，
MUST NOT 用 `llvm-cov report` 默认路径做 100% 闸门，也 MUST NOT 用
`--workspace` 把绑定 crate 的 core 副本并入 core 度量。结构性不可达代码的
类别、各语言豁免标记语法、闸门命令与工具合并语义属工具机制，唯一正文见
`ci-matrix` spec「覆盖率门槛生效」与账本 `LL-020`/`LL-057`，本 spec 不重述。

#### Scenario: 未测代码即红

- **WHEN** 新增一行未被任何测试执行的产码
- **THEN** 对应覆盖率 job 失败

#### Scenario: 豁免逐条标注

- **WHEN** 某段代码申请覆盖率豁免
- **THEN** 豁免标记紧邻该行且附理由，无批量/整文件豁免

#### Scenario: 跨 crate 重复计数即红

- **WHEN** core 覆盖率经 `--workspace` 合并统计（绑定二进制内的 core 副本
  被重复计入）
- **THEN** 该度量方式违规；改用 `-p netwave` 单 crate 度量

#### Scenario: 工具机制解释不入宪法

- **WHEN** 需要记录某覆盖率工具的行合并语义、计数口径或实测数字
- **THEN** 写入 lessons-learned 账本对应 scope 分片，本 spec 只留契约句与
  指向该 LL 的指针；同一事实不在两层同时出现正文

### Requirement: 铁律八 常驻 worker 数据权威与单点所有权

浏览器端 wasm 实例 MUST 只存在于一个常驻 worker 内：主线程 MUST NOT init wasm、
MUST NOT 持有任何数据副本。任一时刻每份数据 MUST 只有唯一所有者（单点所有权），
跨线程移动 MUST 经显式 transfer，MUST NOT 存在隐式复制路径。worker MUST 常驻
至页面关闭，不做按需起停，且为**模块级单例**：同一页面内无论 import 多少次
库入口、创建多少库实例（句柄）， MUST 共用同一 worker。数值容差不因本铁律
改变，仍引用 manifest `core_tol`（铁律三）。transfer 零拷贝机制、元数据搭
结果便车、输入不消耗等实现契约的唯一正文见 `zero-copy-roundtrip` spec
「异步与 Worker 边界契约」；跨 realm 内存生命周期（registry 驱动释放、
共享不误删、显式 `drop()` 逃生口、node napi finalizer）见 `memory-lifecycle`
spec。本 spec 不重述。

#### Scenario: 主线程无 wasm

- **WHEN** 真浏览器测试（vitest browser mode，Chromium）加载浏览器端入口并执行
  一次计算
- **THEN** 主线程 globalThis 上不存在已初始化的 wasm 实例/导出命名空间
- **AND** 计算在常驻 worker 内完成，结果经 transfer 回主线程

#### Scenario: 单点所有权与显式 transfer

- **WHEN** 主线程经 `fromData` 把 buffer 交给 worker（`data` 进 transfer list）
  后再读原 buffer
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

### Requirement: 铁律九 跨端协议钩子

每个公开类 MUST 在全部存在该对象的端提供统一显示串，格式
`ClassName(摘要)`（如 `Frequency(1.0-5.0 GHz, 3 pts)`），各端 MUST 使用同一
字符串内容。入口按语言原生协议命名，MUST NOT 自造跨语言同名方法（Python 不
写 `toString()`，JS 不写 `__str__`）。跨端统一惯用法 `await x.toString()`
MUST 在 node 与浏览器同时成立。逐语言入口形态、长度协议与协议保留名清单属
API 面细节，唯一正文见 `api-contract` spec「跨端显示串与协议保留名」，
本 spec 不重述。

#### Scenario: print 自动触发

- **WHEN** 在 Rust/Python/Node 中 `println!("{f}")` / `print(f)` / `console.log(f)`
- **THEN** 输出统一显示串 `ClassName(摘要)`，无需显式调用转换方法

#### Scenario: 跨端 await toString 一致

- **WHEN** 同一段 `await x.toString()` 分别跑在 node 与浏览器
- **THEN** 两端返回同一显示串

### Requirement: 铁律十 scikit-rf API 兼容优先

公开 API 的命名、参数、返回值与语义 MUST 默认对齐 scikit-rf 同名概念（如
`from_f`、`f`/`f_scaled`/`unit`/`npoints`/`copy`）。偏离 MUST 在对应 change
的 design.md 写明更强收获（能力增量或契约强化），否则一律兼容。本条是
**机械映射豁免**的唯一定义处：TS camelCase（`fScaled` ↔ `f_scaled`）、
Rust/Python snake_case、语言原生协议钩子（`__str__`/`toString`/
`inspect.custom`）、worker 隔离导致的 async 化（铁律八所致）不算偏离；
其余铁律引用本条，不重述豁免清单。

#### Scenario: 偏离须有立案收获

- **WHEN** 新公开 API 与 skrf 同名概念命名或语义不同
- **THEN** design.md 含"更强收获"论证，code-review Standards 轴据此判定；
  无论证即打回

### Requirement: 铁律十二 API 名字单源，禁别名壳

公开 API 的名称（方法/函数/属性）在 core/Python/node/浏览器 MUST 是同一个名字。
统一 MUST 靠**直接命名实现**达成：core 里该函数就叫这个名字，绑定宏原样搬运同名
方法——MUST NOT 在任何层添加转发到另一名字的别名函数/属性来"凑"统一。改名 MUST
连实现带名字一起改（重命名），MUST NOT 保留旧名作兼容别名（无 deprecated 转发、
无 `free() { this.drop() }` 式垫片）。机械映射豁免沿用铁律十定义，本条不重述。

工具链生成物名字不受本铁律管辖（如 wasm-bindgen 为导出类自动生成的 `free()`），
但生成物 MUST NOT 出现在用户可见面：用户可见面只允许那个唯一的名字。

本铁律是铁律十一（绑定薄壳）在名字维度的补集：铁律十一禁壳内有逻辑，本铁律禁
壳内有第二个名字。

#### Scenario: 别名壳即打回

- **WHEN** code-review Standards 轴在任一端发现转发定义：Rust `fn free` 体内
  调 `self.drop()`，或 TS `drop()` 体内 `return this.free()`
- **THEN** 打回：要求把实现直接命名为统一名并删除转发

#### Scenario: 改名不留旧别名

- **WHEN** 公开 API 改名（如 `release`→`drop`）
- **THEN** 同一 PR 内旧名在全部端、测试、文档与生成物（`.pyi`/`.d.mts`）中
  消失，无兼容别名残留

#### Scenario: 三端动词集合相等即绿

- **WHEN** CI 运行 `scripts/check_verbs.py` 提取三端公开动词集合
- **THEN** 三端集合逐名相等（机械 camelCase 映射后比较），任一名字漂移即失败

#### Scenario: 生成物不上浮公开面

- **WHEN** 检查浏览器/node 用户可见导出面
- **THEN** 不含 wasm-bindgen 生成物名（`free`）；该名字仅存在于 worker 内部
  对生成物的调用点

#### Scenario: 统一形态为实例方法

- **WHEN** 检查三端手动释放的调用形态
- **THEN** 公开形态统一为实例方法 `obj.drop()`（浏览器主线程持 `Touchstone`/
  `Frequency` 壳实例，壳内是数字 handle）；`drop(handle)` 仅作为 worker 内部
  `postMessage` 命令形态存在，MUST NOT 上浮为公开 API

### Requirement: 铁律十五 构造入口用 fromX 工厂，公开面禁裸构造器

四端用户面全部类的构造入口 MUST 是 `fromX` 静态工厂（名单见下方指针），
且在 core/Python/node/浏览器四端 MUST 公开可达且同名（机械映射豁免沿用
铁律十）。裸 `new`/构造器 MUST NOT 出现在任何端公开面：Rust core MUST NOT
有 `pub fn new`，Python MUST NOT 有 `#[new]`，node MUST NOT 有
`#[napi(constructor)]`，浏览器壳 MUST NOT 有公开 `constructor`。
浏览器壳内部 `private constructor(handle)` 是壳持 handle 的传输细节、非构造入口，
不受本铁律管辖。管辖范围 = 四端用户面全部类（机制规则不点名），内部 Rust
结构（`Registry` 等资源表）不受管辖。工厂名单属 API 面细节，唯一正文见
`api-contract` spec「fromX 构造入口名单」，本 spec 不重述。

#### Scenario: 裸构造器即打回

- **WHEN** code-review Standards 轴在任一端公开面发现 `pub fn new`/`#[new]`/
  `#[napi(constructor)]`/公开 `constructor`
- **THEN** 打回：要求改名为 `fromX` 静态工厂并四端同步

#### Scenario: 构造入口四端同名

- **WHEN** `check_verbs.py` 提取四端某类的构造入口名
- **THEN** 四端集合逐名相等（机械 camelCase/snake_case 映射后比较），且无裸
  构造器名（`new`/`constructor`）出现在公开面

#### Scenario: 壳内私有 handle 构造器豁免

- **WHEN** 检查浏览器壳 `constructor`
- **THEN** 仅存在 `private constructor(handle)`（内部传输细节），无公开构造器；
  用户构造一律经 `fromX` 工厂

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

### Requirement: 元规则 开发者文档引用自解释

开发者文档（`openspec/specs/`、`AGENTS.md`、`CONTRIBUTING.md`、`Plan/`）中的
引用 MUST 一眼可懂、不依赖读者再去定位可能已归档或终将删除的文档：跨文档引用
MUST 用标题跳转链接（`[标题](文件.md#锚点)`）而非章节序号或代号；指向归档的
引用 MUST 是完整路径且该目录 MUST 现存（改名时全仓同步更新）；MUST NOT 以
「见某规划文档第 N 节」「跟踪于某待决清单」等需二次定位的表述替代可直接读出
的结论。路线图数字代号（中文「阶段」后接数字、英文 `stage`/`phase` 后接数字）
MUST NOT 出现在任何 Markdown。本规则 MUST 门禁化：`scripts/check_md.py`
（命令 `pnpm check:md`）扫描全仓 Markdown，扫描范围与命令唯一定义处见
CONTRIBUTING.md；治理 spec 本文、lessons-learned 账本与 archive 均不豁免——
治理 spec 正文描述被禁词时 MUST 用描述性表达（不含字面触发词），使门禁可
零豁免扫描全仓。

#### Scenario: 文档面阶段代号命中即红

- **WHEN** 任一 Markdown（含 `openspec/specs/`、`Plan/`、
  `openspec/changes/archive/`）出现「阶段」后接数字或英文 `stage`/`phase`
  后接数字
- **THEN** `pnpm check:md` 失败（`scripts/check_md.py` 命中报告）

#### Scenario: 归档指针指向不存在目录即红

- **WHEN** Markdown 出现行内代码形态的 `openspec/changes/archive/<name>/`
  完整路径而该目录不存在
- **THEN** `pnpm check:md` 失败（改名后残留旧路径被捕获）

#### Scenario: 治理 spec 反例不触发自身门禁

- **WHEN** 治理 spec 正文描述被禁止的考古词
- **THEN** 以描述性语言表达（如"英文阶段词后接数字"），不含字面触发词，
  `pnpm check:md` 通过

#### Scenario: 引用需二次定位即打回

- **WHEN** code-review Standards 轴发现开发者文档用章节序号、讨论代号或
  "见某规划文档"式表述指代结论，而结论未就地写出
- **THEN** 判不完成，要求改写为自包含表述或标题跳转链接

### Requirement: 元规则 知识产权合规

本项目算法与 API 借鉴第三方公开作品，知识产权合规是发布前置硬约束：
① 借鉴 MUST clean-room——只取算法思想、数学方法、接口语义与规范格式，
实现 MUST 用目标语言习惯独立重写；MUST NOT 逐行翻译或结构性照搬第三方
源码（变量命名、函数切分、注释文字、组织顺序）。② GPL 源 MUST NOT 有
任何代码或逐行翻译件进入本仓，仅 MAY 参考其输入输出定义与算法思想；
GPL 源名单属事件级事实，唯一正文见账本许可表 `LL-029`。③ 借鉴第三方算法的函数
MUST 在 rustdoc/docstring 标注算法出处（书目 DOI、规范节名或上游项目
URL）——出处标注是独立实现的证据链。④ 第三方代码或派生数据进入分发物
时其声明 MUST 随分发（见 license-compliance spec）。⑤ 受版权保护的书籍
MUST NOT 复制原文/图表进本仓文档，仅 MAY 引用思想与书目信息。⑥ 商标
（Touchstone®）MUST 尊重，用法见 license-compliance spec。

#### Scenario: GPL 代码混入即事故

- **WHEN** review 发现任何源自 GPL 许可上游项目的代码或逐行翻译件
- **THEN** 立即移除并打回；该 LL 计入复发记录

#### Scenario: 借鉴实现标注出处

- **WHEN** 新算法函数借鉴自第三方（书/开源项目/规范）
- **THEN** 函数级 rustdoc/docstring 含出处标注，review Standards 轴
  逐条核对

#### Scenario: 参考前先查许可

- **WHEN** agent 或人准备参考某第三方项目/书籍
- **THEN** 先在账本许可表核对其 license；GPL 源只读思想不开代码

## ADDED Requirements

### Requirement: 铁律编号是名字，编号退役不复用

铁律编号是规则的**名字**而非目录位置：新增铁律取当前最大号 +1，铁律退役
或迁出后其编号 MUST NOT 复用、MUST NOT 重排其余编号，使任意历史引用
（账本、归档 change、review 记录）中的编号永久指向同一规则。文档
MUST NOT 以编号范围（"铁律一~N"）描述铁律集合——范围随增删失效，
用"全部铁律"或点名具体规则。

#### Scenario: 退役编号不复用

- **WHEN** 某条铁律被废除或整条迁出本 spec
- **THEN** 其编号留空，后续新增铁律不占用该号，其余铁律编号不变

#### Scenario: 文档禁写编号范围

- **WHEN** 常驻文档需要指代全部铁律
- **THEN** 写"全部铁律"或点名规则，不写随增删失效的编号区间

### Requirement: 文档语言约定唯一正文在本 spec

文档语言约定的契约级正文 MUST 只存于本 spec 元规则「优先级与单一真相源」
末段；`AGENTS.md` 等 agent 行为准则文档对此只放指针，MUST NOT 重述约定正文。

#### Scenario: 行为准则不重述语言约定

- **WHEN** 检查 `AGENTS.md` 语言相关条目
- **THEN** 该条只含对话行为准则（镜像用户语言、先大白话）与指向本 spec 的
  指针，无文档语言规则正文重述
