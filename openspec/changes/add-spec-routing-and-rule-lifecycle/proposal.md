# Proposal

## Why

`openspec/specs/` 下 13 个能力 spec 没有任何常驻阅读入口：AGENTS.md
「文档阅读入口/文档地图」只路由到宪法、账本、子项目 README 与
CONTRIBUTING，能力 spec 只在"恰好做那个 change"时才被碰到，spec 里的
契约细节对 agent 长期不可见。同时账本只增不减：lessons-learned spec 只写
"文字规则 SHOULD 递减"，却没有退出判据与执行机制，73 条 LL 里约四成已被
spec/门禁/AGENTS.md 完整覆盖，成为第二套规则堆。路由缺失与退出机制缺失是
同一枚硬币的两面——先把"该读哪份 spec"集中成一处可门禁校验的路由，账本条目
才有安全退出的前提。

## What Changes

- 新建 `openspec/specs/README.md`：全部 spec 的唯一路由表（宪法按任务读哪段、
  账本先扫 INDEX、每个能力 spec 一行"何时读"）；新增/删除 spec 必须同步更新
- AGENTS.md「文档阅读入口/文档地图」两节收敛为一句硬护栏（动手前先读
  `openspec/specs/README.md`），路由细节从 AGENTS.md 移除
- 修订元规则「文档受众分层」：AI 必读区收敛为 AGENTS.md +
  `openspec/specs/README.md`，其余 spec 经 README 路由；内容分配清单的维护
  落点由 AGENTS.md 文档地图改为 specs/README.md
- governance spec 新增元规则「规则生命周期」：归层路由表（产品契约→铁律、
  文档流程→元规则、能力契约→能力 spec、坑/纠正→账本）、退役判据（被完整
  覆盖/门禁承载/契约废止；编号不复用、删除留去向）、分片阈值（单文件超千行
  或超四十条 Requirement 触发拆分评审）；governance 自身维持单 spec 双段
- lessons-learned spec 新增 Requirement「账本条目退役」：三类退出判据、
  覆盖度核对（spec 缺的细节先并入其 rationale 再删账本正文）、门禁两步走
  证明（先跑违规样例变红再删）、逐条人确认、去向映射留痕 change 工件、
  INDEX 同步且不留墓碑
- `scripts/check_md.py` 新增 SPECS ROUTER 规则：`openspec/specs/` 下每个
  能力目录必须在 README 有链接行、README 每行必须指向现存目录，双向不符即红
- `openspec/config.yaml` operations 段新增：apply/archive 时扫 specs/ 全目录，
  产出"更新/新增/退役"三态时效结论
- 账本首批退役：31 条 LL 正文删除（逐条证据与去向映射见 design.md），
  INDEX 同步；`Plan/账本退役审计.md` 全文吸收后整文件删除

## Capabilities

### New Capabilities

（无——路由与生命周期均为治理行为，落在既有 capability。）

### Modified Capabilities

- `project-governance`：修订元规则「文档受众分层」（必读区收敛为
  AGENTS.md + specs/README.md，清单维护落点改 README）；新增元规则
  「规则生命周期」（归层路由、退役判据、编号不复用、分片阈值、单 spec 双段）
- `lessons-learned`：新增 Requirement「账本条目退役」（三类判据、覆盖度核对、
  门禁两步走证明、逐条人确认、去向留痕、INDEX 同步）

## Impact

- 文档：`openspec/specs/README.md`（新建）、`AGENTS.md`（两节收敛为指针）、
  `openspec/config.yaml`（operations 增钩子）、`openspec/specs/lessons-learned/`
  （30 条正文删除 + INDEX 同步）、`Plan/账本退役审计.md`（删除）
- 工具链：`scripts/check_md.py`（SPECS ROUTER 规则，`pnpm check:md` 口径不变）
- 代码/API：零改动——本 change 不触碰产品代码、公开 API、数据布局与 CI 矩阵
- 冻结件：archive 不回溯；账本中被 spec 正文钦定为唯一正文的条目
  （LL-029/072 等）不退役，spec 指针不断链

## Non-goals

- 不拆分 governance spec、不做 governance 级 INDEX（维持单 spec 双段，
  拆分留待分片阈值触发时另议）
- 不落实暂缓的四项门禁（LL-025 v8 ignore 校验、LL-036 typecheck 进
  `pnpm check`、LL-018 golden 禁手改、LL-021 black_box lint）——留待之后
  逐条另起 change
- 不改任何产品代码、公开 API、CI 矩阵与 oracle 机制
- 不清空整个账本：42 条保留条目（行为纪律、跨机器实现细节、spec 钦定
  唯一正文、待落门禁口诀）不动

## Prior art

- 仓库内既有同型机制：`openspec/specs/lessons-learned/INDEX.md`——
  "一行一条 + 先扫索引再开分片"的路由模式，本 change 将其推广到全部
  capability spec（`openspec/specs/README.md`）
- 仓库内既有门禁先例：`scripts/check_md.py` 的 LEDGER SECTION /
  ARCHIVE PATH 规则（目录↔文档一致性双向核对），SPECS ROUTER 沿用同一
  脚本与同一命令，不新建脚本
- 外部：无现成方案——openspec CLI（`@fission-ai/openspec`）自带
  spec/changes 目录约定但无 spec 路由表与账本退役机制，本仓自建于
  governance/lessons-learned 两层元规则之上
