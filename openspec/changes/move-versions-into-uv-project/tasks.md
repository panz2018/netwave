# Tasks

本 change 为结构搬家，无数值实现任务（red/green 规则不适用）；等价保险是
**基线输出对比**：搬家前后两脚本输出必须一致（1.1 留基线，2.x 逐项比对）。

## 1. 基线与根 uv 工程

- [x] 1.1 留回归基线：`python3 scripts/check_versions.py > /tmp/cv_base.txt`、
      `python3 scripts/check_outdated.py > /tmp/co_base.txt`（体检需联网，
      允许时间戳类行差异，比对时忽略）。验证：两命令 exit 0。
- [x] 1.2 建根工程：`pyproject.toml`（`name = "netwave-workspace"`、
      `version = "0.0.0"`、private、`requires-python = ">=3.14"`、
      `[tool.uv] package = false`、dev 组 pytest/pytest-cov/ruff）+
      `.python-version`（3.14，与 `python/.python-version` 同值）+
      `uv lock`。验证：根 `uv.lock` 生成；
      `uv run python --version` 输出 3.14.x；`uv run ruff --version` 可用。

## 2. 搬家（内容原样，仅路径适配）

- [x] 2.1 `git mv scripts/versions.json scripts/versions/lib/registry.json`、
      `git mv scripts/check_versions.py scripts/versions/check_versions.py`、
      `git mv scripts/check_outdated.py scripts/versions/check_outdated.py`。
      验证：`git status` 显示 rename，旧路径不存在。
- [x] 2.2 适配 `check_versions.py`：`REGISTRY` 常量改指
      `scripts/versions/lib/registry.json`（`Path(__file__)` 定位），docstring
      内旧路径更新。验证：`uv run python scripts/versions/check_versions.py`
      exit 0 且输出与 /tmp/cv_base.txt 一致。
- [x] 2.3 适配 `check_outdated.py`：`REGISTRY` 常量与 docstring 同上。
      验证：`uv run python scripts/versions/check_outdated.py` 四段均出结果，
      与 /tmp/co_base.txt 无实质差异。

## 3. 接线（package.json / python 工程 / CI）

- [x] 3.1 根 `package.json`：`check:meta` 内 `python3 scripts/check_versions.py`
      → `uv run python scripts/versions/check_versions.py`；`check:outdated`
      同理；`check:py`/`fix:py` 的 ruff 改走根环境（去掉 `--project python`，
      作用域 `python/ scripts/` 不变）。验证：`pnpm check:meta`、
      `pnpm check:py`、`pnpm fix:py`（无 diff）全绿。
- [x] 3.2 `python/pyproject.toml` dev 组删 `ruff`，`uv lock --project python`。
      验证：`uv run --project python ruff --version` 不再可用（或提示装），
      `pnpm check:py` 仍绿（ruff 由根环境提供）。
- [x] 3.3 `.github/workflows/ci.yml` lint job：`pnpm install` 后、`pnpm check`
      前加 `uv sync --locked`（预建根环境 + 断言 lock 新鲜）。
      验证：本地按 LL-004 逐条模拟 lint job 命令序列全绿。
- [x] 3.4 registry 自登记与自引更新：新增 `root-python`（category
      `lang-matrix`、`pin_location: .python-version`、paired_with
      `python-runtime`）、`root-requires`（category `lang-floor`、
      `pin_location: pyproject.toml`、field `project.requires-python`、
      paired_with `root-python`）、`root-uv-lock`（category `lockfile`、
      `pin_location: uv.lock`、paired_with `root-python`）；`$comment` 内
      旧脚本路径更新。验证：`uv run python scripts/versions/check_versions.py`
      exit 0（发现式扫描无未登记 pin）。

## 4. 文档同步（LL-008：grep 旧路径改全）

- [x] 4.1 新建 `scripts/versions/README.md`：本域功能（登记表 + 离线对账 +
      联网体检）、目录结构、跑法命令（uv run 两条 + pnpm 入口两个）。
- [x] 4.2 `scripts/README.md`：表格加 `versions/` 行并指向其 README；
      移除已搬走的 check_versions/check_outdated 相关表述（如有）。
- [x] 4.3 AGENTS.md（依赖版本策略节 `scripts/versions.json` 引用）、
      CONTRIBUTING.md（登记表与闸门路径）更新为新路径。
- [x] 4.4 Plan/ 同步：`scripts-versions包化.md` 删除第一步已完成内容
      （结论吸收进本 change spec，只留第二步拆分/测试/pairs 待办）；
      `测试规划.md` oracle 落地清单与待议节内 `scripts/versions.json`、
      `scripts/check_versions.py` 路径更新；`配对版本校验.md` 登记表路径
      更新。验证：`pnpm check:md` 全绿。
- [x] 4.5 全仓 grep 兜底：`scripts/versions.json`、`scripts/check_versions.py`、
      `scripts/check_outdated.py` 零残留（`openspec/changes/archive/` 历史
      不改写；`upgrade-python-3-15` 暂停件按 design.md 决策留待恢复时更新，
      确认其 proposal 顶部无需本轮改动）。验证：grep 输出仅含豁免路径。

## 5. 验收与收尾

- [x] 5.1 `pnpm check` 全绿（md/ts/rs/py/meta 五路）；两脚本输出与 1.1
      基线一致。
- [x] 5.2 retro：搬家过程踩坑（如有）当轮登记 lessons-learned
      （ci/workflow scope 分片 + INDEX）；无坑则跳过并注明。

## Workflow follow-up

- 实施完成后 `/opsx:sync`（三个 delta：workspace-layout 新增 Requirement、
  dependency-upgrade 与 ci-matrix 修改 Requirement 路径表述），再
  `/opsx:archive`；归档前按 config 指引做 Plan/ 瘦身检查。
- 提交分组由人工确认后执行（agent 不主动 commit）。
