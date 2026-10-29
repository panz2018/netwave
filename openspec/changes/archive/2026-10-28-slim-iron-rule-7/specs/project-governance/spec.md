# Spec Delta

## MODIFIED Requirements

### Requirement: 铁律七 覆盖率 100% 硬约束

四端（core/python/node/wasm）产码行覆盖率 MUST 100%，CI 低于 100% 即失败，
unit 层零豁免。唯一例外为结构性不可达代码（`unreachable!()`、平台专属分支、
防御性 error 转换），MUST 逐条显式标注豁免并写明理由（stable 通道：
`#[cfg(not(coverage))]` 编译剥离或 CI `--ignore-filename-regex` 逐文件排除；
`#[coverage(off)]` 为 nightly-only 禁用——LL-020；Python
`# pragma: no cover`、TS/JS `/* v8 ignore start/stop */`），MUST NOT
整文件/整目录批量豁免。100% 是下限不是目标：数值正确性由 golden/property/cross-binding 三层负责。

覆盖率 MUST 按 crate/包归属各自度量：core 由 core 自己的测试度量
（`cargo llvm-cov -p netwave --codecov --output-path codecov.json` 后由
`scripts/coverage_gate.py` 读 codecov.json 判 100% 地板），绑定胶水由各自
语言工具在自身 job 内度量（`pytest-cov --cov-fail-under=100`、vitest
`lines/branches: 100`）。MUST NOT 用 `llvm-cov report` 默认路径做 100%
闸门，也 MUST NOT 用 `--workspace` 把绑定 crate 的 core 副本并入 core 度量。
两条禁令背后的工具合并语义与实测证据属事件级事实，只存账本 LL-057，
本 spec 不重述。

#### Scenario: 未测代码即红

- **WHEN** 新增一行未被任何测试执行的产码
- **THEN** 对应覆盖率 job 失败（已实测：run 36304682759）

#### Scenario: 豁免逐条标注

- **WHEN** 某段代码申请覆盖率豁免
- **THEN** 豁免标记紧邻该行且附理由，无批量/整文件豁免

#### Scenario: 跨 crate 重复计数即红

- **WHEN** core 覆盖率经 `--workspace` 合并统计（绑定二进制内的 core 副本
  被重复计入）
- **THEN** 该度量方式违规；改用 `-p netwave` 单 crate 度量

#### Scenario: 工具机制解释不入宪法

- **WHEN** 需要记录某覆盖率工具的行合并语义、计数口径或实测数字
- **THEN** 写入 lessons-learned 账本对应 scope 分片，本 spec 只留契约句与
  指向该 LL 的指针；同一事实不在两层同时出现正文
