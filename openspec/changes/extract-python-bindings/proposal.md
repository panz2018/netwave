# Proposal

## Why

core 现为纯数学库（wasm 侧已清零），但 python 绑定仍往 core 塞代码：`core/Cargo.toml`
挂 `pyo3`/`pyo3-stub-gen` optional 依赖，`core/src/frequency.rs` 的枚举与模块函数仍带
`#[cfg_attr(feature = "python", pyclass/pyfunction)]` 属性。这违背「core 是纯计算库、
未来独立发布」的目标，且与已完成的 browser 侧自我完整形态不一致。本变更把 python 绑定
代码从 core 彻底剥离，使 core 对 python 也零绑定依赖。

## What Changes

- core `frequency.rs`：删除所有 python/pyo3-stub-gen 属性与 `use pyo3`/`use pyo3_stub_gen`
  导入；`FrequencyUnit`/`WavelengthUnit` 变纯 Rust enum，`frequency_units()`/`live_count()`
  变纯函数（逻辑留 core）。**BREAKING**（仅内部 crate 边界，Python 公开 API 不变）。
- core `Cargo.toml`：删除 `pyo3`、`pyo3-stub-gen` 依赖与 `python`、`pyo3-stub-gen` feature
  （napi/napi-derive 留待 node change）。
- python crate：新增 `build.rs`，构建期读 `core/src/frequency.rs` 正则提取枚举变体，生成
  `#[pyclass] enum FrequencyUnit`/`WavelengthUnit`（复用 browser `gen_values.mjs` 模式）；
  `frequency_units()`/`live_count()` 改由 python crate 的 `#[pyfunction]` wrapper 调用 core
  纯函数；stub-gen 注解随绑定迁入 python crate。
- python↔core 枚举桥接：newtype `Frequency`/方法签名处用 core 已有的 `as_ref()`/`FromStr`
  转换（Python 用户不可见）。
- 删除从未生效的 `not(coverage)` gating（死代码）。
- python 测试/构建入口自我完整：`scripts/run/test_py.sh` → `python/scripts/test.sh`；
  test_cross.sh 的 python 构建步骤抽到 `python/scripts/build.sh`，cross 入口改为查产物；
  根 `package.json` `test:py` 改指新路径；CI python job 路径同步。
- workspace-layout spec：把「core 零绑定依赖」不变式从 browser-only 扩到 python。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `workspace-layout`: 「core 零绑定依赖」requirement 从「仅 wasm/browser」扩到含 python——
  core 源码与 `Cargo.toml` MUST NOT 含 pyo3/pyo3-stub-gen 符号或依赖；python crate MUST
  自持全部 pyo3 代码（含构建期生成的枚举 pyclass）与测试入口脚本。
- `frequency-unit`: 「跨端零手抄暴露」requirement 的 Python 侧机制从「pyo3 反射 core enum
  成员」改为「python crate build.rs 构建期从 core 源码生成 pyclass enum」——仍是零手抄、
  core 单一定义源，成员集合相等契约不变。

## Impact

- 代码：`core/src/frequency.rs`、`core/Cargo.toml`、`python/src/lib.rs`、新增
  `python/build.rs`、`python/Cargo.toml`。
- 脚本/CI：`scripts/run/test_py.sh`→`python/scripts/test.sh`、新增 `python/scripts/build.sh`、
  `scripts/run/test_cross.sh`、根 `package.json`、`.github/workflows/ci.yml`。
- 文档波及：`core/src/frequency.rs` 顶部「绑定靠反射注册」注释改写；`scripts/README.md`
  test_py.sh 路径；`Plan/绑定放置重构.md` §4 python 半边完成后删除。
- 铁律波及：铁律十一「修复位置 MUST 是 core 绑定宏段」对 python 变陈旧（python 绑定宏
  不再在 core），apply 期按「引用归位」核对更新该散文。
- 覆盖率：枚举 pyclass 迁入 python crate 后进入 python 覆盖率分母，缺覆盖则补 pytest。
- 受影响铁律：铁律十一（绑定薄壳）、铁律十二（API 名字单源）。

## Non-goals

- 不处理 node/napi 绑定剥离（napi/napi-derive 依赖与 `#[cfg_attr(feature="node", napi)]`
  属性本次保留，留给后续 node change）。
- 不改 Python/Node/浏览器任何公开 API 形态（`FrequencyUnit.GHz` 等用户可见面不变）。
- 不动 core 的 `native-http` feature（它是 HTTP 功能能力，非绑定代码）。
- 不改 core 数学实现、数据布局或数值契约。

## Prior art

- `browser/scripts/gen_values.mjs`——本仓已验证的「构建期读 core 源码正则提取枚举变体、
  生成绑定端 enum」模式，python build.rs 直接复用同思路。
- `openspec/specs/workspace-layout/spec.md`「core 零绑定依赖，browser 自持全部 wasm 代码」
  requirement——browser 侧已落地的自我完整不变式，本变更把同一模式扩到 python。
- `openspec/changes/archive/2026-11-25-extract-browser-bindings/`——wasm 绑定剥离的先例 change。

## 专家增补

- 顶尖专家会确保生成物纳入覆盖率与门禁分母：`python/build.rs` 生成的枚举 pyclass 进入
  `test_py.sh` 的 cargo-llvm-cov 分母后，逐 variant 补 `python/tests/` 传入用例保 100% 地板。
- 顶尖专家会复用既有词汇闸门而非新造：`scripts/check_vocab_types.py` 已跨端比对 `.pyi`/`.d.ts`
  与 CANONICAL 列表，生成枚举漂移由该闸门兜底，不新增门禁。
- 顶尖专家会把 build.rs 生成物写进 `OUT_DIR` 并 `include!`，使漏跑 codegen 直接编译失败，
  而非依赖脚本调用顺序（对齐 `python/Cargo.toml` 现有 maturin 构建链）。

## 已定裁决

- `build.rs 生成 pyclass enum`：python 枚举单一真相源 = python crate 的 build.rs 构建期从
  `core/src/frequency.rs` 正则生成带 `#[pyclass]` 的枚举（复用 browser gen_values.mjs 模式），
  非 newtype 手抄镜像、非 core 内 macro_rules。
- `保留枚举类`：Python 端仍暴露 `FrequencyUnit.GHz` 枚举类（保 IDE 词汇检查），不改字符串/常量。
- `as_ref/FromStr 转换`：core enum ↔ python 生成 enum 的内部桥接用 core 已有的 `as_ref()`/
  `FromStr`，不引入 ordinal 映射。
- `frequency_units/live_count 留 core`：两函数逻辑留 core（去属性变纯函数），python crate 做
  `#[pyfunction]` wrapper。
- `stub-gen 随绑定走`：pyo3-stub-gen 注解迁入 python crate，core 不再依赖 pyo3-stub-gen。
- `删 not(coverage) gating`：删除从未生效的 `not(coverage)` 死代码 gating。
- `补 pytest 覆盖率`：枚举 pyclass 进 python 分母后掉出 100% 则逐 variant 补 pytest。
- `native-http 保留`：core 删 python feature 但保留 native-http（功能非绑定）。
- `python 不加 package.json`：python/ 维持 uv 工程，测试脚本搬进 python/ 由根直接 bash 调用。
- `脚本搬进 python/`：test_py.sh→python/scripts/test.sh，构建步骤抽 python/scripts/build.sh。
- `不变式写 workspace-layout`：「core 零绑定符号」不变式写进 workspace-layout spec。
- `单 change 不拆`：core 去绑定化 + python codegen + 脚本搬迁一个 change 全包。
