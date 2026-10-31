# Tasks

顺序即依赖：路由文件先落地，门禁才会上红；门禁绿了才动账本。

## 1. 路由单入口

- [ ] 1.1 新建 `openspec/specs/README.md`：宪法分段路由（铁律段/元规则段，
  标题跳转链接）、账本路由（先扫 INDEX）、13 个能力 spec 各一行
  `spec 名 | 何时读`、维护规则（增删 spec 同 change 更新本表）。
  验证：`pnpm check:md` 绿（链接与锚点可解析）；`ls openspec/specs` 的
  每个含 `spec.md` 的子目录在 README 有对应行
- [ ] 1.2 `scripts/check_md.py` 加 SPECS ROUTER 规则：枚举
  `openspec/specs/*/spec.md` 所在能力目录，与 README 内链接行双向核对，
  目录缺行或行指空目录即红（能力目录 = 含 `spec.md` 的子目录，
  `README.md` 自身不算）。验证：先临时删 README 一行跑出
  `SPECS ROUTER` 红、临时加一行指向不存在目录跑出红，还原后
  `pnpm check:md` 绿（先红后绿，门禁自证）

## 2. 必读区与钩子

- [ ] 2.1 改 `AGENTS.md`：「文档阅读入口」与「文档地图（内容分配清单）」
  两节收敛为硬护栏指针（动手前先读 `openspec/specs/README.md`；宪法与
  账本指针保留在既有段落），删除逐 spec/逐目录路由正文。
  验证：AGENTS.md 无能力 spec 清单正文；`pnpm check:md` 绿
- [ ] 2.2 改 `openspec/config.yaml` `operations`：apply 与 archive 各加一条
  "扫 `openspec/specs/` 全目录，产出更新/新增/退役三态结论并留痕"。
  验证：YAML 可解析（`openspec status --change <name> --json` 正常返回）

## 3. 契约落地（sync delta 进主 spec）

- [ ] 3.1 按 `specs/project-governance/spec.md` delta 改
  `openspec/specs/project-governance/spec.md`：元规则段末尾（不占铁律编号）
  加「规则生命周期」与「spec 路由单入口」，改写「文档受众分层」
  （必读区两文件、清单落点改 README、新增必读区 scenario）。
  验证：三处 Requirement 标题存在；`pnpm check:md` 绿
- [ ] 3.2 按 `specs/lessons-learned/spec.md` delta 改
  `openspec/specs/lessons-learned/spec.md`：加 Requirement「账本条目退役」
  及五个 scenario。验证：`pnpm check:md` 绿

## 4. 账本首批退役（31 条，映射表见 design.md）

- [ ] 4.1 门禁两步走补证（B 组）：LL-037 临时注释 ci.yml 一处 `test:`
  调用跑 `check_ci.py` 出红并还原；LL-043 临时去 `--dts` 跑 typecheck
  出 unused-directive 红并还原；LL-012/022/063 以现存脚本/配置行作证据。
  验证：两次红样例输出留档于本 change 目录，还原后 `pnpm check:md` 绿
- [ ] 4.2 终检 spec 钦定引用：`grep -rn "LL-[0-9]\+" openspec/specs/*/spec.md`，
  确认命中编号（020/029/042/057/072）均不在退役清单。验证：输出与
  design.md 禁删清单一致，零交集
- [ ] 4.3 删除 A 组 16 条正文（LL-001/002/007/027/030/031/035/039/049/053/
  055/056/060/067/068/071）及对应 INDEX 行。验证：INDEX 行数 73→57，
  分片内无残留标题
- [ ] 4.4 删除 B 组 5 条（LL-012/022/037/043/063）、C 组 6 条
  （LL-008/009/038/058/059/070）、D 组 4 条（LL-028/032/033/045）正文及
  INDEX 行。验证：INDEX 行数 57→42，与 design.md 保留清单逐号相符
- [ ] 4.5 全仓扫悬空引用：`grep -rn "LL-0\(01\|02\|07\|08\|09\|12\|22\|27\|28\|30\|31\|32\|33\|35\|37\|38\|39\|43\|45\|49\|53\|55\|56\|58\|59\|60\|63\|67\|68\|70\|71\)" --include=*.md openspec/specs AGENTS.md CONTRIBUTING.md`
  确认活文档无指向已删条目的引用（archive 与账本保留项除外）。
  验证：命中仅落在 archive 或保留条目，`pnpm check:md` 绿

## 5. Plan/ 收口与终检

- [ ] 5.1 删除 `Plan/账本退役审计.md`（判据→spec、映射表→design.md、
  暂缓门禁项→design.md 暂缓项节，全文有去向）。
  验证：`ls Plan/` 无该文件，`pnpm check:md` 绿（无断链）
- [ ] 5.2 跑全量闸门：`pnpm check:md`、`pnpm check:meta`、
  `openspec validate --change add-spec-routing-and-rule-lifecycle`。
  验证：三者退出码 0
- [ ] 5.3 三轴 review（Standards：新元规则与既有真相源不重复；Spec：
  delta 逐条落地；Lessons：对照 INDEX 现存 42 条无命中）。
  验证：结论表呈人，人点名后方可归档
