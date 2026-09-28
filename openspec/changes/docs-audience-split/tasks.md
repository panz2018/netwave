# Tasks

## 1. 建立 lessons-learned 账本

- [x] 1.1 创建账本骨架 `openspec/specs/lessons-learned/`：`INDEX.md`（一行
      一条：LL 编号 | scope | 一句话规则）+ 按 scope 分片小文件（ci.md/
      core.md/python.md/typescript.md/docs.md/testdata.md，单文件 ≤50 行）；
      文件头写明四要素格式（LL-NNN / scope / 犯过证据 / 规则+复发检测）与
      "只增、编号不复用"规则；验证：骨架文件齐备且含格式说明段
- [x] 1.2 迁入首批十条人工纠正 LL-001..LL-010：toY 同步/异步契约、f_scaled
      命名、关闸门求绿、CI push-and-pray、建议不存在的命令（openspec validate）、
      输出不含绝对路径、`_` escape hatch、文档陈旧副本、假死命令（corepack/
      llvm-cov）、utf-8 读取；另迁入 CONTRIBUTING Environment gotchas 余下
      条目（Windows GITHUB_PATH、binaryen 整树、api.github.com 限流、pyo3
      venv 三件套）；按 scope 写入分片并同步 INDEX.md，每条附 commit/session
      证据；验证：条目齐备、四要素完整、INDEX 与分片一一对应
- [x] 1.3 迁入子 README 内容：`core/README.md` Implementation notes+Gotchas
      → core.md 分片、`python/README.md` 两节 → python.md、`typescript/README.md`
      两节 → typescript.md、`testdata/README.md` Gotchas → testdata.md；逐条
      判定可门禁化并填写复发检测方式；验证：7 节内容全部可在对应分片检索到
      且 INDEX 同步

## 2. AGENTS.md 反思铁律

- [x] 2.1 AGENTS.md 新增简短铁律段（数行指针，不重述 spec 正文）：动手前扫
      `openspec/specs/lessons-learned/INDEX.md`，命中再开对应 scope 分片；被
      人工纠正当轮登记（命中旧条目=引用编号并说明原因，无=新增 LL）；review
      三轴含 Lessons；验证：AGENTS.md 新增段落 ≤10 行且 governance spec 元规则
      "只放指针"不违反
- [x] 2.2 AGENTS.md 复盘归位规则改写：坑/教训去向由"子项目 README Gotchas"
      改为"lessons-learned 账本"；验证：AGENTS.md 内无"子 README Gotchas"回写
      指引残留
- [x] 2.3 AGENTS.md「文档书写规范」新增链接相关性一条：只链与本文主题直接
      相关的现存文档，禁止因历史原因保留指向已归档/已删除/无关文档的链接；
      验证：该条存在于 AGENTS.md 书写规范节内

## 3. governance spec 增补（delta 已在 specs/ 中）

- [x] 3.1 复核 delta 中「文档受众分层」ADDED Requirement 与现有铁律/元规则
      无冲突、场景均可验收；验证：`openspec validate docs-audience-split`
      通过（CLI 自带校验）

## 4. CONTRIBUTING.md 重构（人类开发者文档）

- [x] 4.1 迁入 Repository layout：覆盖全部顶层目录（core/python/typescript/
      testdata/scripts/openspec/Plan/.github 等），每目录一句话作用；验证：
      layout 条目数 = 顶层目录数
- [x] 4.2 Toolchain 表去版本号改写为"任务→工具→验证命令"路由表；验证：
      表内无具体版本号，版本由锁文件/rust-toolchain.toml 承载
- [x] 4.3 删除 Environment gotchas、Anti-rework checklist 节（内容均已
      迁入 ledger）；Quality gates 保留命令、阈值改为指针
      指向 ci-matrix/governance spec；review 步骤改写为三轴（Standards × Spec ×
      Lessons），retro 回写去向同步改；验证：文中无已迁节残留

## 5. README 与子 README 瘦身

- [x] 5.1 根 README.md 删除 Repository layout 节，保留指针至 CONTRIBUTING；
      验证：README 无 layout 节、无构建命令
- [x] 5.2 四个子 README 删除 Implementation notes / Gotchas 节，只留本目录
      命令；验证：`grep -E '^#+ .*(Implementation notes|Gotchas)' */README.md`
      零命中
- [x] 5.3 `project-governance` spec 删除「修订历史」节（不另建文件，
      追溯靠 `git log openspec/specs/project-governance/`）；验证：spec
      正文无修订历史节，无新建 HISTORY.md

## 6. 链接清理与门禁

- [x] 6.1 全仓清理无关/历史遗留链接（指向 archive/、已删除 Plan/ 文件、
      已迁走章节的引用），逐文档过一遍只留作用域内相关链接；验证：
      `python3 scripts/check_md.py` 零断链 + 人工抽查清单
- [x] 6.2 `scripts/check_md.py` 新增门禁：子 README 禁现 Implementation
      notes/Gotchas 标题、禁指向 `openspec/changes/archive/` 的链接；先写会失败
      的用例（red）再实现（green）；验证：门禁对旧结构报红、对新结构报绿

## 7. 收尾验证

- [x] 7.1 `pnpm check:md` 全绿（EXIT=0）；三文档受众抽查：README 无开发
      细节、CONTRIBUTING 无坑清单、ledger 四要素完整；验证：命令退出码 0 +
      抽查记录写入本 change 的 review 备注
