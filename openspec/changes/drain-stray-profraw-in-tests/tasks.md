# Tasks

## 1. pytest 根侧：可单测的清扫函数（red 先于 green）

- [x] 1.1 抢在钩子落地前留存真实残留快照：把根与 `python/` 下 15 个
      `default_*_*.profraw` 的逐行清单（`ls *.profraw python/*.profraw`）、
      `target/` 内 profraw 与清单文件的逐行清单，一并贴进本文件完成记录作
      before 基线——钩子一旦落地，首次 pytest 就会把真实文件删掉，事后无从取证。
      验证：本文件完成记录含两组逐行文件名清单，数量 15 ＋ target 内实际数。
- [x] 1.2 red：新建 `scripts/tests/test_drain_profraw.py`，用 `tmp_path` 造夹具
      （`tmp/stray.profraw`、`tmp/nested/deep.profraw`、`tmp/target/inside.profraw`、
      `tmp/node_modules/pkg/x.profraw`、`tmp/keep.txt`），断言
      `from conftest import drain_stray_profraw` 可导入、返回相对 root 的被删路径
      集合恰为两个散落文件、`target/` 与 `node_modules/` 内文件与 `keep.txt` 原样
      保留、无散落时返回空列表。验证：`uv run pytest scripts/tests -k drain_profraw`
      失败（`ImportError: cannot import name 'drain_stray_profraw'`），退出码非 0。
- [x] 1.3 green：在 `scripts/tests/conftest.py` 实现
      `drain_stray_profraw(root: Path) -> list[Path]`——`root.rglob("*.profraw")`，
      任一相对路径段命中 `from lib.repository import SKIP_DIRS` 即跳过，其余
      `unlink()` 并收集相对路径后排序返回。验证：1.2 命令转绿（4 passed），
      `python3 scripts/check_py.py` 仍绿（未新增第二处 `SKIP_DIRS` 赋值）。
- [x] 1.4 在 `scripts/tests/conftest.py` 加 autouse session fixture
      `drain_stray_profraw_session`：yield 前调 `drain_stray_profraw(ROOT)`、
      yield 后再调一次，任一次返回非空即把英文报错（含 `untrustworthy` 字样）＋
      被删文件名与个数写 stderr 并 `raise`。
      验证：首次 `uv run pytest scripts/tests -k offline_guard` 即因 1.1 记录的
      根目录真实残留报错（退出码非 0、stderr 列出文件名与 `untrustworthy` 字样、
      `ls *.profraw` 为空 = 真实样本实证）；再 `touch` 一个
      `zz-drain-proof.profraw` 复跑仍报错并删除；第三次复跑退出码 0（自愈）。

## 2. python 侧：独立 rootdir 的等价钩子与配置隔离

- [x] 2.1 新建 `python/conftest.py`：内联 `drain_stray_profraw(root)` 等价实现
      （见 design「pytest 侧：conftest 内具名函数 ＋ session fixture 首尾各调一次」），
      文件顶部用 `sys.path.insert` 引导 `scripts/versions` 以
      `from lib.repository import SKIP_DIRS`（同 `scripts/check_py.py` 先例），
      加同语义的 autouse session fixture，扫描根 = `Path(__file__).parent`。
      验证：`touch /config/GitHub/netwave/python/zz-drain-proof.profraw` 后
      `cd python && uv run pytest -q` 退出码非 0、报错含该文件名、文件消失；
      复跑退出码 0；`cd python && uv run python -c "import netwave"` 仍成功
      （sys.path 引导未遮蔽发布包）。
- [x] 2.2 确认 `python/` 侧清扫不影响 maturin 覆盖率链：按 ci.yml python job 的
      单 step 链（`show-env` → `clean --workspace` → `maturin develop` → `pytest` →
      `report`）在 `bash -c` 子 shell 内跑通。验证：命令退出码 0、
      `coverage/coverage-python.json` 生成且
      `python3 scripts/coverage_gate.py coverage/coverage-python.json 100` 绿、
      跑完 `git status --porcelain | grep profraw` 无输出。
- [x] 2.3 阻断 pytest 配置上溯（apply 中发现的既有缺陷，见 design
      「`python/` 自带 pytest 与 coverage 配置，阻断上溯」）：`python/pyproject.toml`
      新增 `[tool.pytest.ini_options]`（`testpaths=["tests"]`、
      `addopts=["--cov","--cov-report=term"]`）、`[tool.coverage.run] source=["netwave"]`、
      `[tool.coverage.report] fail_under=100`。验证：`cd python && uv run pytest` 退出码 0、
      收集 67 项、覆盖率表只含 `netwave/__init__.py` 与 `netwave/constants.py`
      （不含 `tests/`、`conftest.py`、`scripts/`）、报 `Total coverage: 100.00%`。
- [x] 2.4 `ci.yml` python job 去掉与配置文件重复的覆盖率参数：
      `uv run pytest --cov=netwave --cov-fail-under=100` → `uv run pytest`，范围与地板
      唯一来源是 `python/pyproject.toml`。验证：`grep -rn "cov-fail-under\|--cov=" .github/workflows/ci.yml` 无输出；`python3 scripts/check_ci.py` 绿。
- [x] 2.5 根 `pyproject.toml` 的 `[tool.pytest.ini_options]` 上方补注释：本表同时
      是仓库根 rootdir 锚点，嵌套 uv 工程 MUST 自带同名表阻断上溯（把成因写在泄漏源
      头上）。验证：`addopts`、`testpaths`、`pythonpath`、`[tool.coverage]` 数值未变
      （diff 仅新增注释行）。
- [x] 2.6 防复发闸门（TDD）：先新建 `scripts/tests/test_check_py.py` 写 red（嵌套
      工程缺 pytest 表 → 报错；仓库根自身豁免；有 pytest 表 → 通过；有
      `[tool.coverage]` 却缺 `run.source` → 报错；真实仓通过），再在
      `scripts/check_py.py` 实现 `check_project_scoping(root)` 并接入 `main` 与文档头。
      验证：red 轮 5 failed（`AttributeError`）→ green 轮 5 passed；
      `python3 scripts/check_py.py` 绿；受控取证：造 `zz-scope-probe/pyproject.toml`
      （无 pytest 表）→ 闸门退出码 1 并指名该文件，删除后转绿。
- [x] 2.7 `python/README.md` 同步本地命令口径：`uv run pytest` 即含覆盖率与地板，
      范围与阈值来自 `pyproject.toml`，并说明 `[tool.pytest.ini_options]` 的作用是阻断
      上溯。验证：README 不再出现 `--cov=netwave --cov-fail-under=100`，`pnpm check:md` 绿。

## 3. vitest native 侧：globalSetup 钩子

- [x] 3.1 新建 `typescript/test/global-drain-profraw.ts`：导出 `setup` 异步函数，
      扫描 `typescript/` 子树删 `*.profraw`（跳过名单按 design 的扫描范围决策取
      `target`/`target-wasm`/`node_modules`/`dist`/`coverage` 字面量，TS 侧无法
      import Python 常量），有删除则写 stderr 证据并置 `process.exitCode = 1`，
      返回同语义的 teardown 闭包。验证：`pnpm -C typescript typecheck` 绿
      （strict/checkJs 下无类型错）、`pnpm check:ts` 绿。
- [x] 3.2 在 `typescript/vitest.native.config.ts` 的 `test` 段加
      `globalSetup: "./test/global-drain-profraw.ts"`。验证：
      `touch /config/GitHub/netwave/typescript/zz-drain-proof.profraw` 后
      `pnpm -C typescript test:native` 退出码非 0 且 stderr 含该文件名，文件已从
      磁盘消失；复跑退出码 0（自愈）；`pnpm -C typescript test:native --coverage`
      在无散落时仍达 lines/branches 100 阈值。

## 4. 三 harness 行为对照与一次性实证

- [x] 4.1 三处行为对照（design 风险项"改一处漏两处"的防线）：伪造文件
      `zz-drain-proof.profraw` **逐树单独放**（根 conftest 扫仓库根子树，会连带删掉
      `python/`、`typescript/` 里的同名文件，三树同放则后两个 harness 无样本可删），
      每放一个跑对应 harness：根→`uv run pytest scripts/tests -k offline_guard`、
      `python/`→`cd python && uv run pytest -q`、`typescript/`→
      `pnpm -C typescript test:native`。断言三者均退出码非 0、各自报错列出文件名、
      跑完该树无残留。验证：三条命令退出码均非 0，且 `find` 按名
      `zz-drain-proof.profraw` 搜索（排除 `target`/`node_modules`/`.venv`）
      无输出；三树各自复跑对应命令均退出码 0。
- [x] 4.2 真实残留清理后的收尾核对：对照 1.1 的 before 基线，确认根与 `python/`
      的 15 个 `default_*_*.profraw` 已全部消失（`ls *.profraw python/*.profraw`
      报 `No such file`），把 after 输出贴进本文件完成记录与 1.1 配对。
      验证：after 清单为空、`target/` 内 profraw 与 `target/netwave-profraw-list`
      数量与 1.1 基线一致（未被误删）、`git status --porcelain` 无未跟踪/未忽略残留。
- [x] 4.3 跨绑定回归不受影响：跑 `pnpm check:cross`（本 change 不触碰数值路径，
      此条为"功能只增不减"的回归证据）。验证：退出码 0，四端 dump 对拍无差异。
- [x] 4.4 CI 侧口径确认：`git diff` 证明 `.github/workflows/ci.yml` 的改动**只**
      新增清理步骤（无其他语义改动），`python3 scripts/check_ci.py` 绿（未新增需
      接线的 `test:*` 脚本）。验证：`git diff --name-only` 含 `ci.yml` 且 diff 行
      仅为新增的清理步骤；闸门退出码 0。

## 5. CI 侧：三个插桩 job 各加测试前与测试后清理步骤

- [x] 5.1 在 `.github/workflows/ci.yml` 的 rust、python、node 三个 job 各加两道
      内联 shell 清理步骤（步骤体同语义：`find` 剪枝 `target`/`target-wasm`/
      `node_modules`/`.venv`/`dist`/`coverage` 后找 `*.profraw`，命中则打印文件名
      与个数并以非零码退出，否则静默通过）：一道在测试步骤之前，一道在
      `cargo llvm-cov report` 与 `coverage_gate.py` **之后**（顺序硬约束，见 design
      「CI 侧：三个插桩 job 各加测试前与测试后两道内联清理步骤」）；wasm / lint /
      bench job 不加。验证：`pnpm check:ts` 绿（biome 管 YAML 格式）、
      `python3 scripts/check_ci.py` 绿。
- [x] 5.2 步骤顺序机器断言：逐 job 核对测试后那道清理步骤的行号晚于同 job 的
      `report` 与 `coverage_gate.py` 行号，且测试前那道早于测试命令；
      未插桩 job 无此步骤。验证：把核对结果（job 名＋三个步骤的行号）写入本文件
      完成记录，无 job 违反顺序。
- [x] 5.3 本地模拟 CI 步骤体：在仓根手跑一次清理命令（无散落时）与一次
      `touch zz-drain-proof.profraw` 后的清理命令，断言前者退出码 0 无输出、
      后者退出码非 0 且输出含该文件名、文件已删。验证：两次退出码与输出符合预期
      （CI 上无法本地跑，此条为步骤体语义的本地等价实证）。

## 6. 治理落点与文档同步（LL-034 波及面）

- [x] 6.1 账本新增四条 LL，并同步 `openspec/specs/lessons-learned/INDEX.md` 路由表
      加四行：
      `LL-103`（`ci.md` 分片）——成因（show-env 未生效 → LLVM 默认模板把 profraw
      写进进程 cwd）、规则（散落 = 采集链未生效的充分证据，harness 与 CI 首尾先删
      后报错，不留开关）、复发检测（`find` 排除 `target` 后有 profraw 即中招）。
      `LL-104`（`workflow.md` 分片）——犯过（本 change 提案首版 tasks.md 漏了
      `openspec/config.yaml` 的 `operations.apply.guidance` 规定的 apply 态只读体检
      一步，人工追问"怎么缺少了"才发现）、规则（写 tasks.md 时 MUST 把同文件
      `operations.apply.guidance` 逐条映射为收尾任务，逐条核对不遗漏；锚点仍按
      LL-089 对齐）、复发检测（review Standards 轴核对 tasks.md 收尾任务数是否等于
      config.yaml apply guidance 条数，缺项即打回）。
      `LL-105`（`ci.md` 分片）——犯过（`python/pyproject.toml` 无
      `[tool.pytest.ini_options]`，pytest 上溯采用根配置，根 `addopts` 的裸 `--cov` 覆盖
      命令行 `--cov=netwave`，使 python 地板实际量整仓；地板 0→100 后该 job 本应红
      （实测 99.75%）却无人察觉，直到本 change 加 conftest 把数字压到 87% 才暴露）、
      规则（嵌套 uv 工程 MUST 自带 `[tool.pytest.ini_options]` 与钉住 `run.source` 的
      `[tool.coverage]`，各测各的；范围与阈值只写配置文件，CI 不重复传参）、
      复发检测（`python3 scripts/check_py.py` 第 4 条规则机器强制；改任何
      `pyproject.toml` 后 MUST 贴覆盖率文件清单作证据，同 LL-094）。
      `LL-106`（`docs.md` 分片，提交后人工纠正补登）——犯过（本 change 把报错文案
      写成中文，落进两个 conftest、vitest 钩子与 `ci.yml` 六处步骤体共 18 行）、
      规则（报错文案与 stderr 输出同样算代码，属英文区；中文只进 `openspec/` 与
      `Plan/`；约定正文见 governance spec「元规则 优先级与单一真相源」）、
      复发检测（可门禁化——`check_comments.py` 加"英文区文件出现 CJK 即红"；
      未落闸门前由 review Standards 轴逐行核 diff 内新增字符串）。
      验证：`pnpm check:md` 绿，INDEX 行数与分片条目数一致、编号连续无跳号。
- [x] 6.2 `Plan/闸门重排-2026-11-12.md` 补去向行：覆盖率采集完整链
      （show-env→clean→build→test→report）随该计划 T1 绑进根聚合测试命令
      `pnpm test:*`，本 change 只提供 harness 钩子、不造入口。
      验证：`pnpm check:md` 绿，该档 §4 出现去向条目。
- [x] 6.3 `Plan/` 新增待议笔记（design/proposal 专家增补中未纳入本次范围的两条）：
      ① `scripts/check_ci.py` 增"凡 `--output-path coverage/` 的 step 同 step 须含
      `show-env`"机器校验（把 LL-091/LL-095 从散文升级为闸门）；
      ② 覆盖率跑完用 `git status --porcelain` 断言工作区无未忽略残留。
      验证：`pnpm check:md` 绿，笔记两条各含目标文件路径。
- [x] 6.4 `scripts/README.md` 补一行说明：profraw 清扫由测试钩子承担、
      `scripts/` 不提供独立清理命令（防后来者再找脚本）。
      验证：`pnpm check:md` 绿，表格新增行指向两个 conftest 与 vitest 钩子文件。
- [x] 6.5 语言约定修正（提交后人工纠正，见 LL-106）：报错文案从中文改为英文
      （全文见下方完成记录 6.5 行），阶段词 `测试前/测试后` 改
      `pre-test/post-test`，共 18 行（`scripts/tests/conftest.py`、
      `python/conftest.py`、`typescript/test/global-drain-profraw.ts`、`ci.yml`
      六处）；本 change 工件内的引用同步。验证：`grep -lP` 按 CJK 字符扫上述
      四个文件无命中；三 harness 报错与自愈行为复验不变。

## 7. 集成闸门

- [x] 7.1 全闸门：`pnpm check`（md/ts/rs/py/meta）全绿。
      验证：退出码 0，无 ::error:: 输出。
- [x] 7.2 三轴 review（governance spec「元规则 review 三轴」）：按本 change 四件
      工件（proposal / specs delta / design / tasks）对照实现 diff 审 Standards、
      Spec、Lessons 三轴，硬伤清零才准入 7.3。验证：review 结论逐条写入本文件
      完成记录，无未闭环硬伤。
- [x] 7.3 apply 态只读体检（health-check spec 的 apply 态，位置在三轴 review 之后、
      `pnpm check:outdated` 之前）：对本次 diff 触碰过的每个文件的**全文**（含不在
      diff 内的旧行）执行只读体检——语义考古维 ＋ 五维度中适用 apply 态的四维
      （⑤ Plan/ 过期仅 archive 态适用）；每维度 MUST 给结论（无发现写"已查，无"）；
      发现附文件+行号+证据写 `Plan/体检-<日期>.md`（先过三级去重），不阻塞、
      修复等点名。本次被触碰文件含 conftest / vitest 配置 / ci.yml / spec 正文，
      不会全部豁免，故 MUST 实跑，不得记"无适用文件"。验证：本文件完成记录含
      逐维度结论清单与命中项（或全"已查，无"）。
- [x] 7.4 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检与
      升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍，含全局 CLI/直装工具的
      机器级升级；上游 bug/不兼容登记回退不阻塞；仅设计级适配、restrictions.json
      破损、流程走不通才停下报告；下限变更等人工发起）。消化后 MUST 复跑
      `pnpm check:outdated` 至退出码 0（SUMMARY 归零）才算本项完成。

## Workflow follow-up

- 按 openspec 流程 archive 本 change（delta 同步进 `openspec/specs/ci-matrix/spec.md`
  的 ADDED requirement），归档前执行 Plan/ 瘦身与三态时效检查。
- **本 change 暂跳过 health-check spec 的 archive 态体检**（人工裁决 2026-11-15）：
  归档完成后的全项目存量只读体检本轮不执行；apply 态体检（task 7.3）照常执行。
  跳过仅限本 change，不改变 health-check spec 对后续 change 的默认要求。
- 提交全景表（分组 → 文件 → commit 标题）交人工点名，agent 不自行 commit。

## 完成记录

### 1.1 before 基线（2026-11-15，钩子落地前采集）

`ls *.profraw python/*.profraw`（15 个，散落 target 外）：

- `default_11430052769940151412_0_421272.profraw`
- `default_11430052769940151412_0_540974.profraw`
- `default_11430052769940151412_0_783014.profraw`
- `default_12424821166574138923_0_1099282.profraw`
- `default_16976478186941642695_0_3856193.profraw`
- `default_16976478186941642695_0_3877079.profraw`
- `default_2892781722089642066_0_421254.profraw`
- `default_2892781722089642066_0_540944.profraw`
- `default_2892781722089642066_0_782996.profraw`
- `default_5283956809441731471_0_3308413.profraw`
- `default_5284246000343966607_0_3856211.profraw`
- `default_5284246000343966607_0_3877097.profraw`
- `python/default_2892781722089642066_0_187850.profraw`
- `python/default_2892781722089642066_0_211804.profraw`
- `python/default_2892781722089642066_0_211896.profraw`

`ls target/*.profraw target/netwave-profraw-list`（2 个，报告输入，不得误删）：

- `target/netwave-266439-2892781722089642066_3.profraw`
- `target/netwave-profraw-list`

### 组 1 pytest 根侧钩子（2026-11-15）

- 1.2 red：`uv run pytest scripts/tests -k drain_profraw` 报
  `ImportError: cannot import name 'drain_stray_profraw' from 'conftest'`。
- 1.3 green：同命令 4 passed；`python3 scripts/check_py.py` 绿（单源
  `SKIP_DIRS`，conftest 只 `from lib.repository import ROOT, SKIP_DIRS`）。
- 1.4 真实样本实证：首次 `uv run pytest scripts/tests -k offline_guard`
  退出码非 0，stderr 含 `untrustworthy` 字样并逐行列出 1.1 基线的 15 个文件，
  跑完 `ls *.profraw python/*.profraw` 报 `No such file`；`target/` 内
  2 个产物原样保留。
- 1.4 自愈实证：`touch zz-drain-proof.profraw` 后复跑退出码 1、报错列出该
  文件、文件已删；第三次复跑退出码 0。全量 `uv run pytest scripts/tests`
  243 passed、覆盖率 100%；`python3 scripts/check_comments.py` 绿。

### 组 2 python 侧钩子与配置隔离（2026-11-15）

- 2.1：`touch python/zz-drain-proof.profraw` 后 `cd python && uv run pytest -q`
  退出码 1、stderr 含 `untrustworthy` 与该文件名、文件已删；复跑 67 passed 退出码 0；
  `uv run python -c "import netwave"` 输出 `ok`（sys.path 引导未遮蔽发布包）。
- 2.2 CI 同款链（`show-env`→`clean --workspace`→`maturin develop`→`pytest`→
  `report`→`coverage_gate`）本地跑通：末行 `CHAIN_OK`、退出码 0，
  `coverage_gate.py coverage/coverage-python.json 100` 报
  `351/351 = 100.00%`（含 LL-100 模式豁免 `[129, 291]`），
  跑完全仓 `find`（剪枝 `target`）无 profraw。
- 2.3 配置隔离前后对照（本组核心证据）：
  - 修复前（移开新 conftest 的基线）：
    `cd python && uv run pytest --cov=netwave --cov-fail-under=100`
    = 401 语句缺 1 = **99.75% 不达标**，
    报告含 `tests/*.py`、`conftest.py`、`scripts/versions/lib/repository.py`，
    缺行 `python/tests/test_frequency_unit.py:32`（`except` 后的防御 `raise`）；
    pytest 头部 `rootdir: /config/GitHub/netwave`、`configfile: pyproject.toml`
    （= 根配置）。
  - 修复后：`cd python && uv run pytest` = 收集 67、报告只含
    `netwave/__init__.py`（5/5）与 `netwave/constants.py`（2/2）、
    `Total coverage: 100.00%`、退出码 0。
- 2.4：`grep -rn "cov-fail-under\|--cov=" .github/workflows/ci.yml` 无输出；
  `python3 scripts/check_ci.py` 报 `3 test scripts all wired into ci.yml`。
- 2.6 TDD：red 轮 5 failed（`AttributeError`，`check_py` 无
  `check_project_scoping` 属性）→ green 轮 5 passed；`python3 scripts/check_py.py` 报
  `python hygiene OK: ... project scoping (47 files scanned)`；受控取证：
  造 `zz-scope-probe/pyproject.toml`
  （无 pytest 表）→ 退出码 1 并指名该文件，删除后转绿。
- 附带发现（记录事实，不在本 change 处理）：`testpaths` 指向空目录时 pytest 以
  退出码 5（no tests collected）失败，故 `testpaths=["tests"]` 配错会当场红而非
  静默漏测。

### 组 3 vitest native 钩子（2026-11-15）

- 3.1：`pnpm -C typescript typecheck`（`tsc --noEmit`）退出码 0；
  `pnpm check:ts`（biome）`Checked 92 files. No fixes applied.`。
  名单对照（LL-076 同族：跳目录名单存在第二份，成因是 TS 无法 import Python
  常量，已在 design 的 vitest 侧决策里记为有意偏离）：TS 侧五项
  `target`/`target-wasm`/`node_modules`/`dist`/`coverage` ⊂ `repository.py` 七项，
  差集 `.venv`/`.git` 在 `typescript/` 子树内不存在（`ls -a typescript/` 实证），
  故两表在本子树内判定等价。
- 3.2：`touch typescript/zz-drain-proof.profraw` 后
  `pnpm -C typescript test:native` 退出码 1、stderr 含 `untrustworthy` 与 `zz-drain-proof.profraw`、
  文件已从磁盘消失；复跑 7 files / 69 tests passed 退出码 0；
  `test:native --coverage` 无散落时 Statements/Branches/Functions/Lines 全 100%。

### 组 4 三 harness 对照与收尾核对（2026-11-15）

- 4.1 逐树单独放（根 conftest 扫仓库根子树，会连带删掉子树同名文件）：
  根 → 退出码 1、`RuntimeError: 测试前发现 1 个散落 target 外的 profraw 文件`、
  文件已删、复跑 1 passed；`python/` → 退出码 1、stderr 列出该文件、已删、
  复跑 67 passed；`typescript/` → 退出码 1、stderr 列出该文件、已删、复跑
  69 passed。三树跑完 `find`（排除 `target`/`node_modules`）按名搜索无输出。
- 4.2 after 清单：`ls *.profraw python/*.profraw typescript/*.profraw` 三处均报
  `No such file`（1.1 基线的 15 个真实残留全部消失）。
  `git status --porcelain` 只含本 change 的 22 项改动（17 改 ＋ 5 新建），
  无 profraw、无其他未忽略残留。
  **与 1.1 基线的差异（如实记录）**：`target/` 内产物名与数量已变
  （基线 2 项 → 现 `target/` 根 1 个 profraw ＋ `target/llvm-cov/` 20 个），
  成因 = 2.2 跑的 CI 同款链自带 `cargo llvm-cov clean --workspace` 合法重建了
  cargo 自有产物，非本 change 的钩子所为（钩子只删 `target/` 外，
  由 1.2/1.3 的 `tmp_path` 单测锁住"不删 target 内"语义）。
- 4.3：`pnpm check:cross` 退出码 0——`FREQ ROUND-TRIP PASS`、`TOUCHSTONE PASS`、
  三条 tamper 自检 PASS、vocab types 两单位 PASS、verbs 词表一致。
- 4.4：`git diff --stat .github/workflows/ci.yml` = 76 insertions / 1 deletion，
  唯一非清理步骤的改动是 2.4 那条 `uv run pytest` 参数简化（已并入本 change
  范围）；`python3 scripts/check_ci.py` 退出码 0。

### 组 5 CI 清理步骤（2026-11-15）

- 5.1：rust / python / node 三个 job 各加 `drain stray profraw (pre-test)` 与
  `(post-test)` 两道内联 shell；wasm / lint / bench 未加。
  步骤体用**无括号 prune 链**（`find . -name target -prune -o ... -o -name '*.profraw' -print`）：
  原计划的 `\( ... \)` 形式实测在 bash 下报
  `syntax error near unexpected token '('`（YAML 里写 `\\(` 落到 bash 是 `\\(`，
  反斜杠被吃掉后括号裸露），无括号形式实测正确（造 `a.profraw`、
  `nested.profraw`、`target/in.profraw`、`node_modules/x.profraw`、
  `coverage/y.profraw` → 只输出前两个，退出码 0）。
  `pnpm check:ts` 绿、`python3 scripts/check_ci.py` 绿。
- 5.2 顺序核对（行号取自改后 ci.yml；格式 `pre-test / 测试 / report / gate / post-test`）：
  rust = 91 / 125 / — / 126 / 128；python = 227 / 257 / 258 /
  261 / 262；node = 332 / 371 / 373 / 376 / 377。三 job 均满足
  pre-test < 测试 < report < gate < post-test；wasm（150）/ lint（27）/
  bench（434）三个 job 无 drain 步骤。
- 5.3 本地模拟步骤体：无散落时退出码 0 且无输出；`touch zz-drain-proof.profraw`
  后退出码 1、stderr 含该文件名与 `1 found, deleted`、文件已删。

### 组 6 治理落点与文档同步（2026-11-15）

- 6.1：`openspec/specs/lessons-learned/ci.md` 新增 LL-103、LL-105，
  `workflow.md` 新增 LL-104，`docs.md` 新增 LL-106（提交后人工纠正补登，见 6.5），
  `INDEX.md` 加对应四行；`pnpm check:md` 绿
  （`Summary: 0 issues in 0 files`、prettier clean、`check_md.py` 报
  `checked 415 files; OK`），INDEX 末四行编号 103/104/105/106 连续无跳号。
- 6.2：`Plan/闸门重排-2026-11-12.md` §4 补去向行（完整采集链随该计划 T1
  绑进 `pnpm test:*`，本 change 只提供 harness 钩子、不造入口）。
- 6.3：新增 `Plan/覆盖率闸门加固-2026-11-15.md`，两条待议各含目标文件路径
  （① `scripts/check_ci.py` 校验 `--output-path coverage/` 同 step 含
  `show-env`；② 覆盖率跑完 `git status --porcelain` 断言无未忽略残留），
  `Plan/README.md` 加索引行。（该档后续扩到四条：提交后补登第 3 条收集数
  下限与第 4 条英文区禁中文闸门，见 6.5）
- 6.4：`scripts/README.md` 表格新增一行，指向 `scripts/tests/conftest.py`、
  `python/conftest.py`、`typescript/test/global-drain-profraw.ts`，
  注明 `scripts/` 不提供独立清理命令。
- 6.5 语言约定违规与修正（人工纠正）：本 change 首版把报错文案写成中文，
  共 18 行落在四个英文区文件（`scripts/tests/conftest.py` 3 行、
  `python/conftest.py` 4 行、`typescript/test/global-drain-profraw.ts` 4 行、
  `ci.yml` 六处步骤体各 1 行 = 6 行，另三处阶段词共 3 行）。
  成因：写报错时只考虑"人能不能看懂"，未先判文件属哪个语言区；
  现有闸门（`check_comments.py`）只拦历史归因/阶段词/spec 指针，不拦 CJK，
  所以 `pnpm check` 全绿也没拦住。修正：报错文案改英文（单行）
  `profraw outside target/ = the coverage chain did not take effect, so coverage numbers for this run are untrustworthy`，阶段词 `测试前/测试后` 改
  `pre-test/post-test`；已按该条落账本 LL-106（`docs.md`）并登记可门禁化
  建议。验证：`grep -lP '[\x{4e00}-\x{9fff}]'` 扫上述四文件无命中；
  三 harness 报错与自愈行为复验（见下方行为复验行）。

行为复验（报错文案改英文后，逐树重跑）：

- 根：`touch zz-drain-proof.profraw` 后 `uv run pytest scripts/tests -k offline_guard`
  → 退出码非 0，stderr 输出（单行）
  `profraw outside target/ = the coverage chain did not take effect, so coverage numbers for this run are untrustworthy (pre-test: found 1, deleted):`，文件已删；
  全量 `uv run pytest` 复跑 248 passed、覆盖率 100%、退出码 0。
- `python/`：`touch python/zz-drain-proof.profraw` 后 `cd python && uv run pytest -q`
  → 退出码 1、stderr 含 `untrustworthy` 与该文件名、文件已删；复跑 67 passed、
  `Total coverage: 100.00%`、退出码 0。
- `typescript/`：`touch typescript/zz-drain-proof.profraw` 后
  `pnpm -C typescript test:native` → 退出码 1、stderr 含同一英文文案与
  `(pre-test: found 1, deleted)`、文件已删；复跑退出码 0。
- `grep -lP '[\x{4e00}-\x{9fff}]'` 扫 `scripts/tests/conftest.py`、
  `python/conftest.py`、`typescript/test/global-drain-profraw.ts`、
  `.github/workflows/ci.yml` 无命中（退出码 1 = 无匹配）。

### 7.1 全闸门（2026-11-15）

- `pnpm check`（`check:md` → `check:ts` → `check:rs` → `check:py` →
  `check:meta`）退出码 0；`pnpm check 2>&1 | grep -c '::error::'` = 0。
- 各腿证据：markdownlint 0 issues、prettier clean、`check_md.py` 413 files OK；
  biome `Checked 92 files`；`cargo fmt --all --check` 49 files already formatted、
  clippy `-D warnings` 无告警；ruff lint/format 通过、根 pytest 248 passed
  覆盖率 100%；`check:meta` 七项全绿（license 6 files、`check_ci.py` 3 test
  scripts wired、vocab 9 binding sources、`check_comments.py` OK、
  `check_proposal.py` 1 in-flight proposal、`check_versions.py` 版本法 OK、
  `check_py.py` 47 files scanned）。

### 7.2 三轴 review（2026-11-15）

Standards（对照 governance 铁律/元规则 ＋ 坏味道，审本次 diff 行）：

- 语义考古：逐行核过 17 改 ＋ 5 新建，报错文案与注释只陈述当前契约
  （"散落 = 采集链未生效 = 本轮数字不可信"，按语言约定用英文），无历史归因、无
  "replaces/no longer/phase-N"；`check_comments.py` 绿佐证。结论：无违规。
- 命名一眼能懂：`drain_stray_profraw` / `check_project_scoping` /
  `global-drain-profraw.ts` 均动词开头、完整单词，与被检对象同名可追溯。无违规。
- 最小增量：未新增独立脚本、未加跳过开关、未抽跨语言公共模块（D1 已记否决理由）；
  每行 diff 可追溯到 proposal What-Changes 条目。无违规。
- LL-034 波及面：CI 步骤顺序、README 命令口径、spec/账本/Plan 均已同步（组 6 记录）。
- 命中并修正 1 处：delta spec 把 `browser` 列为 ci.yml 的 job，实际 ci.yml 无
  browser job（browser 只是 vitest 配置文件，不在 CI 跑）——已删该词，与
  proposal/design 的"wasm、lint、bench"口径统一。
- 记录不修（提一嘴，非硬伤）：CI 步骤体 `printf '%s\n' "$stray" | xargs rm -f`
  对含空格文件名会拆分；LLVM 默认模板 `default_%m_%p.profraw` 不含空格，
  且 `xargs -d` 在 macOS（python/node job 的 runner）不可用，故保持现形式。

Spec（对照 `specs/ci-matrix/spec.md` delta 逐条核实落地）：

- 「覆盖率中间产物不跨轮残留」：根 conftest / `python/conftest.py` /
  vitest globalSetup 三处均在会话首尾先删后报错（组 1/2/3 实证）；
  CI 三插桩 job 各两道步骤且 post-test 晚于 report 与 gate（5.2 行号表）；
  wasm/lint/bench 无此步骤；`target/` 内产物与 `.coverage`/`coverage/*.json`
  不误删（1.2/1.3 单测锁）。五个 Scenario 逐条有证据。落地。
- 「嵌套 Python 工程自带 pytest 配置」：`python/pyproject.toml` 三表齐备（2.3）、
  `check_py.py` 规则 4 机器强制（2.6 TDD 红→绿＋受控取证）、CI 去重复参数（2.4）。
  三个 Scenario 逐条有证据。落地。
- 结论：无"Requirement 无对应落地"。唯一文字与实现不符（browser job）已修。

Lessons（对照 INDEX 逐条核对，命中项按该条复发检测复验）：

- LL-076（两份清单必漂移）：TS 侧 `SKIP_DIRS` 字面量是第二份名单——跨语言物理
  限制，已在 D1/D3 记偏离理由，并补名单对照证据（组 3 记录：五项 ⊂ 七项，
  差集在 `typescript/` 内不存在）。按该条检测方法复验通过。
- LL-094（改 pytest 全局配置须当轮全量跑并贴覆盖率文件清单）：2.3 已贴修复前
  （401 语句含 `tests/`、`scripts/`）与修复后（仅 `netwave/` 两文件）清单。
- LL-048（CI 步骤钉 `shell: bash`）：六个新步骤均显式 `shell: bash`。
- LL-091/LL-095（show-env 不跨 step、输出目录）：未改动采集链与 `mkdir -p`，
  加固项另立 `Plan/覆盖率闸门加固-2026-11-15.md`。
- LL-102（改 .md 必跑 check:md）：本轮每次 .md 编辑后均跑，绿。
- LL-103/104/105：本 change 新增三条，内容与实现一致（6.1）。
- 其余条目（core/oracle/python 绑定细节等）与本次 diff 无关。结论：无未闭环命中。

### 7.3 apply 态只读体检（2026-11-15）

扫描范围 = 本次 diff 触碰的 22 个文件全文，其中 `Plan/`（3 个）、账本（3 个）、
本 change 工件自身（4 个）按 spec 豁免语义不入扫描，实际被检 12 个非豁免文件
（`ci.yml`、根/`python/` 两个 `pyproject.toml`、`python/README.md`、
`scripts/README.md`、`scripts/check_py.py`、`scripts/tests/conftest.py`、
两个新单测、`python/conftest.py`、`vitest.native.config.ts`、
`typescript/test/global-drain-profraw.ts`）。逐维度结论：

- ①文档断言 vs 环境实测：2 条（`python/README.md:19` Layout 少列 5 个测试模块；
  `scripts/README.md:19` 与 `scripts/check_ci.py:6` 引用已退役编号 LL-037）。
- ②死代码/孤儿文件：1 条（`scripts/README.md` 脚本表缺 7 个既有闸门脚本的索引行）。
- ③规则重复/冲突：已查，无（`AGENTS.md`／governance spec／`config.yaml`／
  ci-matrix spec 同一规则均一处正文其余指针）。
- ④可门禁化 LL 未落闸门：1 条（LL-104 的复发检测是工件条数比对、机械可判却
  仍靠自觉；同批 LL-103/105 已落闸门）。
- ⑤Plan/ 过期：仅 archive 态适用，本态不适用。
- 语义考古维：已查，无（12 个文件全文逐行读过，均为当前契约与机制说明）。

四条发现均"待拍板"级、无"硬"级，已按三级去重后写入
`Plan/体检-2026-11-15.md`（第一级账本 INDEX 未命中、第二/三级现有 Plan 条目
未命中：`Plan/覆盖率闸门加固-2026-11-15.md` 两条是 show-env 接线校验与工作区
残留断言，与本批四条不同主题，不构成归属）。体检未修改任何被检文件，修复等点名。

### apply guidance 逐条映射（LL-104 防复发复验）

对照 `openspec/config.yaml` 的 `operations.apply.guidance` 五条：

1. Plan/ 对应章节当场删除 → 本 change 在 `Plan/` 无已完成章节：
   `Plan/闸门重排-2026-11-12.md` §4 去向行指向的是 T1 未执行入口（保留），
   `Plan/覆盖率闸门加固-2026-11-15.md` 两条是未点名延后项（保留），
   `Plan/体检-2026-11-15.md` 是体检输出（等点名）。已跑 `pnpm check:md`。
2. specs 三态时效结论 → 更新：`openspec/specs/ci-matrix/spec.md`（两条 ADDED
   requirement 待归档 sync，本 change 已备 delta）；新增：无需新建 spec 文件
   （profraw 卫生与嵌套工程配置同属 ci-matrix 主题，design 已给出否决新开
   `coverage-hygiene` 能力域的理由）；退役：无（`Plan/闸门重排` T4 拟升级的
   `check_ci.py` 口径与本 change 无冲突，仍待点名）。
   `openspec/specs/README.md` 路由无需改动（未新增 spec 文件）。
3. 三轴 review 硬伤清零 → 7.2，已记录并修掉 1 处（delta spec 的 browser job 误称）。
4. 被触碰文件全文只读体检 → 7.3，本节上方。
5. 最后一项跑 `pnpm check:outdated` 并消化 LAG → 7.4（本条为收尾最后一项，
   锚点为"最后一项"，未前移）。

### 7.4 依赖新鲜度体检（2026-11-15）

`pnpm check:outdated` 退出码 0，末行 `SUMMARY: 0 LAG (all current)`；复跑仍 0，
本项完成条件（SUMMARY 归零）满足。分段：全局 CLI 八项（node/npm/pnpm/uv/
rustup/rustc/openspec/markdownlint-cli2）、tarball 与 cargo 子命令三项
（wasm-pack/binaryen/cargo-llvm-cov）、CI actions 六项
（`dtolnay/rust-toolchain@stable` 为 REF 型非版本 tag，不计 LAG）、
pnpm/cargo dry-run 无更新行。

**本项如实记录一处异常，且本文件首版记录曾给出错误解释（已改正）**：
uv 段打印了 `Update numpy v2.2.6, v2.4.6, v2.5.4 -> v2.2.6, v2.4.6, v2.5.5`
（= python 工程存在待升级包），SUMMARY 却计 0 LAG。本文件首版把这条写成
"dry-run 信息行、`.python-version` 钉 3.10 线的 numpy 上界未变"——该解释
未经实证即写下，违 LL-083（下结论前须受控取证），现撤回。
取证后的真实成因：`scripts/versions/check_outdated.py` 的 `count_uv_changes()`
用正则 `(Updating|Updated|Adding|Removing)` 匹配，而 uv 0.13.8 dry-run 的真实
动词是 `Update`/`Add`（`/tmp/uvverb` 受控实验实证：`Update idna v3.7 -> v3.6`），
正则永不命中 = uv 段恒报 0（假绿）；既有单测夹具同样用臆造动词
（`test_check_outdated.py:527-529` 写 `Updated foo`/`Adding bar`），故测试绿而
闸门失效。该缺陷不在本 change 范围（本 change 不触碰 `check_outdated.py`），
已连证据与建议处置另立 `Plan/依赖闸门uv段假绿-2026-11-15.md` 等点名。
因此本项"退出码 0"达成的是**门禁口径**，不代表 uv 侧真的无落后。
