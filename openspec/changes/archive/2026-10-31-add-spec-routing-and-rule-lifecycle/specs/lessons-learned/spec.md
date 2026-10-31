# lessons-learned Specification Delta

## ADDED Requirements

### Requirement: 账本条目退役

账本 MUST 可退出，防"只增不减"膨胀成第二套规则堆。一条 LL 满足以下
任一判据方可退役（正文删除或迁出，事故证据靠 git log 追溯）：

1. **已铁律化/契约化**：规则结论已被 governance spec 或某能力 spec 完整
   覆盖。退役前 MUST 做覆盖度核对——spec 缺的细节（理由、代价、边界）
   MUST 先并入该 spec 对应 Requirement 的正文或 rationale，再删账本正文；
   被 spec 正文指名"唯一正文见账本"的条目 MUST NOT 退役（否则 spec 断链）。
2. **已门禁化**：规则已被某脚本/CI 闸门/编译器强制。退役前 MUST 两步走
   证明——先构造一条违规样例、跑出该闸门红，再删账本正文；证明不了的
   降级为"待落门禁"，门禁落地前不退役。
3. **一次性事实失效**：仅对某次迁移或已淘汰工具版本有效。容器/CI 平台类
   坑属环境类条件、任何等价环境都会复发，MUST NOT 判为一次性。

退役执行纪律：去向标签是初判不是结论，每条退役 MUST 经人逐条确认；
确认记录与"LL→去向"映射表 MUST 留痕于当次 change 的 design.md（不留
常驻副本）；删除正文的同一 change MUST 同步删除 `INDEX.md` 对应行，
INDEX MUST NOT 留墓碑行（编号只增不复用，历史引用靠 git log 与
design.md 映射）。每轮退役后 MUST 跑 `pnpm check:md`。

本条为治理机制约束，无数值容差；可测性由 review Standards 轴与
`scripts/check_md.py` 承担。

#### Scenario: 铁律化退役先并细节

- **WHEN** 某条 LL 申请以判据 1 退役
- **THEN** 附覆盖对照（目标 spec 节锚点 + 逐点比对），spec 缺的细节
  已在同一 change 并入该 spec；账本正文指名被 spec 引为唯一正文者打回

#### Scenario: 门禁化退役先跑红

- **WHEN** 某条 LL 申请以判据 2 退役
- **THEN** 附违规样例在该门禁下变红的证据；无证据即降级"待落门禁"，
  正文保留

#### Scenario: 容器类坑不算一次性

- **WHEN** 某条 LL 被标"一次性"而其条件是容器/CI 平台/通用工具行为
- **THEN** 打回：等价环境必复发，判据 3 不成立，保留账本

#### Scenario: 退役同步 INDEX 不留墓碑

- **WHEN** 某条 LL 正文被删除
- **THEN** `INDEX.md` 对应行同轮删除，无"已退役"占位行；去向只记于
  当次 change 的 design.md

#### Scenario: 未经确认不得退役

- **WHEN** 退役清单中某条无逐条确认记录
- **THEN** 该条不执行删除；批量标签（"约 N 条"）不构成确认
