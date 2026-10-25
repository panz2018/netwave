# Spec Delta

## MODIFIED Requirements

### Requirement: 钉死点登记表唯一真相源

仓库全部版本钉死点 MUST 登记在机器可读登记表 `scripts/version_pins.json`，
它是"版本钉在哪"的唯一真相源；散文文档 MUST NOT 复制登记表内容。
类别覆盖：Rust 工具链 pin 与 MSRV、CI 语言矩阵数字、包管理器 pin、
lockfile、GitHub 压缩包直装工具（wasm-pack、binaryen）、cargo 子命令、
全局 CLI 检查项、CI actions、Playwright 浏览器、oracle 环境 pin。

#### Scenario: 登记条目结构完整

- **WHEN** 校验登记表任一条目
- **THEN** 条目含：名称、类别、钉版位置（文件路径、`machine:` 安装位置，
  或 `discovered:` 发现规则——位置由闸门发现扫描提供，条目 MUST NOT
  手抄文件清单）、升级方法、配对约束（若有）
- **AND** 散文文档以链接或"当前稳定版"措辞引用，不复制具体版本号

### Requirement: 双向对账闸门

`scripts/check_version_pins.py` MUST 双向对账登记表与真实文件：每个登记条目
对应真实存在的钉版位置（`machine:` 条目只查登记存在；`discovered:` 条目的
位置即发现规则本身）；仓库内每个钉版点都出现在登记表中；一致性规则
（每个 workspace 成员 `Cargo.toml` 必须携带 `rust-version` 且全部彼此一致、
`rust-version` 不高于 `rust-toolchain.toml` pin 的 major.minor、
`packageManager` 为精确版本）任一不满足即 FAIL。
闸门 MUST 接进根 `check:meta`。

#### Scenario: 手动升版漂移当场暴露

- **WHEN** `rust-toolchain.toml` 升到新 stable 而某 `Cargo.toml` 的
  `rust-version` 仍是旧值
- **THEN** 闸门 FAIL 并指出具体文件与期望值

#### Scenario: 成员丢 MSRV 钉静默逃逸

- **WHEN** 某 workspace 成员的 `Cargo.toml` 删掉了 `rust-version` 字段
- **THEN** 闸门 FAIL 并指出该成员——删字段不能逃逸对账

#### Scenario: 登记表条目指向不存在的位置

- **WHEN** 登记条目所指钉版位置在仓库或环境中不存在
- **THEN** 闸门 FAIL，报登记表漂移
