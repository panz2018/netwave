# Proposal

## Why

升级目前无章可循：版本钉死点散落在 `rust-toolchain.toml`、四个 `Cargo.toml`、
`packageManager`、两份 lockfile、CI actions、安装脚本等十余处，升一次 Rust 要手动
改一堆地方，已经出现过手动升版后 `rust-version`/spec 数字滞后于 pin 的漂移。
升级策略本身也散在 AGENTS.md、CONTRIBUTING.md、两份 spec 里，互相重叠且有矛盾
（回退原因既说记子项目 README 又说只记账本）。需要把"升级"这件事收敛成一份
可复用、可门禁、可持续改进的 spec。

## What Changes

- 新增 `dependency-upgrade` capability：升级总策略（最新稳定版优先、证实上游 bug
  才退次新版）、选线原则（多线运行时钉 LTS/稳定线）、登记原则（新工具/库引入必须
  同笔登记升级方法）、钉死点登记表（机器可读 JSON 为唯一真相源）、双向对账闸门、
  升级分级（结构性升级走 OpenSpec change / 例行刷新走普通 PR）、固定升级流程、
  经验回写规则。
- 新增 `scripts/version_pins.json`（登记表）与 `scripts/check_version_pins.py`
  （双向对账闸门，接进根 `check:meta`）；新增 `scripts/check_outdated.py` +
  根 `pnpm check:outdated`（体检四段：项目依赖 + 全局 CLI + GitHub 压缩包直装
  工具与 cargo 子命令 + CI actions，人工触发不进 CI）。
- 迁入并原地删除：AGENTS.md「依赖版本策略」节、CONTRIBUTING.md
  「Toolchain freshness」节 → 新 spec，原地留一行指针。
- 版本条款集中：`workspace-layout` 的「版本底线」Requirement 整体迁入新 spec
  （原处 REMOVED）；`ci-matrix` 的「语言版本矩阵」去掉写死的版本号，数字改由
  新 spec 的登记表持有（MODIFIED）。
- 落地本 spec 的第一批升级：Rust MSRV 收尾（四处 `rust-version` 1.98→1.99，
  对齐已升的 pin 1.99.1）；TypeScript 7 兼容性重测（tsdown dts × TS7，兼容则
  维持最新稳定版，不兼容则钉 6 并记账本）。

## Capabilities

### New Capabilities

- `dependency-upgrade`: 工具链与依赖升级的策略、钉死点登记、对账闸门、升级流程与
  经验回写契约。

### Modified Capabilities

- `workspace-layout`: 「版本底线」Requirement 移除——版本数字的唯一真相源迁至
  `dependency-upgrade` spec 的登记表，本 spec 回归纯目录/发布结构。
- `ci-matrix`: 「语言版本矩阵」Requirement 修改——矩阵结构与"每格必须绿"保留，
  具体版本号（Python/Node 的底线格与最新格）改引 `dependency-upgrade` 登记表。

## Impact

- 文档：`AGENTS.md`、`CONTRIBUTING.md`、`openspec/specs/workspace-layout/spec.md`、
  `openspec/specs/ci-matrix/spec.md`（随归档 sync）。
- 工具：根 `package.json`（`check:meta` 追加、新增 `check:outdated`）、
  `scripts/version_pins.json`、`scripts/check_version_pins.py`、
  `scripts/check_outdated.py`。
- 配置：`core/Cargo.toml`、`python/Cargo.toml`、`typescript/native/Cargo.toml`、
  `typescript/wasm/Cargo.toml`（`rust-version` 1.98→1.99）、
  `typescript/package.json`（TypeScript 重测结果）。
- CI：`.github/workflows/ci.yml` 无需改结构；`check:meta` 自动包含新闸门。
- 不涉及 core 数值代码、API、容差 manifest——铁律一/三/四不受影响；本变更属
  governance 类（依赖版本策略从 AGENTS.md 提级为 spec）。

## Non-goals

- 不做 Python 3.15 / pyo3 0.30 升级——另立 change（`upgrade-python-3-15`），
  按本 spec 落地的流程执行。
- 不接管机器级全局 CLI 的升级事务本身（nvm/rustup 安装、全局 npm 包的升级动作
  由环境侧负责）；本 spec 只要求本项目升级时**检查**这些全局工具是否落后于
  LTS/稳定线并升级它们到新版，不引用、不复制环境侧指南的内容。
- 不管理第三方参考仓库（scikit-rf、SignalIntegrity、本地书籍镜像）的版本——
  许可合规由 license-compliance spec 管，其源码更新不在本项目范围。
- 不新增 `.nvmrc` 等额外钉版点（`engines` + CI 矩阵 + 登记表已覆盖）。
- 不改任何 core 数值行为、API 命名、容差数值。
