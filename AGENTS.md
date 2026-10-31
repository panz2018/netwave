# netwave — agent 行为准则

**受众 = AI**：本文件与全部规矩文档（lessons-learned 账本与 INDEX、
governance spec、`openspec/config.yaml`、子项目 README）由 AI 读取并执行；
人不读细节、不写记录，人的职责只有两项——决策方向与点名执行。

## 硬护栏（凌驾本文件其余条目）

- **动词 = 授权全集**：只执行人明确点名的动作；未点名的改文件、建文件、
  删文件、`git commit` 一律禁止执行。
- **“研究 / 探讨 / 该不该”类题目 = 只出文字**：给答案与原因，动手执行即越权。
- **“实施”不等于改代码**：指执行此前讨论定下的动作，定的是改文档就改文档。
- **已定裁决 = 已获授权**：直接执行，不必重新确认。
- **闸门自动执行**：spec 与本文件规定必做的 `pnpm check`、`pnpm check:md`、
  测试、波及面同步，即使题目没点名也必须跑，漏掉即违规。
- **不确定必须问**：题目语义有歧义、或会动 spec / 公开 API / 数据布局时，
  必须问人，不许自己选。提问不需要口令——提问不改动任何东西。
- **找事实归 agent，拍板归人**：能从环境查到的不许甩给人；决定权不替人行使。

## 最小规则原则

写规则时追求"能完整表达预期行为的最小信息集"：动作边界（拦住不可逆后果的
硬闸）优于过程管束（规定如何思考与问答的软约束）；已被门禁强制的规则只留
"必跑哪条命令"一句；程序性仪式（固定问答格式、档位表、打勾自检清单）
不入常驻准则。判据唯一正文见
[governance spec「元规则 最小规则原则」](openspec/specs/project-governance/spec.md#requirement-元规则-最小规则原则)。

## 通用原则（源自 Karpathy 对 LLM 编码陷阱的观察，任何改动适用）

### 语言 — 镜像用户语言，文档按目录分语言

- 对话必须用用户提问所用的语言回答（镜像用户语言，不得凭模型偏好选语言）
- 向用户提问与解释 MUST 先给通俗易懂的大白话、再补术语，禁止堆术语
- 文档语言约定（哪些目录中文、哪些英文）属契约，正文见宪法元规则
  「优先级与单一真相源」与「文档语言约定唯一正文在本 spec」（LL-035），
  本节只留指针

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

### 对话效率 — 实证、全景、查现成、卫生

- **机制断言先实证**：凡 GC/FFI/工具链行为断言，先读源码或官方文档并给
  出处（文件+行号/链接）；未实证标「未验证」。
- **多步操作先给全景表**：提交分组/文档归属/命名/波及面，先列完整方案表
  让人一次圈定，不增量上报。
- **方案先查现成做法**：提技术方案前先查同生态现成实现，注明采用或偏离及理由。
- **三次即搜**：同一命令或思路原样重试累计 3 次仍无结论，停止原地试验，
  联网搜官方文档、上游 issue 或同生态成熟方案后再动手（LL-058）。
- **会话卫生**：上下文过半时主动写交接笔记并建议开新会话。

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

见 [dependency-upgrade spec](openspec/specs/dependency-upgrade/spec.md)
——最新稳定版优先、选线钉 LTS/稳定线、登记原则、钉死点登记表
（`scripts/versions/lib/registry.json`）、对账闸门与升级流程的唯一真相源；
本节只留指针，不重述规则。

## 反思铁律（防复发，机制见 lessons-learned spec）

- 动手前扫 [openspec/specs/lessons-learned/INDEX.md](openspec/specs/lessons-learned/INDEX.md)，命中再开对应 scope 分片。
- 被人工纠正当轮登记：命中旧条目=引用编号并说明未遵守原因；无=新增 LL 到对应分片+INDEX。不拖到归档。
- review 三轴与可门禁化 LL 落闸门的判据，唯一正文见
  [governance spec「元规则 review 三轴」](openspec/specs/project-governance/spec.md#requirement-元规则-review-三轴)。

## 项目铁律（动手前必读，此处不重述）

- **[openspec/specs/project-governance/spec.md](openspec/specs/project-governance/spec.md)** —
  netwave 全部硬约束的唯一真相源，按任务路由读：**改文档/流程/法务** →
  元规则段（真相源/冻结/教学式 docs/注释内容/引用/受众分层/知产合规）；
  **改产品代码/API/CI** → 铁律段（数据布局/TDD/容差/skrf/z0/性能/覆盖率/
  worker/协议/命名/构造入口）
- OpenSpec 开发工作流（六步循环、技能地图、工具链状态）见
  [CONTRIBUTING.md](CONTRIBUTING.md)；`/opsx:*`
  命令会自动注入约束指针（[openspec/config.yaml](openspec/config.yaml)）

## 文档阅读入口

- **动手前先读所在子项目的 README.md**：只含本目录编译/测试/部署命令；坑与实现细节唯一存于 lessons-learned 账本，README 不重述。
- **参考第三方前先查账本许可表**（lessons-learned docs 分片）：GPL 源只读思想不开代码（宪法 知识产权合规）。
- **作用域纪律**：子项目 README 只放**本目录作用域**的命令与细节；workspace/根级命令（`cargo llvm-cov -p netwave`、markdownlint、链接校验）只放根文档，禁止下沉到子 README。

### 文档地图（内容分配清单，增删只改本节）

#### AI 必读区

- 行为准则 + 本地图 → `AGENTS.md`
- 坑 / 纠正 / 实现决策 → lessons-learned 账本（分片 + INDEX）
- 契约与硬约束 → governance spec
- 工件规则与 Plan/ 生命周期 → `openspec/config.yaml`
- 本目录编译/测试命令 → 子项目 README
- 门禁命令速查、目录 layout、本地参考镜像 → `CONTRIBUTING.md`

#### 人只看区

- 项目是什么 → 根 README
- 待拍板事项 → AI 在对话中呈上的决策表 / 全景表

**历史** → git log（文档不留存）。

**改动要有去向**：常驻文档新增规则须附出处（LL 编号或 spec 指针）；删除/迁出须写明去向（账本/CONTRIBUTING/spec），内容不得蒸发——行数不是指标，禁止为凑行数删除。缺一在 review Standards 轴打回（LL-071）。

## Plan/ 生命周期

只放未执行任务，结论吸收后删除，终态整目录清空——唯一正文见
[openspec/config.yaml](openspec/config.yaml) 的 `operations` 段（apply/archive
钩子自动注入）。新改进想法一律先落 `Plan/` 新 md，不在对话里口头遗留。

## Markdown 校验

改任何 `.md` 后必须跑 `pnpm check:md`（仓库根，退出码 0 才算完成），自动修复
`pnpm fix:md`。标题序号、临时名称、日期、链接与锚点等书写判据由该门禁强制，
本文件不重述；命令唯一定义处是根 `package.json`，改命令只改那里。
