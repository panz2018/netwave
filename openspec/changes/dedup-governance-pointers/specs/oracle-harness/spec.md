# oracle-harness Specification Delta

## ADDED Requirements

### Requirement: 精度分层

数值比较 MUST 按下列三层选取判定口径，任何比较不得跨层混用口径：

1. **bit 级**：仅允许同机同架构的 cross-binding 原生三端互比（core/python/node
   加载同一编译产物）；
2. **相对容差**：一切跨平台/跨实现比较（golden 异机重读、wasm vs 原生）MUST 走
   manifest 相对容差；
3. **写出读回 bit 级**：Touchstone 写出→读回 MUST 逐 bit 相等
   （shortest-roundtrip 格式化保证）。

默认量级（以 `oracle/manifest.json` 实际值为准，本 spec 不随数字变化）：解析变换
往返 1e-12、级联 1e-11、FFT 时域 1e-9。放宽任何容差 MUST 在 manifest 注明原因。

#### Scenario: 写出读回逐 bit

- **WHEN** 任一 `Touchstone` 写出文本后立即读回并比较 `s`
- **THEN** 结果与写出前逐 bit 相等，不使用相对容差

#### Scenario: 跨平台比较不得用 bit 级

- **WHEN** golden 异机重读或 wasm 与原生结果比较
- **THEN** 判定使用 manifest `core_tol` 相对容差；出现 bit 级断言即违规

#### Scenario: 量级改动只改 manifest

- **WHEN** 调整某类操作的默认容差量级
- **THEN** 只改 `oracle/manifest.json` 并注明原因，本 spec 与各端代码零改动
