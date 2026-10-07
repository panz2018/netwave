# Tasks

## 1. core：`release()` 重命名为 `drop()`

- [ ] 1.1 `core/src/frequency.rs`：`Frequency::release()` 重命名为 `drop()`，
      `impl Drop::drop` 一行委托固有方法 `self.drop()`；同步更新 rustdoc 与字段注释。
      验证：`cargo test -p netwave` 全绿；`cargo clippy --workspace --all-targets`
      配 `-D warnings` 零警告（固有方法优先解析，无递归）。
- [ ] 1.2 core 单测：`drop()` 后 `npoints()` 为 0、二次 `drop()` 幂等、
      `live_count()` 只减一次；RAII 路径（离开作用域）行为不变。验证：
      `cargo test -p netwave` 新增用例先 red 后 green。

## 2. Python：导出 `Frequency` pyclass 含 `drop()`

- [ ] 2.1 先写失败测试 `python/tests/test_memory_lifecycle.py`：`drop()` 后访问
      `f`/`npoints` 抛 `ValueError`、二次 `drop()` 不报错、不调 `drop()` 时引用计数
      回收后 `live_count()` 归零。验证：pytest 该文件 red（类未导出）。
- [ ] 2.2 `python/src/lib.rs`：注册 `Frequency` pyclass（`#[pymethods]` 直接命名
      `drop`，零名字映射），释放后访问抛 `PyValueError`；`python/netwave/__init__.py`
      再导出。验证：2.1 测试转 green。
- [ ] 2.3 重新生成 `.pyi`（stub_gen）。验证：`_netwave.pyi` grep `release` 与
      `free` 零命中，新签名含 `drop`。

## 3. node：napi `free()` 重命名为 `drop()`

- [ ] 3.1 `typescript/native/src/lib.rs`：`pub fn free` 重命名为 `pub fn drop`
      （wrapper 无 `impl Drop`，无遮蔽），rustdoc 同步。验证：重建后 native 源码与
      `.d.mts` 用户可见面 grep `free` 零命中。
- [ ] 3.2 重建 node glue（`pnpm -C typescript build:native`，带 `--dts`，
      LL-043）。验证：`.d.mts` 中 `Frequency` 有 `drop(): void`、无 `free`。
- [ ] 3.3 测试改名：`typescript/test/native/memory-lifecycle.test.ts`
      （`f.free()`→`f.drop()`，用例标题同步）、`typescript/test/native/`
      `native.roundtrip.test.ts`（`release`→`drop`）。验证：
      `pnpm -C typescript test:native` 全绿。

## 4. 浏览器：句柄动词与 worker 命令统一 `drop`

- [ ] 4.1 `typescript/src/netwave.worker.ts`：`hosted` 与 `frequencies` 合并为单一
      `resources` 表；命令表 `release`/`dropFrequency` 收拢为单一 `drop`（按句柄
      取资源后分派：wasm `Frequency` 调生成物 `free()`——豁免，裸字节缓冲直接
      删除）；错误文案 `unknown or released handle`→`unknown or dropped handle`。
      验证：worker 往返测试全绿。
- [ ] 4.2 `typescript/src` 三文件（`index.browser`/`index.node`/`types`）：
      `release(handle)` 导出重命名 `drop(handle)`，JSDoc 同步；`index.browser.ts`
      的 `FinalizationRegistry` 回调改发 `{cmd:"drop", handle}`；node 壳同步暴露实例
      `drop()`（经 3.1 绑定搬运）。验证：`pnpm -C typescript typecheck` 通过、
      `typescript/src` grep `release` 与 `dropFrequency` 零命中。
- [ ] 4.3 测试改名：`typescript/test/wasm` 下 `worker`/`memory-lifecycle`/
      `browser-roundtrip`/`browser-surface` 与 `typescript/test/browser/`
      `browser-resident.test.ts`（`release`→`drop`、导出名断言列表同步）。验证：
      `pnpm -C typescript test:wasm` 与 `test:browser` 全绿（真 Chromium 常驻 worker）。

## 5. 门禁：三端动词集合相等

- [ ] 5.1 `scripts/cross_compare.py`：新增公开动词集合提取（core `pub fn` /
      pyo3 `#[pymethods]` / napi `#[napi]` / TS 壳导出），camelCase 机械映射归一后
      断言相等；`free`/`release` 出现在用户可见面即红。验证：本地
      `python3 scripts/cross_compare.py .cross-tmp` 绿；人为注入一个 `free` 别名后
      该脚本红（自检）。
- [ ] 5.2 确认 `pnpm check:cross` 已串起 5.1（LL-037/LL-047）。验证：
      `pnpm check:cross` 全绿且 CI 对应 job 存在（`scripts/check_ci.py` 绿）。

## 6. 文档与账本

- [ ] 6.1 lessons-learned 账本：新增 LL（typescript scope）「node 曾暴露
      `free()` 偏离 memory-lifecycle spec 的 `drop()`——实现偏离 spec 时当轮登记并
      改名回归」+ INDEX 行。验证：`pnpm check:md` 绿。
- [ ] 6.2 `Plan/频率类设计.md`：「待裁决」条目销账（裁决=全端 `drop()`，含
      `upload`/`drop` 句柄对）；`Plan/总体计划.md`：`upload`/`release` 改
      `upload`/`drop`、Network 释放措辞 `dispose()` 改 `drop()`、「worker 资源表
      收拢」待决条目删除（本 change 已定案收拢）。验证：`pnpm check:md` 绿。
- [ ] 6.3 README/CONTRIBUTING 中 `release`/`free` 旧动词示例同步改 `drop`。
      验证：根/子 README 与 CONTRIBUTING grep 旧动词仅剩非动词用法（如 release 版本）。

## 7. 全量验收

- [ ] 7.1 `pnpm check` 全绿（md/ts/rs/py/meta）。
- [ ] 7.2 `pnpm check:cross` 全绿（四端 dump 对拍 + 动词集合相等）。
- [ ] 7.3 四端测试全绿：`cargo test --workspace`、pytest、
      `pnpm -C typescript test:native`、`test:wasm`、`test:browser`。
- [ ] 7.4 全仓 grep 验收：core/python/typescript 的 `.rs`/`.py`/`.ts` 中
      `.free()` 与 `release(` 用户可见面零命中（豁免：worker 内部对 wasm 生成物
      的 `f.free()`、`mem::forget`、`free list` 注释、`target/release` 路径）；
      `dropFrequency` 全仓零命中。
