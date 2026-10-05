# Tasks

> 本 change 含 durable Rust 骨架与永久内存测试：「red 先于 green」以「先写会失败的
> 三条断言测试」落地；「跨端对拍」体现为浏览器双 realm 与 node 单 realm 两条内存线
> 共享同一组断言（同一 `live_count` 见证）。「教学式 docs」针对功能方法，骨架无功能
> 面，rustdoc 只写内存契约（构造/`Drop`/计数器见证）。

## 1. Red — 三条断言测试（先失败，双端共享）

- [ ] 1.1 写 `typescript/test/browser/memory-lifecycle.test.ts`（真浏览器，
      `vitest.browser.config.ts` 已 `include` `test/browser/**`）：先 fail-fast 断言
      `typeof globalThis.gc === "function"`（区分「环境未开 expose-gc」与「机制失败」）；
      再写三条断言——(1) registry 驱动 free：建壳→丢弃最后引用→`gc()`→轮询
      `liveCount()` 归零；(2) 共享不误删：同 handle 两引用，释放其一 `gc()` 计数不减，
      释放其二 `gc()` 归零；(3) 显式 drop 即时：调 `drop()` 后**不** `gc()`，计数立即减。
      验证：worker/registry/骨架未接线时该测试**失败**（red）。
- [ ] 1.2 写 `typescript/test/native/memory-lifecycle.test.ts`（node，
      `vitest.native.config.ts` 已 `include` `test/native/**`）：同 1.1 三条断言，
      经 napi class 直接持对象（不进 `hosted` Map）；验证：napi class 未接线时失败（red）。

## 2. Green — core 骨架（内存管道，不导出）

- [ ] 2.1 在 `core/src/frequency.rs` 加 `Frequency` struct（持 `Vec<f64>` Hz 存储 +
      `FrequencyUnit`）、`from_f(f_hz: Vec<f64>, unit)` 构造、`impl Drop`（RAII，
      生产零内存管理代码）；`static LIVE: AtomicUsize` 以
      `#[cfg(any(test, feature = "mem-test"))]` 门控（`from_f` `fetch_add(1)`、
      `Drop::drop` `fetch_sub(1)`）+ `live_count()`；`core/Cargo.toml` 加 `mem-test`
      feature；验证：`cargo check -p netwave` 与 `cargo test -p netwave`（含一个 core
      单测断言 `from_f` 后 `live_count()` 增、`drop` 后减）通过。
- [ ] 2.2 rustdoc 写内存契约（教学式：构造分配、`Drop` 即 RAII 释放、`LIVE` 计数器
      **仅测试见证**非内存管理、wasm 线性内存高水位 caveat）；验证：`cargo doc`
      对 `netwave` 无警告。

## 3. Green — wasm/napi class 绑定（`mem-test` 门控，LL-044）

- [ ] 3.1 `typescript/wasm/src/lib.rs` 加 `#[wasm_bindgen]` class（`from_f` 构造、
      `free`/`drop` 方法）+ `live_count()`，均 `#[cfg(feature = "mem-test")]` 门控
      （照 `FrequencyUnit` 的 `cfg_attr` 模板）；`typescript/wasm/Cargo.toml` 转发
      `mem-test` feature；验证：`pnpm -C typescript build:wasm`（带 `mem-test`）成功
      且 glue 导出 class 与 `live_count`。
- [ ] 3.2 `typescript/native/src/lib.rs` 加 `#[napi]` class（`from_f` 构造、`drop`
      方法）+ `live_count()`，同 `mem-test` 门控；`typescript/native/Cargo.toml` 转发
      `mem-test`；验证：`pnpm -C typescript build:native`（带 `mem-test`）成功且
      `.d.mts` 含 class 与 `live_count`。

## 4. Green — worker 地址表 + 主线程 registry（浏览器双 realm）

- [ ] 4.1 `typescript/src/netwave.worker.ts` 加 `frequencies: Map<Handle, Frequency>`
      地址表 + `newFrequency`/`dropFrequency`/`liveCount` 命令，镜像既有
      `upload`/`release` 契约（`dropFrequency` 做 `frequencies.get(handle).free()` +
      `delete`）；验证：worker 可被主线程 postMessage 驱动建/删对象、`liveCount` 回传计数。
- [ ] 4.2 `typescript/src/index.browser.ts` 加主线程 `FinalizationRegistry`（held 只存
      handle 数字，不反向引用 wrapper，见 design「主线程 registry 的 held 值」），
      回调 `postMessage {cmd:"dropFrequency", handle}`；加内部 `newFrequency`/`drop`
      通道（**不从包入口导出** `Frequency`，见 design「骨架内部化」）；验证：断言 1
      转绿（registry 驱动 free）。
- [ ] 4.3 验证断言 2 转绿（共享对象在全部引用消失前不被回收）；若失败，按 design
      「主线程 registry 的 held 值」检查 held 是否误持 wrapper。
- [ ] 4.4 验证断言 3 转绿（显式 `drop()` 不依赖 GC 即时回收）。

## 5. Green — node napi finalizer（单 realm）

- [ ] 5.1 验证 node 端 napi cleanup finalizer 自动 `Drop`（壳 GC 即释放，不进
      `hosted` Map，见 design「node 端」）：1.2 的断言 1/2 转绿；`drop()` 在 node
      可选，断言 3 经 napi `drop` 方法转绿。

## 6. 永久 CI 接线 + 实测结论写回

- [ ] 6.1 `typescript/package.json` 加 `test:memory` 脚本（一条命令跑双端内存测试：
      `vitest run --config vitest.memory.config.ts` 或分别调 browser/native 的内存
      测试文件）；`vitest.memory.config.ts` 经 playwright launch options（浏览器）与
      `poolOptions.*.execArgv`（node）注入 `--expose-gc`；验证：`pnpm -C typescript`
      跑 `test:memory` 全绿。
- [ ] 6.2 `.github/workflows/ci.yml` 加内存测试步骤：以 `--features mem-test` 构建
      wasm + napi，跑 `pnpm -C typescript test:memory`（LL-037：`test:memory` 必须
      在 ci.yml 出现 `typescript test:memory`，否则 `check_ci.py` 红）；验证：
      `python3 scripts/check_ci.py` 退出 0。
- [ ] 6.3 把三条断言实测结果（通过/失败/超时）写回 `Plan/频率类设计.md`「内存管理」
      节：全绿→标注「已实测，可冻结并升铁律八内存扩展」；任一失败/超时→写明触发
      回退（显式 `drop()` 为主、registry 仅兜底）并改写该节架构；验证：Plan 文档反映
      实测结论，`pnpm check:md` 退出 0。
- [ ] 6.4 跑 `pnpm check`（全语言闸门）+ `openspec validate`（带 `--strict` 与本
      change 名）；验证：均退出 0。
