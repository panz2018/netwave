# Spec Delta

## Purpose

定义 `Touchstone` 主类对 Touchstone 文件格式（v1.0/v1.1）的完整契约：解析、
纯数据构造、域×格式数据访问、写出与文件名规则、跨端 I/O 形态与错误语义——
是 netwave 文件读写工作流闭环的判定依据，绑定层实现与 code-review 的
验收标准。

## ADDED Requirements

### Requirement: Touchstone 三端类形态与构造即解析

`Touchstone` MUST 作为主类从三端包入口导出（Python `netwave.Touchstone`、
node/浏览器壳 re-export），是"持有解析结果的状态类"（api-contract 修订条款）。
三工厂 `fromText(text, nports?, path?)` / `fromFile(path)` / `fromUrl(url)`
与纯数据构造器 `new Touchstone(...)`（收 frequency、data、z0、parameter，
可选 name、comments）MUST 构造即解析/校验完成，MUST NOT 存在二段式
`load_file` / `read_touchstone` 动词。`parameter`（S/Z/Y/G/H）在构造器与写出接口 MUST
必填无默认（默认 S 会把 Z 数据静默当 S 存）。`frequency` MUST 收 `Frequency`
对象（频率轴唯一权威）。公开属性面：`s`/`z`/`y`/`g`/`h`/`f`/`z0`/`nports`/
`name`/`comments`/`version`/`parameter` + 访问器 `data(parameter?, format?)`；
MUST NOT 存在 `format` 属性、`filename` 属性（文件来源名统一用 `name`，
写出路径是私有方法 `write_path`）、`port_names`、`validate()`、`resistance`/
`reference` 冗余存储。

#### Scenario: 三工厂构造即完成

- **WHEN** 三端各自经 `fromText`/`fromFile`/`fromUrl` 构造并立即读 `s`
- **THEN** 无需任何后续 load/read 调用即得完整数据；三端动词名一致
  （TS 机械 camelCase，Python snake_case）

#### Scenario: parameter 缺失即报错

- **WHEN** 纯数据构造器调用未传 `parameter`
- **THEN** 三端同一位置报参数缺失错误，不发生默认 S 的静默存储

### Requirement: 解析覆盖 1.0/1.1 且 z0 恒实数

解析器 MUST 支持 Touchstone 1.0 与 1.1：`#` 选项行 `R` 标量（1.0）或每端口
实数（1.1）归一成每端口 f64 数组存 `z0`（唯一权威，不存原始 R）。规范禁止
复数参考阻抗（v1.1 R 为 real positive numbers；v2.x 明文 complex not
supported），z0 MUST NOT 接受复数。`z0` 入参形状 MUST 恰为标量或长度
`1`/`nports` 的实数数组，其余长度 MUST 报错。version 推导：全端口同值→
`"1.0"`，存在不同值→`"1.1"`；公开面 version 为字符串。参数域 S/Z/Y/G/H
大小写不敏感读入（`to_ascii_uppercase` 归一），写出/enum/错误消息一律
标准大写。G/H 域仅 2 端口，违者报错。频点边界 MUST 纯由 nports 决定：
数字 token 流按 stride = `1 + 2×nports²` 消费，总数不整除 MUST 报
`TouchstoneError`（行只是排版，频点数 = token 总数 ÷ stride，不看行数）。
噪声参数 v1 不识别不跳过：噪声行混入必破坏 stride 整除性 → 自然报错
（与 SignalIntegrity/旧库同策，不做"频率回落判噪声"启发式）。

#### Scenario: v1.1 每端口 z0 解析

- **WHEN** 解析 `# GHZ S MA R 50 45 50 50` 的 4 端口文件
- **THEN** `z0` = `[50.0, 45.0, 50.0, 50.0]`，`version` = `"1.1"`

#### Scenario: z0 长度非法报错

- **WHEN** 构造器收到长度既非 1 也非 `nports` 的 z0 数组
- **THEN** 报错（三端映射 PyErr/napi Error/throw），构造失败

#### Scenario: 噪声数据报错

- **WHEN** 解析 2 端口文件且网络数据段后跟噪声行（每行 5 项）
- **THEN** token 总数不满足 stride = 9 的整除性，报 `TouchstoneError`
  （消息含实际 token 数与 stride 期望），不静默吞数据

### Requirement: 频率轴入库规则——重复报错、乱序排序

标准（v2.1 规范）要求网络参数数据按频率递增排列。netwave 规则：重复频点
MUST 报错（同频两值是真歧义）；乱序（非单调无重复）MUST 静默排序成递增
入库，不报错不 warning（频点边界由 stride 定、与频率序无关，故乱序与噪声
拒收互不冲突，无 skrf 式误吞）。排序后写出 MUST 为递增序（往返一致）。频率入库
恒 f64 Hz（`#` 行单位倍率在解析层换算，api-contract 既定）。独立真值：
排序为确定性置换，数值逐 bit 不变（同机逐 bit，跨平台引用 manifest
`core_tol`）。

#### Scenario: 乱序文件读入即递增

- **WHEN** 解析频点乱序（如 3,1,2 GHz）的合法文件
- **THEN** `f` 返回递增 Hz 轴，数据行随频点同步重排，无 warning

#### Scenario: 重复频点报错

- **WHEN** 解析含两个相同频点行的文件
- **THEN** 报 `TouchstoneError`（三端映射），消息含重复频点值

### Requirement: 域快捷属性与统一访问器——存储唯一、换算私有

主数据 MUST 只存 S 一份（交错 f64，铁律一布局 `(nfreq, nports, nports)`）；
文件/构造数据为 Y/Z/G/H 时解析/构造时即换算成 S 入库。域快捷属性
`s`/`z`/`y`/`g`/`h` MUST 全存在：`s` 零拷贝返回存储本体，其余现算不缓存
（后端私有 `s_to_domain`）。统一访问器 `data(parameter?, format?)` MUST
覆盖 S/Z/Y/G/H × RI/MA/DB 全组合：默认 `(S, RI)` 零拷贝返回 `s` 本体；
MA/DB 返回 `(nfreq, nports, nports, 2)` 实数对（mag,deg / db,deg）。
MA/DB 语义：角度恒度（规范原文），dB = 20×log₁₀(幅度)（S 参是幅度比）。
返回形状：Python 多维 ndarray（零拷贝视图）；JS/wasm Float64Array + shape
元数据，扁平索引公式 `idx = ((f*n + r)*n + c)*2`（+0=re/mag/db、
+1=im/deg）为三端共享寻址真相。换算函数（`s_to_domain`/`to_ma`/`to_db`）
MUST 全部私有。独立真值：域换算对 skrf golden 对拍（引用 manifest
`core_tol`）；MA/DB 反变换闭式（`mag = 10^(db/20)`）。

#### Scenario: Y 文件读入存 S

- **WHEN** 解析 `# GHZ Y RI` 文件后读 `s` 与 `parameter`
- **THEN** `s` 为 Y→S 换算结果（skrf golden 对拍 `core_tol`），
  `parameter` = `"Y"`（原始域元数据）

#### Scenario: data MA 组合形状与语义

- **WHEN** 调用 `data('S', 'MA')`
- **THEN** Python 得 `(nfreq,nports,nports,2)` ndarray、JS 得
  Float64Array+shape；`[f,r,c,0]`=模、`[f,r,c,1]`=度；与 `s` 的
  `abs`/`angle(deg)` 对拍 `core_tol`

### Requirement: 写出接口——文本与落盘两动词、扩展名 parameter+nports 单源

`writeTouchstone(parameter, format)` MUST 返回 Touchstone 文本（全平铺必填、
无 opts 包、无 `version` 选项——写出直接用存储的 version 字段：解析入口
从文件记录，纯数据构造时由 z0 推导，不在写出时重推；无 `rRef`——
z0 唯一权威），
数字格式化 MUST shortest-roundtrip（写出→读回逐 bit 一致，测试规划既定）。
`writeFile(path, parameter, format)` 实现分层：原生端（Rust/Python/node）
core 内 std::fs 落盘（node async / Python 同步放 GIL / Rust 同步）；
浏览器 wasm core MUST NOT 导出 `writeFile`，该动词只存在于 TS 壳（async，
worker 渲染 + 克隆回传 + Blob 下载）。文件名规则 MUST 由 core 私有
`write_path(path?)` 单源拼出，扩展名恒 = `.{P}Np`（P = 真实参数域、
N = 真实 nports，双双由对象说了算；四形态：空→`name`+`.{P}Np`；
目录→目录+`name`+`.{P}Np`；目录+名→补 `.{P}Np`；带扩展名→按文法剥旧
扩展名重拼正确扩展名）——扩展名的域字母与 n 写错在机制上不可能。
原生端目录歧义以 `is_dir()` 实测判定（末段是已存在目录→拼默认名）。
`path` 原生端必填、浏览器端可选。

#### Scenario: 扩展名自动纠正

- **WHEN** 对 2 端口对象调用 `writeFile("/tmp/x.s3p", 'S', 'RI')`
- **THEN** 实际落盘名为 `x.s2p`（旧扩展名剥除、真实 nports 重拼）

#### Scenario: 写出往返逐 bit 一致

- **WHEN** `writeTouchstone(p, f)` 输出文本再经 `fromText` 读回
- **THEN** `s` 逐 bit 相等、`z0`/`parameter`/`version` 元数据一致
  （同机逐 bit；跨实现比较引用 manifest `core_tol`）

#### Scenario: 浏览器 writeFile 经 worker 且文本在 core

- **WHEN** 浏览器壳调用 `writeFile(path?, parameter, format)`
- **THEN** 主线程零 wasm 执行（铁律八）：worker 消息路由 core 渲染文本 +
  `write_path` 定名，响应 `{text, filename}` 结构化克隆回主线程（浏览器无目录，
  filename 即下载文件名），壳仅做
  Blob + `URL.createObjectURL` + `<a download>` 平台胶

### Requirement: fromUrl 三端统一入口、I/O 全在 core

`fromUrl(url)` MUST 三端可用且 I/O 调用在 core 源码内 cfg 分后端（铁律
十一）：浏览器 `web_sys::fetch` + `wasm_bindgen_futures`（Promise）；node
napi AsyncTask；Python 阻塞 + `allow_threads`。原生端 HTTP 客户端已选
reqwest（rustls，不依赖系统 OpenSSL）；reqwest/tokio MUST cfg 门控 native，
浏览器 wasm 产物 MUST NOT 编译它们。CORS/网络错误 MUST 原样抛出（不吞不
重试）。异步边界同规则适用 `writeFile`/`fromFile`：node MUST async，Python
保持同步 + 放 GIL，Rust core 同步。

#### Scenario: 浏览器 fromUrl 不阻塞主线程

- **WHEN** 浏览器调用 `fromUrl(url)`
- **THEN** 返回 Promise，主线程无 wasm 执行；fetch 失败时错误原样 reject

#### Scenario: wasm 产物零 reqwest

- **WHEN** 构建 wasm32 产物并检查依赖树
- **THEN** reqwest/tokio 不在编译图内（cfg 门控 native 生效）

### Requirement: 名字流水线三件套与 nports 推断

三工厂 MUST 共用同一条名字流水线（`path` 与 `writeFile(path)` 对称，
目录部分直接忽略）：`filenameFromPath(path)` → 含扩展名 filename
（std::path `file_name()`，零新依赖）→ `nameFromFilename(filename)`/
`nportsFromFilename(filename)` 取 stem 与 nports。**`filename` 一词全仓
统一 = 含扩展名文件名，`basename` 退役。** **Touchstone 扩展名文法
（封闭）** = `.` + 域字母（S/Z/Y/G/H 之一）+ 端口数 + `p`，大小写不敏感
（正则 `\.[ghsyz]\d+p`）。`nameFromFilename` 文法不匹配时整段即 stem、
一字符不剥（不按"最后一个点"猜）；`nportsFromFilename` 文法不匹配 MUST
直接报错且消息指引显式传 nports。`fromText(text, nports?, path?)` 的
nports 优先级 = 显式 `nports` 参数 > filename 文法抠 > 两者都无 MUST 报错
（纯数据行列数信息论上无法自推）。`name` 属性语义恒 = 文法剥后的 stem
（无扩展名文件名）。**扩展名读写不对称**（与频率乱序规则同构：可读可
处理，写必正确）：读——扩展名只是 nports 提示，域字母不作准，文件内部
`#` 行 parameter 才是权威；写——私有 `write_path()` MUST 拼正确扩展名
`.{P}Np`；`write_path` MUST NOT 升公开属性（属性收不了参数、原生端藏
`is_dir()` 磁盘 I/O，公开面 `name`/`parameter`/`nports` 已可自拼写出名）。

#### Scenario: nportsFromFilename 无匹配报错

- **WHEN** 调用 `nportsFromFilename("foo.txt")`
- **THEN** 报错，消息指引显式传 nports；不返回猜测值

#### Scenario: nameFromFilename 不猜扩展名

- **WHEN** 调用 `nameFromFilename("2026.10.09")`
- **THEN** 返回整段 `"2026.10.09"`（`.09` 不匹配文法，一字符不剥）

#### Scenario: fromText 双无来源报错、path 含目录可用

- **WHEN** `fromText(text)` 未传 nports 与 path
- **THEN** 报错；而 `fromText(text, path="/tmp/a/b.s4p")` 得 filename="b.s4p"、
  nports=4、`name`="b"（目录忽略、stem 入库）；同传显式 `nports=2` 时显式赢

#### Scenario: 域字母错命名的文件读不纠正、写必纠正

- **WHEN** `# GHZ Z RI` 的 2 端口 Z 文本经 `fromText(text, path="x.s2p")` 读入
- **THEN** `parameter`="Z"（内部 `#` 行为权威，扩展名域字母不作准）；
  其后 `write_path()` 返回 `x.z2p`（写出扩展名域字母与 nports 双双纠正为真值）

#### Scenario: version 写出用存储字段不重推

- **WHEN** 解析 `# GHZ S MA R 50 50 50 50` 的 1.1 四端口文件（全端口同值）
  后立即 `writeTouchstone('S', 'MA')`
- **THEN** 写出 `#` 行仍为 1.1（用解析时记录的 version 字段，不由 z0 重推
  成 1.0）；纯数据构造的对象才在构造时由 z0 推导 version 入库

### Requirement: typing 单源——两 enum 一 error

core MUST 定义 `TouchstoneParameter`（S/Y/Z/G/H）、`TouchstoneFormat`
（RI/MA/DB）两 enum（穷尽匹配、绑定宏反射三端零手抄）与 `TouchstoneError`
（thiserror：重复频点、维度不符、z0 形状非法、语法错、G/H 端口数违例、
nports 无匹配），三端映射 PyErr/napi Error/throw。MUST NOT 定义
`Version` enum（内部 bool + 字符串公开面）、`TouchstoneOptions`（参数
平铺）、`SData` 别名。错误消息 MUST 含 offending 输入原文。

#### Scenario: enum 词汇三端反射一致

- **WHEN** 三端读取 `TouchstoneParameter` 成员集合
- **THEN** 恰为 S/Y/Z/G/H，来自 core 反射（改 core 一处三端重建一致）

#### Scenario: 错误消息携带原文

- **WHEN** 解析含非法 token 的 `#` 行
- **THEN** 三端错误消息均含该 token 原文

### Requirement: 浏览器数据进出 worker 的传输边界

浏览器端 `fromFile(file: File)` MUST 在 TS 壳 `arrayBuffer()` 后以
**transfer**（零拷贝移动、所有权转移）送字节进 worker（复用既有
`{handle, method, args}` + transfer 协议）；写出文本 MUST 经结构化克隆
回传（字符串不可 transfer），峰值 ×2 仅存在于下载触发前，主线程份随
作用域结束 GC 回收。`fromFile` 浏览器签名收 `File`（与原生收 `path`
不同，.d.ts 分端生成，已定接受）。

#### Scenario: 上传字节走 transfer

- **WHEN** 浏览器 `fromFile(file)` 上传数据
- **THEN** postMessage transfer 列表含该 ArrayBuffer，上传后原 buffer
  `byteLength === 0`（detached）
