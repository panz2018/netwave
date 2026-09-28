# Spec Delta

## ADDED Requirements

### Requirement: 文档受众分层

文档按变更级别分三层，内容 MUST 落入对应层：① 契约级决定（改动会波及已发布
代码/跨端契约者）MUST 入 governance spec，走最高级变更；② agent 行为准则
（约束执行动作而非系统状态者）MUST 入 AGENTS.md，保持精简（准则+指针，
MUST NOT 重述 spec 正文与内容清单细节）；③ 事件级事实（踩坑、实现决策、
人工纠正）MUST 只入 lessons-learned 账本。同一事实 MUST NOT 跨层重复。各
文档的内容分配清单属第②层执行细节，只列于 AGENTS.md 文档地图，清单增删
不触发本 spec 变更。

#### Scenario: 新事实正确归层

- **WHEN** 产生一条新信息（坑/决定/准则/契约）
- **THEN** 按判据归入唯一层，其余层不出现其正文

#### Scenario: 坑只进账本

- **WHEN** 新增环境坑或实现决策记录
- **THEN** 仅出现在 lessons-learned 账本，README/CONTRIBUTING 无新增坑节

#### Scenario: 清单调整不动宪法

- **WHEN** 内容分配清单需要调整（新增目录/章节改归属）
- **THEN** 只改 AGENTS.md 文档地图，本 spec 不动
