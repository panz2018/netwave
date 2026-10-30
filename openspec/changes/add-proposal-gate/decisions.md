# Decisions: add-proposal-gate

grilling 轮次裁决台账（出处：本会话第 2–3 轮，人工确认「可以」）。

1. **节名**：新增节 `## Prior art`（英文，与 proposal 既有标题族同族）；
   不做清单沿用 `## Non-goals`。→ design.md 决策 1、spec Requirement
2. **实质内容判定**：Non-goals ≥1 非空行；Prior art ≥1 非空行且至少一行含
   URL / 仓库内文件路径 / 「无现成方案」（口径 c，内部先例与外部链接均合法，
   套话过不了）。→ design.md 决策 2、spec Scenario「无先例走合法出口」
3. **config.yaml 同步**：`rules.proposal` 同轮改两条（Non-goals 对齐 +
   Prior art 新增），措辞与脚本判定严格一致。→ design.md 决策 5、tasks 5
4. **挂载点**：根 `package.json` `check:meta`；CI 经 `pnpm check` 自动覆盖，
   ci.yml 不动。→ proposal Impact、tasks 4
5. **零豁免**：无 skip 标记、无白名单；「无现成方案」是合法出口非豁免。
   → design.md 决策 4、spec Scenario
6. **文档波及面**：`Plan/方案讨论纪律.md` 删「两层分治与工件门禁」节
   （结论被闸门承接，Plan 不留存）；`CONTRIBUTING.md` Quality gates 加一行。
   → proposal What Changes、tasks 6–7
7. **自举**：本 change 的 proposal 自带两节，闸门上线首日扫到自己即过——
   特性非 bug。→ design.md Risks、tasks 3
