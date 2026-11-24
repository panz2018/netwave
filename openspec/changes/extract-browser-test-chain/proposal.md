# Proposal

## Why

`extract-browser-package` 把浏览器端立成顶层 `browser/` 包后留下三处尾巴：
浏览器测试入口脚本仍住在仓库根 `scripts/run/test_browser.sh`、覆盖率链辅助模块
`coverage-dump.ts` 仍住在 `browser/src/`（被 worker 静态 import，导致
`dumpCoverage`/`driveCoverage`/`installFetchStub` 三个测试专用函数连同 worker 的
三条 control 分支被 tsdown 内联进**发布产物** `browser/dist/netwave.worker.js`，
实证：grep 该产物命中 26 处 cov/Coverage/profraw/signature）。测试代码混进发布物
既污染产物、又让"主线 worker 源码"与"覆盖率链脚手架"难以区分。本变更把测试资产
归位到 browser 包内、并用编译期标志把覆盖率代码从发布产物剔除。

## What Changes

- `coverage-dump.ts` 从 `browser/src/` 移到 `browser/test/`（它是测试辅助，非产品源码）。
- worker 的覆盖率专用代码——三条 `control` 分支（`dumpCoverage`/`driveCoverage`/
  `stubFetch`）、顶层 `globalThis.__netwaveWasmInstance` 赋值、`covDir` 探针与
  instrumented import 分支——全部包进编译期常量 `__NETWAVE_COVERAGE__` 守卫；
  tsdown 发布构建填 `false`（默认 `minify: 'dce-only'` + tree-shaking 把守卫块与
  无副作用的 `coverage-dump.ts` 整模块摇掉），两个 vitest 配置填 `true`（测试链不变）。
- **BREAKING**（内部命名/位置）：浏览器测试入口脚本 `scripts/run/test_browser.sh`
  → `browser/scripts/test.sh`；根 `test:browser` 由 `bash scripts/run/test_browser.sh`
  改为 `pnpm -C browser test`，CI browser job 同步。
- `browser/package.json` 的 `test` 命令改为指向 `bash scripts/test.sh`（完整链：
  build + node unit + rust 覆盖率链 + e2e）。
- `scripts/check_ci.py` 增加"委托形式"识别：根 `test:<seg>` 若值为
  `pnpm -C <pkg> <cmd>`，改校验 ci.yml 含该委托命令（替代原 `bash scripts/run/test_<seg>.sh`
  字符串匹配）。
- `browser/scripts/publish_shell.mjs` 末尾增加发布闸门：grep 发布产物
  `dist/netwave.worker.js`，命中覆盖率符号即非零退出（防回归）。
- **BREAKING**（spec 标签/事实）：ci-matrix spec 把陈旧 `wasm` 标签 browser 化——
  requirement「全项目 wasm 测试根聚合入口」改名「全项目浏览器测试根聚合入口」
  （RENAMED），正文历史指针随之删（scenario 标题受 openspec MODIFIED 约束保留
  原名）；并修正「typescript 测试根聚合
  入口」「根 test 总聚合入口」里引用已不存在命令的死事实（`build:wasm`→
  `pnpm -C browser build:browser`、`test:wasm`→`test:browser`）。真技术名
  （`wasm32-unknown-unknown`/`wasm-pack`/`wasm-bindgen`/`#[wasm_bindgen]`/
  `wasm 线性内存`/`插桩 wasm`）与 lessons-learned 账本一律不动。

## Capabilities

### New Capabilities

<!-- 无新建能力：测试入口归位与发布物纯净性分别归既有 ci-matrix 与
     workspace-layout，不另立能力。 -->

### Modified Capabilities

- `ci-matrix`: 「全项目 wasm 测试根聚合入口」requirement 改名「全项目浏览器测试
  根聚合入口」（RENAMED），脚本承载位置由 `scripts/run/test_browser.sh` 改为
  `browser/scripts/test.sh`，根入口调用形式由直接调脚本改为 `pnpm -C browser test`；
  CI browser job 测试步骤随之改。另修正「typescript 测试根聚合入口」「根 test
  总聚合入口」里引用已不存在命令的死事实（`build:wasm`/`test:wasm`）。
- `workspace-layout`: 「平铺 monorepo 结构」requirement 增补 scenario——`browser/`
  自包含须含其测试入口脚本（`browser/scripts/test.sh`）与覆盖率链辅助
  （`browser/test/coverage-dump.ts`），且**发布产物 `dist/netwave.worker.js` MUST
  NOT 含任何覆盖率/测试专用代码**（编译期标志剔除）。

## Impact

- 代码：`browser/src/coverage-dump.ts`（移动）、`browser/src/netwave.worker.ts`
  （import 路径 + `__NETWAVE_COVERAGE__` 守卫）、新增 `browser/src/global.d.ts`
  （标志类型声明）。
- 配置：`browser/tsdown.config.ts`、`browser/vitest.unit.config.ts`、
  `browser/vitest.e2e.config.ts`（三处 define）、`browser/package.json`、
  根 `package.json`、`.github/workflows/ci.yml`。
- 脚本：`scripts/run/test_browser.sh` → `browser/scripts/test.sh`、
  `browser/scripts/publish_shell.mjs`（发布闸门）、`scripts/check_ci.py`（委托识别）。
- 测试：`scripts/tests/test_test_browser_wiring.py`（脚本路径常量随迁，
  `coverage-wasm.lcov`/地板 99 断言本轮不动）。
- spec：`ci-matrix`、`workspace-layout`（delta）。
- 文档：`Plan/测试规划.md`（描述性标签「CI wasm job」→「CI browser job」）。
- 受影响铁律：铁律八（wasm 只运行在 worker、主线程零 wasm）——本变更不改其语义，
  仅把覆盖率链代码从发布产物剔除；worker 泛化分发固定模板不变式（api-contract）
  不受影响（control 分支本就不是业务动词，且发布产物里整体消失）。

## Non-goals

- 不改真技术名（`wasm32-unknown-unknown`/`wasm-pack`/`wasm-bindgen`/
  `#[wasm_bindgen]`/`wasm 线性内存`/`插桩 wasm`/`wasm 产物`）——它们指真实
  wasm 运行时/工具；lessons-learned 账本为冻结历史，不改。
- 不改覆盖率链**内部产物名**（`coverage-wasm.lcov`、`coverage_gate.py` 文件匹配）
  ——仍留后续独立 change。
- 不动 wasm rust 覆盖率地板（仍 99，非 100）——依赖注入消解 fetch 臂是另一件事。
- 不搬 core 内的浏览器 dispatch（`call_namespace`/`resources.rs`/start 钩子）——
  留 `Plan/绑定放置重构.md` 阶段 A。
- 不改 worker 的 control 协议语义与 e2e/unit 测试逻辑——只改其在发布产物里的存在性。

## Prior art

- 编译期标志 + tree-shaking 剔除测试/开发代码是生态标准机制：Vue `__DEV__`、
  React `__DEV__`、tsdown 自身 `define: { 'import.meta.TSDOWN_PRODUCTION': 'true' }`
  （<https://github.com/rolldown/tsdown/blob/main/tsdown.config.ts>）。
- tsdown 默认 `minify: 'dce-only'` + ESM tree-shaking（无副作用模块整模块摇掉），
  Rolldown dead-code-elimination：<https://rolldown.rs/in-depth/dead-code-elimination>。
- 仓库内既有"发布物自包含"先例：`browser/scripts/publish_shell.mjs` 已在做产物
  后处理（改写 import 路径），发布闸门加在其末尾属同一归属。

## 专家增补

- 发布闸门应可门禁化：`browser/scripts/publish_shell.mjs` 末尾 grep
  `dist/netwave.worker.js` 命中 `dumpCoverage|__cov|NETWAVE_WASM_DIR` 即非零退出，
  把"发布物纯净"从一次性人工检查升级为构建期强制（防后续有人再写漏 control 分支）。
- `__NETWAVE_COVERAGE__` 须有类型声明（`browser/src/global.d.ts`），否则
  `pnpm -C browser typecheck`（tsc --noEmit）报未定义标识符。
- 守卫须覆盖顶层 `globalThis.__netwaveWasmInstance = ...` 赋值——DCE 只删死分支，
  不删顶层副作用；漏包则该赋值连同 `wasmInstanceSlot` 仍残留在发布产物。

## 已定裁决

- `coverage-dump归test`：`coverage-dump.ts` 从 `browser/src/` 移到 `browser/test/`，
  worker import 路径改 `../test/coverage-dump.ts`。
- `编译期标志剔除`：worker 覆盖率专用代码包进 `__NETWAVE_COVERAGE__` 守卫，tsdown
  发布构建填 `false`、两个 vitest 配置填 `true`，靠 dce-only + tree-shaking 从发布
  产物剔除。
- `标志名`：用裸 define `__NETWAVE_COVERAGE__`（仿 `__DEV__`），非 `import.meta.env`。
- `标志三处填值`：`browser/tsdown.config.ts`=false、`browser/vitest.unit.config.ts`=true、
  `browser/vitest.e2e.config.ts`=true。
- `标志类型声明`：新增 `browser/src/global.d.ts` 声明 `__NETWAVE_COVERAGE__: boolean`。
- `发布闸门位置`：产物纯净检查加在 `browser/scripts/publish_shell.mjs` 末尾。
- `脚本迁入改名`：`scripts/run/test_browser.sh` → `browser/scripts/test.sh`（内部
  `cd ../..` 不变）。
- `browser命令叫test`：`browser/package.json` 的 `test` 指向 `bash scripts/test.sh`。
- `根命令走pnpm`：根 `test:browser` = `pnpm -C browser test`，CI browser job 同步。
- `check_ci委托识别`：`scripts/check_ci.py` 识别 `pnpm -C <pkg> <cmd>` 委托形式。
- `wiring测试随迁`：`scripts/tests/test_test_browser_wiring.py` 脚本路径常量改
  `browser/scripts/test.sh`，覆盖率产物名/地板断言本轮不动。
- `spec标签browser化`：ci-matrix spec 陈旧 wasm 标签 browser 化——requirement
  「全项目 wasm 测试根聚合入口」RENAMED 为「全项目浏览器测试根聚合入口」、正文
  历史指针删；scenario 标题受 openspec MODIFIED 约束（改名=删旧加新，archive 拒）
  保留原名；「typescript 测试根聚合入口」「根 test 总聚合入口」里引用已不存在命令
  的死事实 `build:wasm`→`pnpm -C browser build:browser`、`test:wasm`→`test:browser`；
  `Plan/测试规划.md`「CI wasm job」→「CI browser job」。真技术名与 lessons-learned
  账本不动。
- `跳过archive态体检`：本 change 归档完成后的 archive 态全项目只读体检跳过
  （health-check spec「archive 态」），apply 态被触碰文件体检照常执行。
