# LL ledger — scope: ci

## Entries

### LL-003 禁止关闸门/跳平台求绿

- 犯过：脚手架期为求绿注释 job、`if:` 跳过平台、删 wasm 格，事后全部恢复
  （`eb76316`/`d4dfd32`/`5e8c51e`）
- 规则：修失败格本身；coverage 折叠进 rust job 的 if-gated step，不单开
  job 重装工具链
- 复发检测：review Standards 轴 diff 中任何 `if:` 跳过或删除的矩阵格即打回

### LL-004 CI 改动先本地模拟

- 犯过：连续约 10 次 push 试错修 CI（`c0f565d`..`f855147`）
- 规则：改 `.github/` 前本地跑 `bash -euo pipefail` + shellcheck，逐 step
  命令原样模拟；已知陷阱见 LL-011..LL-013
- 复发检测：review 时核对 CI 改动 commit 前是否有本地模拟记录

### LL-041 钉版 toolchain 后组件要补装到激活工具链

- 犯过：`rust-toolchain.toml` 钉 1.98.1 后，lint job 里
  `dtolnay/rust-toolchain@stable` + `components: rustfmt, clippy` 只装到
  @stable，rustup 裸装激活的 1.98.1 不含组件，CI 报
  `'cargo-fmt' is not installed for the toolchain '1.98.1'`（本地无此坑，
  因为本地激活工具链早已带组件）
- 规则：钉版后凡用 `@stable`/`@1.x` 形式 setup 的 job，后续必须补一步
  `rustup component add <组件>`（作于当前激活工具链）；改 toolchain 钉版
  属 LL-004 范畴，push 前逐 step 核对组件/目标解析到哪个工具链
- 复发检测：review ci.yml 中 `dtolnay/rust-toolchain` 与
  `rust-toolchain.toml` 共存且无 `rustup component add` 即打回

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
- 复发（2026-11-13）：查 CI 运行状态时见 PATH 无 `gh` 即报"本机没有 gh，
  查不了 CI"，未跑 `git credential fill` 取证——照本条方法取 token 调
  `actions/runs` API 一次即查到 18 格全绿。未遵守原因：下"能力不可用"
  结论前没扫本账本
- 复发检测：review 时核对 main 历史无 agent 直推 commit；对话中声称
  "无凭据建不了 PR/查不了 CI"前，必须附 credential fill 失败的证据

### LL-011 Windows GITHUB_PATH 原生路径且分 step

- 犯过：git-bash 安装器写 unix 路径 + 同 step 使用，pwsh 后续步骤找不到
  （`f855147`）
- 规则：`cygpath -w` 写原生路径；安装与使用分属两个 step
- 复发检测：可门禁化——shellcheck/审查 CI 中 GITHUB_PATH 写入格式

### LL-013 GitHub API 带 token、env 用 block 风格

- 犯过：匿名 60 req/h 共享 runner IP 限流（`1ed1984`）；flow mapping 遇
  `${{ }}` 解析失败
- 规则：release 查询步骤传 `GITHUB_TOKEN`；含表达式的 `env:` 用 block
- 复发检测：可门禁化——yamllint/CI 审查规则

### LL-048 跨平台步骤用 bash 子 shell 语义须钉 `shell: bash`

- 犯过：node job 跨端步骤用 `(cd python && ...)` 隔离子 shell，Windows 默认
  shell 是 PowerShell——其 `( )` 是子表达式非子 shell，第一个 `cd` 泄漏到父
  作用域，第二个 `(cd python ...)` 解析成 `python/python` 报
  `Cannot find path ...python\python`（ubuntu/macos 默认 bash 不暴露，仅
  windows 格红）
- 规则：凡 `run:` 依赖 bash 语义（子 shell `( )`、`[[ ]]`、数组、`$'...'`）
  的步骤 MUST 显式 `shell: bash`；跨平台矩阵步骤不靠"默认 shell"——默认值随
  OS 变（Windows=PowerShell）。同 LL-011（Windows GITHUB_PATH）同族：Windows
  格专坑，本地 linux 复现不出
- 复发检测：review ci.yml 中 `run:` 含 `(cd`/`[[`/`$'` 等 bash-only 语法且
  无 `shell: bash` 即打回；可门禁化——CI 审查脚本扫 bash-only 构造

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

### LL-047 跨端一致性检查归构建各端产物的集成步骤

- 犯过：`test/native/vocabulary-consistency.test.ts`（node job 跑）读三份
  生成类型产物（node `.d.mts`、wasm `.d.ts`、python `_netwave.pyi`）断言
  成员集合相等；node job 只 build napi+wasm，`.pyi` 由独立 `stub_gen` bin
  生成且**全仓无任何 CI job 调用它**——CI 里 `.pyi` 根本不存在，node 四格
  全红 `ENOENT ... _netwave.pyi`。本地全绿只因工作树残留各 job 的历史产物
  （违 LL-004：本地模拟未清干净）
- 规则：跨端一致性检查归**本就已构建各端产物的集成步骤**（node job 末尾
  `check:cross` 已 `maturin develop`+build napi+wasm，三端产物天然齐备），
  勿下沉进单端测试段再为喂它单开跨语言步骤——首版误把该检查放 `test:native`
  并在 node 测试段单开 `stub_gen` 步骤，node 章节凭空依赖 python 构建（职责
  错位，被人工质疑）。终态：检查改纯标准库脚本 `scripts/check_vocab_types.py`
  （同 `check_vocab.py` 族）折进 `check:cross` 末尾（跨端闸门单一入口），
  CI 步骤内 `maturin develop` 后先跑 `stub_gen` 生成 `.pyi`（跑法见 ci.yml
  `stub_gen` 步骤：先导出 uv sysconfig LIBDIR 再 `cargo run`），
  再 `pnpm check:cross`（其前置契约=三端产物齐备）。
  本地模拟 CI 某 job 前先删该 job 不该有的产物，别信脏工作树
- 复发检测：review 读 `readFileSync`/`fs` 生成产物的测试/脚本时，核对其所在
  job 步骤是否生成了被测的每一类产物，且跨端检查是否落在构建各端的集成步骤
  而非单端测试段；可门禁化——job 内产物存在性冒烟

### LL-081 收紧依赖版本范围只抬下界，禁加未实测的上界或放行面

- 犯过：本会话设计 typescript×tsdown 坏版本的范围收紧时，先写出
  `"tsdown": ">=0.23.2 <0.24.0"`（凭推测断言 0.24 整线可用，人工纠正"没试验过
  就不能乱写"），改口时又写成 `>=0.23.2`（把 `^0.23.0` 自带的 `<0.24.0` 丢掉，
  等于放开从未测过的 1.0/2.0 大版本，人工第二次纠正"画蛇添足"）
- 规则：排除已登记坏版本时 MUST 沿用承载文件原有范围写法只抬高下界数字
  （`^0.23.0` → `^0.23.2`；caret 自带的同 major 上界属既有惯例，不删也不新加），
  MUST NOT 新增未经实测的上界，也 MUST NOT 删上界而扩大未实测放行面；
  无更高版本可抬时才降到上一稳定线（`^7` → `^6`）。同轮刷新 lockfile 使锁定
  版本落在新范围内
- 复发检测：review Standards 轴看依赖范围 diff——写法形态改变（caret 换成
  比较符）或上界出现/消失即索要实测证据，给不出即打回

### LL-084 本机 node 26 无 corepack，npm 全局装 pnpm 被 allow-scripts 静默拦

- 犯过：升 pnpm 时按 spec 走 `corepack prepare`，本机 nvm 装的 node 26
  无 corepack（`command -v corepack` 空、`lib/node_modules` 无该包）报
  command not found；改 `npm install -g pnpm@12.18.0` 后 `pnpm -v` 仍
  显示旧版 12.5.1——npm 新版 allow-scripts 安全策略拦下 pnpm 的
  install.js（preinstall/postinstall），二进制未替换却 exit 0 静默成功
- 规则：本机 node 26 无 corepack，改用
  `npm install -g --allow-scripts=pnpm pnpm@<ver>` 装 pnpm；验证升级成功
  MUST 看 `pnpm -v` 实际输出，不信 npm 的退出码。仓库内 `pnpm -v` 读
  `packageManager` 钉版（非全局二进制），验证全局版须 `cd /tmp && pnpm -v`。
  附带：`nvm install --reinstall-packages-from` 不迁移手动 `npm i -g` 装的
  npm 本体，node 自带 npm 落后须另装
- 复发检测：升级 pnpm 后 `cd /tmp && pnpm -v` 不等于目标版即中招；
  `command -v corepack` 空即知本机无 corepack

### LL-085 `~/.cargo/bin` 在 PATH 更前，遮蔽 `~/.local/bin` 直装工具旧版

- 犯过：`install_wasm_pack.sh` 把 wasm-pack 0.15.1 装进 `~/.local/bin`，
  但本机 `~/.cargo/bin`（PATH 第 2 位，早于 `~/.local/bin`）残留历史
  `cargo install` 的 wasm-pack 0.15.0，`which wasm-pack` 仍命中旧版，
  升级静默无效
- 规则：直装工具升级后 MUST `which <tool> && <tool> --version` 确认命中的
  是新版；若被更靠前的 PATH 目录遮蔽，删除遮蔽目录里的旧二进制
  （`rm ~/.cargo/bin/<tool>`）使脚本安装位生效
- 复发检测：`install_*.sh` 跑完后 `which <tool>` 路径不含脚本的
  安装目录（`~/.local/bin`）即中招

### LL-091 llvm-cov show-env 泄漏进常驻终端污染构建，致本地假失败

- 犯过：2026-11-13 apply 会话在常驻终端裸跑
  `eval "$(cargo llvm-cov show-env --sh)"`，环境变量
  （`RUSTC_WRAPPER=-Cinstrument-coverage`、`LLVM_PROFILE_FILE`、
  `CARGO_LLVM_COV_*`）泄漏残留；此后所有 `pnpm build:native` 都带
  `--cfg coverage` 编译，源码 `not(coverage)` 门控的 napi 胶水被剥掉，
  `.node` 缺 `FrequencyUnit` 等导出，vitest 13/63 假失败，agent 一度
  误判为"arm64 链接器丢 napi 符号"的仓库 bug（CI 实为 18 格全绿）
- 规则：show-env 只在子 shell 内用——用 `bash -c` 把 show-env、构建、
  测试、report 整条链一次跑完，随子 shell 销毁，MUST NOT 在常驻终端
  裸 eval。清缓存 MUST 连 napi/wasm 的独立 target 一起清
  （`typescript/native/target`、`typescript/wasm/target` 不在根
  `cargo clean` 范围，同 python.md LL-023 的 `python/target` 同理）。
  本地测试失败先 `env -i` 干净环境复跑：复跑变绿 = 环境污染非代码问题，
  禁止据脏环境结果对仓库下 bug 结论
- 复发检测：报"仓库有 bug"前对话里须有 `env -i` 复跑证据；
  `env | grep CARGO_LLVM_COV` 非空即终端已污染

### LL-092 外部驱动 rust 胶水覆盖率三坑（vitest/napi/maturin，spike 实证）

- 犯过：2026-11-13 unify-coverage-gates spike 在 vitest/napi/maturin 上反复
  试错数轮才跑通胶水覆盖率（被人工批评"瞎试"），三处非显性障碍：
  ① vitest worker 线程不跑 libc atexit，profraw 不倒出（默认池 0 份）；
  ② napi `--platform` 把插桩对象建进 `target/<triple>/debug/`，
  `cargo llvm-cov report` 默认只搜 host `target/debug` 报 not found；
  ③ maturin 从仓库根跑误读根 `pyproject.toml`（无 build-system 段）直接报错
- 规则：napi 胶水采集 = show-env（`--no-cfg-coverage`）→ clean → build debug →
  vitest `--pool=threads --execArgv="" --no-file-parallelism`（threads 池主进程
  正常退出触发 atexit；worker 拒绝 `--expose-gc` 故 gc 走 `NODE_OPTIONS`；
  串行避免多 worker 共享同一 `.node` 的 Rust 静态计数 race）→
  `report --target "$(rustc -vV | sed -n 's/^host: //p')"`。python 胶水 = 同链但
  maturin/pytest 须 `cd python`，report 不带 `--target`（maturin 对象落 host
  `target/debug`）。动手前先查上游：cargo-llvm-cov README「Get coverage of
  external tests」+ issue #207（clean 须在 build 前），勿原地试
- 复发检测：wasm 胶水 spike（S5）或任何新绑定覆盖率立项先核对本条三坑是否命中；
  胶水报告以"含目标 src 路径行且命中 > 0"为准，仅 exit 0 不算通

### LL-093 覆盖率口径漂移假绿——退役执行者须补前提实证，胶水报告须验命中

- 犯过：2026-11-13 退役 `cargo test --workspace` 后 doctest 失去执行者
  （`llvm-cov -p netwave` 不跑 doctest），若不实证"源码无 doctest"则静默漏测；
  spike 中 `report` 命令 exit 0 却因对象路径错配产出缺胶水行的报告，
  仅看退出码即假绿
- 规则：退役某测试执行者时，其覆盖的测试类型（doctest 等）MUST grep 实证
  "确无此类测试"并把前提写进 spec，将来引入须另行立项补执行者；胶水覆盖率
  报告 MUST 断言"含目标 crate 的 src 路径行且命中数 > 0"，不能只看命令 exit 0
  （对象路径/透传错配会产出 exit 0 的空或缺行报告）
- 复发检测：review 时核对退役执行者的 commit 附 grep 前提实证；胶水阅卷前核对
  报告含目标路径行且命中 > 0

### LL-095 llvm-cov 不建输出目录——CI 写报告前须 mkdir -p

- 犯过：CI run 43603143333 全部 rust/python/node job 红——`llvm-cov` 的
  `--output-path coverage/...json` 不创建父目录，而 `coverage/` 被
  `.gitignore` 排除、CI 干净检出里不存在，报
  `failed to create file ... No such file or directory`；本地因目录已存在
  而全绿，LL-004 的本地模拟未覆盖"干净检出"这一差异面
- 规则：CI 步骤凡写 `coverage/` 下产物，MUST 先 `mkdir -p coverage`；
  本地模拟 CI 时凡目标目录在 `.gitignore` 内，须先删该目录再跑，
  否则模拟不出干净检出态
- 复发检测：review 时 grep ci.yml 中 `--output-path coverage/` 的 step
  是否同 step 含 `mkdir -p coverage`

### LL-096 路径 regex 须兼容双分隔符——Windows 反斜杠击穿 `/core/`

- 犯过：CI run 43608401037 标定轮发现 `--ignore-filename-regex '/core/'`
  匹配不到 Windows 的 `D:\a\netwave\netwave\core\src\...`，core 行漏进
  python/native 胶水报告（81.61%/81.20%，拆开验证胶水部分与 linux/macOS
  完全一致）；本地 Linux 路径恒为 `/`，单 OS 模拟（LL-004）复现不了
- 规则：凡对文件路径做 regex 匹配（include/ignore/排除），MUST 用
  `[\\/]` 同时兼容两种分隔符，禁写裸 `/`；spec 写 regex 同理；
  平台特有形态（路径分隔符、换行、ABI）不得假设跨端一致，本地模拟
  声明"每格已验"时须注明哪些面只有 CI 真跑才能覆盖
- 复发检测：review 时 grep ci.yml/spec 中路径 regex 是否含裸 `/xxx/`
  模式；标定轮对比同报告跨平台数字，离群格先查路径形态再查代码

### LL-100 宏属性行计数不并回——行级豁免落 gate 模式驱动

- 犯过：unify-coverage-gates 标定轮双胶水报告各缺两行（python 129/291
  `#[pymethods]`、native 50/199 `#[napi]`），方法体全覆盖唯宏属性行计 0；
  实证（`llvm-cov show --show-expansions` + rustc#79651）：宏属性行挂一个
  region，宏展开 wrapper 的实例计数不并回该行，结构性不可命中；曾误提
  硬编码行号豁免与 nightly `coverage(off)` 两案，均被人工驳回
- 规则：llvm-cov 无稳定行级排除手段（不认 lcov-perl 的 `LCOV_EXCL_*`，
  过滤器只有文件名/函数名 regex，`#[coverage(off)]` nightly-only 即 LL-020），
  宏属性行豁免 MUST 落阅卷脚本模式驱动：三重条件（该行缺命中 + 源码行
  匹配 `#[pymethods]`/`#[napi` + 下方首个代码行以 `impl` 开头），禁硬编码
  行号；源码读不到的缺行 MUST NOT 豁免（照常报红）；豁免行打印附理由
- 复发检测：review 时核对 gate 豁免逻辑是否模式驱动无行号表；新增绑定
  宏（`#[wasm_bindgen]` 等）致胶水报告出现宏属性行缺行时，先查本条再
  设计豁免，禁回硬编码行号

### LL-101 llvm-cov clean 静默跳过致旧插桩二进制污染报告

- 犯过：改 `from_data` 后本地 `cargo llvm-cov -p netwave` 出 992/1124=88.26%
  （应 100%），缺行清单含整段 doc 注释行——`cargo llvm-cov clean --workspace`
  因 `target/llvm-cov-target/CACHEDIR.TAG` 缺失而中止（"missing or invalid
  CACHEDIR.TAG"，仅 warning 不改退出码），旧插桩测试二进制（改前源码编译）
  残留，其 region 表按旧行号贡献 0 计数污染新报告
- 规则：本地重跑 llvm-cov 前若改过被测源码，MUST 确认 `cargo llvm-cov clean`
  真的删了旧二进制（看 deps/ 下目标测试二进制时间戳），不能只看命令 exit 0；
  `CACHEDIR.TAG` 缺失时手动补（cargo 标准签名）或删 `target/llvm-cov-target`
  重来；报告缺行含 doc 注释行/行号与当前源码错位 = 旧二进制污染信号
- 复发检测：review 时若覆盖率数字与改动规模不符（加几行却掉十几个点），
  先查 clean 是否生效再查代码
- 复发（2026-11-17，change `add-test-rs-entry` 验收）：本地 `pnpm test:rs`
  出 981/1002=97.90%，缺行 21 处（`frequency.rs:56,59` + `touchstone.rs`
  19 行）均为测试明确触达的行；已跑 `cargo llvm-cov clean --workspace` 但
  未验删除效果（违本条规则），`target/llvm-cov-target/` 残留 13 个旧 profraw
  - 5 个旧插桩二进制按旧行号污染；`rm -rf target/llvm-cov-target` 重跑即
    964/964=100%。新增误判教训：把污染归因"本地平台差异"前 MUST 先做
    clean-验证实验——CI 含 arm 格且同命令能过即证伪平台说

### LL-103 profraw 散落在 target 外 = 采集链断，被 gitignore 吞掉致信号丢失

- 犯过：仓库根攒到 12 个、`python/` 攒到 3 个 `default_*_*.profraw`（共 15 个，
  跨数周无人清）；`cargo llvm-cov show-env` 未生效时 LLVM 退回默认模板
  `default_%m_%p.profraw` 写在**进程 cwd**，而 `.gitignore` 的 `*.profraw`
  把它们连同"这一轮覆盖率不可信"的信号一起静默吞掉
- 规则：`target/` 外出现 profraw = 采集链未生效的**充分证据**（`cargo llvm-cov report`
  只读 `target/` 内它自己登记的文件，`target/` 外者从来不是报告输入，
  删除零风险）；跑插桩代码的 harness MUST 在会话首尾各扫一次本树，CI MUST 在
  测试前后各加一道全仓清理，一律**先删后报错**（非警告、无开关），报错列出文件名
  与个数；下一轮无残留即自愈。不用 `cargo llvm-cov clean --profraw-only`：它按
  自有清单删（断链产生的 `default_*` 不在内）且静默成功，担不起信号职责
- 复发检测：`find . -name target -prune -o ... -name '*.profraw' -print`（剪枝
  `target`/`target-wasm`/`node_modules`/`.venv`/`.git`/`dist`/`coverage`）有输出
  即中招；覆盖率报告数字可疑时先跑这条再看代码

### LL-105 嵌套 uv 工程缺 pytest 表致上溯，覆盖率地板静默量整仓

- 犯过：`python/pyproject.toml` 无 `[tool.pytest.ini_options]`，pytest 上溯采用
  仓库根配置（`cd python && uv run pytest` 的 rootdir/configfile 都是根
  `pyproject.toml`，pytest 头部实证）；根 `addopts` 的裸 `--cov` 经 pytest-cov
  `_prepare_cov_source` 把 source 置空（=测全部），覆盖命令行 `--cov=netwave`，
  于是 python 地板实际测量 `tests/`＋`conftest.py`＋根 `scripts/versions`；
  地板 0→100（`053b86f`）后该 job 本应红（实测 401 语句缺 1 = 99.75%，缺行
  `python/tests/test_frequency_unit.py:32` 的防御 `raise`）却无人察觉，直到
  本 change 给 `python/` 加 conftest 把数字压到 87% 才暴露
- 规则：嵌套 uv 工程 MUST 自带 `[tool.pytest.ini_options]`（阻断上溯）与钉住
  `run.source` 的 `[tool.coverage]`（各测各的）；范围与阈值只写该工程配置文件，
  CI 不重复传参（同根配置注释立的规矩：不在 `package.json`/`ci.yml` 复制）。
  机器强制落 `scripts/check_py.py` 第 4 条规则（缺 pytest 表 / 有
  `[tool.coverage]` 却缺 `run.source` 均报错）
- 复发检测：`python3 scripts/check_py.py`；改任何 `pyproject.toml` 后 MUST 贴
  覆盖率**文件清单**作证据（只看百分比看不出范围错，同 LL-094）；新工程报
  "覆盖率不达标"而代码没动，先查范围是否被撑大

### LL-107 跨版本共享模块的顶层 import 受最低版约束，新标准库须函数内延迟导入

- 犯过：`python/conftest.py` 为取 `SKIP_DIRS` 常量而 import `lib.repository`，
  而 `scripts/versions/lib/repository.py` 在**模块顶层** import `tomllib`
  （3.11 才进标准库）；`python/` 声明 `requires-python>=3.10`、CI python
  矩阵跑 3.10 下限格，导入该常量即连带触发 tomllib，CI 报
  `ModuleNotFoundError: No module named 'tomllib'`、conftest 加载失败退出码 4
  （本地 3.15 全绿看不出，`uv run --python 3.10 pytest` 复现）
- 规则：被**低于自身工具链版**的运行环境 import 的模块，顶层 import 表 MUST 满足
  该环境最低版——只为取常量而 import 的模块，其顶层不得引入常量用不到的新标准库；
  新标准库（tomllib 等）落在真正解析它的函数体内（延迟导入），让"取常量"与
  "解析 TOML"解耦。`tomllib` 在 3.10 靠第三方 `tomli` 传递可用不可靠（它只是
  maturin/coverage 的可选依赖，会随上游漂移），不得依赖
- 复发检测：`scripts/tests/test_repository_import.py` 用 monkeypatch 屏蔽
  `tomllib` 后 import `lib.repository` 取 `SKIP_DIRS`，顶层 import 即红；
  review 时凡被低版运行环境 import 的模块出现新标准库顶层 import 即打回

### LL-109 升级 rustc 后覆盖率新增缺行须逐行判可达性，禁笼统归因"版本 bug"

- 犯过：rustc 1.99.1→1.100 后 native/python 覆盖率各多缺 13 行，第一反应是
  "新版本把覆盖率弄坏了"，未读源码未查上游即下结论；实为 1.100 收紧了多行
  链式表达式/闭包的 region 计数归属，把旧版"执行了却记到别处"的**假阳性**修掉，
  暴露出本就存在的两类行：①可达错误路径（drop 后访问、坏路径、越界 ordinal、
  成功路径）测试缺失；②构造性不可达（`ndarray::from_shape*`/`runtime::build`
  的 `.map_err`——shape/runtime 参数由数据反算恒自洽，Err 分支任何输入都进不去；
  以及多行语句里无分支的纯结构续行）。实证：绿(1.99.1)/红(1.100) 源码与测试
  `git diff` 逐字节相同，唯一变量是 rustc；同一行 region 计数 `1/4`→`0/2`
- 规则：升级工具链后覆盖率新增缺行，MUST 逐行判可达性再定性，禁一句"版本 bug"
  了事——可达路径（外部可控错误源：坏路径/已释放对象/越界入参/成功返回）= 真缺口，
  补测试触发；构造性不可达（参数由数据反算恒成立、属性行、无分支续行）= 与宏属性行
  同族，落 `scripts/coverage_gate.py` 模式驱动豁免（按 API 名/语句结构锚定，
  禁行号白名单，且可达 map_err、开分支/带闭包参数的续行、整条未执行语句一律仍报红，
  防豁免扩大）。`#[coverage(off)]` 在 stable 仍 E0658（#84605），无稳定行级排除手段
- 复发检测：升级 rustc 后跑 native+python 覆盖率，新增缺行逐行贴源码与计数作证据；
  review 时凡"升级后覆盖率掉了"先问"每行能不能构造输入触发"，能触发却不补测试=打回，
  不能触发却硬塞测试或放宽 floor=打回
