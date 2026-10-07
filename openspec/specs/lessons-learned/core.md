# LL ledger — scope: core

## Entries

### LL-002 API 命名遵 api-contract

- 犯过：自造 `frequency_in` 被否，改回 `f_scaled`
- 规则：命名以 api-contract spec 为准，禁止自造同义词
- 复发检测：review Spec 轴对照 api-contract spec 名称表

### LL-015 交错复数布局与终态借用

- 犯过：布局/搬运方式曾致拷贝（铁律一定契约时定稿）
- 规则：`(nfreq, nports, nports)` 交错 `Complex<f64>`（`[re,im,...]`），
  `#[repr(C)]` 与 numpy complex128 逐字节同；`fill_pattern`
  `re=f*100+p*10+q, im=-re` 使错位/拷贝/字节序错误破坏模式；数值测试
  期望值用同一闭式独立计算，不复用被测输出
- 复发检测：`cargo test -p netwave` + `pnpm check:cross`

### LL-019 触碰 core 后重建全部绑定

- 犯过：未重建即对拍，比到陈旧产物
- 规则：改 core 后先 `maturin develop` + `pnpm -C typescript build:native`
  - `build:wasm`，再跑任何 cross-binding 比较
- 复发检测：`pnpm check:cross` 前置于对拍；review 核对重建步骤

### LL-020 `#[coverage(off)]` 是 nightly-only

- 犯过：误加致 stable 工具链编译失败（rust-toolchain.toml 钉 stable）
- 规则：stable 下禁用 `#[coverage(off)]`；本 crate 当前无覆盖率豁免
- 复发检测：`cargo build` 即红；review Standards 轴 grep

### LL-021 真实基准必须 `black_box` 包裹输入输出

- 犯过：未包裹被优化器折叠，数字失真（真实基准落地时适用）
- 规则：criterion 基准输入输出均 `black_box`；`scaffold_noop` 为有意 no-op
  不受影响
- 复发检测：review Standards 轴检查 bench 函数体含 `black_box`

### LL-022 core crate `publish = false`

- 犯过：无（预防性记录）
- 规则：core 不独立发布，版本随 workspace 移动
- 复发检测：review 检查 `core/Cargo.toml` 保留 `publish = false`

### LL-042 精确常量比较不引用容差

- 犯过：倍率（SI 词头 $10^{3n}$，f64 精确可表示）的测试曾引用 manifest
  `core_tol` 相对容差，把逐 bit 精确断言放松成 1e-12
- 规则：`core_tol` 只约束**计算后数值**的跨平台相对容差；精确常量
  （词头倍率、整数形状等）跨端对拍 MUST 逐 bit `==`，MUST NOT 引用容差
- 复发检测：review Spec 轴检查数值断言——引用容差者必为计算结果；
  常量表测试断言中不得出现 `core_tol`

### LL-044 clippy --workspace 特性统一致 napi/wasm 属性冲突

- 犯过：core 函数 `frequency_units()` 同挂 `#[cfg_attr(feature="node",napi)]`
  与 `#[cfg_attr(feature="browser",wasm_bindgen)]`；`cargo clippy --workspace`
  把 python+node+browser 三特性统一进 core 一次编译，napi 宏见同函数已带
  `#[wasm_bindgen]` 即报 `can only #[wasm_bindgen] public functions`（真实
  glue 构建各只开一端，从不冲突；仅统一 clippy 暴露）
- 规则：同一函数上互斥的 JS 绑定属性用 `all(feature="node",not(feature="browser"))`
  / `all(feature="browser",not(feature="node"))` 门控——真实构建只开一端各端仍
  生效，统一 clippy 下该函数留裸（仍可被 Rust 测试调用，只是不导出 JS）；
  enum 同挂 `#[napi]`+`#[wasm_bindgen]` 不冲突，无需此处理
- 复发检测：`cargo clippy --workspace --all-targets -- -D warnings`（`pnpm check:rs`）

### LL-046 绑定宏生成的 glue 计入 core 覆盖率，须 not(coverage) 剥离

- 犯过：core 的 `FrequencyUnit`/`frequency_units` 挂 pyo3/napi/wasm_bindgen
  属性；`cargo llvm-cov --workspace --fail-under-lines 100` 下这些宏生成的
  注册 glue 被归属到属性行，而 glue 只在 JS/Python 运行时执行、`cargo test`
  永不触发，`frequency.rs` 掉到 92%，100% 地板红（CI rust job）
- 规则：绑定属性与其 `use` 导入统一加 `not(coverage)` 门控（cargo-llvm-cov
  自动设 `cfg(coverage)`），覆盖率构建只测纯 Rust 逻辑；绑定面由 pytest/vitest
  在普通构建覆盖。python 侧须**两端同步**：core 剥属性后，glue crate
  （`python/src/lib.rs`）的 `add_class`/`wrap_pyfunction` 调用也要 `#[cfg(not(coverage))]`，
  否则 glue 编译不过（glue 的 lib.rs 本就在 llvm-cov 排除正则内）。
  `cfg(coverage)` 须在用到的每个 crate 的 `[lints.rust]` 声明 `check-cfg`，
  否则 `-D warnings` 报 unexpected_cfgs
- 复发检测：`cargo llvm-cov --workspace --fail-under-lines 100`（rust job）；
  改绑定属性后必跑，且须验证真实 glue 构建（maturin/napi/wasm-pack）仍导出

### LL-052 泛化表不等于泛化分发

- 犯过：句柄表下沉 core 时只把表做成 `insert<T>`/`with<T>` 类型擦除泛型，
  入口仍按动词逐个导出 `network_upload`/`frequency_npoints` 等
  `#[wasm_bindgen]` 函数、worker 维护逐动词 `cmds` 表——加一个方法要改
  core 入口 + worker 表 + 壳三处，违反 api-contract「worker 泛化分发与
  单常驻拓扑」（人工纠正）
- 规则：wasm 导出恒为单条 `call(handle, method, args)`；分发落点是 core 通用
  `call` + 各资源模块手写 `match`（Rust 无反射，名字→函数必须手写；闭包
  注册表为不存在的自省需求写 downcast 管道，否决）；handle 是
  `number | string`（字符串 = core 模块命名空间，数字 = 实例），禁哨兵值；
  加方法 = 该模块 match 加一臂，worker/壳/types 零改动
- 复发检测：`typescript/src/netwave.worker.ts` 与 wasm glue `.d.ts` grep 逐动词
  入口零命中；worker 往返测试覆盖 `call` 分发（`JsValue` 非 wasm 不可构造，
  分发层原生不可单测）
