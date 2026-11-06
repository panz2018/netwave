# Spec Delta

## ADDED Requirements

### Requirement: 治理脚本单测进 CI

CI MUST 运行治理脚本单测（`scripts/tests/`，命令细节唯一定义在根
`package.json` 的 `check:py`），使 `scripts/` 闸门的回归由 CI 兜底；
lint job MUST 经 `pnpm check` 覆盖该单测，MUST NOT 在 `pnpm check` 之外
重复跑单测命令（命令唯一真相源），MUST NOT 新增独立 job 或重复环境
准备，MUST NOT 引入联网测试（联网一致性验证为本地一次性基线，见
workspace-layout「根级 Python 工具环境」）。

#### Scenario: 闸门回归 CI 兜底

- **WHEN** 任一 PR 改动 `scripts/` 且使治理脚本单测失败
- **THEN** lint job FAIL 并指向失败用例——闸门脚本的回归不能只靠本地

#### Scenario: 不重复命令真相源

- **WHEN** 查看 lint job 步骤序列
- **THEN** 单测仅经 `pnpm check`（内含 `check:py`）运行一次，
  ci.yml 不出现第二处单测命令
