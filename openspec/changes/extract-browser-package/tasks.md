# Tasks

## 1. browser 包骨架与搬迁

- [x] 1.1 建 `browser/` 目录：`Cargo.toml`（crate name `netwave-browser`，
      cdylib，依赖 core features browser+browser-http）、`package.json`
      （`private: true`，见 `browser私有包`），落实 `browser顶层包`
- [x] 1.2 把 glue crate（原 `typescript/wasm/src/lib.rs`，含 coverage dump
      入口）迁入 `browser/src/`，保持空 force-link 壳语义（`glue空壳`）
- [x] 1.3 迁 `netwave.worker.ts`、`index.browser.ts`、`types.ts` 进
      `browser/src/`，落实 `壳随worker进browser`；保持 worker 的
      `new Worker(new URL(...))` vite 邻接约束
- [x] 1.4 迁浏览器端测试：`typescript/test/wasm/`→`browser/test/unit/`、
      `typescript/test/browser/`→`browser/test/e2e/`，落实 `browser内测试改名`
- [x] 1.5 迁 vitest 配置：`vitest.wasm.config.ts`→`browser/vitest.unit.config.ts`、
      `vitest.browser.config.ts`→`browser/vitest.e2e.config.ts`，include 路径同步
- [x] 1.6 browser 自产全部浏览器 dist：`gen:constants`、wasm-pack 产物
      （`netwave_browser.js`+`.wasm`）、壳/`./standalone`/`./worker` 编译、dts
      全部落 **`browser/dist/`**（browser package.json `exports` 含
      `.`/`./standalone`/`./worker`，结构上可独立发布；改掉现状
      `--out-dir ../dist/wasm-web` 反向耦合），落实 `browser自包含可独立发布`
      与 `workspace依赖消费`

## 2. 命名统一（平台名 browser，技术名保留）

- [ ] 2.1 crate/目录/产物改名 `netwave-wasm`→`netwave-browser`、
      `netwave_wasm.js`→`netwave_browser.js`，落实 `browser命名`；全仓 grep
      `netwave_wasm` 逐处改（壳 import、worker、vitest alias、tsdown）
- [ ] 2.2 typescript 包内命令改名 `test:wasm`→`test:unit`、
      `test:browser`→`test:e2e`，内置 `--coverage` 不变
- [ ] 2.3 根命令改名 `test:wasm`→`test:browser`、CI job `wasm`→`browser`、
      artifact `coverage-wasm-*`→`coverage-browser-*`，落实 `根命令与CI改名`；
      技术名 wasm32/wasm-pack/wasm-opt 一律保留
- [ ] 2.4 覆盖率链内部命名（`test_wasm.sh`、`coverage-wasm.lcov`、
      `coverage_gate.py` 匹配）本轮不动，落实 `覆盖率链内部命名不动`；
      把后续改名项写入 `Plan/绑定放置重构.md`

## 3. typescript 回归 node + 薄封装

- [ ] 3.1 typescript 删 worker/壳/types/test（已迁 browser），加
      `netwave-browser` workspace 依赖，落实 `typescript承载node加薄封装`
- [ ] 3.2 合并发布（见 design「构建期合并」决策）：typescript build 把
      browser 已产出的 `browser/dist/`（壳/standalone/worker/wasm/constants/dts）
      合并进 `typescript/dist`；typescript 自产 node 产物 + 薄封装入口，
      `exports.browser`/`./standalone`/`./worker` 指向合并进来的 browser 产物；
      native 不动（`native本轮不动`）
- [ ] 3.3 typescript 集成测试：exports 条件解析（node→napi、browser→合并产物）、
      双端同 API 面；发布物自包含（不运行时依赖未发布的 netwave-browser）

## 4. workspace 与 CI 接线

- [ ] 4.1 根 `Cargo.toml` members 改 core/python/browser/typescript/native；
      `pnpm-workspace.yaml` packages 改 browser、typescript
- [ ] 4.2 `ci.yml`：browser job（原 wasm）测试步骤单行调脚本；typescript job
      维持自建 browser 产物、不加 `needs: browser`，落实 `CI各自自建产物`
- [ ] 4.3 spec 落点：边界写 `workspace-layout`、措辞改 `ci-matrix`、worker
      分发留 `api-contract` 不动，落实 `不新建browser-spec`

## 5. 验证（引用根聚合入口）

- [ ] 5.1 `cargo metadata --no-deps` members 恰为 core/python/browser/
      typescript/native（workspace-layout scenario）
- [ ] 5.2 `pnpm test` 全绿（含 node/browser/python/rust/cross 全链）
- [ ] 5.3 `pnpm test:browser` 全链 exit 0（node 单元 + 真浏览器 e2e + rust lcov 地板）
- [ ] 5.4 `pnpm test:cross` 四端对拍绿（browser 产物改名后 cross dump 仍读到）
- [ ] 5.5 `pnpm check` 全绿（含 check:md、check:ci、check_vocab/check_verbs）

## 6. 收尾

- [ ] 6.1 删除 `Plan/绑定放置重构.md` 中本 change 已定案章节，只留未执行项
      （dispatch 搬迁、native 独立、覆盖率链改名、发布形态），删后跑
      `pnpm check:md`（锚点 `Plan/`）
- [ ] 6.2 扫 `openspec/specs/` 全目录，产出本变更"更新/新增/退役"三态时效
      结论留痕（锚点 `三态时效`）
- [ ] 6.3 `pnpm test` 全绿先于 review（锚点：见 operations guidance）
- [ ] 6.4 三轴 review：按 governance spec「元规则 review 三轴」对照本 change
      工件审实现 diff，逐文件对上 tasks.md，硬伤清零（锚点 `三轴`）
- [ ] 6.5 被触碰文件全文只读体检（health-check apply 态：语义考古维 + 四维，
      发现附文件+行号+证据落 Plan/）（锚点 `体检`）
- [ ] 6.6 迟到追加核对：回看本会话拍板是否全部落工件（锚点 `迟到追加`）
- [ ] 6.7 归档阶段 `跳过archive态体检`：本 change 归档完成后的 archive 态
      全项目只读体检跳过（health-check spec「archive 态」），apply 态被触碰
      文件体检（6.5）照常执行——跳过 2026-11-22
- [ ] 6.8 最后一项：跑 `pnpm check:outdated` 并按 dependency-upgrade spec
      消化 LAG，复跑至退出码 0（锚点 `check:outdated`）
