# Tasks

## 1. pytest 根侧：可单测的清扫函数（red 先于 green）

- [ ] 1.1 抢在钩子落地前留存真实残留快照：把根与 `python/` 下 15 个
      `default_*_*.profraw` 的逐行清单（`ls *.profraw python/*.profraw`）、
      `target/` 内 profraw 与清单文件的逐行清单，一并贴进本文件完成记录作
      before 基线——钩子一旦落地，首次 pytest 就会把真实文件删掉，事后无从取证。
      验证：本文件完成记录含两组逐行文件名清单，数量 15 ＋ target 内实际数。
- [ ] 1.2 red：新建 `scripts/tests/test_drain_profraw.py`，用 `tmp_path` 造夹具
      （`tmp/stray.profraw`、`tmp/nested/deep.profraw`、`tmp/target/inside.profraw`、
      `tmp/node_modules/pkg/x.profraw`、`tmp/keep.txt`），断言
      `from conftest import drain_stray_profraw` 可导入、返回相对 root 的被删路径
      集合恰为两个散落文件、`target/` 与 `node_modules/` 内文件与 `keep.txt` 原样
      保留、无散落时返回空列表。验证：`uv run pytest scripts/tests -k drain_profraw`
      失败（`ImportError: cannot import name 'drain_stray_profraw'`），退出码非 0。
- [ ] 1.3 green：在 `scripts/tests/conftest.py` 实现
      `drain_stray_profraw(root: Path) -> list[Path]`——`root.rglob("*.profraw")`，
      任一相对路径段命中 `from lib.repository import SKIP_DIRS` 即跳过，其余
      `unlink()` 并收集相对路径后排序返回。验证：1.2 命令转绿（4 passed），
      `python3 scripts/check_py.py` 仍绿（未新增第二处 `SKIP_DIRS` 赋值）。
- [ ] 1.4 在 `scripts/tests/conftest.py` 加 autouse session fixture
      `drain_stray_profraw_session`：yield 前调 `drain_stray_profraw(ROOT)`、
      yield 后再调一次，任一次返回非空即把"profraw 散落在 target 外 = 覆盖率采集链
      未生效，本轮覆盖率数字不可信"＋被删文件名与个数写 stderr 并 `raise`。
      验证：首次 `uv run pytest scripts/tests -k offline_guard` 即因 1.1 记录的
      根目录真实残留报错（退出码非 0、stderr 列出文件名与"不可信"字样、
      `ls *.profraw` 为空 = 真实样本实证）；再 `touch` 一个
      `zz-drain-proof.profraw` 复跑仍报错并删除；第三次复跑退出码 0（自愈）。

## 2. python 侧：独立 rootdir 的等价钩子

- [ ] 2.1 新建 `python/conftest.py`：内联 `drain_stray_profraw(root)` 等价实现
      （见 design「pytest 侧：conftest 内具名函数 ＋ session fixture 首尾各调一次」），
      文件顶部用 `sys.path.insert` 引导 `scripts/versions` 以
      `from lib.repository import SKIP_DIRS`（同 `scripts/check_py.py` 先例），
      加同语义的 autouse session fixture，扫描根 = `Path(__file__).parent`。
      验证：`touch /config/GitHub/netwave/python/zz-drain-proof.profraw` 后
      `cd python && uv run pytest -q` 退出码非 0、报错含该文件名、文件消失；
      复跑退出码 0；`cd python && uv run python -c "import netwave"` 仍成功
      （sys.path 引导未遮蔽发布包）。
- [ ] 2.2 确认 `python/` 侧清扫不影响 maturin 覆盖率链：按 ci.yml python job 的
      单 step 链（`show-env` → `clean --workspace` → `maturin develop` →
      `pytest --cov=netwave --cov-fail-under=100` → `report`）在 `bash -c` 子 shell
      内跑通。验证：命令退出码 0、`coverage/coverage-python.json` 生成且
      `python3 scripts/coverage_gate.py coverage/coverage-python.json 100` 绿、
      跑完 `git status --porcelain | grep profraw` 无输出。

## 3. vitest native 侧：globalSetup 钩子

- [ ] 3.1 新建 `typescript/test/global-drain-profraw.ts`：导出 `setup` 异步函数，
      扫描 `typescript/` 子树删 `*.profraw`（跳过名单按 design 的扫描范围决策取
      `target`/`target-wasm`/`node_modules`/`dist`/`coverage` 字面量，TS 侧无法
      import Python 常量），有删除则写 stderr 证据并置 `process.exitCode = 1`，
      返回同语义的 teardown 闭包。验证：`pnpm -C typescript typecheck` 绿
      （strict/checkJs 下无类型错）、`pnpm check:ts` 绿。
- [ ] 3.2 在 `typescript/vitest.native.config.ts` 的 `test` 段加
      `globalSetup: "./test/global-drain-profraw.ts"`。验证：
      `touch /config/GitHub/netwave/typescript/zz-drain-proof.profraw` 后
      `pnpm -C typescript test:native` 退出码非 0 且 stderr 含该文件名，文件已从
      磁盘消失；复跑退出码 0（自愈）；`pnpm -C typescript test:native --coverage`
      在无散落时仍达 lines/branches 100 阈值。

## 4. 三 harness 行为对照与一次性实证

- [ ] 4.1 三处行为对照（design 风险项"改一处漏两处"的防线）：伪造文件
      `zz-drain-proof.profraw` **逐树单独放**（根 conftest 扫仓库根子树，会连带删掉
      `python/`、`typescript/` 里的同名文件，三树同放则后两个 harness 无样本可删），
      每放一个跑对应 harness：根→`uv run pytest scripts/tests -k offline_guard`、
      `python/`→`cd python && uv run pytest -q`、`typescript/`→
      `pnpm -C typescript test:native`。断言三者均退出码非 0、各自报错列出文件名、
      跑完该树无残留。验证：三条命令退出码均非 0，且 `find` 按名
      `zz-drain-proof.profraw` 搜索（排除 `target`/`node_modules`/`.venv`）
      无输出；三树各自复跑对应命令均退出码 0。
- [ ] 4.2 真实残留清理后的收尾核对：对照 1.1 的 before 基线，确认根与 `python/`
      的 15 个 `default_*_*.profraw` 已全部消失（`ls *.profraw python/*.profraw`
      报 `No such file`），把 after 输出贴进本文件完成记录与 1.1 配对。
      验证：after 清单为空、`target/` 内 profraw 与 `target/netwave-profraw-list`
      数量与 1.1 基线一致（未被误删）、`git status --porcelain` 无未跟踪/未忽略残留。
- [ ] 4.3 跨绑定回归不受影响：跑 `pnpm check:cross`（本 change 不触碰数值路径，
      此条为"功能只增不减"的回归证据）。验证：退出码 0，四端 dump 对拍无差异。
- [ ] 4.4 CI 侧口径确认：`git diff` 证明 `.github/workflows/ci.yml` 的改动**只**
      新增清理步骤（无其他语义改动），`python3 scripts/check_ci.py` 绿（未新增需
      接线的 `test:*` 脚本）。验证：`git diff --name-only` 含 `ci.yml` 且 diff 行
      仅为新增的清理步骤；闸门退出码 0。

## 5. CI 侧：三个插桩 job 各加测试前与测试后清理步骤

- [ ] 5.1 在 `.github/workflows/ci.yml` 的 rust、python、node 三个 job 各加两道
      内联 shell 清理步骤（步骤体同语义：`find` 剪枝 `target`/`target-wasm`/
      `node_modules`/`.venv`/`dist`/`coverage` 后找 `*.profraw`，命中则打印文件名
      与个数并以非零码退出，否则静默通过）：一道在测试步骤之前，一道在
      `cargo llvm-cov report` 与 `coverage_gate.py` **之后**（顺序硬约束，见 design
      「CI 侧：三个插桩 job 各加测试前与测试后两道内联清理步骤」）；wasm / lint /
      bench job 不加。验证：`pnpm check:ts` 绿（biome 管 YAML 格式）、
      `python3 scripts/check_ci.py` 绿。
- [ ] 5.2 步骤顺序机器断言：逐 job 核对测试后那道清理步骤的行号晚于同 job 的
      `report` 与 `coverage_gate.py` 行号，且测试前那道早于测试命令；
      未插桩 job 无此步骤。验证：把核对结果（job 名＋三个步骤的行号）写入本文件
      完成记录，无 job 违反顺序。
- [ ] 5.3 本地模拟 CI 步骤体：在仓根手跑一次清理命令（无散落时）与一次
      `touch zz-drain-proof.profraw` 后的清理命令，断言前者退出码 0 无输出、
      后者退出码非 0 且输出含该文件名、文件已删。验证：两次退出码与输出符合预期
      （CI 上无法本地跑，此条为步骤体语义的本地等价实证）。

## 6. 治理落点与文档同步（LL-034 波及面）

- [ ] 6.1 账本新增两条 LL，并同步 `openspec/specs/lessons-learned/INDEX.md` 路由表
      加两行：
      `LL-103`（`ci.md` 分片）——成因（show-env 未生效 → LLVM 默认模板把 profraw
      写进进程 cwd）、规则（散落 = 采集链未生效的充分证据，harness 与 CI 首尾先删
      后报错，不留开关）、复发检测（`find` 排除 `target` 后有 profraw 即中招）。
      `LL-104`（`workflow.md` 分片）——犯过（本 change 提案首版 tasks.md 漏了
      `openspec/config.yaml` 的 `operations.apply.guidance` 规定的 apply 态只读体检
      一步，人工追问"怎么缺少了"才发现）、规则（写 tasks.md 时 MUST 把同文件
      `operations.apply.guidance` 逐条映射为收尾任务，逐条核对不遗漏；锚点仍按
      LL-089 对齐）、复发检测（review Standards 轴核对 tasks.md 收尾任务数是否等于
      config.yaml apply guidance 条数，缺项即打回）。
      验证：`pnpm check:md` 绿，INDEX 行数与分片条目数一致、编号连续无跳号。
- [ ] 6.2 `Plan/闸门重排-2026-11-12.md` 补去向行：覆盖率采集完整链
      （show-env→clean→build→test→report）随该计划 T1 绑进根聚合测试命令
      `pnpm test:*`，本 change 只提供 harness 钩子、不造入口。
      验证：`pnpm check:md` 绿，该档 §4 出现去向条目。
- [ ] 6.3 `Plan/` 新增待议笔记（design/proposal 专家增补中未纳入本次范围的两条）：
      ① `scripts/check_ci.py` 增"凡 `--output-path coverage/` 的 step 同 step 须含
      `show-env`"机器校验（把 LL-091/LL-095 从散文升级为闸门）；
      ② 覆盖率跑完用 `git status --porcelain` 断言工作区无未忽略残留。
      验证：`pnpm check:md` 绿，笔记两条各含目标文件路径。
- [ ] 6.4 `scripts/README.md` 补一行说明：profraw 清扫由测试钩子承担、
      `scripts/` 不提供独立清理命令（防后来者再找脚本）。
      验证：`pnpm check:md` 绿，表格新增行指向两个 conftest 与 vitest 钩子文件。

## 7. 集成闸门

- [ ] 7.1 全闸门：`pnpm check`（md/ts/rs/py/meta）全绿。
      验证：退出码 0，无 ::error:: 输出。
- [ ] 7.2 三轴 review（governance spec「元规则 review 三轴」）：按本 change 四件
      工件（proposal / specs delta / design / tasks）对照实现 diff 审 Standards、
      Spec、Lessons 三轴，硬伤清零才准入 7.3。验证：review 结论逐条写入本文件
      完成记录，无未闭环硬伤。
- [ ] 7.3 apply 态只读体检（health-check spec 的 apply 态，位置在三轴 review 之后、
      `pnpm check:outdated` 之前）：对本次 diff 触碰过的每个文件的**全文**（含不在
      diff 内的旧行）执行只读体检——语义考古维 ＋ 五维度中适用 apply 态的四维
      （⑤ Plan/ 过期仅 archive 态适用）；每维度 MUST 给结论（无发现写"已查，无"）；
      发现附文件+行号+证据写 `Plan/体检-<日期>.md`（先过三级去重），不阻塞、
      修复等点名。本次被触碰文件含 conftest / vitest 配置 / ci.yml / spec 正文，
      不会全部豁免，故 MUST 实跑，不得记"无适用文件"。验证：本文件完成记录含
      逐维度结论清单与命中项（或全"已查，无"）。
- [ ] 7.4 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检与
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
