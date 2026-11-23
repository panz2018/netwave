# license-compliance Delta

## Modified Requirements

### Requirement: 发布元数据 license 字段一致

`core/Cargo.toml`、`python/Cargo.toml`、`browser/Cargo.toml`、
`typescript/native/Cargo.toml`、`browser/package.json`、
`typescript/package.json`、`python/pyproject.toml` 的 license 字段 MUST 全部为
`MIT OR Apache-2.0`，与根声明一致。门禁 MUST 由 `scripts/check_license.py` 校验并入
`pnpm check`，不一致即红。

#### Scenario: 元数据漂移即门禁红

- **WHEN** 任一元数据文件 license 字段被改为与根声明不同（如纯 MIT）
- **THEN** `pnpm check` 退出码非 0 并指出漂移文件
