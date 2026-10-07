# Spec Delta

## ADDED Requirements

### Requirement: 铁律十二 API 名字单源，禁别名壳

公开 API 的名称（方法/函数/属性）在 core/Python/node/浏览器 MUST 是同一个名字。
统一 MUST 靠**直接命名实现**达成：core 里该函数就叫这个名字，绑定宏原样搬运同名
方法——MUST NOT 在任何层添加转发到另一名字的别名函数/属性来"凑"统一。改名 MUST
连实现带名字一起改（重命名），MUST NOT 保留旧名作兼容别名（无 deprecated 转发、
无 `free() { this.drop() }` 式垫片）。

机械映射不算违反（沿用铁律九/十既有豁免）：TS camelCase（`fScaled` ↔
`f_scaled`）、Rust/Python snake_case、语言原生协议钩子（`__str__`/`toString`/
`inspect.custom`）、worker 隔离导致的 async 化（铁律八）。

工具链生成物名字不受本铁律管辖（如 wasm-bindgen 为导出类自动生成的 `free()`），
但生成物 MUST NOT 出现在用户可见面：用户可见面只允许那个唯一的名字。

本铁律是铁律十一（绑定薄壳）在名字维度的补集：铁律十一禁壳内有逻辑，本铁律禁
壳内有第二个名字。

#### Scenario: 别名壳即打回

- **WHEN** code-review Standards 轴在任一端发现转发定义：Rust `fn free` 体内
  调 `self.drop()`，或 TS `drop()` 体内 `return this.free()`
- **THEN** 打回：要求把实现直接命名为统一名并删除转发

#### Scenario: 改名不留旧别名

- **WHEN** 公开 API 改名（如 `release`→`drop`）
- **THEN** 同一 PR 内旧名在全部端、测试、文档与生成物（`.pyi`/`.d.mts`）中
  消失，无兼容别名残留

#### Scenario: 三端动词集合相等即绿

- **WHEN** CI 运行 `scripts/cross_compare.py` 提取三端公开动词集合
- **THEN** 三端集合逐名相等（机械 camelCase 映射后比较），任一名字漂移即失败

#### Scenario: 生成物不上浮公开面

- **WHEN** 检查浏览器/node 用户可见导出面
- **THEN** 不含 wasm-bindgen 生成物名（`free`）；该名字仅存在于 worker 内部
  对生成物的调用点

#### Scenario: 统一形态为实例方法

- **WHEN** 检查三端手动释放的调用形态
- **THEN** 公开形态统一为实例方法 `obj.drop()`；浏览器主线程只有数字 handle，
  `drop(handle)` 仅作为 worker 内部 `postMessage` 命令形态存在，MUST NOT 上浮为
  公开 API

### Requirement: 元规则 冻结非不可变——有问题必修正

已归档 change、已冻结测试、已定案 spec MUST NOT 成为"不可修改"的理由。发现设计
缺陷、重复实现或错误时 MUST 当轮修正：改实现 + 出对应 spec delta + 同步更新冻结
测试中受影响的断言（断言**意图**不变，实现随契约更新）。"测试已冻结""功能已完成"
"已归档" MUST NOT 用作拒绝修正的论据。冻结的含义是"锁定意图防无意漂移"，不是
"禁止有意修正"；有意修正走正常 spec delta + review 三轴，靠 git log 追溯。

#### Scenario: 以冻结为由拒绝修正即打回

- **WHEN** 实现或 code-review 中以"该测试已冻结 / 该 change 已归档 / 该功能已
  完成"为由拒绝修正已知缺陷
- **THEN** 打回：缺陷 MUST 修正，冻结测试的受影响断言随契约同步更新（意图不变）

#### Scenario: 修正走正常变更通道

- **WHEN** 修正一个已冻结契约的实现（如把两张资源表合并为一张）
- **THEN** 走 spec delta + 更新冻结测试协议断言 + review 三轴，不静默改
