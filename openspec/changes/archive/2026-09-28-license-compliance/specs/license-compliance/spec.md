# Spec Delta

## Purpose

定义 netwave 许可落地的可验证要求：双许可文件、发布元数据一致性、第三方
声明随分发、testdata 逐文件登记、商标使用与门禁校验。参考源一律 URL 永久
寻址，禁止记录本地绝对路径。

## ADDED Requirements

### Requirement: 双许可发布

代码 MUST 以 `MIT OR Apache-2.0` 双许可发布，版权人 MUST 为
`Copyright (c) 2026 panz2018`。仓库根 MUST 同时存在 `LICENSE-MIT` 与
`LICENSE-APACHE` 全文文件；所有发布物（crate、wheel、npm 包）MUST 随附
两份许可全文。使用者 MAY 任选其一侧遵守。

#### Scenario: 发布物含双许可全文

- **WHEN** 打包 crate/wheel/npm 包
- **THEN** 包内含 `LICENSE-MIT` 与 `LICENSE-APACHE` 全文，版权行为
  `Copyright (c) 2026 panz2018`

### Requirement: 发布元数据 license 字段一致

`core/Cargo.toml`、`python/Cargo.toml`、`typescript/native/Cargo.toml`、
`typescript/wasm/Cargo.toml`、`typescript/package.json`、
`python/pyproject.toml` 的 license 字段 MUST 全部为 `MIT OR Apache-2.0`，
与根声明一致。门禁 MUST 由 `scripts/check_license.py` 校验并入
`pnpm check`，不一致即红。

#### Scenario: 元数据漂移即门禁红

- **WHEN** 任一元数据文件 license 字段被改为与根声明不同（如纯 MIT）
- **THEN** `pnpm check` 退出码非 0 并指出漂移文件

### Requirement: 第三方声明随分发

凡第三方代码或其派生数据进入分发物，其版权声明与许可全文 MUST 登记于
`THIRD_PARTY_NOTICES.md` 并随分发物提供。参考但未复制的源（算法思想、
API 设计、规范格式）MUST NOT 出现在 notices 中——notices 只登记实际
进入分发物的内容。

#### Scenario: BSD 数据入库带声明

- **WHEN** scikit-rf（BSD-3-Clause）的 .snp 文件复制进 `testdata/`
- **THEN** 原文件内 `!` 注释版权声明保留，且该文件在
  `testdata/LICENSE-NOTES.md` 与 notices 中登记

### Requirement: testdata 逐文件登记

`testdata/LICENSE-NOTES.md` MUST 采用登记表格：文件 | 来源 URL | 上游
版本 | copied/generated | 许可。`copied` 指直接复制第三方文件，
`generated` 指本项目脚本产出（含用第三方工具生成——登记生成工具及版本）。
未登记的文件 MUST NOT 进入 `testdata/`。demo 数据 MUST 自产（netwave
自身输出或手写数值），MUST NOT 取自 scikit-rf/SignalIntegrity 的输出。

#### Scenario: 新数据无登记即打回

- **WHEN** review 发现 `testdata/` 新增文件无登记行
- **THEN** 打回，补登记后方可合入

### Requirement: Touchstone 商标尊重

`Touchstone` 为 Amphenol Corporation（原 Agilent Technologies）注册商标。
面向用户的界面与文档首次提及 MUST 使用 `Touchstone®` 或附商标声明；
项目名、包名、UI 主标题 MUST NOT 使用 Touchstone 字样。

#### Scenario: 网页版页脚商标声明

- **WHEN** 网页版 UI 发布
- **THEN** 页脚含 "Touchstone is a registered trademark of Amphenol
  Corporation" 声明，文案首次提及带 ®

### Requirement: 参考源登记表以 URL 寻址

第三方参考源登记表 MUST 存于 lessons-learned 账本（docs 分片），每条含
权威 URL（GitHub/DOI/官方 PDF），MUST NOT 记录本地绝对路径。当前登记：
scikit-rf BSD-3-Clause（<https://github.com/scikit-rf/scikit-rf>）、
SignalIntegrity GPL-3.0-or-later
（<https://github.com/Nubis-Communications/SignalIntegrity>）、Touchstone
spec v2.1（<https://ibis.org/touchstone_ver2.1/touchstone_ver2_1.pdf>）、
《S-Parameters for Signal Integrity》CUP 全版权
（<https://doi.org/10.1017/9781108784863>）。

#### Scenario: 换机器登记表仍有效

- **WHEN** 在新环境 clone 本仓查许可表
- **THEN** 表中每条经 URL 可直达原文，无需任何本地路径
