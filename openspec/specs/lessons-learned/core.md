# LL ledger — scope: core

## Entries

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
  门控范围不止注册调用：glue 里 `cast::<被门控 pyclass>()` 的**辅助函数**与
  签名含被门控枚举的 **`#[pymethods]` 整块**同样要 `not(coverage)`，
  否则 E0599/E0277（Frequency pyclass 复发一次）。
  `cfg(coverage)` 须在用到的每个 crate 的 `[lints.rust]` 声明 `check-cfg`，
  否则 `-D warnings` 报 unexpected_cfgs
- 复发检测：`cargo llvm-cov -p netwave --codecov` + `coverage_gate.py`（rust job）；
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

### LL-062 worker 内无 `window`，wasm 取全局一律走 `js_sys::global()`

- 犯过：`Touchstone.fromUrl` 浏览器实现用 `web_sys::window()` 取 fetch，
  dedicated worker 里没有 `window`，返回 `None` 直接报错——本地 node 模拟
  全绿，真浏览器套件（`fromUrl` 用例）才暴露
- 规则：wasm 端凡取全局对象/发起 fetch，MUST 走 `js_sys::global()` 再
  `dyn_ref` 到 `web_sys::Window` 或 `web_sys::WorkerGlobalScope`（两者均
  暴露 `fetch_with_str`）；两者皆非时报显式错误。MUST NOT 假设 `window`
  存在（铁律八：浏览器计算跑在常驻 worker 内）
- 复发检测：grep core 的 wasm cfg 代码段出现 `web_sys::window()` 即打回；
  浏览器套件含 `fromUrl` 真实 fetch 用例且 CI 常绿

### LL-057 llvm-cov 默认 report 按实例计缺，100% 闸门用 --codecov 行合并

- 犯过：`cargo llvm-cov -p netwave` 默认走 `llvm-cov report`，按
  **实例**分别计数：每个集成测试二进制静态链接 core 并各自 inline 一份
  私有 helper，其中仅由 lib 单元测试触达的防御臂在其副本中永不执行，
  每副本独立计缺 → touchstone.rs 恒差 6 行（99.21%）；`inline(never)`、
  `--remap-path-prefix`、清缓存重建均无效（实测：逐二进制 union 零缺失，
  report 仍报 6）
- 规则：`--codecov` 只改**输出格式**（走 `llvm-cov show` 语义，同一行
  任一二进制执行过即计覆盖，OR 合并；实测 codecov.json 950/950=100%），
  但 `--fail-under-lines` **不读 codecov 输出**——它读 `llvm-cov report`
  的按实例数字（上游 src/report.rs 实证；实测阈值 99.3 绿 / 99.4 红
  = 99.39%，永远到不了 100）。所以 100% 闸门 MUST 用 `scripts/coverage_gate.py`
  直接读 codecov.json（OR 语义，与其他语言工具一致），MUST NOT 用
  `--fail-under-lines` 做 100% 地板。绑定胶水仍由 pytest-cov/vitest 自身
  job 度量，MUST NOT `--workspace` 并入 core
- 复发检测：CI llvm-cov job 命令含
  `-p netwave --codecov --output-path codecov.json` + `coverage_gate.py`；
  出现 `--fail-under-lines 100` 即红（它读 report，防御臂必红）

### LL-072 钉死交错布局的三条理由与代价

- 犯过：无（预防性，铁律一定契约时的 rationale 自宪法迁入，宪法只留契约句）
- 规则：`(nfreq, nports, nports)` 交错 f64 顺序钉死的依据：① Touchstone
  按频率逐行存储，流式解析线性拷贝无转置；② 热路径逐频点 (p×p) 矩阵运算，
  每频点矩阵连续；③ rayon 沿大轴 `nfreq` 切分负载均衡。代价（单条 trace
  跨步）属显示/IO 路径，非热路径。改布局前必读本节
- 复发检测：布局变更提案 review 时核对是否重新论证这三条理由（Standards 轴）
