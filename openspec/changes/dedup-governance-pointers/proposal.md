# Proposal

## Why

宪法（`openspec/specs/project-governance/spec.md`，559 行）与兄弟 spec、
账本存在大量同一事实两处正文：铁律三/四/六/七/八/九/十五的细节在
`oracle-harness`/`ci-matrix`/`zero-copy-roundtrip`/`api-contract` 已有近乎
逐字的第二份；机械映射豁免在铁律九/十/十二/十五逐字重复四遍；实现 rationale
与 GPL 名单属事件级事实却住在宪法里，违反宪法自身的"文档受众分层"元规则。
每次动手前通读宪法约 12-17K token，其中约 86 行是重复或错位内容。

## What Changes

- **宪法指针化（MODIFIED，11 处）**：铁律一/三/四/六/七/八/九/十二/十五 +
  元规则（优先级、引用自解释、知产合规）删除与别处重复的机制细节正文，
  每条保留契约句（规则在宪法仍完整可读"不许干什么"）+ 指向唯一落点的指针。
- **机械映射豁免单源化**：豁免定义收敛到铁律十一处，铁律九/十二/十五改为
  引用"铁律十机械映射豁免"，不再逐字重述。
- **落点补全（先接住再删）**：`api-contract` 新增"跨端显示串与协议保留名"
  Requirement、扩充"显式数据入口"的 fromX 工厂名单；`oracle-harness` 新增
  "精度分层"Requirement；`ci-matrix` 的 criterion Requirement 并入铁律六
  阈值；`zero-copy-roundtrip` 补 worker 常驻/单例措辞；账本 `core.md` 新增
  铁律一布局 rationale 条目；账本许可表确认收留 GPL 名单。
- **指针路由（AGENTS.md + config.yaml）**：宪法必读指针改为路由式——文档/
  流程/法务任务读元规则段，产品代码/API/CI 任务读铁律段；AGENTS.md 语言
  bullet 的文档语言部分改指针（归宪法元规则）；"标题不带章节序号"例外去掉
  编号范围写法，改为"铁律编号是名字，不是位置"（新增/退役编号不波及）。
- **编号政策**：铁律编号退役不复用、不重排（同 LL 编号惯例）。
- **Plan 收尾**：删除 `Plan/规范精简.md`（Q1-Q7 全部关闭），同步
  `Plan/README.md` 条目。

## Capabilities

### New Capabilities

（无——不新建 capability）

### Modified Capabilities

- `project-governance`：11 条 Requirement 瘦身（删重复正文留契约句+指针）；
  机械映射豁免收敛为铁律十单源；语言约定确认归本 spec（AGENTS.md 改指针）
- `api-contract`：新增"跨端显示串与协议保留名"Requirement（承接铁律九细节）；
  修改"显式数据入口与显式内存回收"补 fromX 工厂名单（承接铁律十五细节）
- `oracle-harness`：新增"精度分层"Requirement（承接铁律三细节）

落点核对：`ci-matrix`、`zero-copy-roundtrip`、`memory-lifecycle` 经逐条核对
**已含**铁律四/六/七/八的机制细节正文，本 change 不修改它们，只在宪法侧
加指针；若实施时发现某处正文缺口，当场补 delta。

## Impact

- `openspec/specs/project-governance/spec.md`：559 → 约 470 行（行数系观察值
  非验收指标，验收以"同一事实全仓只存一份正文"对账为准）
- `openspec/specs/{api-contract,oracle-harness}/spec.md`：落点补全
- `openspec/specs/lessons-learned/core.md` + `INDEX.md`：新增布局 rationale LL；
  许可表确认收留 GPL 名单
- `AGENTS.md`：项目铁律节改路由指针；语言 bullet 改指针；书写规范例外去范围
- `openspec/config.yaml`：context 改路由指针
- `Plan/规范精简.md` 删除、`Plan/README.md` 同步
- 不改动：任何代码、CI 步骤、闸门脚本、已归档 change（历史不改写）

## Non-goals

- 不拆宪法为"治理 + 工程契约"两本文件（编号迁移成本大于收益，已拍板）
- 不整条迁出铁律九/十二/十五（规则本体留宪法保身份与 review 权重，只迁细节）
- 不重排/复用铁律编号
- 不改任何铁律的契约语义（本 change 只去重与指针化，逐条 Scenario 判定标准不变）
- 不动 archive 历史文档中的旧引用
