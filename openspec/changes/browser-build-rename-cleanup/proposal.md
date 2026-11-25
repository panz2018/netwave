# Proposal

## Why

`browser/` 独立成包后留下三类未清干净的历史事实：构建命令仍叫 `build:browser`
（在 browser 包里构建 browser，重复命名）；多处活文件注释/spec/账本仍写已不存在
的旧命令名 `build:wasm` 与旧 job 名 `wasm job`；以及一个为测试脚本本身写镜像断言、
价值已被构建时闸门覆盖的冗余 wiring 测试。本 change 一次清完这三类，并删除已被
change 完全吸收的 `Plan/browser资产彻底归位.md`。

## What Changes

- **命令更名**：`browser/package.json` 的 `build:browser` → `build`，全包唯一构建
  命令去冗余后缀；调用方读作 `pnpm -C browser build`。同步全部活引用（package.json、
  `browser/scripts/test.sh`、`scripts/run/test_ts.sh`、`.github/workflows/ci.yml`、
  `typescript/scripts/merge_browser.mjs`、`typescript/scripts/check_dts_any.mjs`、
  `browser/README.md`、`typescript/README.md`、`CONTRIBUTING.md`、`browser/.gitignore`、
  `browser/Cargo.toml`）。
- **死引用清理（命令名）**：活文件里仍写 `build:wasm` 的注释同步为现名——
  `browser/src/lib.rs`、`typescript/scripts/check_dts_any.mjs`；账本
  `openspec/specs/lessons-learned/`（ci.md、core.md、INDEX.md LL-034、typescript.md）
  规则正文里的 `build:wasm` 同步为现名。
- **死引用清理（job 名）**：CI job 早已 `wasm`→`browser`，散文仍写 "wasm job"——
  `.github/workflows/ci.yml`（顺序注释、rust/browser/node job 多处交叉引用）、
  `browser/scripts/test.sh` 探测注释、`openspec/specs/ci-matrix/spec.md` scenario
  标题（见下）。
- **删除冗余测试**：删 `scripts/tests/test_test_browser_wiring.py`——它对
  `browser/scripts/test.sh` 写逐步骤镜像断言（脚本一改就得跟着改），且唯一不
  被别处捕获的"gate 行存在"断言已由 `coverage_gate.py` 自身与 review 覆盖；
  dist 纯净度断言在 lint job 永远 skip（lint job 不构建 browser），实际由
  `browser/scripts/publish_shell.mjs` 构建时闸门强制。
- **删除已吸收 Plan**：删 `Plan/browser资产彻底归位.md`（全部裁决已被本 change
  吸收，留着即双真相源）。

## Capabilities

### New Capabilities

（无新增 capability。）

### Modified Capabilities

- `ci-matrix`：「typescript 测试根聚合入口」scenario「typescript 入口本地全链绿」
  正文 `build:browser`→`build`；「覆盖率门槛生效（铁律七）」requirement 正文与
  scenario「生产 wasm 产物不含覆盖率导出」内 `build:browser`→`build`。行为契约不变，
  仅命令名事实更新。「全项目浏览器测试根聚合入口」requirement 正文/scenario 不含
  `build:browser`，其 scenario 标题「ci.yml wasm job 不再内联测试命令」的旧 job 名
  经 apply 态 agent-driven sync 直接编辑主 spec 标题修正（openspec delta 无 scenario
  改名机制，见已定裁决 `scenario标题经agent-driven sync直改主spec`），不进 delta。
- `workspace-layout`：「平铺 monorepo 结构」requirement 的 scenario
  「构建顺序 browser 先于 typescript」内 `build:browser`→`build`。行为契约不变。

## Impact

- 改动（命令名/死引用）：`browser/package.json`、`browser/scripts/test.sh`、
  `scripts/run/test_ts.sh`、`.github/workflows/ci.yml`、
  `typescript/scripts/merge_browser.mjs`、`typescript/scripts/check_dts_any.mjs`、
  `browser/src/lib.rs`、`browser/README.md`、`typescript/README.md`、
  `CONTRIBUTING.md`、`browser/.gitignore`、`browser/Cargo.toml`。
- 改动（账本死引用）：`openspec/specs/lessons-learned/ci.md`、`core.md`、
  `INDEX.md`、`typescript.md`。
- 经 delta 改动：`openspec/specs/ci-matrix/spec.md`、`openspec/specs/workspace-layout/spec.md`。
- 删除：`scripts/tests/test_test_browser_wiring.py`、`Plan/browser资产彻底归位.md`。
- 不受影响（实证）：根 pytest 覆盖率地板——`pyproject.toml` 的
  `[tool.coverage.run] source` 只列 versions 域与六个 gate 脚本，测试文件本身
  从不在计分范围，删 `test_test_browser_wiring.py` 对地板零影响。

## Non-goals

- 不动 `core/` 内任何 wasm 相关内容（core 是平台无关核心，其 wasm 条件编译属
  core 自身职责）。
- 不动 C 类合法 `wasm` 引用（`oracle/compare_cross.py`、`oracle/manifest.json`、
  `scripts/check_verbs.py`、`scripts/check_vocab*.py`、各 install 脚本、
  `scripts/versions/*`）——这些 `wasm` 指编译目标/绑定端，是正确术语。
- 不删兄弟测试 `scripts/tests/test_test_py_wiring.py`——它只查接线点（package.json
  暴露 test:py、ci.yml 调脚本、drain 在 clean 前），不镜像脚本逐步骤，无镜像税。
- 不动 `workspace-layout` spec「browser 发布产物不含测试代码」scenario——它由
  `publish_shell.mjs` 构建时闸门满足，不依赖被删的 wiring 测试。
- 不动 `openspec/changes/archive/**`（归档目录里的旧命令名是历史快照，不改）。

## Prior art

- 仓库内先例：`openspec/changes/archive/2026-11-24-relocate-browser-install-scripts/proposal.md`
  明确「不改 `build:browser`→`build`（属 §6，单独批次）」——本 change 即承接该
  遗留批次。
- scenario 改名先例：`openspec/changes/archive/2026-10-24-oracle-harness` 确立
  RENAMED Requirements（FROM/TO）语法；本 change 的 scenario 标题改名因 openspec
  MODIFIED 不能改 scenario 标题，改用 REMOVED+ADDED 表达整条 requirement。

## 专家增补

- 改名后跑 `pnpm -C browser build` 冒烟，确认新命令名端到端可用（`build` 与现有
  `test`/`typecheck`/`gen:constants`/`test:unit`/`test:e2e` 无脚本名冲突，已实测
  `browser/package.json` scripts 表）。
- 资深工程师会在同一笔里 grep 全仓 `build:browser` 与 `wasm job` 兜底确认活文件
  零残留（排除 `target*/`、`dist/`、`node_modules/`、`.venv/`、`archive/**`），
  而非只改 Plan 表列出的文件——tasks 末步显式列该兜底 grep。

## 已定裁决

- `删wiring测试不搬家`：`scripts/tests/test_test_browser_wiring.py` 整个删除，
  不搬家、不改名、gate 行不加替代闸门——镜像税（脚本一改即得同步）+ dist 纯净
  断言在 lint job 永远 skip + gate 行由 `coverage_gate.py` 自身与 review 覆盖。
- `spec产物纯净scenario不动`：`workspace-layout`「browser 发布产物不含测试代码」
  scenario 保持原样——由 `browser/scripts/publish_shell.mjs` 构建时闸门满足，
  不依赖被删测试。
- `根pytest地板不受影响`：删该测试对根 pytest 覆盖率地板零影响（实测
  `pyproject.toml` coverage source 不含测试文件），Plan §5 该前置为假问题，划掉。
- `build改名`：`build:browser`→`build`，全包唯一构建命令去冗余后缀。
- `死引用两类一起清`：命令名 `build:wasm`（lib.rs、check_dts_any.mjs、账本四文件）
  与 job 名 "wasm job"（ci.yml、test.sh、ci-matrix spec scenario 标题）同批同步为现名。
- `C类wasm保留`：core/oracle/check_verbs 等 `wasm`=编译目标/绑定端术语，合法保留不动。
- `scenario标题经agent-driven sync直改主spec`：ci-matrix scenario 标题「ci.yml wasm
  job 不再内联测试命令」改名为 browser——openspec delta 无 scenario 改名机制
  （MODIFIED 删旧 scenario 触发 scenario-loss ERROR，REMOVED+ADDED 同名被 validate
  拒「present in both」，RENAMED 只改 requirement 名；实证 openspec 2.2.0
  validator.ts + cli-validate spec）。netwave 归档走 agent-driven sync（直接编辑主
  spec，SKILL.md「agent-driven intelligent merge」），故该标题在 apply 态 sync 时
  直接编辑主 spec `openspec/specs/ci-matrix/spec.md`，delta 不碰该 requirement。
- `删已吸收Plan`：随本 change 删除整个 `Plan/browser资产彻底归位.md`，内容已被
  本 change 完全吸收，留着即双真相源。
- `全仓wasm逐条确认`：收尾前全仓搜 `wasm`（活文件，排除 target*/dist/node_modules/
  .venv/archive）逐条研究归属，确认死引用全部改完、剩余全是无法且不应改名的合法
  wasm（编译目标/绑定端术语），逐条结论留痕，零漏网才算闭环。
- `跳过归档体检`：本 change 归档阶段跳过 health-check spec 的 **archive 态**只读体检
  （非 apply 态——apply 态体检 task 6.4 照常执行）。
- `改名家族漏网全清`：apply 中全仓扫描发现改名家族另有 5 个漏网死引用（实测对应
  命令/文件/目录均已不存在），经人工点名扩范围一并清理——`test:wasm`（ci-matrix
  spec:227 scenario 标题、:487，实际聚合用 `test:browser`）、`typescript/wasm crate`
  （ci-matrix spec:396，实际 wasm rust 覆盖来自 `browser/` netwave-browser crate）、
  `test_wasm.sh`（ci.md 账本 :28/:248/:404，现为 `browser/scripts/test.sh`）、
  `netwave_wasm.d.ts`（typescript.md 账本 :51，现为 `netwave_browser.d.ts`）、
  `scripts/run/test_browser.sh`（scripts/README.md:24、ci.yml:125 注释、ci-matrix
  spec:481/488/495，现为 `browser/scripts/test.sh`；`test_check_ci.py:150` 反向断言
  保留不动）。spec 正文/scenario 标题属当前事实错误必改；账本历史叙述里的死文件名
  同步为现存名以免误导。
