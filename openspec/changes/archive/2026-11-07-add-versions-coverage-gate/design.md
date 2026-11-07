# Design

## Context

见 proposal.md - Why。补充实测事实：基线 `uv run pytest --cov=scripts/versions`
= 277 stmts / miss 2（`check_versions.py:48`、`check_outdated.py:149`，均为
`sys.exit(main())`）；runpy 原型 3 例离线通过、合并跑 277/277 = 100%；
`--cov-fail-under=100` 在 99% 时退出码 1（红向已验）。

## Goals / Non-Goals

**Goals:**

- versions 域行覆盖率 100%，无豁免行。
- 阈值成为 `check:py` 的硬闸门，经 `pnpm check` 在 CI lint job 生效。
- 钉住门面"返回值→进程退出码"接线（现有 `main()` 直调测试覆盖不到的面）。

**Non-Goals:**

- 设计级补充：不重构门面文件使其"更可测"（如把 `sys.exit` 挪进可调用）——
  现有形状 + runpy 已足够，动生产代码违反最小增量。

## Decisions

1. **runpy 覆盖 `__main__` 守卫，而非 `# pragma: no cover` 豁免**：
   这两行可达（runpy 以 `run_name="__main__"` 重执行即触达），可达而豁免违反
   铁律七"100% 是下限"；`exclude_lines` 配 `__main__` 模式属批量豁免，同样禁用。
   备选：subprocess 真跑脚本——慢、且真跑 `check_outdated.py` 会联网，否决。
2. **桩打在 lib 源头模块属性，不打在门面模块**（实测坑，入账 LL-079）：
   runpy 重执行门面文件时，其 `from lib.x import y` 在 exec 时从 `sys.modules`
   重新绑定，取到 lib 模块当前属性；门面模块上的 monkeypatch 随门面重执行丢失。
   故 `check_versions` 用例 patch `lib.rules.all_laws`/`lib.rules.summary`，
   `check_outdated` 用例 patch `lib.latest.*` 与 `lib.repository.find_python_versions`
   （后者门面以 `from lib.repository import ... find_python_versions` 引入）。
   既有门面测试（直调 `main()`）桩打在门面模块上仍然有效，两类写法并存、各测各的缝。
3. **阈值用 CLI flag 而非 `[tool.coverage] fail_under`**：镜像 python job 现成
   写法（`--cov=netwave --cov-fail-under=100`），阈值在 `package.json` 门面一眼
   可见；pyproject 方案会让阈值对临时手跑 pytest 隐形，且两工程 pyproject 分治
   易漂移。
4. **3 例而非 2 例**：`check_versions` 双向（violations→exit 1、clean→exit 0）
   - `check_outdated` 恒 exit 0。多出的 exit 0 向把闸门通过路径的退出码接线也
     钉住；用例分别进现有门面测试文件（同一 seam 的家），不新建文件。
5. **spec delta 走 ci-matrix 现有 Requirement 加 Scenario**：阈值语义属"治理
   脚本单测如何进 CI"的射程；不新开 Requirement（避免相邻两条裂分），不挂
   铁律七（其射程是四端产码，治理脚本非产码）。
6. **CI 零改动**：lint job 已跑 `pnpm check`；ci-matrix 现有条款禁止第二处
   单测命令/新增 job，阈值进 `check:py` 即自动生效。

## Risks / Trade-offs

- [runpy 重执行门面时 `ROOT` 等模块级常量按真实仓库解析] → 用例全部走桩，
  文件系统扫描函数（`find_uv_projects`/`action_refs`/`find_python_versions`）
  一律替换，不触真仓库；conftest 离线防护兜底。
- [`--cov-fail-under=100` 使未来 versions 域新增代码必须带测试] → 这正是闸门
  目的；结构性不可达行按铁律七逐条 `# pragma: no cover` + 理由，Scenario 已留通道。
- [runpy 用例与既有门面测试看似重复] → 不重复：既有测 `main()` 返回值，
  runpy 测进程退出码接线与守卫行；职责在测试 docstring 写明。

## Migration Plan

正常合入即生效；回滚 = revert 本 change 提交（阈值 flag 与测试同笔，回滚无残留）。
先本地 `pnpm check:py` 绿再 push（LL-004 禁止 push-and-pray）。

## Open Questions

（无。）
