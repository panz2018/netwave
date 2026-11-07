# Proposal

## Why

`scripts/versions/` 是版本一致性闸门（`check_versions.py`，进
`pnpm check:meta`）与过期体检（`check_outdated.py`）的所在地，但现有 39 例
测试只覆盖 `lib/version.py`、`lib/rules.py` 部分分支与 `lib/repository.py`
三个函数——`lib/latest.py` 整个模块零测试，两个门面零测试，四律依赖的地基
（`workspace_members`、`rust_versions`、`ci_python_cells` 等发现式扫描）
几乎裸奔。闸门 bug 的后果是静默放行（该 FAIL 的输入被放过，没人知道它没
拦），比业务代码 bug 更隐蔽；且后续 blocked 清单、pairs 表都要消费这些
函数，地基没测试，机制越堆越虚。

## What Changes

- 新增 `scripts/tests/versions/lib/test_latest.py`：覆盖 `lib/latest.py`
  全部函数——纯逻辑（`first_line`、`is_version_tag`、`find_uv_projects`、
  `action_refs`）离线夹具直测；联网函数（`fetch_json`、`latest_version`、
  `refine_node_lts`）与子进程函数（`run_cmd`）用 pytest `monkeypatch`
  替换依赖后测调用形状与降级分支。
- 补 `scripts/tests/versions/lib/test_repository.py`：
  `workspace_members`、`rust_versions`、`toolchain_channel`、
  `ci_python_cells`、`find_package_managers`、`is_python_project`、
  `find_ci_workflows`（临时目录夹具，离线）。
- 补 `scripts/tests/versions/lib/test_rules.py`：`summary`（通过摘要行
  输出契约）、`all_laws`（四律聚合顺序）。
- 新增门面测试 `scripts/tests/versions/test_check_versions.py` 与
  `test_check_outdated.py`：进程内调用 `main()`，断言错误聚合
  （`::error::`）、退出码（gate 0/1）、体检四段齐全、探针失败降级 WARN、
  恒退 0 契约、非版本 ref 打 `REF` 不误报 `LAG`。
- 新增 `scripts/tests/conftest.py`：自动生效的离线防护——任何测试真去
  联网立刻报错，把"测试必须离线"从口头约定变成机器强制。
- 修正 `scripts/versions/README.md` 中"Unit tests … fixtures only,
  offline"一句（引入依赖替换后不再准确），只改这一句措辞，使用方法保持
  简单。
- 不设覆盖率阈值、不加覆盖率豁免标注，维持 `check:py` 现状只报数；
  完成时把 `--cov-report=term-missing` 各文件剩余未覆盖行号贴进
  tasks.md 完成记录，作为日后是否上阈值的唯一依据。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——本 change 只新增测试与测试侧防护，不改任何闸门行为、输出契约、
命令或 CI 步骤；`dependency-upgrade` spec 与 `workspace-layout` spec 的
要求均不受影响。故 `skip_specs: true`。）

## Non-goals

- 不设覆盖率阈值、不加 `# pragma: no cover` 豁免（阈值待补测后凭真实
  数字另议）。
- 不碰 `scripts/` 其余 9 个闸门脚本（`check_md.py`、`check_license.py`
  等）的测试——versions 域先立先例，其余按模板另批推进。
- 不改生产代码签名（`find_uv_projects`/`action_refs` 的仓库根注入走测试侧
  替换模块常量，不改函数参数）。
- 不改 `check_versions.py` 摘要措辞（`pin` 黑话去除是另一条已登记待办，
  属输出契约变更，禁止搭车）。
- 不实施 blocked 清单、pairs JSON 化、过期检查门禁化（各自独立待触发）。
- 不动 CI（`ci.yml` 零改动；新测试经既有 `pnpm check:py` 自动进闸门）。

## Impact

- `scripts/tests/`：新增 `conftest.py`、`versions/lib/test_latest.py`，
  扩充 `test_repository.py`、`test_rules.py`，新增
  `versions/test_check_versions.py`、`versions/test_check_outdated.py`
  （约 43 例，39 → 约 82）。
- `scripts/versions/README.md`：测试段落一句措辞修正。
- `Plan/软件升级.md`：「versions 域补全单测」待办条目随本 change 完成
  删除（apply 钩子）。
- 生产代码零改动；`package.json`、`pyproject.toml`、`ci.yml` 零改动
  （测试发现靠根 `pyproject.toml` 既有 `testpaths`）。

## Prior art

- 仓库内既有测试风格：`scripts/tests/versions/lib/test_rules.py`
  （tmp_path 夹具 + 类组织，本 change 沿用）。
- pytest 官方 monkeypatch 机制：
  <https://docs.pytest.org/en/stable/reference/reference.html#monkeypatch>
- 离线防护思路（阻断 socket 强制测试离线）无仓库内现成件，采用标准库
  `socket` 层替换的通用做法：
  <https://docs.python.org/3/library/socket.html>

## 专家增补

- `scripts/tests/versions/test_check_outdated.py` 专设一例：全部探针替换
  为抛异常，断言 `main()` 仍返回 0 且四段标题齐全——`check_outdated.py`
  的"恒退 0"是 README 明文契约，目前无任何测试钉住，这是防日后误改成
  闸门（`return 1`）的唯一防线。
- 门面用例造一条 `uses: x/y@stable` 夹具，断言输出 `REF` 而非 `LAG`——
  `check_outdated.py` 第 4 段的非版本 ref 分支是"体检不误报"的关键，
  当前零覆盖。
- `test_latest.py` 覆盖 `latest_version` 的两条 `raise ValueError`
  （未知 kind / 未知 endoflife kind）——探针元组写错时靠这两条报错，最易
  漏测也最该测。
- `run_cmd` 按人工裁决单独测三例：正常命令（`echo`）验证跑对、不存在命令
  验证错误被正确接住（退出码非 0 且错误文字进返回值）、内部执行抛异常时
  返回码 125 不崩溃。
- `find_uv_projects` 排序用例（`python/uv.lock` 先于 `uv.lock`）注释注明
  出处 `Plan/软件升级.md` 曾踩坑记录，retro 时评估是否新增 LL 至
  `openspec/specs/lessons-learned/python.md`。
- 关键判定做反向验证（铁律二对补测任务的落法）：故意改坏被测代码确认
  对应测试变红再改回，验证项记录于 tasks.md，防"永远绿"假测试。
