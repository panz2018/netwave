# Tasks

## 1. coverage-dump 归位与编译期标志剔除（red 先于 green）

- [ ] 1.1 先在 `scripts/tests/test_test_browser_wiring.py` 加一条会失败的断言：
      构建后 `browser/dist/netwave.worker.js` grep `dumpCoverage|__cov|NETWAVE_WASM_DIR`
      零命中（red——当前产物含这些符号，断言先红）
- [ ] 1.2 落实 `coverage-dump归test`：把 `browser/src/coverage-dump.ts` 移到
      `browser/test/coverage-dump.ts`，worker import 路径改 `../test/coverage-dump.ts`
- [ ] 1.3 落实 `标志名`：新增 `browser/src/global.d.ts` 声明
      `declare const __NETWAVE_COVERAGE__: boolean;`（即 `标志类型声明`，使
      `pnpm -C browser typecheck` 不报未定义标识符）
- [ ] 1.4 落实 `编译期标志剔除`：worker 三条 control 分支、顶层
      `globalThis.__netwaveWasmInstance` 赋值、`covDir` 探针与 instrumented import
      分支全部包进 `if (__NETWAVE_COVERAGE__)` 守卫（覆盖顶层副作用，见 design
      「守卫必须覆盖顶层副作用」一节）
- [ ] 1.5 落实 `标志三处填值`：`browser/tsdown.config.ts` worker 配置块加
      `define: { __NETWAVE_COVERAGE__: "false" }`；`browser/vitest.unit.config.ts`
      与 `browser/vitest.e2e.config.ts` 各加 `define: { __NETWAVE_COVERAGE__: "true" }`
- [ ] 1.6 落实 `发布闸门位置`：`browser/scripts/publish_shell.mjs` 末尾加 grep
      `dist/netwave.worker.js`，命中覆盖率符号即非零退出；复跑 1.1 断言转绿

## 2. 测试入口脚本迁入 browser 与命令接线

- [ ] 2.1 落实 `脚本迁入改名`：把 `scripts/run/test_browser.sh` 移到
      `browser/scripts/test.sh`（内部 `cd "$(dirname "$0")/../.."` 到仓库根仍两层，不改）
- [ ] 2.2 落实 `browser命令叫test`：`browser/package.json` 的 `test` 改为
      `bash scripts/test.sh`（删原串 unit+e2e 的写法）
- [ ] 2.3 落实 `根命令走pnpm`：根 `package.json` `test:browser` 改
      `pnpm -C browser test`；`.github/workflows/ci.yml` browser job 测试步骤改
      `pnpm -C browser test`（前置安装步保留）
- [ ] 2.4 落实 `check_ci委托识别`：`scripts/check_ci.py` 增加委托形式识别——根
      `test:<seg>` 值以 `pnpm -C` 前缀开头时，校验 ci.yml 含该委托命令字符串；其余
      根脚本维持原 `bash scripts/run/test_<seg>.sh` 匹配。先给 `scripts/tests/` 补一条
      check_ci 委托识别的单测（red），再实现转绿
- [ ] 2.5 落实 `wiring测试随迁`：`scripts/tests/test_test_browser_wiring.py` 的
      `TEST_BROWSER` 路径常量改 `browser/scripts/test.sh`；`coverage-wasm.lcov`/地板
      99 断言本轮不动（Non-goals）

## 3. spec delta 与波及面同步

- [ ] 3.1 核对 `specs/ci-matrix/spec.md` delta 与实现一致（脚本位置、委托调用形式）
- [ ] 3.2 核对 `specs/workspace-layout/spec.md` delta「browser 发布产物不含测试代码」
      scenario 与实现一致（grep 零命中）
- [ ] 3.3 落实 `spec标签browser化`：ci-matrix delta 含 RENAMED 头（「全项目 wasm
      测试根聚合入口」→「全项目浏览器测试根聚合入口」）、删正文历史指针
      （scenario 标题受 openspec MODIFIED 约束保留原名）；「typescript 测试根聚合
      入口」「根 test 总聚合入口」死命令名 `build:wasm`→browser 包构建命令、
      `test:wasm`→`test:browser`；真技术名与 lessons-learned 账本不动
- [ ] 3.4 落实 `spec标签browser化`：`Plan/测试规划.md`「CI wasm job」→
      「CI browser job」（描述性陈旧标签），改后跑 `pnpm check:md`

## 4. 验证（引用根聚合入口）

- [ ] 4.1 `pnpm test:browser` 全链 exit 0（node unit + e2e + rust lcov 地板）
- [ ] 4.2 `pnpm test:cross` 四端对拍绿（确认 worker 产物改动未破坏跨绑定数值）
- [ ] 4.3 `pnpm check` 全绿（含 check:ci、check:md、check_vocab/check_verbs）
- [ ] 4.4 `pnpm -C browser typecheck` 绿（标志类型声明生效）

## 5. 收尾

- [ ] 5.1 删除 `Plan/绑定放置重构.md` 中本 change 已定案章节（覆盖率链内部改名仍留
      后续，不删），删后跑 `pnpm check:md`（锚点 `Plan/`）
- [ ] 5.2 扫 `openspec/specs/` 全目录，产出本变更"更新/新增/退役"三态时效结论留痕
      （更新 = ci-matrix、workspace-layout；新增/退役 = 无）（锚点 `三态时效`）
- [ ] 5.3 `pnpm test` 全绿先于 review（锚点：见 operations guidance）
- [ ] 5.4 三轴 review：按 governance spec「元规则 review 三轴」对照本 change 工件审
      实现 diff，逐文件对上 tasks.md，硬伤清零（锚点 `三轴`）
- [ ] 5.5 被触碰文件全文只读体检（health-check apply 态：语义考古维 + 四维，发现附
      文件+行号+证据落 Plan/）（锚点 `体检`）
- [ ] 5.6 迟到追加核对：回看本会话拍板是否全部落工件（`coverage-dump归test`、
      `编译期标志剔除`、`标志名`、`标志三处填值`、`标志类型声明`、`发布闸门位置`、
      `脚本迁入改名`、`browser命令叫test`、`根命令走pnpm`、`check_ci委托识别`、
      `wiring测试随迁`、`spec标签browser化` 载体任务全打勾）（锚点 `迟到追加`）
- [ ] 5.7 最后一项：跑 `pnpm check:outdated` 并按 dependency-upgrade spec 消化 LAG，
      复跑至退出码 0（锚点 `check:outdated`）
- [ ] 5.8 落实 `跳过archive态体检`：本 change 归档完成后的 archive 态全项目只读体检
      跳过（health-check spec「archive 态」），apply 态被触碰文件体检（5.5）照常执行
      ——跳过 2026-11-23
