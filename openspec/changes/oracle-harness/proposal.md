# Proposal: oracle-harness

## Why

交叉验证的契约、数据、比较代码目前散在 `testdata/`（数据+manifest）、
`scripts/cross_compare.py`（阅卷）、`.cross-tmp/`（平铺 36 个长文件名 bin）三处，
职责边界不清、文件命名随 case 增长失控，难以统筹。本变更把它们收拢为单一顶层
子项目 `oracle/`（数值真值参照 + 阅卷），答卷区随之迁入 `oracle/tmp/` 并改为
`<end>/<sample>/<field>.bin` 分层布局，为后续 golden 纵向轴（对 scikit-rf）
落地预留清晰骨架。

## What Changes

- **BREAKING**（仓库内部路径契约）：顶层 `testdata/` 消失，内容迁入新顶层子项目
  `oracle/`（`manifest.json`、`samples/`、`LICENSE-NOTES.md`、`README.md`）。
- 阅卷集中：`scripts/cross_compare.py` 迁为 `oracle/compare_cross.py`，全部
  跨端比较只在 oracle 处发生；各端（core/python/node/wasm）只负责 dump 自己的
  计算结果，不做比较。
- 答卷区从仓库根隐藏目录 `.cross-tmp/` 迁入 `oracle/tmp/`，布局从平铺改为
  分层：`<end>/freq.bin`、`<end>/<sample>/s.bin|z0.bin|version.txt`
  （end ∈ core/python/node/wasm），三端 dump 脚本与 compare_cross.py 同步适配；
  忽略规则写 `oracle/.gitignore`（内容 `tmp/`），根 `.gitignore` 不动。
  命名取 cross（横向轴，四端互比），避开与 `typescript/native/`（napi
  crate）撞词的 `native`。
- 容差分层澄清（实证纠正）：core 的 unit/property 测试与 oracle 零依赖——
  现状即硬编码容差常量（如 `core/tests/touchstone_domain.rs` 的
  `const TOL: f64`），manifest 只服务 oracle 阅卷。铁律三"测试代码 MUST NOT
  出现字面量容差"收窄为跨端阅卷层适用，core 内部测试容差为测试自述常量。
- `pnpm check:cross` 管线改为：四端 dump → `oracle/compare_cross.py` →
  词表检查；CI（node job）路径同步。

## Non-goals

本次只改架构、迁移已有功能，不实现新功能。以下全部写入
`Plan/测试规划.md` 留待下期：

- `gen_golden.py` 与 oracle 的 uv 环境（skrf 钉版）——golden 纵向轴
  （四端 vs scikit-rf）不实现；`compare_golden.py` 不创建。推迟的是
  实施，不是契约：铁律四措辞本次即按新契约改写（golden 不入库、CI 现算、
  skrf 版本靠 `oracle/uv.lock`、周更 golden-refresh 作废），spec 不留
  已废弃旧契约。
- manifest 升 schema v1（`cases[]`、样本 sha256、删 `python_relative`）——
  本次 manifest 原样迁移（schema 0）。
- 测试规划精选 17 个真实样本入库（本次只迁现有 dut.s1p/s2p/s4p）。
- `scripts/` 其余脚本（bench_gate、coverage_gate、治理闸门、install_*.sh）
  是否迁入 oracle，留待后议。

## Capabilities

### New Capabilities

- `oracle-harness`：oracle 子项目的阅卷契约——四端 dump 管线、
  `oracle/tmp/` 分层布局、横向轴 bit 级互比 + wasm 相对容差、
  anti-tautology 扰动自检、manifest 作为跨端阅卷容差唯一来源。

### Modified Capabilities

- `workspace-layout`：根目录清单 `testdata/` → `oracle/`；"主 CI 零 Python
  依赖" Requirement 路径同步改 `oracle/`，并明确各端主测试路径范围（oracle
  生成/阅卷步骤不在条款范围，skrf 圈禁于 oracle 环境）。
- `zero-copy-roundtrip`：cross-binding 往返对拍的输入路径改
  `oracle/samples/`，dump 产物路径改 `oracle/tmp/` 分层布局，阅卷位置明确为
  `oracle/compare_cross.py`。
- `project-governance`：铁律三容差分层改写——manifest 路径改
  `oracle/manifest.json`；"测试代码无字面量容差"收窄为跨端阅卷层，
  core 内部 unit/property 测试容差为测试自述常量（core 与 oracle 零依赖）。
  铁律四按新契约改写：skrf 圈禁于 oracle、golden 不入库（CI 现算、只活在
  `oracle/tmp/golden/`）、版本靠 `oracle/uv.lock`、周更 golden-refresh 作废。

## Impact

- 代码：`core/scripts/dump.rs`、`python/scripts/dump.py`、
  `typescript/scripts/dump.mjs`（输出路径+输入路径）、
  `scripts/cross_compare.py` → `oracle/compare_cross.py`。
- 配置：根 `package.json`（`check:cross`）、`typescript/package.json`
  （`cross-dump` 路径）、`.github/workflows/ci.yml`
  （node job 路径与注释）、新增 `oracle/.gitignore`（内容 `tmp/`；根
  `.gitignore` 不改，其旧 `.cross-tmp/` 条目成为无害死行，是否顺手删由人工定）。
- 文档：`testdata/` 删除、`oracle/README.md` 新建、`scripts/README.md`、
  `CONTRIBUTING.md`、根 `README.md`（LICENSE-NOTES 链接）、
  `core/python/typescript` 三个子 README、`scripts/check_md.py`
  （LEDGER SECTION 台账清单）、`Plan/测试规划.md`（golden 层改写 + 下期任务清单）。
- core 测试注释：`core/tests/` 中"from testdata/manifest.json"假引用改为
  自述常量措辞（5 处，仅注释）。
- 依赖：零新增；本次 oracle 无 Python 环境（纯标准库脚本 + 数据）。
