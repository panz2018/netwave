# Tasks

本 change 纯文档，无 core 数值实现（铁律二 red/green 循环不适用）；验收以
"同一事实全仓只存一份正文"对账为准，闸门为 `pnpm check:md` 与
`openspec validate --strict`。顺序固定：先接住落点，再删宪法。

## 1. 落点补全（先接住）

- [ ] 1.1 改主 spec `openspec/specs/api-contract/spec.md`：新增「跨端显示串与
      协议保留名」Requirement、改写「显式数据入口与显式内存回收」补 fromX
      工厂名单。验证：主 spec 含两节，且
      `openspec validate api-contract --type spec --strict --no-interactive`
      通过。
- [ ] 1.2 改主 spec `openspec/specs/oracle-harness/spec.md`：新增「精度分层」
      Requirement。验证：同上 validate 通过。
- [ ] 1.3 账本收留：`lessons-learned/core.md` 新增铁律一布局 rationale 条目
      （钉死顺序三理由+代价，登记下一空号并同步 INDEX.md）；核对许可表已含
      SignalIntegrity（缺则补）。验证：INDEX 与分片编号一致。

## 2. 宪法瘦身（后删）

- [ ] 2.1 改主 spec `openspec/specs/project-governance/spec.md`：按 delta 改写
      11 条 Requirement（铁律一/三/四/六/七/八/九/十/十二/十五 +
      元规则·引用自解释/知产合规），新增 2 条 Requirement（编号退役不复用、
      语言约定唯一正文）。验证：`openspec validate project-governance` 以
      `--type spec --strict --no-interactive` 通过（既有超长 requirement 警告
      不算新增失败）。
- [ ] 2.2 全仓对账：grep 被删短语（"钉死此顺序的理由"、精度分层三级口径、
      pragma 语法清单、劣化阈值百分比、SignalIntegrity、机械映射逐字清单、
      协议保留名清单、fromX 名单），确认每条在被删处之外恰存一份正文
      （archive 除外）。
      验证：对账表逐条打钩，无蒸发。

## 3. 指针路由

- [ ] 3.1 `AGENTS.md`：项目铁律节改两行路由指针（元规则段/铁律段）；语言
      bullet 文档语言部分改指针（保留对话行为准则）；书写规范例外去编号范围，
      改"铁律编号是名字，不是位置"。验证：AGENTS.md 无文档语言正文重述、
      无编号范围字面。
- [ ] 3.2 `openspec/config.yaml`：context 改路由指针。验证：context 只含
      指针与工件规则。

## 4. Plan 收尾与闸门

- [ ] 4.1 删除 `Plan/规范精简.md`，`Plan/README.md` 移除该条目。验证：
      `grep -r 规范精简 Plan/` 无残留。
- [ ] 4.2 `pnpm check:md` 退出码 0。验证：闸门绿。
