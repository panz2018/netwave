# Proposal

## Why

输出动词 `write_touchstone` 与读侧 `from_text` 不成对：`from_*`/`to_*` 天然押韵，
`write_*` 是另起的家族名，且 `write_` 会让调用者误以为落盘（实际纯渲染不碰 I/O）。
Rust 惯例（`to_*` = 借 `&self` 造新值）与同生态位实现（serde_json `to_string`、
pandas `to_csv`）都站在 `to_*` 一边。对象已是 `Touchstone`，`_touchstone` 后缀不携带
信息。未发布期改名零破坏，现在改成本最低。

## What Changes

- **BREAKING**（未发布期豁免）core `Touchstone::write_touchstone` 改名
  `Touchstone::to_text`，签名 `(parameter, format)` 不变。
- 三端绑定同步改名：python `write_touchstone`→`to_text`、node
  `write_touchstone`→`to_text`、浏览器 dispatch 臂 `"writeTouchstone"`→`"toText"`
  及壳方法 `writeTouchstone`→`toText`。
- `scripts/check_verbs.py`：`TOUCHSTONE_VERBS` 集合 `writeTouchstone`→`toText`；
  退役名 `writeTouchstone` 进 `FORBIDDEN` 防复活。
- 主 spec `touchstone-core`「写出接口」Requirement 内动词名同步 `to_text`/`toText`。
- `Plan/测试规划.md`：删除已落地的改名条目，新增「输出动词家族统一 `to_*` 前缀 +
  spec 钉死规矩」未来执行项。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `touchstone-core`: 「写出接口」Requirement 的文本渲染动词由 `writeTouchstone`
  更名为 `toText`（Rust `to_text`），行为、签名、容差、列序规则均不变——仅动词名变。

## Impact

- 代码：`core/src/touchstone.rs`、`python/src/lib.rs`、`typescript/native/src/lib.rs`、
  `typescript/src/index.browser.ts`。
- 测试：`core/tests/touchstone_write.rs`、`python/tests/test_touchstone_class.py`、
  `typescript/test/native/touchstone.test.ts`、`typescript/test/wasm/touchstone.test.ts`。
- 闸门/typing：`scripts/check_verbs.py`、`python/netwave/_netwave.pyi`（stub_gen 重生成）。
- 文档：`openspec/specs/touchstone-core/spec.md`、`Plan/测试规划.md`。
- 不涉及：`write_file`/`writeFile`、私有 `write_path`、`from_text`（已存在）、
  依赖版本、数据布局。

## Non-goals

- 不改 `write_file`/`writeFile`（落盘动词留下个 change，本刀只动文本动词）。
- 不新增 `to_bytes`/`from_bytes`、不加 `encoding` 参数与编码白名单（属 I/O 字节边界刀）。
- 不在本 change 立「输出动词统一 `to_*` 前缀」的 spec 规矩——`writeFile` 仍在，
  此刻立规即自相矛盾；该约定写入 `Plan/测试规划.md` 待家族改齐时落地。
- 不改浏览器 `toFile` 的返回载荷（保持 `{text, filename}`，不字节化）。

## Prior art

- serde_json：`to_string`/`to_vec`/`to_writer` ↔ `from_str`/`from_slice`/`from_reader`
  （<https://docs.rs/serde_json>）——`to_*`/`from_*` 成对惯例的生态实证。
- pandas `to_csv`/`to_json`/`to_numpy`（<https://pandas.pydata.org>）——输出动词
  取 `to_*` 的同生态位实现。
- 仓库内裁决出处：`Plan/测试规划.md`「I/O 边界与编码契约」节已定「输出动词取
  `to_*` 而非 `write_*`」及其 Rust 惯例/clippy `wrong_self_convention` 论证。

## 专家增补

- 退役名防复活：`writeTouchstone` 进 `scripts/check_verbs.py` 的 `FORBIDDEN`，
  沿用 `free`/`release` 同款绊线惯例，杜绝旧名手滑写回公开产物。
- 波及面同步（LL-034）：改名 MUST 同轮改 `check_verbs.py` 与主 spec，否则闸门红、
  spec 与代码矛盾；`_netwave.pyi` 经 stub_gen 重生成而非手改，避免手写漂移。
- 过渡态显式记录：本刀后 `to_text` 与 `write_file` 短期并存，`Plan/测试规划.md`
  的未来项标注消除路径，防止读者误以为家族已改齐。
