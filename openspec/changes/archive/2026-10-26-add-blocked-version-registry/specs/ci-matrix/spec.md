# Spec Delta

## MODIFIED Requirements

### Requirement: 语言版本矩阵

语言版本轴与硬件平台轴是两个正交维度，须分别覆盖：

- **语言版本轴**（主 runner ubuntu 上跑底线 + 最新两格）：python job 跑
  Python 底线版与最新稳定版两格；node job 跑 Node 底线 LTS 与最新 LTS 两格。
  具体版本号 MUST 取自 `dependency-upgrade` spec 的钉死点登记表
  （`scripts/versions.json`），本 spec 不写死数字。
- **硬件平台轴**（各 OS 跑最新语言版本，验平台 ABI 而非版本 spread）：
  python/node job 另在 windows-latest 与 macos-latest 各跑最新一格，
  验证 `.so`/`.pyd`/`.dylib`/`.node` addon 与零拷贝 base object 的平台 ABI。

Rust MUST 只跑单一 stable（`rust-toolchain.toml` 钉死当前 stable）——
消费者自带 toolchain 编译，`rust-version` 由 cargo 自动检查。

#### Scenario: python/node 版本格 + 平台格

- **WHEN** PR 触发 `ci.yml`
- **THEN** python job 在 ubuntu 含登记表指定的底线与最新稳定两格、node job
  在 ubuntu 含登记表指定的两格 LTS；两者另在 windows/macos 各跑最新一格
  验 ABI，全部通过方可合并

#### Scenario: 矩阵数字单源

- **WHEN** 语言矩阵的版本号变更（如新 LTS 转换、新稳定 minor 落地）
- **THEN** 数字只改登记表与 `ci.yml`，本 spec 措辞不随版本号变化
