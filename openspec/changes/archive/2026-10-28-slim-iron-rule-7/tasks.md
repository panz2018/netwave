# Tasks

文档归位类改动（CONTRIBUTING「When to simplify」：docs 跳过 red/green，
编辑 + review），无代码/测试任务。

- [x] 1. 改主 spec `openspec/specs/project-governance/spec.md` 铁律七第二
      自然段：删机制解释与实测数字（"`--codecov` 走……恒差 6 行）"），
      保留按 crate 归属度量句与两条 MUST NOT，句末加"工具合并语义与实测
      证据只存账本 LL-057，本 spec 不重述"；三个既有 Scenario 逐字不动。
      验证：diff 仅命中该段；契约句与 Scenario 零改动。
- [x] 2. 主 spec 铁律七新增 Scenario「工具机制解释不入宪法」（按 delta
      文本逐字落地）。验证：Scenario 四要素齐（WHEN/THEN）。
- [x] 3. 全仓对账：grep `950/950`、`行合并器`、`OR 语义`、`恒差 6 行`
      确认全仓只剩 `openspec/specs/lessons-learned/core.md`（LL-057）与
      本 change 目录（归档后随 archive 留存）。验证：主 spec 零命中。
- [x] 4. 跑 `pnpm check:md`（退出码 0）与
      `openspec validate slim-iron-rule-7 --type change --strict`。验证：双绿。
- [x] 5. Plan/ 瘦身检查（config.yaml archive guidance）：删除
      `Plan/规范精简.md` 中 Q3/Q5 条目与已确认问题 1（结论已入本 change，
      Plan 不留存），跑 `pnpm check:md`。验证：Plan 该文件只剩 Q4/Q7。
