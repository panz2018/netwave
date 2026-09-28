# Proposal

## Why

netwave 将以 MIT OR Apache-2.0 双许可发布（用户 2026-09-27 拍板），但当前
许可状态不完整且自相矛盾：根 README 声明双许可，`typescript/package.json`
却写死纯 MIT，四个 `Cargo.toml` 与 `pyproject.toml` 完全没有 `license`
字段（发布 crates.io/PyPI 会被拒），仓库根没有 LICENSE 文件。

同时，项目的算法与 API 大量借鉴第三方：scikit-rf（BSD-3-Clause）、
SignalIntegrity（GPL-3.0，唯一具传染性的红线源）、Touchstone 规范 v2.1
（IBIS 分发条款 + Amphenol 注册商标）、《S-Parameters for Signal
Integrity》（Cambridge University Press 全版权）。将来 `testdata/` 的
golden 数据有相当部分来自 scikit-rf。目前没有任何 spec 级规则约束"借鉴
不越界"，一次逐行翻译 GPL 代码就会让整个项目的许可被迫改 GPL——这是
事故级风险，必须在写实质代码前（阶段 1/2 之前）把规则钉进宪法。

## What Changes

- governance spec 新增元规则「知识产权合规」：借鉴算法须 clean-room 独立
  实现并在 rustdoc 标注出处；GPL 源禁止任何代码进入本仓；第三方声明随
  分发；testdata 逐文件登记；Touchstone® 商标尊重。
- 新增 capability `license-compliance`：定义许可落地要求——LICENSE 文件、
  元数据字段一致性、README License/References 节、`testdata/LICENSE-NOTES.md`
  登记格式、元数据一致性门禁脚本。
- 仓库文件：新增 `LICENSE-MIT`、`LICENSE-APACHE`（版权人
  `Copyright (c) 2026 panz2018`）；补齐 4×`Cargo.toml`、
  `typescript/package.json`、`python/pyproject.toml` 的 license 字段为
  `MIT OR Apache-2.0`；README 改写 License 节（双许可 + AS IS 人话版 +
  References 四条 URL/DOI）；`testdata/LICENSE-NOTES.md` 从占位改为登记
  模板。
- 门禁：新增 `scripts/check_license.py` 校验各元数据 license 字段与根
  声明一致，并入 `pnpm check`。
- 账本：lessons-learned 新增 LL——第三方许可表（URL 寻址）+ GPL 红线。
- AGENTS.md：加一行指针（参考第三方前先查账本许可表）。

## Capabilities

### New Capabilities

- `license-compliance`: 许可选型落地与第三方知识产权合规——LICENSE 文件、
  发布元数据、第三方声明分发、testdata 登记、商标使用、门禁校验。

### Modified Capabilities

- `project-governance`: 新增元规则「知识产权合规」（clean-room、GPL 红线、
  出处标注、声明随分发、商标尊重）。

## Non-goals

- 不做代码级第三方混入扫描（grep GPL 特征头等）——阶段 1/2 有真实借鉴
  代码后再立项；本次只落元数据一致性门禁。
- 不上 CLA/EasyCLA——当前无外部贡献者，Apache-2.0 §5 默认机制足够。
- 不改 `testdata/` 现有数据文件——登记模板先行，实际登记随阶段 1 golden
  数据入库。
- 不引入 CLA、DCO、贡献者协议等新治理文件。
- 网页版 UI 的商标声明落点（页脚文案）属前端阶段，本次只在 spec 中定
  规则，不产出 UI 代码。

## 受影响铁律

- 铁律三（容差 manifest 是契约）：testdata 登记机制与 manifest 同目录
  联动，登记字段不得与 manifest 冲突。
- 元规则（优先级与单一真相源）：第三方许可表唯一存于 lessons-learned
  账本，宪法只留原则。
