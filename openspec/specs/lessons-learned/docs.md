# LL ledger — scope: docs

## Entries

### LL-005 命令先验证存在

- 犯过：建议不存在的 `openspec validate` 子命令（session 两次追问）
- 规则：让用户/文档引用的命令先自己跑或引 `--help`
- 复发检测：review 抽查文档命令可执行

### LL-006 输出写绝对路径

- 犯过：dump 脚本只 print "dumped bin" 无位置（`5645e11` 修）
- 规则：写文件的脚本输出含完整文件路径
- 复发检测：可门禁化——脚本输出断言测试

### LL-008 改事实后 grep 全仓旧副本

- 犯过：两次全仓扫旧描述（`409b057`/`4f5a9bd` 修四处事实错误）
- 规则：改命令/改名/工具链事实后 grep 全 `.md` 更新每处；工具链状态变化
  同改动更新表格
- 复发检测：review Standards 轴要求 diff 覆盖所有旧引用点

### LL-010 读非 ASCII 文件显式 utf-8

- 犯过：Windows cp1252 读含中文 manifest 抛 `UnicodeDecodeError`（`89e28f2`）
- 规则：所有 `read_text()`/`open()` 显式 `encoding="utf-8"`
- 复发检测：可门禁化——grep `read_text()`/`open(` 无 encoding 即红

### LL-028 sync 后 archive 会重复追加 delta

- 犯过：手动 sync 后再跑 `openspec archive`，CLI 二次应用 delta，
  governance spec 出现重复需求块（MD024 红）
- 规则：sync 与 archive 只选其一应用 delta；archive 自带 sync，手动
  sync 过则归档后必须 diff 主 spec 去重
- 复发检测：可门禁化——`pnpm check:md` MD024 重复标题即红（已生效）

### LL-029 第三方许可表与 GPL 红线

- 犯过：无（预防性登记，license-compliance）
- 规则：参考第三方前先查本表——scikit-rf BSD-3-Clause
  (<https://github.com/scikit-rf/scikit-rf>) 可抄代码但声明随分发；
  SignalIntegrity GPL-3.0-or-later
  (<https://github.com/Nubis-Communications/SignalIntegrity>) **禁抄代码/
  禁逐行翻译，只读思想**；Touchstone spec v2.1 IBIS 条款
  (<https://ibis.org/touchstone_ver2.1/touchstone_ver2_1.pdf>) 实现自由、
  全文勿入仓；《S-Parameters for Signal Integrity》CUP 全版权
  (<https://doi.org/10.1017/9781108784863>) 禁复制原文/图表。借鉴实现
  MUST 在 rustdoc 标注出处
- 复发检测：元数据一致性已门禁化 `pnpm check:meta`；GPL 混入检测待立项；
  review Lessons 轴对照本表

### LL-032 持久文档禁写临时名称

- 犯过：spec/账本/Plan 写入"方案一"等讨论代号与路线图数字代号，代号随时改名导致
  引用漂移（人工纠正，规则入 AGENTS.md 文档书写规范）
- 规则：持久文档用内容命名（如"worker 常驻架构"），需时点附定案日期；引用结论
  用标题跳转链接不用代号
- 复发检测：可门禁化——`check_md.py` grep "方案[一二三]/阶段 [0-9]" 与
  无意义日期戳于 openspec/specs/ 即红；review Standards 轴对照

### LL-033 决策编号不出决策文档

- 犯过：design.md 用 D1–D6 编号做决策标题，代码注释（tsdown.config.ts、
  exports.test.ts）与 tasks.md 跨文件引用 "design D1/D2/D3"——回头无人能解
  （人工纠正，LL-032 同族复发）
- 规则：决策编号仅限单文档内自引用；跨文件引用与代码注释一律用决策标题的
  内容本身（如"见 design.md「tsdown 多 entry 单次构建」"），代码注释不写
  任何外部文档编号
- 复发检测：已门禁化——`check_md.py` DECISION TAG 规则 grep
  `design D[0-9]`/`（D[0-9]`/`按 D[0-9]`/`见 D[0-9]` 于全仓 `.md`+`.ts`
  即红（archive 与账本豁免——它们引用反例作证据）；入 `pnpm check:md`

### LL-035 对话镜像用户语言，文档按目录分语言

- 犯过：worker-resident-implementation 提案会话中对话正文混写英文散文词
  （Finding/Goals/spike 等），且规则草案误写"规划正文用中文"未覆盖
  "对话必须镜像用户提问语言"（人工纠正两次）
- 规则：①对话必须用用户提问所用的语言回答，不得凭模型偏好选语言；
  ②文档仅 `openspec/` 与 `Plan/` 用中文，其余一切（docs、代码注释、
  rustdoc/docstring/JSDoc、README）用英文；命令/文件名/API 名等技术
  标识符在任何正文中保留原文
- 复发检测：review Lessons 轴对照本节；不做脚本门禁（散文语言检测
  误报率高）

### LL-038 模糊指令只执行最小明确项，不可逆操作须显式确认

- 犯过：用户说"可以执行"（指跑 `pnpm check` 门禁），我擅自执行整个
  openspec 归档流程（sync 主 spec + mv change 到 archive），被人工纠正
- 规则：短确认语（"可以执行""执行吧"）只覆盖对话中最近明确讨论的那一项；
  归档/spec 同步等改变仓库状态的操作必须由用户点名（"归档""archive"）
  才触发，禁止自行扩大解释
- 复发检测：review Lessons 轴对照本节；执行前列出"将要做的动作"清单，
  含不可逆动作时停下等确认

### LL-039 注释只写当前契约事实，禁历史与路线图叙述

- 犯过：`types.ts`/入口壳注释写"replaces the hand-written index.d.ts"、
  "脚手架期骨架"、"稍后到来"等变更考古与路线图预告，
  用户指出没人看也没人需要看
- 规则：注释面向今天第一次读代码的用户，只写当前契约与行为；历史变更、
  路线图代号、"不再/曾经"类叙述一律不写，追溯靠 git log
- 复发检测：review Standards 轴 grep src 注释中
  `replaces|no longer|used to|phase-[0-9]`，命中即打回

### LL-045 归档 mv 后必须跑全仓 check:md 修相对链接再提交

- 犯过：frequency-unit 归档 `mv` 进 `archive/` 后直接提交，工件内
  `../../specs/...` 相对链接因目录加深一级全部断链，CI lint 红
  （本地只跑了改动文件的检查，未跑全仓闸门）
- 规则：归档移动使 change 工件目录加深一级，其内所有相对链接需补一级
  `../`；归档当轮必须跑全仓 `pnpm check:md`（check_md.py 会解析
  archive 内链接，断链当场暴露）并修完才提交，禁止只检查本次手改的文件
- 复发检测：已门禁化——`pnpm check:md` 即闸门，CI lint job 必红；
  review 时确认归档 commit 同轮含链接修复
