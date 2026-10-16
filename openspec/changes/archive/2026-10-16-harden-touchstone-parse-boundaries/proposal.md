# Proposal

## Why

`Plan/测试规划.md` 已拍板"特殊格式（CRLF、无尾换行、异常空白、科学计数法、
负零、大端口数）的解析支持全部由 Rust core unit 层承担"，但现有 `core/tests/`
对这类排版变体没有显式断言——解析器"碰巧能过"与"契约保证能过"是两回事，
无断言即无回归保护。同时多 `#` 选项行的处理（规范 v2.1 "additional option
lines after the first one shall be ignored"）此前实现为"后者覆盖前者"（已修），
但主 spec 从未写明该规则，属于契约缺口。

## What Changes

- 主 spec `touchstone-core` 补写多 `#` 选项行规则：第一个 `#` 行生效且完整
  校验，其后所有 `#` 行整行跳过、不解析不校验（即使含非法 token 或复数 R
  也不报错）；复数 R 出现在生效选项行 MUST 报错并点名 offending token
- 新增"排版变体解析"契约：CRLF 行尾、无尾换行、token 间异常空白（tab/多
  空格/行首缩进）、科学计数法输入 token、负零读入符号位保留、最大 32 端口
  端到端解析，全部 MUST 成功且数值 bit 级正确
- 补齐对应 unit 测试（`core/tests/touchstone_parse.rs` 内联文本，不新增
  testdata 文件——变体文件不进 testdata 是已定裁决）

无 BREAKING：多选项行"第一个生效"修复已落地（commit `a1aa4a8`），本 change
将其升格为 spec 契约并补测试；其余为纯测试补强。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `touchstone-core`: 新增两条 Requirement——"多 # 选项行——第一个生效且完整
  校验，后续整行忽略"（含复数 R 场景）与"排版变体解析——行尾/换行/空白/
  记数法/负零/大端口"；现有 Requirement 文本不改

## Impact

- `openspec/specs/touchstone-core/spec.md`（归档时 sync）
- `core/tests/touchstone_parse.rs`（新增测试，预计 +8~10 个）
- `core/src/touchstone.rs`（仅当测试暴露缺陷才动；多选项行修复已在库）
- 不涉及绑定层公共 API、不涉及 testdata/golden/manifest
- 关联账本：LL-053（规范缺省逐关键词抄原文）、LL-042（精确比较逐 bit）、
  LL-055（2 端口列序）
