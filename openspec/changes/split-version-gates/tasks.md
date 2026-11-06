# Tasks

## 1. 回归基线（拆前锁定）

- [x] 1.1 拆包前跑两门面存一次性基线：`uv run python scripts/versions/check_versions.py > /tmp/baseline_before_versions.txt`；`uv run python scripts/versions/check_outdated.py > /tmp/baseline_before_outdated.txt`。验证：两文件存在且非空，退出码 0/0；基线文件不入库。

## 2. 共享库与单测（red 先于 green）

- [x] 2.1 建 `scripts/versions/lib/`（含 `__init__.py`）与 `scripts/tests/` 骨架；根 `pyproject.toml` 加 `[tool.pytest.ini_options] pythonpath = ["scripts/versions"]`。验证：`uv run pytest scripts/tests` 可运行（空收集 exit 5 或 0 均视为骨架通）。
- [x] 2.2 red：写 `scripts/tests/test_version.py`——`parse_version` 补齐三元组（`1.85` == `1.85.0`）、`v` 前缀、`is_exact`、`is_major_only`、`is_outdated` 正反用例；`scripts/tests/test_rules.py`——四律各造 tmp 夹具仓库（缺 `rust-version`、缺 `.python-version`、packageManager 漂移、`.python-version` 不在 CI 矩阵）断言返回对应 `::error::` 文案片段。验证：`uv run pytest scripts/tests` FAIL（模块未实现，red）。
- [x] 2.3 green：实现 `lib/version.py`（`parse_version`/`is_exact`/`is_major_only`/`is_outdated`，补齐语义见 design.md「版本比较统一为补齐语义」）与
      `lib/repository.py`（`ROOT`/`SKIP_DIRS`/`find_files`/`find_python_versions`/`find_ci_workflows`/`workspace_members`/`is_python_project`，`Path(__file__)` 定位）。验证：`uv run pytest scripts/tests/test_version.py` PASS。
- [x] 2.4 green：实现 `lib/rules.py` 四函数（`check_rust_version`/`check_python_projects`/`check_package_manager`/`check_ci_python_versions`，各返回 `errors: list[str]`，错误文案与现 `check_versions.py` 逐字一致）。验证：`uv run pytest scripts/tests` 全 PASS。
- [x] 2.5 实现 `lib/latest.py`（`fetch_json`/`run_cmd`/`first_line`/`latest_version`，自 `check_outdated.py` 原样搬移；`SKIP_DIRS` 改用 `repository` 单一来源，即 design.md
      「SKIP_DIRS 统一为单一来源」修复项）。验证：`uv run ruff check scripts/` 与 `uv run ruff format --check scripts/` 退出 0。

## 3. 门面重写为薄聚合

- [x] 3.1 重写 `check_versions.py`：只 import `lib.rules` 选四律、汇总 `::error::`、退出码 0/1；输出字符串与旧版逐字一致（含通过摘要行）。验证：与 `/tmp/baseline_before_versions.txt` diff 为空。
- [x] 3.2 重写 `check_outdated.py`：四段组装改用 `lib.latest`/`lib.repository`；`PROBES` 与 `section` 留门面。验证：与 `/tmp/baseline_before_outdated.txt` diff 为空或仅 latest 数值行时间性差异（比对规则见 design.md「单测与回归基线」），结论记 PR 描述。

## 4. 命令与 CI 接线

- [x] 4.1 根 `package.json`：`check:py` 追加 `&& uv run pytest scripts/tests`（ruff 之后）。验证：`pnpm check:py` 全绿且输出含 pytest 通过行。
- [x] 4.2 `.github/workflows/ci.yml`：lint job 经 `pnpm check`（内含
      `check:py`）跑治理脚本单测，不另加独立 pytest 步骤（命令唯一真相源
      在根 `package.json`）。验证：ci.yml 无第二处单测命令；本地
      `pnpm check:py` 成功（LL-004）。

## 5. 文档与账本同步

- [x] 5.1 `scripts/versions/README.md`：补模块地图（design.md「目录与模块划分」「函数命名终表」）与退出码
      契约（design.md「退出码契约」）。验证：`pnpm check:md` 退出 0；README 无旧文件名残留（grep `semver.py|freshness.py` 零命中）。
- [x] 5.2 `AGENTS.md`「通用原则 · 简洁优先」加"命名一眼懂"一行（措辞见 design.md「AGENTS.md 命名规则」，附出处
      本 change）。验证：`pnpm check:md` 退出 0。
- [x] 5.3 `Plan/软件升级.md`：目标结构图更新为 design.md
      「目录与模块划分」「函数命名终表」；记入"scripts 覆盖率暂不进 coverage_gate（先报数，阈值待触发）"。验证：`pnpm check:md` 退出 0。
- [x] 5.4 账本 `openspec/specs/lessons-learned/`：ci（或 workflow）分片新增 LL——同一知识两份清单必漂移（SKIP_DIRS/版本比较双实现实例），INDEX 加行。验证：`pnpm check:md` 退出 0，INDEX 与分片编号一致。

## 6. 全闸门验收

- [x] 6.1 全仓 grep 旧符号（`parse_ver|_semver|has_project|discover\(`）确认 `scripts/` 零残留；跑 `pnpm check` 全绿 + `pnpm check:meta` 含新路径成功。验证：grep 零命中、两命令退出 0。
- [x] 6.2 联网体检手动跑一遍 `pnpm check:outdated`，四段齐全、恒退出 0。验证：输出含四段标题与 done 行，exit 0。

## Workflow follow-up

- sync/archive 后把主 spec `workspace-layout` 场景标题「根 pin 由四律自动
  覆盖」改为「根 Python 钉版由四律自动覆盖」（openspec MODIFIED 校验不
  支持场景改名，只能归档后手改；全仓无锚点引用，已 grep 核实），改后跑
  `pnpm check:md`。
- apply 完成前按 config.yaml apply 指引：删除 `Plan/软件升级.md` 中本 change
  已完成章节（闸门拆分与测试接线整节），只留未执行项（blocked、pairs、
  过期门禁化、scripts 治理三问、py3.15、覆盖率阈值待触发），删后跑
  `pnpm check:md`。
- 归档前扫 `openspec/specs/` 做三态时效检查（workspace-layout/ci-matrix
  delta 同步、README 路由核对），结论留痕。
