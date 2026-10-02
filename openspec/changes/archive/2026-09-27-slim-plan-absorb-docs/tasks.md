# Tasks

纯文档变更：无新增数值逻辑，不涉及 red/green 数值测试（开发流程"改文档跳过
red/green"简化路径）；验收 = `pnpm check:md` + `openspec validate` 全绿 +
逐文件对照检查。

## 1. 升格 api-contract

- [x] 1.1 校对 delta spec（`specs/api-contract/spec.md`）与 `总体计划.md`
      「跨语言 API 面契约」原文语义一致，无自造定义
      → 验证：`openspec validate slim-plan-absorb-docs --strict` 通过

## 2. 开发流程迁入 CONTRIBUTING.md

- [x] 2.1 在根 `CONTRIBUTING.md` 新增 "Development workflow" 章节（英文）：
      六步循环（grill→spec→red→green→review→复盘）、何时简化表、技能地图与
      工具链状态表（版本按当前实测：OpenSpec 1.13.1 / pnpm 12.5.1 / uv 0.12.13 /
      wasm-pack 0.15.0 / rustc 1.98.1 / node v26.4.0）
      → 验证：章节存在，工具版本与 `--version` 实测一致
- [x] 2.2 删除 `Plan/开发流程.md`
      → 验证：文件不存在；全仓无残留指向它的链接（grep `开发流程`）

## 3. 总体计划.md 瘦身

- [x] 3.1 删除已被 spec 吸收的正文：语言选型对比表、数据布局理由（→铁律一）、
      GPU 评估全文（→一行结论）、仓库结构树与命名解耦表（→workspace-layout）、
      License/版本底线/CI 矩阵（→workspace-layout + ci-matrix）、已销账 `[x]` 待办
      → 验证：每处替换为一行结论 + spec 标题跳转链接
- [x] 3.2 「跨语言 API 面契约」整节替换为指向 `openspec/specs/api-contract/`
      的指针 + 仅保留未销账的待决细节清单（未打勾条目）
      → 验证：待决清单无 `[x]` 项
- [x] 3.3 保留并核对：项目定位、分阶段路线图（阶段 1–8）、未销账待办
      （抢注、faer 选型、待决清单销账）
      → 验证：`pnpm check:md` 通过

## 4. 测试规划.md 瘦身

- [x] 4.1 删除：旧库方案对比表（历史）、精度标准表（→铁律三 + manifest）、
      CI 集成表（→ci-matrix spec）
      → 验证：三表删除处各留一行指针
- [x] 4.2 保留：测试分层总览、unit/property 用例清单、golden/manifest 契约、
      cross-binding、criterion 基线持久化（阶段 2）、覆盖率标准、阶段映射
      → 验证：`pnpm check:md` 通过

## 5. 功能覆盖规划.md 瘦身

- [x] 5.1 rf-touchstone 处置节压成一段（决定 + 指针，不重述理由全文）；
      其余延后清单与模块布局表保留
      → 验证：`pnpm check:md` 通过

## 6. 指针与状态更正

- [x] 6.1 `AGENTS.md`：`Plan/开发流程.md` 相关引用改指 `CONTRIBUTING.md`
      → 验证：grep 无断链
- [x] 6.2 `testdata/README.md`：比对规则引用从 `Plan/测试规划.md` 改指
      governance spec 铁律三
      → 验证：链接锚点有效
- [x] 6.3 `Plan/README.md`：文件表补 `typescript源码化规划.md`，更新各文件状态
      → 验证：表与 `ls Plan/` 一致
- [x] 6.4 全仓 grep `Plan/开发流程`，清理所有残留引用（archive/ 下历史归档不改写）
      → 验证：grep 退出码非 0（无匹配）

## 7. 收尾门禁

- [x] 7.1 `pnpm check:md` 全绿
- [x] 7.2 `openspec validate slim-plan-absorb-docs --strict` 全绿
