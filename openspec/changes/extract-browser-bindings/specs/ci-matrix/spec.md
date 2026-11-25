## MODIFIED Requirements

### Requirement: 覆盖率门槛生效（铁律七）

CI MUST 启用覆盖率采集并使 100% 行覆盖门槛生效，且 MUST 按 crate/包归属
独立度量、独立地板：core 用
`cargo llvm-cov -p netwave --codecov --output-path coverage/coverage-core.json`

- `scripts/coverage_gate.py coverage/coverage-core.json 100`
  （单 crate + codecov 行合并：同一行任一二进制执行过即计覆盖，绕开默认
  report 按实例计缺的重复计数，LL-057），Python 用
  `pytest-cov --cov-fail-under=100`（python 侧仅胶水时豁免项逐条标注），
  Node/wasm 用 vitest coverage `lines: 100` 阈值写进配置。结构性不可达代码
  MUST 逐条标注豁免（stable 通道 `#[cfg(not(coverage))]` / `# pragma: no cover` /
  `/* v8 ignore start/stop */`，vitest v8 provider；`#[coverage(off)]`
  nightly-only 禁用，LL-020）并附理由。impl 块宏属性行（`#[pymethods]` /
  `#[napi ...]`）MUST 由阅卷脚本按模式豁免（该行缺命中、源码行匹配该宏属性、
  下方首个代码行以 `impl` 开头）——llvm-cov 把宏属性行计作一个 region，宏
  展开 wrapper 的实例计数不并回该行（rustc#79651），该行结构性不可命中，且
  llvm-cov 不认 lcov-perl 的 `LCOV_EXCL_*` 行级标记、无稳定行级排除参数；
  源码读不到的缺行 MUST NOT 豁免（照常报红）；豁免 MUST NOT 硬编码行号。

绑定 crate（python、typescript/native）的 rust 胶水行 MUST 在各自语言 job
内以 `cargo llvm-cov show-env --sh --no-cfg-coverage` + 构建 + 外部测试驱动
（pytest / vitest）+ `cargo llvm-cov report --codecov` 采集
（show-env、clean、构建、外部测试、report MUST 同一 step——环境变量不跨 step；
`--no-cfg-coverage` 防 show-env 默认 `cfg(coverage)` 剥掉源码胶水；
typescript/native 的 report MUST 带 `--target <triple>`——napi `--platform` 把对象
建进 `target/<triple>/debug/`，不带则 report 只搜 host `target/debug` 报 not found；
python 的 maturin 不带 `--target`，对象落 host `target/debug`，report 无需 `--target`），
报告以 `--ignore-filename-regex` 剔除 core 路径后独立阅卷——core 行归
core 报告、胶水行归胶水报告，互不重复计分；绑定 crate 由 show-env/report
外部驱动采集度量。browser crate（netwave-browser）的 rust 行覆盖率 MUST 以 minicov runtime +
`RUSTC_BOOTSTRAP=1` 解锁 `-Zno-profiler-runtime` 在钉死 stable 上编插桩 wasm，
由真浏览器 job（chromium Worker）采集——browser crate 的 fetch 后端把 global
scope 做成参数注入，生产传真实 global、测试传无 fetch 能力的假 scope，故
「无 fetch 能力 scope」臂 MUST 由单元测试驱动命中（不再真不可达）：minicov 的
wasm32 C runtime MUST 由能编 wasm32 的 clang（wasi-sdk 自带，`CC` 指向
`browser/scripts/install_wasi_sdk.sh` 装到 `~/.local` 的 clang）编译（gcc 无 wasm32
后端），插桩构建走独立 target dir（不覆盖生产 `build` 产物），dump 导出
MUST 以 `#[cfg(feature = "coverage")]` 门控（生产产物零污染），profraw MUST
由浏览器测试末尾经 worker 控制消息调 dump 倒出、以 base64 经 vitest browser
command 回传 node 落盘（Uint8Array 直传经序列化降级成 Object，故须 base64），
profraw 文件名 MUST 带 minicov module_signature 防多 worker 覆盖，合并 profraw
MUST 用 `llvm-profdata merge` 加 `-sparse`，合并后以 `llc` 把 `.ll`（由
`--emit=llvm-ir` 产出）编成宿主对象文件，再调 `llvm-cov export --format=lcov`
（llvm-cov 读不了 wasm 符号，故须先 `llc` 编宿主 `.o`；llvm-cov 无 `--codecov`
flag，那是 cargo-llvm-cov 的，散装 `.o` 无独立 codecov 入口）。报告 MUST 度量
browser crate 的绑定代码（句柄表、dispatch、fetch），以 `--ignore-filename-regex`
剔除 `.cargo/registry` 第三方后独立阅卷，落 `coverage/coverage-browser.lcov` 并以
`scripts/coverage_gate.py ... 100` 阅卷（该脚本 MUST 支持 lcov tracefile 输入，
把每条 `DA:<行>,<命中>` 视作 OR 合并后的行级命中；浏览器端 rust 地板为 100，
与其他链同地板——fetch「无 fetch-capable scope」臂经 global 参数注入消解后
可被单元测试命中，不再是地板降到 99 的理由）。
浏览器端 rust 覆盖率链前后 MUST 各执行 `clean_stray_profraw.py`。浏览器端 rust
覆盖率 MUST 仅在真浏览器 job 单采（node matrix 格的浏览器套件维持 TS-only v8，不产
浏览器 lcov）。浏览器端 TS 层 vitest 100% 门槛不变。

#### Scenario: 空 crate 即 100%

- **WHEN** 各 crate/包只有最小 hello/往返代码且全部被测试执行
- **THEN** 覆盖率 job 通过（lines = 100%）

#### Scenario: 未测代码即红

- **WHEN** 新增一行未被任何测试执行的产码
- **THEN** 覆盖率 job 失败（exit ≠ 0），PR 不可合并

#### Scenario: 胶水行未测即红

- **WHEN** `python/src/` 或 `typescript/native/src/` 新增一行未被
  pytest / vitest 任何用例执行的 rust 胶水产码
- **THEN** 对应 job 的胶水阅卷（`coverage_gate.py` 对
  `coverage/coverage-python.json` / `coverage/coverage-native.json`）
  失败（exit ≠ 0），PR 不可合并

#### Scenario: 宏属性行按模式豁免不误红

- **WHEN** 胶水报告缺行是 `impl` 块上的 `#[pymethods]` / `#[napi ...]`
  宏属性行（宏展开 wrapper 实例计数不并回该行，rustc#79651）
- **THEN** 阅卷脚本按三重条件豁免该行并打印理由，阅卷不因此判红；
  缺行源码读不到时不豁免、照常报红

#### Scenario: wasm browser-gated 代码未测即红

- **WHEN** `browser/src/` 的句柄表/dispatch/fetch 代码新增一行未被真浏览器
  wasm 套件或单元测试任何用例执行
- **THEN** `coverage_gate.py` 对 `coverage/coverage-browser.lcov` 阅卷失败
  （exit ≠ 0），PR 不可合并

#### Scenario: wasm 覆盖率报告须含 core browser 路径且命中大于零

- **WHEN** 生成 `coverage/coverage-browser.lcov`
- **THEN** 报告 MUST 含 `browser/src/` 路径行且命中数 > 0（仅命令 exit 0
  不算通，LL-093）；缺目标路径行或全零命中即判链未生效、阅卷失败

#### Scenario: wasm 豁免须先经人工确认清单

- **WHEN** `coverage/coverage-browser.lcov` 出现未达 100% 地板的行
- **THEN** MUST NOT 直接豁免；先列「真不可达」候选清单（逐条附文件+行号+
  不可达理由）交人工确认，确认后方可按 stable 通道标注豁免；未确认者 MUST
  补单元测试至达标（fetch「无 fetch-capable scope」臂经 global 参数注入后
  MUST 由单元测试命中，不再计入地板容差）

#### Scenario: 生产 wasm 产物不含覆盖率导出

- **WHEN** 运行 `pnpm -C browser build`（不带 coverage feature）
- **THEN** 产出的 wasm 不含 `__cov_dump`/`__cov_ptr`/`__cov_len` 导出
  （feature 门控），发布产物零污染
