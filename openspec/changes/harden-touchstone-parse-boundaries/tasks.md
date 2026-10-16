# Tasks

## 1. 排版变体解析测试（先写测试暴露缺陷，再修实现）

- [ ] 1.1 在 `core/tests/touchstone_parse.rs` 新增 CRLF 行尾 + 无尾换行测试：同一 2 端口数据分别以 `\r\n` 结尾且末行无换行、LF 结尾两种文本解析，断言频点与 S 缓冲逐 bit 相同（`to_bits()` 比较，LL-042 不引容差）。验证：`cargo test -p netwave --test touchstone_parse` 通过；若首跑失败即为解析缺陷，修 `core/src/touchstone.rs` 后复跑转绿
- [ ] 1.2 新增异常空白 + 科学计数法测试：数据行含 tab、连续多空格、行首缩进，数值以 `1.0e+0`、`-3e-1` 形式书写，断言解析成功且与等值十进制书写逐 bit 相同。验证：同上命令通过
- [ ] 1.3 新增负零符号位测试：数据含 `-0.0`，断言存储值 `to_bits() == (-0.0f64).to_bits()`。验证：同上命令通过

## 2. 大端口端到端解析测试

- [ ] 2.1 新增 32 端口端到端测试：nports=32、单频点 2049 个数字 token 的合法文本（程序化生成 token 串），断言 `nports()==32`、S 缓冲长度 2048、频点按选项行单位换算入 Hz 轴。验证：`cargo test -p netwave --test touchstone_parse` 通过

## 3. 多选项行契约核对（实现已在库，补 spec 场景对齐）

- [ ] 3.1 核对 `option_line_second_line_ignored_first_wins`、`option_line_invalid_second_line_still_ignored`、`option_line_complex_r_errors_with_offending_token` 三个既有测试与本 change spec 三场景一一对应，缺断言者补齐（如第一场景须同时断言 z0=50 与 MA 反变换数值）。验证：`cargo test -p netwave --test touchstone_parse` 通过且场景覆盖无缺口

## 4. 闸门与文档收尾

- [ ] 4.1 跑 `cargo test -p netwave`、`cargo clippy --workspace`、`cargo fmt --check` 全绿；若 1.x 改过 `core/src`，按 LL-019 重建 python/node/wasm 绑定并跑各端既有测试确认无回归。验证：三命令退出码 0，绑定测试绿
- [ ] 4.2 按 apply guidance 瘦身 `Plan/测试规划.md`：删除本 change 已完成的"Touchstone 解析边界"中已落地条目（保留未执行项），跑 `pnpm check:md` 退出码 0。验证：check:md 绿
