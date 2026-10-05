# Tasks

> 本 change 是 throwaway spike，无 durable 数值 API：tasks 规则中的「跨端对拍」与
> 「教学式 docs」针对数值实现任务，本 spike 不适用（无可发布 API、无三端数值契约）。
> 「red 先于 green」以 spike 形态落地：先写会失败的三条断言测试，再搭原型使其通过。

## 1. Spike 脚手架（隔离，不进主构建）

- [ ] 1.1 建一次性目录 `typescript/spike-memory/`，含独立最小 `#[wasm_bindgen]`
      crate（或 wasm crate 的独立 feature 门）与独立 vitest 配置（仅 `include`
      spike 测试、经 playwright launch options 注入 `--expose-gc`）；验证：目录存在、
      `pnpm check` 主矩阵与 `typescript/package.json` 的 `files` 均未引用该目录。
- [ ] 1.2 在 spike crate 写 `static LIVE: AtomicUsize`，加一个 `#[wasm_bindgen]`
      标注的 `live_count() -> usize` 导出，class `new` 时 `fetch_add(1)`、
      `Drop::drop` 时 `fetch_sub(1)`；验证：`wasm-pack build` 成功且导出 `live_count`。

## 2. Red — 三条断言测试（先失败）

- [ ] 2.1 写断言 1 测试「registry 驱动 free」：建壳→丢弃最后引用→`gc()`→轮询
      `live_count()` 归零；先 fail-fast 断言 `typeof globalThis.gc === "function"`
      （区分「环境未开 expose-gc」与「机制失败」）；验证：worker/registry 未接线时
      该测试**失败**（red）。
- [ ] 2.2 写断言 2 测试「共享不误删」：同 handle 两引用，释放其一 `gc()` 计数不减，
      释放其二 `gc()` 归零；验证：未接线时失败（red）。
- [ ] 2.3 写断言 3 测试「显式 drop 即时」：调 `drop()` 后**不** `gc()`，计数立即减；
      验证：未接线时失败（red）。

## 3. Green — 接线使断言通过

- [ ] 3.1 spike worker 建 `frequencies: Map<Handle, SpikeClass>` 地址表 +
      `new`/`drop`/`liveCount` 命令，镜像 `typescript/src/netwave.worker.ts` 的
      `upload`/`release` 契约；验证：worker 可被主线程 postMessage 驱动建/删对象。
- [ ] 3.2 主线程 `FinalizationRegistry`（held 只存 handle 数字，不反向引用 wrapper），
      回调 `postMessage({cmd:"drop", handle})`；worker `drop` 处理
      `frequencies.get(handle).free()` + `delete`；验证：断言 1 转绿。
- [ ] 3.3 验证断言 2 转绿（共享对象在全部引用消失前不被回收）；若失败，按 design
      D3 检查 held 是否误持 wrapper。
- [ ] 3.4 验证断言 3 转绿（显式 `drop()` 不依赖 GC 即时回收）。

## 4. 结论写回与清理

- [ ] 4.1 把三条断言实测结果（通过/失败/超时）写回 `Plan/频率类设计.md`
      「spike 验证」节：全绿→标注「已实测，可冻结并升铁律八内存扩展」；任一失败/
      超时→写明触发回退（显式 `drop()` 为主、registry 仅兜底）并改写该节架构；
      验证：Plan 文档反映实测结论，`pnpm check:md` 退出 0。
- [ ] 4.2 删除 `typescript/spike-memory/` 整个一次性目录（throwaway，不留存）；
      验证：目录不存在、`pnpm check` 全绿、`git status` 无 spike 残留。
