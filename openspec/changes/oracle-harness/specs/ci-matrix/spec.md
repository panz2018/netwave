# ci-matrix Specification Delta

## MODIFIED Requirements

### Requirement: 主 CI 零 Python 运行时依赖

`ci.yml` 的构建/测试 job MUST NOT 安装或调用 scikit-rf；Python 仅出现在
`python/` 绑定自身的测试 job（pytest 读 `oracle/samples/`）。golden 生成
（`oracle/gen_golden.py`，oracle 的 uv 环境钉版 skrf）另行立项，不在本变更；
落地后 skrf 亦只出现在 oracle 阅卷步骤，各端构建/测试步骤保持零 skrf。

#### Scenario: ci.yml 无 skrf

- **WHEN** 检查 `.github/workflows/ci.yml`
- **THEN** 无任何 `pip install scikit-rf` / `uv add scikit-rf` 步骤
