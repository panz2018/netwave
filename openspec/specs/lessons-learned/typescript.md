# LL ledger — scope: typescript

## Entries

### LL-001 同步/异步 toY 契约

- 犯过：把 `toY` 实现成独立计算路径，偏离契约（session 2026-09-19）
- 规则：同步 `_toY` 调 core 计算；`async toY` 内部包装 `_toY`，仅超阈值走
  worker；`expect(_toY(x)).toEqual(await toY(x))`
- 复发检测：vitest 双路一致性断言

### LL-007 只用公共 API 面

- 犯过：`dump_js` 用 `_` escape hatch（`2f49f18` 改公共 async 面）
- 规则：测试/示例/脚本只用公共 API，禁 `_` 前缀内部面
- 复发检测：可门禁化——grep 脚本/示例中 `_` 调用即红

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
  （`netwave-{os}-{arch}`）发布时才创建，phase-0 禁列进
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
