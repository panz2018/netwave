# Proposal: add-version-restrictions

## Why

升级依赖时反复遇到两类情况：某个上游版本自身带 bug（装了就用不了），或者两个
上游版本凑在一起才坏（各自单独都没问题，例如 typescript 7.0.0 与 tsdown 的 dts
管线不兼容，见 git `3c6c438`）。现行 spec 把这两件事拆成两个互不相干的机制
（「坏版本降级与 blocked 触发式实施」+「pairs 配对校验」），且规定两者禁止在同一次
change 实施。这个拆分是错的：坏版本本质上就是"某个具体版本组合实测失败"，单包 bug
只是组合里只有一个包的特例，两者共用同一份数据、同一套消费代码，分开落地必然出现
两套解析、两套判断（账本 LL-076：同一知识两份清单必漂移）。

同时，现行 spec「升级流程固定顺序」里写着一批"必须配套升级"的配对规矩
（`@napi-rs/cli` ↔ `napi` crate 同 major、pyo3 ↔ numpy 同 major 等）。逐条核对
上游官方文档后：napi-rs 官方从未声明 cli 与 crate 必须同 major（monorepo 内独立
发版，cli/CHANGELOG 大量 "Version bump only for package @napi-rs/cli"）；
pyo3 ↔ numpy 的关系由 cargo 自身强制（rust-numpy 的 Cargo.toml 声明精确 pyo3
范围，配错编译即失败），本仓重复声明没有价值。这类没有官方文档、也没有本仓实测
支撑的规矩属于凭空生成，留在 spec 里会误导后续升级决策，必须清除。

本 change 把两类知识合并为一份**版本限制记录**：只登记实测失败过的具体版本组合，
供升级体检跳过已知坑，从而在"尽量用最新版"与"不重复踩已知坏版本"之间取得平衡。

## What Changes

- 新增数据文件 `scripts/versions/restrictions.json`：一条记录 = 一句原因 +
  该原因下所有**实测失败**的版本组合清单；每个组合是 1~N 个包各自的**具体版本**
  （包数不限：单包 = 该库自身 bug，多包 = 联动 bug）；包名带生态前缀
  （`npm:` / `cargo:` / `pypi:`）以区分跨生态同名包（如 `numpy` 既是 PyPI 包也是
  Rust crate）。记录只增不删。
- 新增 `scripts/versions/lib/restrictions.py`：纯函数模块，负责读记录、判断
  某版本组合是否已登记、为某包算"与对端当前锁定版本搭配后未登记的最高可用版本"。
- `scripts/versions/check_outdated.py` 消费该模块：体检给出的 target 若与对端当前
  锁定版本凑成已登记组合，改为给出未登记的最高可用版本并标注原因；未命中则照常
  报最新稳定版。
- **删除 `check_outdated.py` "退出码恒为 0" 的设定**：任何错误（网络失败、数据
  文件读不出）都必须报告并非零退出，不得降级为警告隐藏。数据文件格式错误直接
  `raise` 异常中断（错误必须暴露才能改正）；记录里引用的包在仓库中已不存在则跳过
  该条、记录保留（历史遗留，将来该依赖加回来时约束重新生效）。
- 该数据文件**不进** `pnpm check` / CI 闸门：正确性由下游构建与单元测试保证，
  这份记录只服务升级决策，不在版本号上设第二道防线。
- spec `dependency-upgrade`：以「版本限制记录」整条替换「坏版本降级与 blocked
  触发式实施」，删除「blocked 与 pairs 不绑定」Scenario，删除「升级流程固定顺序」
  中无官方依据、无本仓实测的配对散文，并新增流程要求——确认坏版本后同轮收紧承载
  钉版文件的版本要求（**只抬高下界、沿用原有范围写法，禁止新增或删除上界**），
  同轮刷新对应 lockfile。
- `scripts/versions/README.md` 补登记方法（跑哪条命令确认、往哪个文件加什么格式、
  同轮怎么收紧范围）。

## Non-goals

- 不登记任何未经实测的版本：没测过的组合一律视为可试，禁止凭推测写范围或列表。
- 不记录"修复于哪个版本"，也不设 green 记录、待重试标记——未登记即放行，
  有新版本就试，试坏了再登记。
- 不把 `restrictions.json` 接进 `pnpm check` / `pnpm check:meta` / CI 闸门，
  也不新增"声明范围是否覆盖已登记版本"的机器校验。
- 不收紧 `typescript/package.json` 现有版本要求、不生成 `restrictions.json` 的
  数据内容——坏版本清单留待 apply 阶段实测后登记（propose 阶段不携带未实测数据）。
- 不做体检门禁化（每周 cron / 自动开 issue），该项继续单独待拍板
  （暂名 `add-freshness-schedule-gate`），禁止与本 change 绑定。
- 不抬 Python/Node 底线、不改任何数值行为与容差、不动四律的实现。

## Prior art

- 仓库内现成机制：`scripts/versions/lib/rules.py`（四律离线闸门，规则驱动、
  按发现扫描、不读登记表）——本 change 沿用其"按发现覆盖、不硬编码名单"的风格，
  但限制记录是**数据**而非律，故不进闸门。
- 仓库内现成机制：`scripts/versions/lib/version.py`（版本解析与比较的单一来源）、
  `scripts/versions/lib/repository.py`（manifest 发现）、`lib/latest.py`（联网探针）
  ——新模块复用而不另造。
- 上游官方机制：npm caret 范围（`^0.23.0` 即"0.23 线"）、cargo 依赖版本要求
  （rust-numpy 的 Cargo.toml 声明精确 pyo3 范围，配错编译失败）、pnpm
  `peers check`（读 lockfile 校验 peer 声明，见 `pnpm-lock.yaml`
  `peerDependencies` 段）——工具自身的版本要求直接遵守，不在本仓重复登记。
- 上游官方文档：rust-numpy README（<https://github.com/PyO3/rust-numpy>）与
  napi-rs cli README（<https://github.com/napi-rs/napi-rs/tree/main/cli>，只声明
  Node.js 版本要求，未声明 cli 与 crate 同 major）——用于判定哪些配对规矩无依据。
- 本仓实测先例：git `3c6c438`（"tsdown dts x TS7 incompatibility with
  typescript@6 fallback (verified)"）。

## 专家增补

- `scripts/tests/versions/lib/test_restrictions.py` 必须断言"未实测的交叉组合不算
  坏"：给定登记了 `TS 7.0.0 × tsdown 0.23.0` 与 `TS 7.0.1 × tsdown 0.23.1`，
  断言 `TS 7.0.0 × tsdown 0.23.1` 判为放行——组合清单最容易被写错成交叉相乘。
- `scripts/tests/versions/lib/test_restrictions.py` 必须断言格式错误抛异常而非静默
  通过：非法 JSON、缺 `reason`、缺 `combos`、包名缺生态前缀四类输入各断言 `raise`；
  另断言"包名在仓库不存在"是跳过而非报错（两种失败语义相反，不写测试必混）。
- `scripts/versions/lib/restrictions.py` 需 100% 覆盖（铁律七，`check:py` 的
  `--cov-fail-under=100` 实测口径为 `--cov=scripts/versions`），故判定逻辑必须是
  不联网的纯函数，网络调用留在 `check_outdated.py`。
- `scripts/versions/README.md` 把"包名必须带生态前缀"与"只写实测版本、禁写范围"
  两条并列写成硬规矩——这两条最容易被后来者凭直觉写错。
- `scripts/check_ci.py` 若对 `check:outdated` 出现在 CI 有断言，需核对措辞随
  "退出码不再恒 0"一并更新，避免闸门与 spec 说法不一。

## 受影响铁律

- 铁律七（覆盖率 100% 硬约束）：新增 `scripts/versions/lib/restrictions.py` 及其
  测试须满足 `check:py` 的覆盖率口径。
- 元规则 优先级与单一真相源 / 文档语言约定：`restrictions.json` 是坏版本事实的
  唯一载体，`Plan/软件升级.md` 对应章节同轮删除；spec 与 README 不复制具体版本号
  （承载版本的钉版文件本身才是真相源）。
