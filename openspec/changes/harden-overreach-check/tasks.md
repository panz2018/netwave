# Tasks

## 1. 修订 LL-098 账本条目

- [ ] 1.1 改 `openspec/specs/lessons-learned/workflow.md` LL-098 规则③：检查时点
  由"提交前"改为"写总结前"，并写明触发条件"本轮发生过写操作才触发，只读问答轮
  免检"。验证：该条正文出现"写总结前"且含只读轮免检表述。
- [ ] 1.2 改同条复发检测行：点名范围具体化为"apply 态 = 本 change 的 `tasks.md`，
  对话态 = 人工该轮原话点名的文件"，删除不可追溯的"该轮点名范围"措辞。验证：
  检测行不再含"该轮点名范围"裸表述，且与 1.1 时点口径一致。
- [ ] 1.3 给同条补"不可门禁化原因"留痕：点名清单非机器可读输入、脚本无法独立
  判定范围外文件。验证：复发检测行含不可门禁化原因句（满足 lessons-learned spec
  「不可门禁化留痕」Scenario）。

## 2. 具体化 config.yaml apply review 步

- [ ] 2.1 改 `openspec/config.yaml` `operations.apply.guidance` 中"对照本 change
  工件审实现 diff"那条，补"diff 文件集逐文件对上 `tasks.md`，对不上即越权、
  停手还原"，不新增 guidance 条目。验证：该条措辞更新且 guidance 条目数不变。

## 3. AGENTS.md 加前后闸互见指针

- [ ] 3.1 给 `AGENTS.md`「动词复述」条加一句指针"收尾对账见 LL-098"，使前闸
  （动手前复述）与后闸（写总结前对账）互相可见。验证：该条含指向 LL-098 的指针，
  且未新增独立准则条目。

## 4. 收口与同步

- [ ] 4.1 跑 `pnpm check:md`（仓库根，退出码 0）。验证：命令退出码 0。
- [ ] 4.2 三轴 review：按 governance spec「元规则 review 三轴」（Standards/Spec/
  Lessons）对照本 change 工件（proposal/design，specs 已 skip_specs）审实现 diff，
  硬伤清零才准入 4.3。验证：三轴逐轴结论无打回项。
- [ ] 4.3 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检与
  升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍，含全局 CLI/直装工具的
  机器级升级；上游 bug/不兼容登记回退不阻塞；下限变更等人工发起）。消化后 MUST
  复跑 `pnpm check:outdated` 至退出码 0（SUMMARY 归零）才算本项完成。验证：
  复跑退出码 0。

## Workflow follow-up

- 归档本 change 时执行 Plan/ 瘦身：删除 `Plan/防越权机制-2026-11-14.md`（结论已
  吸收进 LL-098、config.yaml、AGENTS.md），删后跑 `pnpm check:md`。
- 本 change 归档时**一次性跳过** archive 态 health-check（人工本轮点名，规则本体
  在 `config.yaml` archive 段原地保留，下个 change 照常执行）。
