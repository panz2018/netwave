# scripts/versions 包化计划（版本域搬家 + uv 工程 + 可测分层）

> 目标：把版本治理相关内容从 `scripts/` 平铺中收进 `scripts/versions/` 包，
> `scripts/` 建独立 uv 工程，库代码与门面分离、可单元测试。配对校验新功能
> （见[配对版本校验](配对版本校验.md)）直接落在新结构里，不往旧文件堆。
> 本文是已拍板思路的落地计划；scripts 其余闸门的治理仍见
> [scripts治理](scripts治理.md)（待议）。

## 目标结构

```text
scripts/
  pyproject.toml               # scripts 一个 uv 工程（dev 组：pytest、pytest-cov、ruff）
  uv.lock
  .python-version
  README.md                    # scripts 总说明（平铺闸门清单 + 指向 versions/）
  versions/                    # 版本域包：对外只有 README + 两个门面
    README.md                  # 本域功能、模块地图、跑法
    check_versions.py          # 门面一：离线对账闸门
    check_outdated.py          # 门面二：联网体检
    lib/                       # 库代码 + 数据（可单测，非门面全进这里）
      __init__.py
      registry.py              # 读登记表 + 条目结构校验
      registry.json            # 登记表（从 scripts/versions.json 搬入改名）
      semver.py                # 版本解析/比较（parse_ver 与 _semver 归一）
      values.py                # 从仓库文件读当前钉版值（含新补 reader）
      pairs.py                 # 配对约束校验（4 约束词，新代码）
      blocked.py               # 坏版本黑名单消费
      freshness.py             # 联网探测（GitHub/npm/endoflife）
  tests/                       # 单测（versions 域先行，其余闸门逐步补）
    test_registry.py
    test_semver.py
    test_values.py
    test_pairs.py
    test_blocked.py
  check_license.py …           # 其余 11 个 py 闸门 + 2 个 sh 暂维持平铺
```

分层规则（本域定死，后续域收编沿用）：

- **uv 工程文件放 `scripts/` 根**：整个 scripts 一套环境（一份 lock），
  其余平铺闸门将来 lint/测试共用，不按域各建工程。
- **门面只在 `versions/` 根**：`check_versions.py`（离线：
  registry+values+pairs+blocked 聚合）、`check_outdated.py`（联网：
  freshness+blocked 聚合）。门面只做组装输入 + 选检查集 + 汇总退出码。
- **库代码与数据进 `lib/`**：不与门面并列；`registry.json` 跟着读它的
  `registry.py` 走，`Path(__file__)` 定位，不依赖 cwd。
- **包名 `versions`、布局对齐 `python/netwave/` 平铺包惯例**（不引入
  `src/` 双层）；`lib` 不用 `core` 命名，避免与 Rust `core/` 串门。

## 跑法

- 离线闸门：`uv run --project scripts python -m versions.check_versions`
  （在 scripts 根以模块方式跑，`from versions.lib import …` 天然成立）
- 联网体检：`uv run --project scripts python -m versions.check_outdated`
- 单测：`uv run --project scripts pytest scripts/tests`（或 cd scripts 后
  `uv run pytest`）
- 根 `package.json` 门面命令改指新路径（见波及面），日常入口不变：
  `pnpm check:meta` / `pnpm check:outdated`。

## 实施步骤

1. **建 uv 工程**：`scripts/pyproject.toml`（dev 组 pytest、pytest-cov、
   ruff）+ `uv lock` + `.python-version`（与主工程同值）。
2. **搬家拆包**：登记表 `git mv` 到
   `scripts/versions/lib/registry.json`；`check_versions.py` 按职责拆进
   `lib/registry|semver|values|blocked.py`，`check_outdated.py` 拆进
   `lib/freshness|blocked.py`；两个门面重写为薄聚合层。拆分只搬逻辑
   不改行为——以旧脚本当前输出为回归基线。
3. **补 reader**：`values.py` 增加 `requires-python`、`engines.node`、
   devDependencies 具体版、`Cargo.lock` crate 解析版的读取（配对校验前置）。
4. **加 pairs**：`lib/pairs.py` 实现 4 约束词（`eq`/`eq_major`/`le`/`ge`）
   校验，registry 填 6 条已确定边（见[配对版本校验](配对版本校验.md)）；
   离线门面接入。
5. **单测**：纯逻辑模块（registry/semver/values/pairs/blocked）先写
   red/green 用例；`freshness.py` 网络段打桩测调用形状，异常分支逐条
   `# pragma: no cover` 标注豁免（禁整文件排除）。
6. **README**：`scripts/versions/README.md`（本域是什么、模块地图、
   三条跑法命令）；`scripts/README.md` 改为平铺闸门清单 + 指向
   `versions/README.md`。
7. **波及面一次改全**（见下表），跑 `pnpm check` 全绿 + 旧新输出对比一致。

## 波及面清单（漏一处即漂移）

| 位置                        | 改动                                                                                                                                                                          |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 根 `package.json`           | `check:meta` 内 `check_versions.py` 路径改 `versions/` 新入口并带 `--project scripts`；`check:outdated` 同理；`check:py` 的 ruff 作用域拆出 scripts、改走 `--project scripts` |
| `.github/workflows/ci.yml`  | lint job 加 `uv sync --project scripts`；ruff 步骤按新作用域拆两步                                                                                                            |
| registry 自登记             | 新增 `scripts-uv-lock`、`scripts-python` 两条（自家发现式扫描会扫到，不登记 `check:meta` 当场 FAIL——版本闸门管到自己头上）                                                    |
| registry 内自引路径         | `pin_location` 指向 `scripts/versions.json` 的条目改 `scripts/versions/lib/registry.json`                                                                                     |
| `scripts/README.md`         | 删版本域相关描述，指向 `versions/README.md`                                                                                                                                   |
| AGENTS.md / CONTRIBUTING.md | grep `scripts/versions.json`、`check_versions.py`、`check_outdated.py` 旧路径，逐处更新（LL-008）                                                                             |
| openspec spec               | dependency-upgrade spec 中 `scripts/versions.json` 路径表述与登记条目结构（`pairs`）补述——随本计划开 change 一并处理                                                          |
| `Plan/配对版本校验.md`      | registry 路径注释已指新位置                                                                                                                                                   |
| `Plan/scripts治理.md`       | 问题一在版本域范围内标记已拍板，其余闸门仍待议                                                                                                                                |

## 与待议问题的关系

- **scripts治理.md 问题一**（独立 uv 项目）：版本域已拍板要做（工程文件放
  scripts 根、覆盖全 scripts）；其余闸门是否收编进包结构仍待议。
- **问题二**（单测与覆盖率）：本计划落地 versions 域单测骨架；覆盖率是否进
  coverage_gate、pytest 挂哪条命令，实施时随本计划定（建议进 `check:meta`
  所在链路，命令名实施时定）。
- **问题三**（scripts 改名）：与本计划无关，维持 `scripts/`。
- **落地形态**：触及 workspace-layout / ci-matrix / dependency-upgrade 三个
  spec 与根命令面，属结构性升级，MUST 开 OpenSpec change（名称 propose 时
  再定）后实施。
