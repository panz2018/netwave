# ci-matrix Specification Delta

## MODIFIED Requirements

### Requirement: 治理脚本单测进 CI

CI MUST 运行治理脚本单测（`scripts/tests/`，命令细节唯一定义在根
`package.json` 的 `check:py`），使 `scripts/` 闸门的回归由 CI 兜底；
lint job MUST 经 `pnpm check` 覆盖该单测，MUST NOT 在 `pnpm check` 之外
重复跑单测命令（命令唯一真相源），MUST NOT 新增独立 job 或重复环境
准备，MUST NOT 引入联网测试（联网一致性验证为本地一次性基线，见
workspace-layout「根级 Python 工具环境」）。

覆盖率的范围与阈值 MUST 定义在根 `pyproject.toml` 的 `[tool.coverage]`
与 `[tool.pytest.ini_options]`（单一真相源），`check:py` 命令行 MUST NOT
再携带 `--cov=` 范围或 `--cov-fail-under=` 阈值——范围列于命令行属易漏
清单，改测试域时须同步改命令与 CI，漂移即失效。行覆盖率地板范围 =
`scripts/versions` 域 + `scripts/coverage_gate.py` + `scripts/check_comments.py`
三者，阈值数值以 `pyproject.toml` 为唯一定义处（散文不复制数字）；
范围外的 `scripts/` 其余脚本暂不设地板。

#### Scenario: 闸门回归 CI 兜底

- **WHEN** 任一 PR 改动 `scripts/` 且使治理脚本单测失败
- **THEN** lint job FAIL 并指向失败用例——闸门脚本的回归不能只靠本地

#### Scenario: 不重复命令真相源

- **WHEN** 查看 lint job 步骤序列
- **THEN** 单测仅经 `pnpm check`（内含 `check:py`）运行一次，
  ci.yml 不出现第二处单测命令

#### Scenario: versions 域覆盖率地板生效

- **WHEN** `scripts/versions` 域行覆盖率低于 `pyproject.toml` 所钉
  `fail_under` 阈值（含新增未测行、也含删除既有覆盖用例）
- **THEN** `pnpm check:py` 退出码非 0，lint job FAIL——覆盖率不得
  无声下滑；结构性不可达行如需豁免，按铁律七逐条标注并附理由

#### Scenario: 阅卷人与门禁脚本覆盖率地板生效

- **WHEN** `scripts/coverage_gate.py` 或 `scripts/check_comments.py` 出现
  未测行（新增分支、或删除既有覆盖用例）
- **THEN** `pnpm check:py` 退出码非 0，lint job FAIL——阅卷人回归 =
  全部覆盖率地板失效，门禁脚本回归 = 该门禁静默失效，两者必须有测试兜底

#### Scenario: 覆盖率配置单一真相源

- **WHEN** 查看根 `package.json` 的 `check:py` 命令
- **THEN** 其中不含 `--cov=` 或 `--cov-fail-under=`——范围与阈值只在
  `pyproject.toml` 声明一处；命令行与配置文件两处并存即 review 打回
  （两份清单必漂移）
