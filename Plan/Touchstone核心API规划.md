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
  **v1 决策：解析并保留噪声原始行（`noise`），噪声计算延后**——与覆盖规划
  "解析保留、计算延后"一致。

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
  `fromUrl`/`validate` 等按新 API 重新实现即可。
- `Touchstone` 是主类：需随 Touchstone 核心 change 提交 api-contract spec
  delta，修订"无状态一次性变换（如 Touchstone 文本解析）MUST 是模块级函数"
  条款——`Touchstone` 归入"持有解析结果的状态类"。

## v1 公开 API 面

### 属性（名字对齐 skrf `Network`，TS 端机械 camelCase）

| 属性        | 语义                                                                                                                             | 来源/理由                                                 |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| `s`         | 交错复数扁平 f64，`(nfreq, nports, nports)`；文件里若是 Y/Z/G/H，解析后按 `parameter` 记录原始类型，`s` 存换算前数据由 design 定 | skrf `Network.s`；铁律一布局                              |
| `f`         | 转发内部 `Frequency` 实例，恒 f64 Hz                                                                                             | skrf `Network.f`                                          |
| `z0`        | 每端口复数数组（`#` 行 `R` 归一后的唯一权威）                                                                                    | skrf `Network.z0`                                         |
| `nports`    | 端口数                                                                                                                           | skrf `Network.nports`                                     |
| `name`      | 文件名（无扩展名）                                                                                                               | skrf `Network.name`                                       |
| `comments`  | `!` 注释合并文本                                                                                                                 | skrf `Network.comments`                                   |
| `version`   | `"1.0"` / `"1.1"`                                                                                                                | skrf `Touchstone.version`（Network 无，借 Touchstone 名） |
| `parameter` | 文件记录的参数类型 S/Y/Z/G/H（G/H 仅 2 端口）                                                                                    | skrf `Touchstone.parameter`；旧库功能覆盖                 |
| `format`    | 文件数值格式 RI/MA/DB                                                                                                            | skrf `Touchstone.format`                                  |
| `noise`     | 2 端口文件尾部噪声原始行（解析保留，计算延后）                                                                                   | 规范 1.0/1.1 允许；skrf `Network.noise` 名                |

### 数据入口（静态工厂）

| 方法                                  | 语义                                                                                          |
| ------------------------------------- | --------------------------------------------------------------------------------------------- |
| `fromText(text, name?)` / `from_text` | 解析字符串（对齐 skrf `Network.from_string`，命名取旧库 fromText 语义、函数名在 design 定稿） |
| `fromFile(path)` / `from_file`        | 原生端 std::fs/memmap2 流式（铁律六）；浏览器收 `File`/`Blob`                                 |
| `fromUrl(url)` / `from_url`           | async；浏览器 = core 内 cfg 门控 `web_sys::fetch`，原生端 HTTP 客户端选型见待决               |

三入口构造即解析完成（对齐旧库"构造即解析"与 skrf `Network('x.s2p')`），
不存在二段式 `load_file` / `read_touchstone` 动词。

### 写出与校验

| 方法                                          | 语义                                                                                                                                                                                                        |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `writeTouchstone(opts?)` / `write_touchstone` | 吐 Touchstone 文本；选项：`form`(RI/MA/DB)、`parameter`(S/Y/Z/G/H)、`version`(1.0/1.1)、`rRef`。默认 shortest-roundtrip，写出→读回 bit 级一致（测试规划已定）。skrf `Network.write_touchstone` 整体下沉至此 |
| `writeFile(path, opts?)` / `write_file`       | 原生端写文件；浏览器拿 `writeTouchstone` 文本自行落盘                                                                                                                                                       |
| `validate()` / `validate`                     | 维度/格式/频点数一致性自检（旧库功能覆盖，名字自定）                                                                                                                                                        |
| `drop()` / `drop`                             | 统一释放动词（已定案，见 memory-lifecycle spec）                                                                                                                                                            |

### Network 侧的桥

- `Network.fromTouchstone(ts)`：把 `Touchstone` 手里的
  `(f, s, z0, name, comments)` 接过来构造 `Network`。
- `Network` 公开面上 MUST NOT 出现 `read_touchstone` / `write_touchstone` /
  `from_string` / `zipped_touchstone`——文件知识全在 `Touchstone`。

## v1 不做清单（含理由）

| 项                                                                                     | 理由                                       |
| -------------------------------------------------------------------------------------- | ------------------------------------------ |
| `port_names`                                                                           | 非标准语法（厂商注释方言，见标准核实结论） |
| `comments_after_option_line`                                                           | 已裁决放弃                                 |
| `resistance`/`reference`/`frequency_unit`/`frequency_nb`/`filename`                    | 派生量或重复存储，已裁决                   |
| Touchstone 2.0/2.1（`[Port]`、`[Noise Data]`、`[Number of Frequencies]` 等方括号语法） | 覆盖规划已定延后                           |
| 噪声计算（NFmin→噪声矩阵换算）                                                         | 解析保留、计算延后（覆盖规划）             |
| HFSS 注释抠 gamma/z0（skrf `hfss_touchstone_2_*`）                                     | 厂商方言，非硬约束                         |
| `get_sparameter_data` 等 dict 松散访问器                                               | api-contract 三层契约拒绝                  |
| zip 包读取（skrf `zipped_touchstone`）                                                 | 旧库无此功能，非功能覆盖项                 |
| `s_def` / `port_modes` / `s_traveling` 等参考定义换算                                  | 计算层语义，归 Network 且牵涉 2.x，延后    |

## I/O 归属（from_url 实现路线）

- 铁律十一（绑定薄壳）：fetch 调用写在 core 源码内，cfg 分后端——
  browser feature 用 `web_sys::fetch` + `wasm_bindgen_futures`（返回 Promise），
  node 走 napi AsyncTask，Python 阻塞 + `allow_threads`。壳零改动。
- 原生端 HTTP 客户端选型（reqwest / ureq / 不引入依赖只支持 file:）
  在 Touchstone 核心 design.md 定案。
- 浏览器 CORS/COOP-COEP 失败原样抛错，库不吞不重试；文档声明这层差异。
- 落地后销账：总体计划「待决细节清单」中"网络/文件 I/O 归属与异步边界"
  条目由本规划 + design.md 承接。

## 待决

- [ ] `s` 对 Y/Z/G/H 文件的存放语义：存原始参数数据（`s` 名不符实）还是
      解析时即换算成 S？涉及"解析层不做计算"边界，design.md 定案。
- [ ] 频率轴非单调/重复频点拒绝规则（总体计划待决清单已登记，归本项）。
- [ ] 原生端 HTTP 客户端选型（见 I/O 归属节）。
- [ ] `fromText` 是否需要 nports 显式参数：1.0/1.1 可由数据行列数自推端口数，
      建议不要求用户传，design.md 确认。

## 波及文档（落地时同步改）

- `功能覆盖规划.md`：修正噪声行表述（见标准核实结论）；
  "rf-touchstone 功能 100% 覆盖"口径补一句"功能覆盖，非 API 同名"。
- `总体计划.md`：待决细节清单 I/O 条目销账；`fromTouchstone` 命名进
  四端命名映射表。
- `openspec/specs/api-contract/spec.md`：随 Touchstone 核心 change 提 delta，
  修订"Touchstone 文本解析 MUST 是模块级函数"条款。
