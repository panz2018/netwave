# Design

## Context

`check_outdated.py` 现为四段纯联网报告：main 顺序跑 dry-run 命令、
`.python-version` 比对、`restricted_lines()`、CLI/直装工具/actions 探针，
每段独立 try/except 收集 failures，退出码 = 有无 failures。restrictions
判定只在 `restricted_lines()` 一段生效，且 `locked_versions()` 只认
lockfile（pnpm/Cargo/uv），运行时钉版不在其列，故 `pypi:python` 类组合
永不命中。触发靠人工点名，无稳定节奏。动机与人工裁决见 `proposal.md` —
Why；行为契约见本 change `specs/dependency-upgrade/spec.md`。

约束：`scripts/versions` 域受 `check:py` 的 `--cov-fail-under=100`
（铁律七）；单测离线（`scripts/tests/conftest.py` autouse 网络守卫）；
`lib/restrictions.py` 是纯函数层（无网络无子进程），判定逻辑不得复制。

## Goals / Non-Goals

**Goals:**

- restrictions 过滤下沉为各段共用的"出行为前过一道"步骤，peers 扩到
  运行时/工具钉版。
- 触发接线落在 `openspec/config.yaml` 的 apply guidance，零新代码、零新
  状态文件。
- 退出码语义迁移不破坏现有单测的断言结构（FAILED 集合仍在）。

**Non-Goals:**

- 不改 `lib/restrictions.py` 的判定语义（精确匹配、只增不删、异常契约）。
- 不加时间戳/缓存/自愈——apply 节奏即触发节奏，程序保持无状态。
- 不改 `check:outdated` 的四段结构与探针集。

## Decisions

### D1 触发 = apply 末尾，guidance + rules.tasks 双写，不做每日戳

`openspec/config.yaml` 双写：`operations.apply.guidance` 加一条 +
`rules.tasks` 加一条（tasks.md 最后一项 MUST 是体检+消化）。apply 全部
任务完成后跑 `pnpm check:outdated`，所报 LAG 按预授权消化——放末尾使
升级不干扰本 change 主任务，红也不阻塞已完成工作。guidance 是 advisory
可被无视，rules.tasks 钉进任务清单硬结构，两处都钉才稳定。备选一：每日戳
加每日纪律——否：第一个会话常是 ask 模式无执行权限，纪律靠记性不可靠，
且时间戳/缓存是额外状态面（本 change 曾含此设计，人工裁决推翻）。备选二：
apply 开头——否：开头跑完若升级红，回退动作混在 change 任务中间，归属
不清。

### D2 peers 扩展：`runtime_pins(root)` 进 `lib/repository.py`

新增 `runtime_pins(root) -> dict[str, str]`：`.python-version` →
`pypi:python`（值取 minor，与登记粒度一致）、`rust-toolchain.toml`
channel → `cargo:rustc`、CI action `uses:` tag → `github:<repo>`（复用
`action_refs()`）。`restricted_lines()` 与新增的"全段过滤"共用
`locked_versions ∪ runtime_pins` 作为 peers。备选：把钉版写进 lockfile
解析——否，钉版不在 lockfile 里，伪造数据源违反"钉版文件即真相源"。

### D3 全段过滤 = 出行为统一走 `target_line()`

facade 新增小函数 `target_line(source, name, installed, latest)`：先
`pick_unrestricted(name, candidates, peers, restrictions)`，命中则输出
target 换版 + `SKIP <reason>`，未命中原样输出；各段把"直接 print 比较行"
改为调用它。candidates 拿不到时（如 GitHub release 只有单值）退化为
"latest 单候选过 `is_restricted`"。备选：每段各写过滤——即现状的反面，
拒绝；判定唯一入口仍是 `lib/restrictions.py`。

### D4 不设档位标记：一切 LAG 预授权

体检报出的 LAG 即 agent 工作清单，全部直接执行；下限（MSRV、
`engines.node`、CI 底线格）不在体检探针范围，无需输出层区分。备选：
`routine`/`structural` 两档标记——否：代码兼容性由闸门验证，agent 试了
就知道，预判档位只制造"报了就升不了"的新摩擦；下限本就不在体检范围，
无需第二套分级。

### D5 断网重试一次即 SKIP

每源失败重试 1 次（间隔不睡眠，立即重试），仍失败 → 该源行 SKIP、不计
FAILED。SKIP 行显式点名源名，agent 汇报时转述，长期断网由人从汇报里看出。
备选：多次退避重试——体检是顺跑工具不是基础设施，一次重试覆盖"瞬时抽风"，
更多重试只拉长断网时的等待，拒绝。

### D6 停的边界：机械适配自主，设计级适配与破损才停

既定升级流程内的动作全部自主：刷新、机械适配（改名/换参数/换调用）、
全闸门+四端对拍、登记回退。三类例外停下报告：适配触及公开 API 或需
设计决策（硬护栏：公开 API 变更须人拍板；可先降级保绿）；
`restrictions.json` 破损（判定基准失真，先修再走）；升级流程本身无法
推进。备选：一切适配自主——否，"升级不报告"覆盖的是流水线例行环节，
不是给设计决策发空白授权。提交权不变：预授权授"执行+验证"，不含
commit；升级改动在全景表单列一组（`chore(deps): 体检刷新 <日期>`），
等人工点名。

### D7 预授权与硬护栏的关系：AGENTS.md 加例外句

AGENTS.md「动词 = 授权全集」规定未点名动作禁止执行；本 change 的预授权
若不与硬护栏对接，护栏压过 spec，agent 仍会停下来问。落地 = AGENTS.md
加一句例外："apply 体检所报 LAG 的升级 = 已获授权动作（出处：
dependency-upgrade spec 「apply 末尾体检与升级预授权」）"。备选：只改
spec 不改 AGENTS.md——否，硬护栏凌驾其余条目，例外不写进硬护栏所在文件
等于没写。

## Risks / Trade-offs

- [apply 频率低于每日，升级节奏变慢；apply 中断则升级顺延] → 接受：
  人工裁决"稳定触发优先"——本仓 change 频繁，实际接近每日；无 change
  或任务未跑完的日子不体检，本就是 apply 触发形态的固有代价。
- [升级后闸门当天跑两遍] → 接受：change 任务收尾一遍、升级验收一遍，
  lockfile/钉版变了上一遍作废，两遍是"升级必须带自己的验收"的固有成本。
- [dry-run 命令输出解析复杂，过滤改造面大] → 缓解：dry-run 段维持原样
  透传 + 仅对 restrictions 点名包追加 target 行（现状 `restricted_lines`
  模式的推广），不重写三家命令的输出解析。
- [预授权下 agent 自动升级出错] → 缓解：全闸门 + 四端对拍是硬验收，红
  必回退；git 可逐笔 revert；下限不在授权面内。
- [peers 扩到运行时后，登记组合命中面变大，误登记影响变广] → 缓解：
  登记仍须实测证据（契约不变）；`pick_unrestricted` 只降 target 不报错，
  最坏情况是少提示一次，下次 apply 对端版本变化自愈。

## Migration Plan

1. 先改 `lib/repository.py` + 单测（红→绿），再改 facade；无数据迁移，
   程序保持无状态。
2. `openspec/config.yaml` guidance 与 `AGENTS.md` 例外句随本 change 归档
   生效；回滚 = revert 本 change，无残留状态。
