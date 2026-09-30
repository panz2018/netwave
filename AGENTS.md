# netwave — agent 行为准则

## 通用原则（源自 Karpathy 对 LLM 编码陷阱的观察，任何改动适用）

### 编码前思考 — 不假设，不藏困惑

- 显式陈述假设；不确定就问，不要默默选解释
- 有更简单方案就说；困惑就停下，点名困惑处

### 简洁优先 — 最小代码解决问题

- 不做没要求的功能、单次使用不造抽象、不加没要求的"灵活性"
- 200 行能压到 50 行就重写；资深工程师会说"过度复杂"就简化

### 精准修改 — 只碰必须碰的

- 不顺手"改进"相邻代码/注释/格式，不重构没坏的东西，匹配现有风格
- 只清理自己改动造成的孤儿；无关死代码提一嘴，不删
- 检验：每一行 diff 都能追溯到本次请求
- **改动波及面必须改全**：动构建/工具链/API 时，同步核对并改到
  文档（README/spec/账本）与 CI（步骤顺序、闸门命令）——
  改代码 ≠ 改完；漏改 CI 构建顺序或文档旧事实即未完成
  （LL-008 grep 旧副本、LL-034 CI 构建不变式）

### 目标驱动 — 先定成功标准再循环

- "修 bug" → "先写复现测试，再让它通过"；"加验证" → "先写非法输入测试"
- 多步任务列短计划：`步骤 → 验证: 检查项`

琐碎改动（改错别字、一行明显修复）自行判断，不必全套流程。

## 终端命令规范（防卡死）

- **一次一条命令**：禁止 `a && b && c`
  串多个慢命令（install/build/首次运行工具链），慢在哪一步必须看得见。
- **全部加 timeout**：联网/构建命令 `timeout 300 <cmd>`；纯本地快命令
  `timeout 60 <cmd>`。超时即报告并拆分排查，不原地干等。
- **首次联网操作预告**：`pnpm install`、`uv sync`（下载 Python）、
  `wasm-pack build`、`cargo` 首次拉 crate 均可能数分钟，执行前说明预计耗时。
- corepack 命令必须带 `COREPACK_ENABLE_DOWNLOAD_PROMPT=0`（否则交互卡死）。

## 依赖版本策略

- **默认用最新版**：新增或升级依赖时直接钉最新（含间接依赖， `cargo update` /
  `pnpm outdated` 定期体检）；项目早期升级成本最低。
- **最新版有 bug 才回退**：仅当最新版导致构建/测试失败且确认是上游bug（非本项目用法问题）时，回退到次新版（`--precise`），并在所在子项目 README 的 Gotchas 记录回退原因与跟踪的上游 issue。
- **配对依赖一起升**：pyo3↔numpy、napi↔napi-derive 等必须同 major 联动，升级后必跑四端对拍确认数值不变。

## 反思铁律（防复发，机制见 lessons-learned spec）

- 动手前扫 [openspec/specs/lessons-learned/INDEX.md](openspec/specs/lessons-learned/INDEX.md)，命中再开对应 scope 分片。
- 被人工纠正当轮登记：命中旧条目=引用编号并说明未遵守原因；无=新增 LL 到对应分片+INDEX。不拖到归档。
- review 三轴：Standards × Spec × Lessons（逐条对照账本，命中即打回）。
- 可门禁化的 LL 落进 `pnpm check`，文字规则退役。

## 项目铁律（动手前必读，此处不重述）

- **[openspec/specs/project-governance/spec.md](openspec/specs/project-governance/spec.md)** —
  netwave 全部硬约束的唯一真相源（数据布局 / 精度分层 / TDD / 容差 manifest /
  z0 端口属性 / 性能底线 / 零拷贝 / 语言约定 / 权威术语源）
- OpenSpec 开发工作流（六步循环、技能地图、工具链状态）见
  [CONTRIBUTING.md](CONTRIBUTING.md)；`/opsx:*`
  命令会自动注入约束指针（[openspec/config.yaml](openspec/config.yaml)）

## 文档语言与阅读入口

- **语言**：仅 `openspec/` 与 `Plan/`
  用中文；其余一切（README、docs、代码注释、rustdoc、docstring、JSDoc、commit
  message）用英文。
- **动手前先读所在子项目的 README.md**：只含本目录编译/测试/部署命令；坑与实现细节唯一存于 lessons-learned 账本，README 不重述。- **参考第三方前先查账本许可表**（lessons-learned docs 分片）：GPL 源只读思想不开代码（宪法 知识产权合规）。- **作用域纪律**：子项目 README 只放**本目录作用域**的命令与细节；workspace/根级命令（如
  `cargo llvm-cov --workspace`、markdownlint、链接校验）只放根文档——面向用户的放
  根 README，面向开发的（门禁命令、环境坑、文档地图）放根 CONTRIBUTING.md——
  禁止下沉到子 README。

## Plan/ 生命周期

- Plan/ 只放**未执行**任务；执行完且结论吸收进
  `openspec/specs/`、各 README 或 governance spec 后**删除该文件**。
- 终态：Plan/ 清空删除，`openspec/` 为唯一事实源（constitution 已迁入
  `openspec/specs/project-governance/`）。
- 新改进想法一律先落 Plan/ 新 md，不在对话里口头遗留。
- 复盘结论按类型归位：坑/纠正/实现决策 → lessons-learned 账本（对应 scope 分片+INDEX）；流程机制 → CONTRIBUTING（Development workflow）；硬约束 → governance spec。README 与子 README 不设"复盘/Gotchas"章节。
- **文档地图（内容分配清单，增删只改本节）**：契约级决定→governance spec；行为准则+本地图→AGENTS.md；坑/纠正/实现决策→lessons-learned 账本；人类开发命令与目录 layout→CONTRIBUTING；本目录命令→子 README；用户视角→根 README；历史→git log（文档不留存）。

## 文档书写规范（改 Plan/ 或任何 Markdown 必须遵守）

- **标题不带章节序号**：位置数字会进 GitHub 锚点，章节重排即全仓断链。例外： 概念编号保留（铁律一~七——它们是名字，不是位置）。
- **禁写临时名称**："方案一/方案二"、"阶段 N"等讨论代号与路线图编号随时会改名、
  随时会变更，禁止写入 spec、账本、Plan 及任何持久文档；用内容本身命名（如
  "worker 常驻架构"）；引用他文结论用标题跳转链接，不用代号。
- **禁写无意义日期**：文档只留最终结论，不留历史过程（"已拍板于 X"、"X 修订"、
  "已瘦身（X）"、"session X"等时间戳一律不写）——日期无人看，追溯靠 git log。
  例外：外部标准版本号（如 Touchstone v2.1）与 git commit hash（可解析的证据）。
- **引用一律用标题跳转链接**（反引号内为格式模板）：`[标题名](文件.md#锚点)`
  禁止 `§X.Y`、禁止"见第 N 节"、禁止裸数字章节引用。
- **只链相关**：只链接与本文主题直接相关的现存文档；禁止因历史原因保留指向已归档/已删除/无关文档的链接。
- **代码块内不放链接**（不渲染）：块内注释写"见下方说明"，链接放块外正文。
- **锚点 slug 规则**：标题转小写、空格→`-`、标点删除、中文保留。改标题或增删章节后，必须跑链接校验（Python 模拟 slug 规则，逐一验证文件存在 + 锚点匹配，断链当场暴露）。
- **每次改动后必须跑 markdown 检查**：`pnpm check:md`（仓库根，退出码 0 才算
  完成）。它聚合三项：markdownlint 内容规则（`.markdownlint.jsonc`）、Prettier
  格式（`.prettierrc.json`，`proseWrap: preserve`——中文+行内代码下 `always`
  会碎断）、`scripts/check_md.py` 链接+跨行 code span 校验
  （纯标准库）。自动修复：`pnpm fix:md`。
- **JS/TS/JSON 的 lint+format 归 Biome**（根 `biome.jsonc`），聚合为
  `pnpm check:ts` / `pnpm fix:ts`；Markdown 归 Prettier；两者作用域不重叠。
  `.claude/` 下的第三方生成文件不受本仓库格式约束，已在
  `.markdownlint-cli2.jsonc` 中忽略。
- **`tsc --noEmit` 类型门禁不进零构建闸门**：`src/` 壳 import `dist/` 的
  生成绑定，类型门禁必须在 glue 构建后跑——本地 `pnpm build:wasm` +
  `build:native` 后 `pnpm -C typescript typecheck`，CI 在 node job 双 glue
  构建后跑。禁止为零构建环境造 glue 桩（桩=第二份 API 真相源，必漂移）。
- **对称命令（根 package.json 为唯一定义处，本文只列名字）**：聚合
  `check`/`fix`（跑全部语言）+ 按语言四组
  `check:md`/`fix:md`、`check:ts`/`fix:ts`、`check:rs`/`fix:rs`、
  `check:py`/`fix:py`——`check:` 只报告，`fix:` 会改文件；具体子命令与旗标
  以根 `package.json` 的 `scripts` 为准，改命令只改那里。日常节奏：改完代码
  `pnpm fix` → `pnpm check`；提交前 CI 跑的就是同一条 `pnpm check`。
- 历史文档（宪法修订历史）里的旧式引用**不改写**——历史记录保持原样。
