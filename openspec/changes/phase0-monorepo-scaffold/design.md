# Design

## 总体思路

阶段 0 的唯一技术风险点是**三绑定零拷贝机制能否走通**，其余是机械脚手架。
设计围绕一个最小载体：core 的 `fill_pattern(nfreq, nports) ->
Vec<Complex64>`（实为返回自有缓冲的所有权包装），三绑定各自把这块内存以
视图形式交给宿主语言，测试改写视图后经 core 回读。

## core 临时 API

```text
core/src/lib.rs
  pub fn fill_pattern(nfreq: usize, nports: usize) -> Vec<Complex<f64>>
  // allocates nfreq*p*p interleaved-complex f64, fills a deterministic
  // pattern: re = f*100 + p*10 + q, im = -(same) so every element is
  // distinct and sign-checkable.
```

- 返回 `Vec<Complex<f64>>`（`num-complex`，内存布局即交错 f64，与铁律一逐字节
  一致——`Complex<f64>` 是 `#[repr(C)]`，re 在前 im 在后）。
- 图案可预测：测试不依赖 core 输出算期望（避免 tautology），期望值由测试内
  闭式公式 `f*100 + p*10 + q` 独立计算（闭式解，铁律二合规）。
- 零拷贝验证不靠这个返回值直接传（Vec 跨 FFI 需转移所有权），绑定层各自见下。

## Python 绑定（PyO3 + rust-numpy）

- `python/src/lib.rs`：`fill_pattern_py` 在 Rust 侧分配 `Vec<Complex64>`，
  用 `PyArray::from_vec`（所有权转移进 ndarray）返回；"写回 core 可见"的
  验证方式：同一 ndarray 二次传回 Rust 函数 `sum_first_element(arr:
  &Readonly<PyArray<Complex64,_>>)` 读回——内存从未拷贝，视图即数据。
  - 说明：PyO3 侧让 Python 长期持有、Rust 同时保留的"双活视图"需要
    `PyArray::from_borrowed_data` + cleanup 回调，属阶段 6 深水区；阶段 0
    用所有权转移（from_vec）即可证明零拷贝语义（owndata=False 的
    from_raw 变体可后置）。**假设记录**：阶段 0 的"写回 core 可见"以
    "Python 改写 → 传回 Rust 读回一致"为验收形态。
- `pyproject.toml`：name=`netwave`，requires-python=">=3.10"（底线；开发/CI
  钉 3.14，`.python-version` 进 git，abi3 一个 wheel 覆盖 3.10–3.14），
  dev-dependencies 含 maturin、pytest、pytest-cov；`uv` 管理，`uv.lock` 进 git。
- 构建：`uv run maturin develop`（本地）/ `maturin build`（CI）。

## TypeScript 单包 `netwave`（目录 `typescript/`）

**单包单目录，exports 条件分发**（2026-09-21 定案，取代此前"伞形包 +
`@netwave/node` + `@netwave/wasm` 三包方案）：

```text
typescript/
├── package.json          # name=netwave（唯一 npm 包）；files=["dist"]
├── native/src/lib.rs     # napi Rust crate（publish=false crate）
├── wasm/src/lib.rs       # wasm-bindgen Rust crate（publish=false crate）
├── src/
│   ├── index.node.mjs    # node 条件壳（re-export napi 产物）
│   ├── index.browser.mjs # browser 条件壳（re-export wasm-bindgen 产物）
│   ├── standalone.js     # 纯 HTML 零构建单文件 ESM 入口（fetch wasm）
│   ├── netwave.worker.js # 预置 Worker 胶水（零数值逻辑）
│   └── index.d.ts        # 类型声明（node/wasm 语义一致）
├── dist/                 # 全部构建产物（.gitignore；napi/wasm-pack 输出 +
│   └── …                 #   壳文件拷贝），exports 只指向这里，发布白名单
└── test/                 # vitest workspace：native 项目 + wasm 项目
```

- `exports` 条件分发：

  ```text
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "node": "./dist/index.node.mjs",
      "browser": "./dist/index.browser.mjs",
      "default": "./dist/index.browser.mjs"
    },
    "./standalone": "./dist/standalone.js",
    "./worker": "./dist/netwave.worker.js"
  }
  ```

- **消费者只见包名**：用户唯一写法是 `import "netwave"`（子路径
  `netwave/standalone`、`netwave/worker`）；`index.*.mjs` 文件名是 exports
  内部映射，消费者不可见。入口文件保留 `index.` 前缀（生态惯例），
  不改名 `netwave.`——包名已在包本身，文件名再带即冗余（同目录短名纪律）。

- **体积账**：打包器按 exports 条件只拉命中分支（网页端只进 wasm，Node 端
  只进 `.node`），消费者发布产物体积无感；install 磁盘占用由 napi 按平台
  `optionalDependencies`（`os`/`cpu` 标签）砍到本平台一块。三包方案对此
  并无优势（伞形包 dependencies 同样两个都装），只多出一套同版本同步机器。
- **不发 UMD**：`<script type="module">` 即 2026 标准答案；纯 HTML 用户走
  `./standalone`（自托管）或 CDN `https://esm.sh/netwave`，零 Node.js。
- **单一 async 面**（2026-09-22 修订）：JS 计算动词不加后缀直接返回 `Promise`，
  用户唯一写法 `await toY(x)`；同步直通版降级为 `_` 前缀逃生口（`@internal`，
  铁律七覆盖率照常计入）；属性读取保持同步。Worker 分流库内自动（小数据立即
  resolve，大数据进 Worker 池/napi AsyncTask，阈值阶段 3/6 按 benchmark 定）。
- **Worker**：`netwave.worker.js` 是**单一命令分发器**——显式静态表
  `cmds = { toY, toZ, ... }`（构建脚本生成，加函数只改表不加文件，零数值逻辑），
  由库的 async 壳内部 `new Worker(new URL("netwave.worker.js", import.meta.url))`
  托管，普通用户不直接接触；高级用户可经 `netwave/worker` 子路径自建。
  边界契约（普通调用输入克隆进入、`upload` 才 transfer、结果一律 transfer、
  SAB 可选升级）见
  [zero-copy-roundtrip spec](specs/zero-copy-roundtrip/spec.md#requirement-异步与-worker-边界契约阶段-0-定契约实现在阶段-36)。
  Node `worker_threads` 加载 `.node` addon 无障碍。
- **tree-shaking**：包入口禁 `export *`（打包器保守处理会整模块保留），显式
  具名导出（构建脚本从 `.d.ts` 生成防漏）；Worker 分发禁动态属性访问命名空间。
  wasm 二进制不受 JS 摇树，体积靠 Rust 侧 `lto = true` + wasm-opt 控制。
- 阶段 0 冒烟：vitest 断言 exports 字段结构 + node 环境解析到 napi 壳；
  浏览器/Worker 实测属阶段 6。构建：`napi build` 与 `wasm-pack build` 输出
  统一落 `dist/`，壳/胶水文件由构建脚本从 `src/` 拷入 `dist/`。

## Node 绑定（napi-rs，`typescript/native/`）

- `typescript/native/src/lib.rs`：`fill_pattern` 返回 `ArrayBuffer`（napi 的
  `ArrayBuffer::with_data`/External 后端，Rust Vec 转移进 V8 外部内存），
  JS 拿 `new Float64Array(buf)` 视图；`read_element(buf, idx)` 把 buffer
  传回 Rust 读元素——同一 External 内存，零拷贝。
- `napi build` 产出 `.node`，由 `typescript/package.json` 的 node 条件壳引用；
  devDependencies（`@napi-rs/cli`、`vitest`、`@vitest/coverage-v8`）统一在
  `typescript/package.json` 声明。
- 版本底线 engines: node >=22（最旧在支持期 LTS，Node 20 已 2026-04 EOL）；
  开发用当前 latest stable 26（nvm v26.4.0）。

## wasm 绑定（wasm-bindgen，`typescript/wasm/`）

- `typescript/wasm/src/lib.rs`：`fill_pattern(nfreq, nports)` 写入
  lazily-initialized 静态线性内存，返回 offset/length；JS 侧
  `new Float64Array(memory.buffer, offset, len)` 取视图；`read_element(idx)`
  从线性内存读回。
  - wasm 内存增长（memory.grow）会 detach 旧视图——阶段 0 缓冲固定小尺寸，
    不触发增长；失效强制机制属阶段 6。
- `wasm-pack build --target bundler`（browser 条件产物）+
  `--target nodejs`（vitest 跑往返用）；阶段 0 不做浏览器实测。
- 多线程 wasm（阶段 3）：core rayon 代码不变，加 wthreads 适配 +
  `+atomics,+bulk-memory,+mutable-globals` 编译 flag；JS Worker 池胶水由
  wasm-bindgen/wthreads 自动生成；无 COOP/COEP 自动单线程回退。

## 测试与对拍

- core：unit（图案闭式期望、长度/布局断言）+ criterion 空基准（一个
  `fill_pattern` 小尺寸基准占位）。
- python：pytest（往返 + owndata=False 断言 + `--cov-fail-under=100`）。
- node/wasm：vitest（往返 + byteOffset/buffer 同一性断言 + coverage lines 100）。
- cross-binding：同一 `(nfreq=2, nports=2)` 与同一写入值，四端各跑一遍，
  原生三端逐 bit 比对（CI 同机 job 内比对 JSON 输出），wasm 相对容差
  （`testdata/manifest.json` 登记 `core_tol` 占位，阶段 1 正式化）。

## CI 结构

```text
.github/workflows/ci.yml
  matrix: [linux-x64, linux-arm64, windows-x64, darwin-arm64, wasm32]
  steps: fmt → clippy → cargo test → (wasm格: wasm-pack + vitest)
         → coverage（llvm-cov / v8）→ criterion
  python job: ubuntu 单格，uv sync + maturin develop + pytest --cov
```

- 五格全铺（用户已拍板）。windows 格 napi 构建走 MSVC runner 自带工具链，
  不需要 zig；zigbuild 仅发版交叉编译 Linux glibc 老版本时用（已装备用）。
- rust-toolchain.toml 钉 stable（当前 1.98.1）；edition 2024（自 Rust 1.85 起
  稳定，greenfield 无兼容包袱直接用最新）；MSRV 底线即当前 stable 1.98，
  升版走 OpenSpec 变更；MSRV 检查 job 留到阶段 2 有真实代码后加。
- 覆盖率：`cargo llvm-cov --workspace --fail-under-lines 100`；
  hello 代码全被测试执行即天然 100%。

## 风险与回退

- rust-numpy abi3 与 NumPy 2.x：rust-numpy ≥0.24 支持 NumPy 2，uv.lock 钉版。
- aarch64 本机跑不了 x64 CI 格：本地只验 linux-arm64 + wasm32，其余靠 CI。
- napi External 内存生命周期：转移所有权给 V8，Rust 不再持有——往返读回
  必须经 JS 传回 buffer，设计已如此。
