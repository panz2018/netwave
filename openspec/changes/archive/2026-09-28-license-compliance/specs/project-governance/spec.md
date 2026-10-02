# Spec Delta

## ADDED Requirements

### Requirement: 元规则 知识产权合规

本项目算法与 API 借鉴第三方公开作品，知识产权合规是发布前置硬约束：
① 借鉴 MUST clean-room——只取算法思想、数学方法、接口语义与规范格式，
实现 MUST 用目标语言习惯独立重写；MUST NOT 逐行翻译或结构性照搬第三方
源码（变量命名、函数切分、注释文字、组织顺序）。② GPL 源（唯一已知：
SignalIntegrity，GPL-3.0-or-later）MUST NOT 有任何代码或逐行翻译件进入
本仓，仅 MAY 参考其输入输出定义与算法思想。③ 借鉴第三方算法的函数
MUST 在 rustdoc/docstring 标注算法出处（书目 DOI、规范节名或上游项目
URL）——出处标注是独立实现的证据链。④ 第三方代码或派生数据进入分发物
时其声明 MUST 随分发（见 license-compliance spec）。⑤ 受版权保护的书籍
MUST NOT 复制原文/图表进本仓文档，仅 MAY 引用思想与书目信息。⑥ 商标
（Touchstone®）MUST 尊重，用法见 license-compliance spec。

#### Scenario: GPL 代码混入即事故

- **WHEN** review 发现任何源自 SignalIntegrity 的代码或逐行翻译件
- **THEN** 立即移除并打回；该 LL 计入复发记录

#### Scenario: 借鉴实现标注出处

- **WHEN** 新算法函数借鉴自第三方（书/开源项目/规范）
- **THEN** 函数级 rustdoc/docstring 含出处标注，review Standards 轴
  逐条核对

#### Scenario: 参考前先查许可

- **WHEN** agent 或人准备参考某第三方项目/书籍
- **THEN** 先在账本许可表核对其 license；GPL 源只读思想不开代码
