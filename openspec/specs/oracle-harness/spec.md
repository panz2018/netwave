# oracle-harness Specification

## Purpose

定义 oracle 子项目的交叉验证阅卷契约：四端只 dump 不阅卷、`oracle/tmp/`
分层答卷布局、横向轴原生逐 bit + wasm 相对容差、anti-tautology 扰动自检，
以及 manifest 作为跨端阅卷容差的唯一来源。

## Requirements

### Requirement: oracle 子项目是交叉验证的唯一阅卷处

顶层 `oracle/` MUST 是跨端一致性验证的唯一集中地：契约（`manifest.json`）、
输入样本（`samples/`）、阅卷脚本（`compare_cross.py`）、答卷区（`tmp/`，
由 `oracle/.gitignore` 忽略）皆在其中。各端（core/python/node/wasm）MUST
只 dump 自己的计算结果为字节文件，MUST NOT 在各端测试内做跨端比较。
阅卷脚本 MUST 纯标准库（无第三方依赖），使任何装有 python3 的环境可直接
运行。

#### Scenario: 各端只交卷不阅卷

- **WHEN** 检查四端测试与 dump 脚本
- **THEN** 无任何一端自行比较他端结果或读取他端产物做断言；全部跨端比较
  只发生在 `oracle/compare_cross.py`

#### Scenario: 阅卷零依赖可运行

- **WHEN** 在只装有 python3（无 venv、无第三方包）的环境运行
  `python3 oracle/compare_cross.py <dir>`
- **THEN** 脚本正常执行完成比对（仅标准库：json/struct/random/pathlib）

### Requirement: dump 产物分层布局

四端 dump 产物 MUST 写入 `oracle/tmp/`（由 `oracle/.gitignore` 忽略，
阅后即焚；根 `.gitignore` 不改），布局 MUST 为 `<end>/<sample>/<field>.bin`：
`end` ∈ core/python/node/wasm；`sample` 为输入样本名（空格 sanitize 为
下划线，原件文件名不改）；`field` ∈ `s`/`z0`/`version.txt`。非 Touchstone
轴（λ↔f 往返）写 `<end>/freq.bin`。平铺命名（仓库根 `.cross-tmp/` 与
`<end>_ts_<case>_z0.bin` 类）废止。二进制格式契约不变：小端 f64、re/im
交错（governance 铁律一）。

#### Scenario: 分层路径可寻址

- **WHEN** 四端 dump 完成后检查 `oracle/tmp/`
- **THEN** 每个样本的每个字段位于 `<end>/<sample>/<field>.bin`，
  无平铺长文件名残留；`oracle/tmp/` 不被 git 跟踪

### Requirement: 横向轴一致性判定

`compare_cross.py` MUST 对同一输入的四端产物执行横向轴判定：原生三端
（python/node 对 core）同机同架构 MUST 逐 bit 相等（按 u64 位型比较，
`-0` 与 `0` 判不等）；wasm MUST 用相对容差，容差唯一来源为
`oracle/manifest.json` 的 `core_tol.relative`，脚本内 MUST NOT 出现字面量
容差。version 字段 MUST 逐字串比较。

#### Scenario: 原生逐 bit、wasm 相对容差

- **WHEN** 四端产物一致时运行 compare_cross.py
- **THEN** 输出 PASS；任一原生端与 core 出现位型差异（含符号位）即 FAIL
  并报端名与下标；wasm 相对误差 ≥ manifest `core_tol.relative` 即 FAIL

### Requirement: anti-tautology 扰动自检

`compare_cross.py` MUST 内置反同义反复自检：每次运行对每个非参照端
（python/node/wasm）的 Touchstone S 数据在内存副本的随机样本随机下标注入
按元素量级缩放的扰动（保证超过相对容差），要求比较器在注入的端与下标检出；
未检出或定位错误 MUST 失败。磁盘上的 `.bin` MUST NOT 被自检修改。core 不作
为扰动目标（篡改参照与篡改任一原生端不可区分）。

#### Scenario: 扰动必须被定位

- **WHEN** 自检对某端某样本随机下标注入扰动
- **THEN** 比较器报出的端与下标与注入处一致，否则退出码非 0

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

### Requirement: manifest 是跨端阅卷容差的唯一来源

跨端阅卷（横向轴与后续纵向轴）使用的容差 MUST 只在
`oracle/manifest.json` 定义；阅卷脚本 MUST 运行时读取。core 内部
unit/property 测试与 oracle MUST 零依赖（不读 manifest，容差为测试自述
常量，见 governance 铁律三）。

#### Scenario: 容差改动只改 manifest

- **WHEN** 调整 wasm 相对容差
- **THEN** 只需修改 `oracle/manifest.json`，阅卷脚本与各端代码零改动
