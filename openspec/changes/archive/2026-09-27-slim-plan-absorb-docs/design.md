# Design

## Context

见 proposal.md——Why。现状：`Plan/` 五份文档与 `openspec/specs/` 四个已归档能力
spec（project-governance / workspace-layout / ci-matrix / zero-copy-roundtrip）
存在大量正文重复；AGENTS.md 规定 Plan/ 只放未执行任务、吸收完即删。

## Goals / Non-Goals

**Goals:**

- 每块定案内容只有一个存放处：spec（受 `openspec validate` 管辖）> README /
  CONTRIBUTING（操作与命令）> Plan/（未执行任务）。
- 瘦身后 Plan/ 各文件可直接逐段对照"还剩什么没干"。

**Non-Goals:**

- 不改写历史文档中的旧式引用（governance spec 修订历史保持原样，AGENTS.md 已有
  此豁免）。
- 不重组 openspec 目录结构。

## Decisions

1. **API 面契约升格为新能力 `api-contract` 而非并入 project-governance**：
   铁律是不可协商约束，API 契约是结构定案，二者演进节奏不同；独立能力可被
   `openspec validate` 单测且未来 Network / 绑定高级能力可单独 MODIFIED。备选（并入 governance）
   被否：会让最高级 spec 频繁因细节修订而改动。
2. **开发流程.md 迁入 CONTRIBUTING.md 而非新建 spec**：开发流程是"人怎么干活"
   的操作文档，不是系统行为契约；CONTRIBUTING.md 已是开发者入口，语言用英文
   （AGENTS.md 语言约定：仅 openspec/ 与 Plan/ 用中文）。备选（新建
   `openspec/specs/dev-workflow`）被否：流程无法写成 WHEN/THEN 行为需求。
3. **总体计划.md 保留骨架而非整体删除**：分阶段路线图（测试基础设施至光学适配验证）与待决清单是
   尚未吸收进任何 spec 的未执行计划，删除即丢失规划；被吸收的选型论证
   （GPU 否决、布局理由、绑定方案对比表）逐段替换为一行 + spec 链接。
4. **测试规划删"已定案"留"未执行"**：精度标准表与 CI 集成表已由铁律三/铁律七 +
   ci-matrix spec + manifest 承载，删除；unit/property 用例清单、criterion 基线
   持久化方案（Touchstone 核心任务）、阶段映射保留——它们是测试基础设施至绑定高级能力的实施输入。
5. **testdata/README.md 的 `Plan/测试规划.md` 引用改指 governance spec 铁律三**：
   比对规则（原生 bit 级 / wasm 相对容差）在铁律三已有规范表述，避免指向即将
   删表的文档。

## Risks / Trade-offs

- [瘦身后丢失"为什么这样定"的论证上下文] → 每处删除保留一行结论 + 指向承载
  spec/归档 change 的链接；论证全文可在 git 历史与 `openspec/changes/archive/` 找回。
- [CONTRIBUTING.md 变长后与子 README 边界模糊] → 只收流程循环与技能地图，
  命令细节仍归子 README（AGENTS.md 作用域纪律不变）。
- [Plan/README 状态表与实际文件漂移] → 本次一并重写状态表，且 `pnpm check:md`
  校验链接存在性。
