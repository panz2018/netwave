# Spec Delta

## ADDED Requirements

### Requirement: 根级 Python 工具环境

仓库根 MUST 存在 uv 工具工程 `pyproject.toml`（private，不发布）及其
`uv.lock`、`.python-version`，作为全部仓库治理脚本（`scripts/` 闸门与后续
测试）的统一 Python 环境：工具依赖（pytest、pytest-cov、ruff）MUST 在该
工程 dev 组声明并锁死，MUST NOT 依赖开发者全局 Python 所装内容。根工程
MUST NOT 声明 uv workspace 成员；`python/` 维持独立 uv 工程（发布物依赖
故事独立，uv 按就近目录解析互不干扰）。根 `.python-version` 与主工程
`python/.python-version` 同值，随登记表条目纳入对账。

#### Scenario: 门禁脚本经根环境运行

- **WHEN** 在仓库根运行 `uv run python scripts/versions/check_versions.py`
- **THEN** 命令经根 `uv.lock` 锁定的环境执行成功，不要求任何全局安装的
  第三方包

#### Scenario: 发布工程环境独立

- **WHEN** 在 `python/` 目录运行 `uv sync`
- **THEN** 解析到 `python/pyproject.toml` 自身工程（numpy/maturin/pytest
  等发布侧依赖），与根工具工程互不影响

#### Scenario: 根 pin 纳入自登记

- **WHEN** 对账闸门发现式扫描扫到根 `uv.lock` 或根 `.python-version`
- **THEN** 二者已登记为登记表条目（root-uv-lock / root-python / root-requires），
  `pnpm check:meta` 通过；缺登记即 FAIL
