# Tasks

## 1. 回归基线与 red 夹具

- [ ] 1.1 留回归基线：`uv run python scripts/versions/check_versions.py > /tmp/cv_base.txt`、`uv run python scripts/versions/check_outdated.py > /tmp/co_base.txt`（当前两闸门全绿输出存档，供后续逐行对比）
- [ ] 1.2 red：在临时目录造夹具——缺 `rust-version` 的 `Cargo.toml`、缺 `.python-version` 的 `pyproject.toml`（含 `[project]` 与 `requires-python`），以夹具仓库运行 `check_versions.py`，断言第 2 律（pyproject → 同目录 `.python-version`）FAIL 并点名该目录（当前代码无此律，预期失败即 red 成立）

## 2. check_versions.py 改造（规则驱动闸门）

- [ ] 2.1 green：实现第 2 律（扫描含 `[project]` 的 `pyproject.toml`，断言声明 `requires-python` 且同目录存在 `.python-version`），使 1.2 夹具 FAIL、真实仓库 PASS
- [ ] 2.2 删除登记表相关代码：check #1（结构/categories/paired_with/blocked 校验）、#1b（黑名单）、#2（pin_location 存在性）、#6（发现式完整性）及 `REGISTRY`、`REQUIRED_FIELDS`、`DISCOVERED_RULES`、`discovered_locations`、`current_values`、`locations`、`EXACT_VERSION`、`parse_ver` 中仅服务登记表的部分；docstring 改写为规则驱动四律描述
- [ ] 2.3 验证：`uv run python scripts/versions/check_versions.py` 输出与 `/tmp/cv_base.txt` 除新增第 2 律外逐行一致且退出码 0；再跑 1.2 夹具确认两律均 FAIL

## 3. check_outdated.py 瘦身（纯发现式体检）

- [ ] 3.1 删除 blocked 消费链：`load_blocked`、`blocked_target`、`PROBE_TO_ENTRY`、`BlockedMap`、`REGISTRY`、`locations` 及各调用点，target 直接取最新稳定版；`PROBES` 探针集保留为程序常量；docstring 同步（去掉 blocked/registry 描述）
- [ ] 3.2 验证：`uv run python scripts/versions/check_outdated.py` 输出与 `/tmp/co_base.txt` 一致（blocked 段本为空）、退出码 0；`grep -n "blocked\|registry" scripts/versions/check_outdated.py` 零命中

## 4. 登记表退役

- [ ] 4.1 `git rm scripts/versions/lib/registry.json`（`lib/` 目录随之消失）；验证：`pnpm check:meta` 全绿（`check_versions.py` 不再引用该路径）

## 5. 文档指针同步（波及面改全）

- [ ] 5.1 `scripts/versions/README.md` 整篇重写：域使命="规则驱动一致性闸门 + 联网体检"，Layout 表去掉 registry.json 行，Usage 命令不变
- [ ] 5.2 同步 `AGENTS.md`（依赖版本策略节指针）、`CONTRIBUTING.md`（:79/:89/:91 登记表表述）、`scripts/README.md:19`（versions/ 行描述）——真相源声称改为"钉版文件本身 + 规则闸门"
- [ ] 5.3 验证：`grep -rn "registry.json" --include="*.md" --include="*.py" . | grep -v openspec/changes/archive | grep -v openspec/changes/retire-pin-registry` 零命中（本 change 工件内引用历史描述除外）

## 6. Plan 收尾与全闸门

- [ ] 6.1 `Plan/软件升级.md`：删除已吸收章节（登记表 schema 重构、配对版本校验已定部分、scripts/versions 拆包旧版），保留待议块（闸门拆分+`scripts/tests/` 接线、pairs JSON 化待触发、过期门禁化、scripts 治理三问、py3.15），文首状态行同步改写
- [ ] 6.2 `Plan/测试规划.md`：删 `:295` registry 相关行（oracle pin 条目、check_versions 补对齐规则行），保留 oracle uv/python 环境落地计划
- [ ] 6.3 验证：`pnpm check:md` 退出码 0
- [ ] 6.4 全闸门收口：`pnpm check` 全绿 + `pnpm check:cross` 四端对拍通过（本 change 不动产品代码，预期与基线无差异）；按 apply 指引扫 `openspec/specs/` 输出三态时效结论（更新=dependency-upgrade/ci-matrix，新增=无，退役=无）留痕本文件

## Workflow follow-up

- 归档（`/opsx:archive`）时：openspec 将 delta 合入主 spec；归档前执行 Plan/ 瘦身检查与 specs 三态时效检查（openspec/config.yaml operations.archive）
- `specs/README.md` 路由摘要随主 spec 措辞更新（dependency-upgrade 行去掉"登记表"字样）
- 提交分组建议：①闸门代码（组 2/3/4）②文档指针（组 5）③Plan 收尾（组 6）三笔，等人工点名后提交
