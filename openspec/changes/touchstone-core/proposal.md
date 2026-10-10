# Proposal

## Why

netwave 目前只有 `Frequency` 与 `Network` 骨架，没有任何 Touchstone 文件读写
能力——用户无法加载/保存 Touchstone 文件，整个工作流闭环缺了入口和出口。对标
scikit-rf `Network` 的读写职责需要下沉到 netwave 主类 `Touchstone`（解析、
域换算、写出、跨端 I/O），命名对齐 skrf、功能覆盖旧库 RF-Touchstone，
Network 立项时直接消费其产物，不重写解析。

## What Changes

- 新增 core `Touchstone` 主类：构造即解析完成（`fromText`/`fromFile`/`fromUrl`
  三工厂 + 纯数据构造器 `new Touchstone(frequency, data, z0, parameter, ...)`），
  持有 `Frequency` 轴、交错 f64 S 主数据、每端口实数 z0、元数据
  （`name`/`comments`/`version`/`parameter`）。
- 公开数据面：域快捷属性 `s`/`z`/`y`/`g`/`h`（复数视图，非 S 域现算）+
  统一访问器 `data(parameter?, format?)`（域×格式全组合，MA/DB 实数对）；
  换算函数全部私有。
- 写出：`writeTouchstone(parameter, format)` 吐文本（shortest-roundtrip）；
  `writeFile(path, parameter, format)` 原生端 core 落盘、浏览器端为 TS 壳
  平台胶（worker 渲染文本 + 私有 `write_path(path?)` 定名 → 克隆回主线程 →
  Blob 下载）；文件名扩展名永远拼真实 `.{parameter}{nports}p`。
- 静态函数：名字流水线三件套 `filenameFromPath`/`nameFromFilename`/
  `nportsFromFilename`（覆盖旧库 `getFilename`/`getBasename`/`parsePorts`；
  `filename` 一词全仓统一 = 含扩展名文件名）；
  `fromUrl` 原生端 reqwest、浏览器端 `web_sys::fetch`（core 内 cfg 门控）。
- 解析支持 Touchstone 1.0 + 1.1（单/每端口实数 z0）；频点边界纯由
  nports stride 定（token 流不整除即错，噪声行混入自然报错，与 SI/旧库
  同策）；重复频点报错、乱序静默排序；G/H 仅 2 端口。
- 修订 api-contract「无状态一次性变换 MUST 是模块级函数」条款：
  `Touchstone` 归入"持有解析结果的状态类"，三端类形态导出。
- 新增 typing：`TouchstoneParameter`/`TouchstoneFormat` enum +
  `TouchstoneError`（thiserror，三端映射），core 单源反射零手抄。

## Capabilities

### New Capabilities

- `touchstone-core`: Touchstone 文件（1.0/1.1）的解析、构造、域访问、写出、
  跨端 I/O 与文件名规则——`Touchstone` 类全部公开契约。

### Modified Capabilities

- `api-contract`: 修订「有状态对象用类、无状态变换用模块函数」——
  `Touchstone` 是持有解析结果的状态类（非模块级解析函数）；worker 命名空间
  新增 `"touchstone"` 路由（工厂经 `{handle:"touchstone", method:...}`）。

## Non-goals

- Touchstone 2.0/2.1 方括号语法（`[Port]`/`[Noise Data]`/`[Reference]`）；
  噪声参数识别/属性/计算（v1 遇噪声数据直接报错，不识别不跳过）。
- `port_names`（厂商注释方言）、HFSS 注释抠值、zip 包读取、
  `s_def`/`port_modes` 参考定义换算。
- a/t 参数（非文件域）与 skrf 笛卡尔积分量衍生面（`s_re`/`s_mag`/时域量）
  ——归 Network 计算层。
- `validate()`、`comments_after_option_line`、`format` 属性、`rRef`/`version`
  写出选项（各有已定裁决理由）。
- 大文件窗口化/流式 API（v1 用扁平自寻址 + 切片）。
- `Network.fromTouchstone` 桥的实现（Network 立项时承接，本 change 只定契约）。

## Impact

- 新代码：`core/src/touchstone.rs`（类 + 私有解析/换算/渲染家族）；
  `python/src/lib.rs`、`typescript/native|wasm/src/lib.rs`、
  `typescript/src/index.browser.ts`/`index.node.ts`/`netwave.worker.ts`
  增加 `Touchstone` 绑定与 `"touchstone"` 命名空间路由。
- 新依赖：reqwest（rustls）+ tokio 进原生 crate（cfg 门控 native；浏览器
  wasm 零影响，走 `web_sys::fetch`）。
- 文档：`Plan/Touchstone核心API规划.md` 全部裁决落地；`功能覆盖规划.md`
  噪声表述修正；api-contract delta 随本 change 提交。
- 受引用铁律：一（交错 f64 布局）、二（TDD）、三（manifest 容差）、
  六（大文件流式）、八（常驻 worker 数据权威）、九（协议钩子 async）、
  十（skrf 兼容优先）、十一（绑定薄壳）、十二（名字单源）。
