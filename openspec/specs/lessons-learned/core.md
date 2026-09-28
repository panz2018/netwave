# LL ledger — scope: core

## Entries

### LL-002 API 命名遵 api-contract

- 犯过：自造 `frequency_in` 被否，改回 `f_scaled`（session 2026-09-27）
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

- 犯过：未包裹被优化器折叠，数字失真（阶段 2 真实基准落地时适用）
- 规则：criterion 基准输入输出均 `black_box`；`scaffold_noop` 为有意 no-op
  不受影响
- 复发检测：review Standards 轴检查 bench 函数体含 `black_box`

### LL-022 core crate `publish = false`

- 犯过：无（预防性记录）
- 规则：core 不独立发布，版本随 workspace 移动
- 复发检测：review 检查 `core/Cargo.toml` 保留 `publish = false`
