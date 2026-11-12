# Tasks

本 change 零代码、零数值实现（纯流程 guidance + 能力 spec），铁律二
red/green 与 cross-binding 对拍不适用；验收以门禁命令与人工核对为准。

- [x] 1. 改 `openspec/config.yaml`：`operations.archive.guidance` 新增
      归档前全项目只读体检一条（五维清单、只读+当场实证、三级去重归属一处、
      上限与分级、硬伤卡归档、子代理降级、闸门已覆盖不报），只写规则不写
      出处
- [x] 2. 将本 change 的 `specs/archive-health-check/spec.md` delta 内容
      确认可原样并入主 spec（archive 时由 openspec 落盘），核对与 governance
      spec「元规则 review 三轴」、既有 archive"Plan/ 瘦身"条无措辞冲突
- [x] 3. 更新 `openspec/specs/README.md` 能力 spec 路由表，新增
      `archive-health-check` 行（何时读：归档前体检、存量审查）
- [x] 4. 验收：`openspec validate add-archive-health-check` 通过；
      `pnpm check:md` 退出码 0（含 SPECS ROUTER 一致性）；
      `python3 scripts/check_proposal.py` 通过

三态时效结论（apply guidance 留痕）：更新——无（既有 spec 经核对无需改，
governance 三轴与既有 archive 瘦身条无冲突）；新增——
`openspec/specs/archive-health-check/spec.md`（本 change sync 落地）；
退役——无。附带：修复存量断链
`archive/2026-11-11-add-bytes-io-encoding/proposal.md:9`（归档目录加深致
相对路径少一层，check:md BROKEN FILE 清零）。

- [x] 5. 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply
      末尾体检与升级预授权」消化所报 LAG：升级 + 全闸门 + 四端对拍（含全局
      CLI/直装工具的机器级升级），上游 bug/不兼容登记回退不阻塞；仅设计级
      适配、restrictions.json 破损、流程走不通才停下报告；下限变更（MSRV、
      engines.node、CI 底线格）等人工发起。消化完成后 MUST 复跑
      `pnpm check:outdated` 至退出码 0（SUMMARY 归零）才算本项完成

      消化记录：初报 2 LAG（node 26.13.0→26.13.1、openspec 1.17.0→2.0.0）；
      node 走 `nvm install --reinstall-packages-from` + `nvm alias default`，
      复跑暴露 npm 11.20.0→12.2.2，`npm i -g npm@12.2.2` 消化；openspec
      major 实测 `list`/`validate` 行为正常。本 change 纯文档/流程不碰绑定
      与数值，按「按触及面选验收闸门」跑 `pnpm check` 不跑 `check:cross`。
      终态：`pnpm check:outdated` SUMMARY 归零。
