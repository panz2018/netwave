# typescript 源码化规划（源码化已落地，剩 worker 实现与后续演进）

工具链与源码改写（TS 壳 + tsdown + dts 生成 + 类型门禁）已由
ts-source-rewrite change 落地（已归档，追溯靠 git log）；
worker 常驻架构定案已入主 spec 与账本（追溯靠 git log）。
本文件只留未执行任务。

## 待执行：worker 实现（常驻架构落地）

契约级定案（数据权威在常驻 worker wasm、单点所有权、结果 transfer 传出、
元数据搭结果便车、浏览器 `_` 废止 / node 保留、worker 常驻至页面关闭）已定案，
随实现 change 同步进主 spec：

- governance spec 升格"单点所有权 + 移动仅经显式 transfer + 常驻 worker 为
  数据权威 + 主线程无 wasm"。
- zero-copy-roundtrip spec 按定案改写（分流废止、浏览器 `_` 废止、元数据
  搭结果便车）→ 验证：实现 change 归档时主 spec 含上述条款，
  `openspec validate` 绿。
- 浏览器端 `_` 同步计算函数随实现落地删除（不加 deprecated）。
- Worker 池 or 单 worker：实现落地时决定（前置门槛 = 数据分片归属）。
- standalone.js 改为内部自起常驻 worker（Pages / `<script type="module">`
  零配置不变）。
- 真浏览器测试线随实现落地：vitest browser mode + playwright provider +
  仅 Chromium（同一套测试代码与 `pnpm test` 入口）；不引入
  `@playwright/test`；多浏览器矩阵待浏览器特异 bug 出现再加。

## 待执行：TS7 dts 兼容性重测

tsdown dts × TypeScript 7（tsgo）不兼容（tsgo 对任意入口均不生成 dts），
现钉 `typescript@6`。源码化已落地，重测 TS7 dts：兼容则升回 7。
注意 esm 格式 dts 产物名 `.d.mts` 与 `exports.types` 的对齐已由
publish_shell 的 dts hub 处理，升级时复验。

## 待执行：npm bundler 用户支持（按需触发）

`--target web` 为长期形态（已定案）。npm bundler（Vite/webpack）用户需自管
`.wasm` 落位（README 文档级说明）。待真实 npm bundler 用户需求出现，增量加
`--target bundler` 构建 + `exports.browser` 条件分发——纯加法、非破坏性。
定案随 worker 实现 change 落地后升格进 governance spec。
