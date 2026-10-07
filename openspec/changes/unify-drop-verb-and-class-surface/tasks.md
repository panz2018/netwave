# Tasks

## 1. core：`drop()` 改名 + `Network` 骨架

- [x] 1.1 `core/src/frequency.rs`：`Frequency::release()` 重命名为 `drop()`，
      `impl Drop::drop` 一行委托固有方法 `self.drop()`；同步更新 rustdoc 与字段
      注释。验证：`cargo test -p netwave` 全绿；`cargo clippy` 配
      `--workspace --all-targets -D warnings` 零警告（固有方法优先解析，无递归）。
- [x] 1.2 core 单测：`drop()` 后 `npoints()` 报错（非返回 0）、二次
      `drop()` 幂等、`live_count()` 只减一次；RAII 路径（离开作用域）行为
      不变。验证：`cargo test -p netwave` 新增用例先 red 后 green。
- [x] 1.3 `core/src/network.rs`（新增骨架）：`Network` 持频率/端口维度与
      `Vec<f64>` 数据 + `dropped` 见证；`from_f64(nfreq, nports, data)`
      构造、`fill_pattern(nfreq, nports)` 工厂、`read_element(idx)`、
      `drop()`（`Drop::drop` 同款委托）。零计算/解析/端口语义。验证：
      `cargo test -p netwave` 骨架用例（构造/读/释放/释放后读报错）先 red
      后 green。
- [x] 1.4 core 收尾（裁决：无 `isDropped` 见证、释放后报错 core 单源、
      动词零残留）：错误类型 `Released` 改名 `Dropped` 并提到 `lib.rs`
      全资源共享；删除 `Network::is_dropped`/`Frequency::is_dropped`
      （释放后访问报错即契约，不另设第二套真相源）；`Frequency::npoints()`
      释放后返回 `Err(Dropped)`（修 node 曾返回 0 的 bug，判断不在绑定层
      重写）；rustdoc 散文里 release/released 措辞全改 drop/dropped。
      验证：`cargo test -p netwave` 全绿；`cargo clippy` 配
      `--workspace --all-targets -- -D warnings` 零警告；core/src grep
      `release` 零命中。

## 2. core：浏览器资源表（cfg=browser）

- [ ] 2.1 资源表模块（`cfg(feature = "browser")`）改**泛型分发表**：
      `Mutex<Registry>`，内含实例表（`u32 → Box<dyn Resource>`）、命名空间表
      （`&'static str → NamespaceFn`）与单一计数器；`Resource` trait 只有一个
      `call` 方法（收方法名与 `JsValue` 参数数组）；命名空间函数指针承接工厂
      与模块自由函数；分发器 `#[wasm_bindgen] call` 收 handle/方法名/参数：
      数字 → 实例表（`method=="drop"` → `remove` 触发 `Drop`），字符串 →
      命名空间表；无哨兵 handle。表模块不认识任何具体资源类型，加动词零改动。
      验证：`cargo check -p netwave` 非 browser 绿（证 cfg 隔离）；表逻辑
      （insert/remove/命名空间路由/未知句柄报错）拆纯 Rust 函数 native 测绿，
      `JsValue` 适配层由组 5 worker 往返覆盖。
- [ ] 2.2 删除逐动词 `#[wasm_bindgen]` 入口（`network_upload`/
      `network_fill_pattern`/`network_read_element`/`frequency_from_f`/
      `frequency_npoints`），改为各资源模块实现 `Resource::call` 手写 `match`
      （方案 A；闭包注册表否决：为不存在的自省需求写 downcast 管道；属性宏
      `#[resource]` 缓建为方法面膨胀后的升级路径）+ `call_namespace` 工厂
      `match`；`#[wasm_bindgen(start)]` 在 `lib.rs` 调 `network::register()`/
      `frequency::register()` 挂命名空间。验证：wasm 导出面 grep 逐动词入口
      零命中（glue `.d.ts` 只剩 `call` + `FrequencyUnit` + 词汇函数）；
      加方法 = 该模块 match 加一臂，worker/壳/types 零改动（往返测试证明）。

## 3. Python：`Network`/`Frequency` pyclass 首次导出

- [x] 3.1 先写失败测试 `python/tests/test_memory_lifecycle.py`：`Network(data)`
      构造后 `read_element(idx)` 正确、`drop()` 后访问抛 `ValueError`、二次
      `drop()` 不报错、不调 `drop()` 时引用计数回收后 `live_count()` 归零；
      `Frequency.from_f(...)` 同套断言。验证：pytest 该文件 red（类未导出）。
- [x] 3.2 `python/src/lib.rs`：注册 `Network`（构造器收数据 + `nfreq`/
      `nports` shape + `read_element` + `drop`）与 `Frequency`（`from_f` +
      `drop`）pyclass，`#[pymethods]` 直接
      命名（零名字映射）；`python/netwave/__init__.py` 再导出。验证：3.1 转
      green；公开面无 `upload`。
- [x] 3.3 重新生成 `.pyi`（stub_gen）。验证：`_netwave.pyi` grep `release` 与
      `free` 零命中，新签名含 `drop`/`read_element`/`from_f`。

## 4. node：napi 类形态 + `free()` 改名

- [x] 4.1 `typescript/native/src/lib.rs`：`Frequency` wrapper 的 `pub fn free`
      重命名 `pub fn drop`（wrapper 无 `impl Drop`，无遮蔽）；新增 `Network`
      napi 类（构造器收 Float64Array + `nfreq`/`nports` shape + `readElement` + `drop`），rustdoc 同步。
      验证：重建后 native 源码与 `.d.mts` 用户可见面 grep `free` 零命中。
- [x] 4.2 重建 node glue（`pnpm -C typescript build:native`，带 `--dts`，
      LL-043）。验证：`.d.mts` 中 `Network`/`Frequency` 均有 `drop(): void` 与
      `readElement`、无 `free`、无 `upload`。
- [x] 4.3 测试改写：`typescript/test/native/memory-lifecycle.test.ts`
      （`f.free()`→`f.drop()`）、`typescript/test/native/`
      `native.roundtrip.test.ts`（`upload`/`release` 句柄流改 `new Network()` +
      实例 `readElement`/`drop()`）。验证：`pnpm -C typescript test:native` 全绿。

## 5. 浏览器：壳类 + worker 零状态

- [ ] 5.1 `typescript/src/netwave.worker.ts`：删除 `hosted`/`frequencies`/
      `nextHandle` 与逐动词 `cmds` 表（`networkUpload`/`networkFillPattern`/
      `networkReadElement`/`frequencyFromF`/`frequencyNpoints`/`drop`/
      `frequencyUnits`/`liveCount`），退为**单条固定模板**：收到
      `{id, handle, method, args}` 后 await wasm ready、原样转发 core
      `call(handle, method, args)`，结果/错误机械回传——与动词数量无关，
      以后加方法本文件零改动。验证：worker 往返测试全绿；本文件 grep 动词名
      零命中。
- [ ] 5.2 `typescript/src/index.browser.ts`：壳类方法改发泛化消息——工厂/
      静态方法发字符串 handle（`{handle:"network", method:"upload"}`，命名空间
      = core 模块名；方法名 = core 名机械 camelCase，不重命名），实例方法发
      数字 handle（`{handle:7, method:"readElement"}`）；
      `FinalizationRegistry` 回调发 `{handle, method:"drop", args:[]}`；
      自由函数 `frequencyUnits`/`liveCount` 经 `"frequency"` 命名空间路由进
      worker（名单在 Rust 拼、计数在 Rust 读，壳只发一条 `postMessage`，
      **零计算**——铁律十一；`liveCount` 数的就是 `Frequency`，同归 `"frequency"`
      不新造 `"system"`）；`FrequencyUnit` 常量对象保持主线程直 import glue
      （普通常量对象，import 不实例化 wasm，不走 worker）。验证：typecheck
      通过、grep `cmd` 零命中、壳内无 `Object.keys` 等派生计算。
- [ ] 5.3 `typescript/src/types.ts`：`WorkerRequest` 从 `{id, cmd, args}` 改
      `{id, handle: Handle | string, method: string, args: unknown[]}`
      （`Handle` 保持 `number`，字符串 handle = 命名空间名，均 `@internal`）；
      `index.node.ts` 不受影响（已在 4.x 改完）。验证：typecheck 通过。
- [ ] 5.4 测试改写：`typescript/test/wasm` 下 `worker`/`memory-lifecycle`/
      `browser-roundtrip`/`browser-surface` 与 `typescript/test/browser/`
      `browser-resident.test.ts`（消息断言改 `{handle, method, args}` 形态；
      新增「加动词零改动」哨兵：对 worker 源码 grep 动词名零命中）。
      验证：`pnpm -C typescript test:wasm` 与 `test:browser` 全绿（真 Chromium
      常驻 worker）。

## 6. 门禁：三端动词集合相等

- [x] 6.1 新增 `scripts/check_verbs.py`（与 `check_vocab_types.py` 同范式：
      二进制对拍器 `cross_compare.py` 只吃 `.bin`，静态动词门禁独立成脚本才能
      职责单一）：从三份生成物（`.pyi` / node `.d.mts` / browser `.d.mts`）提取
      `Network`/`Frequency` 类方法名（含静态与实例）与模块级自由函数名，
      camelCase 机械映射归一后断言等于唯一动词集；`upload` 仅浏览器；
      `free`/`release` 作为名字出现在任一用户可见产物即红。
      验证：`python3 scripts/check_verbs.py` 绿；人为注入一个 `free` 方法别名
      与一个 `release` 自由函数后该脚本各红一次（已实测，自检）。
- [x] 6.2 `pnpm check:cross` 串起 6.1（LL-037/LL-047）。验证：
      `pnpm check:cross` 全绿且 CI 对应 job 存在（`scripts/check_ci.py` 绿）。
- [ ] 6.3 `scripts/check_verbs.py` 加钉死 wasm glue 导出面：解析 glue `.d.ts`，
      顶层导出集合 MUST 恰为 `call` + `FrequencyUnit`（+ wasm-pack 生成的
      init/默认导出）——多一个少一个都红。这是「单条 `call`」不变式的机械钉子：
      谁再给某函数挂 `#[wasm_bindgen]` 直导出即红（LL-052 复发检测）。
      验证：当前绿；人为给 `live_count` 加回 `#[wasm_bindgen]` 后该检查红一次。

## 7. 文档与账本

- [x] 7.1 lessons-learned 账本：新增 LL（typescript scope）「node 曾暴露
      `free()` 偏离 memory-lifecycle spec 的 `drop()`——实现偏离 spec 时当轮登记
      并改名回归」+ INDEX 行。验证：`pnpm check:md` 绿。
- [x] 7.2 `Plan/频率类设计.md`：「待裁决」条目销账（裁决=全端 `drop()` +
      `Frequency.fromF`）；`Plan/总体计划.md`：`upload`/`release` 改
      `upload`/`drop`、Network 释放措辞 `dispose()` 改 `drop()`、「worker 资源表
      收拢」与「公开面收敛」中已由本 change 兑现的部分销账。验证：
      `pnpm check:md` 绿。
- [x] 7.3 README/CONTRIBUTING 中 `release`/`free` 旧动词示例同步改 `drop`，
      示例改用 `Network`/`Frequency` 类形态。验证：根/子 README 与 CONTRIBUTING
      grep 旧动词仅剩非动词用法（如 release 版本）。

## 8. 全量验收（泛化分发返工后重跑）

- [ ] 8.1 `pnpm check` 全绿（md/ts/rs/py/meta）。
- [ ] 8.2 `pnpm check:cross` 全绿（四端 dump 对拍 + 动词集合相等）。
- [ ] 8.3 四端测试全绿：`cargo test --workspace`、pytest、
      `pnpm -C typescript test:native`、`test:wasm`、`test:browser`。
- [ ] 8.4 全仓 grep 验收：core/python/typescript 的 `.rs`/`.py`/`.ts` 中
      `.free()` 与 `release(` 用户可见面零命中（豁免：`mem::forget`、
      `free list` 注释、`target/release` 路径——句柄表下沉 core 后 wasm 生成物
      `free()` 已无调用点）；`dropFrequency`/`newFrequency`、JS 侧 `hosted`/
      `frequencies`/`nextHandle` 全仓零命中；node/Python 公开面无 `upload`；
      worker 与 wasm 导出面逐动词入口（`network_*`/`frequency_from_f`/
      `frequency_npoints`）零命中（泛化 `call` 是唯一分发入口）。
