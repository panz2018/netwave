# 设计：考古文字清理与门禁扩面

## 背景与目标

「元规则 代码只写使用信息」只覆盖 `.rs`/`.py`/`.ts`，配置文件
（`.yml`/`.yaml`/`.toml`）为门禁真空区，`ci.yml` 已积累数十处开发过程
注释。本 change 扩面门禁、定稿封闭模式集、清完存量、同步治理 spec。
人工裁决全程见本 change 讨论记录，结论已吸收进 proposal 与 delta。

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
8 个能力 spec 正文的 15 处考古叙述是纯措辞改写、无契约行为变化，
直接改主 spec 正文，逐条清单留痕 tasks.md。理由：为改措辞造 8 份
delta 是空转（sync 时机械合并，无评审增量）。

### D7 保留 `coverage_gate.py` 的 floor 能力

floor 参数与地板 0 单测是通用阈值工具的合法输入值，不随 spec 流程
叙述清理而阉割。

## 测试策略

`scripts/tests/` 新增 `check_comments` 单测（沿用 `test_coverage_gate.py`
先例）：每个固定形态标记一条正例（必须红）、三类负例（裸日期、
`deprecated`、豁免文件路径）必须绿。注意：测试夹具中的触发标记必须
构造在**非注释行**（字符串字面量）或以拼接构造——`.py` 注释行本身在
扫描面上，写死字面标记会让门禁脚本的测试自己变红。

## 波及面

- `scripts/check_comments.py`（扩面+模式+豁免）
- `.github/workflows/ci.yml`、`rust-toolchain.toml`（存量改写）
- 6 个能力 spec 正文措辞（清单见 tasks.md；另 3 处命中判定保留）
- `scripts/tests/test_check_comments.py`（新增）
- `Plan/考古文字清理-2026-11-14.md`（apply 完成时结论已吸收，删除）
- 命令面不变：`pnpm check:meta`/`pnpm check:md` 入口与退出码契约不动；
  ci.yml 的 YAML 格式由 `pnpm check:ts`（Biome）执法，改写后须绿。
