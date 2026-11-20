# Proposal

## Why

CI run 44668544175（commit e2600b8）四个 wasm job 全部挂在 `scripts/run/test_wasm.sh`
的 target 探测：`rustup target list --installed` 报 wasm32-unknown-unknown 未安装。
根因：`rust-toolchain.toml` 把活动工具链覆盖成钉版（1.100），而 wasm job 的
`dtolnay/rust-toolchain@stable` + `target:` 只把 target 装进 @stable，没装进钉版
工具链——探测命令跟随 override 查的是钉版工具链，自然找不到。这是 LL-041
（component 同机制）在 target 上的复发。

## What Changes

- `.github/workflows/ci.yml` wasm job：dtolnay 步骤后新增一步裸
  `rustup target add wasm32-unknown-unknown`（作用于激活工具链），镜像 lint job
  「components for the pinned toolchain」的既有写法；dtolnay 的 `target:` 输入保留。
- `scripts/run/test_wasm.sh`：保留 target 探测，补注释点明它查的是激活工具链、
  依赖 CI 已把 target 装进激活工具链这一前提。
- `openspec/specs/lessons-learned/ci.md` LL-041：从「组件」泛化为「target 与
  component 都要装进激活工具链；`rustup ... list` 探测跟随 override」，
  复发检测同步加 target；INDEX.md 对应行同步。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——本 change 修 CI 安装步骤的实现 bug，不新增/修改任何 spec 级行为契约；
ci-matrix spec 不动，已在已定裁决中拍板。skip_specs: true。）

## Impact

- `.github/workflows/ci.yml`（wasm job 工具链安装步骤）
- `scripts/run/test_wasm.sh`（探测块注释）
- `openspec/specs/lessons-learned/ci.md` + `INDEX.md`（LL-041 泛化）
- 关联铁律：LL-034 CI 构建不变式（改 CI 须同步核对文档/闸门——本次波及面即
  LL-041 账本，无 spec/README 事实变更）

## Non-goals

- 不改 `test_wasm.sh` 的探测逻辑本身（只加注释，不删探测、不改查询目标）。
- 不动其余 job：rust/bench/python job 不需要 wasm32 target，node job 已有裸
  `rustup target add`（实证：见 Prior art），无同类隐患。
- 不在 ci-matrix spec 补 scenario（已定裁决 `spec不动`）。

## Prior art

- 仓内同机制修法先例：`.github/workflows/ci.yml` lint job「components for the
  pinned toolchain」步骤（dtolnay 装 @stable + 裸 `rustup component add` 补到
  激活工具链）；node job「install wasm toolchain」步骤已含裸
  `rustup target add wasm32-unknown-unknown`。本次采用同一模式，无偏离。
- 账本先例：`openspec/specs/lessons-learned/ci.md` LL-041。

## 专家增补

- 顶尖 CI 工程师会顺手核对全仓 `dtolnay/rust-toolchain` 与 `rust-toolchain.toml`
  共存的所有 job：已实证 `.github/workflows/ci.yml` 中 lint（component，已有裸
  add）、node（target，已有裸 add）、rust/python/bench（不需要 wasm32）均无同类
  隐患，仅 wasm job 一处要补——增补为「已查，无遗漏」。
- 会在 LL-041 复发检测里写明「`rustup ... list` 探测跟随 override」这一机制，
  防未来在脚本里用裸 `rustup target list` / `rustup component list` 做就绪探测
  时再踩（落点：`openspec/specs/lessons-learned/ci.md` LL-041 复发检测段）。

## 已定裁决

- `CI补装target`：wasm job dtolnay 步骤后新增裸命令 `rustup target add wasm32-unknown-unknown`，作用于激活工具链（grilling Q1=A）。
- `保留dtolnay输入`：dtolnay 的 `target:` 输入保留，裸命令单独成步并加注释，
  镜像 lint job 写法（grilling Q4=A）。
- `探测注释`：`test_wasm.sh` 保留 target 探测，补注释点明查询目标为激活工具链
  及其 CI 前提（grilling Q2=A）。
- `LL-041泛化`：LL-041 正文与复发检测从 component 泛化到 target+component，
  INDEX.md 同步（grilling Q3=A）。
- `spec不动`：ci-matrix spec 不补 scenario，本 change skip_specs（grilling Q6=A）。
- `体检一次性跳过`：本次归档完成后的 archive 态全项目存量体检一次性跳过
  （health-check spec archive 态），apply 态被触碰文件体检照常执行，
  不豁免后续 change（人工点名 2026-11-20）。
