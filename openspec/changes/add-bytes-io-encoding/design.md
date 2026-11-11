# Design

## Context

见 proposal.md - Why。现状：core 只有 `from_text`/`to_text` 字符串边界；
browser dispatch 已有 `fromBytes` 臂但走严格 `String::from_utf8`（latin-1
样本必挂）且仅 @internal；python/node 的 `from_file` 各自读文件后喂
`from_text`。词汇枚举既有模式：`TouchstoneParameter`/`TouchstoneFormat` 用
`strum` 的 `AsRefStr`+`EnumIter` + 手写 `FromStr`（大小写不敏感、offending
token 入错误），编码枚举照抄此模式。

## Goals / Non-Goals

**Goals:**

- 字节边界 = 编解码薄层 + 转发既有 text 动词，解析/渲染逻辑零复制。
- 编解码全平台同一 Rust 实现（wasm/native/python/node 共用 core，铁律十一
  的"按 target 选 backend"只发生在 I/O，编解码不分支）。
- 错误消息三端可引用原词（沿用 `TouchstoneError` 携带 offending 输入的
  既有约定）。

**Non-Goals:**

- 设计级：不做编码自动嗅探（chardet 类统计推断）——猜测链只有 UTF-8/
  latin-1 两档语法判定，无启发式。
- 不引入 codec 依赖（`encoding_rs`/`chardetng` 等），理由见下文
  「latin-1 编解码手写」决策。

## Decisions

### D1 `TouchstoneEncoding` 枚举而非 `&str` 透传

变体 `Utf8`/`Iso88591`，`AsRefStr` 给规范名（`"UTF-8"`/`"ISO-8859-1"`），
`FromStr` 做归一化匹配：输入 `trim` + 转小写 + 去 `-`/`_`/空格后，与
规范名及别名集 `{utf8, iso88591, latin1}` 比对。拒绝集天然形成：归一化后
不在表内（`utf16`、`ascii`、`latin`、`l1`、`cp819`）即
`EncodingUnsupported{token}`。
备选：接受任意 str 交给 codec 库查表——拒：引入依赖且违背"白名单窄集"
裁决（Q13）；别名硬编码进 match 臂而非归一化函数——拒：归一化一处维护，
match 只留语义分支。
绑定反射暴露沿用 `TouchstoneParameter` 既有路径（`iter()` + `as_ref()`），
python/node 壳不复制名单。

### D2 latin-1 编解码手写，不引 codec crate

解码：`bytes.iter().map(|b| *b as char).collect::<String>()`（ISO-8859-1
与 U+0000–U+00FF 一一映射，恒成功）。编码：`char as u32 <= 0xFF` 则
`as u8`，否则 `CharNotLatin1{ch}`。
备选：`encoding_rs`（rustls 生态、whatwg 标准实现）——拒：为 256 项一一
映射引依赖不成比例，且 whatwg 的 windows-1252 家族语义反而引入本变更
不需要的表；`latin1` crate——拒：非维护活跃、同上。

### D3 猜测链与显式路径共用一个解码函数

私有 `decode_bytes(bytes, Option<TouchstoneEncoding>)` 返回
`Result<String, TouchstoneError>`：`None` → `from_utf8`（先剥 `EF BB BF`）
失败退 latin-1；`Some(Utf8)` → 剥 BOM 后严格校验，失败 `EncodingDecode`；
`Some(Iso88591)` → 直映不剥 BOM。`from_bytes` 公开动词 = `decode_bytes` +
`from_text` 转发；browser dispatch 的 `fromBytes` 臂改调 `from_bytes`
（顺带修复严格 UTF-8 缺口与 nports/path 参数位）。
备选：猜测链写在 dispatch 层——拒：三端各写一份必漂移，"缺省 vs 显式
同果"Scenario 即防此。

### D4 `to_bytes` = `to_text` + 编码；`toBytes` 回传走 structured clone

core 返回 `Vec<u8>`；browser dispatch 包 `js_sys::Uint8Array::new`（拷贝
语义，与 `f64_array` 同模式——输出方向不 transfer，输入方向 `fromBytes`
的 bytes 由壳 transfer 进 worker，维持铁律八单所有权）。python 返回
`PyBytes`；node 返回 `Buffer`（napi `Uint8Array` 构造，node 侧 Buffer 即
其子类视图）。
备选：node 返回 `ArrayBuffer`——拒：生态惯例 Buffer/Uint8Array，与既定
裁决（JS 收发统一 Uint8Array）一致。

### D5 python 入参收 buffer 协议三件套

`&Bound<PyAny>` → `extract::<&[u8]>`（bytes/bytearray/memoryview 原生支持），
不收 numpy uint8（要 `tobytes()` 一行自转）。返回 `bytes`（不可变，与
`to_bytes` 语义匹配）。

### D6 错误变体三枚，不复用 `Syntax`

`EncodingUnsupported{name}`/`EncodingDecode{encoding}`/`CharNotLatin1{ch}`
独立成变体而非塞 `Syntax{token}`：编码错误与语法错误的用户自救路径不同
（改 `encoding` 参数 vs 改文件内容），消息模板分开。`TouchstoneError` 加
变体非破坏性（穷举 match 仅 core 内部两处 dispatch 检查，编译器兜底）。

## Risks / Trade-offs

- [猜测链误判：恰为合法 UTF-8 的 latin-1 文件（纯 ASCII 或碰巧合法多字节）
  按 UTF-8 解出不同字符] → 行业同策（skrf 同链），spec 已定"读缺省=猜"；
  要确定性显式传 `encoding`；unit 有"缺省 vs 显式同果"交叉断言兜底。
- [读猜写定不闭环：latin-1 进、默认 UTF-8 出，µ 字节变化] → 有意偏差已
  记 spec 与 proposal Prior art；往返 Scenario 按"同编码闭环"判定。
- [browser `fromBytes` 升公开后参数从 2 个变 4 个（加 nports/encoding）]
  → 旧调用 `(bytes, path)` 位置不变，新参数居后，壳内 `fromFile` 调用点
  同步补 `null` 占位；@internal 升公开无兼容包袱。
- [latin-1 手写映射出错] → 256 项全表 unit 断言（`0x00..=0xFF` 逐字节
  round-trip），成本一行循环，错即红。

## Migration Plan

纯新增 API，无迁移。回滚 = revert 本 change 提交（无数据布局变更、无
既有动词签名改动）。

## Open Questions

（无——15 条裁决已在 grilling 轮全部拍板；延后项 from_url/文件动词/
property 随机字节均记 Plan/测试规划.md，不属本 change。）
