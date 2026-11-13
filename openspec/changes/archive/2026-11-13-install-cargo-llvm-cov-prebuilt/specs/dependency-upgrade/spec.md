# Spec Delta

## MODIFIED Requirements

### Requirement: 升级流程固定顺序

每次升级 MUST 按序执行：全局 CLI 体检（nvm、rustup、node、npm/pnpm、uv、
OpenSpec、markdownlint-cli2 等是否落后 LTS/稳定线，落后先升）→ 工具链升级与
组件/target 补装 → 项目依赖刷新（刷新时按「版本限制记录」跳过已登记版本）→
代码兼容修改 → 全闸门 + 四端对拍 → 文档同步（grep 全仓旧版本号与旧事实）。
配对联动 MUST NOT 以本 spec 散文为凭：依赖间版本关系只认两类依据——上游官方
声明（由包管理器/编译器自身强制，本仓不重复登记）与本仓实测记录
（`scripts/versions/restrictions.json`）。

#### Scenario: 工具链升版后补装

- **WHEN** `rust-toolchain.toml` 升到新钉版
- **THEN** 向新激活工具链补装 rustfmt/clippy 组件与 wasm32-unknown-unknown
  target；cargo-llvm-cov 为 GitHub 预编译 tarball 直装工具
  （`scripts/install_cargo_llvm_cov.sh`），其二进制与工具链版本无关，
  MUST NOT 随工具链升版重装

#### Scenario: GitHub 直装工具落后即重跑安装脚本

- **WHEN** 体检发现已装 wasm-pack / binaryen / cargo-llvm-cov 落后于其
  GitHub 最新 release
- **THEN** 重跑对应 `scripts/install_*.sh` 升级到最新 release

#### Scenario: 无依据的配对规矩不得作为升级约束

- **WHEN** 升级规划需要判断两个依赖是否必须同升
- **THEN** 只认上游官方文档声明或本仓实测记录；两者皆无则视为无约束，
  按各自最新稳定版处理
- **AND** 若事后实测发现不兼容，按「版本限制记录」登记，而非回头补写散文规矩

#### Scenario: 升级完成判据

- **WHEN** 任一工具链或依赖升级执行完毕
- **THEN** `pnpm check` 全绿且 `pnpm check:cross` 四端对拍通过方视为完成
