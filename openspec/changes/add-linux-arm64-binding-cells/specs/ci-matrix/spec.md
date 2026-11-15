# Spec Delta

## MODIFIED Requirements

### Requirement: 语言版本矩阵

语言版本轴与硬件平台轴是两个正交维度，须分别覆盖：

- **语言版本轴**（主 runner ubuntu 上跑底线 + 最新两格）：python job 跑
  Python 底线版与最新稳定版两格；node job 跑 Node 底线 LTS 与最新 LTS 两格。
  具体版本号 MUST 取自承载它们的钉版文件（`.github/workflows/ci.yml` 矩阵格、
  `python/.python-version`、`typescript/package.json` 的 `engines.node`），
  一致性由 `dependency-upgrade` spec 的规则驱动闸门校验，本 spec 不写死数字。
- **硬件平台轴**（各 OS 跑最新语言版本，验平台 ABI 而非版本 spread）：
  python/node job 另在 windows-latest、macos-latest 与 linux-arm64
  （`ubuntu-26.04-arm`）各跑最新一格，验证 `.so`/`.pyd`/`.dylib`/`.node`
  addon 与零拷贝 base object 的平台 ABI；linux-arm64 格验证 aarch64 ABI。

Rust MUST 只跑单一 stable（`rust-toolchain.toml` 钉死当前 stable）——
消费者自带 toolchain 编译，`rust-version` 由 cargo 自动检查。

#### Scenario: python/node 版本格 + 平台格

- **WHEN** PR 触发 `ci.yml`
- **THEN** python job 在 ubuntu 含 `python/.python-version` 所指底线与
  最新稳定两格、node job 在 ubuntu 含 `engines.node` 所指底线与最新 LTS
  两格；两者另在 windows/macos/linux-arm64 各跑最新一格验 ABI，全部通过
  方可合并

#### Scenario: 矩阵数字单源

- **WHEN** 语言矩阵的版本号变更（如新 LTS 转换、新稳定 minor 落地）
- **THEN** 数字只改 `ci.yml` 矩阵格与对应底线声明文件，本 spec 措辞
  不随版本号变化

<!-- 「覆盖率门槛生效（铁律七）」无行为变更，不列 delta；其 Scenario 标题
「胶水行未测即红（地板启用后）」的括号限定语指向本 change 删除的标定机制，
属主 spec 直接清理，见 tasks 2.1。 -->

## REMOVED Requirements

### Requirement: 覆盖率地板两阶段标定

**Reason**: 标定机制是覆盖率门槛从缺省到 100 的一次性过渡过程，全部代码域
已完成收口、地板恒为 100；过渡机制不再约束任何后续改动，新平台格直接沿用
现行门槛。

**Migration**: 无迁移动作——所有阅卷命令的地板参数已是 100，删除本条不改变
任何现行 CI 行为；后续新增矩阵格按「覆盖率门槛生效（铁律七）」以 100 执行。
