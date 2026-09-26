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

## 项目铁律（动手前必读，此处不重述）

- **[Plan/constitution.md](Plan/constitution.md)** —
  netwave 全部硬约束的唯一真相源（数据布局 / 精度分层 / TDD / 容差 manifest /
  z0 端口属性 / 性能底线 / 零拷贝 / 语言约定 / 权威术语源）
- OpenSpec 工作流见 [Plan/开发流程.md](Plan/开发流程.md)；`/opsx:*`
  命令会自动注入约束指针（[openspec/config.yaml](openspec/config.yaml)）

## 文档语言与阅读入口

- **语言**：仅 `openspec/` 与 `Plan/`
  用中文；其余一切（README、docs、代码注释、rustdoc、docstring、JSDoc、commit
  message）用英文。
- **动手前先读所在子项目的 README.md**：编译/测试/部署命令与实现细节、坑（Gotchas）以各子 README 为唯一存放处，顶层只留指针不重述。
- **作用域纪律**：子项目 README 只放**本目录作用域**的命令与细节；workspace/根级命令（如
  `cargo llvm-cov --workspace`、markdownlint、链接校验）只放根 README，禁止下沉到子 README。

## Plan/ 生命周期

- Plan/ 只放**未执行**任务；执行完且结论吸收进
  `openspec/specs/`、各 README 或 constitution 后**删除该文件**。
- 终态：Plan/ 清空删除，`openspec/` 为唯一事实源（constitution 届时迁入
  `openspec/project.md`）。
- 新改进想法一律先落 Plan/ 新 md，不在对话里口头遗留。
- 复盘结论按类型归位：流程坑 →
  [Plan/开发流程.md](Plan/开发流程.md)；命令/实现坑 → 对应子项目 README 的 Gotchas 节；硬约束 →
  constitution。README 不设独立"复盘"章节，只沉淀结论。

## 文档书写规范（改 Plan/ 或任何 Markdown 必须遵守）

- **标题不带章节序号**：位置数字会进 GitHub 锚点，章节重排即全仓断链。例外：概念编号保留（铁律一~七、阶段 0-8——它们是名字，不是位置）。
- **引用一律用标题跳转链接**（反引号内为格式模板）：`[标题名](文件.md#锚点)`
  禁止 `§X.Y`、禁止"见第 N 节"、禁止裸数字章节引用。
- **代码块内不放链接**（不渲染）：块内注释写"见下方说明"，链接放块外正文。
- **锚点 slug 规则**：标题转小写、空格→`-`、标点删除、中文保留。改标题或增删章节后，必须跑链接校验（Python 模拟 slug 规则，逐一验证文件存在 + 锚点匹配，断链当场暴露）。
- **每次改动后必须跑 markdown 检查**：`pnpm check:md`（仓库根，退出码 0 才算
  完成）。它聚合三项：markdownlint 内容规则（`.markdownlint.jsonc`）、Prettier
  格式（`.prettierrc.json`，`proseWrap: preserve`——中文+行内代码下 `always`
  会碎断，2026-09-26 改回）、`scripts/check_md.py` 链接+跨行 code span 校验
  （纯标准库）。自动修复：`pnpm fix:md`。
- **JS/TS/JSON 的 lint+format 归 Biome**（根 `biome.jsonc`）+ `tsc --noEmit`
  类型门禁，聚合为 `pnpm check:ts` / `pnpm fix:ts`；Markdown 归 Prettier；
  两者作用域不重叠。`.claude/` 下的第三方生成文件不受本仓库格式约束，已在
  `.markdownlint-cli2.jsonc` 中忽略。
- **对称命令（根 package.json 为唯一定义处，本文只列名字）**：聚合
  `check`/`fix`（跑全部语言）+ 按语言四组
  `check:md`/`fix:md`、`check:ts`/`fix:ts`、`check:rs`/`fix:rs`、
  `check:py`/`fix:py`——`check:` 只报告，`fix:` 会改文件；具体子命令与旗标
  以根 `package.json` 的 `scripts` 为准，改命令只改那里。日常节奏：改完代码
  `pnpm fix` → `pnpm check`；提交前 CI 跑的就是同一条 `pnpm check`。
- 历史文档（宪法修订历史）里的旧式引用**不改写**——历史记录保持原样。
