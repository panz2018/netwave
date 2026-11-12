# Spec Delta

## MODIFIED Requirements

### Requirement: fromX 构造入口名单

本 Requirement 是 `fromX` 工厂**名单**的唯一正文（governance 铁律十五只留
契约句，名单在此）：`fromData`/`from_data`、`fromText`/`from_text`、
`fromBytes`/`from_bytes`、`fromFile`/`from_file`、`fromUrl`/`from_url`、
`fromF`/`from_f`、`fromWavelength`/`from_wavelength`。名单内入口 MUST 四端
同名（机械映射豁免见 governance 铁律十）。

#### Scenario: 新构造入口先登记名单

- **WHEN** 提议新增一个 `fromX` 构造入口
- **THEN** 同一 change 内本节名单已含该名，否则 code-review Standards 轴判不完成

#### Scenario: 名单与实现同步

- **WHEN** 某 `fromX` 入口改名或废除
- **THEN** 本节名单在同一 PR 内同步更新，无已消失入口残留、无未实现入口空挂

#### Scenario: 字节入口四端同名

- **WHEN** 检查四端公开导出面
- **THEN** Rust/python 为 `from_bytes`、node/浏览器壳为 `fromBytes`，
  参数形状一致（`(bytes, nports?, path?, encoding?)`），无端专属别名
