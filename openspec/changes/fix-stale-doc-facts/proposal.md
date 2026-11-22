# Proposal

## Why

change `add-wasm-rust-coverage` 归档后的 archive 态体检（2026-11-22）发现三处
文档事实陈旧：LL-106 账本条目仍写「CJK 闸门待落门禁」并指向已被删除的 Plan
文件（断链）；`scripts/README.md` 脚本表缺录 4 个已存在并被 CI 调用的脚本
（LL-034 波及面漏改）；`CONTRIBUTING.md` Quick start 漏 `pnpm test:wasm`。
三处均已实测核实，属纯文档修复，不动任何 Requirement 正文。

## What Changes

- `openspec/specs/lessons-learned/docs.md` LL-106「复发检测」段改写为
  「已落闸门 `scripts/check_comments.py`」（CJK 正则 + 白名单豁免，已接入
  `check:meta`），删除对已不存在的 `Plan/覆盖率闸门加固-2026-11-15.md` 的
  断链指针。
- `scripts/README.md` Scripts 表补录 `run/test_wasm.sh`、`run/test_cross.sh`、
  `install_wasi_sdk.sh`、`install_wasm_bindgen_cli.sh` 四行。
- `CONTRIBUTING.md` Quick start 代码块补 `pnpm test:wasm` 一行（注明薄调用
  `scripts/run/test_wasm.sh`）。
- 修复完成后删除 `Plan/体检发现-2026-11-22.md`（结论全部被本 change 吸收，
  Plan/ 不留存）。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- 无——三处修改均为既有事实的文档更正，不改任何 spec Requirement；
  `.openspec.yaml` 已设 `skip_specs: true`（doc-only 先例：
  archive/2026-11-15-harden-overreach-check）。

## Impact

- 文档三处 + Plan/ 一个文件删除；无代码、无 CI、无公开 API 改动。
- 闸门波及：改 `.md` 必跑 `pnpm check:md`；动 `openspec/specs/` 须过
  `pnpm check:meta`（`check_md.py` / `check_comments.py` 扫 specs 目录）。

## Non-goals

- 不新增或修改任何 spec Requirement、不改 `scripts/check_comments.py` 本体。
- 不顺手改写 LL-106 条目其余段落（犯过/规则段事实仍准确，保持原样）。
- 不处理体检报告「已查，无」维度之外的任何存量问题。

## Prior art

- 账本条目直改先例：archive/2026-11-19-gate-cjk-in-english-zone（delta 只含
  project-governance，LL-106 条目本体直接改账本）。
- doc-only change 先例：archive/2026-11-15-harden-overreach-check
  （`.openspec.yaml` 设 `skip_specs: true`）。

## 专家增补

- 改写账本后跑 `pnpm check:meta` 而非只跑 `pnpm check:md`——
  `scripts/check_md.py` 与 `scripts/check_comments.py` 均扫
  `openspec/specs/`，账本改写若引入新断链指针会被当场拦。

## 已定裁决

- `三项全修`：体检发现 1/2/3 全部修复，不挑选。
- `新开change-fix-stale-doc-facts`：无在途 change，按 AGENTS.md 琐碎文档修复
  亦须进 change 承载，命名 `fix-stale-doc-facts`。
- `修完即删Plan体检报告`：三项结论被本 change 吸收后当场删除
  `Plan/体检发现-2026-11-22.md`，不等归档。
- `skip-specs文档形态`：不建 specs delta，`.openspec.yaml` 设
  `skip_specs: true`，归档走 doc-only 路径。
