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

### LL-040 合并只走 PR，禁直推 main；PR 用 credential helper 建

- 犯过：用户要求"提交PR合并进主分支"，agent 见 push 权限可用即
  `git push origin HEAD:main` 直推合并，被人工纠正后 force-with-lease 回滚；
  又因未找到 gh CLI 就误报"建不了 PR"，实际 git credential helper 里有
  凭据（VS Code 注入）
- 规则："提交PR" = 建 PR 并等人工在 PR 页面点 Merge，任何情况下不得
  直推 main。建 PR 的方法：用 `git credential fill`（stdin 喂
  `protocol=https` + `host=github.com`）取 token，调
  `api.github.com/repos/{owner}/{repo}/pulls` 创建（token 不得回显进
  对话）。找不到 gh CLI / token 环境变量 ≠ 无凭据，先试 credential helper
- 复发检测：review 时核对 main 历史无 agent 直推 commit；对话中声称
  "无凭据建不了 PR"前，必须附 credential fill 失败的证据

### LL-009 交互命令预先非交互化

- 犯过：corepack 下载确认假死；cargo-llvm-cov 首跑询问 llvm-tools 假死
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

### LL-034 tsdown dts 需双 glue 先建

- 犯过：ts-source-rewrite 把 tsdown 挂进 `build:native` 末尾，但 CI node job
  里 `build:native` 跑在 `build:wasm` 之前——tsdown dts 生成时 wasm-web glue
  缺失，`index.browser.d.mts` 的 re-export 动词静默退化为 `any`
  （tsdown 只 warn "Module not found, treating as external"，exit 0 不拦）
- 规则：CI node job 先 `build:wasm` 再 `build:native`（含 tsdown）——
  tsdown 构建不变式 = 双 glue（napi + wasm-web）均已落 `dist/`
- 复发检测：可门禁化——CI 审查 node job 步骤顺序（build:wasm 必须先于
  build:native）；构建后 grep `dist/index.browser.d.mts` 无 `: any` 即绿

### LL-036 改完 TS 必跑 typecheck，勿只跑 pnpm check

- 犯过：worker-resident-implementation 改 `tsdown.config.ts` 引入隐式 any
  （`neverBundle` 回调参数缺标注），只跑 `pnpm check` 未跑
  `pnpm -C typescript typecheck` 即提交，靠人工在编辑器里发现 TS7006
- 规则：`pnpm check` 按设计不含类型门禁（`src/` 壳 import `dist/` 生成
  绑定，须 glue 构建后跑）；本地 glue 常在，改完任何 `.ts`（含
  `*.config.ts`）当轮必跑 `pnpm -C typescript typecheck`
- 复发检测：`tsconfig.json` 的 `include` 已覆盖 `*.ts` 配置文件，
  `tsc --noEmit --listFiles | grep tsdown.config.ts` 命中即证门禁覆盖；
  可门禁化——把 typecheck 加进提交前 hook

### LL-037 新增 test:* 脚本必须同步进 CI，否则不算闸门

- 犯过：worker-resident-implementation 落地真浏览器线 `test:browser`
  （本地 `pnpm test` 已含），但 CI 只跑 `test:wasm`（node 模拟）——
  铁律八"主线程无 wasm"只有真浏览器能证，这条线不进 CI 等于闸门形同虚设
- 规则：新增 `typescript` `test:<name>` 脚本时，当轮必须把它接进
  `.github/workflows/ci.yml`（本地能跑 ≠ CI 已守）；CI 是闸门的唯一定义处
- 复发检测：已门禁化——`scripts/check_ci.py`（并入 `pnpm check:meta`）
  枚举 `typescript/package.json` 全部 `test:*`，任一未被 ci.yml 调用即红
