# Design

## Context

见 proposal.md - Why。当前形态：ci.yml rust job 双跑（`cargo test --workspace`

- `llvm-cov -p netwave`，后者仅 linux-x64 格）；python/node job 只量本语言层
  覆盖率（pytest-cov / vitest v8），rust 胶水行无人度量。人工裁决（2026-11-13
  grilling 会话）：合并、全平台、胶水扩面；**命令内联 ci.yml，不新增根
  package.json 脚本**（聚合入口属闸门重排档 T1，延后点名）。

## Goals / Non-Goals

**Goals:**

- core 测试单跑（llvm-cov 执行），native 四格各出 core 覆盖率并阅卷。
- python/native 的 rust 胶水行进入覆盖率视野，独立报告独立地板。
- 两阶段标定：新域先地板 0 收数字，核对后同 change 翻 100。

**Non-Goals:**

- 设计级边界：不改 `coverage_gate.py` 代码（多报告=多次调用，参数已够）；
  不动 wasm/lint/bench job；不引入 codecov.io 上传（报告仅 artifact 留存）。

## Decisions

1. **官方 `show-env` + `report` 三步包住外部驱动**。`exec` 子命令**不存在**
   （`cargo llvm-cov --help` 实证：仅 `test|run|report|show-env|clean|nextest`），
   官方外部测试机制为同一 shell 内四步：
   `eval "$(cargo llvm-cov show-env --sh --no-cfg-coverage)"` →
   `cargo llvm-cov clean --workspace` → 插桩构建 + pytest/vitest 驱动 →
   `cargo llvm-cov report --codecov --output-path ...`。
   `--no-cfg-coverage` 必需：show-env 默认自动设 `cfg(coverage)`，会把源码
   `cfg_attr(..., not(coverage), napi/pyclass)` 胶水剥掉，与胶水扩面目标相冲。
   约束：show-env、clean、构建、外部测试、report MUST 同一 CI step（环境变量
   不跨 step）。
2. **命令内联 ci.yml，不落 package.json**。铁律七钉的命令字面本就写在
   spec，内联与 spec 一致零冲突；根聚合入口 `test:*` 属闸门重排档 T1/T2/T4，
   人工定夺延后。代价：本地暂无单命令复现 CI 测试面（已知缺口，T1 点名时补）。
3. **胶水报告 `--ignore-filename-regex` 剔除 core 路径**。core 行归
   core 报告（自测口径）、胶水行归胶水报告（对面驱动口径），避免同一行
   两处计分与口径混淆。备选：合并总数判红——core 100% 会掩盖胶水低分，弃用。
4. **地板：首轮全部 0，标定后统一 100**。core@linux-x64 虽已标定，但
   四格共用一条阅卷命令，地板只能单值；且 core 其余三格与双胶水均为新域，
   第一天 100 大概率红（LL-057 同类假红）。故首轮四格 core + 双胶水统一
   地板 0，收数字核对后同 change 内全部翻 100。地板数值唯一定义处 =
   ci.yml 阅卷命令参数。
5. **`cargo test --workspace` 退役**，编译闸门由
   `cargo build --workspace --all-targets` 承接。llvm-cov `-p netwave`
   不编译绑定 crate，build 补位；doctest 无人执行的前提（源码无代码围栏）
   grep 实证后写入 spec。
6. **报告落 `coverage/` 目录**。`.gitignore` 已有 `coverage/`、`*.profraw`，
   零新增 ignore 规则；命名 `coverage-<对象>.json` 淘汰 codecov/glue 黑话。
7. **node 端用 `build:native:debug` 而非 release**。插桩 release 构建慢且
   优化改变行映射，debug 保行号对得上源码；ABI 验证语义不受影响
   （`.node` 导出符号与零拷贝协议同形）。

## Risks / Trade-offs

- [napi build 不透传 show-env 注入的 RUSTFLAGS → 胶水报告假 0%] → apply 首步
  本地 spike 验证；不通则改用 napi 配置的 cargo 参数注入
  （`napi.config.rust` 段或 env 显式传递）。
- [vitest 多进程 profraw 互相覆盖 → 计数丢失] → spike 验证
  `LLVM_PROFILE_FILE` 默认含 `%p`；不含则 show-env 后显式 export 补 `%p`。
- [windows/mac 格内联命令的 shell 语义差异（pwsh 无 bash 语法）] → 胶水
  步骤统一 `shell: bash`（LL-011 既有裁决）。
- [四平台覆盖率数字差异（内联决策）致某格 <100] → 两阶段标定吸收；
  真缺口补测试，不可达行逐条豁免。
- [插桩构建使 python/node job 变慢] → 接受：替代正常构建而非额外一遍，
  debug 档控制成本；换来胶水行首次可见。
- [本地无 `pnpm test` 复现入口] → 已知延后项（T1），CI 即真相；
  标定轮数字经 artifact 核对弥补本地不可复现的窗口。

## Migration Plan

1. 一个 PR 内分提交：ci.yml 三 job 改造（首轮全部地板 0）→
   spec 修订（本 delta 同步主 spec 由 archive 完成）→ LL 登记 + 文档同步。
2. CI 绿后收一轮四平台 core + 双胶水数字（artifact 下载核对），人工定性
   缺行，补测试/豁免标注，翻地板至 100（同 change 内第二笔闸门提交）。
3. 回滚：ci.yml 步骤级 revert 即恢复旧双跑口径（无数据布局、无对外 API）。

## Open Questions

- wasm 端 profraw 倒出可行性（S5 spike，独立立项，不阻塞本 change）。
- 根聚合入口 `test:*` 的最终命名与构成（闸门重排档 T1 点名时定）。
