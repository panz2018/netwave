# Design

## Context

见 `proposal.md` - Why。当前状态：`scripts/check_comments.py` 同时扫代码注释与
`openspec/specs/**/*.md` 正文的考古词（改动名动态生成 + `STAGE_WORDS` 英文词表），
豁免 governance/lessons-learned/archive；`scripts/check_md.py` 扫全部 Markdown 的
链接/锚点/结构。存量：活 spec 17 处「阶段 N」、`Plan/` 39 处、archive 60+ 处、
代码注释 9 处开发文档指针（`core/src/frequency.rs`、`typescript/src/`）。归档目录
脚手架归档目录原名带路线图数字代号。

## Goals / Non-Goals

**Goals:**

- 全仓（活文档 + archive + 代码注释）「阶段 N」与开发文档指针清零。
- 门禁按受众两分：代码面 `check_comments.py`、文档面 `check_md.py`，零豁免。
- 归档目录改名后全仓引用一致、无断链。

**Non-Goals:**

- 不改 `package.json` 命令名、CI job 拓扑、任何运行时行为（见 proposal
  Non-goals）。
- 不改 `AGENTS.md`。

## Decisions

### 门禁按受众拆两脚本，而非三脚本或单脚本

`check_comments.py` 收窄为只扫 `.rs`/`.py`/`.ts` 注释（考古词 + 开发文档指针
`spec:`/`LL-\d+`/铁律编号/`openspec/`/`Plan/`）；Markdown 词表检查并入
`check_md.py`（其已有全 md 遍历与链接校验，合一避免双遍历）。否决三脚本：
md 结构与 md 词表同属文档面、同一批文件，拆开只增维护面。否决单脚本：
受众不同、闸门命令不同（`check:meta` vs `check:md`），混在一起豁免逻辑
说不清（本次已实证豁免即漂移源）。

### 词表：`阶段\s*[0-9]` + 英文对等 + 描述性反例

中文 `阶段\s*[0-9]`（兼容无空格）；英文沿用现有 `stage [0-9]|phase-[0-9]` 并
补 `phase [0-9]`。governance 正文反例改描述性表达（"英文阶段词后接数字"），
使零豁免可行。否决"第N阶段"等变体：当前无此写法，YAGNI，出现再扩。

### 归档改名与引用同步

`git mv` 将脚手架归档目录（原名带路线图数字代号）改为
`archive/2026-09-27-monorepo-scaffold`。全仓 grep 旧名逐处更新为散文式
说明（老名字已改名）或新名。
现存规则「不得向 archive 发 markdown 链接」保留不变；活文档中的归档指针均为
行内代码路径，文档面新增校验：行内代码形态的 `openspec/changes/archive/<name>/`
完整路径 MUST 指向现存目录（改名后残留旧路径即红）。`check_comments.py` 的
改动名词表由现存目录名动态生成，改名后旧名自动不再命中、新名自动纳入扫描。

### 账本证据转述而非豁免

`lessons-learned/docs.md` 的 LL-032 证据行原文（列举路线图数字代号处）
转述为「路线图数字代号」，原文证据靠 git log 追溯。否决保留+行内豁免标记：
豁免标记本身成为第二真相源，必漂移。

### 先扩门禁（red），再清存量（green）

任务顺序：扩门禁词表并撤豁免 → 跑门禁，预期大面积红（即门禁生效的 red 证据，
命中清单即完整存量台账）→ 按台账逐面清理（代码注释 → 活 spec/账本 → Plan →
archive + 归档改名）→ 门禁转绿。否决先清后扩：清理过程无机器台账，靠人工
grep 易漏。

## Risks / Trade-offs

- [archive 改写量大（60+ 处）且为冻结历史] → 只替换阶段词为内容命名，不动
  其余叙述；逐文件 diff 人工复核。
- [governance 反例描述化后，未来读者不知道具体触发词] → 门禁脚本源码即完整
  词表，报错信息含命中词，可执行性不依赖 spec 列举。
- [改名后旧归档名在 git log/外部引用中失效] → 可接受：仓库内自洽优先，
  外部无消费者（未发布）。
- [check_md.py 扩扫 archive/Plan 首跑可能抓到未预见存量] → 按报错逐条清理，
  清理即目标本身。

## Migration Plan

纯文档+脚本变更，无部署/回滚复杂度。单 PR：按 Decisions 顺序提交分组，
`pnpm check` 绿后由人工提交。

## Open Questions

（无）
