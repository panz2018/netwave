# LL ledger — scope: typescript

## Entries

### LL-001 同步/异步 toY 契约

- 犯过：把 `toY` 实现成独立计算路径，偏离契约
- 规则：同步 `_toY` 调 core 计算；`async toY` 内部包装 `_toY`，仅超阈值走
  worker；`expect(_toY(x)).toEqual(await toY(x))`
- 复发检测：vitest 双路一致性断言
- **修订**："小数据不起 worker"分流随 worker 常驻架构（见
  `Plan/typescript源码化规划.md`）废止——所有计算不管大小
  全进常驻 worker；
  浏览器端 `_` 同步计算逃生口废止（主线程无 wasm），node 端保留 `_`（napi
  core 在进程内）；双路一致性断言改为 worker 往返 vs `_toY`（仅 node）

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

### LL-030 主线程 wasm 实例退役（worker 常驻架构）

- 犯过：脚手架期壳在主线程 init wasm 与 worker 双实例并存，主线程可持数据副本，
  权威歧义（worker 常驻架构定案时纠正）
- 规则：浏览器端数据/状态/计算全常驻单个 worker 内 wasm，主线程不 init wasm、
  不持数据副本；元数据搭结果便车回传，主线程只从返回值同步读描述符；实现时
  旧壳双实例模式不得回流
- 复发检测：真浏览器测试线（vitest browser mode，随 worker 实现落地）断言
  upload 后主线程视图 detached；review 轴 grep 主线程壳中
  `wasmInit`/`WebAssembly.instantiate`

### LL-031 同步元数据读取改异步

- 犯过：契约曾定"属性/元数据（`shape`/`frequency`）保持同步"，主线程无 wasm 后
  不成立（worker 常驻架构定案时纠正）
- 规则：计算与元数据一律异步进 worker；已 resolve 结果描述符上的元数据可同步
  读；worker 异常终止数据丢失为已接受行为，不引入 IndexedDB 恢复
- 复发检测：api-contract 类型面元数据访问器全为 `Promise`（node 端 `_` 除外）
