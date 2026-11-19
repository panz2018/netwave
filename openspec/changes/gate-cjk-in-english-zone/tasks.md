# Tasks

## 1. red 先行：CJK 规则自测

- [ ] 1.1 `自测同轮`：在 `scripts/tests/test_check_comments.py` 补 CJK 规则
      自测用例——无标记中文行红（报错含命中字符与 `file:line`）、有效
      `形状豁免`（`「标题」(specs/<capability>/spec.md)` 且标题真实）绿、假路径
      或假标题引用红（"豁免引用无效"）、半截形状（缺路径或缺标题）不豁免仍红、
      `门禁白名单`（`scripts/check_*.py` 与 `scripts/tests/`）内中文不报、
      `中文区豁免`（`openspec/`、`Plan/`）不扫。
- [ ] 1.2 验证 red：`python3 -m pytest scripts/tests/test_check_comments.py`
      因 CJK 规则未实现而失败。

## 2. green：check_comments.py 实现 CJK 检查

- [ ] 2.1 `全行扫描`：CJK 检查对 `iter_scanned_files` 命中文件的全部行生效
      （独立于 `is_comment()` 过滤的既有循环），`表意文字集` 取
      `\u4e00-\u9fff`，全角标点不查；报错格式 `CJK '<char>' <path>:<line>`。
- [ ] 2.2 `形状豁免`：匹配 `「<标题>」(specs/<capability>/spec.md)` 形状，
      核验时补 `openspec/` 前缀读文件并确认标题真实存在，放行该行；形状不完整、
      路径不存在或标题不属实报"豁免引用无效"。
- [ ] 2.3 `门禁白名单`：`scripts/check_*.py` 与 `scripts/tests/` 下文件在
      CJK 检查中整文件跳过；`openspec/` 与 `Plan/` 走 `中文区豁免`（沿用既有
      豁免目录机制）。
- [ ] 2.4 模块 docstring 补 CJK 规则与两条豁免说明（英文，自描述门禁风格）。
- [ ] 2.5 验证 green：`python3 -m pytest scripts/tests/test_check_comments.py`
      全绿。

## 3. 存量修复

- [ ] 3.1 `存量改写`：`python/src/lib.rs` 注释与
      `typescript/test/wasm/worker.test.ts` 测试名改写纯英文。
- [ ] 3.2 `存量改写`：8 处中文 spec 标题引用补全
      `「标题」(specs/<capability>/spec.md)` 形状——
      `scripts/versions/check_outdated.py` 5 处、
      `scripts/versions/lib/repository.py` 2 处、
      `core/tests/touchstone_write.rs` 1 处。
- [ ] 3.3 验证：`pnpm check` 全绿（含 `check:meta` 新闸门与全仓存量）。

## 4. 收尾（apply guidance 锚点逐条）

- [ ] 4.1 `pnpm test` 全绿（全量测试含四端对拍，先于 review）。
- [ ] 4.2 `三轴` review：按 governance spec「元规则 review 三轴」对照本
      change 工件审实现 diff，diff 文件集逐文件对上 tasks.md，硬伤清零。
- [ ] 4.3 `体检`：被触碰文件全文只读体检（health-check apply 态），发现附
      文件+行号+证据落 `Plan/` 等点名，不阻塞。
- [ ] 4.4 `Plan/` 销账：删除 `Plan/覆盖率闸门加固-2026-11-15.md` 第 4 条
      （本 change 已完成项），删后跑 `pnpm check:md`。
- [ ] 4.5 `三态时效`：扫 `openspec/specs/` 全目录，对照本产出生成
      更新/新增/退役三态时效结论，留痕于本文件完成记录。
- [ ] 4.6 `迟到追加`：复查 proposal.md `## 已定裁决` 每个关键词的载体任务
      均已打勾，未打勾即红。
- [ ] 4.7 `check:outdated`：跑 `pnpm check:outdated` 并按 dependency-upgrade
      spec 消化所报 LAG，复跑至退出码 0。

## Workflow follow-up

- sync delta 入主 spec（project-governance 新增 Requirement）后归档本 change。
- 归档时跳过 archive 态 health-check 只读体检（`体检跳过` 一次性裁决，见
  proposal.md 已定裁决；archive guidance 默认项本次经人工点名豁免）。
