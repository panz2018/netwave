# LL ledger — scope: workflow

## Entries

### LL-058 试错止损：同一失败 3 次即停，联网搜成熟方案

- 犯过：llvm-cov 覆盖率恒差 6 行问题上，agent 在默认 report 路径上连续换招
  （`inline(never)`、`--remap-path-prefix`、清缓存重建、逐二进制 union）均
  无效仍继续原地试验；用户两次否定 workaround 菜单并要求联网搜索后，
  一次搜索即命中官方 `--codecov` 行合并器（根本解法，实测 950/950=100%）
- 规则：同一命令/同一思路原样重试累计 3 次仍无明确结论，或同一错误修了
  又犯来回打转，立即停止原地试验，联网搜官方文档/上游 issue/同生态成熟
  方案后再动手——绝大多数难题早有标准解法，卡住多半是在用旧知识或过时
  方案绕路；跳出旧知识、用最直接最根本的解决方案
- 复发检测：review Lessons 轴检查排查会话：同一失败第 4 次重试前无搜索
  记录即打回；可门禁化时落进流程工具

### LL-059 复查必须重读源码，禁凭记忆复述旧结论

- 犯过：用户多次要求检查 `version` 的定义，agent 反复声称已检查仍回答
  `version` 是 `bool`（实际定义是 `String`），用户指出“看了这么多次
  眼睁睁地看着还说错”
- 规则：被要求“再检查/查仔细”时，禁止凭上下文记忆复述旧结论；必须重新
  打开目标文件，回答时引用文件+行号作证据；同一错误第二次原样出现
  即视为未读，直接打回
- 复发检测：review 时核对“已检查”类回答是否附文件:行号出处，无出处即打回

### LL-061 openspec apply 连续跑完，不等催

- 犯过：apply 阶段 agent 分批停下等用户催促，用户两次质问“怎么停止了，
  继续呀直到全部完成”
- 规则：执行 tasks.md 时一次连续推进到全部完成或真正阻塞才停；每批完成
  后自报进度并自动续跑下一批；只有需要人工决策（提交授权、方案分歧）
  或闸门失败无法自行修复时才停下询问
- 复发检测：review 时检查 apply 会话：任务未跑完且无阻塞理由的停顿即打回

### LL-064 迁移只推实施，契约措辞必须与终裁同步

- 犯过：oracle 重构 propose 阶段，以"本次只同步路径、golden 层推迟"为由，
  把已废弃的旧契约（golden 提交进 git、每周 golden-refresh）机械抄进
  governance delta 铁律四，用户在工件 review 时才抓到
- 规则：写 spec/delta/任何契约文档时，措辞必须反映最新终裁；"推迟"只
  适用于实施（代码、CI 步骤），不适用于契约本身——spec 是真相源，抄录
  已废弃契约等于复活它
- 复发检测：review Spec 轴逐条对照裁决账本：delta 措辞与终裁不一致即打回

### LL-065 活文档指针先指 delta 路径，sync/archive 时改指主 spec

- 犯过：dependency-upgrade change apply 阶段，AGENTS/CONTRIBUTING 迁移指针的
  目标主 spec 要 sync 后才存在，check:md 报 BROKEN FILE，agent 停下来问排序，
  用户裁定"先指 delta 路径"是本仓既定做法，不必再问
- 规则：活文档引用 change 新建的 spec 时，指针直接指当时存在的 delta 路径
  `openspec/changes/<change>/specs/<cap>/spec.md`；sync/archive 时 check:md 报
  BROKEN FILE/ARCHIVE LINK，当场把指针改成主 spec 链接——这是 sync 流程的
  默认步骤，不是新决策
- 复发检测：sync/archive 时 check:md 报指针违规而未当场修复即打回；
  apply 时为此排序停下来询问即视为未读本条

### LL-066 rustup 无 GitHub Releases，查最新版用 tags API

- 犯过：体检脚本对 rustup 查 `releases/latest` 返回 404——rustup 只打 git tag
  不发 GitHub Release（`rustup self update` 报 up to date 但 API 无 release）
- 规则：查 rustup 最新版用 `api.github.com/repos/rust-lang/rustup/tags` 首项；
  写版本体检前先验证目标仓库 releases API 可用，404 即改查 tags
- 复发检测：体检脚本新增工具时 releases API 报 404 而未改 tags 即打回

### LL-067 写规则前先查治理 spec 是否已有，禁就近塞进当前 change

- 犯过：用户要求"把 else 只做错误兜底写进 openspec"，agent 直接把它作为新
  Requirement 塞进手头的 dependency-upgrade change delta，没先查治理宪法——
  该规则其实早已是 `project-governance` 铁律十三（全仓编码宪法），结果放错
  作用域（升级 spec 混入全仓编码规则）且与铁律十三重复
- 规则：接到"把某规则写进 spec"时，动手前先 grep `openspec/specs/`（尤其
  `project-governance`）确认是否已有覆盖：已有则引用/强化，不另造重复条目；
  确需新增再按规则作用域选目标 spec——全仓编码规则归 governance 铁律，
  能力专属规则归对应 capability，禁止因"正在改这个 change"就近塞入
- 复发检测：review Spec 轴检查新增 Requirement：与 governance 铁律语义重复、
  或作用域与所在 capability 不符即打回

### LL-068 文字规则不门禁化必复发——else 兜底第二次踩

- 犯过：governance 铁律十三「else 只做错误兜底」早已存在，但只靠 review、
  未落进 `pnpm check`；agent 新写 `check_outdated.py` 时仍把已知工作分支
  （endoflife/stable）写进 `else`，同一族问题第二次出现，靠人工 review 才抓到
- 根因：AGENTS.md 明文「可门禁化的 LL 落进 pnpm check，文字规则退役」——
  铁律十三可门禁化却仍是纯文字，写代码处于"让它跑通"模式，`if/elif/.../else`
  的 else 天然当 default 用，没有闸门拦、又没在写前复读铁律，必复发
- 规则：凡「可机械检测」的铁律 MUST 落进 `pnpm check`，不能只留文字 + review。
  else 兜底对 Python 可门禁化：`if/elif` 链（≥1 个 `elif`）的 `else` 体首句
  非 `raise`/`return`/`break`/`continue` 即违规（布尔二选一 0 个 elif、错误守卫、
  循环 break 天然不命中）；Rust 由编译器穷尽 match 保证，TS 视 lint 能力另议
- 复发检测：新增/修改 Python 判别链后跑该门禁；门禁未接入 `check:meta` 即视为
  本条未落实

### LL-070 指令动词穷尽——"回答"不含"修复"，越权执行第三踩

- 犯过：用户命令"提交，然后回答完成的 plan 部分为什么没删"，agent 提交后把
  回答擅自升级成执行——当场删改 Plan/ 文件并再提交（人工纠正）。同族前科：
  LL-038（"可以执行"被扩成整个归档流程）、方案讨论纪律词表"没说出口的动作
  一律不做"
- 根因：把"答案里附带了修复方案"偷换成"修复已获授权"；阶段解锁词表只存在于
  Plan/ 按需读文件，干活时不触达
- 规则：用户点名的动词即本次授权全集（"提交+回答"= commit + 只答）；
  "回答/为什么"类请求只输出分析，任何文件改动另待"实施"口令；
  规则同步入 AGENTS.md 对话效率节（常驻注入位）
- 复发检测：review Lessons 轴对照本条；散文语义无法机械门禁化，靠常驻注入 +
  人工纠正当轮引用编号

### LL-071 防膨胀用去向纪律，不用行数预算

- 犯过：agent 提议给 AGENTS.md 设行数上限门禁防再膨胀，被人工否决——上限会
  逼出"为凑数删内容"，内容无去向丢失（同族：LL-068 门禁化要选对指标）
- 规则：常驻文件防膨胀=去向纪律（新增附出处、删除写明迁往何处，review
  Standards 轴核对）；行数只作观察值，不作闸门；"去向是否合理"是语义判断，
  不可机械检测，不门禁化（LL-035 同理）
- 复发检测：review 时 diff 中出现无去向删除即打回；再提行数预算直接引本条

### LL-073 Plan/ 草案条文未转正即非契约，照搬即过度执行

- 犯过：`Plan/方案讨论纪律.md`「裁决台账」写有"已立项 →
  `openspec/changes/<name>/decisions.md`"，agent 据此在首个立项 change 新建
  `decisions.md`，内容与同 change `design.md`「Decisions」节大量重复，被人工
  纠正（该节属 Plan/ 待讨论草案，从未拍板转正；archive 25 个 change 无一实践）
- 根因：把 Plan/ 的**提案中规矩**当成既成契约执行——Plan/ 按生命周期终态清空，
  其条文是待裁决素材而非真相源；且新建文件与既有工件双写同一事实，正撞
  "同一事实只存一份正文"铁律
- 规则：Plan/ 内规矩未经拍板/归档转正即不具约束力，MUST NOT 据此新增工件或
  改变既有惯例；持久落点沿用既有工件（决策唯一存 `design.md`「Decisions」节，
  不另建 `decisions.md`）。引用 Plan/ 条文前先确认其是否已转正
- 复发检测：review Standards 轴核对——diff 中出现 Plan/ 草案独有、既有惯例
  没有的新工件（尤其与同 change 其他工件内容重叠）即打回
