# Design

## Context

见 `proposal.md` - Why。当前 `ci.yml`：rust job 有 `linux-arm64`
（`os: ubuntu-26.04-arm`）、wasm job 有 `ubuntu-26.04-arm`，python / node
job 仅 ubuntu/windows/macos。python / node job 的测试步骤全部定义在 job 级
`steps`，matrix 仅由 `include` 提供 `os` 与语言版本——加一格 OS 即自动继承
全部步骤，无需复制步骤链。

## Goals / Non-Goals

**Goals:**

- python / node 各得一格 linux-arm64，验证 `.so`/`.node` 的 aarch64 ABI。
- `ci-matrix` spec 与 `ci.yml` 矩阵口径一致（Requirement + Scenario 同步）。
- 删除已收口的标定过程 Requirement 及其悬空引用，spec 只留当前契约。

**Non-Goals:**

- 见 `proposal.md` Non-goals（门禁扩面、ABI 打印、账本改动、版本 spread）。

## Decisions

1. **matrix 加格而非新 job**：job 级步骤自动继承，与 windows/macos 格同构；
   备选"单开 arm job"会复制整条步骤链，双份维护，弃。
2. **只跑最新语言版**（python 3.15 / node 26，数值以 `ci.yml` 矩阵格为准）：
   arm 格目的为 ABI 而非版本 spread，与 windows/macos 口径对齐；备选
   "底线+最新两格"重复 ubuntu 已覆盖的版本轴，弃。
3. **覆盖率地板直接 100**：python/native 胶水域与 core 域均已收口，arm 仅
   新增 OS 维度；若 arm 首跑因编译器内联决策差异报缺行，按铁律七逐条定性
   （补测试或豁免），不降地板。备选"先跑过渡值"——过渡机制本身随本 change
   从 spec 删除，自相矛盾，弃。
4. **直接纳入 required**：与 windows/macos 格同等对待；required 名单在
   GitHub 分支保护设置侧维护（仓库内无配置文件），加格后须人工同步添加
   `python (ubuntu-26.04-arm, …)`、`node (ubuntu-26.04-arm, …)` 两个 check 名。
   备选"先容错试运行"——arm runner 模式 rust/wasm job 已长期验证，风险集中
   在绑定步骤本身，容错试运行反而掩盖 ABI 断裂，弃。
5. **node arm 格跑全套含 `check:cross`**：与 ubuntu 格完全同构，跨端词汇
   对拍在 arm 上顺带验证；备选"裁剪至 native ABI"造成格间步骤不一致，弃。
6. **删「覆盖率地板两阶段标定」整条 + 悬空措辞**：Scenario
   「胶水行未测即红（地板启用后）」的括号限定语等指向已删机制的措辞一并
   清除；`scripts/coverage_gate.py` 的 floor 参数与地板 0 单测保留（通用
   阈值工具，0 为合法输入值）。
7. **ci.yml 历史归因注释删除**：因标定机制移除而悬空的注释（如
   `Floor 100: calibration closed`）删除，改写为当前契约陈述或径直删除；
   历史靠 git log。

## Risks / Trade-offs

- [arm 上 `check:cross` 首跑：`stub_gen` 动态链接 libpython、napi 零拷贝
  buffer 对齐未经验证] → 失败时按根因循环定性（环境问题 vs 代码问题，
  `env -i` 复跑排除污染，LL-091）；该格直接 required，断裂即拦在 PR 上，
  正是补格目的。
- [arm runner 排队时间拉长整体 CI] → `fail-fast: false` + concurrency 取消
  旧 run 已缓解；arm 格与 x64 并行，不串行。
- [required 名单漏加导致闸门静默缺口] → tasks 内置人工步骤，验收含
  分支保护截图/清单核对。

## Migration Plan

纯 CI 矩阵扩展 + spec 同步，无代码迁移。回滚 = revert `ci.yml` 与 spec 两
文件 + 分支保护移除两个 check 名。
