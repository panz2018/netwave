# Proposal

## Why

CI 矩阵中 rust job 与 wasm job 已有 linux-arm64 格，唯独 python / node 两个
绑定 job 没有——`.so`/`.node` 产物的 aarch64 ABI 无人验证。开发机即 arm64，
缺格意味着"仅 x64 CI 绿、arm 用户装不上"的风险照不到。人工裁决
（2026-11-13）单开本 change 补格，不塞进覆盖率统一 change。

## What Changes

- `ci.yml` python job 矩阵加一格 `ubuntu-26.04-arm` × Python 最新稳定版；
  node job 矩阵加一格 `ubuntu-26.04-arm` × Node 最新 LTS。matrix 加格自动
  继承 job 级全部步骤（含 wasm 构建、napi 构建、vitest、check:cross），
  无需复制步骤链。
- 新格覆盖率阅卷沿用现有地板参数（100），不设过渡值。
- `ci-matrix` spec：删除「覆盖率地板两阶段标定」整条 Requirement 及其
  Scenario（标定机制随覆盖率统一 change 收口，属已完成的过程），并清除
  引用该机制的悬空措辞；「硬件平台轴」Requirement 与对应 Scenario 补
  python/node 在 linux-arm64 各跑最新一格验 aarch64 ABI 的断言。
- `ci.yml` 删除因标定机制移除而悬空的历史归因注释（历史靠 git log 追溯）。
- 新格纳入 required check：required 名单在 GitHub 分支保护设置侧维护
  （仓库内无该配置文件），人工同步添加两个新 check 名。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `ci-matrix`: 硬件平台轴新增 python/node 的 linux-arm64 格要求；删除
  「覆盖率地板两阶段标定」Requirement（覆盖率门槛恒为 100，无过渡阶段）。

## Impact

- `.github/workflows/ci.yml`：python / node 两 job 的 matrix 各加一格；
  删除悬空历史归因注释。
- `openspec/specs/ci-matrix/spec.md`：Requirement 增删与 Scenario 同步。
- GitHub 分支保护（仓库外，人工网页操作）：required checks 加
  `python (ubuntu-26.04-arm, …)`、`node (ubuntu-26.04-arm, …)` 两项。
- 覆盖率报告命名已含 matrix 标识（`coverage-<对象>-<os>-<版本>`），
  新格产物与现有格不冲突，无需改命名。
- `Plan/linux-arm64绑定格-2026-11-13.md`：实施完成后删除（Plan/ 终态清空）。
- 受影响铁律：铁律七（覆盖率门槛生效）——新格按现行门槛执行，不新增豁免。

## Non-goals

- 不扩门禁扫描面：`scripts/check_comments.py` 加 `.yml`/`.yaml`、
  `scripts/check_md.py` 加考古词模式等防复发机制属另一 change
  （`Plan/考古文字清理-2026-11-14.md`），本 change 只清因删标定而悬空的注释。
- 不加"arm 格存在性"门禁：与 windows/macos 格同等，靠 spec 措辞与 review 兜底。
- 不在 CI 步骤加产物 ABI 打印（如 `readelf`）：arm runner 原生编译且测试
  通过即 ABI 实证。
- 不改 `scripts/coverage_gate.py` 的 floor 参数能力与地板 0 单测：通用阈值
  工具不随 spec 流程措辞删除而阉割。
- 不改 lessons-learned 账本：LL-097 留原文作历史证据。
- 不动语言版本 spread：arm 格只跑最新语言版，与 windows/macos"验 ABI 不验
  版本"口径一致。

## Prior art

- `ci.yml` rust job `linux-arm64` 格（`os: ubuntu-26.04-arm`）与 wasm job
  `ubuntu-26.04-arm` 格：arm runner 模式现成，本 change 照抄该 runner 标签。
- `ci.yml` python / node job 现有 windows/macos 格：「各 OS 跑最新语言版验
  平台 ABI」的矩阵形态先例，arm 格与之同构。
- `scripts/install_cargo_llvm_cov.sh` 已含 `Linux:aarch64` 分支（wasm 工具链
  安装脚本同理），arm 格工具链安装无新增工作。

## 专家增补

- `openspec/specs/ci-matrix/spec.md` 的 Scenario「python/node 版本格 + 平台格」
  须同步补 arm64 断言：只改 Requirement 正文不改 Scenario 会让 spec 自相矛盾，
  review Standards 轴打回。
- required 落地清单先行：加格与分支保护 required 名单是两套机制，提案阶段即
  列明两个新 check 名（`python (ubuntu-26.04-arm, …)`、
  `node (ubuntu-26.04-arm, …)`），避免"CI 绿但闸门未拦"的静默缺口。
- `scripts/check_ci.py` 已保证 `typescript test:*` 全接线，matrix 加格自动
  继承该约束，无需为新格另加接线检查。
