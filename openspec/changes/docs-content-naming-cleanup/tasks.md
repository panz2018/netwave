# Tasks

## 1. 门禁先行（red：让机器生成完整存量台账）

- [ ] 1.1 `scripts/check_comments.py` 收窄为代码面：删除 `openspec/specs/**/*.md`
      扫描段与 governance/ledger 豁免；`STAGE_WORDS` 加 `阶段\s*[0-9]` 与
      `phase [0-9]`；新增开发文档指针词（`spec:` 后接空格、`LL-\d+`、
      `openspec/`、`Plan/`）扫 `.rs`/`.py`/`.ts` 注释。验证：
      `python3 scripts/check_comments.py`
      对现有 9 处代码指针与阶段词命中报红（red 证据留存于终端输出）
- [ ] 1.2 `scripts/check_md.py` 扩为文档面：新增考古词表扫描（`阶段\s*[0-9]`、
      英文 `stage [0-9]`/`phase[- ][0-9]`、由 `openspec/changes/`（含 archive）
      现存目录名动态生成的改动名），扫全部 Markdown（`openspec/specs/`、`Plan/`、
      `openspec/changes/archive/`、根与子 README），零豁免；新增行内代码归档路径
      存在性校验（`openspec/changes/archive/<name>/` MUST 现存）。验证：
      `python3 scripts/check_md.py` 大面积报红且命中数与 grep 台账一致
      （`grep -rn "阶段\s*[0-9]" --include="*.md" | wc -l`）

## 2. 代码面清理（green 之一：用户可见注释）

- [ ] 2.1 `core/src/frequency.rs`：删除 7 处 `spec:`/`LL-\d+` 注释引用，
      改写为自包含使用描述（如 "vocabulary single source" 直接写清含义）。
      验证：`grep -n "spec:\|LL-[0-9]" core/src/frequency.rs` 零命中；
      `cargo test -p netwave-core` 全绿（仅注释改动不影响行为）
- [ ] 2.2 `typescript/src/index.node.ts`、`typescript/src/types.ts`：删除
      `spec:` 引用改自包含描述。验证：`grep -rn "spec:\|LL-[0-9]" typescript/src/`
      零命中；`pnpm -C typescript test` 全绿

## 3. 活 spec 与账本清理（green 之二）

- [ ] 3.1 按本 change spec delta 把五份主 spec（api-contract/ci-matrix/
      frequency-unit/project-governance/zero-copy-roundtrip）正文「阶段 N」
      改写为内容命名、删 `总体计划`/`design.md` 待决指针改自包含表述、
      区间契约改内容锚点。验证：`grep -rn "阶段\s*[0-9]" openspec/specs/`
      零命中
- [ ] 3.2 governance spec 元规则按 delta 落地（REMOVED 旧条 + ADDED 两条），
      反例词改描述性表达。验证：`pnpm check:md` 对 governance 零命中
- [ ] 3.3 `lessons-learned/core.md:35` 活引用、`docs.md:55` 证据行改写为
      内容命名/转述。验证：`grep -rn "阶段\s*[0-9]" openspec/specs/lessons-learned/`
      零命中

## 4. Plan/ 清理与归档改名（green 之三）

- [ ] 4.1 `Plan/总体计划.md`：「分阶段路线图」标题改「路线图」、条目去数字
      改内容命名有序列表、「阶段模型铁则」改写、待办/待决清单的阶段引用改
      内容命名。验证：`grep -n "阶段\s*[0-9]\|分阶段" Plan/总体计划.md` 零命中
- [ ] 4.2 `Plan/功能覆盖规划.md`、`测试规划.md`、`频率类设计.md`、`README.md`：
      阶段引用与 `#分阶段路线图` 锚点同步改。验证：
      `grep -rn "阶段\s*[0-9]\|分阶段" Plan/` 零命中
- [ ] 4.3 归档目录改名：`git mv` 将
      `archive/2026-09-27-phase0-monorepo-scaffold` 改为
      `archive/2026-09-27-monorepo-scaffold`，全仓 grep 旧名逐处更新
      （活文档 + archive 内互引）。验证：
      `grep -rn "phase0-monorepo-scaffold" . --exclude-dir=.git` 零命中
- [ ] 4.4 `openspec/changes/archive/**` 的「阶段 N」逐处改写为内容命名
      （其余叙述不动）。验证：`grep -rn "阶段\s*[0-9]" openspec/changes/archive/`
      零命中

## 5. 全量验证与收尾

- [ ] 5.1 `pnpm check` 全绿（含 check:meta 代码面、check:md 文档面+链接锚点）。
      验证：退出码 0
- [ ] 5.2 全仓终验：阶段词 grep（`grep -rn "阶段\s*[0-9]"`，排除
      `.git`/`target`/`target-wasm`/`node_modules`）零命中；代码面开发指针 grep
      （`grep -rn "spec: \|LL-[0-9]" core/src python/src typescript/src`）
      零命中。验证：两条 grep 均零命中
- [ ] 5.3 按 openspec/config.yaml apply 指引做 Plan/ 瘦身：本 change 已覆盖
      `Plan/文档卫生清理.md` 全部条目，删除该文件；`pnpm check:md` 复跑绿。
      验证：文件不存在且 `pnpm check:md` 退出码 0
