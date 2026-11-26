# zero-copy-roundtrip Delta

## MODIFIED Requirements

### Requirement: cross-binding 往返对拍

四端 MUST 对同一真实 Touchstone 输入（`oracle/samples/` 下的 `.s1p`/`.s2p`/
`.s4p`）执行"取视图 → 改元素 → 派生回读"往返，结果一致。阅卷 MUST 集中在
`oracle/compare_cross.py`（各端只 dump，不做跨端比较）：原生三端
（core/python/node）同机同架构 MUST 逐 bit 一致；browser 端（wasm 实现，
跨平台）MUST 用相对容差（引用 manifest key `core_tol`，manifest 位于
`oracle/manifest.json`）。dump 产物 MUST 按分层布局写入
`oracle/tmp/<end>/<sample>/<field>.bin`。dump 脚本 MUST 按端自我完整：node 端
住 `typescript/scripts/dump.node.mjs`，browser 端住 `browser/scripts/dump.mjs`。
浏览器端 dump MUST 经真浏览器 harness（playwright + Chromium：静态服务器挂
`browser/dist/` 与 `oracle/samples/`，经 File 上传喂真壳 `fromFile`、经壳 getter
`s`/`z0`/`version` 取主数据回传落盘）执行，MUST NOT 以 node 伪造 worker 作用域
替代；浏览器路径的验收 MUST 在真浏览器完成（不以 node 模拟替代）。scaffold 图案对拍
（`core.bin`/`python.bin`/`node.bin`/`wasm.bin`，源自 `fill_pattern`）
不存在，anti-tautology 自检扰分层布局下的 Touchstone S bin。

#### Scenario: 四端往返一致

- **WHEN** 四端以同一真实 Touchstone 输入与相同改写值执行"改元素→派生回读"
  往返并 dump
- **THEN** `oracle/compare_cross.py` 判定 core/python/node 三端回读结果逐 bit
  相同
- **AND** browser 端（wasm 实现）回读与原生结果相对误差 < manifest `core_tol`
- **AND** 任一视图改写后，其余端重新获取视图读取到改写后的值

#### Scenario: 浏览器往返经常驻 worker

- **WHEN** 真浏览器测试执行 `fromData` → 计算 → 回读往返
- **THEN** 全程只有一个常驻 worker 存活，主线程无 wasm 实例
