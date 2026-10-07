# Proposal

## Why

脚手架已归档（`monorepo-scaffold`——原名带路线图数字代号，已改名，追溯见
`git log`；`migrate-constitution-to-openspec`），
但 `Plan/` 五份规划仍大量保留**已被 openspec spec 吸收的定案正文**（数据布局理由、
仓库结构、版本底线、异步/Worker 边界契约）与**已放弃/已完成的历史内容**（GPU 评估
过程、旧库对比表、已销账待办），与"Plan/ 只放未执行任务、终态删除"的生命周期
（AGENTS.md）不符。同时 `总体计划.md` 中一批长期 API 面定案（三层契约、z0 双动词、
频率轴契约等）从未进入任何 spec，缺一个受 `openspec validate` 管辖的落点。

## What Changes

- **新增能力 spec `api-contract`**：把 `总体计划.md`「跨语言 API 面契约」中已定案、
  长期有效的部分（三层契约、类式 API 形态、`upload`/`release`、z0 双动词、频率轴
  f64 Hz、结构变更语义、worker 泛化分发）升格为受管辖的 spec；未定案条目留在
  Plan/ 待决清单。
- **`开发流程.md` 整体迁入根 `CONTRIBUTING.md`**（英文精简版：六步循环、何时简化、
  技能地图与工具链状态表），删除该文件；`AGENTS.md` 指针同步改指 CONTRIBUTING。
- **`总体计划.md` 瘦身**：删除已被 `workspace-layout` / `project-governance` /
  `zero-copy-roundtrip` spec 吸收的正文（语言选型对比、数据布局理由、仓库结构树、
  License/版本底线、GPU 评估全文、已销账待办），只保留项目定位一句话、分阶段
  路线图（测试基础设施至光学适配验证未执行部分）、待办/待核实与待决细节清单（仅未销项），其余改
  为 spec 指针。
- **`测试规划.md` 瘦身**：删除旧库方案对比表（历史）、精度标准表（已由铁律三 +
  manifest 承载）、与 `ci-matrix` spec 重复的 CI 集成表；保留各阶段测试交付、
  unit/property 用例清单、criterion 基线持久化方案（Touchstone 核心未执行）。
- **`功能覆盖规划.md` 瘦身**：rf-touchstone 处置定案压成一行（理由已在 spec/旧库
  README）；保留核心 crate 模块布局、延后清单、阶段映射（Touchstone 核心至光学适配验证未执行）。
- **`Plan/README.md` 更正**：文件表补漏掉的 `typescript源码化规划.md`，更新各文件
  状态描述。
- **`typescript源码化规划.md` 保留**：源码改写未执行，仍是在途计划；仅核对无过时
  表述。
- **`testdata/README.md` 指针更正**：其对 `Plan/测试规划.md` 比对规则的引用改指
  governance spec 铁律三（该表即将从测试规划删除）。

## Capabilities

### New Capabilities

- `api-contract`: 跨语言 API 面长期契约——三层职责划分、类式 API 形态、显式托管与
  内存回收、z0 双动词、频率轴单位契约、结构变更语义、worker 泛化分发。

### Modified Capabilities

（无——`project-governance` 铁律、`workspace-layout`、`ci-matrix`、
`zero-copy-roundtrip` 的 Requirement 均不变，本次只删除 Plan/ 中对它们的重复正文。）

## Impact

- `Plan/`：删除 `开发流程.md`；`总体计划.md`、`测试规划.md`、`功能覆盖规划.md`、
  `README.md` 大幅瘦身；`typescript源码化规划.md` 基本不动。
- 根 `CONTRIBUTING.md`：新增开发工作流章节（英文）。
- `AGENTS.md`、`testdata/README.md`：指针改写。
- `openspec/specs/api-contract/`：本变更归档时新建。
- 不触碰任何代码、CI、manifest 数值。

## Non-goals

- 不修改七条铁律与任何既有 spec 的 Requirement。
- 不执行 typescript 源码化（那是 `typescript源码化规划.md` 自己的任务）。
- 不删除整个 `Plan/` 目录——分阶段路线图与未销账待办仍是未执行计划，留待各阶段
  吸收后自然清空。
- 不改动 `testdata/manifest.json` 内容。
