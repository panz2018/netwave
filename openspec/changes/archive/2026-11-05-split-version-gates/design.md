# Design

## Context

动机见 proposal.md - Why。当前态：`scripts/versions/` 有两个平铺门面
（`check_versions.py` 约 150 行、`check_outdated.py` 约 210 行），底层活
（仓库根定位、目录跳过、文件发现、版本解析比较）各写一份且已漂移；
根 uv 工具工程与 `versions/` 域骨架已由 `retire-pin-registry` 落地，
本 change 在其上继续拆包。grilling 会话 13 条裁决为本文决策依据。

## Goals / Non-Goals

- Goals：共享逻辑单一来源；门面薄聚合；纯逻辑有永久单测；改名后
  一眼可懂；对外行为零变化。
- Non-Goals：见 proposal.md Non-goals；设计层面另排除——不引入
  `src/` 双层布局（对齐 `python/netwave/` 平铺惯例）、不引入新
  Python 工具（ruff 已有 lint+format，不加 pyright/mypy）、
  `lib` 不用 `core` 命名（避免与 Rust `core/` 串门）。

## Decisions

### 目录与模块划分（终表）

```text
scripts/versions/
  check_versions.py   # 门面一：选四律 + 汇总 ::error:: + 退出码
  check_outdated.py   # 门面二：跑四段 + 排版 + PROBES 常量
  lib/
    __init__.py
    version.py        # 版本解析/比较
    repository.py     # 仓库扫描 + 钉版提取
    rules.py          # 四律判定
    latest.py         # 联网探测（只被 outdated 消费）
scripts/tests/
  test_version.py  test_rules.py  test_repository.py
```

- 门面只在 `versions/` 根；库代码进 `lib/`；包名布局对齐
  `python/netwave/` 平铺惯例。
- 未来插槽（本 change 不建文件）：`lib/blocked.py`（blocked 核准后，
  两门面消费）、`lib/pairs.py`（pairs 触发后，versions 消费）、
  过期门禁化复用 `latest.py` + `blocked.py` 过滤结果。

### 函数命名终表

| 模块            | 函数                                                                                                                           | 来源                                             |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------ |
| `version.py`    | `parse_version`                                                                                                                | 归一 `parse_ver`+`_semver`，补齐三元组           |
| `version.py`    | `is_exact` / `is_major_only` / `is_outdated`                                                                                   | 原内联正则与比较                                 |
| `repository.py` | `ROOT` / `SKIP_DIRS` / `find_files` / `find_python_versions` / `find_ci_workflows` / `workspace_members` / `is_python_project` | 原 `discover`/`has_project` 等                   |
| `rules.py`      | `check_rust_version` / `check_python_projects` / `check_package_manager` / `check_ci_python_versions`                          | 原 `main()` 内联四段，各返回 `errors: list[str]` |
| `latest.py`     | `fetch_json` / `run_cmd` / `first_line` / `latest_version`                                                                     | 原 `_req`/`run` 与段 2 的 if/elif                |

- 命名原则（落 AGENTS.md，见「AGENTS.md 命名规则」）：完整单词、动词开头、禁自造缩写
  黑话（MSRV/pin/glue）；与被检字段同名者照抄字段名保可追溯
  （`check_package_manager` 查 `packageManager` 字段，不改叫
  node_version；`check_rust_version` 照抄 `rust-version`）。
- `PROBES` 留在门面：spec「过期体检命令」明文探针集为程序内常量。
- 对外输出字符串（`::error::`、`LAG`/`OK`、摘要行、
  `check:outdated done`）不改——改内部命名不动对外契约。

### 版本比较统一为补齐语义（行为修复）

旧 `parse_ver("1.85") -> (1, 85)` 与旧 `_semver("1.85") -> (1, 85, 0)`
判定相反（`(1,85) < (1,85,0)` 为真，会误报"rust-version 高于
rust-toolchain 钉版"）。
统一取补齐三元组。当前仓库两值恰好同格式故未爆雷，属潜伏 bug。

### SKIP_DIRS 统一为单一来源（行为修复）

outdated 局部 `skip` 比闸门 `SKIP_DIRS` 少 `target-wasm`/`dist`/
`coverage` 三项，统一到 `repository.SKIP_DIRS`。定性为修复而非纯搬家：
对齐"按发现覆盖"的既有意图（构建产物本就不是钉版载体）。实际输出
预计不变（那些目录无 uv.lock/.python-version）。账本新增 LL：同一
知识两份清单必漂移（同 LL-034 模式）。

### workflow 发现不强行统一

律 4 全仓扫 `*.yml` 找 `python-version:`（发现式，防矩阵写在他处逃逸）；
段 4 只扫 `.github/workflows/*.yml`（actions 只存在于 workflows）。
`repository.py` 提供 `find_ci_workflows()`（workflows 目录枚举）供段 4
用；律 4 继续 `find_files("*.yml", 含python-version)`。两者语义不同，
硬合削弱覆盖。`scripts/check_ci.py` 只读单文件 `ci.yml` 做 test:*
对账，与 `find_ci_workflows` 无重叠，不合并（grep 已核实：其仅
`ROOT/.github/workflows/ci.yml` 一处路径拼接）。

### 导入机制

门面保持 `uv run python scripts/versions/check_versions.py` 直跑——
`sys.path[0]` 为脚本目录，`from lib import ...` 天然可用，入口命令
形态不变。pytest 侧在根 `pyproject.toml` 加
`[tool.pytest.ini_options] pythonpath = ["scripts/versions"]`，使
`scripts/tests/` 能导入 `lib`。否决 `python -m versions.check_versions`：
需处理包初始化且改 package.json 入口，波及面大收益小。

### 单测与回归基线

- 永久单测只测纯逻辑（夹具数据）：`version.py` 全部分支（含
  `1.85` vs `1.85.0`、`v` 前缀、major-only）、`rules.py` 四律正反夹具
  （即 spec「换网自证」Scenario 的可回归化）、`repository.py` 的
  发现与跳过逻辑（tmp 目录夹具）。
- 联网输出一致性 = 一次性临时基线：拆前跑两门面存
  `/tmp/baseline_before.txt`，拆后跑存 `baseline_after.txt`，
  `diff` 为空即"只搬不改"成立；outdated 联网段允许时间性差异
  （两次跑间隔内上游发版），比对时忽略 latest 数值行、保留行结构。
  基线文件不入库，diff 结论写 PR 描述留痕。
- 接线：`uv run pytest scripts/tests` 追加进 `check:py`（ruff 之后）；
  CI lint job 在 `uv sync --locked` 后加同命令一步。
- 覆盖率：本次只 `--cov` 报数不卡线；阈值进 coverage_gate 为待触发项
  记 Plan（裁决 #5，用户点名写 Plan）。

### 退出码契约

versions 门面：0=全律通过、1=有违规（`::error::` 逐条 stderr）；
outdated：恒 0（informational，段失败降级 WARN 不中断）。写进
`scripts/versions/README.md` 模块地图。

### AGENTS.md 命名规则

「通用原则 · 简洁优先」下新增一行：

> 命名必须一眼能懂：函数/文件用完整单词、动词开头，禁自造缩写与
> 黑话；与被检字段/文件同名者照抄字段名保可追溯。

理由：约束 agent 日常行为归 AGENTS.md；无法机器判定，不进 spec。
出处：本 change（grilling 会话对 `semver`/`msrv`/`pin` 的逐条纠正）。

## Risks / Trade-offs

- [拆包时手滑改变行为] → 「单测与回归基线」的一次性基线 diff 为空 +
  四律夹具单测双保险。
- [pytest pythonpath 与 `python/` 工程 pytest 配置互相干扰] → 根工程
  与 `python/` 是独立 uv 工程，pytest 按就近配置解析；CI 两条命令路径
  不同（`scripts/tests` vs `python/`），互不收集。
- [outdated 基线受网络时间差影响误报] → 「单测与回归基线」的比对规则
  忽略 latest 数值、保留结构；WARN 行位置稳定可比。
- [改名后外部引用断裂] → 全仓 grep 旧符号名（`parse_ver`、`_semver`、
  `has_project`、`discover`）确认零残留；对外只有命令入口，不变。

## Migration Plan

顺序见 tasks.md。回滚 = `git revert` 本 change 提交（无数据迁移、
无锁文件变化；`uv.lock` 仅当 pytest 配置变更需要时刷新——实际 pytest
为既有 dev 依赖，预计 lock 不变）。

## Open Questions

（无——13 条裁决已在 grilling 会话全部拍板，frontier 为空。）
