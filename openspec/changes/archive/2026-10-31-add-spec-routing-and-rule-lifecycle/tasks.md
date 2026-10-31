# Tasks

顺序即依赖：路由文件先落地，门禁才会上红；门禁绿了才动账本。

## 1. 路由单入口

- [x] 1.1 新建 `openspec/specs/README.md`：宪法分段路由（铁律段/元规则段，
      标题跳转链接）、账本路由（先扫 INDEX）、13 个能力 spec 各一行
      `spec 名 | 何时读`、文档地图两区清单（自 AGENTS.md 迁入）、维护规则。
      验证：`pnpm check:md` 绿；每个含 `spec.md` 的子目录在 README 有对应行 ✓
- [x] 1.2 `scripts/check_md.py` 加 SPECS ROUTER 规则：枚举
      `openspec/specs/*/spec.md` 能力目录，与 README 链接行双向核对。
      验证：删 README 一行跑出 `SPECS ROUTER touchstone-core` 红、加幽灵目录行
      跑出 `missing capability` 红，还原后绿 ✓（先红后绿自证通过）

## 2. 必读区与钩子

- [x] 2.1 改 `AGENTS.md`：「文档阅读入口」与「文档地图」两节收敛为硬护栏
      指针（动手前先读 `openspec/specs/README.md`），逐 spec/逐目录清单正文
      迁入 README；清理指向已退役条目的悬空编号（LL-008/035/058/071）。
      验证：AGENTS.md 无能力 spec 清单正文；`pnpm check:md` 绿 ✓
- [x] 2.2 改 `openspec/config.yaml` `operations`：apply 与 archive 各加
      "扫 `openspec/specs/` 全目录，产出更新/新增/退役三态结论并留痕"。
      验证：`openspec status --change <name> --json` 正常返回 ✓

## 3. 契约落地（sync delta 进主 spec）

- [x] 3.1 按 governance delta 改主 spec：元规则段末尾加「规则生命周期」
      与「spec 路由单入口」，改写「文档受众分层」（必读区两文件、清单落点
      改 README、新增必读区 scenario）。验证：三处 Requirement 标题存在 ✓
- [x] 3.2 按 lessons-learned delta 改主 spec：加 Requirement「账本条目退役」
      及五个 scenario。验证：`pnpm check:md` 绿 ✓

## 4. 账本首批退役（29 条，映射表见 design.md）

- [x] 4.1 门禁两步走补证：LL-037 删 ci.yml `test:native` 调用行跑
      `check_ci.py` 出 `::error::` 红并还原绿；LL-043 移走
      `index.node.generated.d.mts` 跑 typecheck 出 TS2578 unused-directive 红
      并还原绿；LL-012/022/063 以现存脚本/配置行作证据 ✓
- [x] 4.2 终检 spec 钦定引用：`grep "LL-[0-9]\+" openspec/specs/*/spec.md`
      命中 020/029/042/057/072，均不在退役清单，零交集 ✓
- [x] 4.3 删除 A 组 16 条正文（LL-001/002/007/027/030/031/035/039/049/053/
      055/056/060/067/068/071）及对应 INDEX 行 ✓
- [x] 4.4 删除 B 组 5 条（LL-012/022/037/043/063）、C 组 6 条
      （LL-008/009/038/058/059/070）、D 组 2 条（LL-033/045）正文及 INDEX 行。
      补证发现 LL-028（MD024 未启用）/LL-032（方案代号/日期戳未 grep）为
      假门禁，降级保留并入待落门禁。验证：INDEX 行数 73→44，与 design.md
      保留清单逐号相符 ✓
- [x] 4.5 全仓扫悬空引用：活文档（AGENTS.md/specs/README）对已删 29 编号
      零残留（AGENTS.md 4 处、ci.md 1 处已改写为不依赖编号的表述）✓

## 5. Plan/ 收口与终检

- [x] 5.1 删除 `Plan/账本退役审计.md`（判据→spec、映射表→design.md、
      暂缓门禁项→design.md 暂缓项节，全文有去向）。验证：`ls Plan/` 无该文件 ✓
- [x] 5.2 跑全量闸门：`pnpm check:md`（332 files OK）、`pnpm check:meta`
      （全 OK）、`openspec validate add-spec-routing-and-rule-lifecycle`
      （exit 0；strict 仅 2 条正文偏长警告，与本仓既有 spec 常态一致，非闸门）✓
- [x] 5.3 三轴 review（Standards：新元规则与既有真相源不重复；Spec：
      delta 逐条落地；Lessons：对照 INDEX 现存 44 条无命中）。
      验证：结论表已呈人，人以 `/opsx:archive` 点名归档 ✓
