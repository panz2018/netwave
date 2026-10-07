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

- [x] 2.1 资源表模块（`cfg(feature = "browser")`）改**类型擦除泛型表**：
      `Mutex<BTreeMap<u32, Box<dyn Any + Send>>>` + 单一计数器；模块只有
      `insert<T>`/`with<T>`/`remove` 三泛型操作，不认识任何具体资源类型
      （旧 `Resource` enum 否决：每加资源改表模块，违反开闭）；注册焊死在
      各工厂入口内，无独立注册函数。验证：`cargo check -p netwave` 非
      browser 绿（证 cfg 隔离）；`cargo test -p netwave --features browser`
      句柄表用例（注册/查表/`drop` 触发 `Drop`/未知句柄报错/错类型 downcast
      报错）全绿（本机未装 wasm32 target：表逻辑拆纯函数 native 验证，
      `#[wasm_bindgen]` 适配层由组 5 worker 往返覆盖）。
- [x] 2.2 各资源的 `#[wasm_bindgen]` 句柄入口写回**各自模块**（同 feature
      门控）：`network_upload`/`network_fill_pattern`/`network_read_element`
      入 `network.rs`，`frequency_from_f` 入 `frequency.rs`，`drop`/
      `frequency_units`/`live_count` 留 `resources.rs`（类型无关）；
      `drop(handle)` = `remove` 直接触发 Rust `Drop`，不经 JS 对象中转。
      验证：2.1 同一套测试全绿；未来新资源只在自己模块加入口。

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

- [x] 5.1 `typescript/src/netwave.worker.ts`：删除 `hosted`/`frequencies`/
      `nextHandle`（JS 零状态）；命令表改为机械 camelCase 转发 core 句柄入口
      （`networkUpload`/`networkFillPattern`/`networkReadElement`/
      `frequencyFromF`/`drop`/`frequencyUnits`/`liveCount`）；`release`/
      `dropFrequency`/`newFrequency` 消失；错误文案 `unknown or released handle`
      →`unknown or dropped handle`（错误源由 core throw 透传）。验证：worker
      往返测试全绿。
- [x] 5.2 `typescript/src/index.browser.ts`：导出 `Network`/`Frequency` 壳类
      （实例持 `@internal` 数字 handle，方法体纯 `postMessage`；
      `Network.upload(view, nfreq, nports)` 显式传 shape）；
      `FinalizationRegistry` 挂壳实例、held 为数字 handle、回调发
      `{cmd:"drop", handle}`；`internals` 测试缝退役；自由函数
      `frequencyUnits`/`liveCount` 保留。验证：`pnpm -C typescript typecheck`
      通过、`typescript/src` grep `release`/`dropFrequency`/`newFrequency` 零命中。
- [x] 5.3 `typescript/src/index.node.ts`：删除 `hosted` Map 与 `lastHandle`，
      `upload`/`release`/`readElement` 自由函数退役，改由 4.1 的 napi 类搬运
      导出；`typescript/src/types.ts` 同步（`Handle` 降 `@internal` 或删除）。
      验证：typecheck 通过、node 壳 grep `hosted`/`release` 零命中。
- [x] 5.4 测试改写：`typescript/test/wasm` 下 `worker`/`memory-lifecycle`/
      `browser-roundtrip`/`browser-surface` 与 `typescript/test/browser/`
      `browser-resident.test.ts`（句柄函数流改壳类实例方法、导出名断言列表
      同步为 `Network`/`Frequency`）。验证：`pnpm -C typescript test:wasm` 与
      `test:browser` 全绿（真 Chromium 常驻 worker）。

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

## 8. 全量验收

- [x] 8.1 `pnpm check` 全绿（md/ts/rs/py/meta）。
- [x] 8.2 `pnpm check:cross` 全绿（四端 dump 对拍 + 动词集合相等）。
- [x] 8.3 四端测试全绿：`cargo test --workspace`、pytest、
      `pnpm -C typescript test:native`、`test:wasm`、`test:browser`。
- [x] 8.4 全仓 grep 验收：core/python/typescript 的 `.rs`/`.py`/`.ts` 中
      `.free()` 与 `release(` 用户可见面零命中（豁免：`mem::forget`、
      `free list` 注释、`target/release` 路径——句柄表下沉 core 后 wasm 生成物
      `free()` 已无调用点）；`dropFrequency`/`newFrequency`、JS 侧 `hosted`/
      `frequencies`/`nextHandle` 全仓零命中；node/Python 公开面无 `upload`。
