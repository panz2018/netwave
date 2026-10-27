# scripts/versions 包化计划（第二步：拆模块 + 单测 + pairs）

> 第一步（根 uv 工程 + 版本域三件套搬家）已由 OpenSpec change
> `move-versions-into-uv-project` 落地：根新增 `pyproject.toml`、`uv.lock`、
> `.python-version`，版本域三件套进 `scripts/versions/`（README、两门面、
> `lib/registry.json`）。结构与决策见该 change 的 design
> 与 `openspec/specs/`（sync 后）。本文只留**未执行**的第二步。
> scripts 其余闸门的治理仍见 [scripts治理](scripts治理.md)（待议）。

## 目标结构（在已落地骨架上继续）

```text
scripts/versions/
  README.md                  # 本域功能、跑法（已有；拆分后补模块地图）
  check_versions.py          # 门面一：离线对账闸门（重写为薄聚合层）
  check_outdated.py          # 门面二：联网体检（同上）
  lib/
    __init__.py
    registry.py              # 读登记表 + 条目结构校验
    registry.json            # 登记表（已在）
    semver.py                # 版本解析/比较（parse_ver 与 _semver 归一）
    values.py                # 从仓库文件读当前钉版值（含新补 reader）
    pairs.py                 # 配对约束校验（4 约束词，新代码）
    blocked.py               # 坏版本黑名单消费
    freshness.py             # 联网探测（GitHub/npm/endoflife）
scripts/tests/
  test_registry.py  test_semver.py  test_values.py  test_pairs.py  test_blocked.py
```

分层规则（本域定死，后续域收编沿用）：

- **门面只在 `versions/` 根**：`check_versions.py`（离线：
  registry+values+pairs+blocked 聚合）、`check_outdated.py`（联网：
  freshness+blocked 聚合）。门面只做组装输入 + 选检查集 + 汇总退出码。
- **库代码与数据进 `lib/`**：不与门面并列；`registry.json` 跟着读它的
  `registry.py` 走，`Path(__file__)` 定位，不依赖 cwd。
- **包名 `versions`、布局对齐 `python/netwave/` 平铺包惯例**（不引入
  `src/` 双层）；`lib` 不用 `core` 命名，避免与 Rust `core/` 串门。
- 环境：仓库根 uv 工具工程（第一步已建），不另建 scripts 工程。

## 跑法（拆分后）

- 离线闸门：`uv run python scripts/versions/check_versions.py`（门面直跑；
  若改 `python -m` 需先定 `__init__.py` 导入机制，届时一并定）
- 联网体检：`uv run python scripts/versions/check_outdated.py`
- 单测：`uv run pytest scripts/tests`
- 日常入口不变：`pnpm check:meta` / `pnpm check:outdated`（根
  `package.json` 已指新路径；拆分若改入口再同步）

## 实施步骤

1. **搬家拆包**：`check_versions.py` 按职责拆进
   `lib/registry|semver|values|blocked.py`，`check_outdated.py` 拆进
   `lib/freshness|blocked.py`；两个门面重写为薄聚合层。拆分只搬逻辑
   不改行为——以当前脚本输出为回归基线。
2. **补 reader**：`values.py` 增加 `requires-python`、`engines.node`、
   devDependencies 具体版、`Cargo.lock` crate 解析版的读取（配对校验前置）。
3. **加 pairs**：`lib/pairs.py` 实现 4 约束词（`eq`/`eq_major`/`le`/`ge`）
   校验，registry 填 6 条已确定边（见[配对版本校验](配对版本校验.md)）；
   离线门面接入。
4. **单测**：纯逻辑模块（registry/semver/values/pairs/blocked）先写
   red/green 用例；`freshness.py` 网络段打桩测调用形状，异常分支逐条
   `# pragma: no cover` 标注豁免（禁整文件排除）。
5. **README**：`scripts/versions/README.md` 补模块地图。
6. **波及面一次改全**（见下表），跑 `pnpm check` 全绿 + 旧新输出对比一致。

## 波及面清单（漏一处即漂移）

| 位置                         | 改动                                                                                           |
| ---------------------------- | ---------------------------------------------------------------------------------------------- |
| 根 `package.json`            | 若门面入口形态变化（`-m`），`check:meta`/`check:outdated` 同步；新增 pytest 命令挂接位置届时定 |
| `.github/workflows/ci.yml`   | lint job 已有 `uv sync --locked`；若新增单测步骤在此接入                                       |
| registry                     | 新增 `pairs` 表与 6 条边；条目结构校验随 pairs 扩展                                            |
| `scripts/versions/README.md` | 补模块地图                                                                                     |
| openspec spec                | dependency-upgrade spec 的登记条目结构（`pairs`）补述——随本步开 change 处理                    |

## 与待议问题的关系

- **scripts治理.md 问题二**（单测与覆盖率）：本步落地 versions 域单测骨架；
  覆盖率是否进 coverage_gate、pytest 挂哪条命令，实施时随本步定
  （建议进 `check:meta` 所在链路，命令名实施时定）。
- **问题三**（scripts 改名）：与本计划无关，维持 `scripts/`。
- **落地形态**：触及 dependency-upgrade spec 与根命令面，属结构性升级，
  MUST 开 OpenSpec change（名称 propose 时再定）后实施。
