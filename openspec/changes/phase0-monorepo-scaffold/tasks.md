# Tasks

> 顺序即执行顺序：每个数值/绑定任务前必有 red 测试。标记 [RED] 的任务必须先跑
> 看到失败，再进入对应 [GREEN] 任务。

## 1. 仓库骨架

- [x] 1.1 建目录：`core/src`、`python/src`、`typescript/native/src`、
      `typescript/wasm/src`、`typescript/test`、`testdata/`
- [x] 1.2 根 `Cargo.toml`：
      `[workspace] members = ["core","python","typescript/native","typescript/wasm"]`，
      resolver="2"；`rust-toolchain.toml` 钉 stable（当前 1.98.1，升版走 OpenSpec 变更）
- [x] 1.3 `core/Cargo.toml`：name=netwave、edition=2024、rust-version=1.98、
      publish=false；deps：num-complex；dev-deps：criterion
- [x] 1.4 根 `package.json`（private，packageManager="pnpm@12.5.1"）+
      `pnpm-workspace.yaml`（typescript）；`.gitignore`（target/、
      node_modules/、dist/、.venv/、**pycache**/）
- [x] 1.5 `typescript/package.json`（npm 名 netwave，单包：exports 全部指向
      `dist/`——node→napi 壳、browser/default→wasm 壳、./standalone 纯 HTML
      单文件、./worker 预置 Worker 胶水；`files=["dist"]`；engines node>=22；
      原生二进制按平台 optionalDependencies；不发 UMD；devDeps：@napi-rs/cli、
      vitest、@vitest/coverage-v8）+ `src/index.d.ts` 等入口壳（计算动词返回
      `Promise`，同步逃生口 `_` 前缀标 `@internal`，属性读取同步）；
      测试断言 exports 结构与条件解析（node 环境解析到 napi 壳）+
      断言入口无 `export *`（显式具名导出，保 tree-shaking）
- [x] 1.6 `python/pyproject.toml`（name=netwave，requires-python>=3.10，
      devDeps：maturin、pytest、pytest-cov）；`.python-version` 钉 3.14（开发版）；
      `uv sync` 生成 `uv.lock`
- [x] 1.7 `testdata/manifest.json` 骨架（含 `core_tol` 占位键）+
      `testdata/LICENSE-NOTES.md` 占位
- [x] 验证：`cargo metadata --no-deps` 列出四成员；`pnpm install` 成功；
      `uv run python -c "import sys; print(sys.version)"` ≥3.10（实测 3.14.7）

## 2. core：fill_pattern（脚手架数值 API，red 先于 green）

- [x] 2.1 [RED] `core/tests/fill_pattern.rs`：闭式期望
      `re=f*100+p*10+q, im=-re`；断言长度 128B（nfreq=2,nports=2）、每频点 64B 连续、re 前 im 后；
      运行 `cargo test -p netwave` 看到编译失败/断言红
- [x] 2.2 [GREEN] `core/src/lib.rs` 实现 `fill_pattern`（num-complex，
      教学式 rustdoc：交错布局、图案公式、"临时 API 阶段 2 替换"声明）→ 测试绿
- [x] 2.3 criterion 基准占位 `core/benches/scaffold.rs`（fill_pattern 小尺寸）
      → `cargo bench` 通过
- [x] 验证：`cargo llvm-cov -p netwave --fail-under-lines 100` 通过；
      docs 达教学式标准（rustdoc 自包含解释为何如此编写）

## 3. Python 绑定（red 先于 green）

- [x] 3.1 [RED] `python/tests/test_roundtrip.py`：取 ndarray → 断言
      owndata=False、dtype=complex128、shape=(2,2,2)、图案闭式期望 → 写
      `arr[0,0,1]=1+2j` → 传回 `read_element` 读回一致；`uv run pytest` 看到红
- [x] 3.2 [GREEN] `python/src/lib.rs`：PyO3 `fill_pattern_py`
      （PyArray::from_vec，所有权转移）+ `read_element`（Readonly 借用读回）；
      全量 type hints 写进 `.pyi` stub → pytest 绿
- [x] 验证：`uv run maturin develop` 成功；
      `uv run pytest --cov=netwave --cov-fail-under=100` 通过

## 4. Node 绑定（red 先于 green）

- [x] 4.1 [RED] `typescript/test/native.roundtrip.test.ts`：`await fillPattern()`
      公开 async 面（小数据立即 resolve）+ `_fillPattern()` 同步逃生口绑定往返 →
      Float64Array 视图 → 图案期望 → 写 `view[2]=3.5` → `await readElement` 读回
      一致 → 断言 `await fillPattern()` 与 `_fillPattern()` 数值一致 → vitest 看到红
- [x] 4.2 [GREEN] `typescript/native/src/lib.rs`：napi `fill_pattern`
      （ArrayBuffer/External 转移）+ `readElement`；`napi build`（于
      `typescript/`）→ vitest 绿
- [x] 验证：`pnpm -C typescript test --coverage`（thresholds lines 100）通过

## 5. wasm 绑定（red 先于 green）

- [x] 5.1 [RED] `typescript/test/wasm.roundtrip.test.ts`：`await fillPattern()`
      公开 async 面 + `_fillPattern()` 同步逃生口 →
      `new Float64Array(memory.buffer, offset, len)` 视图 → 图案期望 → 写元素 →
      `await readElement` 读回一致 → 断言两路数值一致；vitest 看到红
- [x] 5.2 [GREEN] `typescript/wasm/src/lib.rs`：wasm-bindgen `fill_pattern`
      （线性内存 + offset/length）+ `readElement`；
      `wasm-pack build --target nodejs` → vitest 绿
- [x] 验证：wasm 覆盖率 lines 100 通过

## 6. cross-binding 对拍

- [x] 6.1 四端各输出 `(nfreq=2,nports=2)` 往返结果为 JSON/二进制到约定路径，
      CI 单 job 内比对：原生三端逐 bit 一致、wasm 相对容差（manifest `core_tol`）
- [x] 6.2 假 golden 自检：故意篡改一端输出，对拍脚本必须失败（防 tautology）

## 7. CI

- [x] 7.1 `.github/workflows/ci.yml`：五格矩阵（linux-x64/arm64、windows-x64、
      darwin-arm64、wasm32）+ fmt/clippy(-D warnings)/cargo test/criterion/
      llvm-cov(--fail-under-lines 100)
- [x] 7.2 python job（ubuntu 双版本格 3.10/3.14）：uv sync → maturin develop →
      pytest --cov-fail-under=100；确认 ci.yml 零 skrf
- [x] 7.3 node/wasm job（node 双版本格 22/26）：pnpm install → napi build /
      wasm-pack build（均在 `typescript/`）→ vitest coverage lines 100 →
      cross-binding 对拍步骤
- [ ] 验证：推 PR 五格全绿；故意加一行未测代码确认覆盖率 job 红

## 8. 收尾

- [x] 8.1 `markdownlint-cli2` + `python3 scripts/check_links.py` 通过
- [x] 8.2 code-review 双轴（Standards：铁律一/四/六/七；Spec：三份 delta spec）
- [ ] 8.3 `/opsx:sync` → `/opsx:archive`，复盘三问回写文档
