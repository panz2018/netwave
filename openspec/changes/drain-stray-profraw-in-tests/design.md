# Design

## Context

见 `proposal.md` — Why。此处只记约束现状：

- profraw 落点由 `LLVM_PROFILE_FILE` 决定；`cargo llvm-cov show-env` 把它指到
  `target/llvm-cov/`（模板 `netwave-%p-%18m.profraw`，本机实证），env 缺失时 LLVM
  退回默认模板 `default_%m_%p.profraw` 并写在**进程 cwd**——这就是根目录与
  `python/` 下 15 个 `default_*` 文件的来源。
- `cargo llvm-cov report` 只消费 `target/` 内它自己登记的 profraw，`target/` 外的
  profraw 从来不是任何报告的输入 → 删除零风险。
- `cargo llvm-cov clean --profraw-only` 存在（本机 `--help` 实证），但按自有清单删，
  且静默成功。
- 目录遍历跳过名单已有单一来源 `scripts/versions/lib/repository.py` 的 `SKIP_DIRS`
  （`target`、`target-wasm`、`node_modules`、`.venv`、`.git`、`dist`、`coverage`），
  `scripts/check_py.py` 的 `skip_dirs_defs` 机器强制全仓只有一处顶层赋值。
- vitest 侧实证（`typescript/node_modules/vitest/dist/chunks/index.Di8au7q4.js`）：
  `globalSetup?: string | string[]`（只接受文件路径，不接受内联函数，L3907）；
  globalSetup 文件须导出 `default`/`setup`，`setup` 的返回值若为函数则登记为
  teardown，`_teardownGlobalSetup()` 在测试结束时 `await` 它（L6601-6614）。
- `typescript/tsconfig.json` 的 `include` 含 `test/**/*.ts` 与 `*.ts`，且
  `checkJs`/`strict` 开启——新建的 vitest 钩子文件受 `pnpm -C typescript typecheck`
  约束；`biome.jsonc` 的 includes 覆盖 `typescript/` 全目录。
- `python/` 目前**没有** conftest.py，pytest 靠 `python/` 为 rootdir 自动发现。

## Goals / Non-Goals

**Goals:**

- 三个插桩 harness 各自在会话首尾清扫本树，散落即先删后非零退出。
- pytest 侧逻辑可单测（红→绿），vitest 侧靠一次性实证。
- 名单复用单一来源，不新增第二份 `SKIP_DIRS`。

**Non-Goals:**

- 设计级边界：不改覆盖率采集链本身（show-env 位置、report 参数、地板），
  只增加"链断时留下可执行信号"这一层；采集链的聚合入口归 `闸门重排` T1。
- 不追求跨 harness 共享一份实现（见「各 harness 内联等价逻辑，不抽公共模块」）。

## Decisions

### D1 各 harness 内联等价逻辑，不抽公共模块

三处各写十余行遍历删除。备选：抽 `scripts/clean_stray_profraw.py` 供三方调用。
否决理由：① 进 `[tool.coverage.run].source` 就得背 100% 地板＋单测；② vitest 要
`execFileSync("python3", ...)`，给 JS 测试引入 Python 运行时依赖，直接违反
workspace-layout spec「主 CI 零 Python 依赖」requirement；③ 逻辑仅"遍历＋按后缀删"，
抽象收益低于成本。跨语言无法共享是物理限制，不是选择。

### D2 pytest 侧：conftest 内具名函数 ＋ session fixture 首尾各调一次

`scripts/tests/conftest.py` 新增 `drain_stray_profraw(root: Path) -> list[Path]`
（返回被删文件，相对 root 的路径），并新增 autouse session fixture：yield 前调一次
（清上轮残留）、yield 后调一次（清本轮当场断链），任一次有返回即写 stderr 并
`raise`。`python/conftest.py`（新建）内联同名等价实现——两个 pytest 工程是独立
rootdir，跨工程 import 需把 `scripts/versions` 加进 `python/` 的 pythonpath，
为十余行逻辑污染发布工程的测试配置不值；`SKIP_DIRS` 则**必须** import
（`check_py.py` 机器强制）。根 `pyproject.toml` 的 pytest `pythonpath` 已含
`scripts/versions`，故 `scripts/tests/conftest.py` 可直接写
`from lib.repository import SKIP_DIRS`；`python/conftest.py` 需自带 `sys.path`
引导（同 `check_py.py` 先例：先 `sys.path.insert` 再 import，均置于文件顶部）。

### D3 vitest 侧：`globalSetup` 文件导出 setup 并返回 teardown

新建 `typescript/test/global-drain-profraw.ts`，`export async function setup()`
清扫并返回 teardown 函数完成收尾清扫；`vitest.native.config.ts` 加
`globalSetup: "./test/global-drain-profraw.ts"`。跳过名单在此文件里以字面量写出
（TS 无法 import Python 常量）——`check_py.py` 只扫 `*.py`，不构成第二份
`SKIP_DIRS` 赋值。名单取 `repository.py` 七项中在 `typescript/` 子树内实际存在的
五项（`target`、`target-wasm`、`node_modules`、`dist`、`coverage`；该子树无
`.venv`、`.git`），两表差集恒空由三 harness 对照任务实证并留痕。
teardown 内**显式设 `process.exitCode = 1`** 并写 stderr，不依赖"teardown 抛错
是否冒泡"这一未实证的内部行为（vitest 源码显示 `_teardownGlobalSetup` 的 await
在 close 路径上，抛错语义随版本而异）。

### D4 报错形态：先删、后写证据、再失败

顺序固定为"删除 → 打印 → 非零退出"，保证报错即自愈：报错文本含被删文件名与个数，
人无需再手动清理。备选"报错不删"否决——那会把清理重新推回人工，正是本次要消灭的。
报错文案只写当前契约（散落 = 采集链未生效 = 本轮覆盖率数字不可信），不写 LL 编号
与 spec 指针（`scripts/check_comments.py` 扫描范围内只留当前契约）。

### D5 扫描范围 = 各自子树，跳过名单取单一来源

本地钩子按子树扫：根 conftest 扫仓库根、`python/conftest.py` 扫 `python/`、
vitest 钩子扫 `typescript/`。`rglob("*.profraw")` ＋ 任一父目录命中 `SKIP_DIRS`
即跳过；`target` 与 `target-wasm` 已在名单内，天然满足"不碰 target 内产物"。
本地不做全仓扫：谁产生谁清理，边界清楚且避免每次 pytest 全仓遍历
（CI 侧例外，见「CI 侧：三个插桩 job 各加测试前与测试后两道内联清理步骤」）。

### D6 CI 侧：三个插桩 job 各加测试前与测试后两道内联清理步骤

本地按子树扫（谁产生谁清理），CI 按全仓扫（job 工作目录就是仓根，一次扫完更简单，
且 CI 上不存在误删其他子树活跃数据的风险）。步骤体为内联 shell，不新建脚本、
不进根 `package.json`：它是 CI 环境专属的文件系统准备，同现有 `mkdir -p coverage`
内联先例；`check_ci.py` 的接线闸门只管 `test:*` 命令，不会因此项要求报缺接线。

硬约束（顺序）：测试后的清理 MUST 排在 `cargo llvm-cov report` 与
`coverage_gate.py` **之后**。理由：report 读 `target/` 内 profraw，清理只删
`target/` 外，本身不冲突；但若清理步骤插在测试与 report 之间，一旦某轮
show-env 断链使 profraw 落在 `target/` 外，report 会先被跳过而拿不到任何计数，
报错信号退化为"报告为空"而非"链断"。排在阅卷之后，两个信号各自完整。

未插桩的 job（wasm、lint、bench）不加此步骤：不产 profraw，加了是噪音。

### D7 治理落点：ci-matrix spec ＋ 账本三条 LL，不新增能力域

备选：新开 `coverage-hygiene` 能力。否决——ci-matrix 已承载"覆盖率采集与地板"
全部契约（`覆盖率门槛生效（铁律七）`、`覆盖率报告命名与留存`），本条是同一主题的
前置条件，拆新域会稀释路由。delta 用 ADDED（现存 requirement 全部不动，
无 MODIFIED，避开 strict 校验的整块复制义务）。

账本三条 LL 的 scope 归属：profraw 散落属 CI/覆盖率工具链坑 → `ci.md`；
"写 tasks.md 漏抄同文件 apply guidance"属流程失误 → `workflow.md`（与 LL-089
同族：都是 config.yaml 流程规则执行不完整）；pytest 配置上溯致覆盖率范围漂移
→ `ci.md`（与 LL-093/LL-094 同族：闸门量错东西）。

### D8 `python/` 自带 pytest 与 coverage 配置，阻断上溯

实证（本机，逐条）：

- pytest 只把含 `[tool.pytest.ini_options]` 的 `pyproject.toml` 当配置文件，否则
  继续上溯（`_pytest/config/findpaths.py`）；`python/pyproject.toml` 无该表，故
  `cd python && uv run pytest` 的 rootdir 是仓库根、configfile 是根
  `pyproject.toml`（pytest 头部输出实证）。
- pytest-cov `_prepare_cov_source`（`pytest_cov/plugin.py`）：参数中出现一个无值
  `--cov` 即把 source 置为 `None`（测全部），因此根 `addopts` 的裸 `--cov` 赢过
  CI 命令行里的 `--cov=netwave`。
- 后果实测：CI 同款命令在**移除本 change 新增 conftest** 的情况下也只有
  401 语句缺 1 行 = 99.75%（缺行 `python/tests/test_frequency_unit.py:32`，
  `except` 后的防御 `raise`），即 python job 自地板 0→100（`053b86f`）起就应红；
  加上本 change 的 conftest 后降到 87%（conftest 自身＋其 import 的
  `scripts/versions/lib/repository.py` 一并入测量）。
- 反向实证：把范围收到 `netwave` 包后 `7 语句 100%`、退出码 0，旧 99.75% 一并消失
  （`tests/` 不再入测量，那行不可达 `raise` 不再计数）。

决策：`python/pyproject.toml` 加三张表——`[tool.pytest.ini_options]`
（`testpaths=["tests"]`、`addopts=["--cov","--cov-report=term"]`）、
`[tool.coverage.run] source=["netwave"]`、`[tool.coverage.report] fail_under=100`，
与根 `pyproject.toml` 同构（各工程各声明自己的范围与地板）。`ci.yml` 的 python job
随之简化为 `uv run pytest`，让配置文件成为范围与阈值的唯一来源（根配置注释立的
规矩：scope 与 floor 不在 `package.json`/`ci.yml` 重复）。

备选与否决：

- 只加 `[tool.coverage]` 不加 pytest 表 → 无效：rootdir 仍是仓库根，裸 `--cov` 仍
  来自根 `addopts`。
- 在 `addopts` 里补 `--cov-config=pyproject.toml` → 不需要：coverage 会从当前目录
  自动搜索配置文件（`.coveragerc` → `pyproject.toml` 的 `[tool.coverage]`），根侧
  `fail_under=100` 在无 `--cov-config` 的情况下生效即为证据；多传一个参数反而多
  一个可漏点。
- 排除 `conftest.py`/`tests/` 的 omit 写法 → 只治症状：上溯仍在，下一个文件加入
  又漂；且把测试文件排除出测量本身口径可疑。

防复发落闸门（见 `scripts/check_py.py` 第 4 条规则）：嵌套 `pyproject.toml` 缺
`[tool.pytest.ini_options]` 即报错，声明 `[tool.coverage]` 却缺 `run.source` 同样
报错——把"配置写错但不生效"这类静默态变成机器可判。

## Risks / Trade-offs

- [同一份逻辑存在三处，改一处漏两处] → tasks 里有一条"三处行为对照"验证：
  同一伪造文件分别放进三棵子树，三个 harness 各跑一次，断言三者都报错并删除；
  pytest 侧另有 `tmp_path` 单测锁语义。
- [开跑前清扫误删本轮正在写的 profraw] → 不会：插桩进程在测试**期间**写文件，
  清扫发生在会话开始（写之前）与会话结束（进程已退出、文件已 flush）；
  且 `report` 只读 `target/` 内产物，`target/` 外删除不影响本轮阅卷。
- [CI 上多跑一次遍历，拖慢闸门] → 遍历跳过全部大目录（`target`、`node_modules`、
  `.venv`），命中集在健康工作区恒为空，成本为目录 stat 级，实测记录进 tasks。
- [CI 清理步骤误删本轮报告输入] → 步骤只删 `target/` 外（`find` 剪枝
  `target`/`target-wasm`），且测试后那道 MUST 排在 report 与 gate 之后（见 CI 侧
  决策的顺序硬约束）；tasks 里有一条断言：插桩 job 的清理步骤在 ci.yml 中的行号
  晚于同 job 的 `report` 与 `coverage_gate.py`。
- [teardown 抛错语义随 vitest 版本变化] → D3 用显式 `process.exitCode = 1`，
  不依赖抛错冒泡；vitest 升级后由 tasks 的实证步骤复验。
- [`python/conftest.py` 的 `sys.path` 引导与 `python/` 自身包名冲突] → 引导只加
  `scripts/versions` 一个目录（`lib` 与两个闸门模块名不与 `netwave` 包重名），
  `netwave` 包解析不受影响；apply 时以 `python -c "import netwave"` 复验。
- [现存 15 个真实残留被一次性实证消耗，将来无真实样本] → 单测用 `tmp_path`
  伪造，永久回归不依赖真实样本；真实样本仅用于证明"钩子接进了 harness"。
- [新闸门误报第三方/未来工程] → 判据只看仓库内 `pyproject.toml` 的两处存在性，
  跳过 `SKIP_DIRS`，仓库根自身豁免（它是锚点不是受害者）；新增工程若确实不需要
  覆盖率，不写 `[tool.coverage]` 即不受第二条约束。

## Migration Plan

1. 先落 pytest 侧（函数＋单测红→绿），再落 `python/conftest.py`，最后落 vitest 侧。
2. 一次性实证：用现存 15 个真实文件做 before/after `ls`，`typescript/` 侧临时造
   `zz-drain-proof.profraw` 验证后删除样本。
3. 回滚：三处钩子各自独立可 revert（两个 conftest ＋ 一个 config 行 ＋ 一个钩子
   文件），无数据迁移、无产物依赖，revert 即回到现状。

## Open Questions

（无——命名、范围、报错形态、治理去向均已在提案与 spec 中定死。）
