# Design

## Context

见 proposal.md - Why。当前 `scripts/check_proposal.py` 已解析在途 change 的
`proposal.md` 做三节存在性校验，已在 `pnpm check:meta` 内、CI 必跑；本 change
在同一脚本内新增对 `tasks.md` 的 guidance 锚点覆盖校验。`openspec/config.yaml`
的 `operations.apply.guidance` 现有五条，散文无标识。

## Goals / Non-Goals

**Goals:**

- 把 LL-104 的"收尾漏抄"从 review 自觉变为 CI 机器拦截。
- 锚点与 guidance 同文件同条目存放，guidance 增删改时闸门自动跟上，不建第二处清单。
- 人工裁决跳过留痕即放行，闸门只拦静默漏抄。

**Non-Goals:**

- 不改 guidance 五步语义与顺序（见 proposal Non-goals）。
- 不做任务正文语义质量判定（归 review）。
- 不引入新依赖、不改 CI 步骤顺序（`check:meta` 已在链内）。

## Decisions

### 锚点词选定（guidance 五条各一个）

| guidance 条             | 锚点词           | 理由                            |
| ----------------------- | ---------------- | ------------------------------- |
| ① Plan/ 瘦身 + check:md | `Plan/`          | 该条唯一对象即 Plan/ 目录       |
| ② specs 三态时效        | `三态时效`       | 该条特征词，其他条无此词        |
| ③ 三轴 review           | `三轴`           | 特征词                          |
| ④ apply 态体检          | `体检`           | 特征词（health-check 中文惯用） |
| ⑤ check:outdated 消化   | `check:outdated` | 命令名即特征词                  |

备选：给每条加显式 `[anchor: xxx]` 标记——否决，污染 guidance 散文且与
"最小规则原则"冲突；自然特征词零侵入且唯一可判。锚点唯一性实测：五条锚点
互不为子串、在 config.yaml guidance 段外极少共现（实现时以真实 tasks.md 验证）。

### 覆盖判定 = 打勾任务行含锚点（存在性）

只扫 `tasks.md` 中以 `- [ ]` 或 `- [x]` 开头的行；某锚点至少命中一行即该条
覆盖。不数次数（见"存在性而非计数相等"）。散文/标题/Workflow
follow-up 圆点行不参与判定。
备选"全文 grep 锚点"——否决：跳过声明、说明散文均含锚点，会假绿。

### 跳过出口 = 打勾行含锚点 + "跳过" + ISO 日期

正则要求同一打勾任务行内同时出现锚点、`跳过`、`\d{4}-\d{2}-\d{2}`。三条件
同行，防"跳过"与日期分处两地拼出假出口。日期格式钉 ISO，与
`Plan/体检-<日期>.md` 命名同族。

### 存在性而非计数相等

LL-104 原句"收尾任务数 = guidance 条数"实测不成立（一条可拆多任务、流程
固定动作另计），废弃；改为逐条存在性。报错信息指名缺失锚点对应 guidance 条
摘要，便于定位。

### 校验范围 = 在途 change，零豁免

与既有三节门禁同口径：扫 `openspec/changes/*/tasks.md`（排除 `archive/`），
无在途 change 即绿。本 change 自身即首个被测样本，落地时自校验。

## Risks / Trade-offs

- **锚点词漂移**：guidance 改写后锚点可能不再唯一 → 锚点与 guidance 同条目
  存放，改 guidance 必看到锚点；单测锁五条锚点常量。
- **误拦合并写法**：把多条 guidance 塞进同一打勾行——只要该行含全部对应锚点
  仍绿；若漏锚点则红，提示补锚点，可接受。
- **新 change 首跑成本**：写 tasks.md 须带锚点，多一步；由 `rules.tasks` 软
  提示 + 闸门硬拦双保险，与三节门禁同体验。
