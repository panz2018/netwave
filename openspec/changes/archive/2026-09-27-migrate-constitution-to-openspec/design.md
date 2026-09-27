# Design

## Context

见 proposal.md 的 Why。当前状态：宪法 v1.7 位于 `Plan/constitution.md`，
全仓 16 个文件共 46 处引用（`grep constitution` 实测）；`openspec/config.yaml`
的 context 与 rules 已存在并指向旧位置；`openspec/specs/` 已有三个归档能力。

## Goals / Non-Goals

- Goal：铁律正文唯一存放点 = `openspec/specs/project-governance/spec.md`；
  Plan/ 可整体删除；所有引用可解析（`check_md.py` 零断链）。
- Non-Goal：不改铁律语义；不动 `.claude/` 第三方生成文件。

## Decisions

1. **落点选能力 spec `project-governance`，不选 `openspec/project.md`**：
   旧计划（总体计划/Plan README）写的是"迁入 openspec/project.md"，但
   openspec 的 `project.md` 不是 CLI 识别工件（validate/list 均不管辖），
   放那里等于又造一个不受门禁约束的孤儿文档。建成能力 spec 后，铁律本身
   进入 `openspec validate --specs` 的校验范围，"唯一真相源"才有工具背书。
   旧文档中"迁入 project.md"的表述一并改掉。
2. **文体转写而非照搬**：每条铁律 → `### Requirement: 铁律N <短名>` +
   WHEN/THEN Scenario；MUST/SHALL 措辞保留原约束强度。Scenario 写成可验证
   形态（CI 命令 / code-review 轴），与现有三个 spec 风格一致。
3. **修订历史原样迁入 spec 末尾**：历史记录不改写（AGENTS.md 明文），
   作为 spec 的 `## 修订历史` 节保留，标题层级降为 `##`。
4. **代码注释只改指向措辞**：`constitution rule N` →
   `governance spec rule N`；铁律编号（一~七）是名字不是位置，保留。
5. **config.yaml rules 保留**：工件专属规则与 spec 正文分工不变，
   context 指针改指新位置。

## Risks / Trade-offs

- 断链风险：锚点 slug 因文体转写变化 → 迁移后立即跑 `pnpm check:md`
  全仓校验；引用统一改指文件级链接，不依赖节级锚点（除非原引用已是锚点）。
- 编辑器回写幽灵文件（本次归档已遇到）→ 删除 constitution 后确认
  `git status` 干净再提交。

## Migration Plan

顺序：写 spec → 改 config.yaml → 改全部引用 → 删旧文件 → 校验
（check_md + openspec validate --specs）→ 提交。单 PR 完成，符合
"改宪法 = 四端同步"的同步性要求（本变更零代码逻辑，四端无感）。

## Open Questions

（无）
