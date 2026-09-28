# LL ledger — scope: ci

## Entries

### LL-003 禁止关闸门/跳平台求绿

- 犯过：phase-0 为求绿注释 job、`if:` 跳过平台、删 wasm 格，事后全部恢复
  （`eb76316`/`d4dfd32`/`5e8c51e`）
- 规则：修失败格本身；coverage 折叠进 rust job 的 if-gated step，不单开
  job 重装工具链
- 复发检测：review Standards 轴 diff 中任何 `if:` 跳过或删除的矩阵格即打回

### LL-004 CI 改动先本地模拟

- 犯过：连续约 10 次 push 试错修 CI（`c0f565d`..`f855147`）
- 规则：改 `.github/` 前本地跑 `bash -euo pipefail` + shellcheck，逐 step
  命令原样模拟；已知陷阱见 LL-011..LL-013
- 复发检测：review 时核对 CI 改动 commit 前是否有本地模拟记录

### LL-009 交互命令预先非交互化

- 犯过：corepack 下载确认假死；cargo-llvm-cov 首跑询问 llvm-tools 假死
  （2026-09-22）
- 规则：设 `COREPACK_ENABLE_DOWNLOAD_PROMPT=0`；先预装
  `llvm-tools-preview`
- 复发检测：可门禁化——CI 环境预装检查；agent 侧文字规则

### LL-011 Windows GITHUB_PATH 原生路径且分 step

- 犯过：git-bash 安装器写 unix 路径 + 同 step 使用，pwsh 后续步骤找不到
  （`f855147`）
- 规则：`cygpath -w` 写原生路径；安装与使用分属两个 step
- 复发检测：可门禁化——shellcheck/审查 CI 中 GITHUB_PATH 写入格式

### LL-012 binaryen 整树安装

- 犯过：只拷 `bin/` 致 macOS SIGABRT（`08c600d`）
- 规则：release 整树解到 `~/.local/opt/binaryen`（RUNPATH `$ORIGIN/../lib`）
- 复发检测：`scripts/install_binaryen.sh` 保持整树布局；CI wasm-opt 冒烟

### LL-013 GitHub API 带 token、env 用 block 风格

- 犯过：匿名 60 req/h 共享 runner IP 限流（`1ed1984`）；flow mapping 遇
  `${{ }}` 解析失败
- 规则：release 查询步骤传 `GITHUB_TOKEN`；含表达式的 `env:` 用 block
- 复发检测：可门禁化——yamllint/CI 审查规则
