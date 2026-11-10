# Spec Delta

## MODIFIED Requirements

### Requirement: 2 端口列序——文件 legacy 序、内部恒 row-major、I/O 边界换回

Touchstone v1.x 约定 2 端口文件的列序为 `N11, N21, N12, N22`（off-diagonal
反序，规范 v2.1 "1-port and 2-port Networks" 节；v2.x 用
`[Two-Port Data Order] 21_12|12_21` 显式声明，本实现按 v1.x legacy `21_12`
读入）；3 端口及以上为行主序 `N11, N12, N13 / N21, …`。netwave 规则：
**内部存储恒 row-major**（`(nfreq, nports, nports)`，铁律一布局），
2 端口文件解析时 MUST 在 I/O 边界交换 off-diagonal 对（位置 2↔4、3↔5
的 re/im 交错对），使 `s`/`z`/`y`/`g`/`h` 与 `data()` 对任意 nports 都
是统一 row-major——消费者 MUST NOT 为 nports=2 做特殊索引。写出时
MUST 在 I/O 边界换回 legacy 序（交换为自逆），保证写出文本可被任何
v1.x 工具正确读入。3 端口及以上读写均无交换（文件序=row-major）。
skrf 同策（`io/touchstone.py` rank==2 时 transpose）；rf-touchstone
内部存转置矩阵为反例，不采。

#### Scenario: 2 端口文件读入交换 off-diagonal

- **WHEN** 解析 `# GHZ S RI R 50` + `1.0 1 2 3 4 5 6 7 8`
  （文件序 S11=1+2j, S21=3+4j, S12=5+6j, S22=7+8j）
- **THEN** `s` = `[1,2, 5,6, 3,4, 7,8]`（row-major：S11, S12, S21, S22），
  off-diagonal 对在 I/O 边界交换，内部无 2 端口特殊序

#### Scenario: 3 端口文件读入无交换

- **WHEN** 解析合法 3 端口文件（stride=19）
- **THEN** 数据逐 token 原样入 row-major 存储，无交换

#### Scenario: 2 端口写出换回 legacy 序且往返 bit-exact

- **WHEN** 对非对称 2 端口网络调用 `to_text(S, RI)`
- **THEN** 数据行为 legacy 序（S11, S21, S12, S22）；重新解析得
  与原始 `s` 逐 bit 相同的 row-major 存储

### Requirement: 写出接口——文本与落盘两动词、扩展名 parameter+nports 单源

`toText(parameter, format)` MUST 返回 Touchstone 文本（全平铺必填、
无 opts 包、无 `version` 选项——写出直接用存储的 version 字段：解析入口
从文件记录，`fromData` 工厂构造时由 z0 推导，不在写出时重推；无 `rRef`——
z0 唯一权威），
数字格式化 MUST shortest-roundtrip（写出→读回逐 bit 一致，测试规划既定）。
2 端口写出 MUST 按 v1.x legacy 列序（`N11, N21, N12, N22`）在 I/O 边界
换回（见「2 端口列序」需求），内部 row-major 不外泄。
`writeFile(path, parameter, format)` 实现分层：原生端（Rust/Python/node）
core 内 std::fs 落盘（node async / Python 同步放 GIL / Rust 同步）；
浏览器 wasm core MUST NOT 导出 `writeFile`，该动词只存在于 TS 壳（async，
worker 渲染 + 克隆回传 + Blob 下载）。文件名规则 MUST 由 core 私有
`write_path(path?, parameter)` 单源拼出，扩展名恒 = `.{P}Np`（P = 真实写出的
parameter（写出动词实参，扩展名与文件内容同域）、
N = 真实 nports，双双由对象说了算；四形态：空→`name`+`.{P}Np`；
目录→目录+`name`+`.{P}Np`；目录+名→补 `.{P}Np`；带扩展名→按文法剥旧
扩展名重拼正确扩展名）——扩展名的域字母与 n 写错在机制上不可能。
原生端目录歧义以 `is_dir()` 实测判定（末段是已存在目录→拼默认名）。
`path` 原生端必填、浏览器端可选。

#### Scenario: 扩展名自动纠正

- **WHEN** 对 2 端口对象调用 `writeFile("/tmp/x.s3p", 'S', 'RI')`
- **THEN** 实际落盘名为 `x.s2p`（旧扩展名剥除、真实 nports 重拼）

#### Scenario: 写出往返一致

- **WHEN** `toText(p, f)` 输出文本再经 `fromText` 读回
- **THEN** `f = RI` 时 `s` 逐 bit 相等（shortest-roundtrip 十进制保证）；
  `f = MA/DB` 时 `s` 在 manifest `core_tol` 容差内相等（极坐标↔直角为
  超越函数换算，逐 bit 物理不可能，容差即标准）；`z0`/`parameter`/
  `version` 元数据恒一致
  （同机逐 bit；跨实现比较引用 manifest `core_tol`）

#### Scenario: 浏览器 writeFile 经 worker 且文本在 core

- **WHEN** 浏览器壳调用 `writeFile(path?, parameter, format)`
- **THEN** 主线程零 wasm 执行（铁律八）：worker 消息路由 core 渲染文本 +
  `write_path` 定名，响应 `{text, filename}` 结构化克隆回主线程（浏览器无目录，
  filename 即下载文件名），壳仅做
  Blob + `URL.createObjectURL` + `<a download>` 平台胶

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
  后立即 `toText('S', 'MA')`
- **THEN** 写出 `#` 行仍为 1.1（用解析时记录的 version 字段，不由 z0 重推
  成 1.0）；纯数据构造的对象才在构造时由 z0 推导 version 入库
