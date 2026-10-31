# LL ledger — scope: typescript

## Entries

### LL-017 napi/wasm 绑定实现细节

- 犯过：napi `Buffer::from(vec)` 内部 `mem::forget`，JS 侧重建须传满容量
  （`Complex<f64>` = `v.capacity()*16` 字节）否则 GC double-free；返回裸
  Vec 退化为逐元素 JS Array；napi CLI 旗标升级漂移（`--manifest-path` 非
  `--cargo-cwd`、`--format commonjs` 非 `cjs`）；wasm target 用 `web` 非
  `bundler`（bundler glue 在 node/vitest 加载不了）；wasm init 传
  `{ module_or_path: bytes }`（node 无 `fetch("file:...")`）；
  `js_sys::WebAssembly::Memory`（无 `js_sys::Memory`）；wasm 线性内存
  transfer 会 detach instance，须 `.slice()` 出新 ArrayBuffer 再 transfer；
  `src/` shell import `"../dist/..."`，`publish_shell.mjs` 复制进 `dist/`
  时改写为 `"./..."`——只改 `src/` 禁手改 `dist/`；平台分包
  （`netwave-{os}-{arch}`）发布时才创建，脚手架期禁列进
  `optionalDependencies`（未发布名破坏 frozen-lockfile）
- 规则：按上列约束实现；napi 升级后重查旗标
- 复发检测：`pnpm -C typescript build:native && build:wasm` + vitest 双套件

### LL-024 改 core 后重建 node/wasm

- 犯过：未重建即测试/对拍，比到陈旧产物
- 规则：`pnpm build:native` + `build:wasm` 先于任何测试/对拍
- 复发检测：`pnpm check:cross` 前置重建

### LL-025 覆盖率豁免用 v8 ignore 且逐条附理由

- 犯过：无（预防性，铁律七落地）
- 规则：`/* v8 ignore start/stop */` + 每条理由注释；禁整文件豁免
- 复发检测：vitest coverage 配置 + review Standards 轴 grep

### LL-026 容器内 napi machine-id 坑

- 犯过：容器报 `Skipping cross-process filesystem reconciliation lock`
  （missing: machine）
- 规则：`/etc/machine-id` 须 `^[0-9a-f]{32}$`（带横线 UUID 校验失败）；
  无害仅跳锁；消音：
  `cat /proc/sys/kernel/random/uuid | tr -d '-' | sudo tee /etc/machine-id`
- 复发检测：文字规则（环境类，不可自动门禁）

### LL-050 wasm glue 清空后须 `extern crate` 强制链接 core

- 犯过：把 wasm 入口全部下沉 core 后，glue crate `lib.rs` 只剩文档注释、
  无任何对 `netwave` 的引用，Rust 不再把 core 链进 cdylib，`wasm-pack build`
  产出的 `.js`/`.d.ts` 导出面为空（worker 全部命令 unknown）
- 规则：入口全在 core 时，glue `lib.rs` MUST 保留 `extern crate netwave;`
  强制链接，否则 core 的 `#[wasm_bindgen]` 导出全部丢失
- 复发检测：`pnpm -C typescript build:wasm` 后 grep glue 的
  `netwave_wasm.d.ts` 含 `network_upload` 等入口；worker 往返测试即红

### LL-051 napi `usize` 映射 bigint 破坏三端类型平价

- 犯过：node `Frequency::npoints()` 返回 `usize`，napi 映射成 JS `bigint`，
  而 wasm/Python 同方法返回 `number`/`int`，三端类型不一致（铁律九）
- 规则：跨端返回整数一律 `u32`（f64 精确可表示），MUST NOT 用 `usize`/
  `isize`（napi→bigint）；与 `live_count` 同因（见 frequency.rs 注释）
- 复发检测：review Standards 轴 grep napi 签名中的 `usize`/`isize`；
  `check_vocab_types.py` 扩类型断言时覆盖返回类型

### LL-054 napi-cli 与 napi crate 配对升级

- 犯过：`@napi-rs/cli` 3.10.5→3.10.8 与 napi crate 3.13→3.14 同时升，
  生成的 `index.node.generated.mjs` 解构列表漏掉 `FrequencyUnit`/
  `WavelengthUnit`/`frequencyUnits`/`liveCount`（`.node` 二进制仍导出，
  d.ts 仍声明，运行时值 undefined，13 测试红）——cli 3.10.8 读 crate 3.14
  abi 时丢枚举（人工审计升级发现）
- 规则：napi 三件套（cli/crate/derive-backend）配对升级；升级后必须
  grep 生成的 mjs 确认枚举名在解构列表内，不能只看 d.ts；组合回归时
  优先保 Rust crate 最新（影响产物），钉死 cli 精确版本（`^` 会漂移）
- 复发检测：`typescript/test/native/frequency-unit.test.ts` 读
  `FrequencyUnit.GHz` 即红；`pnpm build:native` 后 grep generated mjs
  枚举名零命中即红
