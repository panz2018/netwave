# Design

## Context

宪法与兄弟 spec 的重复正文经逐条核对（293 处铁律引用中活文档约 50 处，
archive 冻结不改）。本 change 只去重与指针化：规则本体、编号、Scenario 判定
标准全部不变，因此无代码/CI 改动，纯文档变更走 openspec 通道留痕。

## Decisions

- **指针格式 = 行内代码点名，不用 Markdown 链接**：宪法指向落点时写
  `` `oracle-harness` spec「精度分层」`` 而非 `[精度分层](../oracle-harness/spec.md#...)`。
  理由：spec 间相对路径链接在 check_md.py 中曾因层级写错断链（LL 有先例），
  且 requirement 锚点带 `requirement-` 前缀易写错；点名格式自解释、免维护。
  带锚点链接仅保留在既有正确链接处，不新增。
- **落点先接住再删**：实施顺序固定为"先补落点正文（api-contract、
  oracle-harness、账本），后删宪法侧正文"，同 change 内完成，任何时刻全仓
  不存在"宪法已删、落点未写"的蒸发窗口。
- **LL-072 预留**：铁律一 rationale（钉死布局的三条理由+代价）迁账本
  `core.md`，登记为新 LL（下一空号 072，实施时以 INDEX 实际下一号为准）；
  宪法侧写 `LL-072` 指针在登记号确认后校准。
- **GPL 名单去向**：账本许可表（lessons-learned docs 分片）已有 SignalIntegrity
  登记则不重复写，只删宪法侧括号内点名；实施时核对，缺则补。
- **机械映射豁免单源在铁律十**：铁律九/十二/十五删除逐字豁免清单，改
  "沿用铁律十机械映射豁免"。选铁律十而非铁律九作定义处：skrf 兼容是豁免
  语义的最大伞，且铁律九本身也引用它。
- **路由指针措辞**：`AGENTS.md` 项目铁律节拆两行——"改文档/流程/法务 →
  元规则段；改产品代码/API/CI → 铁律段"；`config.yaml` context 同步。
  漏读风险由 review Standards 轴兜底（拍板记录于本 change，不入宪法——
  路由是读取优化，非新契约）。
- **AGENTS.md 语言 bullet 收缩**：保留对话行为（镜像用户语言、先大白话），
  文档语言规则改指针（正文归宪法元规则，新增 Scenario
  「行为准则不重述语言约定」钉住）。
- **编号范围去字面化**：`AGENTS.md` 书写规范例外改为"铁律编号是名字，
  不是位置"，不写"一~七/一~十五"；宪法新增 Requirement
  「铁律编号是名字，编号退役不复用」把政策本身入宪。

## Risks / Trade-offs

- **读者跳文件成本**：细节移出宪法后，执行者需按指针去落点读。缓解：契约句
  保留在宪法，"不许干什么"不跳可读；只有"怎么干"才跳。
- **指针失效**：落点 Requirement 改名会使点名失效。缓解：check_md.py 已钉
  归档路径与断链；spec 间点名属散文，改名时按"改动波及面改全"纪律 grep 校准。
- **行数预期**：预计 559 → 约 470。行数只作观察，验收以逐条对账表为准
  （LL-071：内容不得蒸发）。

## Migration plan

纯文档，无部署。实施顺序：落点补全 → 宪法瘦身 → AGENTS.md/config.yaml
路由 → Plan 收尾 → 全仓对账（grep 被删短语，确认唯一正文存在）→
`pnpm check:md` + `openspec validate --strict`。回滚 = revert 提交。

## Open questions

（无——Q1-Q7 裁决见 grilling 会话与 proposal）
