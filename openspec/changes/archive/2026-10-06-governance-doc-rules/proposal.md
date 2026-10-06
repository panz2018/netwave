# Proposal: governance-doc-rules

## Why

治理文档存在三类无约束漂移：代码内文档引用权威书目无格式规范（曾内嵌本机
绝对路径，外部读者不可访问）；注释里反复长出改动名/阶段词/考古叙述（LL-039
已登记但未门禁化，存量已命中）；agent 交流话术与对话效率无成文准则（多次因
堆术语、挤牙膏式推进受阻）。

## What Changes

- 修订宪法元规则「教学式文档与类型标注」：代码内文档引用权威书目 MUST 用
  「书名 + 可访问链接」，格式唯一真相源为根 README References 节；MUST NOT
  写本地绝对路径；**去掉该元规则内嵌的绝对路径**，改为指针（本机镜像见
  CONTRIBUTING「Local reference mirrors」表）。
- 宪法新增元规则**「注释只写当前事实」**：代码注释与文档只描述当前契约，
  MUST NOT 写改动名/路线图阶段词/讨论代号/考古叙述；稳定契约指针（铁律编号、
  LL 编号、spec 名）允许保留。随 change 落门禁脚本
  `scripts/check_comments.py`（挂 `pnpm check:meta`）：改动名由
  `openspec/changes/` 目录名动态生成 + 硬编码阶段词，扫 `.rs`/`.py`/`.ts`
  注释与 `openspec/specs/**/*.md`；治理 spec、账本、archive 豁免。
- `CONTRIBUTING.md` 新增「Local reference mirrors (this machine only)」小节
  （英文）：4 真参考表（两书 + scikit-rf + SignalIntegrity，含许可红线）+
  换机 `ls` 自检指引；单列「Predecessor project (not a reference)」段标注
  RF-Touchstone lineage。
- `AGENTS.md`「语言」节补大白话强化；「通用原则」节末新增「对话效率」小节
  （机制断言先实证 / 多步操作先给全景表 / 方案先查现成做法 / 会话卫生，
  单行要点形态）。
- 存量清理：门禁首跑命中的现存注释（已知 `core/tests/frequency_memory.rs`
  首行 `skeleton`）当轮改写为当前事实描述。
- 根 README References **不动**。

## Capabilities

### New Capabilities

（无。）

### Modified Capabilities

- `project-governance`: 修订「教学式文档与类型标注」元规则（引用格式 +
  去绝对路径改指针）；新增元规则「注释只写当前事实」。

## Impact

- `openspec/specs/project-governance/spec.md`（sync 应用 delta）
- `scripts/check_comments.py`（新建）+ 根 `package.json` `check:meta` 挂入
- `CONTRIBUTING.md`、`AGENTS.md`
- 存量注释/spec 措辞清理（门禁命中即改）
- CI：`pnpm check` 经 `check:meta` 自动覆盖新门禁，无新 job

## Non-goals

- API 铁律九/十/十一与 `release()`→`drop()` 对齐——归姊妹 change
  `governance-api-rules`。
- `frequency-class` 功能实现——独立实现 change。
- 主 spec 正文「阶段 N」旧措辞清理（现存 15 处，涉 5 份 spec）——门禁首版
  不含中文阶段词，存量另落 `Plan/` 后续任务，避免本 change 重写五份主 spec。
- GPL 代码混入自动检测——LL-029 复发检测仍靠 review Lessons 轴。
