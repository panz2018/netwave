# Design: governance-doc-rules

## 门禁动态名单：改动名怎么生成不误伤

`check_comments.py` 的改动名模式来自 `openspec/changes/` 与
`openspec/changes/archive/` 目录名（剥 `YYYY-MM-DD-` 日期前缀），**减去
`openspec/specs/` 下活 spec 能力名**——`frequency-unit`、`license-compliance`
等既是历史改动名又是活 spec 名，正文引用它们是合法契约指针（元规则明文允许
`spec: <capability>`），不得误杀。仅归档且无同名 spec 的名字
（如 `frequency-memory-lifecycle`、`ts-source-rewrite`）才是考古残留。

已实测：主 spec 正文对纯归档名零命中，门禁首跑即绿；代码注释已知一处命中
（`core/tests/frequency_memory.rs` 首行 `skeleton`），当轮改写。

## 阶段词硬编码名单为何不动态

`stage N` / `phase-N` / `skeleton` / `arrives with` 是稳定词汇，不随 change
增减；中文「阶段 N」存量散布 5 份主 spec（15 处），首版不收以免本 change
重写五份主 spec——存量清理单独立项（见 proposal Non-goals）。

## 扫描范围与豁免

- 扫：`.rs`/`.py`/`.ts` 的注释行（`//`、`///`、`//!`、`#`、`--`、`/* */`
  块内）+ `openspec/specs/**/*.md` 正文。
- 豁免：`openspec/specs/project-governance/spec.md`（定义规则须举反例）、
  `openspec/specs/lessons-learned/`（账本引反例作证据，同 LL-033 豁免先例）、
  `openspec/changes/archive/`（冻结历史）、`node_modules`/`target`/`dist`/
  `.venv`（第三方不进门禁）。
- 挂 `pnpm check:meta`（与 check_license/check_ci/check_vocab 同族元数据
  卫生），CI 经现有 `pnpm check` 自动覆盖，零新 job。

## 三条线分离的落点复核

- README References：可移植引用（书名/仓库 + URL），**不动**。
- CONTRIBUTING「Local reference mirrors」：本机绝对路径 + 许可红线 +
  换机 `ls` 自检；RF-Touchstone 单列「Predecessor project (not a reference)」
  段（MIT，panz2018），不入 4 参考表。
- governance spec：只留指针（「本机镜像见 CONTRIBUTING 该表，可移植引用见
  README References」），删除现存内嵌的 `/config/GitHub/knowledge/RF/` 路径。

## AGENTS.md 增量形态

「语言」节补一行大白话强化；「通用原则」节末加 `### 对话效率` 小节四条
单行要点（与「编码前思考」「简洁优先」平级），不带 Scenario——AGENTS.md
是行为准则层，非 spec。总增量约 8 行，符合精简红线。
