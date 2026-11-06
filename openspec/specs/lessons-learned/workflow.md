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
  不另建 `decisions.md`）。引用 Plan/ 条文前先确认其是否已转正。
  反向同理：拍板后要生效的规则 MUST 落生效位（AGENTS.md / spec），
  同轮删除 Plan/ 内副本——Plan/ 不是生效规则的家，"在 Plan/ 里试行"
  等于没落地
- 复发检测：review Standards 轴核对——diff 中出现 Plan/ 草案独有、既有惯例
  没有的新工件（尤其与同 change 其他工件内容重叠）即打回；
  已拍板生效的规则正文仍留在 Plan/ 即打回

### LL-074 同一门禁的多节要求合为一条 Requirement，禁机械 ADDED 造重复

- 犯过：sync 专家增补规则时向 governance spec 机械 ADDED 新 Requirement
  「提案工件必带专家增补节」，与既有「提案工件必带出处与不做清单」八成
  重复（同一脚本 `check_proposal.py`、同一命令 `pnpm check:meta`、同套
  零豁免与归档不回溯措辞）；Scenario 标题撞 MD024 后还用「专家增补」前缀
  绕门禁，治标不治本，被人工看出"两条 Requirement 长得很像"
- 根因：把 delta 的 ADDED 当成默认操作，没先对照主 spec 既有同闸门条目查重；
  绕 MD024 的前缀补丁掩盖了重复本身，门禁绿≠内容对
- 规则：新增 spec Requirement 前 MUST 对照主 spec 既有 Requirement，凡共享
  同一门禁脚本/命令/豁免句式/归档策略的多节要求 MUST 合为一条
  （delta 用 RENAMED + MODIFIED，MODIFIED 须含合并后全部保留 Scenario），
  不得另起一条重复正文
- 复发检测：review Standards 轴 diff 中出现两条 Requirement 共享同一脚本 +
  同一命令 + 同一豁免句式即打回；Scenario 靠加限定前缀规避 MD024 即打回

### LL-075 照搬旧文须按现行规则洗词，黑话不随复制复活

- 犯过：`split-version-gates` delta 从主 spec 照搬 Scenario 标题
  「根 pin 由四律自动覆盖」，全仓黑话改名轮（pin→钉版、禁缩写黑话）
  漏网，人工 review 时才抓到
- 规则：把旧文档内容复制进新工件时，正文措辞 MUST 按现行命名/用词规则
  过一遍；仅 openspec 机器校验强制的标识符（MODIFIED 块内既有 Scenario
  标题）可保留旧名，且 MUST 就地注明保留原因与改名去向。工具洗不掉的
  黑话（check_md.py 不查 pin/MSRV）靠人工过目兜底
- 复发检测：review Standards 轴对新增/照搬段落 grep 黑话词
  （pin/MSRV/glue 等），命中且无豁免说明即打回

### LL-076 同一知识两份清单必漂移，收编单一来源

- 犯过：`scripts/versions/` 两门面各写一份跳过目录清单与版本比较实现，
  已实际漂移——outdated 的 skip 比闸门 `SKIP_DIRS` 少
  `target-wasm`/`dist`/`coverage` 三项；`parse_ver` 不补齐三元组而
  `_semver` 补齐，`1.85` 对 `1.85.0` 判定相反（潜伏误报）
- 根因：同 LL-034（tsdown 双 glue 顺序）——同一事实存两处，改一处漏一处，
  且两份都"看起来对"，无机器对账时漂移静默存活
- 规则：跨脚本共用的常量（目录清单）与算法（版本解析/比较）MUST 收进
  `scripts/versions/lib/` 单一来源（`repository.SKIP_DIRS`、
  `version.parse_version`），门面与后续域收编一律引用，禁止再抄一份
- 复发检测：grep `scripts/` 出现第二份 `SKIP_DIRS`/`skip =` 清单或第二套
  版本解析实现（`semver`/`parse_ver`/`_semver`）即打回；
  `scripts/tests/test_repository.py::test_skip_dirs_cover_build_outputs`
  钉住集合内容
