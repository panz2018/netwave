# Design

## Context

动机见 proposal.md·Why。当前状态：登记表 `scripts/version_pins.json` 有 28 条目、
三种 `pin_location` 形态（文件路径 / `machine:` / `discovered:`）；离线闸门
`check_version_pins.py` 做结构 + 双向对账 + 一致性检查；联网体检
`check_outdated.py` 四段探测但完全不读登记表。两个脚本都是纯标准库 Python。
黑名单设计经 explore + grilling 全部定案，本文记录技术决策及理由。

## Goals / Non-Goals

**Goals:**

- 坏版本知识进入登记表（单一真相源），体检与闸门两层消费。
- 改名 `versions.json` / `check_versions.py`，波及面（文档、接线、活跃 change）改全。
- 两类禁令（自身 bug / 配对不兼容）生命周期明确、可执行。

**Non-Goals:**（design 层补充，范围性 Non-goals 见 proposal）

- 不追求黑名单的机器完备性：`verified` × `blocked` 矛盾、blocked 版本是否真的
  存在等均不校验——登记表是人维护的契约，闸门只查结构与可判定的冲突。
- 体检层不做"blocked 版本已装"之外的推断（如依赖树级联影响）。

## Decisions

### 两类禁令、两种生命周期

`blocked` 项按事实性质分流：**版本自身 bug**（如某 release 带回归）是不可变
发布事实，禁令永久保留——升级到修复版不删条目，因为条目防的是"回踩"，而
升级目标由"最新可用版"计算，条目只挡回退路径，不挡升级路径。**配对不兼容**
（如 wasm-pack X 与 binaryen Y 不配套）是上下文事实，对方变化后禁令失效，
删除时同一笔 commit 把结论挪进配对条目 `verified`（先例：
`typescript-tsdown-pair` 的 `verified` 记法）。
备选"全部永久保留"被否：配对禁令长期挂着会让体检把已兼容组合报成被堵，
噪音淹没真禁令。

### 双层消费：闸门离线、体检联网

闸门层（`check_versions.py`，进 `check:meta`）只读仓库文件，检查**当前钉版值**
是否命中 blocked：`rust-toolchain.toml` channel、`packageManager`、
`.python-version`、workflow 全 pin 的 action tag、`discovered:` 成员值、CI python
矩阵格。`machine:` 条目（已装的全局 CLI / cargo 子命令）闸门跳过——闸门不跑
探测命令，否则 CI 结果随机器状态漂移、不可复现；这类条目的黑名单由体检层
探测已装版本消费。体检层（`check_outdated.py`）对可枚举版本列表的段过滤
blocked、改报 target；lockfile 三段（pnpm/cargo/uv dry-run）原样输出——过滤
lockfile 等于重造 resolver，lockfile 内坏版本走生态机制（pnpm overrides、
cargo `[T-001]` advisory、uv exclusion）。
备选"黑名单只放体检层"被否：体检是人工命令，当前钉版踩坑无人拦；
备选"闸门也探测 machine 版本"被否：破坏 CI 可复现性。

### 探测名↔条目名映射表放 `check_outdated.py` 内

体检探测用的名字与登记表条目名不完全一致（如 `node`→`node-global`、
`uv`→`uv-global`、`markdownlint-cli2`→`markdownlint-cli2-global`，
`rustc` 无条目）。映射表写在脚本内而非 JSON：这是脚本内部实现细节，
进登记表会让"唯一真相源"混入非钉版信息；改名波及面也最小。
决策记录于此文档供实现与 review 对照。

### `version` 精确匹配、拒绝范围写法

结构检查拒绝 `>=`、`*`、`1.x` 等写法。理由：黑名单是"点名"工具，范围语义
（堵到哪个版本为止）引入排序比较与区间合并复杂度，而实际场景都是点名个别
坏版本；上游修复后逐个删即可。

### `ci-actions` 不支持 blocked

该条目一条扛全部 action（`pin_location` 是 workflow 目录级），blocked 挂上去
分不清哪个 action 坏。逐 action 拆条目 = 把刚删掉的 watch 清单请回来，违背
slim 方向。本期明确不支持并在 spec 落为闸门 FAIL（防止误挂静默失效）；
将来若需要，另开 change 设计 action 级条目形态。

### 不做 verified × blocked 矛盾机器检查

`verified` 是自由文本（如 "verified with binaryen 119"），硬抠版本号做矛盾检测
brittle（格式多样、可能多个版本并存）。矛盾靠 review 兜底；此决策记录于此。

### 改名深度：只改活文档，归档冻结

`git mv` 两文件 + 更新全部活引用：根 `package.json` `check:meta`、`AGENTS.md`、
`CONTRIBUTING.md`、主 spec（dependency-upgrade、ci-matrix，随本 change 归档
sync）、`Plan/测试规划.md`、活跃 change `upgrade-python-3-15` 的 proposal/tasks。
`openspec/changes/archive/` 是冻结历史，旧文件名引用保留原样
（check_md.py 对归档区豁免活文档链接规则）。JSON 内部键名（`pins`、
`pin_location`、`categories`）不动——语义仍准确，改名只针对文件名名不副实
（表内还有配对、machine 钉、发现规则，不止"pins"）。

### Plan/ 收口形态

`Plan/测试规划.md` 问题二整节删除（结论全部进 spec）；待议节标题改为两问按
内容命名（"过期检查门禁化"、"配对版本校验"），落地形态改"两问合并"；
机器人安全阀（自动化提议升级时 MUST NOT 推荐 blocked 版本）作为备查要求
并入"过期检查门禁化"节——那是门禁化 change 的验收项，本 change 不实现。

## Risks / Trade-offs

- **黑名单腐化**：条目只增不删 → 体检噪音。缓解：配对类禁令有明确删除条件
  （生命周期规则进 spec）；自身 bug 类噪音低（不挡升级路径，只挡回踩）。
- **映射表漂移**：登记表改名而脚本映射表未改 → 该条目黑名单静默失效。
  缓解：映射表与登记表同仓同 review；体检对无法映射的 blocked 条目输出警告。
- **改名断链**：遗漏引用点。缓解：tasks 含全仓 grep 旧文件名 + `pnpm check:md`
  链接校验；归档区豁免规则保证不误伤冻结历史。

## Migration Plan

一次性 change：改名 + 字段 + 两脚本 + 文档同步，单分支完成，闸门全绿后合并。
无运行时迁移、无数据迁移（登记表当前无 blocked 字段，加字段向后兼容）。
回滚 = revert 合并 commit。

## Open Questions

（无——设计经 grilling 全部定案。）
