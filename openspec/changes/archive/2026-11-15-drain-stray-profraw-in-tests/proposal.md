# Proposal

## Why

本地跑覆盖率时，只要 `cargo llvm-cov show-env` 这一段没生效，插桩二进制就会按
LLVM 默认模板把原始计数文件写到进程当前目录——仓库根现存 12 个、`python/` 现存
3 个 `default_*_*.profraw`。这些文件从来不是任何覆盖率报告的输入（报告只读
`target/` 内 cargo-llvm-cov 自己登记的 profraw），所以它们既不影响结果也没人收，
一攒就是几周；更糟的是它们本应是"覆盖率链断了、这一轮报告数字不可信"的响亮信号，
现在却被 `.gitignore` 的 `*.profraw` 静默吞掉。清理必须成为测试自身的一部分：
每次跑测试自动清扫，并且发现散落当场报错，让断链那一轮就红。

## What Changes

- 三个跑插桩代码的测试 harness（根 pytest、`python/` pytest、vitest native）在
  **会话开始与会话结束两处**清扫各自子树（仓库根 / `python/` / `typescript/`）内
  `target/` 以外的 `*.profraw`：先删除、再报错退出，报错文本列出被删文件名与个数
  作为证据；下一轮无残留即自愈，无需人工确认。
- 清扫逻辑在 pytest 侧写成 conftest 内可导入的具名函数 `drain_stray_profraw(root)`，
  由 `scripts/tests/test_drain_profraw.py` 以 `tmp_path` 夹具做红→绿单测（永久回归
  保护）；vitest 侧由 `globalSetup` 引用的模块文件承担同等逻辑。
- 跳过目录复用单一来源 `scripts/versions/lib/repository.py` 的 `SKIP_DIRS`
  （`check_py.py` 规则 3 机器强制全仓只有一处赋值）。
- ci-matrix spec 新增两条 requirement，把"覆盖率中间产物不跨轮残留、散落即报错"
  与"嵌套 Python 工程自带 pytest 配置"写成契约；账本新增四条 LL——`ci.md` 记
  profraw 散落成因与防复发、记 pytest 配置上溯致覆盖率范围漂移，`workflow.md`
  记本 change 提案阶段暴露的"写 tasks.md 漏抄 config.yaml apply guidance"流程失误，
  `docs.md` 记本 change 提交后暴露的"英文区文件误写中文报错文案"。
- `ci.yml`：三个构建插桩代码的 job（rust / python / node）各加两道清理步骤
  （测试前、测试后），与本地钩子同流程同语义；未插桩的 job（wasm、lint、bench）
  不加。步骤体为内联 shell（同现有 `mkdir -p coverage` 这类文件系统准备先例），
  不新建脚本。
- `Plan/闸门重排-2026-11-12.md` 补一行去向：覆盖率采集完整链（show-env→clean→
  build→test→report）随该计划 T1 绑进根聚合测试命令，本 change 不重复造入口。
- 修 `python/` 的 pytest 配置上溯：`python/pyproject.toml` 原本没有
  `[tool.pytest.ini_options]`，pytest 因此上溯采用仓库根配置，而根 `addopts` 里的
  裸 `--cov` 会覆盖命令行传入的 `--cov=netwave`（pytest-cov 把无值 `--cov` 当作
  "测全部"），使 `python/` 的 100% 地板实际测量整个仓库而非本包——实测该地板在
  本 change 之前即为 99.75% 不达标。修法：`python/pyproject.toml` 自带
  `[tool.pytest.ini_options]`（`testpaths`/`addopts`）与 `[tool.coverage]`
  （`source=["netwave"]`、`fail_under=100`），各测各的；`ci.yml` 的 python job 随之
  去掉重复的 `--cov=netwave --cov-fail-under=100`，范围与阈值唯一来源是该配置文件。
- `scripts/check_py.py` 增第 4 条规则防复发：仓库内任何嵌套 `pyproject.toml` 缺
  `[tool.pytest.ini_options]` 即报错；声明了 `[tool.coverage]` 却缺 `run.source` 同样
  报错（地板范围未钉 = 静默漂移）。按 TDD 新建 `scripts/tests/test_check_py.py`。

## Capabilities

### New Capabilities

（无——本 change 不引入新能力域。）

### Modified Capabilities

- `ci-matrix`: 新增 requirement「覆盖率中间产物不跨轮残留」——跑插桩代码的测试
  harness MUST 在会话开始与结束时清除 `target/` 外的 `*.profraw`，发现即先删后报错；
  新增 requirement「嵌套 Python 工程自带 pytest 配置」——嵌套 uv 工程 MUST 自带
  `[tool.pytest.ini_options]` 与钉住 `run.source` 的 `[tool.coverage]`，使各工程覆盖率
  范围互不污染；现有 requirement 的口径与 Scenario 全部不变。

## Impact

- 测试钩子：`scripts/tests/conftest.py`（改）、`python/conftest.py`（新建）、
  `typescript/vitest.native.config.ts`（改，加 `globalSetup`）、
  `typescript/test/global-drain-profraw.ts`（新建）。
- 单测：`scripts/tests/test_drain_profraw.py`（新建）。
- 覆盖率配置：`python/pyproject.toml`（改，新增 pytest 与 coverage 两表）、
  `pyproject.toml`（改，仅补注释说明本表是仓库根 rootdir 锚点）、
  `python/README.md`（改，本地命令口径）。
- 闸门：`scripts/check_py.py`（改，新增 project scoping 规则）、
  `scripts/tests/test_check_py.py`（新建，TDD）。
- 复用：`scripts/versions/lib/repository.py` 的 `SKIP_DIRS`（只读引用，不改）。
- 治理：`openspec/specs/ci-matrix/spec.md`（归档时 sync）、
  `openspec/specs/lessons-learned/ci.md`、`workflow.md` 与 `docs.md` ＋ `INDEX.md`
  （四条 LL）、
  `Plan/闸门重排-2026-11-12.md`（补去向行）、`Plan/` 新增待议笔记。
- CI：`.github/workflows/ci.yml`（rust / python / node 三个 job 各加测试前与
  测试后两道内联清理步骤；wasm / lint / bench 不动）。
- 不受影响：`package.json` 脚本面、`scripts/` 闸门集合（`check_py.py` 新增规则除外）、
  根 `[tool.coverage.run].source` 名单与根 `addopts`、`target/` 内 cargo-llvm-cov
  自有产物、`.coverage` 与 `coverage/*.json` 报告文件、wasm/browser 两个 vitest 配置。
- 受引用铁律：铁律七（覆盖率 100% 硬约束）——本 change 让"覆盖率数字可信"的前置
  条件（采集链完好、测量范围正确）变成可执行闸门，不改动地板数值本身。

## Non-goals

- 不改覆盖率采集链的构造：`show-env` 位置、`cargo llvm-cov report` 参数、各地板
  数值全部不动。本 change 只修两处"闸门量的不是它以为的东西"：profraw 散落被
  `.gitignore` 吞掉、`python/` 覆盖率范围被根配置撑大。
- CI 清理步骤不抽成 `scripts/` 脚本也不进根 `package.json`：它是 CI 环境专属的
  文件系统准备（同现有 `mkdir -p coverage` 内联先例），而 `check_ci.py` 的接线
  闸门只管 `test:*` 命令；抽脚本会把 CI 细节变成第二处真相源。
- 不新建 `scripts/` 独立清理脚本，也不把清理逻辑纳入 `[tool.coverage.run].source`
  的 100% 地板名单——逻辑仅十余行，为它加脚本＋floor 是过度结构。
- 不碰 `target/` 内的 profraw 与 `target/netwave-profraw-list`（归
  `cargo llvm-cov clean` 管），不碰 `.coverage`、`coverage/*.json` 等报告类产物。
- 不提供跳过开关（环境变量等）：自愈式设计下加开关等于给未来留静默通道。
- 不在本 change 内实现根聚合测试命令（`pnpm test` 等），只留去向指针。
- 不给 wasm / browser 两个 vitest 配置挂钩子：二者不产 profraw（wasm 未插桩、
  browser 跑在 Chromium 进程内）。

## Prior art

- `cargo llvm-cov clean --profraw-only`（本机 `cargo llvm-cov clean --help` 实证存在）
  ——官方专删 profraw 的子命令。**偏离理由**：它按 cargo-llvm-cov 自己的清单删，
  show-env 断链时产生的 `default_*` 文件不在清单内（正是本次要清的），且它静默
  成功、不报错，无法承担"断链信号"职责；`--workspace` 还会连带删插桩对象、拖慢
  下一轮构建。
- 仓库内 `scripts/tests/conftest.py` 的 autouse fixture 先例（离线网络守卫）——
  同一"钩子内做全仓性守卫"的既有形态，本次沿用其结构。
- 仓库内 `scripts/versions/lib/repository.py` 的 `SKIP_DIRS`——目录遍历跳过名单的
  单一来源，`scripts/check_py.py` 规则 3（LL-076）已机器强制不得复制第二份。
- 账本 `openspec/specs/lessons-learned/ci.md` LL-091（show-env 泄漏/缺失致本地
  污染）与 LL-101（clean 静默跳过致旧产物污染）——同一"静默失效"家族，本 change
  把其中"文件散落"这一维从散文规则升级为闸门。

## 专家增补

- 断链信号升级为**报错而非警告**：警告靠人读、没人读，`target/` 外出现 profraw
  本身就是采集链未生效的充分证据，`drain_stray_profraw()` 发现即先删后 raise，
  让可疑报告那一轮直接红，而不是被当可信数字用掉后再追溯。
- 加**会话收尾**这一处检查：只在开跑前查会把"本次跑当场断链"推迟一轮才暴露，
  而中间那份报告已被消费；`conftest.py` 的 session fixture teardown 与 vitest
  globalSetup 文件里 `setup` 返回的 teardown 函数各多调一次同一函数，换来当轮即红。
- 报错文案只写当前契约，且按语言约定用英文（代码与 CI 属英文区，见 governance
  spec「元规则 优先级与单一真相源」语言约定；本仓首次落地时误写中文，已改）：
  `profraw outside target/ = the coverage chain did not take effect, so coverage numbers for this run are untrustworthy`；代码注释与报错串内不写 LL 编号与 spec 指针——
  `scripts/check_comments.py` 扫描范围内只留当前契约，编号只落 spec 散文与账本。
- 一次性实证素材：现存 15 个真实散落文件（根 12 ＋ `python/` 3）在钩子落地前保留，
  apply 时以 before/after `ls` 证明钩子真删；`typescript/` 侧无真实样本，手工造一个
  `typescript/zz-drain-proof.profraw` 验证 vitest 钩子当场报错＋删除后即删样本。
