# Tasks

## 1. 闸门 red 基线（先加阈值，确认现状红）

- [ ] 1.1 根 `package.json` `check:py` 的 pytest 追加
      `--cov-fail-under=100`（度量范围 `--cov=scripts/versions` 不变）。
      验证：`pnpm check:py` 退出码非 0，报
      "Required test coverage of 100% not reached"（实测 99.28%，
      miss = `check_versions.py:48`、`check_outdated.py:149`）

## 2. runpy 门面用例（green）

- [ ] 2.1 `scripts/tests/versions/test_check_versions.py` 新增 2 例：
      `runpy.run_path(check_versions.__file__, run_name="__main__")`，
      桩打在 `lib.rules.all_laws`（violations 例）与
      `lib.rules.all_laws`+`lib.rules.summary`（clean 例），断言
      `SystemExit.code` 分别为 1 / 0。验证：
      `uv run pytest scripts/tests/versions/test_check_versions.py -q` 通过
- [ ] 2.2 `scripts/tests/versions/test_check_outdated.py` 新增 1 例：
      runpy 真跑门面，桩打在 `lib.latest`（`find_uv_projects`/`run_cmd`/
      `fetch_json`/`latest_version`/`refine_node_lts`/`action_refs`）与
      `lib.repository.find_python_versions`，断言 `SystemExit.code == 0`
      （恒退 0 契约的进程级钉法）。验证：
      `uv run pytest scripts/tests/versions/test_check_outdated.py -q` 通过
- [ ] 2.3 桩绑定注释按当前契约事实写（"runpy 重执行按 sys.modules
      重绑定，桩打在 lib 源头模块"），不引用 change 名
      （check_comments 口径）。验证：`pnpm check:meta` 通过

## 3. 覆盖率与反向验证

- [ ] 3.1
      `uv run pytest --cov=scripts/versions --cov-report=term-missing --cov-fail-under=100`
      全绿，逐文件 100%、TOTAL 100%、零豁免行；
      把结果表贴进本文件完成记录
- [ ] 3.2 反向验证（防恒绿闸门）：临时移除 2.1 的 exit-1 例复跑
      `pnpm check:py` 确认退出码非 0（覆盖率跌回 99%），还原后全绿；
      结果记入完成记录

## 4. 账本与文档同步

- [ ] 4.1 `openspec/specs/lessons-learned/python.md` 新增 LL-079
      （runpy 重执行门面时 `from lib.x import y` 按 `sys.modules` 重绑定，
      桩须打在 lib 源头模块，门面模块上的 patch 被冲掉），
      `INDEX.md` 同步路由行。验证：`pnpm check:md` 退出 0
- [ ] 4.2 `scripts/versions/README.md` 测试段补一句：versions 域覆盖率
      地板经 `check:py` 的 `--cov-fail-under` 生效。验证：`pnpm check:md`
- [ ] 4.3 `Plan/软件升级.md`：删除「scripts/ 治理待议」中 versions 域
      覆盖率已拍板内容（"要不要单元测试+覆盖率 100%"节的 versions 结论、
      "待决：scripts 覆盖率阈值是否进 coverage_gate"段）与
      「落地形态汇总」对应行；其余 scripts/ 待议内容保留，节首状态行
      改注本 change 承接指针。验证：`pnpm check:md` 退出 0

## 5. 集成闸门

- [ ] 5.1 `pnpm check` 全绿（含 check:py 阈值、check:meta 的
      check_ci/check_comments/check_proposal）；`ci.yml` 零改动确认
      （git status 不含该文件）。验证：退出码 0

## Workflow follow-up

- apply 完成时按 config.yaml apply 钩子：Plan/ 对应章节当场删除 +
  `pnpm check:md`；扫 openspec/specs/ 三态时效（预期：更新=ci-matrix
  随本 change delta 归档生效，其余无），结论留痕本文件完成记录
- 提交分组与标题由人工确认后执行（agent 不主动 commit）
