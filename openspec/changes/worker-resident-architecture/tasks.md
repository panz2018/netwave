# Tasks

本 change 为规划文档修订 + 工具兼容验证，无数值实现任务（red-first 与
cross-binding 对拍规则不适用；tsdown 验证不触碰计算路径）。

## 1. Plan 文档修订（typescript源码化规划.md）

- [x] 1.1 新增"worker 常驻架构（已定案）"章节：数据权威在
      常驻 worker 的 wasm 内、`upload` transfer 托管驻留、结果一律 transfer 传出不
      留副本、主线程无 wasm 实例、worker 常驻至页面关闭、worker 异常终止数据丢失
      为已接受行为（不引入 IndexedDB）、Worker 池未来再议（前置门槛=数据分片归属）
      → 验证：章节存在且与 design.md 决策一致
- [x] 1.2 同文档写入 API 面定案：计算与元数据一律异步进 worker、元数据搭结果
      便车回传从返回值同步读描述符、浏览器端 `_` 同步计算逃生口废止、node 端保留
      `_` 同步函数（私有面）→ 验证：文本覆盖三端语义且无"小数据不起 worker"残留
- [x] 1.3 "待拍板：wasm target 形态"节改写为"已定案：长期 web"，bundler
      形态标注"待真实 npm bundler 用户需求出现再增量添加（exports.browser 条件
      分发，纯加法）"→ 验证：全文 grep "待拍板" 无 wasm target 残留
- [x] 1.4 写入 standalone.js 形态定案（内部自起常驻 worker，Pages 零配置）与
      真浏览器测试线选型（vitest browser mode + playwright provider + 仅
      Chromium，
      不引入 `@playwright/test`）→ 验证：两处文本存在
- [x] 1.5 执行步骤节补记：主 spec 修订（governance 单点所有权/常驻 worker
      权威 + zero-copy-roundtrip 第 1/2/6 条）随 worker 实现 change 同步，本次
      不动主 spec → 验证：步骤文本存在

## 2. lessons-learned 账本登记

- [x] 2.1 `lessons-learned/typescript.md`：LL-001 保留原文并加"修订"标注
      （分流废止；浏览器 `_` 废止、node 保留）→ 验证：条目含修订标注且
      原文未删
- [x] 2.2 新增 LL 条目：主线程 wasm 实例退役（防旧壳模式回流）、同步元数据
      读取改异步（元数据搭结果便车）；`INDEX.md` 同步一行一条 → 验证：
      `python3 scripts/check_md.py` 账本门禁绿

## 3. tsdown × TypeScript 7 最小兼容验证

- [x] 3.1 `typescript/` 安装 tsdown 为 devDependency（`COREPACK_ENABLE_DOWNLOAD_PROMPT=0 pnpm add -D tsdown`，联网预计 1–2 分钟）→ 验证：`pnpm -C typescript exec tsdown --version` 成功
- [x] 3.2 对现有壳跑一次 tsdown 构建（entry=src 壳，napi/wasm glue 保持
      external，不启用 wasm 源码集成）→ 验证：构建退出码 0，产物清单齐全
- [x] 3.3 dts 产物与手写 `index.d.ts` 逐 export 对拍（diff 导出名与签名）→
      验证：结论三分记录进 Plan 文档（兼容 / dts 不兼容→钉 `typescript@6` 供 dts
      并记录 / 构建失败→记录 blocker 重评 Rslib 备选）
- [x] 3.4 验证结论回写 `Plan/typescript源码化规划.md` 步骤 2 备注；若失败则
      `pnpm remove tsdown` 回退 lock → 验证：Plan 含结论段，`pnpm check:md` 绿

## 4. 门禁收尾

- [x] 4.1 仓库根 `pnpm check:md` 全绿（markdownlint + prettier + check_md 含
      账本门禁）→ 验证：退出码 0
- [x] 4.2 仓库根 `pnpm check:ts` 全绿（biome + tsc --noEmit；验证若动了
      typescript/ 依赖不影响门禁）→ 验证：退出码 0
