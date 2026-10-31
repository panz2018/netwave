# LL ledger — scope: workflow

## Entries

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
