# dependency-upgrade Delta Spec

## MODIFIED Requirements

### Requirement: 升级执行权限划分

升级分两类：**上限升级**（lockfile 依赖刷新含 major、工具链与运行时
钉版切换、CI 矩阵最新格、直装工具、全局 CLI、CI actions）MUST 由
agent 直接执行，MUST NOT 要求开 OpenSpec change；验收按触及面选闸门
（见「按触及面选验收闸门」），实测失败按「版本限制记录与坏版本降级」
回退并当轮登记。**下限变更**（MSRV `rust-version`、`engines.node`、
CI 底线矩阵格、新增/移除钉版点）由人工发起，agent MUST NOT 自动执行。
有自动生效仓库钉版者以钉版为准升级，其余在本机执行、回退靠重装
（机制见各 scenario）。追溯靠 git log，坏版本事实靠
`scripts/versions/restrictions.json`（仓库内组合）与账本（机器级工具）。

#### Scenario: 上限升级直接执行不开 change

- **WHEN** 体检报出任一上限 LAG（lockfile、钉版、矩阵最新格、工具）
- **THEN** agent 直接执行升级 + 全闸门 + 四端对拍，不开 OpenSpec change，
  提交信息注明升级内容与体检出处

#### Scenario: 无仓库钉版的全局 CLI 与直装工具机器级升级

- **WHEN** 体检报出无仓库钉版的全局 CLI 或 GitHub 压缩包直装工具落后
  （npm、openspec、uv、rustup、wasm-pack、binaryen、cargo-llvm-cov 等）
- **THEN** agent 在本机直接升级到最新（`npm install -g` / `cargo install`
  / 重下 tarball），不停下等点名；实测坏则重装回退到上一可用版并当轮
  记账本

#### Scenario: node 升级保打开即用

- **WHEN** 体检报出 node 落后（node 无自动生效的仓库钉版，当前版本以
  机器 `node --version` 为准）
- **THEN** agent 执行 `nvm install <最新> --reinstall-packages-from=<旧版>`
  并 `nvm alias default <最新>`，使新终端打开即用最新版且全局 npm 包
  （openspec、markdownlint-cli2 等）随版本迁移不丢失；仅 install 不
  alias、或不带 `--reinstall-packages-from` 均不算升级完成

#### Scenario: 自动生效钉版的 CLI 以钉版为准

- **WHEN** 体检报出的 CLI 在仓库有自动生效的钉版（pnpm
  `packageManager` 由 corepack 读、rustc `rust-toolchain.toml` 由 rustup
  读）
- **THEN** 其当前版本以仓库钉版为准（非机器全局安装版），升级 =
  改仓库钉版文件（进 git、跨机器一致）而非重装全局；机器 active
  版本与钉版不一致时向钉版对齐

#### Scenario: 按触及面选验收闸门

- **WHEN** 升级一项依赖/工具后确定验收范围
- **THEN** 触及四端绑定或数值路径者跑 `pnpm check` + `pnpm test:cross`
  四端对拍；纯 lint/文档/CLI 工具（不碰绑定与数值）只跑 `pnpm check`，
  不跑 `test:cross`

#### Scenario: 下限变更人工发起

- **WHEN** MSRV、`engines.node` 或 CI 底线矩阵格需要抬升（如旧底线 EOL）
- **THEN** 由人工点名发起，agent 不自动执行；发起后的执行仍按本 spec
  升级流程验收

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
- **THEN** `pnpm check` 全绿且 `pnpm test:cross` 四端对拍通过方视为完成
