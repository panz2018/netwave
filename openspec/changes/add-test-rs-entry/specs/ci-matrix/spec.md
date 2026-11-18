# ci-matrix Delta

## MODIFIED Requirements

### Requirement: 五格构建矩阵

主 CI MUST 在以下五格全部通过：linux-x64、linux-arm64、windows-x64、
darwin-arm64、wasm32-unknown-unknown。macOS MUST NOT 提供 x64（Intel）
支持——Apple 已宣布停止支持 x86 程序，macOS 目标仅 Apple Silicon。
native 四格 MUST 执行 rust 测试与覆盖率合并命令：
`cargo llvm-cov -p netwave` 执行 core 测试，
加 `cargo build --workspace --all-targets` 作编译看门闸
（命令构成见「覆盖率门槛生效（铁律七）」）；MUST NOT 另跑
`cargo test --workspace`（core 测试由 llvm-cov 执行，绑定 crate 编译闸门
由 build 承担；本仓库源码无可执行 doctest——grep `core/src`、`python/src`、
`typescript/*/src` 的文档注释围栏仅 `text` 标注（非 rust、不可执行）且位于
bin target（bin 不跑 doctest），将来引入可执行 doctest 须另行立项补执行者）。
该链的命令细节 MUST 由 `scripts/run/test_rs.sh` 唯一承载：本地经根
`package.json` 的 `test:rs` 薄调用、CI 经 rust job 直接调
`scripts/run/test_rs.sh`，两端调同一脚本文件，参数物理同源不可漂移；
CI MUST NOT 为 rust job 补装 pnpm/Node 环境。
wasm32 格为 `cargo check`/wasm-pack 构建 + Node 侧 vitest 跑 wasm 产物。

#### Scenario: 矩阵全绿方可合并

- **WHEN** PR 触发 `ci.yml`
- **THEN** 五格 job 全部执行且 exit 0
- **AND** 任一格失败即整个 required check 失败，PR 不可合并

#### Scenario: core 测试只执行一遍

- **WHEN** 查看 native 任一格的步骤序列
- **THEN** core 测试仅经 `cargo llvm-cov -p netwave` 执行一次，
  ci.yml 不出现第二处执行同一批 core 测试的命令

#### Scenario: 本地与 CI 同脚本

- **WHEN** 对比本地 `pnpm test:rs` 与 ci.yml rust job 的测试步骤
- **THEN** 两端都只调用 `scripts/run/test_rs.sh`，llvm-cov、覆盖率地板、
  编译看门闸、profraw 清扫的参数只在该脚本内定义一处

### Requirement: 覆盖率中间产物不跨轮残留

凡驱动插桩代码执行的测试 harness MUST 在测试会话的开始与结束两处清除自身子树内
`target/` 之外的 `*.profraw`；`target/` 外出现 profraw = 覆盖率采集链未生效的
充分证据，故 harness MUST 先删除再报错退出（非警告、非静默、无跳过开关），
报错文本列出被删文件名与个数作为证据。
清扫逻辑 MUST 只有一份实现：`drain_stray_profraw` 函数（与剪枝清单
`SKIP_DIRS` 同库），CLI 壳 `scripts/run/clean_stray_profraw.py` 供 shell
消费；两个 pytest conftest 与 vitest 全局 setup MUST 消费同一实现
（import 共享函数或调用 CLI），MUST NOT 各自复制清扫逻辑。

CI MUST 与本地同流程：每个构建插桩代码的 job MUST 在测试步骤**之前与之后**
各有一道清理步骤，扫描全仓 `target/` 外的 `*.profraw`，语义与 harness 钩子一致
（先删后报错）；rust job 的清扫由 `scripts/run/test_rs.sh` 内置，python /
node job 的清理步骤 MUST 调用 `python3 scripts/run/clean_stray_profraw.py`；
未插桩的 job（不产 profraw）MUST NOT 加此步骤。

容差：存在性闸门，无数值阈值；判定口径 = `target/` 外 `*.profraw` 计数，目标值 0
（不涉及数值计算真值，故不引用 oracle manifest key）。

#### Scenario: 散落即报错并清除

- **WHEN** 测试会话开始时 `target/` 外存在 `*.profraw`（上一轮采集链断裂的残留）
- **THEN** harness 以非零码失败，报错文本列出被删文件名与个数
- **AND** 这些文件已从磁盘删除，工作区无残留

#### Scenario: 干净工作区静默通过

- **WHEN** 测试会话开始与结束时 `target/` 外均无 `*.profraw`
- **THEN** harness 不因本条款报错，正常执行测试并按原有闸门判定

#### Scenario: 断链当轮即红

- **WHEN** 本次测试会话自身因采集链未生效而在 `target/` 外写出 `*.profraw`
- **THEN** 会话结束处的检查当场以非零码失败，本轮覆盖率报告不被当作可信数字消费

#### Scenario: 下一轮自愈无需人工确认

- **WHEN** 上一轮因散落残留报错后，采集链已恢复正常并重跑同一测试命令
- **THEN** harness 通过（报错只发生一次），无需人工设置开关或删除文件

#### Scenario: 报告类产物与 target 内产物不误删

- **WHEN** 工作区存在 `.coverage`、`coverage/*.json` 或 `target/` 内的 profraw
  及清单文件
- **THEN** 本条款的清理不删除其中任何一项，覆盖率报告与
  `cargo llvm-cov clean` 的自有产物不受影响

#### Scenario: CI 测试前后各有一道清理闸门

- **WHEN** 查看 `.github/workflows/ci.yml` 中构建插桩代码的 job（rust / python /
  node）步骤序列
- **THEN** 测试步骤之前与之后各有一道清理，扫描 `target/` 外的 `*.profraw`，
  发现即先删后以非零码失败并列出文件名与个数
- **AND** rust job 的清理在 `scripts/run/test_rs.sh` 内，python / node job 的
  清理步骤调用 `python3 scripts/run/clean_stray_profraw.py`
- **AND** 未插桩的 job（wasm、lint、bench）无此步骤

#### Scenario: 清扫实现唯一不复制

- **WHEN** 在仓库内 grep profraw 清扫的遍历删除逻辑
- **THEN** 遍历 + 剪枝 + 先删后报的实现只存在于 `scripts/versions/lib/repository.py`
  一处，conftest 与 vitest setup 均为 import 或 CLI 消费，无第二份复制

## ADDED Requirements

### Requirement: rust 测试根聚合入口

根 `package.json` MUST 提供 `test:rs` 入口，薄调用 `scripts/run/test_rs.sh`；
该脚本 MUST 依次执行：profraw 前置清扫、`cargo-llvm-cov` 存在性探测（缺则打印
`scripts/install_cargo_llvm_cov.sh` 安装命令并非零退出，MUST NOT 自动安装）、
core 覆盖率链与地板阅卷、编译看门闸、profraw 后置清扫，且 MUST
`set -euo pipefail` 使任一环节失败即非零退出。本地跑绿 MUST 等价于 CI rust
job 同口径通过。

容差：存在性与退出码闸门，无数值阈值；覆盖率地板数值沿用铁律七与
`coverage_gate.py` 现有定义，本条不新增数值。

#### Scenario: 本地一条命令全链绿

- **WHEN** 开发者在仓库根运行 `pnpm test:rs` 且工具齐备
- **THEN** core 覆盖率报告产出并经地板阅卷，编译看门闸通过，脚本 exit 0

#### Scenario: 缺工具报错可行动

- **WHEN** `cargo-llvm-cov` 未安装时运行 `pnpm test:rs`
- **THEN** 脚本在任何 cargo 测试执行前以非零码退出，stderr 打印
  `bash scripts/install_cargo_llvm_cov.sh`，不发起网络安装

#### Scenario: 注入残留即红

- **WHEN** 仓库根存在人为放置的 `stray.profraw` 时运行 `pnpm test:rs`
- **THEN** 脚本以非零码失败并列出该文件名，且该文件已从磁盘删除
