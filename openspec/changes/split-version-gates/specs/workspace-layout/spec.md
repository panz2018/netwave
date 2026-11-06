# Spec Delta

## ADDED Requirements

### Requirement: 治理脚本分层

`scripts/versions/` MUST 按三层组织：门面（`check_versions.py`、
`check_outdated.py`）、共享库（`lib/` 包）、单测（`scripts/tests/`）。
门面 MUST 只做输入组装、检查集选择与退出码汇总；跨门面共用的仓库扫描、
钉版提取与版本解析比较 MUST 收进 `lib/` 且全仓仅此一份；只被单个门面
使用的联网探测逻辑亦 MUST 进 `lib/`，不与门面并列平铺。共享库 MUST 以
`Path(__file__)` 定位仓库根，MUST NOT 依赖调用方 cwd。

#### Scenario: 跳过目录集合单一来源

- **WHEN** 任一门面或共享库扫描仓库文件
- **THEN** 其排除目录集合取自 `lib/` 的单一常量，仓库内不存在第二份
  跳过目录清单

#### Scenario: 版本比较语义唯一

- **WHEN** 任一工具需要比较两个版本号大小或判断精确钉版
- **THEN** 判定取自 `lib/` 的统一实现（缺失补丁位按 0 补齐后比较），
  仓库内不存在第二套版本解析/比较实现

#### Scenario: 门面保持薄聚合

- **WHEN** 新增一条版本规则或体检段
- **THEN** 判定逻辑进 `lib/`，门面只增加"选入检查集 + 汇总"的接线，
  不在门面内内联规则判定

## MODIFIED Requirements

### Requirement: 根级 Python 工具环境

仓库根 MUST 存在 uv 工具工程 `pyproject.toml`（private，不发布）及其
`uv.lock`、`.python-version`，作为全部仓库治理脚本（`scripts/` 闸门与
治理脚本单测）的统一 Python 环境：工具依赖（pytest、pytest-cov、ruff）
MUST 在该工程 dev 组声明并锁死，MUST NOT 依赖开发者全局 Python 所装
内容。根工程 MUST NOT 声明 uv workspace 成员；`python/` 维持独立 uv 工程
（发布物依赖故事独立，uv 按就近目录解析互不干扰）。根 `.python-version`
与主工程 `python/.python-version` 同值，由规则驱动闸门自动纳入覆盖，
无需登记。治理脚本单测 MUST 置于 `scripts/tests/`，其运行配置（含使
`scripts/versions/lib` 可导入的 pytest pythonpath）MUST 落在根工程
`pyproject.toml`；单测 MUST NOT 联网，联网输出的一致性验证由一次性
临时基线承担，基线文件 MUST NOT 入库。

#### Scenario: 门禁脚本经根环境运行

- **WHEN** 在仓库根运行 `uv run python scripts/versions/check_versions.py`
- **THEN** 命令经根 `uv.lock` 锁定的环境执行成功，不要求任何全局安装的
  第三方包

#### Scenario: 发布工程环境独立

- **WHEN** 在 `python/` 目录运行 `uv sync`
- **THEN** 解析到 `python/pyproject.toml` 自身工程（numpy/maturin/pytest
  等发布侧依赖），与根工具工程互不影响

#### Scenario: 根 pin 由四律自动覆盖

<!-- 标题保留旧名：openspec MODIFIED 校验要求复制既有 Scenario 标题，
     不支持场景改名；归档后随 tasks「Workflow follow-up」把主 spec 此标题
     改为「根 Python 钉版由四律自动覆盖」（全仓无锚点引用，已 grep 核实）。 -->

- **WHEN** 规则驱动闸门扫描仓库 manifest
- **THEN** 根 `.python-version` 受矩阵覆盖律约束（值 MUST 出现在 CI python
  矩阵格中）、根 `pyproject.toml` 的 `[project]` 受 Python 工程律约束
  （`requires-python` + 同目录 `.python-version`），漏声明当场 FAIL——
  登记表退役后无任何登记环节

#### Scenario: 治理脚本单测离线可跑

- **WHEN** 在无网络环境执行 `uv run pytest scripts/tests`
- **THEN** 全部用例成功（纯逻辑夹具，无网络请求、无子进程依赖外部网络）

#### Scenario: 单测挂进 Python 闸门

- **WHEN** 运行 `pnpm check:py`
- **THEN** ruff lint/format 检查之后自动运行 `uv run pytest scripts/tests`，
  任一用例失败即该命令 FAIL
