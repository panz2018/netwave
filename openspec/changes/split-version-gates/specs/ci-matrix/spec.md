# Spec Delta

## ADDED Requirements

### Requirement: 治理脚本单测进 CI

CI MUST 在既有 lint job（已含根 uv 工具环境 `uv sync --locked` 步骤）内
运行治理脚本单测 `uv run pytest scripts/tests`，使 `scripts/` 闸门的
回归由 CI 兜底；该步骤 MUST NOT 新增独立 job 或重复环境准备，MUST NOT
引入联网测试（联网一致性验证为本地一次性基线，见 workspace-layout
「根级 Python 工具环境」）。

#### Scenario: 闸门回归 CI 兜底

- **WHEN** 任一 PR 改动 `scripts/` 且使治理脚本单测失败
- **THEN** lint job FAIL 并指向失败用例——闸门脚本的回归不能只靠本地

#### Scenario: 不新增环境准备

- **WHEN** 查看 lint job 步骤序列
- **THEN** 单测步骤紧随既有 `uv sync --locked`，无第二次 uv 环境安装
