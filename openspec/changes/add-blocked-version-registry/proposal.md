# Proposal

## Why

已知坏版本目前只存在于人脑与 lessons-learned 散文里：`check:outdated` 不知道哪个
版本带 bug，照样催升已知坏版本；离线对账闸门也不拦"当前钉版恰好是坏版本"。
bug 知识与检查脚本之间没有机器可读的连接。本 change 把坏版本黑名单并入版本
登记表（单一真相源），让体检报告自动跳过坏版本、闸门当场拦住踩坑；同时把登记表
改名——它早已不止管"钉"（还管配对、machine 钉、发现规则），`version_pins` 这个
名字名不副实。

## What Changes

- **BREAKING**（仓库内部路径）：`scripts/version_pins.json` → `scripts/versions.json`，
  `scripts/check_version_pins.py` → `scripts/check_versions.py`（对称改名；JSON 内部
  键名 `pins`/`pin_location`/`categories` 不动；归档区是冻结历史不改写）。
- 登记表条目新增可选字段 `blocked`：`[{"version", "reason", "issue"?}]`，
  `version` 必须精确版本号（拒绝范围/通配写法），`reason` 必填、`issue` 可选。
  除 `ci-actions` 外全部条目可挂（`ci-actions` 一条扛全部 action，挂上去分不清
  是哪个 action 坏，本期不支持并在 spec 注明理由）。
- `check_outdated.py` 首次接登记表：可枚举版本列表的段（全局 CLI、GitHub 直装
  工具、cargo 子命令、CI actions 的 semver tag、python 运行时 pin）过滤 blocked，
  latest 命中即改报 target = 次新可用版；全部候选被堵报 `no known good target`
  并保持 LAG；lockfile 三段原样输出不碰。脚本内维护探测名↔条目名映射表。
- `check_versions.py`（离线闸门）新增：`blocked` 结构合法性检查；仓库内可读钉版值
  （文件值、`discovered:` 成员值、CI python 矩阵格）命中 blocked 即 FAIL——
  当前钉版不许停在已知坏版本上。`machine:` 条目的黑名单由体检探测已装版本消费，
  闸门跳过（闸门只读仓库文件、不跑探测命令，保证 CI 可复现）。
- 黑名单语义 = **现行禁令**，不是历史档案：版本自身 bug 的禁令永久有效（发布版
  不可变，不会自愈）；配对不兼容的禁令随对方版本变化而删除，删除时把兼容性知识
  挪进配对条目 `verified`。升级到修复版不需要删条目放行。
- 治理边界调整：版本级 bug 的证据（version + reason + issue）随登记表条目入库，
  lessons-learned 不再收版本级 bug，只留非版本性的坑（工具行为变化、流程坑等）。
- `Plan/测试规划.md`：问题二整节删除（结论进 spec）；待议节改为两问按内容命名
  （"过期检查门禁化"、"配对版本校验"），机器人不得提议 blocked 版本作为
  门禁化的安全阀要求并入前者备查。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `dependency-upgrade`：新增"坏版本黑名单"Requirement（条目结构、两类禁令生命周期、
  双层消费、全堵兜底）；「钉死点登记表唯一真相源」「双向对账闸门」「过期体检命令」
  「最新稳定版优先」「经验回写」随改名与黑名单更新措辞。
- `ci-matrix`：登记表文件路径引用更新（`scripts/versions.json`）。

## Impact

- 工具：`scripts/versions.json`、`scripts/check_versions.py`（改名）、
  `scripts/check_outdated.py`（首次读登记表 + blocked 过滤；仍纯标准库，无新依赖）。
- 接线：根 `package.json` `check:meta` 指向 `check_versions.py`；CI 命令序列不变。
- 文档：`AGENTS.md`（钉死点登记表指针）、`CONTRIBUTING.md`（freshness 节路径）、
  `openspec/specs/dependency-upgrade/spec.md`、`openspec/specs/ci-matrix/spec.md`
  （随归档 sync）、`Plan/测试规划.md`（问题二收口）。
- 活跃 change：`openspec/changes/upgrade-python-3-15/`（proposal/tasks 引用旧路径，
  同步改）。
- 不碰 core 数值代码、API、容差 manifest；属 governance 类变更。

## Non-goals

- 不做过期检查 CI 门禁、定时机器人（待议问题，留
  [测试规划·待议](../../../Plan/测试规划.md)）；机器人"不得提议 blocked 版本"
  仅作备查要求写入规划，本 change 不实现任何自动化。
- 不做 `paired_with` 版本相容校验与 `constraint` 字段（待议问题，另 change）。
- 不改 lockfile 段的黑名单行为（过滤 lockfile = 重造 resolver；lockfile 内坏版本
  走生态机制：pnpm overrides、cargo `[T-001]` advisory、uv exclusion）。
- 不改登记表内部键名（`pins`/`pin_location`/`categories` 语义仍准确，最小 diff）。
- 不做 `verified` × `blocked` 同版本矛盾机器检查（`verified` 是自由文本，硬抠
  版本号 brittle；靠 review 兜底）。
- 不改 `openspec/changes/archive/` 内任何文件（冻结历史，旧路径引用保留原样）。
- 不拆 `ci-actions` 为逐 action 条目（等于把刚删掉的 watch 清单请回来）。
