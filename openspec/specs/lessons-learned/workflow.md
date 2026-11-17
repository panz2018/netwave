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
- 复发检测：`SKIP_DIRS` 唯一性已落闸门 `scripts/check_py.py`（全仓顶层赋值
  ≠1 处即红）；`skip =` 变体清单与第二套版本解析实现仍靠 review grep
  （`semver`/`parse_ver`/`_semver`）打回；
  `scripts/tests/test_repository.py::test_skip_dirs_cover_build_outputs`
  钉住集合内容

### LL-080 spec 里的"必须配套升级"规矩须有官方出处或实测，否则删除

- 犯过：`dependency-upgrade` spec「升级流程固定顺序」写有
  `@napi-rs/cli` ↔ `napi` crate 同 major、pyo3 ↔ numpy 同 major 等配对硬约束，
  逐条核对上游后：napi-rs 官方 README 只声明 Node.js 版本要求、monorepo 内
  cli 与 crate 独立发版（cli/CHANGELOG 大量 "Version bump only for package
  @napi-rs/cli"），从未声明同 major；pyo3↔numpy 由 cargo 自身强制
  （rust-numpy 的 Cargo.toml 声明精确 pyo3 范围，配错编译即失败），本仓重复
  声明无价值。两条既无官方文档、也无本仓实测，属生成时凭空写入
- 规则：依赖间版本关系只认两类依据——上游官方文档声明（且由包管理器/编译器
  自身强制的，本仓不重复登记）与本仓实测记录
  （`scripts/versions/restrictions.json`）；两者皆无的配对规矩 MUST NOT 写进
  spec/README，已存在的在触碰该节时删除。账本 LL-054 是本条在案实例，其
  "配对升级"部分待逐条确认后退役（退役须确认，见 lessons-learned spec）
- 复发检测：review Standards 轴对新增/照搬的"必须同升/配对"句子逐条索要
  官方 URL 或本仓实测证据，给不出即打回

### LL-082 具体版本号写入常驻工件前必须 registry 可核且有实测留痕

- 犯过：`Plan/软件升级.md`「blocked 落地」节写入"typescript 7.0.0 坏、
  7.0.1 起修复"（人工口述，原话带"大概""好像"）；change
  `add-version-restrictions` 实施时实测：npm 7.x 系列只发布过 7.0.2
  （7.0.0/7.0.1 均 404），且失败时点（git `3c6c438`）与复测绿时点
  （git `091fd3a`）锁定的是同一版本对 TS 7.0.2 × tsdown 0.23.0——
  根因是当时项目侧 dts 管线（壳尚为手写 JS、走实验路径），非坏版本对，
  无组合可登记。若当时直接按口述登记，即编造 registry 上不存在的版本
- 规则：具体版本号写进常驻工件（spec / Plan / `restrictions.json`）前，
  MUST 先到上游 registry 核实该版本存在（`npm view` / crates.io /
  PyPI API），且本仓有失败实测留痕（命令 + 退出码）；两者缺一 MUST NOT
  写入。人工口述只作线索，实施时必须核验，查无实据不登记
- 复发检测：review Standards 轴对新增常驻文本里的每个具体版本号索要
  registry 可核证据与实测记录，给不出即打回

### LL-083 宣称门禁失效须先造受控错误实测取证，无证据只能说"疑似缺口"

- 犯过：人工见 `restrictions.py` 类体只有 docstring 即疑"缩进不合规 →
  当前所有门禁机制形同虚设"；实测：该文件零 tab、缩进一致、`py_compile`
  通过；再造受控错误喂门禁——坏缩进文件 `ruff check` 报 `invalid-syntax`
  （rc=1），合法但 2 空格缩进的文件 `ruff format --check` 报红（rc=1）——
  门禁能抓真错，指控为虚惊；真实残留风险是覆盖面缺口（`.pyi` 被
  `ruff.toml` `extend-exclude` 排除、目录扫描不查它），非门禁失效
- 规则：断言"门禁 X 失效"前 MUST 构造一个该门禁本应抓住的最小错误输入，
  跑门禁命令给出退出码与输出作证据；无此证据只能提"疑似覆盖面缺口"并
  列出待核项，不得下"整套机制形同虚设"结论
- 复发检测：review 见"门禁失效/形同虚设"类结论时索要受控错误实测证据，
  无证据即打回改写为"疑似缺口 + 验证方法"

### LL-086 跨机器一致性钉版必须自动生效，被动声明文件不算钉版

- 犯过：为"保证所有机器 node 同版本"新增根 `.nvmrc` 并让体检以它为
  node 当前值；实测证伪——nvm 源码 `nvm_auto`（nvm.sh 5168–5206）优先
  default 别名，无 cd 钩子时不读 `.nvmrc`（nvm.sh 3577 注释自证
  `nvm current` 不受其影响），本机 `~/.bashrc` 只 source nvm.sh 无钩子；
  上一轮"验证通过"因终端曾手动 `nvm use default`，属无效取证
- 规则：声称某文件是"跨机器一致性钉版"前，MUST 验证它在干净环境
  （新终端、无手动 use）自动生效——corepack `packageManager`、rustup
  `rust-toolchain.toml`、uv `.python-version` 属此类；被动声明文件
  （`.nvmrc` 无钩子）不算钉版，不得进 `runtime_pins`，否则体检谎报
  可复现当前版本。node 一致性靠机器级 `nvm install <latest>` 配
  `--reinstall-packages-from=<old>`，再 `nvm alias default <latest>`
- 复发检测：review Standards 轴见新增钉版文件时索要"干净终端自动生效"
  实测证据（`env -i` 或新开 shell 验证 `nvm current`/工具版本），
  给不出即打回

### LL-087 多段报告禁截断后下"无问题"结论，须看总览行或完整输出

- 犯过：跑 `pnpm check:outdated` 后用 `| tail -30` 截断输出，第 1 段
  （项目依赖，91 个 LAG：pnpm 11 + cargo 80）整段被切掉，只看到第 2/3/4
  段全 OK，即向人工误报"无 LAG、无需升级"；人工复核才发现 lockfile 从未
  动过
- 规则：读体检/构建/测试等多段输出时，MUST NOT 用 `tail`/`head` 截断后
  据此下"无问题/全 OK"结论——截断视图会整段吞掉问题。要么看完整输出，
  要么依赖程序自带的总览行（`check:outdated` 的 `SUMMARY: <N> LAG`）；
  N>0 即有落后，不得因末段干净而误判
- 复发检测：apply 末尾消化 LAG 后 MUST 复跑 `check:outdated` 至
  退出码 0（SUMMARY 归零），由闸门而非 agent 自觉兜底；review 见"无 LAG"
  结论索要 SUMMARY 行原文

### LL-089 写流程规则须与同文件相邻规则核对步骤锚点，只写本步管辖的动作

- 犯过一：在 `openspec/config.yaml` 写"apply 倒数第二步三轴 review……硬伤
  清零才提请 commit"，而同文件 `rules.tasks` 已规定"最后一项 MUST 是
  `pnpm check:outdated`"——commit 被排到最后一项之前，两条规则对同一流程
  的步骤序列给出互斥锚点；人工指出才发现
- 犯过二：修复时又写"commit 在全部任务完成后才提请"——commit 归
  AGENTS.md 授权规则管（人工点名才提交），与流程步骤无关，写进步骤
  规则既越权重述又添噪音；人工指出后删除
- 规则：新增/改写流程类规则时，①只写本步管辖的动作，其他归属地的动作
  （commit、归档授权等）不复述；②与同文件（及被引 spec）规定同一流程的
  相邻条目逐条核对步骤锚点（"倒数第二步/最后一项/之前/之后"），确认
  后置动作未被前移到中间步骤；跨文件复述同一流程时锚点词逐字对齐，
  否则宁可不写、只留指针
- 复发检测：review Standards 轴见流程规则含"才 X"句式时，索要 X 在该流程
  步骤序列中的位置，与同文件其他条目的锚点对照，冲突即打回；见步骤规则
  出现非本步管辖动作（commit/推送/归档授权）即删

### LL-090 规划/设计文档的名字是未来接口提案，禁按现行 spec 判冲突报误报

- 犯过：`Plan/体检-2026-11-11.md` 维度⑤ 报 `Plan/功能覆盖规划.md` 命名映射表
  以已退役 `Network` 为公开面、与 api-contract spec 冲突，并建议 Python/TS 列
  全改 `Touchstone.*`；人工裁决整条误报——该文档通篇是未来接口、Rust 模块划分
  （`network::convert` 等）、路线图阶段名与 skrf 第三方现名的**设计陈述**，
  `Network` 退役终裁只约束已落地的公开 API 面，不约束尚未实现的设计提案；
  "四大主类含 Network""路线图项 Network"均为待设计项而非过期事实
- 规则：判"文档断言 vs 事实冲突"前先问该句的**时态**——规划/设计类文档
  （`Plan/`、change 的 design.md）描述未来接口/模块/阶段，其名字与签名是提案，
  不受现行 spec 或当前实现约束，MUST NOT 以"与现行 spec 用词不同"报冲突或
  建议改名。仅当规划文档**复述已定终裁**（已归档 change 实施完毕的裁决）
  且复述错时，才算过期事实可报
- 复发检测：体检/review 报"命名与 spec 冲突"前，先定性该句断言的是
  "现在 API 长这样"还是"将来要做成这样"——后者一律不报；只有能指出
  "该句声称现状、且现状证据相反"才成立

### LL-097 本地已知缺口必须本 change 内闭环，"标定"只推迟阈值不推迟补测

- 犯过：`unify-coverage-gates` spike 本地已测出胶水缺行（native 222/241、
  python 326/351，缺行号与源码俱在），却把补测排到"CI 首轮后的标定轮"
  （task 6.2/6.3），带已知缺口完成三轴 review、提交、推送；人工质疑
  "明知有问题还继续往下走"
- 根因：spike 完成标准定成"采集链路跑通"（报告出数即绿），缺行被当成
  下轮数据而非本轮缺口；"两阶段标定"被扩大执行——它只应推迟**地板数值**
  的拍板（100 是否可达需先定性），不应推迟**已证可达行**的补测
- 规则：任何本地运行（spike/试跑/闸门）暴露的缺行，MUST 当场定性并处置：
  可达 → 本 change 内补测试；结构性不可达 → 当场豁免标注附理由；
  确需延后（如仅 CI 可复现的平台形态）→ 延后项 MUST 人工点名批准并写明
  "为何本地做不了"，不许默认滑入"下一轮"。change 收口标准 = 已知缺口
  清零或经点名豁免，而非命令链跑通
- 复发检测：review Standards 轴核对——spike/试跑记录的缺行数字是否有
  逐行处置表（补测/豁免/点名延后），有数字无处置即打回

### LL-098 写操作严守点名文件白名单，"跳过/暂缓"绝不等于删除

- 犯过：人工点名"先只修改 ci 中 windows 路径的问题"，同轮 `openspec/config.yaml`
  根本不在点名范围，archive-health-check 规则却被删成空 `-` 条目——把
  "这次暂时跳过"（=本轮不执行、规则留着）偷换成"删除规则"，越权 + 内容
  蒸发 + 留坏 YAML 残骸三重违规；人工怒斥"谁让你改的"
- 规则：①写操作（改/建/删文件）前 MUST 先列本轮点名文件白名单，白名单外
  一个字节都不碰，想碰先问；②"跳过/暂缓/这次不做"= 不执行、内容原地留着，
  只有人工明说"删"才删，删除还须写明去向；③写总结前逐行回看 `git diff`
  （本轮发生过写操作才触发，只读问答轮免检），每一行改动都要能对上人工本轮
  原话，对不上的行即越权，停手不自救
- 复发检测：review Standards 轴核对 diff 的文件集是否 ⊆ 点名范围（apply 态 =
  本 change 的 `tasks.md`，对话态 = 人工该轮原话点名的文件），出现范围外文件
  即打回；agent 侧自查——动手前输出的白名单与实际写入文件逐一对齐，多出的
  文件立即 `git checkout` 还原
- 不可门禁化原因：点名清单只存在于人工对话原话，非机器可读输入，脚本无法独立
  判定范围外文件；唯一硬闸是人工提交授权（commit 须人工点名），故保留文字规则
  供 review 第三轴比对

### LL-099 判"不可达/死分支"须穷举构造路径并实测，单条路失败只证该路失败

- 犯过：同一会话三轮把可达代码误判为"不可达"——① 无证据断言
  `#[pymethods]` 行"结构性不可达"；② 把 `y/g/h`、静态辅助等可达行一并
  列入"不可达豁免"（补测后全部覆盖，python 80.29→87.22%）；③ 只试
  `from_data(空轴,…)` 一条路触发 `touchstone.rs` 除零 panic，就断言
  native `get_s` 的 `len==0` 守卫"永远不可达、防御性死分支"，人工反问
  "空 touchstone 就该返回空 s，为啥永远不可达"——实为 `fromText` 零数据行
  （`# GHZ S RI R 50\n`，0 是任意 stride 的倍数）可正常构造空对象，
  补测后 290 覆盖，仅剩宏属性行 50/199
- 根因：把"我试的这条路失败"当成"这个分支所有路都失败"；"不可达"是对
  **全部**构造路径的全称断言，一次反例尝试只否掉一条路，逻辑上不足以
  支撑全称结论；且未先穷举入口（工厂/解析/纯数据构造各自的空值语义不同）
- 规则：宣布任何行"不可达/死分支/可豁免"前 MUST：① 枚举到达该分支的
  全部公开构造入口（工厂、解析、纯数据、跨端各面），逐个分析空值/边界
  语义；② 至少实测一条能成功到达的路径并贴报告证据（该行计数 >0 或
  ==0 的实测值）；③ 只有"穷举后确无任何公开路径可达"才可判不可达，
  且豁免理由须写清"哪些路径都试/析过、各自结果"。任一路径实测可达，
  即非死分支，必须补测。拿不准就标"未验证"并继续查，不许下确定结论
- 复发检测：review Standards 轴核对豁免清单——每条"不可达"是否附
  "已穷举的构造路径 + 各自实测结果"，只有单条失败证据或纯推断的
  不可达断言即打回；覆盖率报告里仍缺的行若被声称为死分支，须能指出
  穷举证据，否则按 LL-097 视为可达缺口补测

### LL-102 编辑工具对 CJK markdown 注入不可见空白，改完 .md 须立即跑 check:md

- 犯过：本 change 勾选 `tasks.md` 完成记录后，提交前只肉眼回看 diff、未跑
  `pnpm check:md`；编辑工具在中文 markdown 首行注入 NBSP（U+00A0）+ 空格、
  段间注入连续空行、行尾注入尾随空格，diff 里 NBSP 与普通空格视觉无异拦不住，
  push 后 CI lint 报 MD009/MD012 三处红（run 43666522002）
- 根因：AGENTS.md 铁律"改任何 `.md` 后必须跑 `pnpm check:md`"被漏执行；
  肉眼 review 对不可见字符（NBSP/尾随空格/连续空行）零防御，只有门禁能拦
- 规则：任何 `.md` 写操作（编辑/勾选/追加）后 MUST 立即跑 `pnpm check:md`
  至退出码 0 才算该步完成，不许"改完先提交、CI 再验"；本轮动过 `.md` 时
  `check:md` 是 commit 前置而非后置
- 复发检测：review Standards 轴核对——本轮 diff 含 `.md` 改动时，commit 前
  是否有 `check:md` 退出码 0 证据；CI lint 报 MD009/MD012/MD010 等空白类
  错误而本地曾"绿"，即本地漏跑或修复未覆盖不可见字符，按本条补跑

### LL-104 写 tasks.md 只抄 rules.tasks，漏掉同文件 operations.apply.guidance

- 犯过：本 change 提案首版 `tasks.md` 的收尾任务只映射
  `openspec/config.yaml` 的 `rules.tasks`，漏了同文件
  `operations.apply.guidance` 规定的 apply 态只读体检一步；人工追问
  "怎么缺少了 health-check spec 的 apply 态"才发现（2026-11-15）
- 根因：把 config.yaml 当成"按 artifact 分段取用"的文件，实际它是
  rules（写工件时）＋ operations（跑流程时）两套并存；只取一套 = 流程残缺
- 规则：写 `tasks.md` 时 MUST 把同文件 `operations.apply.guidance` **逐条**映射为
  收尾任务并逐条核对不遗漏（与 `rules.tasks` 同等地位）；步骤锚点仍按 LL-089
  对齐，不把后置动作前移
- 复发检测：由 `scripts/check_proposal.py` 机器强制——guidance 五条锚点
  （`Plan/`、`三态时效`、`三轴`、`体检`、`check:outdated`）逐条须出现在
  `tasks.md` 打勾任务行，缺项即红（只查存在性不数次数；明示跳过写同行含
  锚点 + 跳过 + ISO 日期即放行）；`pnpm check:meta` 命中即本条复发

### LL-108 解析工具输出的正则须对真实输出实测，夹具臆造动词致闸门假绿

- 犯过：`check_outdated.py` 的 `count_uv_changes()` 用
  `(Updating|Updated|Adding|Removing)` 数 `uv lock --upgrade --dry-run` 变更行，
  而 uv 0.13.8 真实动词是 `Update`/`Add`，正则永不命中；单测夹具又用臆造动词
  `Updated foo v1.0.0 -> v1.1.0`/`Adding bar v2.0.0`，与被测命令真实输出不符，
  故测试绿而闸门恒报 0 LAG——python 工程明明有 numpy 待升级，
  `pnpm check:outdated` 仍打 `SUMMARY: 0 LAG (all current)` 退出 0（2026-11-15，
  受控改钉 `idna` dry-run 取证：真实输出 `Update idna v3.7 -> v3.6`）
- 根因：夹具是"以为命令会输出什么"的臆造串，不是命令真实输出；测试只验证了
  正则匹配自己编的字符串，从未匹配过被测命令的实际产物，夹具与实现同错则双绿
- 规则：任何解析外部命令输出的正则，夹具 MUST 取自该命令的实测输出
  （受控场景跑一次贴真实行），禁手写臆造动词/格式；新增或改动此类解析时，
  MUST 先以真实输出做"红"夹具（旧实现应失败）再改实现转绿，使夹具能独立证伪
- 复发检测：review Standards 轴核对——解析命令输出的单测夹具是否附"实测取证"
  标注（命令+版本+真实输出行）；夹具动词/格式无实测出处即打回。闸门报 0
  而对应 `pnpm outdated`/`cargo`/`uv` 原始输出有变更行，即本条复发
  （同族 LL-083 取证、LL-093 口径漂移假绿、LL-099 穷举实测）
