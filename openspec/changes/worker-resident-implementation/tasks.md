# Tasks

## 1. 前置小项（独立，先行摘除）

- [x] 1.1 TS7 dts 兼容性重测：`pnpm -C typescript add -D typescript@7` →
      `pnpm build:shells` + `pnpm typecheck`，验证 dts 产物生成且 `.d.mts` 与
      `exports.types` 对齐（publish_shell dts hub 复验）。兼容则保留 7 不留尾巴；
      不兼容则回退钉 `typescript@6`，把"待 tsgo 支持 dts 后重测"写入
      `Plan/总体计划.md`「待办/待核实」并在账本 ci 分片登记 + INDEX 同步
- [x] 1.2 语言约束提级：AGENTS.md「通用原则」顶部新增两条——①对话必须用
      用户提问所用的语言回答（镜像用户语言，不得凭模型偏好选语言）；②文档
      按目录分语言：仅 `openspec/` 与 `Plan/` 用中文，其余一切（docs、代码
      注释、README 等）用英文；账本 docs 分片新增对应 LL 条目（四要素齐全）+ INDEX 同步；验证：`pnpm check:md` 退出码 0

## 2. 契约类型与失败测试（red 先于 green）

- [x] 2.1 `types.ts` 扩公开契约：`Handle`、`upload`/`release` 签名、结果
      `NetwaveBuffer` 增加 `shape`/`frequency` 元数据字段、消息协议类型更新；
      验证：`pnpm typecheck` 通过（此时新实现未动，浏览器壳测试应为 red）
- [x] 2.2 先写失败测试：node 模拟常驻 worker 套件断言 upload 后原 buffer
      detached、release 后句柄调用 reject、结果 buffer transfer 回传、元数据随
      结果同消息回传（消息计数断言）；验证：新测试全部 red（实现未动）
- [x] 2.3 浏览器端 `_` 废止测试：断言浏览器入口模块不导出任何 `_` 前缀同步
      计算函数（exports 名单测）；验证：测试 red（现壳仍导出 `_`）

## 3. worker 常驻实现（green）

- [x] 3.1 重写 `worker.ts`：worker 内直接 init wasm glue，维护
      `handle -> Network` 表，cmd 表显式静态（upload/release/现有动词），结果
      buffer 拷新 ArrayBuffer 后 transfer，元数据搭结果便车；验证：2.2 测试转绿
- [x] 3.2 重写 `index.browser.ts`：删除全部 wasm import 与 `_` 同步导出，
      改为懒起唯一常驻 worker + 泛化消息收发 + 从返回值重建视图；验证：2.2/2.3
      测试转绿，`pnpm typecheck` 通过
- [x] 3.3 `dist/standalone.js` 以 `standalone: "src/index.browser.ts"` 编译产
      出（公开子路径 `./standalone` 不变），`<script type="module">` / Pages 零
      配置不变；验证：browser 壳冒烟测试（upload→readElement→release，单例
      worker 断言）通过
- [x] 3.4 教学式 docs 补齐：新增公开 API（upload/release/结果类型）JSDoc
      达到宪法元规则教学式标准（自包含、说明所有权与 transfer 语义）；验证：
      code-review Standards 轴逐条过
- [x] 3.5 worker 全局单例：壳内 `getWorker()` 懒建 + `globalThis` 注册表
      （已存在即返回，不存在才 `new Worker(...)`），跨模块副本强制单例；
      README 声明"同页面只应加载一份库"；验证：浏览器套件多次 import +
      多句柄后存活 worker 数仍为一（铁律八 Scenario "多实例共用单一 worker"）

## 4. 真浏览器测试线

- [x] 4.1 加 vitest browser mode + playwright provider（仅 Chromium、
      headless），新增 `vitest.browser.config.ts` 并入 `pnpm test` 聚合入口；
      不引入 `@playwright/test`；首次浏览器二进制联网下载前预告耗时；验证：
      `pnpm test` 含浏览器套件且全绿
- [x] 4.2 浏览器特异断言落地：主线程 `globalThis` 无 wasm 实例（LL-030
      复发检测）、worker 消息计数（元数据便车无额外往返）、浏览器无 `_` 导出；
      验证：三条断言在真浏览器内绿
- [x] 4.3 覆盖率闸门：浏览器套件 v8 覆盖率并入 100% 硬闸门（铁律七），
      结构性不可达路径逐条 `/* v8 ignore */` + 理由；验证：浏览器配置下
      `pnpm test:wasm --coverage` lines/branches 100

## 5. 跨端对拍与回归

- [x] 5.1 cross-binding 对拍：node 模拟 worker 路径与原生 core 同输入对拍，
      原生逐 bit、wasm 用 manifest `core_tol` 相对容差；验证：
      `pnpm check:cross`（或 `node typescript/scripts/dump.mjs` +
      `scripts/cross_compare.py`）通过
- [x] 5.2 全量回归：`pnpm -C typescript test`（native + wasm + browser）、
      `pnpm check`（全语言闸门）退出码 0；验证：CI 同命令本地全绿

## 6. spec 同步与文档收尾

- [x] 6.1 归档时主 spec 同步：governance spec 含"常驻 worker 数据权威与单点
      所有权"Requirement，zero-copy-roundtrip spec 按 delta 改写（分流废止、
      浏览器 `_` 废止、元数据搭便车）；验证：`openspec validate` 绿
- [x] 6.2 `Plan/typescript源码化规划.md` 整删（任务全部落地），
      `Plan/总体计划.md`「待办/待核实」+「待决细节清单」接收未来项（多 worker
      分桶[门槛=数据分片归属+实测需求]、npm bundler 支持[按需触发]、TS7 dts
      重测[仅 1.1 不兼容时]）；验证：`pnpm check:md` 退出码 0，Plan/ 无本
      change 已定案残留文字
