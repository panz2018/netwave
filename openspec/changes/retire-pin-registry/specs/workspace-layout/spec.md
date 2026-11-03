# Spec Delta

## MODIFIED Requirements

### Requirement: 根级 Python 工具环境

仓库根 MUST 存在 uv 工具工程 `pyproject.toml`（private，不发布）及其
`uv.lock`、`.python-version`，作为全部仓库治理脚本（`scripts/` 闸门与后续
测试）的统一 Python 环境：工具依赖（pytest、pytest-cov、ruff）MUST 在该
工程 dev 组声明并锁死，MUST NOT 依赖开发者全局 Python 所装内容。根工程
MUST NOT 声明 uv workspace 成员；`python/` 维持独立 uv 工程（发布物依赖
故事独立，uv 按就近目录解析互不干扰）。根 `.python-version` 与主工程
`python/.python-version` 同值，由规则驱动闸门自动纳入覆盖，无需登记。

#### Scenario: 门禁脚本经根环境运行

- **WHEN** 在仓库根运行 `uv run python scripts/versions/check_versions.py`
- **THEN** 命令经根 `uv.lock` 锁定的环境执行成功，不要求任何全局安装的
  第三方包

#### Scenario: 发布工程环境独立

- **WHEN** 在 `python/` 目录运行 `uv sync`
- **THEN** 解析到 `python/pyproject.toml` 自身工程（numpy/maturin/pytest
  等发布侧依赖），与根工具工程互不影响

#### Scenario: 根 pin 由四律自动覆盖

- **WHEN** 规则驱动闸门扫描仓库 manifest
- **THEN** 根 `.python-version` 受矩阵覆盖律约束（值 MUST 出现在 CI python
  矩阵格中）、根 `pyproject.toml` 的 `[project]` 受 Python 工程律约束
  （`requires-python` + 同目录 `.python-version`），漏声明当场 FAIL——
  登记表退役后无任何登记环节
