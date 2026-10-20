# zero-copy-roundtrip Specification Delta

## MODIFIED Requirements

### Requirement: cross-binding 往返对拍

四端 MUST 对同一真实 Touchstone 输入（`oracle/samples/` 下的 `.s1p`/`.s2p`/
`.s4p`）执行"取视图 → 改元素 → 派生回读"往返，结果一致。阅卷 MUST 集中在
`oracle/compare_cross.py`（各端只 dump，不做跨端比较）：原生三端
（core/python/node）同机同架构 MUST 逐 bit 一致；wasm 跨实现 MUST 用相对容差
（引用 manifest key `core_tol`，manifest 位于 `oracle/manifest.json`）。
dump 产物 MUST 按分层布局写入 `oracle/tmp/<end>/<sample>/<field>.bin`。
浏览器端 wasm 往返 MUST 在真浏览器（vitest browser mode，Chromium）经常驻
worker 执行，不再以 node 模拟代替浏览器路径的验收。scaffold 图案对拍
（`core.bin`/`python.bin`/`node.bin`/`wasm.bin`，源自 `fill_pattern`）废止，
anti-tautology 自检改扰分层布局下的 Touchstone S bin。

#### Scenario: 四端往返一致

- **WHEN** 四端以同一真实 Touchstone 输入与相同改写值执行"改元素→派生回读"
  往返并 dump
- **THEN** `oracle/compare_cross.py` 判定 core/python/node 三端回读结果逐 bit
  相同
- **AND** wasm 回读与原生结果相对误差 < manifest `core_tol`
- **AND** 任一视图改写后，其余端重新获取视图读取到改写后的值

#### Scenario: 浏览器往返经常驻 worker

- **WHEN** 真浏览器测试执行 `fromData` → 计算 → 回读往返
- **THEN** 全程只有一个常驻 worker 存活，主线程无 wasm 实例
- **AND** 回读结果与原生结果相对误差 < manifest `core_tol`
