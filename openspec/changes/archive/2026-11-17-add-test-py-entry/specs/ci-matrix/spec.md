# ci-matrix Delta

## MODIFIED Requirements

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
各有一道清理，扫描全仓 `target/` 外的 `*.profraw`，语义与 harness 钩子一致
（先删后报错）；rust job 的清扫由 `scripts/run/test_rs.sh` 内置，python job 的
清扫由 `scripts/run/test_py.sh` 内置，node job 的清理步骤 MUST 调用
`python3 scripts/run/clean_stray_profraw.py`；未插桩的 job（不产 profraw）
MUST NOT 加此步骤。

`scripts/run/test_rs.sh` MUST 在覆盖率步骤之前与之后各删除一次
`target/llvm-cov-target/` 整目录，MUST NOT 依赖 `cargo llvm-cov clean`——
该命令在 `CACHEDIR.TAG` 缺失时静默 no-op（exit 0 但不删），残留的旧插桩
二进制会按旧行号污染新报告。`scripts/run/test_py.sh` MUST 在覆盖率链之前与
之后各执行一次 `cargo llvm-cov clean --workspace`——python 胶水的插桩对象落
host `target/debug`，`clean --workspace` 是其适用的清理命令。两个脚本的后置
清理块 MUST 以 profraw 清扫（`clean_stray_profraw.py`）开头、插桩清理其后：
带"断链当轮即红"检测职责的清扫顶到后置块最前，防日后向后置块追加命令把清扫
挤到末尾而削弱检测；散落清扫（`SKIP_DIRS` 含 `target`，只删 `target/` 外）与
插桩清理（只清 `target/` 内）作用集互斥，换序不互相破坏。

容差：存在性闸门，无数值阈值；判定口径 = `target/` 外 `*.profraw` 计数为 0，
且 `target/llvm-cov-target/` 于 `test:rs` 运行前后均不存在、`test:py` 运行前后
`target/` 外 profraw 计数均为 0（不涉及数值计算真值，故不引用 oracle
manifest key）。

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
- **THEN** 散落清扫扫描不删除其中任何一项，覆盖率报告不受影响；
  `target/llvm-cov-target/` 整目录由 rust 入口的前后置删除，属另一机制，
  不经散落扫描器

#### Scenario: CI 测试前后各有一道清理闸门

- **WHEN** 查看 `.github/workflows/ci.yml` 中构建插桩代码的 job（rust / python /
  node）步骤序列
- **THEN** 测试步骤之前与之后各有一道清理，扫描 `target/` 外的 `*.profraw`，
  发现即先删后以非零码失败并列出文件名与个数
- **AND** rust job 的清理在 `scripts/run/test_rs.sh` 内、python job 的清理在
  `scripts/run/test_py.sh` 内，node job 的清理步骤调用
  `python3 scripts/run/clean_stray_profraw.py`
- **AND** 未插桩的 job（wasm、lint、bench）无此步骤

#### Scenario: 旧插桩二进制不跨轮残留

- **WHEN** `target/llvm-cov-target/` 存在上一轮遗留的插桩二进制与 profraw
- **THEN** `pnpm test:rs` 在运行 `cargo llvm-cov` 前删除该目录，覆盖率报告
  只含当前源码编译二进制的 region 数据
- **AND** 脚本结束后该目录再次删除，下一轮无旧污染向量

#### Scenario: python 入口前后各清一次插桩

- **WHEN** 查看 `scripts/run/test_py.sh` 的命令序列
- **THEN** `cargo llvm-cov clean --workspace` 在覆盖率链之前与之后各出现一次
- **AND** 后置清理块中 `clean_stray_profraw.py` 排在 `clean --workspace` 之前

#### Scenario: 后置块清扫先于插桩清理

- **WHEN** 查看 `scripts/run/test_rs.sh` 与 `scripts/run/test_py.sh` 的后置清理块
- **THEN** 两脚本后置块均以 `clean_stray_profraw.py` 开头、插桩清理命令其后，
  带检测职责的清扫不被后置追加的命令挤到末尾

#### Scenario: 清扫实现唯一不复制

- **WHEN** 在仓库内 grep profraw 清扫的遍历删除逻辑
- **THEN** 遍历 + 剪枝 + 先删后报的实现只存在于 `scripts/versions/lib/repository.py`
  一处，conftest 与 vitest setup 均为 import 或 CLI 消费，无第二份复制

## ADDED Requirements

### Requirement: python 测试入口本地与 CI 同脚本

python 绑定测试与 rust 胶水覆盖率链的命令细节 MUST 由 `scripts/run/test_py.sh`
唯一承载：本地经根 `package.json` 的 `test:py` 薄调用、CI 经 python job 直接调
同一脚本文件，参数物理同源不可漂移；CI MUST NOT 为 python job 保留独立的 profraw
drain 步骤（清扫已内置于脚本）。

容差：存在性闸门，无数值阈值；判定口径 = 根 `package.json` 含 `test:py` 且
ci.yml python job 调用 `scripts/run/test_py.sh`，胶水覆盖率地板仍为 100
（地板数值见「覆盖率门槛生效（铁律七）」，本条不重复数值真值）。

#### Scenario: python 入口本地与 CI 同脚本

- **WHEN** 对比本地 `pnpm test:py` 与 ci.yml python job 的测试步骤
- **THEN** 两端都只调用 `scripts/run/test_py.sh`，show-env、clean、maturin、
  pytest、report、coverage_gate 的参数只在该脚本内定义一处

#### Scenario: python 入口缺工具报错可行动

- **WHEN** 本地缺 `cargo-llvm-cov` 或 `uv` 时执行 `pnpm test:py`
- **THEN** 脚本以非零码退出并打印对应安装命令，不静默跳过、不自动安装

#### Scenario: python 胶水行未测即红

- **WHEN** `python/src/` 新增一行未被任何 pytest 用例执行的 rust 胶水产码
- **THEN** `pnpm test:py` 经 `coverage_gate.py` 对 `coverage/coverage-python.json`
  阅卷失败（exit ≠ 0），PR 不可合并
