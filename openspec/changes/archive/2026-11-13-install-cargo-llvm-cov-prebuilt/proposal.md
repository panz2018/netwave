# Proposal

## Why

CI 的 rust job 用 `cargo install cargo-llvm-cov --locked` 源码编译安装覆盖率
工具，每次冷启动耗数分钟；而 cargo-llvm-cov 官方 release 对本仓库全部目标平台
提供预编译产物（v0.9.1 实测：linux x64/arm64、macOS x64/arm64、
windows-msvc x64，github.com/taiki-e/cargo-llvm-cov/releases）。同仓库的
wasm-pack / binaryen 已走"官方 tarball 直装最新"套路（`install_wasm_pack.sh` /
`install_binaryen.sh`），cargo-llvm-cov 是最后一个例外，口径不齐。

## What Changes

- 新增 `scripts/install_cargo_llvm_cov.sh`：从 GitHub 最新 release 下载官方
  预编译包安装到 `~/.local/bin`，覆盖四平台（linux x64/arm64 取 musl、
  macOS x64/arm64、windows x64 msvc），照 `install_wasm_pack.sh` 套路
  （latest tag 查询、`GITHUB_TOKEN` 防限流、`GITHUB_PATH` 追加、装后冒烟）。
- ci.yml rust job：`cargo install cargo-llvm-cov --locked` 替换为
  `bash scripts/install_cargo_llvm_cov.sh`；安装步骤不带 `if`，四平台每格
  都跑（验证各平台安装可用）；覆盖率计算步骤维持原样（`if: linux-x64`、
  命令字面 `cargo llvm-cov -p netwave --codecov` + `coverage_gate.py 100`
  不变，铁律七口径不动）。
- dependency-upgrade spec 两处措辞随直装化修订：「工具链升版后补装」中
  cargo 子命令重装口径、「GitHub 直装工具落后即重跑安装脚本」清单补
  cargo-llvm-cov。
- 脚本装后按 LL-085 处理 PATH 遮蔽：`which` 命中非 `~/.local/bin` 时删除
  `~/.cargo/bin` 内的旧 `cargo install` 版。
- 文档同步：`scripts/README.md` 脚本表加行；`Plan/闸门重排-2026-11-12.md`
  决策四缺工具提示文案改指新脚本。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `dependency-upgrade`：cargo-llvm-cov 从"cargo 子命令源码编译重装"改归
  "GitHub 直装工具重跑安装脚本"类——「工具链升版后补装」Scenario 的 cargo
  子命令重装口径与「GitHub 直装工具落后即重跑安装脚本」Scenario 的工具
  清单随之更新。

## Impact

- `.github/workflows/ci.yml`：rust job 安装步骤替换 + 新增四平台安装步骤。
- `scripts/install_cargo_llvm_cov.sh`：新增。
- `openspec/specs/dependency-upgrade/spec.md`：两个 Scenario 措辞（经本 change
  delta 同步）。
- `scripts/README.md`、`Plan/闸门重排-2026-11-12.md`、
  `Plan/覆盖率统一-2026-11-12.md`（S3 节收口删除）。
- 本机：`~/.local/bin/cargo-llvm-cov` 新增，`~/.cargo/bin/cargo-llvm-cov`
  旧版删除（LL-085）。
- 不受影响：覆盖率命令字面、`coverage_gate.py`、ci-matrix spec 铁律七、
  `check_outdated.py`（第 3 节已按 tarball 工具探测 cargo-llvm-cov，零改动
  即一致）。

## Non-goals

- 四平台跑覆盖率计算（属覆盖率统一档 S2，另行点名）。
- rust 测试与覆盖率合并单命令（S1）、胶水扩面（S4）、wasm spike（S5）。
- ci-matrix spec 铁律七修订（命令字面与工具作用域分离条款本次不动）。
- 本 change 归档时跳过 archive-health-check 五维只读体检（人工点名豁免，
  2026-11-13；仅本次，不改 config.yaml 与 archive-health-check spec）。

## Prior art

- `scripts/install_wasm_pack.sh`：同仓库已验证的四平台直装套路（latest tag、
  GITHUB_TOKEN、GITHUB_PATH/cygpath、装后冒烟），本脚本照此结构。
- <https://github.com/taiki-e/cargo-llvm-cov/releases>：官方预编译产物来源；
  上游另有 `cargo-llvm-cov` 一键安装脚本（`get.llvm-cov.dev`），偏离不采用——
  仓库内工具安装统一走自有 `scripts/install_*.sh`，便于套 LL-085 遮蔽处理
  与本地/CI 共用同一入口。

## 专家增补

- tar 顶层为裸二进制无包裹目录（实测 `tar tzf`：`cargo-llvm-cov` /
  windows 为 `cargo-llvm-cov.exe`），拷贝逻辑区别于 `install_wasm_pack.sh`
  的目录写法，直接解到 `~/.local/bin` 并 `chmod +x`。
- LL-085 遮蔽处理写进脚本：`which cargo-llvm-cov` 命中非 `~/.local/bin` 且
  遮蔽位在 `~/.cargo/bin` 时删除旧二进制，防"升级静默无效"。
- 脚本收尾冒烟 `cargo llvm-cov --version` 打印版本才算成功；ci.yml 安装
  步骤自带该冒烟，四平台安装失败当天可见。
- 装后跑一次 `python3 scripts/versions/check_outdated.py` 第 3 节口径确认
  （probe `cargo llvm-cov --version` 仍命中、不再 LAG）。
