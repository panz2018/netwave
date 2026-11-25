# Tasks

## 1. 范围与前置（red 先于 green）

- [ ] 1.1 `范围只清browser`：确认本 change 仅动 browser 绑定，python/node（阶段 C）
      不在本次 diff 内；验收：diff 文件集不含 `python/`、`typescript/native/`。
- [ ] 1.2 写失败测试：grep `core/src/` 含 `wasm_bindgen`（搬迁前应命中，作为
      red 基线）；写 `cargo tree -p netwave` 断言当前仍含 wasm-bindgen（red）。
- [ ] 1.3 写失败测试：browser 枚举 ordinal 一致性单测——比对生成物
      `values.generated.mjs` 成员 ordinal 与 core `from_ordinal`（生成物未建即 red）。
- [ ] 1.4 写失败测试：fetch「无 fetch-capable scope」臂单测——传无 fetch 能力假
      global，断言返回 Fetch 错误（注入点未建即 red）。

## 2. 句柄表与 dispatch 搬迁

- [ ] 2.1 `resources进browser`：`core/src/resources.rs` → `browser/src/resources.rs`，
      句柄表 + `Resource` trait + `#[wasm_bindgen] call` 适配器随迁。
- [ ] 2.2 `句柄表测试单元测试`：`core/tests/resources_table.rs` →
      `browser/src/resources.rs` 底部 `#[cfg(test)] mod tests`，不动 crate-type。
- [ ] 2.3 frequency/touchstone 的 `impl Resource` + `call_namespace` + `register` + helpers → `browser/src/frequency_glue.rs` / `touchstone_glue.rs`。
- [ ] 2.4 `#[wasm_bindgen(start)] register_resources()` → `browser/src/lib.rs`。
- [ ] 2.5 `cov-drive进browser`：`drive_copy_arms()` 随 dispatch 进 browser，core
      删 `cov-drive` feature。
- [ ] 2.6 验证：`pnpm test:browser` 全绿；grep `core/src/` 零 `wasm_bindgen`（1.2
      red 转 green）。

## 3. 枚举构建期生成

- [ ] 3.1 `gen_values合并`：`browser/scripts/gen_constants.mjs` 改名
      `gen_values.mjs`，新增从 core enum 抽变体名+ordinal 段，输出单文件
      `values.generated.mjs`/`.d.mts`（常量+两枚举合一）；命令改 `gen:values`
      （`browser/package.json`）。
- [ ] 3.2 `index-browser-import源`：`browser/src/index.browser.ts` 从
      `values.generated.mjs` import 常量+两枚举；worker JS / types.ts 零改动。
- [ ] 3.3 `check_verbs导出集合`：`scripts/check_verbs.py` 的 `WASM_GLUE_EXPORTS`
      改 `{call, register_resources}`，新增校验 `values.generated.mjs` 含两枚举。
- [ ] 3.4 同步 `browser/tsdown.config.ts`（匹配 `values.generated`）与
      `typescript/scripts/merge_browser.mjs`（复制清单改 `values.generated.*`）。
- [ ] 3.5 验证：1.3 ordinal 一致性单测转 green；`pnpm test:browser` 绿。

## 4. from_url / fetch 搬迁与覆盖率地板

- [ ] 4.1 `core删browser-http`：core 删 `browser-http` feature 与
      web-sys/wasm-bindgen-futures 依赖；browser `fromUrl` arm 自调 web_sys::fetch + core `Touchstone::from_text`。
- [ ] 4.2 `promise在browser`：fromUrl 的 Promise 包装 + fetch 全在 browser arm；
      core native `from_url`(reqwest) 不动。
- [ ] 4.3 `url_filename改pub`：core `url_filename` 改 pub，browser `fromUrl` arm
      复用；确认/补 query-fragment 剥离单测。
- [ ] 4.4 fetch global 参数注入：生产传 `js_sys::global()`、测试传假 scope；
      1.4 red 转 green。
- [ ] 4.5 `wasm地板100`：`browser/scripts/test.sh` 的 `coverage_gate.py ... 99`
      → `100`。
- [ ] 4.6 `覆盖率链grep路径`：test.sh 的 `.ll` grep 从 `core/src/...` 改
      `browser/src/...`。
- [ ] 4.7 验证：`pnpm test:browser` 全链 exit 0，coverage_gate.py 对
      `coverage/coverage-browser.lcov` 以地板 100 阅卷通过。

## 5. core 依赖清理

- [ ] 5.1 `browser零feature依赖`：`browser/Cargo.toml` 改
      `netwave = { path = "../core" }` 零 feature。
- [ ] 5.2 core `Cargo.toml` 删 wasm-bindgen/js-sys/web-sys/wasm-bindgen-futures
      依赖与 `browser`/`browser-http`/`cov-drive` feature；删枚举上的
      `cfg_attr(feature="browser", wasm_bindgen)`。
- [ ] 5.3 验证：1.2 `cargo tree -p netwave` 断言转 green（只剩 num-complex/strum/
      thiserror）；`pnpm check` 全绿。

## 6. spec 与跨端对拍

- [ ] 6.1 `api-contract拆两条`：apply 态 sync 把 delta 合进主 spec——wasm 导出面
      与词汇常量来源拆两条；scenario 标题在主 spec 内直接编辑（delta 不碰改名）。
- [ ] 6.2 cross-binding 对拍：`pnpm test:cross` 全绿（browser 公开 API 逐字节不变，
      三端名字一致）。
- [ ] 6.3 docs 教学式标准：搬迁涉及的 browser crate 模块注释达到教学式标准
      （宪法元规则），只写当前契约事实。

## 7. 收尾闸门（七锚点逐条覆盖）

- [ ] 7.1 `Plan/`：删除 `Plan/绑定放置重构.md` 中本 change 已定案章节（resources
      归属、start 钩子、fetch 注入、99→100、发包除外），删后跑 `pnpm check:md`。
- [ ] 7.2 `三态时效`：扫 `openspec/specs/` 全目录，对照本 change 产出
      api-contract/ci-matrix/workspace-layout 的更新/新增/退役三态结论留痕。
- [ ] 7.3 `旧名清零`：全仓 grep 旧标识符（`gen_constants`、`constants.generated`、
      `core/src/resources.rs`、`cov-drive` feature 名），确认活文件引用已同步现名、
      零残留（排除 target*/dist/node_modules/.venv/archive）。
- [ ] 7.4 `三轴`：按 governance spec「元规则 review 三轴」（Standards/Spec/Lessons）
      对照本 change 工件审实现 diff，diff 文件集逐文件对上 tasks.md，硬伤清零。
- [ ] 7.5 `体检`：对触碰文件全文只读体检（health-check spec apply 态：语义考古维
      + 四维），发现附文件+行号+证据落 Plan/ 等点名，不阻塞。
- [ ] 7.6 `迟到追加`：apply 中途拍板的决定当场追加进 proposal.md `## 已定裁决`
      并补对应任务行，收尾复查每个关键词载体任务已打勾。
- [ ] 7.7 `check:outdated`：跑 `pnpm check:outdated` 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍，含
      全局 CLI/直装工具机器级升级；上游 bug/不兼容登记回退不阻塞）；消化后复跑
      `pnpm check:outdated` 至退出码 0（SUMMARY 归零）才算完成。
