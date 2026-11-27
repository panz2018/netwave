# Design

## Context

动机见 `proposal.md - Why`。约束：core 必须是零绑定纯库（workspace-layout delta）；
Rust 孤儿规则禁止 python crate 给 core 定义的 `FrequencyUnit` 实现 pyo3 的 `PyClass`
trait——故带 `#[pyclass]` 的枚举必须归属 python crate。browser 侧已用
`browser/scripts/gen_values.mjs` 在构建期读 core 源码正则提取枚举变体解决同一问题，
本设计把同模式移植到 python。

## Goals / Non-Goals

**Goals:**

- core 源码与 `Cargo.toml` 对 python 零绑定符号/依赖（pyo3、pyo3-stub-gen）。
- python 枚举成员单一真相源 = core enum，python 那份构建期机械生成、零手抄。
- Python 公开 API（`FrequencyUnit.GHz`）与跨端成员相等契约不变。

**Non-Goals:**

- 不改 Python/Node/浏览器公开 API 形态；不动 core 数学实现。
- 不处理 node/napi（留后续 change）。

## Decisions

### D1：python 枚举用 build.rs 构建期生成，而非 newtype 镜像或 core macro_rules

- **选定**：`python/build.rs` 读 `../core/src/frequency.rs`，正则提取
  `pub enum FrequencyUnit { … }`/`WavelengthUnit` 的 unit-variant 名（声明顺序），
  生成 `OUT_DIR/enums.rs`，内含带 `#[pyclass]`/`#[derive(...)]` 的同名 enum；
  `python/src/lib.rs` `include!(concat!(env!("OUT_DIR"), "/enums.rs"))`。
- **备选 A（newtype 手抄镜像）**：python crate 手写 `#[pyclass] enum`，variant 名复制
  一份——违背「零手抄」，被否。
- **备选 B（core macro_rules）**：core 定义生成枚举的宏、python 传 `#[pyclass]` 属性展开
  ——core 仍含绑定感知宏，违背「core 零杂七杂八」，被否。
- **理由**：build.rs 生成物属 python crate（满足孤儿规则），variant 名只在 core 出现
  一次；build.rs 挂在 cargo/maturin 编译链，漏跑直接编译失败，比脚本调用顺序稳。
  正则解析与 browser `gen_values.mjs` 同构，且 `scripts/check_vocab_types.py` 闸门兜底
  漂移。

### D2：core↔python 枚举桥接走 `as_ref()`/`FromStr`，不走 ordinal

- **选定**：python newtype `Frequency(CoreFrequency)` 的构造/`unit()` getter 处，
  python enum → core enum 用 `core::FrequencyUnit::from_str(py_enum.as_ref())`，
  core enum → python enum 用 `py_enum::from_str(core_enum.as_ref())`（生成的 pyclass
  enum 同样 derive `AsRefStr`/实现 `FromStr`，或经生成的字符串常量）。
- **备选（ordinal）**：codegen 额外生成 `to_ordinal`/`from_ordinal`，用 `iter().nth()`
  对齐——browser 因 JS 边界只传数字才用 ordinal，python 无此约束；ordinal 顺序错位会
  静默炸。被否。
- **理由**：core 已有 `as_ref()`/`FromStr`，零新增映射代码；N=5 字符串查表开销可忽略。

### D3：`frequency_units()`/`live_count()` 逻辑留 core，python 做 wrapper

- **选定**：core 保留两函数（删 `#[pyfunction]`/stub 属性变纯 `pub fn`）；python crate
  加 `#[pyfunction] fn frequency_units()`/`live_count()` 一行调用 core。
- **理由**：`frequency_units()` 是 `iter().map(as_ref)` 透传、`live_count()` 读 core
  内部 `LIVE` atomic——逻辑属 core，python 仅搬运（铁律十一薄壳）。

### D4：stub-gen 注解随绑定迁入 python crate

- **选定**：`gen_stub_pyclass_enum`/`gen_stub_pyfunction` 注解贴到 python crate 的
  生成枚举与 wrapper 上；core 删 `pyo3-stub-gen` 依赖与 feature。
- **理由**：`.pyi` 是纯 python 发布产物，core 不应知道 stub-gen。

### D5：脚本自我完整搬迁

- **选定**：`scripts/run/test_py.sh` → `python/scripts/test.sh`（根 `package.json`
  `test:py` 改指新路径）；`scripts/run/test_cross.sh` 内的 `uv sync`/`maturin develop`/
  `stub_gen` 步骤抽到 `python/scripts/build.sh`，cross 入口改为「产物缺失则提示先跑
  build」——对齐 browser 端 test_cross.sh 不重建 browser、只查产物的形态。
- **理由**：python 是 uv 工程不加 package.json（Q4），脚本归 python/ 由根直接 bash 调用。

## Risks / Trade-offs

- [build.rs 正则解析 core enum 失败/漂移] → 与 browser `gen_values.mjs` 同构已验证；
  `check_vocab_types.py` 跨端比对 `.pyi`/`.d.ts` 与 CANONICAL，漂移当场红。
- [枚举 pyclass 迁入 python 后掉出 100% 覆盖率] → 逐 variant 补 `python/tests/` 传入用例。
- [删 `not(coverage)` gating 后覆盖率构建行为变化] → 该 gating 从未生效（test_py.sh 用
  `--no-cfg-coverage`），删除是死代码清理；删后跑 test_py.sh 验证覆盖率链照常。
- [铁律十一「修复位置 MUST 是 core 绑定宏段」对 python 变陈旧] → apply 期「引用归位」
  grep 该散文并更新为「python 绑定宏住 python crate」。

## Migration Plan

1. core 删 python 属性/依赖（保留 napi），`cargo check -p netwave` 无 feature 通过。
2. python build.rs + lib.rs wrapper + stub-gen 迁入，`maturin develop` + pytest 全绿。
3. 脚本搬迁 + CI 路径同步，`pnpm test:py`/`test:cross` 全绿。
4. 回滚：每步独立 git commit，任一失败 revert 该步；core 去绑定与脚本搬迁分属不同 commit。

## Open Questions

（无——所有决策已在 proposal.md「已定裁决」锁定。）
