# Tasks

## 1. harness 实证与 dump 拆分

- [x] 1.1 按 `真harness` 裁决实证：最小骨架 playwright 脚本验证"静态服务器挂
      dist/+samples/ + chromium headless + File 上传喂真壳 fromFile + 计算"通路可用
      （s[0] 回传正确）；取数定走壳 getter，不依赖未落地的 to_file/writeFile
- [x] 1.2 按 `dump拆分` 裁决新建 `browser/scripts/dump.mjs`（真浏览器 harness，
      静态服务器挂 `browser/dist/` + `oracle/samples/`，File 上传喂真壳 `fromFile` →
      壳 getter `s`/`z0`/`version` 取主数据经 evaluate 回传落盘），按 `答卷` 裁决写
      `oracle/tmp/browser/`；`browser/package.json` 加 `dump` 脚本
- [x] 1.3 按 `dump拆分` 裁决把 `typescript/scripts/dump.mjs` 删 browser 段改名
      `typescript/scripts/dump.node.mjs`；`typescript/package.json` 的 `cross-dump`
      改 `dump:node`
- [x] 1.4 验证：`pnpm -C browser build` 后两端各自跑 dump 产答卷，再跑
      `python3 oracle/compare_cross.py oracle/tmp` 阅卷绿（cross-binding 跨绑定对拍）

## 2. 消费方路径归位

- [x] 2.1 按 `产物源头` 裁决改 `scripts/run/test_cross.sh`：browser 产物探针指
      `browser/dist/wasm/`（缺失提示 `pnpm -C browser build`），dump 拆两条命令
      （node + browser）
- [x] 2.2 按 `产物源头` 裁决改 `scripts/check_verbs.py`（`BROWSER_DTS`/
      `WASM_GLUE_DTS`）与 `scripts/check_vocab_types.py` 的 browser dts 路径至
      `browser/dist/`；跑 `pnpm check:meta` 实证门禁绿
- [x] 2.3 按 `merge_browser` 裁决确认 `typescript/scripts/merge_browser.mjs`
      与发布壳 exports 零改动（单包发布形态不变）
- [x] 2.4 CI：`.github/workflows/ci.yml` node job 增
      `playwright install --only-shell chromium` 步；cross 步骤命令随 dump 拆分更新
- [x] 2.5 `scripts/tests/` wiring 镜像测试随 test_cross.sh/package.json 变化同步
      断言；验证：`pnpm check:meta` 绿

## 3. oracle 端名改名

- [x] 3.1 按 `端名` 裁决改 `oracle/compare_cross.py`：ENDS、容差分支键、print
      文案、扰动自检列表 `wasm`→`browser`；真技术名（`wasm32-*`/`wasm-pack`/
      `dist/wasm/`）不动
- [x] 3.2 按 `端名` 裁决同步 `oracle/manifest.json` note 与 `oracle/README.md`
      端名措辞；容差键与数值不动
- [x] 3.3 验证：`pnpm test:cross` 全绿且扰动自检对新端名 `browser` 注入定位生效

## 4. 文档与 Plan 同步

- [x] 4.1 同步 `scripts/README.md`、`typescript/README.md`、`browser/README.md`
      的命令与路径事实；验证：`pnpm check:md` 绿
- [x] 4.2 `Plan/绑定放置重构.md` §6 `单包发布` 待拍板项吸收删除、
      `Plan/测试规划.md` wasm dump harness 行吸收删除（锚点 `Plan/`）；
      删后 `pnpm check:md` 绿

## 5. 收尾闸门（按 config.yaml apply guidance 逐锚点打勾）

- [x] 5.1 `pnpm test` 全绿（先于 review 排除实现断裂）
- [x] 5.2 旧名清零：从 git diff 列消失旧标识符（`dump.mjs` 旧路径、`cross-dump`、
      oracle 端名 `wasm`），全仓 grep 确认活文件与描述散文零残留（锚点 `旧名清零`）。
      核对：`dump.mjs`/`cross-dump` 仅余于本 change 工件（描述本次移动）；oracle
      `"wasm"` 端名活文件零残留；剩余 `wasm` 均真技术名（wasm 产物/memory.grow/
      dist/wasm）或 lessons-learned 账本（不动）
- [x] 5.3 三态时效：扫 openspec/specs/ 全目录出更新/新增/退役结论留痕本文件
      （锚点 `三态时效`）。更新：ci-matrix、oracle-harness、zero-copy-roundtrip、
      workspace-layout（四件已 sync）；新增：无；退役：无
- [x] 5.4 三轴 review：按 governance spec「元规则 review 三轴」对照本 change
      工件审实现 diff，逐文件对上 tasks.md，硬伤清零（锚点 `三轴`）。Standards：
      新脚本注释只写当前契约无考古；Spec：四 delta 已 sync、validate strict 绿；
      Lessons：命中 extract-browser-test-chain 归位判据，无新账本
- [x] 5.5 体检：对触碰文件全文做 apply 态只读体检（health-check spec，发现落
      Plan/ 等点名不阻塞）（锚点 `体检`）。已查：新脚本与改动文件无考古叙述、
      无死引用，无适用发现
- [x] 5.5b `跳过归档体检`：本 change 归档（archive）态只读体检按已定裁决跳过
      （跳过 2026-11-26）；仅指 archive 态，apply 态体检见 5.5 照常执行
- [x] 5.6 迟到追加复查：proposal `## 已定裁决` 每关键词载体任务已打勾，未打勾即红
      （锚点 `迟到追加`）。逐词核对：单包发布/产物源头/dump拆分/真harness/端名/
      答卷/merge_browser/一个change/跳过归档体检 载体行均已打勾
- [x] 5.7 delta specs 同步进主 spec（sync-specs），`openspec validate --strict`
      绿；按 `一个change` 裁决本 change 覆盖全部归位面，无遗留批次
- [x] 5.8 最后一项：跑 `pnpm check:outdated` 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍），
      消化后复跑至退出码 0（锚点 `check:outdated`）。消化：vitest/@vitest/* 5.1.1→5.1.2、
      @types/node 26.6.7→26.6.10（patch）；browser-playwright 精确 pin 对齐为 ^5.1.2；
      复跑 0 LAG，`pnpm test`（含四端对拍）绿
