# project-governance Specification Delta

## MODIFIED Requirements

### Requirement: 铁律三 容差集中在 manifest，精度分层是契约

跨端阅卷的数值容差 MUST 只在 `oracle/manifest.json` 定义（`core_tol` 键），
阅卷脚本 MUST 运行时读取，阅卷源码 MUST NOT 出现字面量容差。core 内部
unit/property 测试容差为测试自述常量（`const`），与 oracle 零依赖——容差
集中治理的边界是跨端阅卷层，不含 core 自校验层。精度分层：① bit 级断言只
允许出现在同机同架构的 cross-binding 原生三端互比（core/python/node 加载同
一编译产物）；② 一切跨平台/跨实现比较（golden 异机重读、wasm vs 原生）
MUST 走 manifest 相对容差；③ Touchstone 写出→读回 MUST 是 bit 级
（shortest-roundtrip 格式化）。默认量级：解析变换往返 1e-12、级联 1e-11、
FFT 时域 1e-9（以 manifest 实际值为准）。放宽任何容差 MUST 在 manifest
注明原因。

#### Scenario: 测试代码无字面量容差

- **WHEN** 检查 oracle 阅卷脚本
- **THEN** 数值比较的容差全部来自 manifest 读取，无硬编码 `1e-9` 类字面量

#### Scenario: core 自校验容差为自述常量

- **WHEN** 检查 core 的 unit/property 测试源码
- **THEN** 容差以测试内 `const` 常量声明并注明适用层；core 测试不读
  `oracle/manifest.json`，对 oracle 零依赖

#### Scenario: wasm 对拍走相对容差

- **WHEN** cross-binding 对拍比较 wasm 与原生结果
- **THEN** 使用 manifest `core_tol` 相对容差（非 bit 级、非绝对容差）；
  原生三端同机互比 MUST bit 级

### Requirement: 铁律四 skrf 是 oracle 但主 CI 零 Python

scikit-rf 是数值权威，MUST 只出现在 `oracle/` 子项目内（`gen_golden.py`，
下期实施），各端主测试路径（cargo test / pytest / vitest）MUST 零 skrf
依赖。golden 数据 MUST NOT 提交进 git——由 gen_golden 在 CI 现算，只活在
gitignore 的 `oracle/tmp/golden/`（阅后即焚）。skrf 版本 MUST 由
`oracle/uv.lock` 钉死（随 gen_golden 落地建立），升级 = 显式改 lock 的
PR；不设每周 golden-refresh job。

#### Scenario: 主 CI 无 skrf

- **WHEN** 检查 `.github/workflows/ci.yml` 的 cargo test / pytest / vitest
  步骤
- **THEN** 无任何安装或调用 scikit-rf 的步骤（gen_golden 落地后 skrf 亦只
  出现在 oracle 阅卷步骤，各端步骤保持零 skrf）

#### Scenario: golden 不入库

- **WHEN** `git ls-files` 检查受版本控制的文件
- **THEN** 无任何 golden 数值 `.bin` 被跟踪；golden 只存在于
  `oracle/tmp/golden/`（gitignore）
