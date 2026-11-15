# 设计：考古清理、堵源头、关缝隙与覆盖率统一

## 背景与目标

考古文字反复清不干净，实证三个叠加根因：扫描面真空（配置类无门禁）、
治理规则自相矛盾（`AGENTS.md` 要求附出处 vs 「使用信息」禁指针）、
审查缝隙（三轴只审 diff，archive 态体检只扫改动面外，"被触碰但不在 diff
内"的旧行两边不管）。本 change 对应四层解法：扩面门禁、堵源头、
两态体检关缝隙、存量清零；另将治理脚本覆盖率范围与阈值统一进
`pyproject.toml`。人工裁决全程见本 change 讨论记录，结论已吸收进
proposal 与 delta。

## 决策

### D1 两层分工：门禁只守固定形态，语义考古交 AI 审查

门禁模式 = 机械可判、零语义歧义的**封闭固定形态集**（六项：`LL-` 编号、
`CI run` + 六位以上数字、动词+日期归因、动态 change 目录名、开发文档指针、
`design decision`/`design D` + 数字）。中文"废止/推翻/原口径/不再是"等
需理解上下文才能区分"契约声明"与"历史归因"的语义考古**不进任何词表**，
由 review Standards 轴的 AI 全面审查承担。理由：词表硬匹配语义必然误报
（实证两例：`touchstone-core/spec.md` 的"不再是合法选项行"描述输入行为结果、
`api-contract/spec.md` 的 `upload 概念全仓废止` 是契约声明），误报会训练
人忽略门禁输出，反而削弱固定形态层的可信度。

### D2 扫描面与豁免

`check_comments.py` 后缀集 `rs/py/ts` → `rs/py/ts/yml/yaml/toml`。
文件级豁免白名单（白名单外零豁免）：

- `pnpm-lock.yaml`——生成物，字符串内容不可控；
- `openspec/changes/archive/` 下 `.openspec.yaml`——冻结历史，沿用
  `check_md.py` 的 archive 豁免先例；
- 既有构建目录（沿用脚本内 `EXEMPT_DIRS`）；
- `openspec/config.yaml`——整体豁免：其正文的路径引用（`Plan/`、
  `openspec/specs/`）是给 agent 的流程指令功能语义，机械指针模式无法
  区分"指令"与"泄漏"，误杀伤功能；其内容质量由 AI 审查覆盖。

`openspec/changes/<在途 change>/.openspec.yaml` 与 `pnpm-workspace.yaml`
不豁免（实证：当前无触发内容）。

### D3 日期归因只认"动词+日期"

模式取 `Re-enabled <ISO 日期>`、`重新启用 <ISO 日期>`、`已标定`，
不取裸 ISO 日期。实证依据：`scripts/tests/versions/lib/test_latest.py`
夹具含 `rustc 1.99.1 (58cf8f9c3 2026-10-13)`，裸日期模式会误伤；
动词前缀区分"归因叙述"与"数据值"。`deprecated` 是标准契约用语，
不进任何模式。

### D4 新标记对全部扫描文件统一生效（假设记录）

`CI run` 号、动词+日期、`design decision N` 三类新标记对六类后缀统一
应用，不按后缀分模式。实证依据：当前 `.rs`/`.py`/`.ts` 中此类标记零
存量（grep 核实），统一应用无误报成本；且"注释不写 CI run 号"对代码
同样成立，分模式只增复杂度。

### D5 `check_md.py` 不改动

原 Plan 曾拟给 `check_md.py` 增中文考古词模式，被 D1 推翻：语义考古
不进门禁，`check_md.py` 维持现状。治理 spec line 446 的自指问题
（正文列举被禁词字面）随之不存在——中文词根本不在门禁词表内。

### D6 delta 与直接改写的分界

治理 spec 扫描范围扩面是行为变化，走本 change 的 specs delta；
6 个能力 spec 正文的 11 处考古叙述是纯措辞改写、无契约行为变化，
直接改主 spec 正文，逐条清单留痕 tasks.md。理由：为改措辞造多份
delta 是空转（sync 时机械合并，无评审增量）。另 3 处命中经判定为
当前契约表述保留不改（tasks 3.7）。

### D7 保留 `coverage_gate.py` 的 floor 能力

floor 参数与地板 0 单测是通用阈值工具的合法输入值，不随 spec 流程
叙述清理而阉割。

### D8 堵源头：出处落 commit 与账本，不落文件注释

`AGENTS.md`「改动要有去向：常驻文档新增规则须附出处（LL 编号或 spec
指针）」与「代码只写使用信息」互斥——前者驱动 agent 往 ci.yml 等文件
里塞 `LL-011`，后者又禁止它，这就是"永无止境"的源头。修法：去向 =
commit message 与 lessons-learned 账本（正是"追溯靠 git log"），被门禁
扫描的文件内只留当前契约。本条只改 `AGENTS.md` 措辞，不动 governance
spec（「使用信息」条本无冲突）。

### D9 两态体检：同一机制、两种触发，关审查缝隙

实证缝隙：review 三轴只审 diff，archive 态体检明文"扫描范围 = 改动面
之外"，被触碰文件的非 diff 旧行两边都不管——`ci.yml` 的 `LL-011` 正是
这样隐身数月。解法：同一套体检机制加 apply 态触发（三轴 review 后、
`check:outdated` 前，扫 diff 触碰文件全文），与三轴（diff 行）、archive
态（其余存量）拼成无缝覆盖。维度 = 五维去 `Plan/` 维（目录级对象，
单文件态不适用）加语义考古维；语义考古维两态通用（archive 态五变六）。
只读、三级去重、落 Plan/ 等点名、不阻塞——两态同纪律，不写两套。
apply 态每次必跑，全豁免时记"已查，无适用文件"——豁免判定交给机械
规则，不留临场判断空间。

### D10 spec 改名 `archive-health-check` → `health-check`

机制不再专属 archive，按"命名一眼懂"标准必须改名。实证波及面仅 3 处
需同步：`openspec/config.yaml` L71 指针、`openspec/specs/README.md` 路由行、
spec 自身标题；账本 `workflow.md` L241 与 `Plan/防越权机制` L9 属冻结
历史/临时笔记，按豁免不改。目录改名由 apply 时 `git mv` 执行，
`check_md.py` 的 BROKEN FILE/ARCHIVE PATH 门禁兜底防漏改。

### D11 覆盖率配置整体迁入 `pyproject.toml`

范围与阈值写 `[tool.coverage]`/`[tool.pytest.ini_options]`，`check:py`
命令行删 `--cov=`/`--cov-fail-under=`——整体搬而非双写，否则两份清单
必漂移（LL-076 同因）。地板范围 = `scripts/versions` + `coverage_gate.py`
（三份 codecov 报告的阅卷人，它回归 = 全部地板失效）+ `check_comments.py`
（本 change 新扩门禁，零测试即静默失效）。阈值 100 与既有口径一致；
前置补测：阅卷人非数字键分支 + `runpy` 守卫（出自 Plan/ 的
`阅卷人覆盖率-2026-11-14.md` 已核清单），`check_comments.py`
的测试即本 change 任务 1.1。

### D12 审查步骤合法、清理步骤仍禁（旧裁决边界修正）

早前裁决"不在 config.yaml 加人工清理步骤"拦的是**自动改文件**的清理
动作（软约束会被跳过且越权）；本次加的是**只读审查**步骤（发现落
Plan/ 等点名，不自动改任何东西），两者不同类，不冲突。语义考古无法
门禁化，才更需要流程里的固定审查步骤——此为人工裁决，覆盖旧裁决的
字面范围，边界记于此防被误读为违反旧裁决。

## 测试策略

`scripts/tests/` 新增 `check_comments` 单测（沿用 `test_coverage_gate.py`
先例）：每个固定形态标记一条正例（必须红）、三类负例（裸日期、
`deprecated`、豁免文件路径）必须绿。注意：测试夹具中的触发标记必须
构造在**非注释行**（字符串字面量）或以拼接构造——`.py` 注释行本身在
扫描面上，写死字面标记会让门禁脚本的测试自己变红。阅卷人
`coverage_gate.py` 补 2 条（非数字键分支、`runpy` 守卫）后，三者随
`[tool.coverage]` 地板 100 受闸。

## 波及面

- `scripts/check_comments.py`（扩面+模式+豁免）、`scripts/tests/`（新增
  `test_check_comments.py` + 阅卷人补测 2 条）
- `.github/workflows/ci.yml`、`rust-toolchain.toml`（存量改写）
- 6 个能力 spec 正文措辞（清单见 tasks.md；另 3 处命中判定保留）
- `AGENTS.md`（去向措辞堵源头）、`openspec/config.yaml`（apply guidance
  加 apply 态体检一步；archive guidance 的 spec 名指针改名同步）
- `openspec/specs/archive-health-check/` → `health-check/`（`git mv` +
  `specs/README.md` 路由行同步）
- 根 `pyproject.toml`（`[tool.coverage]`）、根 `package.json`（`check:py`
  删 `--cov` 参数）
- `Plan/考古文字清理-2026-11-14.md`、`Plan/阅卷人覆盖率-2026-11-14.md`
  （结论已吸收，apply 完成时删除）
- 命令面：`pnpm check:meta`/`pnpm check:md` 入口与退出码契约不动；
  `check:py` 名称与退出码契约不变、命令体简化；ci.yml 的 YAML 格式由
  `pnpm check:ts`（Biome）执法，改写后须绿。
