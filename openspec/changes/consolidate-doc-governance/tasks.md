# Tasks

## 1. governance spec 落地（delta 同步）

- [ ] 1.1 把 delta 的「元规则 最小规则原则」「元规则 review 三轴」写入
      `openspec/specs/project-governance/spec.md`（元规则段末尾，不占铁律编号）
- [ ] 1.2 用 delta 的两区受众 + Plan/ 正文归属版本替换原
      「元规则 文档受众分层」全文

## 2. AGENTS.md 重写

- [ ] 2.1 新增「硬护栏」节（七条，内容见 design.md「Decisions」），
      删除原「对话效率」中的「指令动作穷尽」条目
- [ ] 2.2 新增「最小规则原则」节（四条要点 + 三条 Anthropic 链接，
      不重述 governance 正文细节，只留准则与指针）
- [ ] 2.3 新增受众声明（受众=AI；人=决策+点名）
- [ ] 2.4 「文档阅读入口」的受众分层改为两区清单（AI 必读区 / 人只看区）
- [ ] 2.5 「Plan/ 生命周期」整节压成一行指针 → `openspec/config.yaml`
      （去向：config.yaml 已有正文）
- [ ] 2.6 「文档书写规范」整节退役为一句"改任何 `.md` 后 `pnpm check:md`
      过闸才算完成"（去向：`scripts/check_md.py` 门禁 + 账本 LL-032/033/045）
- [ ] 2.7 「反思铁律」压成两句 AI 行为 + 指针（review 三轴去向：
      governance 元规则；六步循环去向：CONTRIBUTING 门面）
- [ ] 2.8 「对话效率」压缩：三次即搜/全景表/查现成各留一句 + LL 指针，
      删除程序性细节段落

## 3. CONTRIBUTING.md 变薄门面

- [ ] 3.1 删除「Development workflow」六步循环正文与 review 三轴正文
      （去向：governance 元规则 review 三轴 + 本节留指针）
- [ ] 3.2 「Toolchain (task → tool)」表压成指针：版本以 lockfile /
      `rust-toolchain.toml` / `scripts/versions/lib/registry.json` 现查为准
      （去向：dependency-upgrade spec 已是唯一真相源）
- [ ] 3.3 保留：Repository layout、Quick start 命令、Quality gates 命令名速查、
      When to simplify 表、Local reference mirrors 表（位置不动）、
      Predecessor 段
- [ ] 3.4 文首受众说明改为"AI 必读区薄门面 + 人可亲手敲的命令速查"

## 4. config.yaml 与 Plan/、账本

- [ ] 4.1 `openspec/config.yaml`：确认 `operations` 段为 Plan/ 生命周期唯一
      正文，措辞补齐 AGENTS.md 被删的两条（完成子任务即时删除、终态整目录清空）
- [ ] 4.2 `Plan/方案讨论纪律.md`：删「硬护栏」「最小规则原则」两节正文，
      改为指向 `AGENTS.md` 的指针；保留 8 项待讨论表
- [ ] 4.3 新建 `Plan/账本退役审计.md`：INDEX 72 条逐条标去向的待办 +
      三类退出判据（已铁律化 / 已门禁化 / 一次性环境事实）
- [ ] 4.4 账本 LL-070：规则正文改为指针（正文归 AGENTS.md 硬护栏），
      保留事故证据；INDEX 该行措辞同步

## 5. 波及面与闸门

- [ ] 5.1 grep 全仓核对被迁/被删条目的旧引用（六步循环、review 三轴、
      文档书写规范、Plan/ 生命周期、指令动作穷尽），改到或改指新落点
- [ ] 5.2 `pnpm check:md` 通过（0 issues、Prettier、链接锚点）
- [ ] 5.3 `pnpm check:meta` 通过（`check_comments.py`、`check_proposal.py`、
      版本对账不受影响）
- [ ] 5.4 `openspec validate` 通过本 change
- [ ] 5.5 提交（用户已授权免过目）：按 governance+config /
      AGENTS+CONTRIBUTING / Plan+账本 分三笔
