# ci-matrix Delta

## ADDED Requirements

### Requirement: 覆盖率中间产物不跨轮残留

凡驱动插桩代码执行的测试 harness MUST 在测试会话的开始与结束两处清除自身子树内
`target/` 之外的 `*.profraw`；`target/` 外出现 profraw = 覆盖率采集链未生效的
充分证据，故 harness MUST 先删除再报错退出（非警告、非静默、无跳过开关），
报错文本列出被删文件名与个数作为证据。

CI MUST 与本地同流程：每个构建插桩代码的 job MUST 在测试步骤**之前与之后**
各有一道清理步骤，扫描全仓 `target/` 外的 `*.profraw`，语义与 harness 钩子一致
（先删后报错）；未插桩的 job（不产 profraw）MUST NOT 加此步骤。

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
- **THEN** 测试步骤之前与之后各有一个清理步骤，扫描 `target/` 外的 `*.profraw`，
  发现即先删后以非零码失败并列出文件名与个数
- **AND** 未插桩的 job（wasm、browser、lint、bench）无此步骤
