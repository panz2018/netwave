# license-compliance Specification Delta

## RENAMED Requirements

- FROM: `### Requirement: testdata 逐文件登记`
- TO: `### Requirement: samples 逐文件登记`

## MODIFIED Requirements

### Requirement: 第三方声明随分发

凡第三方代码或其派生数据进入分发物，其版权声明与许可全文 MUST 登记于
`THIRD_PARTY_NOTICES.md` 并随分发物提供。参考但未复制的源（算法思想、
API 设计、规范格式）MUST NOT 出现在 notices 中——notices 只登记实际
进入分发物的内容。

#### Scenario: BSD 数据入库带声明

- **WHEN** scikit-rf（BSD-3-Clause）的 .snp 文件复制进 `oracle/samples/`
- **THEN** 原文件内 `!` 注释版权声明保留，且该文件在
  `oracle/LICENSE-NOTES.md` 与 notices 中登记

### Requirement: samples 逐文件登记

`oracle/LICENSE-NOTES.md` MUST 采用登记表格：文件 | 来源 URL | 上游版本 |
copied/generated | 许可。`copied` 指直接复制第三方文件，`generated` 指本
项目脚本产出（含用第三方工具生成——登记生成工具及版本）。未登记的文件
MUST NOT 进入 `oracle/samples/`。demo 数据 MUST 自产（netwave 自身输出或
手写数值），MUST NOT 取自 scikit-rf/SignalIntegrity 的输出。

#### Scenario: 新数据无登记即打回

- **WHEN** review 发现 `oracle/samples/` 新增文件无登记行
- **THEN** 打回，补登记后方可合入
