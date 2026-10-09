# Touchstone 核心 API 规划

> netwave 中 `Touchstone` 是主类（区别于 scikit-rf：skrf 的 `Touchstone` 只是
> 读取辅助类，功能主体在 `Network`）。netwave 把 skrf `Network` 中与 Touchstone
> 文件读写相关的职责下沉到 `Touchstone` 类，属性名与语义尽量对齐 skrf `Network`，
> 保证 skrf 用户低成本迁移；Network 立项时直接消费 `Touchstone` 的产物，不重写解析。
>
> 对标原则：功能对齐旧库 RF-Touchstone（功能覆盖，不要求函数名一致）；
> 命名对齐 skrf `Network`；标准语法以 Touchstone File Format Specification
> （v2.1 文档同时收录 1.0/1.1 规则）为准。

## 标准核实结论（对照 Touchstone File Format Specification）

- **`[Port]` 端口名不是任何版本的正式语法**。规范全文无 `[Port]` 关键字；
  skrf 的 `port_names` 实际是从厂商注释惯例抠出来的（`! Port[1] = Name`、
  Sigrity `! Name::Net`，见 skrf `io/touchstone.py` 的 `_parse_port`）。
  **v1 决策：不做 `port_names`**——非标准方言，等真实需求出现再作为
  厂商兼容扩展评估。
- **噪声参数在 1.0/1.1 就存在**，不是 2.x 独有。规范 Noise Parameter Data 节
  原文：噪声参数只允许出现在 2 端口文件，1.0/1.1 文件中直接跟在网络参数数据
  之后（每行 5 列：频率、NFmin(dB)、Γopt 模、Γopt 角、Rn），靠"频率开始
  变小"识别噪声段起点。**只有 `[Noise Data]`、`[Number of Noise Frequencies]`
  两个方括号关键字是 2.0/2.1 专属**（原文 "not permitted in Version 1.0 and
  Version 1.1 files"）。
  `功能覆盖规划.md` 中"噪声数据行（`[Number of Noise Frequencies]`）"的表述
  有误，需修正为"1.0/1.1 的 2 端口文件尾部噪声行"。
  **v1 决策：不支持噪声**——旧库 `touchstone.ts` 全文无 noise（实证），故 netwave
  v1 不设 `noise`/`noise_freq` 属性；解析时遇到噪声行**静默跳过、不报错**，
  属性与计算随噪声模块整体延后。

## 已定裁决（本轮对话拍板）

- `f` 不另存变量：`Touchstone` 内部持有 `Frequency` 实例，`f` 是转发 property；
  频率轴唯一权威在 `Frequency`（api-contract：主数据恒 f64 Hz，解析时换算）。
- 不保存 `resistance`/`reference` 原始值：`#` 选项行 `R`（标量/每端口）
  解析时统一归一成每端口实数数组，只存 `z0` 一份。
- **z0 恒实数（规范实证，修正早前"复数 z0"误判）**：规范原文 v1.1 的 R 是
  "p **real, positive numbers**"（每端口实数）；v2.x `[Reference]` 节明文
  "**complex and imaginary impedance values are not supported**"；混合模式节
  重申 "complex reference impedances are not supported"。**任何版本都不存在
  复数参考阻抗**。z0 合法形状仅两种：1.0 = 单实数全端口共用；1.1 = nports
  个实数按端口序。内部存储 = 每端口 f64 实数数组；构造器收标量或实数数组
  （三端同形，JS 无复数歧义自然消失）。未来 v2.x 扩展仍足实数域。
- 不保存 `frequency_unit`：单位是 `Frequency.unit` 元数据，`Touchstone` 不复制。
- 不保存 `frequency_nb`：频点数走 `f.npoints`，派生量不双存。
- 不引入 `filename`：文件来源名统一用 skrf `Network` 的 `name`。
- 放弃 `comments_after_option_line`：注释只留 `comments` 一个口子，
  写出不承诺注释位置还原。
- `from_url` 要做：三端统一入口（浏览器 fetch 的 CORS 是用户站点责任，
  错误原样抛出；实现路线见「I/O 归属」节）。
- 旧库对齐口径 = **功能 100% 覆盖**，不要求函数名/签名一致；
  `fromUrl` 等按新 API 重新实现即可。
- 不设 `validate()`：skrf 无此方法；旧库有是因为其 setter 允许拼出半成品状态，
  netwave 构造即解析完成，非法状态构造不出来，一致性由解析器抛错兜底。
- 只保存 `s` 主数据：文件为 Y/Z/G/H 时解析时即换算成 S 存储（对齐 skrf——
  skrf `Network` 只存 `s`，`y`/`z` 为现算 property）；`parameter` 仅记录文件
  原始类型作元数据。
- 域快捷属性全留 + 统一访问器分工（合并原则）：公开面同时有域快捷属性
  `s`/`z`/`y`/`g`/`h`（复数 `(nfreq, nports, nports)` 视图，底层扁平 f64
  存储，对齐 skrf `Network` 同名公开属性，
  实证 network.py:1046–1254）与统一访问器 `data(parameter?, format?)`
  （域×格式全组合，要 MA/DB 实数对时才需要）。不拆 `s_ri`/`s_ma`/`z_ri`…
  20 个格式属性——格式维度只走 `data()`。换算函数全部私有；存储仍只有
  `s` 一份，非 S 域属性现算。文件参数域恰为 S/Z/Y/G/H 五种（规范 `#` 行
  keyword）；功率波幅参数（a-parameters）与传输散射参数（t-parameters，
  ABCD 类）写不进 Touchstone 文件，非文件域、归 Network。私有存储字段名：
  core 内叫 `s`（Rust 字段私有由语言强制，无需下划线；`s_ri` 带格式后缀
  会误导——内存里就是复数本体）；绑定壳层按各端惯例用 `_s`。
  （见「域快捷属性与统一数据访问器」节）。
- 抠端口数/取名进公开静态函数：`nportsFromName`/`nameFromPath`（覆盖旧库
  `parsePorts`/`getFilename`/`getBasename` 功能，实证旧库即公开静态）。
  `nportsFromName` 匹配不到扩展名时**直接报错**（调用它就是为了拿 nports，
  拿不到不能静默继续），错误消息指名指引显式传 nports。
- 写出接口全平铺、无 opts 包（与构造器同规）：
  `writeTouchstone(parameter, format)` / `writeFile(path, parameter, format)`——
  `parameter`/`format` 必填（与构造器对称）；**无 `version` 选项**（由 z0
  推导，实证 skrf `write_touchstone` 签名亦无 version 参）；**无 `rRef` 选项**
  （skrf 的 `r_ref` 是写出时覆盖参考电阻用，与 `z0` 冗余——`z0` 是唯一权威，
  要改参考阻抗就改对象再写出）。
- MA/DB 语义钉死（五源交叉验证，无歧义）：角度恒**度**（规范原文 "All
  angles are measured in degrees"）。dB = **20×log₁₀(幅度)**，五源一致：
  规范 "decibel = 20 × log10 magnitude"；skrf `complex_2_db` = 20log₁₀|z|
  （mathFunctions.py:150，另有独立 `complex_2_db10` 专供功率量）；SI
  `20*math.log10(abs(val))`（SParameters.py:159）；旧库注释 "DB: Decibel
  (20*log10)"；电子书 `20*math.log10` 与反变换 `10^(A/20)`。电子书中的
  10log 均为**功率量**（dBm 功率谱），幅度比一律 20log——S 参是幅度比。
- `data()` 返回形状对称 skrf `s`（实证 skrf `s` = `(nfreq, nports, nports)`
  复数 ndarray）：RI = 同形状复数；MA/DB = `(nfreq, nports, nports, 2)`
  实数对（mag,deg / db,deg）——只是把复数换成实数对，与 `s` 对称。
  底层存储恒扁平 f64（铁律一），对外形状**现在就定，不留 reshape 给用户**：
  Python 经 PyO3 直接交多维 ndarray（`(nfreq,nports,nports)` 或
  `(nfreq,nports,nports,2)`，零拷贝视图，无需用户 reshape）；JS/wasm 无多维
  typed array 类型，交 Float64Array + shape 元数据（平台物理限制，非选择）。
  `s` 与 `data()` 同规则，不单独漂。
- 跨端零拷贝边界（实证机制）：Python 经 buffer protocol 把 ndarray 内存
  直接交给 Rust `&[f64]`，零拷贝；node 经 napi `Buffer`/`Float64Array`
  同理零拷贝；浏览器 wasm 因 JS 堆与 wasm 线性内存分离，typed array 传入
  时**必有一次 memcpy**（物理隔离，无法零拷贝；SharedArrayBuffer 可消除
  但需 COOP/COEP 部署成本，v1 不用）——拷一次后全在 wasm 内存，后续
  访问零拷贝，与 worker 常驻架构契合。
- `version` 公开面用字符串 `"1.0"`/`"1.1"`（对齐 skrf 裸 str），未来 2.0/2.1
  直接扩字符串值，不改类型。
- 大文件窗口化接口 v1 不定义：>100 MB 解析后仍是扁平 f64 的
  `(nfreq, nports, nports)` 自寻址布局，GUI 取"某几行某几列"直接切片即可，
  无需新 API；
  三库均无分页访问器（实证）。真实需求（如 worker 端流式窗口）出现再立项。
- `nports` 推断：`fromFile`/`fromUrl` 从扩展名 `.sNp` 抠（skrf `_parse_file`
  同法，正则 `[ghsyz](\d+)p`）；`fromText` 无文件名时 MUST 显式传 `nports`
  （或传 `name` 由扩展名推）——纯数据行列数存在歧义（一行 10 个数可为
  1 频点×3 端口或 2 频点×2 端口），信息论上无法自推，必须有一个来源。
  `name` 语义 = 无扩展名文件名（实证 skrf `self.name` 同义）；显式 `nports`
  与 `name` 同传时**显式 `nports` 赢**（显式 > 推断），`name` 仅元数据不校验。
- 词汇大小写：读入大小写均可（解析器 `to_ascii_uppercase` 归一，用户友好）；
  写出、enum、文档、错误消息一律规范标准大写（RI/MA/DB、S/Z/Y/G/H）。
- G/H 非 2 端口直接报错：规范 G/H 仅定义于 2 端口，skrf `g`/`h` docstring
  钉死 shape `fx2x2`（实证）；构造器与 `data('G'/'H')` 运行时同一规则，
  进 `TouchstoneError` 三端映射。
- v1.0 与 v1.1 语法唯一差别是参考阻抗：1.0 的 `R` 仅标量、1.1 可每端口
  （均实数，规范禁止复数）；解析层归一成每端口数组即同时覆盖两版，成本极低。
  **已定：v1 同时支持 1.0+1.1 的单/多 z0**。version 推导同步简化：
  全端口同值→1.0，存在不同值→1.1。
- 普通数据构造器 `new Touchstone(...)` 必选：三入口只覆盖"已有文件/文本"，
  计算结果拼 Touchstone 与纯数据写入都需要直接收 `(f, s, z0)` 的构造器
  （对标三库，见「数据构造器」节）。
- 频率轴规则：**重复频点直接报错**（同频两值无法取舍，真歧义）；
  **乱序（忽高忽低）可接受，内部静默排序成递增存储**，不报错不 warning——
  排序是确定性操作，软件一行解决，不把工具能做的事推给用户
  （见「频率轴规则」节）。
- 数据构造器单一入口、全平铺参数：不造工厂族也不用 opts 包，
  `new Touchstone(frequency, data, z0, parameter, name?, comments?)`——
  **`parameter` 必填无默认**（默认 S 会让忘传的用户把 Z 数据静默当 S 存，
  数值全错不报错）；`name` 默认空串、`comments` 默认无注释；
  **`format` 不是构造参数**（内存数据恒为实部/虚部交错复数，RI/MA/DB
  只在解析文本与写出文本时起作用，归 `writeTouchstone` 选项）；
  **`version` 不是构造参数**（由 `z0` 推导：全端口同一实数→1.0，
  每端口存在不同值→1.1；解析入口则从文件记录）（见「数据构造器」节）。
- HTTP 客户端已定：**reqwest**（crates.io 实测下载量高层库第一，见
  「I/O 归属」节分析）。
- `Touchstone` 是主类：需随 Touchstone 核心 change 提交 api-contract spec
  delta，修订"无状态一次性变换（如 Touchstone 文本解析）MUST 是模块级函数"
  条款——`Touchstone` 归入"持有解析结果的状态类"。

## v1 公开 API 面

### 属性（名字对齐 skrf `Network`，TS 端机械 camelCase）

| 属性                        | 语义                                                                                                                                                                                              | 来源/理由                                                                                                     |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `s`                         | 复数 `(nfreq, nports, nports)` 视图（底层扁平 f64，铁律一）；文件为 Y/Z/G/H 时解析时即换算成 S 存储，`s` 是唯一主数据；即 `data()` 默认值的快捷入口                                               | skrf `Network.s`；铁律一布局                                                                                  |
| `z`/`y`/`g`/`h`             | 域快捷属性：复数 `(nfreq, nports, nports)` 视图，现算不缓存（后端 = 私有 `s_to_domain`）；skrf 用户 `ts.z` 肌肉记忆不断                                                                           | skrf `Network.z`/`y`/`g`/`h` 同名公开属性（实证 network.py:1046–1254）；全留与 `s` 对称                       |
| `f`                         | 转发内部 `Frequency` 实例，恒 f64 Hz                                                                                                                                                              | skrf `Network.f`                                                                                              |
| `z0`                        | 每端口实数数组（f64 欧姆；`#` 行 `R` 归一后的唯一权威；规范禁止复数参考阻抗）                                                                                                                     | skrf `Network.z0`                                                                                             |
| `nports`                    | 端口数                                                                                                                                                                                            | skrf `Network.nports`                                                                                         |
| `name`                      | 文件名（无扩展名）                                                                                                                                                                                | skrf `Network.name`                                                                                           |
| `comments`                  | `!` 注释合并文本                                                                                                                                                                                  | skrf `Network.comments`                                                                                       |
| `version`                   | `"1.0"` / `"1.1"`（字符串，未来 2.0/2.1 直接扩值不改类型）                                                                                                                                        | skrf `Touchstone.version` 裸 str（Network 无，借 Touchstone 名）                                              |
| `parameter`                 | 文件记录的参数类型 S/Y/Z/G/H（G/H 仅 2 端口）                                                                                                                                                     | skrf `Touchstone.parameter`；旧库功能覆盖                                                                     |
| `format`                    | 文件数值格式 RI/MA/DB                                                                                                                                                                             | skrf `Touchstone.format`                                                                                      |
| `data(parameter?, format?)` | 统一数据访问器：S/Z/Y/G/H × RI/MA/DB 全组合；RI = `(nfreq, nports, nports)` 复数，MA/DB = 同形状 +2 维实数对（mag,deg / db,deg），与 `s` 对称；默认 `(S, RI)` 零拷贝返回 `s` 本体；其余现算不缓存 | 20 组合不拆 20 属性；skrf `get_sparameter_data(format)` 同法（io/touchstone.py:775）；GUI 表格任意域/格式显示 |

### 静态函数（全部，无遗漏）

| 方法                                           | 语义                                                                                                            |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `fromText(text, nports?, name?)` / `from_text` | 解析字符串（对齐 skrf `Network.from_string`）；无 `name` 扩展名可推时 `nports` 必填（见已定裁决）               |
| `fromFile(path)` / `from_file`                 | 原生端 std::fs/memmap2 流式（铁律六）；浏览器收 `File`/`Blob`                                                   |
| `fromUrl(url)` / `from_url`                    | async；浏览器 = core 内 cfg 门控 `web_sys::fetch`，原生端已选 reqwest                                           |
| `nportsFromName(name)` / `nports_from_name`    | `.sNp` 扩展名抠端口数（覆盖旧库公开静态 `parsePorts`）；三工厂内部共用；匹配不到**直接报错**并指引显式传 nports |
| `nameFromPath(path)` / `name_from_path`        | 路径/URL → 无扩展名文件名（覆盖旧库公开静态 `getFilename`/`getBasename`）                                       |

三入口构造即解析完成（对齐旧库"构造即解析"与 skrf `Network('x.s2p')`），
不存在二段式 `load_file` / `read_touchstone` 动词。

### 数据构造器（普通构造）

`new Touchstone(frequency, data, z0, parameter, name?, comments?)`（Python
`Touchstone(frequency, data, z0, parameter, name="", comments="")`）：
全平铺参数，无 opts 包。

- `frequency`：**`Frequency` 对象**，不是裸 Hz 数组——频率轴唯一权威就是
  `Frequency` 实例（api-contract 既定），构造器直接收对象、不在内部再造；
  绑定层收 Float64Array/ndarray 时在入口一行包成 `Frequency`。
- `data`：**格式固定实部/虚部交错 f64**（铁律一布局，唯一内存形态，
  无需也无法声明 RI/MA/DB）。各端直接收原生类型，**不需要数组转 data 的
  转换函数**：Rust `Vec<f64>`/`&[f64]`；Python
  `np.asarray(x, dtype=np.float64).ravel()`（PyO3 收 ndarray/任意序列，一行）；
  node/浏览器 `Float64Array`（普通数组 `Float64Array.from(arr)` 一行）。
  交错只是排列约定，扁平化即得，造转换函数=造第二份真相源。
- `z0`：标量实数或每端口实数数组（规范禁止复数参考阻抗，三端同形：
  Rust `Vec<f64>` + 标量 `impl Into` 归一；Python float/ndarray；
  JS/TS `number \| Float64Array`——无复数则无歧义）。
- `parameter`：**必填**（S/Z/Y/G/H，声明 `data` 是什么域，core 内换算成 S）。
- `name`/`comments`：可选，默认空串/无注释。
- 构造时校验：维度自洽（`frequency.npoints × nports² == data.len()`）、
  频点无重复（乱序则内部排序）、G/H 仅 2 端口。

**format 为什么不在构造器**：RI/MA/DB 是文本文件里复数的两种书写方式，
内存里永远是复数——解析时按文件 `#` 行换算成复数入库，写出时按
`writeTouchstone(parameter, format)` 排版，构造器收的是复数本身，声明 format 无意义。
用户只有幅度/角度数组时的构造工具用各端原生即可（实证无需新增）：
Python `cmath.rect` / `mag * np.exp(1j*np.deg2rad(angle))`；JS/TS
`mag*(Math.cos(rad)+1j*Math.sin(rad))` 填交错位；Rust
`num_complex::Complex::from_polar`。原生一行解决，不造 `fromPolar` 重复轮子。

**version 为什么不在构造器**：由 `z0` 推导——全端口同一实数→1.0，
每端口存在不同值→1.1（1.1 的存在意义就是表达每端口参考阻抗）；
解析入口的 version 从文件本身记录，也不由用户传。

**单一入口，不造工厂族**：不用 `fromZ`/`fromY`/`fromG`/`fromH` 四个工厂——
`parameter` 必填参数一个位置覆盖全部参数域，动词面不膨胀；参数词汇是 core
enum 反射（跨端词汇零手抄），无字符串拼写风险。skrf 的 `from_z` 需求
（用户只有 Z 数据）由 `new Touchstone(frequency, z, z0, 'Z')` 同等满足；
差异点（skrf 用 `from_z` 具名工厂）记入四端命名映射表。

三库对标（实证）：

- skrf：`Network.__init__` 不传 `file` 时走 kwargs 直收数据——
  `Network(f=..., s=..., z0=...)`（docstring 原文 "directly from data"）；
  另有 `Network.from_z(z, ...)` 具名工厂收 Z 数据（实证全类仅此一个
  参数域工厂 + `from_string`，无 from_y/from_g/from_h）。
- SignalIntegrity：`SParameters.__init__(f, data, Z0=50.0, header=[])`
  即纯数据构造器，文件解析在 App 层完成后喂进来。
- rf-touchstone：无纯数据构造器（只有 fromText/fromFile/fromUrl），
  用户只能先 writeContent 拼文本——netwave 的数据构造器是对旧库短板的补齐。

写文件路径闭环：内存数据 → `new Touchstone(...)` → `writeFile(path)` /
`writeTouchstone()`；或已解析对象改完再写。

### 写出

| 方法                                                      | 语义                                                                                                                                                                                                                                                                                                                |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `writeTouchstone(parameter, format)` / `write_touchstone` | 吐 Touchstone 文本；全平铺必填 `parameter`(S/Y/Z/G/H)、`format`(RI/MA/DB)，与构造器对称。无 `version`（z0 推导，skrf 同法）、无 `rRef`（`z0` 唯一权威）。shortest-roundtrip，写出→读回 bit 级一致（测试规划已定）。三库写出名：skrf `write_touchstone`、SI `Text`/`WriteToFile`、旧库 `writeContent`——本名对齐 skrf |
| `writeFile(path, parameter, format)` / `write_file`       | 原生端写文件；**浏览器端导出但调用即抛"浏览器不支持"**（实证：旧库根本无 `writeFile`，只有 `writeContent()` 返回文本，落盘/下载归调用方 GUI——`URL.createObjectURL` + `<a download>` 是 GUI 行为不属核心库；选"导出但抛错"保三端 API 面一致）                                                                        |
| `drop()` / `drop`                                         | 统一释放动词（已定案，见 memory-lifecycle spec）                                                                                                                                                                                                                                                                    |

### 属性承载字段（core `Touchstone` struct——公开属性的后端存储）

Rust 字段级私有，但每个字段都有上表公开 property 对应——本节是公开属性的
存储清单，不是隐藏状态；真正的私有件只有下一节的函数。

| 字段        | 类型               | 说明                                      |
| ----------- | ------------------ | ----------------------------------------- |
| `frequency` | `Frequency` 实例   | 频率轴唯一权威（Hz，递增存储）            |
| `s`         | 交错复数扁平 f64   | 唯一主数据，`(nfreq, nports, nports)`     |
| `z0`        | 每端口实数数组 f64 | `#` 行 `R` 归一后的唯一权威（规范禁复数） |
| `nports`    | `u32`              | 端口数（冗余自 z0 长度，热路径免间接）    |
| `name`      | `Option<String>`   | 文件/URL 名（无扩展名）                   |
| `comments`  | `String`           | `!` 注释合并文本                          |
| `version`   | `bool`（是否 1.1） | 解析自文件记录；数据构造时由 `z0` 推导    |
| `parameter` | enum（S/Y/Z/G/H）  | 文件原始参数类型，仅元数据                |
| `format`    | enum（RI/MA/DB）   | 写出默认格式偏好                          |

不存：频率单位（在 `Frequency.unit`）、频点数（`frequency.npoints`）、
噪声（v1 不支持）、resistance/reference 原始值（已归一进 `z0`）。
浏览器端：以上状态全在常驻 worker 内 core，主线程壳持 handle
（memory-lifecycle spec 既定机制，非本类新增）。

### 私有函数（core `Touchstone`，均不公开）

三库对标（实证）：skrf `Touchstone` 私有件恰为解析家族
（`_parse_n_floats`/`_parse_float_block`/`_parse_port`/`_parse_file`/
`_hfss_port_values`），其换算 `s2z`/`z2s` 等是模块级函数（network.py:7128 起）
不是类私有；SI `SParameters` 零私有（全公开）；旧库解析内联在公开
`readContent`、静态件全公开。netwave 取 skrf 私有解析家族，并把换算收进
类私有——因为统一访问器 `data(parameter, format)` 是本类唯一公开数据面
（合并原则），换算知识不外泄。

| 函数                | 职责                                                                               |
| ------------------- | ---------------------------------------------------------------------------------- |
| `parse_text`        | 逐行解析主循环（fromText/fromFile/fromUrl 共用）                                   |
| `parse_option_line` | `#` 行：单位/参数域/格式/R（标量或每端口，归一进 z0）                              |
| `parse_data_line`   | 数据行 → 复数（按 format 换算；RI/MA/DB 三分支）                                   |
| `skip_noise_lines`  | 2 端口尾部噪声行识别并静默跳过（已定裁决）                                         |
| `sort_and_check_f`  | 乱序排序入库；重复频点报错                                                         |
| `convert_to_s`      | Y/Z/G/H → S 换算（构造器与解析器共用，唯一实现）                                   |
| `s_to_domain`       | S → Z/Y/G/H 换算（`z`/`y`/`g`/`h` 快捷属性与 `data('Z'/'Y'/'G'/'H', …)` 共用后端） |
| `to_ma` / `to_db`   | 复数 → (mag,deg)/(db,deg) 实数对（`data(…, 'MA'/'DB')` 后端；RI 即存储布局）       |
| `infer_version`     | 由 z0 推导 1.0/1.1（全端口同实数→1.0）                                             |
| `format_number`     | shortest-roundtrip 数字格式化（写出 bit 级一致）                                   |
| `render_text`       | 写出文本拼装（writeTouchstone 内部）                                               |

抠端口数不入私有件——升为公开静态 `nportsFromName`（见「静态函数」节）。

### 域快捷属性与统一数据访问器（全留 + 分工，换算全私有）

三库对标（实证）：skrf `Network` 公开面就有 `s`/`z`/`y`/`a`/`g`/`h` 快捷属性
（network.py:1046–1254）；skrf `Touchstone` 同时有"单一访问器 + format 参数"
（`get_sparameter_data(format)`、`get_format(format)`，io/touchstone.py:775/738）；
SI `Text(formatString)` 同法；旧库 `format` setter + `writeContent` 按 format 排版。

**netwave 裁决：域快捷属性全留，格式维度不拆属性，两层入口分工**：

- 域快捷属性 `s`/`z`/`y`/`g`/`h`：复数 `(nfreq, nports, nports)` 视图
  （底层扁平 f64 存储的零拷贝 reshape）。`s` 零拷贝返回存储本体；
  `z`/`y`/`g`/`h` 现算不缓存（后端 = 私有 `s_to_domain`）。全留理由：对齐
  skrf 同名公开属性（兼容主原则），`ts.z` 肌肉记忆不断；要么全留要么全删，
  不留 `s` 删其余会破坏对称。
- 统一访问器 `data(parameter?, format?)` / Python
  `data(parameter=..., format=...)`：域×格式全组合；`parameter` ∈ S/Z/Y/G/H
  （规范 `#` 行全部文件域），`format` ∈ RI/MA/DB；默认 `(S, RI)` = 零拷贝
  返回 `s` 本体。要 MA/DB 实数对（GUI 表格、幅度/角度显示）时才需要它——
  格式维度不拆成 `s_ma`/`z_db`… 20 个属性（命名灾难）。词汇全是 core enum
  反射，无字符串拼写风险；与构造器参数名 `data` 对称（收数据、还数据同名字）。
- 返回形状对称 skrf `s`（实证 skrf `s` = `(nfreq, nports, nports)` 复数）：
  RI = 同形状复数；MA/DB = `(nfreq, nports, nports, 2)` 实数对
  （mag,deg / db,deg）——只是把复数换成实数对。角度恒度、dB = 20×log₁₀(幅度)
  （规范原文钉死，见已定裁决）。底层存储恒扁平 f64（铁律一），多维是
  零拷贝视图（Python reshape / JS shape 元数据）；未来改多维则 `s` 一起改。
- 换算全部私有（`s_to_domain`/`to_ma`/`to_db`），外部只见属性与方法、
  无需理解换算——入口与换算是整体。
- 存储仍只有 `s` 一份（铁律一布局不变），非默认入口每次现算。
  core 内私有存储字段就叫 `s`（Rust 字段私有由语言强制，无需下划线；
  `s_ri` 带格式后缀会误导——内存里就是复数本体）；绑定壳层按各端惯例用 `_s`。

功率波幅参数（a-parameters）与传输散射参数（t-parameters，ABCD 类）写不进
Touchstone 文件（规范 `#` 行只允许 S/Z/Y/G/H），非文件域，归 Network。
skrf `Network` 的笛卡尔积分量衍生面（实证 `_generated_functions`：
`PRIMARY_PROPERTIES × COMPONENT_FUNC_DICT` → `s_re`/`s_mag`/`s_db`/`s_deg`…
及时域量 `step_response` 等）仍归 Network 计算层，不进 Touchstone——
GUI 需要的分量在 `data(…, 'MA'/'DB')` 实数对里已齐（RI=re/im、
MA=mag/deg、DB=db/deg）。分量命名在 Network 立项时进四端命名映射表。

### Network 侧的桥

- `Network.fromTouchstone(ts)`：把 `Touchstone` 手里的
  `(f, s, z0, name, comments)` 接过来构造 `Network`。
- `Network` 公开面上 MUST NOT 出现 `read_touchstone` / `write_touchstone` /
  `from_string` / `zipped_touchstone`——文件知识全在 `Touchstone`。
- 域换算不在 Network 重复造轮：Network 的 z/y 直接消费 `Touchstone` 的
  `z`/`y` 快捷属性；Network 只保留计算层动词（级连/去嵌/时域等）与
  a/t（功率波幅/传输散射）等非文件域换算。

## v1 不做清单（含理由）

| 项                                                                                     | 理由                                                                          |
| -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `port_names`                                                                           | 非标准语法（厂商注释方言，见标准核实结论）                                    |
| `comments_after_option_line`                                                           | 已裁决放弃                                                                    |
| `resistance`/`reference`/`frequency_unit`/`frequency_nb`/`filename`                    | 派生量或重复存储，已裁决                                                      |
| Touchstone 2.0/2.1（`[Port]`、`[Noise Data]`、`[Number of Frequencies]` 等方括号语法） | 覆盖规划已定延后                                                              |
| `noise`/`noise_freq` 属性与噪声计算                                                    | 旧库不支持噪声（实证）；v1 遇噪声行静默跳过、不报错，属性与计算随噪声模块延后 |
| HFSS 注释抠 gamma/z0（skrf `hfss_touchstone_2_*`）                                     | 厂商方言，非硬约束                                                            |
| `get_sparameter_data` 等 dict 松散访问器                                               | api-contract 三层契约拒绝                                                     |
| zip 包读取（skrf `zipped_touchstone`）                                                 | 旧库无此功能，非功能覆盖项                                                    |
| `s_def` / `port_modes` / `s_traveling` 等参考定义换算                                  | 计算层语义，归 Network 且牵涉 2.x，延后                                       |
| `validate()`                                                                           | skrf 无；构造即解析完成，非法状态构造不出来（见已定裁决）                     |

## I/O 归属（from_url 实现路线）

- 铁律十一（绑定薄壳）：fetch 调用写在 core 源码内，cfg 分后端——
  browser feature 用 `web_sys::fetch` + `wasm_bindgen_futures`（返回 Promise），
  node 走 napi AsyncTask，Python 阻塞 + `allow_threads`。壳零改动。
- 浏览器端不引入任何 Rust HTTP 库：`web_sys::fetch` 就是浏览器原生 fetch 的
  thin binding（JS 侧无新依赖），这是 wasm 端唯一正路。
- 原生端 HTTP 客户端分析（crates.io API 实测下载量，总下载/近期）：

  | 库        | 总下载  | 近期下载 | 适配 netwave 否 | 理由                                                                                                                                       |
  | --------- | ------- | -------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
  | `hyper`   | 9.9 亿  | 2.3 亿   | 不选            | 下载量第一但是底层库，要自己拼 TLS/连接池/重定向，违背简洁优先                                                                             |
  | `reqwest` | 7.8 亿  | 2.1 亿   | **已选**        | 高层客户端事实标准；异步 tokio 与 napi AsyncTask 同构；HTTPS 走纯 Rust rustls 不依赖系统 OpenSSL，交叉编译友好（CI 多目标）；支持流式 body |
  | `ureq`    | 2.2 亿  | 0.7 亿   | 备选            | 同步阻塞、依赖极少；无 async，node 端 AsyncTask 包同步请求可行但浪费                                                                       |
  | `isahc`   | 0.18 亿 | 0.012 亿 | 不选            | 引 libcurl 系统依赖，交叉编译坑多                                                                                                          |
  | `awc`     | 0.13 亿 | 0.010 亿 | 不选            | actix 生态绑定，为它拖整个 runtime 不值                                                                                                    |
  | `surf`    | 0.05 亿 | 0.005 亿 | 不选            | 生态小且维护停滞                                                                                                                           |

  代价声明：reqwest 拖 tokio 进依赖树，影响的是 **Python 与 node 两个原生产物**
  （tokio 链进 .so/.node，用户无感，仅体积增大）；浏览器 wasm 产物 cfg 门控
  不编译 reqwest，走 `web_sys::fetch`，零影响。

- 浏览器 CORS/COOP-COEP 失败原样抛错，库不吞不重试；文档声明这层差异。
- 落地后销账：总体计划「待决细节清单」中"网络/文件 I/O 归属与异步边界"
  条目由本规划 + design.md 承接。

## 频率轴规则（三库对标 + 已定）

- 标准原文（v2.1 规范）：网络参数数据 "shall be arranged in increasing order
  of frequency"——**标准本身要求递增**。
- skrf：不拒绝——检测到非单调/重复频点只发 `InvalidFrequencyWarning`，
  提供 `drop_non_monotonic_increasing()` 让用户手动删掉坏行（实证
  `frequency.py`）。
- SignalIntegrity：无显式校验（实证：FrequencyList 无 sort/monotonic 检查）。
- rf-touchstone：无显式校验（`validate()` 只查维度不查频率序）。
- **netwave 已定：重复频点报错；乱序静默排序成递增存储**。
  理由：① 重复频点是真歧义（同频两个值取哪个，无法替用户决定）→报错；
  ② 乱序无歧义，排序是确定性操作，标准写的 increasing order 是存储要求，
  内部排完即守标准——软件一行能解决的事不报错不警告不把活推给用户；
  ③ 排序后写出即递增，往返一致；④ 报错仅重复频点一处，三端错误映射进既有
  PyErr/napi Error/throw 机制。

## touchstone.rs 类型定义（typing 面）

三库 typing 对标（实证）：skrf 用 `typing.Literal` 字符串别名
（`SparamFormatT = Literal["db","ri","ma"]`、`PrimaryPropertiesT` 等，无类无 struct）；
旧库用 `as const` 数组 + 联合类型（`TouchstoneFormats`/`TouchstoneParameters`）；
SI 无显式 typing。共同点：**只有词汇表 + 错误，无 Options struct、无 Version 枚举**
（skrf `version` 就是裸 str，旧库无 version）。

命名对标（实证）：旧库导出 `TouchstoneFormats`/`TouchstoneParameters`
（`as const` + 联合类型）；skrf 用 `SparamFormatT` 等 Literal 别名。
`DataFormat` 一名有歧义——本项目 "data" 已专指交错 f64 主数据，格式枚举
却叫 DataFormat 会撞车。**已定：改名 `TouchstoneFormat` /
`TouchstoneParameter`，对齐旧库命名。**

netwave `touchstone.rs` 只定义：

| 类型                  | 形态                   | 说明                                                                       |
| --------------------- | ---------------------- | -------------------------------------------------------------------------- |
| `TouchstoneParameter` | enum { S, Y, Z, G, H } | 参数域；core 定义一次，三端宏反射（跨端词汇零手抄）                        |
| `TouchstoneFormat`    | enum { RI, MA, DB }    | 文本读写格式（仅解析/写出用）；同上反射                                    |
| `TouchstoneError`     | thiserror enum         | 解析/构造错误：重复频点、维度不符、语法错；三端映射 PyErr/napi Error/throw |

删除：`Version`（内部 bool 或由 `z0` 推导即可，不配拥有类型）、
`TouchstoneOptions`（参数已平铺，无选项包）、`SData`（直接用
`Vec<Complex64>`/交错 f64 视图，别名是多余间接）。
复用不重定义：`Frequency`/`FrequencyUnit`（frequency 模块既有）、`Complex64`（num-complex）。

## 三库命名对照（netwave vs skrf vs SI vs 旧库）

| netwave                             | skrf                          | SI                   | 旧库 RF-Touchstone                       | 差异说明                         |
| ----------------------------------- | ----------------------------- | -------------------- | ---------------------------------------- | -------------------------------- |
| `s`/`z`/`y`/`g`/`h`                 | 同名（`Network` 公开属性）    | 无（`m_d` 内部）     | `data` 单一                              | netwave 对齐 skrf                |
| `f`/`z0`/`nports`/`name`/`comments` | 同名（`Network`）             | `f`/`Z0`             | `frequency`/`ports`                      | netwave 对齐 skrf                |
| `version`/`parameter`/`format`      | `Touchstone` 同名             | 无                   | `format`                                 | netwave 借 skrf `Touchstone`     |
| `data(parameter, format)`           | `get_sparameter_data(format)` | `Text(formatString)` | `writeContent()`                         | 同法不同名，对齐旧库功能         |
| `fromText`/`fromFile`/`fromUrl`     | `from_string`/构造器收路径    | `SParametersParser`  | `fromText`/`fromFile`/`fromUrl`          | netwave 同旧库名                 |
| `writeTouchstone`/`writeFile`       | `write_touchstone`            | `WriteToFile`        | 无 `writeFile`（仅 `writeContent`）      | netwave 拆文本/落盘两动词        |
| `nportsFromName`/`nameFromPath`     | 无（内联 `_parse_file`）      | 无                   | `parsePorts`/`getFilename`/`getBasename` | netwave 同旧库拆法               |
| `drop()`                            | 无                            | 无                   | 无                                       | netwave 自有（memory-lifecycle） |

## 内部命名备注

- 内部频率字段就叫 `frequency`：skrf `Network` 内部同名（实证 `self.frequency`
  遍布源码，`f` 是其转发 property）——长是长了点，兼容规矩优先。

## 待决

（无——本轮裁决已全部落定，实现细节归 design.md。）

## 波及文档（落地时同步改）

- `功能覆盖规划.md`：修正噪声行表述（见标准核实结论）；
  "rf-touchstone 功能 100% 覆盖"口径补一句"功能覆盖，非 API 同名"。
- `总体计划.md`：待决细节清单 I/O 条目销账；`fromTouchstone` 命名进
  四端命名映射表。
- `openspec/specs/api-contract/spec.md`：随 Touchstone 核心 change 提 delta，
  修订"Touchstone 文本解析 MUST 是模块级函数"条款；统一访问器
  `data(parameter, format)`（换算私有）的归属调整一并进 delta。
