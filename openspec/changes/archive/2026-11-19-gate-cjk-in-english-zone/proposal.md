# Proposal

## Why

语言约定（代码/配置/CI 步骤体属英文区，中文只进 `openspec/` 与 `Plan/`）目前
只有 governance spec 散文，无机器校验。change `drain-stray-profraw-in-tests`
把 profraw 清扫的报错文案写成中文共 18 行（两个 conftest、vitest 钩子、
`ci.yml` 六处步骤体），`pnpm check` 全绿未拦住，靠人工 review 才发现
（账本 LL-106）。本 change 把该约定落成 `scripts/check_comments.py` 的机器
闸门，并清掉现存 3 处英文区中文残留。

## What Changes

- `scripts/check_comments.py` 新增 CJK 检查：对扫描面内六类后缀文件的
  **全部行**（不只注释行）检测 CJK 统一表意文字（`\u4e00-\u9fff`），命中即红。
- 豁免一（形状自动核验）：行内含 `「中文标题」(specs/<capability>/spec.md)`
  形状且闸门现场核验 `openspec/` 下该 spec 文件存在、标题真实存在于该文件，
  则该行放行；引用不成立时报"豁免引用无效"。形状不含 `openspec/` 字样，
  与既有"禁开发文档指针"铁律零冲突。
- 豁免二（门禁白名单）：`scripts/check_*.py` 与 `scripts/tests/` 下文件整
  文件豁免——其内中文是门禁自身的匹配模式、报错文案与自测夹具，属功能零件。
- 存量修复：2 处英文区真违规改写英文（`python/src/lib.rs` 注释、
  `typescript/test/wasm/worker.test.ts` 测试名）；8 处中文 spec 标题引用
  （含 `core/tests/touchstone_write.rs` 一处）补全
  `「标题」(specs/<capability>/spec.md)` 形状使其落入豁免。
- `scripts/tests/test_check_comments.py` 补 CJK 规则自测（红/绿/引用核验/
  白名单四向）。

## Capabilities

### New Capabilities

（无——不新开能力，语言闸门归 governance。）

### Modified Capabilities

- `project-governance`: 新增 Requirement「元规则 语言分区机器闸门」——
  英文区文件出现 CJK 表意文字即 `pnpm check:meta` 失败，含形状豁免与门禁
  白名单两条豁免路径及其核验判据。

## Impact

- 门禁：`scripts/check_comments.py`（新检查 + 两类豁免）、
  `scripts/tests/test_check_comments.py`（自测）。
- 存量源码：`python/src/lib.rs`、`core/tests/touchstone_write.rs`、
  `typescript/test/wasm/worker.test.ts`（改写）；
  `scripts/versions/check_outdated.py`、`scripts/versions/lib/repository.py`
  （spec 引用补路径）。
- 文档：`Plan/覆盖率闸门加固-2026-11-15.md` 第 4 条销账；governance spec
  经 sync 更新。
- 闸门链：`pnpm check:meta` 执法面扩大，`pnpm check` 全套必须转绿。

## Non-goals

- 不做 Markdown 的 CJK 检查（md 归 `scripts/check_md.py`，是否扩面另议）。
- 不查全角标点（`，。（）「」` 等），只查 CJK 统一表意文字。
- 不动 `check_comments.py` 既有"陈旧引用"注释检查的行为与豁免。
- 不在本 change 实现 Plan 同档第 1、2、3 条（show-env 校验、工作区残留
  断言、pytest 收集数断言）。

## Prior art

- 同族校验骨架：`scripts/check_ci.py`（"`test:*` 必须接进 ci.yml"）与
  `scripts/check_comments.py` 现有模式集——同一 `pnpm check:meta` 命令承载。
- 豁免形状核验先例：`scripts/check_proposal.py` 对锚点标记的现场存在性校验
  （同仓库、同口径）。

## 专家增补

- 报错输出打印命中的具体字符与位置（如 `CJK '搬' python/src/lib.rs:71`），
  让人一眼定位而非只报行号——落 `scripts/check_comments.py` 报告格式。
- 豁免形状必须**整形状**匹配（`「…」(openspec/specs/…spec.md)` 缺一不可），
  防止只写 `「标题」` 或只写路径的半截豁免静默放行——自测须含半截形状
  仍红的用例，落 `scripts/tests/test_check_comments.py`。
- `scripts/check_comments.py` 模块 docstring 同步补 CJK 规则与两条豁免的
  说明（英文），保持该文件"自描述门禁"的既有风格。

## 已定裁决

- `全行扫描`：CJK 检查对扫描面文件的全部行生效，不复用既有"只看注释行"
  过滤——LL-106 的中文在 `ci.yml` 的 `run:` 步骤体，非注释行。
- `表意文字集`：字符集只取 CJK 统一表意文字 `\u4e00-\u9fff`，不含全角标点。
- `形状豁免`：行内含 `「中文标题」(specs/<capability>/spec.md)` 且 `openspec/`
  下文件存在、标题真实即放行；不发明新标记名词，存量引用补路径即自动豁免。
  形状用相对 `openspec/` 的 `specs/...` 而非 `openspec/specs/...`，避免与
  既有"禁 `openspec/` 指针"铁律冲突（核验时闸门补 `openspec/` 前缀）。
- `门禁白名单`：`scripts/check_*.py` 与 `scripts/tests/` 整文件豁免，范围
  锁死门禁自身与门禁自测，业务代码不入。
- `中文区豁免`：`openspec/` 与 `Plan/` 属中文区，CJK 检查不扫（沿用既有
  豁免目录机制）。
- `存量改写`：2 处英文区真违规（`python/src/lib.rs`、
  `typescript/test/wasm/worker.test.ts`）改写英文，8 处中文 spec 标题引用
  补形状豁免，不用豁免保留真违规。
- `自测同轮`：CJK 规则同轮补 `scripts/tests/test_check_comments.py` 自测，
  含无标记中文行红、形状豁免绿、假路径引用红、半截形状红、白名单不报。
- `体检跳过`：本 change 一次性跳过归档态 health-check 只读体检（archive
  guidance 默认必做项，人工点名仅本次归档适用，不改后续 change 默认；apply
  态全文体检 4.3 照常执行）。
