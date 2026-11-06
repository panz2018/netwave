# Proposal

## Why

`scripts/versions/` 两个门面（`check_versions.py` 离线四律闸门、
`check_outdated.py` 联网体检）目前各自内嵌同一批底层活——仓库根定位、
垃圾目录跳过、钉版文件发现、版本号解析比较——且已实际漂移：outdated 的
跳过目录比闸门少三项（`target-wasm`/`dist`/`coverage`），版本比较存在两套
语义不同的实现（`parse_ver` 不补齐三元组、`_semver` 补齐，`1.85` 对
`1.85.0` 判定结果相反）。闸门域即将继续加功能（blocked 消费、pairs 读表、
过期门禁化复用），不先分层收编，每加一个功能就多复制一份漂移源。人工已
在 grilling 会话逐条拍板拆分方案（13 条裁决），本 change 将其固化为工件。

## What Changes

- `scripts/versions/` 拆为薄门面 + `lib/` 共享层：新增
  `lib/version.py`（版本解析/比较）、`lib/repository.py`（仓库扫描与
  钉版提取）、`lib/rules.py`（四律判定）、`lib/latest.py`（联网探测）；
  两个门面重写为"组装输入 + 选检查集 + 汇总退出码"的薄聚合层。
- 函数/文件命名全部改为一眼可懂的完整名（`parse_version`、`find_files`、
  `find_python_versions`、`check_rust_version`、`check_ci_python_versions`、
  `fetch_json`、`run_cmd`、`latest_version` 等），禁自造缩写黑话。
- **行为修复**：`check_outdated.py` 的跳过目录集合统一为闸门的
  `SKIP_DIRS` 单一来源（补齐三项）；版本比较统一为补齐三元组语义。
- 新增 `scripts/tests/` 单测目录：纯逻辑模块（版本比较、四律判定）以
  夹具做永久单测并接进 `check:py` 与 CI lint job；联网输出的一致性由
  一次性临时基线（改前/改后输出 diff 为空）验证，基线文件不入库。
- 根 `pyproject.toml` 增加 pytest `pythonpath` 配置；根 `package.json`
  的 `check:py` 追加 `uv run pytest scripts/tests`；`ci.yml` lint job
  追加 scripts 单测步骤。
- `scripts/versions/README.md` 补模块地图与退出码契约（versions 门面
  0/1、outdated 恒 0）。
- 波及文档同步：`AGENTS.md` 新增"命名一眼懂"一行；`Plan/软件升级.md`
  更新目标结构图为终表并记入"scripts 覆盖率暂不进 coverage_gate"裁决。

不改变任何对外输出字符串（`::error::`、`LAG`/`OK`、摘要行）、四律判定
语义、`pnpm check:meta` / `pnpm check:outdated` 命令入口形态。

## Capabilities

### New Capabilities

（无——本 change 不引入新能力域。）

### Modified Capabilities

- `workspace-layout`：「根级 Python 工具环境」新增 scripts 单测接线契约
  （`scripts/tests/` 布局、pytest pythonpath、`check:py` 挂接），并新增
  「治理脚本分层」Requirement（门面/共享层/单测三层布局规则）。
- `ci-matrix`：新增「治理脚本单测进 CI」Requirement（lint job 在
  `uv sync --locked` 后运行 scripts 单测）。

`dependency-upgrade` 不出 delta：四律语义、体检四段、探针集常量等契约
措辞均不变，SKIP_DIRS 统一属实现修复（对齐"按发现覆盖"既有意图，
排除构建产物目录），留痕 design.md 与账本。

## Impact

- 代码：`scripts/versions/`（两门面重写 + `lib/` 四模块新增）、
  `scripts/tests/`（新增）。
- 配置：根 `pyproject.toml`（pytest pythonpath）、根 `package.json`
  （`check:py` 追加 pytest）、`.github/workflows/ci.yml`（lint job 加
  一步）。
- 文档：`scripts/versions/README.md`、`AGENTS.md`、`Plan/软件升级.md`、
  `openspec/specs/lessons-learned/`（新增 LL：两份清单必漂移的又一实例）。
- 铁律关联：铁律七（覆盖率门槛）——scripts 侧覆盖率本次只报数不进
  coverage_gate，作为待触发项记 Plan，不豁免任何既有覆盖率契约。
- 不受影响：四端产物、oracle 对拍、产品代码、`check:meta` 其余闸门。

## Non-goals

- 不实施 blocked 机制与 pairs JSON 化（spec「blocked 与 pairs 不绑定」
  条款，各自独立触发）。
- 不把 `check:outdated` 或其联网测试进 CI 门禁（过期检查门禁化是另一
  待拍板项 `add-freshness-schedule-gate`）。
- 不改四律判定语义、不改对外输出字符串、不改 `pnpm check:*` 入口名称。
- 不给 scripts 侧上覆盖率阈值门禁（先报数，阈值下一轮再议）。
- 不合并 `scripts/check_ci.py` 与 `lib/repository.py` 的 workflow 定位
  逻辑（语义不同：单文件存在性对账 vs 目录枚举，结论记 design.md）。

## Prior art

- pytest `pythonpath` 配置项（官方特性，解决非 src 布局包的测试导入）：
  <https://docs.pytest.org/en/stable/reference/reference.html#confval-pythonpath>
- 平铺包 + 门面布局沿用本仓既有惯例：`python/netwave/`（发布包）、
  `scripts/versions/`（现门面），分层参照同生态 CLI 工具常见的
  `lib/` 内部模块组织；无跨语言现成方案可整体照搬，属仓内惯例延伸。

## 专家增补

- 一次性回归基线留痕：`baseline_before.txt` / `baseline_after.txt` 的
  diff 结论写进 PR 描述（文件本身不入库），使"只搬不改"可审计而非口头
  保证。
- `lib/version.py` 单测覆盖语义分叉边界：`1.85` vs `1.85.0`、`v` 前缀、
  major-only tag——正是旧两实现判定相反之处，见 `scripts/tests/`。
- 退出码契约（versions 门面 0/1、outdated 恒 0）写进
  `scripts/versions/README.md`，防止未来有人给 outdated 加非零退出破坏
  "informational" 定位。
- `uv run ruff check scripts/` 在拆包后本地先跑：包内相对导入的 lint
  行为与平铺不同，避免拆完才发现格式/导入排序红。
