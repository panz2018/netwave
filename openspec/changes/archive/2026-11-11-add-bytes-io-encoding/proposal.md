# Proposal

## Why

数据进出 core 目前只有字符串边界（`from_text`/`to_text`）：浏览器壳拿到
`File` 后只能自行 `arrayBuffer()` 再走内部协议 `fromBytes`，且该内部路径
用严格 UTF-8 解码，latin-1 编码的真实样本（µ = `0xB5`）必挂；调用方也
无法直接交一段字节进来。字节边界是 I/O 三形态（字符串/字节/文件）中缺
的一环，补齐它才能兑现[测试规划·I/O 边界与编码契约](../../../../Plan/测试规划.md)
定下的读猜写定与编码白名单。

## What Changes

- core 新增 `Touchstone::from_bytes(bytes, nports, path, encoding)`：
  白名单 `{UTF-8, ISO-8859-1}`（别名归一化 `utf8`/`latin1`/`latin-1`/
  `iso88591`）；缺省猜测链 UTF-8（含 BOM 剥离）失败退 ISO-8859-1；
  显式编码即指令、解码失败不兜底；解码后复用 `from_text`，解析逻辑零复制。
- core 新增 `Touchstone::to_bytes(parameter, format, encoding)`：`to_text`
  渲染后编码，缺省 UTF-8；latin-1 编码遇超出 U+00FF 字符报错（JS
  `TextEncoder` 编不出 latin-1，编码必须在 Rust 侧完成）。
- 新增词汇枚举 `TouchstoneEncoding`（与 `TouchstoneParameter`/
  `TouchstoneFormat` 同族同模式，绑定反射暴露）与三个错误变体
  `EncodingUnsupported`/`EncodingDecode`/`CharNotLatin1`（均携带 offending
  输入原文）。
- 三端绑定同名透传：python `from_bytes`/`to_bytes`（收
  `bytes`/`bytearray`/`memoryview`，返回 `bytes`）、node `fromBytes`/
  `toBytes`、浏览器壳 `fromBytes` 由 @internal 升公开并改走 core 新解码
  链、新增 `toBytes` → `Uint8Array`。
- spec 落两处：api-contract 的 fromX 名单加 `from_bytes`/`fromBytes`；
  touchstone-core 新增"字节边界与编码契约"Requirement（含与 skrf 的两条
  有意偏差注记）。

## Capabilities

### New Capabilities

（无——字节边界属 Touchstone I/O 既有能力域的扩展，不另立门户。）

### Modified Capabilities

- `touchstone-core`: 新增"字节边界与编码契约"Requirement——三形态动词矩阵
  的字节行、编码白名单与别名归一化、读缺省猜测链（UTF-8 含 BOM 剥离 →
  ISO-8859-1）、写缺省 UTF-8、显式编码不兜底、latin-1 编码越界报错、
  与 skrf 的有意偏差记录。
- `api-contract`: fromX 构造入口名单加 `from_bytes`/`fromBytes`（该 spec
  自带 Scenario 要求新入口先登记名单）。

## Impact

- 代码：`core/src/touchstone.rs`（枚举、错误变体、两动词、browser dispatch
  的 `fromBytes` 臂改造 + `toBytes` 新臂）、`python/src/lib.rs` +
  `python/netwave/_netwave.pyi`、`typescript/native/src/lib.rs`、
  `typescript/src/index.browser.ts` 与类型面。
- 测试：`core/tests/` 编码边界 unit（内联字节）、python/node/wasm 各端
  绑定测试；覆盖率门槛铁律七不放宽。
- 文档：`openspec/specs/touchstone-core/spec.md`、
  `openspec/specs/api-contract/spec.md`、各子 README、`Plan/测试规划.md`
  动词矩阵与下期清单销账。
- 依赖：无新增 crate（UTF-8 校验用 `std::str::from_utf8`，latin-1 逐字节
  映射手写，无 codec 库）。
- 受影响铁律：三（容差分层——本改动纯字节精确，无数值容差）、七（覆盖率
  100%）、八（worker 数据驻留——`toBytes` 回传走 structured clone）、
  十一（I/O backend 按 target 选择——latin-1 编解码全平台同一实现）、
  十五（fromX 工厂名单）。

## Non-goals

- 不做 `from_file`/`to_file` 与 `write_file`→`to_file` 改名（下轮；本轮
  文件动词维持现状，字节动词与文件动词互不阻塞）。
- 不改 `from_url`：其现走 `resp.text()`（native reqwest / browser fetch），
  与字节猜测链不一致的问题已记 `Plan/测试规划.md` 下期清单，另轮讨论。
- 不立"输出动词 MUST `to_*`"总规矩（`writeFile` 仍在，立规即自相矛盾，
  随 `to_file` 落地轮立）。
- 不支持 UTF-16/ASCII/乱码编码名，不追求 Python `codecs.lookup` 的别名
  全量（窄名单四别名，spec 注明故意子集）。
- 不动 golden/答卷布局（`comments.txt` 等答卷字段属 oracle 重组任务）。

## Prior art

- scikit-rf（BSD-3）读侧同策：猜测链 `utf-8-sig` → `ISO-8859-1`
  （`/config/GitHub/knowledge/RF/scikit-rf/Repo/scikit-rf/skrf/io/touchstone.py` L261–267）；
  写侧白名单经 `codecs.lookup` 归一（`skrf/network.py` L238–248）。
  netwave 采用其读猜测链与白名单思想，偏离两处并记 spec：写缺省 UTF-8
  （skrf 默认 ISO-8859-1）、显式 UTF-8 也剥 BOM（skrf 仅猜测路径剥）。
- SignalIntegrity（GPL-3.0，只读思想不开代码）：`open()` 完全不传
  encoding、吃平台 locale
  （`/config/GitHub/knowledge/RF/SignalIntegrity/repo/SignalIntegrity/SignalIntegrity/Lib/Parsers/ParserFile.py` L31/L40）
  ——反面参照，证明编码契约必要性，不采其行为。
- Rust 生态：`std::str::from_utf8` 做 UTF-8 语法校验（标准库，零依赖）；
  latin-1 无 std 支持，逐字节 `u8 as char` 手写（ISO-8859-1 与 Unicode
  U+0000–U+00FF 一一映射，见 <https://en.wikipedia.org/wiki/ISO/IEC_8859-1>）。

## 专家增补

- 交叉一致性断言：同一 latin-1 字节喂"缺省猜测"与"显式 `ISO-8859-1`"
  结果逐 bit 相同（验证猜测链与显式路径共用同一实现而非两套代码），
  落 `core/tests/touchstone_parse.rs`。
- 健壮性：固定乱码字节序列（含 `0x00`、UTF-16 残留、半截多字节序列）喂
  `from_bytes` 断言报错而非 panic，落 `core/tests/touchstone_parse.rs`；
  proptest 随机字节版记 `Plan/测试规划.md`（core 尚无 proptest 依赖）。
- 真实样本冒烟：`hfss_19.2.s10p`（非 ASCII 注释）走猜测链——samples 尚未
  入库，任务记 `Plan/测试规划.md` 留待 samples 完成后兑现。
