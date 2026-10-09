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
- 不保存 `resistance`/`reference` 原始值：`#` 选项行 `R`（标量/每端口/复数）
  解析时统一归一成每端口复数数组，只存 `z0` 一份。
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
- `nports` 推断：`fromFile`/`fromUrl` 从扩展名 `.sNp` 抠（skrf `_parse_file`
  同法，正则 `[ghsyz](\d+)p`）；`fromText` 无文件名时 MUST 显式传 `nports`
  （或传 `name` 由扩展名推）——纯数据行列数存在歧义（一行 10 个数可为
  1 频点×3 端口或 2 频点×2 端口），信息论上无法自推，必须有一个来源。
- v1.0 与 v1.1 语法唯一差别是参考阻抗：1.0 的 `R` 仅标量、1.1 可每端口且可
  复数；解析层归一成每端口数组即同时覆盖两版，成本极低。**已定：v1 同时支持
  1.0+1.1 的多 z0 与复数 z0**。
- 普通数据构造器 `new Touchstone(...)` 必选：三入口只覆盖"已有文件/文本"，
  计算结果拼 Touchstone 与纯数据写入都需要直接收 `(f, s, z0)` 的构造器
  （对标三库，见「数据构造器」节）。
- 频率轴规则：解析与构造均 MUST 校验严格单调递增，非单调/重复频点直接报错
  （拒绝而非静默删行，见「频率轴规则」节）。
- `Touchstone` 是主类：需随 Touchstone 核心 change 提交 api-contract spec
  delta，修订"无状态一次性变换（如 Touchstone 文本解析）MUST 是模块级函数"
  条款——`Touchstone` 归入"持有解析结果的状态类"。

## v1 公开 API 面

### 属性（名字对齐 skrf `Network`，TS 端机械 camelCase）

| 属性        | 语义                                                                                                  | 来源/理由                                                 |
| ----------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| `s`         | 交错复数扁平 f64，`(nfreq, nports, nports)`；文件为 Y/Z/G/H 时解析时即换算成 S 存储，`s` 是唯一主数据 | skrf `Network.s`；铁律一布局                              |
| `f`         | 转发内部 `Frequency` 实例，恒 f64 Hz                                                                  | skrf `Network.f`                                          |
| `z0`        | 每端口复数数组（`#` 行 `R` 归一后的唯一权威）                                                         | skrf `Network.z0`                                         |
| `nports`    | 端口数                                                                                                | skrf `Network.nports`                                     |
| `name`      | 文件名（无扩展名）                                                                                    | skrf `Network.name`                                       |
| `comments`  | `!` 注释合并文本                                                                                      | skrf `Network.comments`                                   |
| `version`   | `"1.0"` / `"1.1"`                                                                                     | skrf `Touchstone.version`（Network 无，借 Touchstone 名） |
| `parameter` | 文件记录的参数类型 S/Y/Z/G/H（G/H 仅 2 端口）                                                         | skrf `Touchstone.parameter`；旧库功能覆盖                 |
| `format`    | 文件数值格式 RI/MA/DB                                                                                 | skrf `Touchstone.format`                                  |

### 数据入口（静态工厂）

| 方法                                           | 语义                                                                                              |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `fromText(text, nports?, name?)` / `from_text` | 解析字符串（对齐 skrf `Network.from_string`）；无 `name` 扩展名可推时 `nports` 必填（见已定裁决） |
| `fromFile(path)` / `from_file`                 | 原生端 std::fs/memmap2 流式（铁律六）；浏览器收 `File`/`Blob`                                     |
| `fromUrl(url)` / `from_url`                    | async；浏览器 = core 内 cfg 门控 `web_sys::fetch`，原生端 HTTP 客户端选型见待决                   |

三入口构造即解析完成（对齐旧库"构造即解析"与 skrf `Network('x.s2p')`），
不存在二段式 `load_file` / `read_touchstone` 动词。

### 数据构造器（普通构造）

`new Touchstone(f, s, z0, opts?)` / `Touchstone(f, s, z0, opts?)`：直接收
计算结果拼成 Touchstone 对象——`f`（Hz 频率轴或 `Frequency` 实例）、`s`
（交错 f64，shape 校验）、`z0`（标量或每端口），opts：`name`/`comments`/
`version`/`parameter`/`format`（写出偏好，缺省 1.0/S/RI）。构造时校验：
维度自洽（`len(f)×nports×nports == s.len()`）、频率严格单调递增，不过即报错。

三库对标（实证）：

- skrf：`Network.__init__` 不传 `file` 时走 kwargs 直收数据——
  `Network(f=..., s=..., z0=...)`（docstring 原文 "directly from data"）；
  另有 `Network.from_z(z, ...)` 等 alternate 构造器收非 S 参数。
- SignalIntegrity：`SParameters.__init__(f, data, Z0=50.0, header=[])`
  即纯数据构造器，文件解析在 App 层完成后喂进来。
- rf-touchstone：无纯数据构造器（只有 fromText/fromFile/fromUrl），
  用户只能先 writeContent 拼文本——netwave 的数据构造器是对旧库短板的补齐。

写文件路径闭环：内存数据 → `new Touchstone(...)` → `writeFile(path)` /
`writeTouchstone()`；或已解析对象改完再写。

### 写出

| 方法                                          | 语义                                                                                                                                                                                                        |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `writeTouchstone(opts?)` / `write_touchstone` | 吐 Touchstone 文本；选项：`form`(RI/MA/DB)、`parameter`(S/Y/Z/G/H)、`version`(1.0/1.1)、`rRef`。默认 shortest-roundtrip，写出→读回 bit 级一致（测试规划已定）。skrf `Network.write_touchstone` 整体下沉至此 |
| `writeFile(path, opts?)` / `write_file`       | 原生端写文件；浏览器拿 `writeTouchstone` 文本自行落盘                                                                                                                                                       |
| `drop()` / `drop`                             | 统一释放动词（已定案，见 memory-lifecycle spec）                                                                                                                                                            |

### Network 侧的桥

- `Network.fromTouchstone(ts)`：把 `Touchstone` 手里的
  `(f, s, z0, name, comments)` 接过来构造 `Network`。
- `Network` 公开面上 MUST NOT 出现 `read_touchstone` / `write_touchstone` /
  `from_string` / `zipped_touchstone`——文件知识全在 `Touchstone`。

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
- 原生端 HTTP 客户端分析（crates.io 实时 API 在本环境被 403 拦截，下载量按
  crates.io 公开常识排序，落地前复核）：

  | 库                | 使用量                            | 适配 netwave 否 | 理由                                                                                                                                                                 |
  | ----------------- | --------------------------------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `reqwest`         | crates.io HTTP 类第一（事实标准） | **推荐**        | 异步 tokio 原生——与 napi AsyncTask 同构；HTTPS（rustls）纯 Rust 不依赖系统 OpenSSL，交叉编译友好（CI 已有 aarch64/wasm 多目标）；支持流式 body，接 memmap 式分块解析 |
  | `ureq`            | 第二梯队                          | 备选            | 同步阻塞、依赖极少，但无 async——node 端 AsyncTask 里包同步请求可行但浪费；HTTPS 同样走 rustls                                                                        |
  | `hyper`           | 底层库                            | 不选            | 太底层，要自己拼 TLS/连接池/重定向，违背简洁优先                                                                                                                     |
  | `curl`/`isahc` 等 | —                                 | 不选            | 引系统依赖或生态小，交叉编译坑多                                                                                                                                     |

  代价声明：reqwest 拖 tokio 进依赖树——python/浏览器 feature 不编译它
  （cfg 门控到 native+url feature），wasm 产物零影响。

- 浏览器 CORS/COOP-COEP 失败原样抛错，库不吞不重试；文档声明这层差异。
- 落地后销账：总体计划「待决细节清单」中"网络/文件 I/O 归属与异步边界"
  条目由本规划 + design.md 承接。

## 频率轴规则（三库对标 + 推荐）

- 标准原文（v2.1 规范）：网络参数数据 "shall be arranged in increasing order
  of frequency"——**标准本身要求递增**。
- skrf：不拒绝——检测到非单调/重复频点只发 `InvalidFrequencyWarning`，
  提供 `drop_non_monotonic_increasing()` 让用户手动删掉坏行（实证
  `frequency.py`）。
- SignalIntegrity：无显式校验（实证：FrequencyList 无 sort/monotonic 检查）。
- rf-touchstone：无显式校验（`validate()` 只查维度不查频率序）。
- **netwave 推荐：解析与构造均严格单调递增校验，违规直接报错**。
  理由：① 标准原文就是 shall increasing，拒绝=守标准；② skrf 的"警告+手动删"
  把烂数据问题推给用户的后续计算（插值/IFFT 遇到乱序轴结果静默错）；
  ③ 报错实现最便宜（解析循环里一个比较），静默排序则篡改用户数据不可接受；
  ④ 错误三端映射进既有 PyErr/napi Error/throw 机制，无新面。
  若日后真实用户文件确有乱序需求，再加显式 opt-in `sort_frequencies()` 动词。

## 待决

- [ ] 原生端 HTTP 客户端最终确认（推荐 reqwest，见 I/O 归属节分析）。
- [ ] 数据构造器参数形态：位置参数 `(f, s, z0)` vs options 对象，design.md
      定稿（Python 侧 kwargs 天然兼容两者）。

## 波及文档（落地时同步改）

- `功能覆盖规划.md`：修正噪声行表述（见标准核实结论）；
  "rf-touchstone 功能 100% 覆盖"口径补一句"功能覆盖，非 API 同名"。
- `总体计划.md`：待决细节清单 I/O 条目销账；`fromTouchstone` 命名进
  四端命名映射表。
- `openspec/specs/api-contract/spec.md`：随 Touchstone 核心 change 提 delta，
  修订"Touchstone 文本解析 MUST 是模块级函数"条款。
