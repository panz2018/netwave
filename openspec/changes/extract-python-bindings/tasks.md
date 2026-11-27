# Tasks

## 1. core 去 python 绑定（保留 napi）

- [x] 1.1 `core/src/frequency.rs`：删所有 `#[cfg_attr(feature="python"/"pyo3-stub-gen", ...)]`
      属性与 `use pyo3::prelude::*`/`use pyo3_stub_gen::derive::*` 导入；`FrequencyUnit`/
      `WavelengthUnit` 变纯 Rust enum，`frequency_units()`/`live_count()` 变纯 `pub fn`
      （逻辑留 core，见 `frequency_units/live_count 留 core`）。napi 属性本次保留。
- [x] 1.2 `core/src/frequency.rs`：删从未生效的 `not(coverage)` gating（见
      `删 not(coverage) gating`）。
- [x] 1.3 `core/Cargo.toml`：删 `pyo3`、`pyo3-stub-gen` 依赖与 `python`、`pyo3-stub-gen`
      feature；保留 `native-http`（见 `native-http 保留`）与 napi/napi-derive。
- [x] 1.4 验证：`cargo tree -p netwave`（默认 feature）只剩 num-complex/strum/thiserror，
      无 pyo3；`cargo check -p netwave` 通过。

## 2. python crate 自持绑定（codegen + wrapper）

- [x] 2.1 新增 `python/build.rs`：构建期读 `../core/src/frequency.rs`，正则提取
      `FrequencyUnit`/`WavelengthUnit` unit-variant 名，生成 `OUT_DIR/enums.rs`（带
      `#[pyclass]`/derive），实现 `build.rs 生成 pyclass enum`（复用 browser
      `browser/scripts/gen_values.mjs` 模式）。
- [x] 2.2 `python/src/lib.rs`：`include!` 生成的枚举；保留 Python 端 `FrequencyUnit.GHz`
      枚举类形态（见 `保留枚举类`）；newtype `Frequency`/方法签名处用 core 已有
      `as_ref()`/`FromStr` 做 core↔python 枚举转换（见 `as_ref/FromStr 转换`）。
- [x] 2.3 `python/src/lib.rs`：加 `#[pyfunction] fn frequency_units()`/`live_count()`
      wrapper 调用 core 纯函数；stub-gen 注解（`gen_stub_pyclass_enum`/`gen_stub_pyfunction`）
      贴到 python crate 的生成枚举与 wrapper（见 `stub-gen 随绑定走`）。
- [x] 2.4 `python/Cargo.toml`：删对 core 的 `features=["python"]`（保留 `native-http`）；
      pyo3-stub-gen 改直接依赖。
- [x] 2.5 先写失败测试再补实现：`python/tests/` 逐 variant 加 `FrequencyUnit`/
      `WavelengthUnit` 传入用例，使枚举 pyclass 进 python 覆盖率分母后仍达 100%（见
      `补 pytest 覆盖率`）。
- [x] 2.6 验证：`pnpm test:py` 全绿（glue 覆盖率链 + pytest）。

## 3. 脚本与 CI 自我完整搬迁

- [x] 3.1 `scripts/run/test_py.sh` → `python/scripts/test.sh`；根 `package.json`
      `test:py` 改指 `bash python/scripts/test.sh`；python/ 不加 package.json（见
      `python 不加 package.json`、`脚本搬进 python/`）。
- [x] 3.2 新增 `python/scripts/build.sh`：承载 `uv sync`/`maturin develop`/`stub_gen`；
      `scripts/run/test_cross.sh` 改为产物缺失则提示先跑 build（对齐 browser 端只查产物）。
- [x] 3.3 `.github/workflows/ci.yml`：python job 路径同步为 `bash python/scripts/test.sh`。
- [x] 3.4 验证：`pnpm test:cross` 全绿（四端对拍 + 词汇/动词闸门）。

## 4. spec 与文档同步

- [x] 4.1 `openspec/specs/workspace-layout/spec.md`：把「core 零绑定依赖」不 变式从
      browser-only 扩到 python（见 `不变式写 workspace-layout`），与本 change delta 一致。
- [x] 4.2 `openspec/specs/frequency-unit/spec.md`：「跨端零手抄暴露」Python 侧机制改为
      build.rs 生成，与 delta 一致。
- [x] 4.3 `core/src/frequency.rs` 顶部「绑定靠反射注册」注释改写为「core 是词汇真相源，
      各端 pyclass/napi enum 由 build.rs/gen_values 机械生成」。
- [x] 4.4 `scripts/README.md`：test_py.sh 路径同步为 python/scripts/test.sh。
- [x] 4.5 本 change 单 change 全包不拆（见 `单 change 不拆`）。

## 5. 收尾闸门与打勾（逐锚点）

- [x] 5.1 `pnpm test` 全绿（全量含四端对拍，先于 review）。
- [x] 5.2 `Plan/`：删除 `Plan/绑定放置重构.md` §4 python 半边已完成章节，跑 `pnpm check:md`
      （锚点 `Plan/`）。
- [x] 5.3 三态时效：扫 `openspec/specs/` 全目录，对照本次产出更新/新增/退役结论留痕
      （锚点 `三态时效`）。
- [x] 5.4 旧名清零：从 git diff 列消失的旧标识符/文件（test_py.sh 路径等），全仓 grep
      确认活文件引用已同步、零残留（锚点 `旧名清零`）。
- [x] 5.5 引用归位：对 git diff --name-status HEAD 报出的 R/D 文件，grep 全仓描述其
      位置/职责的散文（含铁律十一「core 绑定宏段」）逐条更新，列 R/D 清单（锚点 `引用归位`）。
- [x] 5.6 三轴 review：按 governance spec「元规则 review 三轴」对照本 change 工件审实现
      diff，diff 文件集逐文件对上 tasks.md，硬伤清零（锚点 `三轴`）。
- [x] 5.7 体检：对触碰文件全文只读体检（health-check spec apply 态），发现落 Plan/
      等点名，不阻塞（锚点 `体检`）。
- [x] 5.8 迟到追加：复查 proposal.md `## 已定裁决` 每个关键词载体任务已打勾，未打勾即红
      （锚点 `迟到追加`）。
- [x] 5.9 `pnpm check:md` 全绿（改任何 .md 后必跑）。
- [x] 5.10 最后一项：跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾
      体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍），复跑至退出码 0
      （SUMMARY 归零）（锚点 `check:outdated`）。
