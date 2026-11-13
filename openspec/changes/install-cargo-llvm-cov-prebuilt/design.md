# Design

## Context

见 proposal.md - Why。现状：ci.yml rust job 内
`cargo install cargo-llvm-cov --locked`（仅 linux-x64 覆盖率步骤内联安装）；
仓库已有
`scripts/install_wasm_pack.sh` / `install_binaryen.sh` 两个四平台直装脚本作为
成熟模板。已实证事实（2026-11-12/13 实测）：

- 官方 release（v0.9.1）资产命名 `cargo-llvm-cov-<target>.tar.gz`，
  linux 有 musl/gnu 两变体；windows 另有 `.zip`。
- tar 顶层为裸二进制（`cargo-llvm-cov` / `cargo-llvm-cov.exe`），
  **无包裹目录**——与 wasm-pack（顶层 `wasm-pack-<tag>-<plat>/`）不同。
- 本机 `~/.cargo/bin` 在 PATH 早于 `~/.local/bin`，现存历史 cargo-install 版
  （LL-085 遮蔽条件成立）。
- `check_outdated.py` 第 3 节已按 tarball 工具探测 cargo-llvm-cov
  （probe `cargo llvm-cov --version`），装法改变不影响体检口径。

## Goals / Non-Goals

**Goals:**

- 四平台 runner 上安装均可用且当天可见（安装步骤每格冒烟）。
- 本地与 CI 共用同一脚本入口。

**Non-Goals:**

- 覆盖率计算跨平台（S2）、覆盖率命令与地板变化（铁律七口径不动）。
- 上游 `get.llvm-cov.dev` 一键脚本的采用（偏离，理由见 proposal Prior art）。

## Decisions

1. **平台 case 写全五格**（linux x64/arm64、darwin x64/arm64、windows x64）：
   照 `install_wasm_pack.sh` 的 `case "$os:$arch"` 结构；S2 落地时零改动。
   备选"只写今天用得着的格"被否——成本为零，不留欠账。
2. **linux 取 musl**：静态链接免 glibc 兼容面，与 wasm-pack 脚本一致。
   备选 gnu：无收益。
3. **解包直接落 `~/.local/bin`**：tar 顶层是裸二进制，`tar xzf -C "$bindir"`
   - `chmod +x "$bindir"/cargo-llvm-cov*`（通配覆盖 `.exe`）。不照抄
     wasm-pack 的目录拷贝行（布局不同，照抄必错）。
4. **LL-085 遮蔽处理写进脚本**：装后 `which cargo-llvm-cov` 若命中
   `~/.cargo/bin`，删除该旧二进制并复验。备选"只报警不删"被否——LL-085
   已拍板规则，且删的是刚被替代的旧版工具。
5. **ci.yml 安装步骤不带 `if`、四平台都跑**：每格验证脚本装得上 +
   `cargo llvm-cov --version` 冒烟（带 `GITHUB_TOKEN` env 防 API 限流）；
   覆盖率步骤保留 `if: linux-x64` 与命令字面。安装与计算解耦，S2 只需删
   覆盖率步骤的 `if`。
6. **spec 修订走本 change delta**（dependency-upgrade 两个 Scenario），
   不直改主 spec——人工裁决 2026-11-13。

## Risks / Trade-offs

- [latest 漂移：上游某 release 破坏兼容] → 与 binaryen/wasm-pack 同策略：
  失败当场红、fix forward 或重跑脚本回退旧 tag（dependency-upgrade spec）。
- [musl 版在 glibc runner 上理论差异] → musl 静态自包含，上游 CI 即发布
  musl 产物；四平台冒烟当天兜底。
- [windows runner 上 bash 工具链差异（tar/curl）] → windows-latest 自带
  git-bash 环境，wasm-pack 脚本已在同 runner 验证过同款调用。
- [本机删 `~/.cargo/bin/cargo-llvm-cov` 误删在用工具] → 仅删遮蔽位且
  `~/.local/bin` 已有新版时执行；删后 `which`+`--version` 复验。

## Migration Plan

部署：合入后 CI 自动生效；本机跑一次脚本完成迁移。
回滚：revert 本 change 提交即回到 `cargo install` 路径；本机重装
`cargo install cargo-llvm-cov --locked` 恢复。
