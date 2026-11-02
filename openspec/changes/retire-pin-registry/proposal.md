# Proposal

## Why

钉死点登记表（`scripts/versions/lib/registry.json`，31 条 pin）经源码核实
已名存实亡：离线闸门 `check_versions.py` 的判定规则（MSRV、packageManager、
`.python-version` ∈ CI 矩阵）全部硬编码于程序、直读仓库文件，一条 pin 数据
都未被消费；`blocked` 与 `pairs` 两个真约束机制 0 条数据，登记表唯一承载的
是"没人读的清单"。同一知识存三处（spec 散文、程序硬编码、JSON 清单），
清单那份既重复又漂移（空类 `oracle-env`、类名与条目名同名的 `ci-actions`），
是纯复杂度。人工已裁决：登记表退役，规则驱动上位。

## What Changes

- **BREAKING** 删除 `scripts/versions/lib/registry.json`（pins + categories
  整体退役）；"版本钉在哪"的唯一真相源改为**钉版文件本身**
  （`rust-toolchain.toml`、`.python-version`、`ci.yml`、`package.json` 等），
  散文与 spec 以路径指针引用。
- **BREAKING** spec `dependency-upgrade` 三条 Requirement 退役并由
  「规则驱动一致性闸门」取代：不再要求"每个钉版点必须登记"，改为闸门
  按四条结构性规则扫描仓库 manifest（成员 `rust-version`、
  `pyproject.toml` → `requires-python` + `.python-version`、
  `packageManager` 精确一致、`.python-version` ∈ CI python 矩阵）。
- 坏版本处置改为触发式条款：机制当前不实现；真遇坏版本时降到相邻较低
  稳定版（原则式，不写死级差），当轮新建 `Plan/` 计划文件写明原因与细节，
  并强制开 change 实现 blocked 机制（数据文件 + 闸门消费）。
- `check_versions.py` 删除登记表相关检查与死代码（check #1/#1b/#2/#6、
  `DISCOVERED_RULES`、`current_values`、`locations`、`REGISTRY`、
  `REQUIRED_FIELDS`），保留 check #3/#4/#5 并升级为规则驱动闸门主体。
- `check_outdated.py` 删除 blocked 消费链（`load_blocked`、`blocked_target`、
  `PROBE_TO_ENTRY`、`REGISTRY`、`BlockedMap`），退回纯发现式体检；
  全局 CLI 探针集保留为程序常量（加探针改一处）。
- 指针同步：`AGENTS.md`、`CONTRIBUTING.md`、`openspec/specs/README.md`
  路由摘要、`ci-matrix/spec.md`、`scripts/README.md`、
  `scripts/versions/README.md`（整篇重写为新使命）。
- `Plan/软件升级.md` 收尾：删除已吸收章节（登记表 schema 重构、配对校验
  已定部分、旧拆包），保留待议块（闸门拆分+测试接线、pairs JSON 化、
  过期门禁化、scripts 治理三问、py3.15）。

## Capabilities

### New Capabilities

（无——本 change 不引入新能力域。）

### Modified Capabilities

- `dependency-upgrade`：「登记原则」「钉死点登记表唯一真相源」「双向对账
  闸门」「坏版本黑名单」四条 Requirement 退役/改写；新增「规则驱动一致性
  闸门」与「坏版本降级与 blocked 触发式实施」；「过期体检命令」「选线
  原则」「经验回写」中依赖登记表的措辞改为指向钉版文件与规则闸门。
- `ci-matrix`：矩阵数字来源从"登记表"改为"钉版文件与规则闸门"
  （`:51-52`、`:63-64`、`:70` 三处措辞）。

## Impact

- 代码：`scripts/versions/check_versions.py`（约删 150 行）、
  `scripts/versions/check_outdated.py`（约删 40 行）、删
  `scripts/versions/lib/registry.json`。
- 契约：`openspec/specs/dependency-upgrade/spec.md`、
  `openspec/specs/ci-matrix/spec.md` 随本 change delta 更新。
- 文档指针：`AGENTS.md:104`、`CONTRIBUTING.md:79/89/91`、
  `openspec/specs/README.md`、`scripts/README.md:19`、
  `scripts/versions/README.md`。
- 计划：`Plan/软件升级.md` 收尾瘦身；`Plan/测试规划.md` 删
  `:295`（oracle 加 registry pin 条目）保留 oracle uv/python 环境计划。
- 闸门接线不变：`pnpm check:meta` / `pnpm check:outdated` 命令入口不动。
- 不涉及产品代码（Rust/Python/TS 包）、不涉及数据布局与跨端协议——
  铁律一/三/七/九不触碰；本 change 属治理工具链与契约变更。

## Non-goals

- 不实现 blocked / pairs 机制（各自独立触发、独立实施，禁止绑定同次
  change；触发时按 spec 新条款开 change）。
- 不做 `check_versions.py` / `check_outdated.py` 的模块拆分与
  `scripts/tests/` 测试接线（顺延，计划保留于 `Plan/软件升级.md`）。
- 不做 `check:outdated` 门禁化（cron 折中方案待议）。
- 不做 scripts/ 目录改名与治理三问、不做 Python 3.15 升级。
- 不新建 spec 文件（blocked/pairs 条款留在 `dependency-upgrade` 内）。

## Prior art

- 包管理器原生机制：pnpm `peers check`（实测退码 0/1/2，读 lockfile
  不联网）、`uv lock --locked`、`cargo tree -d`——"声明+校验"由生态
  工具承担，netwave 不需要自建清单。
- 仓库内先例：`openspec/specs/dependency-upgrade/spec.md`「体检按发现
  覆盖全部环境」已采用"按发现（非硬编码名单）"原则，本 change 把同一
  原则推广到对账侧；`openspec/specs/api-contract/spec.md:200` 确立
  "从未实现的入口从契约删除、不留空挂"先例。

## 专家增补

- 规则驱动四律的**正反回归夹具**：临时造缺 `rust-version` 的
  `Cargo.toml` 与缺 `.python-version` 的 `pyproject.toml` 目录，断言
  闸门 FAIL——换网（清单核对→规则扫描）必须当场证明新网兜得住，
  落点 `scripts/versions/check_versions.py` 的 red/green 手工验证
  （正式测试体系随顺延的 `scripts/tests/` 落地）。
- 波及面**全仓 grep 收口**：实施当轮对 `*.md` 与 `*.py` 全仓 grep
  `registry.json` 清零（archive 目录与本 change 工件除外），防 `AGENTS.md`、
  `CONTRIBUTING.md`、`scripts/README.md` 等入口残留旧事实（LL-034
  CI 构建不变式同款要求）。
