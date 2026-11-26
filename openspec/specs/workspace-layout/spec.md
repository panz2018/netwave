# workspace-layout Specification

## Purpose

定义 netwave monorepo 的目录结构、workspace 组织与发布名解耦契约，保证 core 与
三绑定同仓同步发版（ABI 严格同步）且各注册表命名稳定。

## Requirements

### Requirement: 平铺 monorepo 结构

仓库根 MUST 包含 `core/`、`python/`、`browser/`、`typescript/`、`oracle/` 子项目
目录与根 `[workspace]` `Cargo.toml`（members = core、python、browser、
typescript/native），以及 `pnpm-workspace.yaml`（packages = browser、typescript）。
`oracle/` 为数值真值参照与阅卷子项目（契约、样本、阅卷脚本；不发布、不参与
Cargo/pnpm workspace）。`browser/` 为浏览器端自包含子项目：内含 wasm-bindgen
Rust glue crate、resident worker、主线程传输壳、浏览器端测试、浏览器端测试入口
脚本（`browser/scripts/test.sh`）与覆盖率链辅助模块（`browser/test/coverage-dump.ts`），
依赖方向单向指向 core。`browser/` 的发布产物 `dist/netwave.worker.js` MUST NOT
含任何覆盖率链/测试专用代码（worker 的覆盖率 control 分支与 `coverage-dump.ts`
经编译期常量在发布构建中整体剔除）。TypeScript 侧承载 node（`typescript/native/` napi Rust crate）与
node+browser 薄封装发布壳，经 pnpm workspace 依赖消费 `browser/`，不再持有
wasm-bindgen crate。exports 条件分发，单包发布名 `netwave`。目录一律短名，
发布名在各清单文件独立声明。数值真值内容（manifest、样本、LICENSE-NOTES）居
`oracle/`，仓库根无 `testdata/` 目录。

#### Scenario: workspace 清单一致

- **WHEN** 在仓库根运行 `cargo metadata --no-deps`
- **THEN** 输出的 workspace members 恰为 core、python、browser、
  typescript/native 四个包
- **AND** `pnpm-workspace.yaml` 列出 browser 与 typescript
- **AND** 仓库根存在 `oracle/` 目录且不存在 `testdata/` 目录

#### Scenario: 发布名与目录名解耦

- **WHEN** 读取各清单文件
- **THEN** `python/pyproject.toml` 的 `[project] name` 为 `netwave`；
  `typescript/package.json` 的 `name` 为 `netwave`；`core/Cargo.toml` 的
  package name 为 `netwave`（`publish = false` 占位）；`browser/` 的 Rust crate
  name 为 `netwave-browser`、pnpm 包 `private: true`

#### Scenario: 单包按环境自动分发

- **WHEN** 读取 `typescript/package.json`（npm 发布名 `netwave`）
- **THEN** 其 `exports` 条件映射：`"node"` 条件指向 napi 产物（`.node` +
  ESM/CJS 双壳），`"browser"`/`"default"` 条件指向构建期从 `browser/` 包合并
  进 typescript 产物的浏览器 ESM（发布物自包含，运行时不依赖未发布的 browser）；
  另含纯 HTML 零构建单文件入口（`./standalone` 子路径）与预置 `./worker`
  （浏览器 Worker 胶水，零数值逻辑）
- **AND** 原生二进制按平台拆 `optionalDependencies`（`os`/`cpu` 标签），
  install 只拉本平台块
- **AND** 不发 UMD 格式（`<script type="module">` 即标准答案，UMD 是历史包袱）
- **AND** 单包不含任何数值代码，数值全在 core

#### Scenario: browser 子项目自我完整

- **WHEN** 检查 `browser/` 目录内容
- **THEN** worker、主线程传输壳、worker 协议类型、浏览器端测试、浏览器端测试
  入口脚本（`browser/scripts/test.sh`）与覆盖率链辅助模块
  （`browser/test/coverage-dump.ts`）均在 `browser/` 内，wasm 构建产物落
  `browser/dist/`
- **AND** `typescript/` 不再持有 worker、传输壳或 wasm-bindgen crate
- **AND** `browser/` 仅依赖 core，不被 core 反向依赖

#### Scenario: browser 发布产物不含测试代码

- **WHEN** 构建 `browser/` 后检查发布产物 `browser/dist/netwave.worker.js`
- **THEN** 该产物不含覆盖率链/测试专用符号（grep `dumpCoverage`、`__cov`、
  `NETWAVE_WASM_DIR` 均零命中）——worker 的三条覆盖率 control 分支、
  `globalThis.__netwaveWasmInstance` 赋值与 `coverage-dump.ts` 整模块经编译期
  常量在发布构建中被剔除
- **AND** 测试运行路径（vitest）仍保留这些代码，覆盖率链照常工作

#### Scenario: 构建顺序 browser 先于 typescript

- **WHEN** 检查 typescript 的 node 构建链（`scripts/run/test_ts.sh`）
- **THEN** `pnpm -C browser build` 先于 `build:native`（tsdown dts pass
  需 browser wasm glue 与 napi glue 双产物齐备，缺 browser glue 会使壳 dts
  对再导出动词退化为 `any`）
- **AND** CI 的 browser job 与 typescript job 并行独立、无 `needs` 跨 job 依赖

#### Scenario: 命名空间预留名不占用

- **WHEN** 未来新增网页端插件（如 Touchstone 格式转换器 / 显示器）
- **THEN** 其 npm 发布名 MUST 使用 `@netwave/<功能名>` 形式
  （预留：`@netwave/converter`、`@netwave/touchstone`），
  与本变更已定名字不冲突

### Requirement: 主 CI 零 Python 依赖

各端主构建/测试路径（cargo test、pytest 读 oracle 样本、vitest、wasm 构建）
MUST NOT 依赖 Python 运行时生成数据；oracle 的生成/阅卷步骤不在此条款范围
（skrf 圈禁于 oracle 环境，见 governance 铁律四）。`oracle/` 承载容差
manifest 与 Touchstone 输入样本（本阶段 manifest 为骨架、样本为脚手架三件）。

#### Scenario: 构建不触发 Python

- **WHEN** 在无 skrf 安装的环境执行 `cargo test --workspace` 与
  `pnpm -r build`
- **THEN** 全部命令成功退出（exit 0），无 skrf 导入错误

### Requirement: 根级 Python 工具环境

仓库根 MUST 存在 uv 工具工程 `pyproject.toml`（private，不发布）及其
`uv.lock`、`.python-version`，作为全部仓库治理脚本（`scripts/` 闸门与
治理脚本单测）的统一 Python 环境：工具依赖（pytest、pytest-cov、ruff）
MUST 在该工程 dev 组声明并锁死，MUST NOT 依赖开发者全局 Python 所装
内容。根工程 MUST NOT 声明 uv workspace 成员；`python/` 维持独立 uv 工程
（发布物依赖故事独立，uv 按就近目录解析互不干扰）。根 `.python-version`
与主工程 `python/.python-version` 同值，由规则驱动闸门自动纳入覆盖，
无需登记。治理脚本单测 MUST 置于 `scripts/tests/`，其运行配置（含使
`scripts/versions/lib` 可导入的 pytest pythonpath）MUST 落在根工程
`pyproject.toml`；单测 MUST NOT 联网，联网输出的一致性验证由一次性
临时基线承担，基线文件 MUST NOT 入库。

#### Scenario: 门禁脚本经根环境运行

- **WHEN** 在仓库根运行 `uv run python scripts/versions/check_versions.py`
- **THEN** 命令经根 `uv.lock` 锁定的环境执行成功，不要求任何全局安装的
  第三方包

#### Scenario: 发布工程环境独立

- **WHEN** 在 `python/` 目录运行 `uv sync`
- **THEN** 解析到 `python/pyproject.toml` 自身工程（numpy/maturin/pytest
  等发布侧依赖），与根工具工程互不影响

#### Scenario: 根 Python 钉版由四律自动覆盖

- **WHEN** 规则驱动闸门扫描仓库 manifest
- **THEN** 根 `.python-version` 受矩阵覆盖律约束（值 MUST 出现在 CI python
  矩阵格中）、根 `pyproject.toml` 的 `[project]` 受 Python 工程律约束
  （`requires-python` + 同目录 `.python-version`），漏声明当场 FAIL——
  登记表退役后无任何登记环节

#### Scenario: 治理脚本单测离线可跑

- **WHEN** 在无网络环境执行 `uv run pytest scripts/tests`
- **THEN** 全部用例成功（纯逻辑夹具，无网络请求、无子进程依赖外部网络）

#### Scenario: 单测挂进 Python 闸门

- **WHEN** 运行 `pnpm check:py`
- **THEN** ruff lint/format 检查之后自动运行 `uv run pytest scripts/tests`，
  任一用例失败即该命令 FAIL

### Requirement: 治理脚本分层

`scripts/versions/` MUST 按三层组织：门面（`check_versions.py`、
`check_outdated.py`）、共享库（`lib/` 包）、单测（`scripts/tests/`）。
门面 MUST 只做输入组装、检查集选择与退出码汇总；跨门面共用的仓库扫描、
钉版提取与版本解析比较 MUST 收进 `lib/` 且全仓仅此一份；只被单个门面
使用的联网探测逻辑亦 MUST 进 `lib/`，不与门面并列平铺。共享库 MUST 以
`Path(__file__)` 定位仓库根，MUST NOT 依赖调用方 cwd。

#### Scenario: 跳过目录集合单一来源

- **WHEN** 任一门面或共享库扫描仓库文件
- **THEN** 其排除目录集合取自 `lib/` 的单一常量，仓库内不存在第二份
  跳过目录清单

#### Scenario: 版本比较语义唯一

- **WHEN** 任一工具需要比较两个版本号大小或判断精确钉版
- **THEN** 判定取自 `lib/` 的统一实现（缺失补丁位按 0 补齐后比较），
  仓库内不存在第二套版本解析/比较实现

#### Scenario: 门面保持薄聚合

- **WHEN** 新增一条版本规则或体检段
- **THEN** 判定逻辑进 `lib/`，门面只增加"选入检查集 + 汇总"的接线，
  不在门面内内联规则判定

### Requirement: core 零绑定依赖，browser 自持全部 wasm 代码

core MUST 是纯数学库：源码 MUST NOT 含任何 `wasm_bindgen`/`js_sys`/`web_sys`
符号，`Cargo.toml` MUST NOT 含 wasm-bindgen/js-sys/web-sys/wasm-bindgen-futures
依赖或 `browser`/`browser-http`/`cov-drive` feature。句柄表、字符串 dispatch、
`#[wasm_bindgen(start)]` 注册钩子、browser fetch 后端与绑定测试 MUST 全部住在
`browser/` crate。browser 对 core 的依赖 MUST 零 feature（仅消费 core 纯数学
公开 API），使 core 可作为零绑定依赖库独立发布。browser 的跨端 dump 脚本 MUST
住 `browser/scripts/`；门禁与测试消费 browser 构建产物（wasm glue、worker 壳、
生成 dts）MUST 从 `browser/dist/` 读取，MUST NOT 依赖 typescript/dist 的发布
副本——该副本仅在 typescript 打包发布时由复制步骤生成。

#### Scenario: core grep 不到 wasm 符号

- **WHEN** grep `core/src/` 全目录的 `wasm_bindgen`、`js_sys`、`web_sys`
- **THEN** 零命中

#### Scenario: core 依赖树只剩数学库

- **WHEN** 在仓库根运行 `cargo tree -p netwave`（默认 feature，不开 native-http）
- **THEN** 依赖只剩 num-complex、strum、thiserror（+ 其传递依赖），无任何
  wasm-bindgen/js-sys/web-sys

#### Scenario: browser 零 feature 依赖 core

- **WHEN** 读取 `browser/Cargo.toml`
- **THEN** `netwave` 依赖不带任何 feature

#### Scenario: 句柄表与绑定测试住 browser

- **WHEN** 检查 `browser/src/` 与 `browser/` 测试目录
- **THEN** 句柄表、frequency/touchstone dispatch、start 钩子、coverage 驱动
  入口与句柄表测试均在 `browser/` 内，core 不再持有

#### Scenario: browser 产物消费读源头目录

- **WHEN** 检查 `scripts/run/test_cross.sh` 探针、`scripts/check_verbs.py`、
  `scripts/check_vocab_types.py` 引用的 browser 产物路径
- **THEN** 全部指向 `browser/dist/`，无一处读 typescript/dist 下的 browser
  产物副本；browser 端 dump 脚本位于 `browser/scripts/`
