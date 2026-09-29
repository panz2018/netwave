# typescript 源码化规划（工具链已定案，worker 常驻架构已定案，源码改写未执行）

## 背景与动机

当前 `typescript/src/` 只有手写 `.mjs`/`.cjs`/`.js` 壳文件 + 手写
`index.d.ts`，存在双份维护问题：

- `index.d.ts` 契约与 `index.node.mjs`/`index.browser.mjs`
  里的 JSDoc 各写一遍，改签名要同步两处，会漂移。
- CJS 壳（`index.node.cjs`）是 ESM 壳的手工翻译版——正是打包器要解决的"多格式输出"痛点。
- 目标是让 TS 消费者拿到真正的类型与可维护源码，所以不能只有壳文件，需要 TS 源码。

评估过 [Rslib](https://rslib.rs/)（web-infra-dev/rslib）：在"无 TS 源码"的前提下不需要它；一旦源码化，它的 ESM+CJS+`dts`
一次输出、`target: node/web` 分壳、Worker 语法原生识别就真正对上了。

## 目标结构

```text
src/
  types.ts          # NetwaveBuffer 等公共类型（契约单一来源）
  index.node.ts     # node 壳：import napi glue（external）
  index.browser.ts  # browser 壳：import wasm-pack glue（external）
  worker.ts
  standalone.ts
```

关键约束：

- napi 生成的 `index.node.generated.mjs` 与 wasm-pack glue 保持
  **external**（不进 bundle）；打包器只编译本项目自己的壳，与 Rslib 的
  `external`/`autoExternal` 模型吻合。
- `index.d.ts` 改为从源码生成，手写契约并入 `types.ts`。
- 现有 `publish_shell.mjs` 发布逻辑保持不变（壳文件重写规则见
  [typescript/README.md](../typescript/README.md)）。
- 零拷贝契约（`NetwaveBuffer`
  描述符、await 后重建视图）不受影响——打包只碰 JS 壳，不碰 `.node`/`.wasm`
  二进制路径。

## 工具选型（已定案）

| 环节                        | 定稿                                                                   | 理由                                                                                                                        |
| --------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| 包管理                      | pnpm（不动）                                                           | workspace 主场，已定                                                                                                        |
| 测试/覆盖率                 | Vitest（不动，100% 阈值）                                              | wasm/ESM 场景唯一顺手                                                                                                       |
| lint+format (JS/TS/JSON)    | **Biome**（全仓库）                                                    | 单二进制替代 ESLint+Prettier 三件套；薄壳用不上插件生态；与 Rust 工具气质一致                                               |
| format (Markdown)           | **Prettier `proseWrap: "preserve"`**（全仓库 `*.md`，忽略 `.claude/`） | 统一列表/标题结构、不重排段落换行（中文+行内代码下 `always` 会碎断）；markdownlint 关掉与 Prettier 冲突的规则只留内容性规则 |
| 打包                        | **tsdown**（Rslib 降备选）                                             | 只需"TS→ESM+CJS+dts+IIFE + external glue"，Rslib 差异化能力（MF/样式/wasm 源码集成）全用不上，tsdown 配置量最小             |
| `.node`/`.wasm` 二进制+glue | napi build / wasm-pack（不动，external）                               | 打包器不介入二进制管线                                                                                                      |

**CJS 去留（已拍板：保留）**：`build:native` 本就跑两遍 napi 各出 ESM/CJS
glue，tsdown `format: ["esm","cjs"]` 顺手出 CJS，成本近零；Jest 默认 CJS、老工具
`require()` 场景仍在，防御性保留，等真实用户反馈再议砍除。

tsdown 产物清单：`index.node.mjs` / `index.node.cjs` / `index.browser.mjs` /
`index.d.ts` / `standalone.js`（IIFE，HTML `<script>` 直接导入）/
`netwave.worker.js`。

## worker 常驻架构（已定案）

无 SharedArrayBuffer 环境（GitHub Pages 无 COOP/COEP）下跨线程消息传递的渐近
最优：数据仅经显式 `upload` transfer 进入 worker 一次，之后命令移动、数据不动。
以下契约级定案随 worker 实现 change 同步进主 spec（见执行步骤第 6 条），本次
主 spec 不动：

- **数据权威在常驻 worker 的 wasm 内**：全部数据、状态、计算常驻单个 Web
  Worker 内的 wasm 实例；主线程不持有 wasm 实例、不持有数据副本——无双实例、
  无双份数据，不存在权威歧义。
- **单点所有权，移动仅经显式 transfer**：`upload` 显式 transfer 托管输入，
  托管后驻留 worker 反复可用；普通计算动词不静默消耗输入（`upload` 后主线程
  视图 detached 是规范强制，非可选）。
- **结果一律 transfer 传出、worker 不留副本**：结果 buffer 新分配、所有权移交
  主线程，transfer 出去的 buffer 在 worker 侧自动消失。
- **计算与元数据读取一律异步进 worker**：`shape`/`frequency` 等元数据同样在
  worker 内读取、搭结果消息便车回传；主线程从已 resolve 的返回值同步读
  描述符（描述符随结果回传，不算数据副本）。
- **`_` 同步逃生口两端不对称**：浏览器端 `_` 前缀同步计算函数废止（主线程无
  wasm，同步计算无处发生，不加 deprecated，随实现落地删除）；node 端保留 `_`
  同步函数（napi core 在进程内，同步直通永远可行，私有面不污染公开 API）。
  公开 API 两端一致：全 async。
- **worker 常驻至页面关闭**：由库的 async 壳托管长生命周期 worker；worker 异常
  终止（浏览器 OOM 等）数据丢失为**已接受行为**，API 不承诺恢复，不引入
  IndexedDB（复杂度超出收益）。
- **Worker 池未来再讨论**：前置门槛 = 数据分片归属（数据驻留与池化冲突），
  worker 实现落地时决定单 worker 或池。
- **standalone.js 形态**：内部自起常驻 worker，Pages / `<script type="module">`
  用户依旧零配置。
- **真浏览器测试线**（随 worker 实现落地）：vitest browser mode + playwright
  provider + 仅 Chromium（同一套测试代码与 `pnpm test` 入口，真 worker/真
  transfer/真 detach 只有真浏览器能验证）；不引入 `@playwright/test`（纯计算库
  无 UI E2E 需求），多浏览器矩阵待浏览器特异 bug 出现再加。
- **LL-001 分流废止**："小数据不起 Worker、直接同步 resolve"随本方案废止——
  所有计算不管大小全进常驻 worker（每次 ~1ms 消息往返，公开面本就全 async，
  用户无感）。

## 执行步骤

0. （已落地）接入 `typescript/tsconfig.json`
   （strict+allowJs+noEmit）、根 `biome.jsonc`、根 `.prettierrc.json`
   （proseWrap preserve，只管 `*.md`）、markdownlint 关冲突规则、
   CI 加 biome/prettier/tsc 步骤 → 验证：`biome check .`、
   `prettier --check "**/*.md"`、`tsc --noEmit`、markdownlint、check_md 全绿。
1. 壳改写为 TS 源码（`types.ts` 收编 `index.d.ts` 契约）→
   验证：`tsc --noEmit` 通过、vitest 直接测 `.ts` 全绿。
   - **一并解决现存 test typing 问题**：`typescript/test/`
     下**全部**测试文件都有同类问题——凡解构 `fillPattern` 返回值处编辑器报
     TS2339（`buffer`、`byteOffset`、`length` 不存在于 `object` 类型），
     `test/wasm/wasm.roundtrip.test.ts`、`test/native/native.roundtrip.test.ts`、
     `test/wasm/worker.test.ts` 等无一幸免——根因是 wasm-bindgen 把
     `js_sys::Object` 映射为裸 `object`（napi glue 同样无类型），类型在
     `.mjs`/`.cjs` 无类型壳边界丢失；CI 绿只因
     `checkJs: false` + `exclude: ["test"]` 双重豁免。源码化后 `src/` 为
     typed TS、返回类型标注 `NetwaveBuffer`，报错自然消失；届时把 `test/`
     移回 tsconfig include、翻开 `checkJs`，让 test 进类型门禁（验证：
     `tsc --noEmit` 含 test 全绿）。过渡期若需消编辑器报错，可在壳的
     `@returns` JSDoc 引用 `import("./index.d.ts").NetwaveBuffer`，但源码化
     时随 JSDoc 一并删除，不留双份。
2. 接入 tsdown，输出 esm（node/browser 分 target）、cjs 与 dts；
   napi/wasm glue 保持 external → 验证：`dist/` 产物与旧壳 exports
   逐一对齐（`exports.test.ts` 扩展断言）。
   - **tsdown × TypeScript 7 验证结论（实测，tsdown 0.23.0 / rolldown
     1.2.11）**：bundle 路径全绿（4 壳一次出，external 生效；旗标
     `external` 已弃用，正式接入用 `deps.neverBundle`）；**dts × TS7 不兼容**
     ——tsgo 对任意入口（含最小 `.ts`）均不生成 dts，tsdown 自身告警
     "TypeScript 7.0 … experimental"；**回退方案已验证可行**：钉
     `typescript@6`（现 `^6.0.3`）后 dts 正常生成，且 esm 格式产物名为
     `.d.mts`——正式接入时 `exports.types` 需对齐 `.d.mts`（或双出）。源码化
     步骤 1（壳改 `.ts`）后重测 TS7 dts，兼容则升回 7。
3. 测试入口切到源码；覆盖率 `/* v8 ignore */` 逐条保留理由 → 验证：`test:native`
   / `test:wasm` 覆盖率仍 100%。
4. 跨绑定对拍回归（`scripts/cross_compare.py`
   四端）→ 验证：逐 bit + 容差 + 篡改自检全绿。
5. 更新 [typescript/README.md](../typescript/README.md)
   的 Commands 与 Gotchas；本文件按 Plan 生命周期吸收进 spec/README 后删除。
6. 主 spec 修订随 worker 实现 change 同步（本规划不动主 spec）：governance
   spec 升格"单点所有权 + 移动仅经显式 transfer + 常驻 worker 为数据权威 +
   主线程无 wasm"；zero-copy-roundtrip spec 第 1/2/6 条按
   [worker 常驻架构](#worker-常驻架构已定案) 节改写（分流废止、
   浏览器 `_` 废止、元数据搭结果便车）→ 验证：实现 change 归档时主 spec 含
   上述条款，`openspec validate` 绿。

## wasm target 形态（已定案：长期 web）

`--target web` 为长期形态：单产物喂 vitest / 浏览器 / GitHub Pages，
`<script type="module">` + 显式 `init()` 零构建直接嵌入；bundler glue 在
node/vitest 不可加载（账本 LL-017），转 bundler 需另维构建线 + 测试线 +
standalone，收益当前为零。

已知代价：npm bundler（Vite/webpack）用户需自管 `.wasm` 落位——web glue 的
运行时 `fetch` 对打包器是黑盒，`.wasm` 不进对方模块图，用户须拷进 public 目录
或 `init()` 传自有 URL（README 文档级说明，非不能用）。待真实 npm bundler 用户
需求出现，增量加 `--target bundler` 构建 + `exports.browser` 条件分发——纯加法、
非破坏性，其余用户不受影响。定案随 worker 实现 change 落地后升格进 governance
spec（见执行步骤第 6 条）。

## 风险与保留意见

- wasm 路径：打包器的 wasm 源码集成（compile/preserve 等模式）一律不启用，保持 wasm-pack
  `--target web`
  自带 glue；打包器不应介入 wasm 加载，否则 worker 内存不可 transfer 等已趟平的坑（见
  [typescript/README.md](../typescript/README.md) 的Implementation
  notes）会重踩。
- CI node 格子与 rust job wasm32 格已恢复；源码化后打包步骤需同步加进两处
  （node job 的 build 步骤换为 tsdown 产物）。
