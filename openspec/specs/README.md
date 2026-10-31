# openspec specs 路由（AI 必读区第二入口）

本文件是 `openspec/specs/` 下全部 spec 的唯一路由表。`AGENTS.md` 的硬护栏
指向此处；动手前按本表定位该读哪份契约，禁止凭记忆猜规则。

## 宪法（硬约束唯一真相源）

[project-governance](project-governance/spec.md) 分两段按任务读：

- 改产品代码 / API / CI / 数据 → [铁律段](project-governance/spec.md#requirement-铁律一-数据布局是契约)
- 改文档 / 流程 / 法务 / 规矩本身 →
  [元规则段](project-governance/spec.md#requirement-元规则-优先级与单一真相源)

## 纠错账本

[lessons-learned](lessons-learned/spec.md)：动手前先扫
[INDEX.md](lessons-learned/INDEX.md)，命中再开对应 scope 分片
（[ci](lessons-learned/ci.md) / [core](lessons-learned/core.md) /
[python](lessons-learned/python.md) / [typescript](lessons-learned/typescript.md) /
[oracle](lessons-learned/oracle.md) / [docs](lessons-learned/docs.md) /
[workflow](lessons-learned/workflow.md)）；被人工纠正当轮登记，退役走
[账本条目退役](lessons-learned/spec.md#requirement-账本条目退役)。

## 能力 spec（何时读哪份）

| spec                                               | 何时读                                                                 |
| -------------------------------------------------- | ---------------------------------------------------------------------- |
| [api-contract](api-contract/spec.md)               | 设计/改动任一端公开 API 面、类形态、动词与释放入口、worker 分发命令表  |
| [ci-matrix](ci-matrix/spec.md)                     | 改 `.github/workflows/`、构建矩阵、lint/基准/覆盖率门槛与 job 编排     |
| [dependency-upgrade](dependency-upgrade/spec.md)   | 升级任何工具链或依赖、改版本钉死点、加体检脚本                         |
| [frequency-class](frequency-class/spec.md)         | 改 `Frequency` 频率轴功能面（构造、访问器、换算、显示串）              |
| [frequency-unit](frequency-unit/spec.md)           | 改频率/波长单位词汇表、倍率、单位暴露形态与未知单位错误                |
| [license-compliance](license-compliance/spec.md)   | 改许可文件、发布元数据、第三方声明、samples 登记、商标用法             |
| [memory-lifecycle](memory-lifecycle/spec.md)       | 改跨 realm 内存回收、`drop()`、finalizer、句柄所有权                   |
| [oracle-harness](oracle-harness/spec.md)           | 改 `oracle/` 阅卷、golden 生成、dump 布局、manifest 容差               |
| [touchstone-core](touchstone-core/spec.md)         | 改 Touchstone 解析/写出、选项行语义、端口列序、域×格式访问、文件名规则 |
| [workspace-layout](workspace-layout/spec.md)       | 改仓库目录结构、Cargo/pnpm workspace 组织、发布名与版本同步            |
| [zero-copy-roundtrip](zero-copy-roundtrip/spec.md) | 改零拷贝视图往返、worker 异步边界、元数据回传、transfer 语义           |

## 文档地图（内容分配清单，增删只改本节）

### AI 必读区

- 行为准则 → `AGENTS.md`（本文件由其硬护栏指向）
- spec 路由 + 本清单 → 本文件
- 坑 / 纠正 / 实现决策 → [lessons-learned](lessons-learned/INDEX.md) 账本（分片 + INDEX）
- 契约与硬约束 → [project-governance](project-governance/spec.md)（宪法）
- 工件规则与 Plan/ 生命周期 → `openspec/config.yaml`
- 本目录编译/测试命令 → 各子项目 README
- 门禁命令速查、目录 layout、本地参考镜像 → `CONTRIBUTING.md`

### 人只看区

- 项目是什么 → 根 README
- 待拍板事项 → AI 在对话中呈上的决策表 / 全景表

## 维护规则

新增或删除 `openspec/specs/` 下的能力目录，MUST 同一 change 内更新本表；
一致性由 `scripts/check_md.py` 的 SPECS ROUTER 规则门禁强制（`pnpm check:md`）。
本表只放路由，规则正文一律留在各 spec 内。
