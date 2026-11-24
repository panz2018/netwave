# Tasks

## 1. 死引用清扫

- [ ] 1.1 `三处一起修`：本组三任务同场完成，不拆分（同一迁移遗留）。
- [ ] 1.2 `删指针留契约`：改 `browser/test/coverage-dump.ts` 头注释，删去
  「for the same reason as `test/wasm/coverage-dump.ts`」历史指针，只留当前契约
  （独立成模块、dump 臂只在插桩实例执行故不入 v8 分母）。
- [ ] 1.3 `e2e注释改实glob`：改 `browser/vitest.e2e.config.ts` 头注释，
  「test/wasm/** runs unmodified here」改为实际 include 口径
  （`test/unit/**` + `test/e2e/**`）。
- [ ] 1.4 `删孤儿文件`：删除 `typescript/test/vite-env.d.ts`（typescript 下
  无 `?raw` 使用者）。验证：`pnpm check`（含 tsc 类型门）绿。
- [ ] 1.5 `grep清零验证`：`grep -rn "test/wasm" --include='*.ts'` 排除
  `openspec/changes/archive/` 后活文件零命中。

## 2. 收尾

- [ ] 2.1 `新开微小change`：本 change（`fix-browser-test-chain-stale-refs`）
  承载全部结论，已定裁决逐条对上任务行。
- [ ] 2.2 `Plan体检文件整删`：删除 `Plan/体检发现-extract-browser-test-chain.md`
  （发现项全部吸收）。删后跑 `pnpm check:md`（锚点 `Plan/`）。
- [ ] 2.3 三态时效：扫 `openspec/specs/` 全目录，本 change 纯注释/删孤儿文件，
  无 spec 需改、无需新增、无可退役，结论留痕本行（锚点 `三态时效`）。
- [ ] 2.4 `pnpm test` 全绿（先于 review 排除实现断裂）。
- [ ] 2.5 三轴 review：按 governance spec「元规则 review 三轴」对照本 change
  工件审实现 diff，diff 文件集逐文件对上 tasks.md，硬伤清零才准入后续（锚点 `三轴`）。
- [ ] 2.6 体检：被触碰文件（`browser/test/coverage-dump.ts`、
  `browser/vitest.e2e.config.ts`）全文只读体检（health-check spec apply 态），
  发现落 Plan/ 等点名，不阻塞；全豁免记「已查，无适用文件」（锚点 `体检`）。
- [ ] 2.7 迟到追加：apply 中途若拍板新决定，当场追加进 proposal.md
  `## 已定裁决` 并补任务行；收尾复查各关键词载体任务已打勾（锚点 `迟到追加`）。
- [ ] 2.8 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检
  与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍，含全局 CLI/直装工具的
  机器级升级；登记回退不阻塞）；消化后复跑至退出码 0（锚点 `check:outdated`）。
