# Proposal

## Why

browser 包独立化战役（`extract-browser-package` → `extract-browser-bindings`）已把
源码、测试入口、安装脚本、绑定代码全部归位 `browser/`，但跨端对拍（cross）这一环
仍散落在 typescript：browser 段的 dump 代码混在 `typescript/scripts/dump.mjs` 里、
以 node 伪造 worker 作用域驱动 `typescript/dist/` 的发布副本，`test_cross.sh` 探针与
`check_verbs.py`/`check_vocab_types.py` 门禁也读 typescript/dist 里的 browser 产物。
这既违反「browser 自我完整」的既定判据（删掉 `browser/` 必须跟着删的文件就是 browser
资产），也让浏览器端 dump 走的是 node 模拟路径——与 zero-copy-roundtrip spec
「浏览器路径的验收 MUST 在真浏览器完成（不以 node 模拟替代）」口径不符。

## What Changes

- **BREAKING**（内部脚本位置/命名）：`typescript/scripts/dump.mjs` 拆两端——node(napi)
  段留 typescript 改名 `dump.node.mjs`；browser 段重写为真浏览器 harness（独立
  playwright 脚本：静态服务器挂 `browser/dist/` + `oracle/samples/` → File 上传 →
  真壳 `fromFile`/`toFile` → anchor 下载 `saveAs` 落盘），迁至
  `browser/scripts/dump.mjs`（目录内命名不带 wasm/browser）。
- **BREAKING**（消费路径）：`scripts/run/test_cross.sh` 探针改读 `browser/dist/`
  （wasm glue 缺失提示 `pnpm -C browser build`）；`scripts/check_verbs.py`、
  `scripts/check_vocab_types.py` 的 browser dts 路径改指 `browser/dist/`。
- **BREAKING**（oracle 端名）：跨端阅卷端标识 `wasm` → `browser`——
  `oracle/compare_cross.py` 的 ENDS、答卷目录名 `oracle/tmp/browser/`、
  `oracle/manifest.json` note、`oracle/README.md`。真技术名（`wasm32-*`、
  `wasm-pack`、`dist/wasm/` 产物目录、wasm 数值容差语义）不动，沿用
  `extract-browser-test-chain` 的「陈旧标签 browser 化、真技术名保留」先例。
- npm 入口：typescript `cross-dump` → `dump:node`；browser 新增 `dump`；
  CI node job 增 `playwright install --only-shell chromium`。
- `typescript/scripts/merge_browser.mjs` 与发布壳 exports **不动**——单包在
  typescript 发布的形态不变，复制步骤保留为纯发布构建步骤。

## Capabilities

### New Capabilities

<!-- 无新增 capability，全部落在既有 capability 的 requirement 修订。 -->

### Modified Capabilities

- `ci-matrix`: 「cross-binding 测试根聚合入口」requirement 修订——browser 端产物
  探测改 `browser/dist/`（缺失提示 `pnpm -C browser build`），dump 拆两条命令
  （node 端 `typescript/scripts/dump.node.mjs`、browser 端
  `browser/scripts/dump.mjs` 真浏览器 harness）。
- `oracle-harness`: 端标识 `wasm` → `browser`——「oracle 子项目是交叉验证的唯一
  阅卷处」「dump 产物分层布局」「横向轴一致性判定」「anti-tautology 扰动自检」
  四条 requirement 正文的端名单与答卷目录名随之更新；容差语义不变（browser 端
  即 wasm 实现，仍走 `core_tol.relative`）。
- `zero-copy-roundtrip`: 「cross-binding 往返对拍」requirement 修订——browser 端
  dump MUST 经真浏览器 harness（playwright + chromium）执行，node 伪造 worker
  路径退役；dump 脚本承载位置写死到两端各自包内。
- `workspace-layout`: 「core 零绑定依赖，browser 自持全部 wasm 代码」requirement
  扩充——browser 的跨端 dump 脚本与构建产物自我完整，门禁/测试读 browser 产物
  MUST 从 `browser/dist/` 读取；typescript 的发布副本仅在打包时生成。

## Impact

- 移动/改名：`typescript/scripts/dump.mjs` → `typescript/scripts/dump.node.mjs`
  （删 browser 段）；新增 `browser/scripts/dump.mjs`。
- 改动：`scripts/run/test_cross.sh`（探针 + dump 两条命令）、
  `scripts/check_verbs.py`、`scripts/check_vocab_types.py`、
  `oracle/compare_cross.py`、`oracle/manifest.json`、`oracle/README.md`、
  `typescript/package.json`（`dump:node`）、`browser/package.json`（`dump`）、
  `.github/workflows/ci.yml`（node job +chromium 安装步、dump 命令）、
  `scripts/tests/` 相关 wiring 镜像测试。
- 文档：`scripts/README.md`、`typescript/README.md`、`browser/README.md`；
  `Plan/绑定放置重构.md` §6 发包形态项与 `Plan/测试规划.md` wasm dump harness
  行吸收后删除。
- spec：`ci-matrix`、`oracle-harness`、`zero-copy-roundtrip`、`workspace-layout`
  （经 delta）。
- 不受影响：`typescript/scripts/merge_browser.mjs`、发布壳 exports、
  `browser/dist/wasm/` 产物目录名（真技术名）、oracle 容差数值。
- 受影响铁律：铁律八（真浏览器场景验收——本 change 把 dump 从 node 模拟改为真
  chromium，正是该铁律口径的落实）。

## Non-goals

- 不改 npm 发包实现细节（发布壳复制 vs 依赖导入的选择留待
  `Plan/发布许可打包.md` 承载的发包 change 拍板；本 change 只固定「单包在
  typescript 发布」这一形态裁决）。
- 不动 `browser/dist/wasm/`、`wasm32-unknown-unknown`、`wasm-pack` 等真技术名。
- 不动 oracle 容差数值与 manifest 结构（仅 note 措辞随端名更新）。
- 不合并 vitest e2e 线与 dump harness（dump 是独立一次性脚本，不进测试套件）。

## Prior art

- 仓库内先例：`openspec/changes/archive/2026-11-24-extract-browser-test-chain/`
  确立「browser 测试资产随链路归位迁入 `browser/`」与「陈旧 wasm 标签 browser
  化、真技术名保留」两条同判据模式；`openspec/changes/archive/2026-11-24-relocate-browser-install-scripts/`
  确立「删掉 `browser/` 必须跟着删的文件就是 browser 资产」判据。
- harness 方向沿用 `Plan/测试规划.md` 已定条目（静态服务器 + File 上传 + anchor
  下载 saveAs，退路 `file.arrayBuffer()` 经 evaluate 回传）。
- 同生态无现成方案：跨绑定 dump 需与本仓 worker 常驻架构耦合，playwright 官方
  仅给 [download 事件通用示例](https://playwright.dev/docs/downloads)，按本仓
  契约自组。

## 专家增补

- 实施第一步先实证 headless chromium 的 download 事件 + `saveAs` 在
  `browser/scripts/dump.mjs` 的最小骨架里可用（Plan 已定实证步骤），失败即切
  `file.arrayBuffer()` 经 evaluate 回传的退路，避免整条 harness 写完才发现落盘
  方式不通。
- `scripts/check_verbs.py` 的 `WASM_GLUE_DTS`/`BROWSER_DTS` 常量与
  `scripts/check_vocab_types.py` 的 browser dts 路径同批改指 `browser/dist/`，
  并跑 `pnpm check:meta` 实证门禁在新路径下仍绿，防「只改了 dump 消费方、漏了
  门禁消费方」的半截归位。
- `oracle/compare_cross.py` 端名改名后跑一次扰动自检（脚本内置 anti-tautology）
  确认新端名 `browser` 的注入定位仍生效，防端名单改漏导致该端静默退出比对。

## 已定裁决

- `单包发布`：npm 发布维持单包在 typescript；browser 自我包含，发布壳复制/导入
  自选、与本 change 无关。
- `产物源头`：test_cross 探针与门禁读 browser 产物一律从 `browser/dist/`，编译
  也在 browser 内；typescript/dist 的副本仅发布打包时生成。
- `dump拆分`：node 段留 typescript 改名 `dump.node.mjs`；browser 段迁
  `browser/scripts/dump.mjs`，命名去 wasm/browser。
- `真harness`：browser 段重写为独立 playwright 脚本（静态服务器挂 dist/+samples/
  → File 上传 → 真壳 fromFile/toFile → anchor 下载 saveAs）；实证失败退路
  `file.arrayBuffer()` 经 evaluate 回传。
- `端名`：oracle 端标识 `wasm` → `browser`（ENDS、答卷目录名、manifest note、
  README）；真技术名保留。
- `答卷`：dump 答卷仍落 `oracle/tmp/browser/`——oracle 阅卷材料，非 browser 包
  资产。
- `merge_browser`：`typescript/scripts/merge_browser.mjs` 保留原位原样，纯发布
  步骤。
- `一个change`：产物归位 + dump 拆分重写 + 端名改名一次做完，不拆批次。
