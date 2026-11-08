# Proposal

## Why

`pnpm check:outdated` 目前只在人工点名时全量联网，且四个检查段里只有
`restricted_lines()` 一段消费 `scripts/versions/restrictions.json`——其余段
（包管理器 dry-run、`.python-version`、全局 CLI、直装工具、CI actions）拿
"上游最新版"直接比，已登记的坏组合照样报 LAG，产生"提示升级却升不了"的
假警报。同时缺稳定的日常触发：人工手动跑会忘；做成 CI 门禁破坏"CI 红 =
你这个 PR 弄坏了什么"；做成"每天第一个会话第一条命令"的纪律不可靠——
第一个会话常是 ask 模式没有执行权限，且依赖记性与时间记录。本 change 把
触发挂到 OpenSpec apply 工作流（每次 apply 开始自动体检），配"一切 LAG
预授权 + 实测失败登记回退"，让升级在每次 change 落地时顺带完成，程序
无需时间戳与缓存。

## What Changes

- `check_outdated.py` **全部检查段统一消费 restrictions**：每段报
  latest/target 前过 `pick_unrestricted()`，命中已登记组合即改报"未登记的
  最高可用版 + SKIP 原因"；运行时/工具 pin（`.python-version` →
  `pypi:python`、`rust-toolchain.toml` channel → `cargo:rustc`、CI action
  tag）纳入 peers，使"运行时 × 库"组合真正可命中（例：`pypi:python`
  3.16 与 `pypi:numpy` 2.3.0 同锁时报 SKIP 而非 LAG）。
- **退出码语义调整**：源不可达（重试一次仍失败）= SKIP，不算 FAILED、
  不影响退出码；FAILED 仅保留给"源可达但答案不合契约"或本地探针无法执行
  的真错误。
- **体检不报下限**：MSRV（`rust-version`）、`engines.node`、CI 底线矩阵格
  不是体检目标，MUST NOT 报为 LAG；下限变更由人工发起。
- **apply 末尾触发 + 升级预授权**：`openspec/config.yaml` 双写——
  `operations.apply.guidance` + `rules.tasks`（tasks.md 最后一项 MUST 是
  体检+消化）。apply 全部任务完成后跑 `pnpm check:outdated`；所报一切
  LAG 预授权：agent 直接执行升级 + 全闸门 + 四端对拍，机械适配自主做完，
  上游 bug/不兼容登记回退不阻塞；仅设计级适配、`restrictions.json` 破损、
  流程走不通才停下报告。升级不开新 change，追溯靠 git log +
  `restrictions.json`；提交权不变（升级改动全景表单列一组，等人工点名）。
- **BREAKING**（体检命令自身契约）：探针失败从"必非零退出"改为"重试一次
  后 SKIP 不算失败"；REMOVED「升级分级」（结构性升级 MUST 走 change 的
  约束废除）。

## Capabilities

### New Capabilities

- 无（不新增能力，全部落在既有 `dependency-upgrade` 能力内）。

### Modified Capabilities

- `dependency-upgrade`：「过期体检命令」重写（全段消费 restrictions、
  运行时/工具 pin 参与组合判定、SKIP 与 FAILED 分层、不报下限声明、
  apply 自动触发且仍 MUST NOT 进 CI 或 `pnpm check`）；「版本限制记录
  数据文件」补充运行时/工具 pin 以生态前缀名参与组合的登记写法；
  「运行时大版本升级流程」改实测语义（删支持矩阵调研，留一次改齐
  原子性）；REMOVED「升级分级」；新增「升级执行权限划分」（上限升级
  agent 直接执行不开 change，下限变更人工发起）与「apply 末尾体检与
  升级预授权」。

## Impact

- 代码：`scripts/versions/check_outdated.py`（各段出行为统一过滤 +
  SKIP/FAILED 分层 + 重试一次）、`scripts/versions/lib/repository.py`
  （运行时/工具 pin 提取进 peers）。
- 测试：`scripts/tests/versions/`（覆盖率 100% 门槛由 `check:py` 的
  `--cov-fail-under` 强制，铁律七）。
- 配置：`openspec/config.yaml`（`operations.apply.guidance` 一条 +
  `rules.tasks` 一条，双写保险）。
- 文档：`scripts/versions/README.md`（退出码、登记示例）、`AGENTS.md`
  （apply 体检 LAG 属已授权动作的例外句，附出处）、`Plan/软件升级.md`
  （「过期检查门禁化」节改写为本形态，apply 定案后整节删除）。
- CI：零改动——`ci.yml` 不含 `check:outdated`，维持现状。
- 受影响铁律：铁律二（TDD，先红后绿）、铁律七（覆盖率 100% 硬约束，
  `scripts/versions` 域）；元规则「最小规则原则」（不新增门禁命令、
  不造第二套判定、不加时间戳状态）。

## Non-goals

- 不进 CI、不进 `pnpm check`——「MUST NOT 进 CI」条款维持不变。
- 不做时间戳/缓存/自愈——触发频率由 apply 节奏天然决定，程序不记时间。
- 不做"每天第一个会话第一条命令"纪律——ask 模式无权限、靠记性，已被
  人工判为不可靠。
- 不做 `requires-python` / `engines` 下游元数据预测——兼容性只认实测 +
  `restrictions.json` 登记，不认声明预测。
- 不做 restrictions 过期清理或自动删除——记录只增不删，库升版后组合按
  精确匹配自然失效。
- 不做 cron 定时任务、Dependabot/Renovate 式机器人——定时报错形态已被
  人工否决。
- 不改 `restrictions.json` 的只增不删与具体版本精确匹配语义。
- 下限变更（MSRV、`engines.node`、CI 底线格）不在自动化范围。

## Prior art

- 仓库内现成实现：`scripts/versions/lib/restrictions.py` 的
  `pick_unrestricted()` / `is_restricted()` 组合判定已存在，本 change 只扩
  消费面与 peers 取数，不造第二套判断；`openspec/config.yaml` 的
  `operations.apply.guidance` 机制已存在（apply 时自动注入），触发接线复用
  它而非新造钩子。
- <https://github.com/dependabot/dependabot-core> 与
  <https://docs.renovatebot.com/> ——定时开 PR 形态，因每日 PR churn 与
  "机器人 PR 仍需人点合并"被否。
- <https://endoflife.date/api> ——体检已在用的版本源，维持不变。

## 专家增补

- `scripts/tests/versions/` 补夹具：运行时组合命中/失效正反例、各段
  target 换版、SKIP 不影响退出码、FAILED 仍非零；`check:py` 的
  `--cov-fail-under=100` 门槛同轮保持绿。
- `scripts/versions/README.md` 的 Exit codes 与 Usage 两节同轮改写，
  补 SKIP 语义与 apply 末尾触发，防文档旧事实（LL-034 波及面同步）。
- `AGENTS.md` 硬护栏「动词 = 授权全集」与本预授权存在张力，须加一句
  例外（apply 末尾体检所报 LAG = 已获授权动作，出处 = 本 change），否则
  硬护栏压过 spec 授权，agent 仍会停下来问。
- 接线双写：guidance 是 advisory 文本可被无视，`rules.tasks` 把体检钉进
  每个 change 的 tasks.md 末项（任务清单是 apply 逐项打勾的硬结构），
  两处都钉才稳定。
