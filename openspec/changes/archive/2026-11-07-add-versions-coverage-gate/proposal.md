# Proposal

## Why

`scripts/versions` 域补测（change `add-versions-domain-tests`）后实测覆盖率
277 stmts / miss 2 = 99%，仅剩两个门面文件的 `sys.exit(main())` 两行未覆盖，
且 `check:py` 只报数不设阈值——闸门脚本回归时覆盖率可无声下滑。人工已拍板：
该域覆盖率提到 100% 并把阈值做成命令与 CI 闸门（runpy 方案已实测可行：
3 例离线用例使 277/277 = 100%，99% 时 `--cov-fail-under=100` 退出码 1）。

## What Changes

- `scripts/tests/versions/test_check_versions.py` 新增 2 例、
  `test_check_outdated.py` 新增 1 例：以 `runpy.run_path(..., run_name="__main__")`
  真跑门面，覆盖 `sys.exit(main())` 守卫行，并钉住"返回值→进程退出码"接线
  （check_versions 双向 0/1、check_outdated 恒 0）；桩打在 lib 源头模块属性上。
- 根 `package.json` 的 `check:py`：pytest 追加 `--cov-fail-under=100`
  （度量范围维持 `--cov=scripts/versions` 不变）。CI 经 `pnpm check` 自动生效，
  `ci.yml` 零改动（命令唯一真相源在根 package.json）。
- `ci-matrix` spec「治理脚本单测进 CI」Requirement 新增 Scenario：versions 域
  覆盖率 100% 地板经 `check:py` 生效，低于即 lint job 红。
- `Plan/软件升级.md`：删除 versions 域已拍板内容（「scripts/ 治理待议」中
  覆盖率阈值相关段与「落地形态汇总」对应行），其余 scripts/ 待议内容保留。
- 新增 LL-079（lessons-learned python 分片 + INDEX）：runpy 重执行门面时
  `from lib.x import y` 按 `sys.modules` 重绑定，桩必须打在 lib 源头模块，
  打在门面模块上会被冲掉。

## Capabilities

### New Capabilities

（无——不引入新能力。）

### Modified Capabilities

- `ci-matrix`：「治理脚本单测进 CI」Requirement 新增 Scenario——治理脚本
  versions 域行覆盖率 MUST 以 `--cov-fail-under=100` 度量并生效于 lint job，
  ci.yml MUST NOT 出现第二处阈值命令。

## Impact

- 测试：`scripts/tests/versions/test_check_versions.py`、
  `scripts/tests/versions/test_check_outdated.py`（+3 例，全离线）。
- 命令：根 `package.json` `check:py`（加一个 flag）。
- spec：`openspec/specs/ci-matrix/spec.md`（delta：1 个 Scenario）。
- 账本：`openspec/specs/lessons-learned/python.md` + `INDEX.md`（LL-079）。
- 文档：`scripts/versions/README.md`（测试段补阈值生效一句）、
  `Plan/软件升级.md`（已拍板内容剥除）。
- 生产代码：零改动（`scripts/versions/` 下 `.py` 不动）。
- 受影响铁律：铁律七（覆盖率 100% 硬约束）——本 change 把该约束的口径从
  四端产码延伸到治理脚本 versions 域，豁免通道沿用（本次无需豁免）。

## Non-goals

- 不扩度量范围到 `scripts/` 其余无测闸门脚本（`check_md.py` 等 8 个）——
  属「scripts/ 治理待议」另议题。
- 不改 `ci.yml`（不新增 job、不出现第二处单测/阈值命令）。
- 不把阈值写进 `pyproject.toml`（`[tool.coverage]`），维持命令可见性。
- 不动 `scripts/versions/` 生产代码与既有测试断言。
- 不实施 blocked / pairs 机制（各自独立待触发项）。

## Prior art

- 仓库内现成实现：`ci.yml` python job 的
  `uv run pytest --cov=netwave --cov-fail-under=100`（本 change 同款 flag，镜像其写法）；
  `scripts/coverage_gate.py` 仅适用 Rust codecov.json，不适用 Python 域，
  故不采用。
- pytest-cov 官方 `--cov-fail-under` 阈值语义：
  <https://pytest-cov.readthedocs.io/en/latest/config.html>。
- runpy 标准库 `run_name="__main__"` 重执行语义：
  <https://docs.python.org/3/library/runpy.html>。

## 专家增补

- 闸门"红"向验证纳入验收：故意移除一条 runpy 用例确认 `check:py` 退出码 1
  （防恒绿闸门），落 `tasks.md` 反向验证任务。
- runpy 用例顺带钉住门面退出码契约（`sys.exit(main())` 接线），这是现有
  `main()` 直调测试覆盖不到的 CI 输出面——`test_check_versions.py` 双向、
  `test_check_outdated.py` 恒 0。
- LL-079 入账时同步 `openspec/specs/lessons-learned/INDEX.md` 路由行，
  防账本与 INDEX 漂移（LL-034 波及面同步惯例）。
