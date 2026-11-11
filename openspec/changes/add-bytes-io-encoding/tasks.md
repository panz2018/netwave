# Tasks

## 1. core：编码词汇与解码（先 red 后 green）

- [ ] 1.1 先在 `core/tests/touchstone_parse.rs` 写失败测试：
      `TouchstoneEncoding` 归一化解析——受理 `"UTF-8"` `"utf8"` `"ISO-8859-1"`
      `"latin1"` `"Latin_1"` `"iso88591"`，拒绝 `"UTF-16"` `"ASCII"` `"latin"`
      `"L1"` `"cp819"` 与乱码名并报 `EncodingUnsupported` 且消息含原词。
      验证：`cargo test -p netwave encoding` 编译失败或断言红
- [ ] 1.2 在 `core/src/touchstone.rs` 实现 `TouchstoneEncoding`（`AsRefStr` + `EnumIter` + `FromStr`，归一化 trim/小写/去连字符下划线空格，
      别名集 `utf8`/`iso88591`/`latin1`）与错误变体 `EncodingUnsupported`
      /`EncodingDecode`/`CharNotLatin1`（均携带 offending 输入）。
      验证：1.1 转绿
- [ ] 1.3 先写失败测试：`from_bytes` 猜测链——latin-1 含 `0xB5` 缺省解析
      成功、BOM 缺省与显式 UTF-8 均剥离、显式 UTF-8 喂 latin-1 报
      `EncodingDecode` 不兜底、显式 ISO-8859-1 不剥 BOM 保留 `ï»¿`、
      缺省猜测与显式指定同果交叉断言。验证：`cargo test -p netwave` 红
- [ ] 1.4 实现私有 `decode_bytes`（UTF-8 剥 BOM 后 `std::str::from_utf8`，
      缺省失败退 latin-1 逐字节直映；显式失败不兜底）与公开
      `Touchstone::from_bytes`（解码后转发 `from_text`）。验证：1.3 转绿
- [ ] 1.5 先写失败测试：`to_bytes`——缺省 UTF-8 使 µ 编为 `0xC2 0xB5`、
      ISO-8859-1 使 µ 编为 `0xB5`、超 U+00FF 字符报 `CharNotLatin1` 含
      该字符、`0x00..=0xFF` 全 256 字节 latin-1 round-trip、字节往返
      bit 级闭环、乱码字节（`0x00`/UTF-16 残留/半截多字节）报错不 panic。
      验证：`cargo test -p netwave` 红
- [ ] 1.6 实现 `Touchstone::to_bytes`（`to_text` 渲染后编码；latin-1 编码
      要求 `char as u32 <= 0xFF` 否则报错）。验证：1.5 转绿，
      `cargo test -p netwave` 全绿且 `cargo llvm-cov -p netwave` 新代码
      行覆盖 100%（铁律七）

## 2. browser dispatch 与浏览器壳

- [ ] 2.1 改 `core/src/touchstone.rs` browser dispatch：`fromBytes` 臂参数
      扩为 `(bytes, nports, path, encoding)` 并改调 `Touchstone::from_bytes`
      （修严格 UTF-8 缺口）；新增 `toBytes` 实例臂（调 `to_bytes`，回包
      `js_sys::Uint8Array`）。验证：`cargo build`（features `browser`，
      target `wasm32-unknown-unknown`）通过
- [ ] 2.2 改 `typescript/src/index.browser.ts`：`fromBytes` 由 @internal 升
      公开（签名 `(bytes, nports?, path?, encoding?)`，bytes 走 transfer）、
      新增 `toBytes(parameter, format, encoding?)` 返回 `Uint8Array`；
      `fromFile` 内部调用补参数占位；同步类型面与 JSDoc（英文，教学式：
      说明读猜写定与白名单）。验证：`pnpm -C typescript exec tsc --noEmit`
      通过

## 3. python / node 绑定

- [ ] 3.1 python：`python/src/lib.rs` 加 `from_bytes`（收 buffer 协议三件套
      bytes/bytearray/memoryview，signature 为
      `(bytes, nports=None, path=None, encoding=None)`）与 `to_bytes`
      （返回 `bytes`），GIL 释放策略同 `from_text`；
      `python/netwave/_netwave.pyi` 同步。验证：
      `python/tests/test_touchstone_class.py` 新增用例（latin-1 猜测、
      显式报错、往返闭环、白名单外报错）全绿，`pytest --cov` 新行 100%
- [ ] 3.2 node：`typescript/native/src/lib.rs` 加 `fromBytes`/`toBytes`
      （`Uint8Array` 收发，Buffer 系其子类）。验证：
      `typescript/test/native/touchstone.test.ts` 新增用例全绿，vitest
      lines/branches 100%

## 4. 跨端对拍与全量闸门

- [ ] 4.1 wasm（Node 宿主）测试补 `fromBytes`/`toBytes` 用例（latin-1 字节
      经 worker 猜测链、`toBytes` 回传 `Uint8Array`）。验证：
      `pnpm -C typescript test:wasm` 全绿
- [ ] 4.2 cross-binding 对拍：`fromBytes` 签名变化若影响 dump 路径则同步
      `typescript/scripts/dump.mjs`；确认 `oracle/scripts/compare_cross.py`
      现有字段集全绿（本 change 不新增答卷字段）。验证：`pnpm check:cross`
      退出码 0
- [ ] 4.3 全量闸门：`cargo test -p netwave`、`cargo fmt --check`、
      `cargo clippy`（all-targets，`-D warnings`）、`pnpm check`、
      `pnpm check:md`。验证：各命令退出码 0

## 5. 文档与波及面同步（LL-034）

- [ ] 5.1 spec 主文件同步：本 change 两个 delta 经 archive/sync 落入
      `openspec/specs/touchstone-core/spec.md` 与
      `openspec/specs/api-contract/spec.md`（fromX 名单含 `fromBytes`/
      `from_bytes`）。验证：`openspec validate add-bytes-io-encoding`
      通过；sync 后主 spec 无重复 Requirement 块
- [ ] 5.2 README 同步（英文）：`core/README.md`、`python/README.md`、
      `typescript/README.md` 动词清单加 `from_bytes`/`to_bytes`（一句话 + 编码白名单与读猜写定指针，坑留账本）。验证：`pnpm check:md`
      退出码 0
- [ ] 5.3 `Plan/测试规划.md` 同步：动词矩阵 `enc?` 改 `encoding?`；I/O
      落地条目中本轮完成部分删除（结论入 spec），保留延后项——from_url
      改 bytes+猜测链、property 随机字节不 panic、`hfss_19.2.s10p` 真实
      样本猜测链冒烟（待 samples 入库）。验证：`pnpm check:md` 退出码 0，
      Plan 内无已完成条目残留
- [ ] 5.4 账本时效：实施中若踩坑（如 BOM/别名判定返工），按反思铁律在
      `openspec/specs/lessons-learned/` 登记或引用既有条目。验证：INDEX
      与分片一致，`pnpm check:md` 绿

## 6. 收尾体检

- [ ] 6.1 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾
      体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍，含全局
      CLI/直装工具的机器级升级；上游 bug/不兼容登记回退不阻塞；仅设计级
      适配、restrictions.json 破损、流程走不通才停下报告；下限变更等人工
      发起）。验证：消化后复跑 `pnpm check:outdated` 退出码 0（SUMMARY
      归零）

## Workflow follow-up

- 实施完成经用户点名后 archive：归档前执行 Plan/ 瘦身检查与 openspec/specs/
  全目录三态时效检查（更新/新增/退役），`specs/README.md` 路由表随增删同步。
- 延后项（from_url 改造、`from_file`/`to_file`/`write_file` 改名 `to_file`、
  "输出动词 MUST `to_*`"入 spec、property 随机字节、真实样本冒烟）留在
  `Plan/测试规划.md`，另立 change。
