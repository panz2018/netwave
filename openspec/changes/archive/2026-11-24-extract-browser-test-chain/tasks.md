# Tasks

## 1. coverage-dump 归位与编译期标志剔除（red 先于 green）

- [x] 1.1 先在 `scripts/tests/test_test_browser_wiring.py` 加一条会失败的断言：
      构建后 `browser/dist/netwave.worker.js` grep `dumpCoverage|__cov|NETWAVE_WASM_DIR`
      零命中（red——当前产物含这些符号，断言先红）
- [x] 1.2 落实 `coverage-dump归test`：把 `browser/src/coverage-dump.ts` 移到
      `browser/test/coverage-dump.ts`，worker import 路径改 `../test/coverage-dump.ts`
- [x] 1.3 落实 `标志名`：新增 `browser/src/global.d.ts` 声明
      `declare const __NETWAVE_COVERAGE__: boolean;`（即 `标志类型声明`，使
      `pnpm -C browser typecheck` 不报未定义标识符）
- [x] 1.4 落实 `编译期标志剔除`：worker 三条 control 分支、顶层
      `globalThis.__netwaveWasmInstance` 赋值、`covDir` 探针与 instrumented import
      分支全部包进 `if (__NETWAVE_COVERAGE__)` 守卫（覆盖顶层副作用，见 design
      「守卫必须覆盖顶层副作用」一节）
- [x] 1.5 落实 `标志三处填值`：`browser/tsdown.config.ts` worker 配置块加
      `define: { __NETWAVE_COVERAGE__: "false" }`；`browser/vitest.unit.config.ts`
      与 `browser/vitest.e2e.config.ts` 各加 `define: { __NETWAVE_COVERAGE__: "true" }`
- [x] 1.6 落实 `发布闸门位置`：`browser/scripts/publish_shell.mjs` 末尾加 grep
      `dist/netwave.worker.js`，命中覆盖率符号即非零退出；复跑 1.1 断言转绿

## 2. 测试入口脚本迁入 browser 与命令接线

- [x] 2.1 落实 `脚本迁入改名`：把 `scripts/run/test_browser.sh` 移到
      `browser/scripts/test.sh`（内部 `cd "$(dirname "$0")/../.."` 到仓库根仍两层，不改）
- [x] 2.2 落实 `browser命令叫test`：`browser/package.json` 的 `test` 改为
      `bash scripts/test.sh`（删原串 unit+e2e 的写法）
- [x] 2.3 落实 `根命令走pnpm`：根 `package.json` `test:browser` 改
      `pnpm -C browser test`；`.github/workflows/ci.yml` browser job 测试步骤改
      `pnpm -C browser test`（前置安装步保留）
- [x] 2.4 落实 `check_ci委托识别`：`scripts/check_ci.py` 增加委托形式识别——根
      `test:<seg>` 值以 `pnpm -C` 前缀开头时，校验 ci.yml 含该委托命令字符串；其余
      根脚本维持原 `bash scripts/run/test_<seg>.sh` 匹配。先给 `scripts/tests/` 补一条
      check_ci 委托识别的单测（red），再实现转绿
- [x] 2.5 落实 `wiring测试随迁`：`scripts/tests/test_test_browser_wiring.py` 的
      `TEST_BROWSER` 路径常量改 `browser/scripts/test.sh`；产物名断言随
      `产物名browser化` 改 browser，地板 99 不动
- [x] 2.6 落实 `产物名browser化`：迁入后的 `browser/scripts/test.sh` 产出与 gate
      阅卷路径 `coverage/coverage-wasm.lcov`→`coverage/coverage-browser.lcov`
      （地板 99 不动）；`.github/workflows/ci.yml` browser job 上传 path 同步
      （artifact 名 `coverage-browser-*` 已就位，不动）
- [x] 2.7 落实 `产物名browser化`：`scripts/tests/test_coverage_gate.py` fixture
      `coverage-wasm.info`→`coverage-browser.info`；先改断言（red）再随 2.6 转绿

## 3. spec delta 与波及面同步

- [x] 3.1 核对 `specs/ci-matrix/spec.md` delta 与实现一致（脚本位置、委托调用形式）
- [x] 3.2 核对 `specs/workspace-layout/spec.md` delta「browser 发布产物不含测试代码」
      scenario 与实现一致（grep 零命中）
- [x] 3.3 落实 `spec标签browser化`：ci-matrix delta 含 RENAMED 头（「全项目 wasm
      测试根聚合入口」→「全项目浏览器测试根聚合入口」）、删正文历史指针
      （scenario 标题受 openspec MODIFIED 约束保留原名）；「typescript 测试根聚合
      入口」「根 test 总聚合入口」死命令名 `build:wasm`→browser 包构建命令、
      `test:wasm`→`test:browser`；真技术名与 lessons-learned 账本不动
- [x] 3.4 落实 `spec标签browser化`：`Plan/测试规划.md`「CI wasm job」→
      「CI browser job」（描述性陈旧标签），改后跑 `pnpm check:md`
- [x] 3.5 落实 `产物名browser化`：ci-matrix delta 含「覆盖率报告命名与留存」
      「覆盖率门槛生效（铁律七）」两条 MODIFIED，产物名 `coverage-wasm.lcov`→
      `coverage-browser.lcov`（地板 99 不动，scenario 标题保留原名、整块复制）

## 4. 验证（引用根聚合入口）

- [x] 4.1 `pnpm test:browser` 全链 exit 0（node unit + e2e + rust lcov 地板）
- [x] 4.2 `pnpm test:cross` 四端对拍绿（确认 worker 产物改动未破坏跨绑定数值）
- [x] 4.3 `pnpm check` 全绿（含 check:ci、check:md、check_vocab/check_verbs）
- [x] 4.4 `pnpm -C browser typecheck` 绿（标志类型声明生效）

## 5. 收尾

- [x] 5.1 删除 `Plan/绑定放置重构.md` 中本 change 已定案章节（覆盖率链内部改名仍留
      后续，不删），删后跑 `pnpm check:md`（锚点 `Plan/`）
      ——本 change 未定案该 Plan 任何章节（其主体是 dispatch/句柄表搬迁阶段
      A/B/C，本 change 未做；§8 覆盖率链内部改名 99→100 依赖注入仍留后续），
      故无"已定案章节"可删；仅同步本 change 移动/改名造成的 stale 事实
      （`scripts/run/test_browser.sh`→`browser/scripts/test.sh`、
      `coverage-wasm.lcov`→`coverage-browser.lcov`），改后跑 `pnpm check:md` 绿。
- [x] 5.2 扫 `openspec/specs/` 全目录，产出本变更"更新/新增/退役"三态时效结论留痕
      （更新 = ci-matrix、workspace-layout；新增/退役 = 无）（锚点 `三态时效`）
      ——留痕：更新 ci-matrix（脚本位置、委托调用形式、产物名 browser 化、
      requirement RENAMED，均由本 change delta 承载，archive/sync 时落主 spec）；
      更新 workspace-layout（「browser 发布产物不含测试代码」scenario，delta 承载）；
      新增能力 = 无（归既有 ci-matrix/workspace-layout，不另立）；退役 spec = 无。
      lessons-learned 账本为冻结历史，不改。
- [x] 5.3 `pnpm test` 全绿先于 review（锚点：见 operations guidance）
- [x] 5.4 三轴 review：按 governance spec「元规则 review 三轴」对照本 change 工件审
      实现 diff，逐文件对上 tasks.md，硬伤清零（锚点 `三轴`）
      ——结论：Standards 轴净（注释均陈述当前契约，无门禁词表外语义考古；
      新增 v8 ignore 逐条附理由，合 LL-025）；Spec 轴净（delta 各 Requirement
      均有实现落地并经 4.1/4.2/4.3/4.4 验证）；Lessons 轴命中 LL-025（v8 ignore
      附理由）已满足、LL-062（worker 取全局走 js_sys::global）未触碰。越权核对：
      diff 文件集逐文件对上 tasks.md，唯一超出项 `browser/test/vite-env.d.ts`
      为修迁移遗漏（typescript→browser 时 `?raw` ambient 声明未随迁，HEAD 即
      typecheck 红），属 task 4.4「typecheck 绿」的必要前提，非越权。
- [x] 5.5 被触碰文件全文只读体检（health-check apply 态：语义考古维 + 四维，发现附
      文件+行号+证据落 Plan/）（锚点 `体检`）
      ——发现 1 项：`browser/test/coverage-dump.ts:3` stale 自指路径
      `test/wasm/coverage-dump.ts`（迁移遗留旧路径，不在本次 diff 行内），
      附证据落 `Plan/体检发现-extract-browser-test-chain.md` 等点名，不阻塞。
- [x] 5.6 迟到追加核对：回看本会话拍板是否全部落工件（`coverage-dump归test`、
      `编译期标志剔除`、`标志名`、`标志三处填值`、`标志类型声明`、`发布闸门位置`、
      `脚本迁入改名`、`browser命令叫test`、`根命令走pnpm`、`check_ci委托识别`、
      `wiring测试随迁`、`spec标签browser化`、`产物名browser化` 载体任务全打勾）
      （锚点 `迟到追加`）
- [x] 5.7 最后一项：跑 `pnpm check:outdated` 并按 dependency-upgrade spec 消化 LAG，
      复跑至退出码 0（锚点 `check:outdated`）
      ——首跑 12 LAG（pnpm 1、cargo 6、uv 4）全消化：`cargo update`（anyhow/hyper/
      napi/napi-build/napi-derive/napi-derive-backend 传递升）、`uv lock --upgrade`
      ×2（coverage/packaging）、pnpm CLI 12.21→12.23（npm -g 原生二进制 swap 在本机
      nvm 环境不生效，改 `pnpm self-update` 装 standalone 并自动 bump
      `packageManager` pin）。升级后复跑 `pnpm check`=0（biome ^2.6.8 新格式要求
      已 `--write`）、`pnpm test` 全量=0（各地板达标、四端 bit-exact）；
      `pnpm check:outdated` 复跑 SUMMARY=0 LAG。
- [x] 5.8 落实 `跳过archive态体检`：本 change 归档完成后的 archive 态全项目只读体检
      跳过（health-check spec「archive 态」），apply 态被触碰文件体检（5.5）照常执行
      ——跳过 2026-11-23
