# Spec Delta

## ADDED Requirements

### Requirement: 元规则 语言分区机器闸门

文档语言约定（代码/配置/CI 步骤体属英文区，中文只进 `openspec/` 与 `Plan/`）
MUST 由 `scripts/check_comments.py`（命令 `pnpm check:meta`）机器强制：对扫描
面内六类后缀（`.rs`/`.py`/`.ts`/`.yml`/`.yaml`/`.toml`）文件的**全部行**（不
限注释行）检测 CJK 统一表意文字（`\u4e00-\u9fff`），命中即红。全角标点不属
被禁字符。仅两条豁免路径——有效 spec 标题引用形状、门禁自身与自测白名单——
判据见场景；`openspec/` 与 `Plan/` 属中文区，沿用既有豁免目录机制不扫。

#### Scenario: 英文区文件出现中文即红

- **WHEN** 扫描面内某六类后缀文件的任一行（含 `ci.yml` 的 `run:` 步骤体等非
  注释行）出现 CJK 统一表意文字，且该行无有效豁免
- **THEN** `pnpm check:meta` 失败，报告指明文件、行号与命中的具体字符

#### Scenario: 有效 spec 标题引用放行

- **WHEN** 某行含 `「过期体检命令」(specs/dependency-upgrade/spec.md)` 且该
  spec 文件存在、`过期体检命令` 确为该文件中的标题
- **THEN** `pnpm check:meta` 对该行放行，不因中文报错

#### Scenario: 无效 spec 引用不放行

- **WHEN** 某行含 `「不存在标题」(specs/dependency-upgrade/spec.md)`（标题在
  该文件不存在）或路径指向不存在的 spec 文件
- **THEN** `pnpm check:meta` 失败并报"豁免引用无效"

#### Scenario: 半截豁免形状不放行

- **WHEN** 某行只含 `「某标题」`（缺路径）或只含 `(specs/.../spec.md)`（缺
  中文标题），形状不完整
- **THEN** `pnpm check:meta` 对该行照常检测中文，半截形状不产生豁免

#### Scenario: 门禁自身与自测文件不误报

- **WHEN** `scripts/check_md.py` 的 `STAGE_WORDS` 含中文匹配模式，或
  `scripts/tests/` 下自测夹具含中文诱饵
- **THEN** `pnpm check:meta` 通过——这些文件在门禁白名单内整文件豁免

#### Scenario: 中文区目录不扫

- **WHEN** `openspec/` 或 `Plan/` 下的 `.md`/`.yaml` 等文件含中文
- **THEN** `pnpm check:meta` 不报错——中文区沿用既有豁免目录机制
