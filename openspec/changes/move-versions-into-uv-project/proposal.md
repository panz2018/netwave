# Proposal

## Why

`scripts/` 平铺 13 个 py 闸门 + 登记表，版本治理三件套（登记表 +
`check_versions.py` + `check_outdated.py`）与其他闸门混在一层，随配对校验、
黑名单等功能继续膨胀将难以理解、易出错；且门禁脚本寄居 `python/` 的 uv
环境，工具依赖（ruff/pytest）没有独立声明与锁定，环境里装了什么不可控。
建根级 uv 工程并把版本域收进 `scripts/versions/` 包，是后续拆分模块、
补配对校验、立单测体系的地基——本 change 只搬家、不拆刀。

## What Changes

- 仓库根新增 uv 工具工程：`pyproject.toml`（private `netwave-workspace`，
  dev 组 pytest/pytest-cov/ruff）+ `uv.lock` + `.python-version`（与主工程
  同值）。与根 `Cargo.toml`/`package.json` 的 workspace 根模式对称；根工程
  不声明 `[tool.uv.workspace]`，`python/` 维持独立 uv 工程（发布物依赖故事
  独立）。
- **BREAKING**（仓库内部路径）：版本域三件套搬家——
  `scripts/versions.json` → `scripts/versions/lib/registry.json`、
  `scripts/check_versions.py` → `scripts/versions/check_versions.py`、
  `scripts/check_outdated.py` → `scripts/versions/check_outdated.py`。
  脚本内容原样迁移（仅登记表路径常量与文档字符串适配），不拆模块、不加测试。
- 根 `package.json`：`check:meta`/`check:outdated` 改经 `uv run` 指新路径；
  `check:py`/`fix:py` 的 ruff 改走根环境（作用域 python/ scripts/ 不变）；
  `python/pyproject.toml` dev 组删 ruff（归根环境统一，消除双钉）。
- CI lint job：`pnpm check` 前加 `uv sync --locked`（断言根 lock 新鲜并预建
  环境）。
- 登记表自登记三条：`root-python`、`root-requires`、`root-uv-lock`——自家
  发现式扫描会扫到根 pin 文件，不登记 `check:meta` 当场 FAIL（版本闸门管到
  自己头上）。
- 文档同步：新建 `scripts/versions/README.md`（本域功能 + 跑法）、
  `scripts/README.md` 加指针、AGENTS.md/CONTRIBUTING.md 旧路径更新、
  Plan/ 相关文档路径与状态更新。

## Capabilities

### New Capabilities

（无——本 change 是结构搬家，不引入新系统行为。）

### Modified Capabilities

- `workspace-layout`：平铺 monorepo 结构补"根级 Python 工具环境"
  （`pyproject.toml`/`uv.lock`/`.python-version`，private 不发布；
  `python/` 保持独立工程）。
- `dependency-upgrade`：登记表与双向对账闸门的钉死路径更新
  （`scripts/versions/lib/registry.json`、`scripts/versions/check_versions.py`）。
- `ci-matrix`：语言矩阵数字的登记表路径引用更新。

## Impact

- 工具：`scripts/versions/`（新包目录：README + 两门面 + `lib/registry.json`）、
  根 `pyproject.toml`/`uv.lock`/`.python-version`。
- 配置：根 `package.json`（check:meta/check:outdated/check:py/fix:py）、
  `python/pyproject.toml`（dev 组删 ruff）、`.github/workflows/ci.yml`
  （lint job 加 uv sync）。
- 文档：AGENTS.md、CONTRIBUTING.md、scripts/README.md、
  scripts/versions/README.md（新建）、Plan/scripts-versions包化.md、
  Plan/测试规划.md、Plan/配对版本校验.md。
- 不涉及：core/绑定数值代码、oracle、`python/` uv 工程本体（除删 ruff）、
  其余 11 个平铺闸门（维持现状，后续按同模式逐域收编）。

## Non-goals

- 不拆分库模块（registry/semver/values/pairs/blocked/freshness 留后续 change）。
- 不加单元测试与覆盖率门槛（后续 change）。
- 不实现配对版本校验（`pairs`）与补 reader（后续 change，见
  Plan/配对版本校验.md）。
- 不动其余平铺闸门位置、不改 `scripts/` 目录名（scripts治理 问题三维持）。
- 不改任何数值行为、容差、公开 API。
- 不恢复/改动暂停中的 `upgrade-python-3-15`（其旧路径引用随恢复时更新）。
