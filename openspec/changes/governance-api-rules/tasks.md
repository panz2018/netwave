# Tasks: governance-api-rules

## 1. 应用 delta 至主 spec

- [ ] 1.1 `openspec sync`（或 archive 自带 sync）：铁律九/十/十一写入
      `openspec/specs/project-governance/spec.md`；铁律八正文末尾补跨 realm
      生命周期指针句
- [ ] 1.2 `api-contract`：「显式托管入口与显式内存回收」Requirement 正文
      `release()` 改 `drop()` 并补指向 memory-lifecycle 的指针句与
      `drop` 立即回收 Scenario
- [ ] 1.3 验证：sync 后 diff 主 spec 无重复需求块（LL-028）

## 2. 波及面清零（LL-008）

- [ ] 2.1 全仓 grep `release()`，确认无残留旧方法名副本（账本/归档引用
      反例作证据者保留并注明）
- [ ] 2.2 grep `铁律九|铁律十|铁律十一` 确认 AGENTS.md/config.yaml 只有
      指针无正文重述（元规则：铁律正文唯一存放）

## 3. 闸门

- [ ] 3.1 `pnpm check:md` 退出码 0
- [ ] 3.2 `openspec validate` 通过

## 4. Plan/ 瘦身（archive 时）

- [ ] 4.1 删除 `Plan/频率类设计.md` 中「三条新铁律」全节与「实现清单」
      中 `governance-api-rules` 小节（结论已入主 spec）
- [ ] 4.2 状态头改写：治理拆为 `governance-api-rules` +
      `governance-doc-rules` 两 change
