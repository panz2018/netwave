# Tasks

## 1. harness 实证与 dump 拆分

- [ ] 1.1 按 `真harness` 裁决实证：最小骨架 playwright 脚本打开挂壳页面，anchor
      点击下载 + `download.saveAs` 落盘可用则定稿；失败切 `file.arrayBuffer()` 经
      evaluate 回传退路，结论写回本 change
- [ ] 1.2 按 `dump拆分` 裁决新建 `browser/scripts/dump.mjs`（真浏览器 harness，
      静态服务器挂 `browser/dist/` + `oracle/samples/`，File 上传 → 真壳
      `fromFile`/`toFile` → 落盘），按 `答卷` 裁决写 `oracle/tmp/browser/`；
      `browser/package.json` 加 `dump` 脚本
- [ ] 1.3 按 `dump拆分` 裁决把 `typescript/scripts/dump.mjs` 删 browser 段改名
      `typescript/scripts/dump.node.mjs`；`typescript/package.json` 的 `cross-dump`
      改 `dump:node`
- [ ] 1.4 验证：`pnpm -C browser build` 后两端各自跑 dump 产答卷，再跑
      `python3 oracle/compare_cross.py oracle/tmp` 阅卷绿（cross-binding 跨绑定对拍）

## 2. 消费方路径归位

- [ ] 2.1 按 `产物源头` 裁决改 `scripts/run/test_cross.sh`：browser 产物探针指
      `browser/dist/wasm/`（缺失提示 `pnpm -C browser build`），dump 拆两条命令
      （node + browser）
- [ ] 2.2 按 `产物源头` 裁决改 `scripts/check_verbs.py`（`BROWSER_DTS`/
      `WASM_GLUE_DTS`）与 `scripts/check_vocab_types.py` 的 browser dts 路径至
      `browser/dist/`；跑 `pnpm check:meta` 实证门禁绿
- [ ] 2.3 按 `merge_browser` 裁决确认 `typescript/scripts/merge_browser.mjs`
      与发布壳 exports 零改动（单包发布形态不变）
- [ ] 2.4 CI：`.github/workflows/ci.yml` node job 增
      `playwright install --only-shell chromium` 步；cross 步骤命令随 dump 拆分更新
- [ ] 2.5 `scripts/tests/` wiring 镜像测试随 test_cross.sh/package.json 变化同步
      断言；验证：`pnpm check:meta` 绿

## 3. oracle 端名改名

- [ ] 3.1 按 `端名` 裁决改 `oracle/compare_cross.py`：ENDS、容差分支键、print
      文案、扰动自检列表 `wasm`→`browser`；真技术名（`wasm32-*`/`wasm-pack`/
      `dist/wasm/`）不动
- [ ] 3.2 按 `端名` 裁决同步 `oracle/manifest.json` note 与 `oracle/README.md`
      端名措辞；容差键与数值不动
- [ ] 3.3 验证：`pnpm test:cross` 全绿且扰动自检对新端名 `browser` 注入定位生效

## 4. 文档与 Plan 同步

- [ ] 4.1 同步 `scripts/README.md`、`typescript/README.md`、`browser/README.md`
      的命令与路径事实；验证：`pnpm check:md` 绿
- [ ] 4.2 `Plan/绑定放置重构.md` §6 `单包发布` 待拍板项吸收删除、
      `Plan/测试规划.md` wasm dump harness 行吸收删除（锚点 `Plan/`）；
      删后 `pnpm check:md` 绿

## 5. 收尾闸门（按 config.yaml apply guidance 逐锚点打勾）

- [ ] 5.1 `pnpm test` 全绿（先于 review 排除实现断裂）
- [ ] 5.2 旧名清零：从 git diff 列消失旧标识符（`dump.mjs` 旧路径、`cross-dump`、
      oracle 端名 `wasm`），全仓 grep 确认活文件与描述散文零残留（锚点 `旧名清零`）
- [ ] 5.3 三态时效：扫 openspec/specs/ 全目录出更新/新增/退役结论留痕本文件
      （锚点 `三态时效`）
- [ ] 5.4 三轴 review：按 governance spec「元规则 review 三轴」对照本 change
      工件审实现 diff，逐文件对上 tasks.md，硬伤清零（锚点 `三轴`）
- [ ] 5.5 体检：对触碰文件全文做 apply 态只读体检（health-check spec，发现落
      Plan/ 等点名不阻塞）（锚点 `体检`）
- [ ] 5.5b `跳过归档体检`：本 change 归档（archive）态只读体检按已定裁决跳过
      （打勾时同行注明 跳过 + ISO 日期）；仅指 archive 态，apply 态体检见 5.5
      照常执行
- [ ] 5.6 迟到追加复查：proposal `## 已定裁决` 每关键词载体任务已打勾，未打勾即红
      （锚点 `迟到追加`）
- [ ] 5.7 delta specs 同步进主 spec（sync-specs），`openspec validate --strict`
      绿；按 `一个change` 裁决本 change 覆盖全部归位面，无遗留批次
- [ ] 5.8 最后一项：跑 `pnpm check:outdated` 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍），
      消化后复跑至退出码 0（锚点 `check:outdated`）
