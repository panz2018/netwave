# Tasks

## 1. 离线防护脚手架

- [ ] 1.1 新建 `scripts/tests/conftest.py`：autouse fixture 替换
      `socket.socket`，任何测试真去联网立刻抛错（含明确报错文字
      "network access forbidden in tests"），并加一条 smoke 用例断言防护生效
      （尝试 `urllib.request.urlopen` 抛异常）；验证：
      `uv run pytest scripts/tests -q` 全绿，且临时写一条真联网用例时该用例红

## 2. lib/repository.py 发现式扫描补测

- [ ] 2.1 在 `scripts/tests/versions/lib/test_repository.py` 补
      `workspace_members`（读根 Cargo.toml `members` 拼 `X/Cargo.toml`）与
      `rust_versions`（成员缺 `rust-version` 时省略、成员目录无 Cargo.toml 时
      跳过）用例，tmp_path 夹具造 Cargo.toml；验证：新用例经
      `uv run pytest scripts/tests/versions/lib/test_repository.py -q` 通过
- [ ] 2.2 补 `toolchain_channel`（读 `rust-toolchain.toml` 的 channel）与
      `find_ci_workflows`（`.github/workflows/*.yml` 排序返回、无目录返回空）
      用例；验证：同上命令通过
- [ ] 2.3 补 `ci_python_cells`（`python-version:` 列表与内联两种写法都抽到、
      带引号与不带引号都识别、SKIP_DIRS 内 yml 不计入）用例；验证：同上通过
- [ ] 2.4 补 `find_package_managers`（只收带 `packageManager` 的
      package.json、值原样返回）与 `is_python_project`（有 `[project]` 为真、
      注释里提到 `[project]` 不算、坏 TOML 返回 False）用例；验证：同上通过

## 3. lib/rules.py 输出契约补测

- [ ] 3.1 在 `scripts/tests/versions/lib/test_rules.py` 补 `summary` 用例：
      断言通过摘要行的完整措辞（以 `version laws OK:` 开头、含
      `rust-version` 与 `pin` 两字段）与成员计数——输出契约逐字钉住，
      为后续"去 `pin` 黑话"change 提供 red 基线；验证：
      `uv run pytest scripts/tests/versions/lib/test_rules.py -q` 通过
- [ ] 3.2 补 `all_laws` 用例：干净夹具返回四个空列表、违规夹具按四律顺序
      聚合（顺序是报告契约）；验证：同上通过

## 4. lib/latest.py 纯逻辑补测

- [ ] 4.1 新建 `scripts/tests/versions/lib/test_latest.py`，覆盖
      `first_line`（多行横幅取首个非空行、前导空行跳过、全空返回 `?`）与
      `is_version_tag`（带 v 前缀或裸数字的一至三段版本号均为真，
      `stable`/`main`/带后缀的分支名均为假）；验证：
      `uv run pytest scripts/tests/versions/lib/test_latest.py -q`
      通过
- [ ] 4.2 补 `find_uv_projects`：monkeypatch `lib.latest.ROOT` 指向 tmp_path
      （先断言替换生效），造 `python/uv.lock` 与根 `uv.lock`，断言返回
      `["python", "."]` 顺序（`python/uv.lock` 先于 `uv.lock`，出处
      `Plan/软件升级.md` 曾踩坑记录，注释注明）且 SKIP_DIRS（`target/`、
      `node_modules/`）内的 uv.lock 不计入；验证：同上通过
- [ ] 4.3 补 `action_refs`：夹具 yml 含普通 action 引用行、
      docker 引用行（排除）、多级路径引用行（保留原样）、
      无 `@` 的 `uses:` 行（不匹配）；断言返回集合；验证：同上通过

## 5. lib/latest.py 联网与子进程函数补测

- [ ] 5.1 补 `fetch_json` 三例（替换 `urllib.request.urlopen`，闭包收集
      请求对象）：有 `GITHUB_TOKEN` + api.github.com 地址 → 带
      `Authorization: Bearer`；无令牌 → 不带；npm 地址 + 有令牌 → 不带令牌；
      三例均断言带 `User-Agent`；验证：
      `uv run pytest scripts/tests/versions/lib/test_latest.py -q` 通过
- [ ] 5.2 补 `latest_version` 六例（替换 `fetch_json`）：npm 取
      `dist-tags.latest`、github 取 `tag_name`、github-tags 取首个 tag 名、
      空 tag 列表返回 `?`、endoflife `lts`（跳过非 LTS cycle 取首个 LTS）与
      `stable`（取首条）、无 LTS 返回 `?`；验证：同上通过
- [ ] 5.3 补 `latest_version` 两条报错分支：未知来源 kind 与未知 endoflife
      kind 各断言 `pytest.raises(ValueError)` 且消息含非法值；验证：同上通过
- [ ] 5.4 补 `refine_node_lts` 两例（替换 `fetch_json` 返回 nodejs.org
      版本列表）：命中 LTS 线返回该行最新补丁版（`v26.12.1` → `26.12.1`）、
      线上无匹配时原样返回入参行号；验证：同上通过
- [ ] 5.5 补 `run_cmd` 三例：`echo hello` → rc 0 且输出 `hello`；
      `netwave-no-such-cmd` → rc 非 0 且错误文字进返回值（验证 stdout+stderr
      拼接与失败不抛异常）；替换内部执行函数使其抛异常 → rc 125 且不崩溃；
      验证：同上通过

## 6. 门面测试

- [ ] 6.1 新建 `scripts/tests/versions/test_check_versions.py`：替换
      `lib.rules.all_laws` 注入预设错误，调 `main()` 断言每条错误以
      `::error::` 前缀进 stderr 且返回 1；全空错误时断言打印通过摘要且返回 0；
      验证：`uv run pytest scripts/tests/versions/test_check_versions.py -q` 通过
- [ ] 6.2 新建 `scripts/tests/versions/test_check_outdated.py`：把全部探针
      依赖（`run_cmd`、`fetch_json`、`latest_version`、`refine_node_lts`、
      `find_uv_projects`、`action_refs`）替换为抛异常，调 `main()` 断言仍返回 0
      且四段标题（`=== 1..4 ===`）齐全、失败段落降级为 `WARN`——钉住"恒退 0"
      契约；验证：`uv run pytest scripts/tests/versions/test_check_outdated.py -q`
      通过
- [ ] 6.3 补体检正常路径用例：探针返回构造数据，断言 LAG/OK 标记正确，
      并造 `uses: x/y@stable` 夹具断言输出 `REF` 而非 `LAG`（非版本 ref
      不误报）；验证：同上通过

## 7. 文档同步

- [ ] 7.1 修正 `scripts/versions/README.md` 测试段落中"Unit tests …
      fixtures only, offline"措辞（改为：离线夹具 + 依赖替换，测试禁止真联网），
      使用方法段保持原样不加细节；验证：`pnpm check:md` 退出 0

## 8. 集成验证

- [ ] 8.1 反向验证（铁律二对补测任务的落法）：逐处故意改坏被测代码——
      四律各一处（删 `rust-version`、删 `requires-python`、
      `packageManager` 改 range、CI 矩阵删一格）、`is_version_tag` 正则放宽、
      `is_outdated` 比较反向、两门面退出码翻转——确认对应测试变红后改回，
      验证项与结果逐条记入本文件完成记录；验证：改坏时
      `uv run pytest scripts/tests -q` 出现失败、改回后全绿
- [ ] 8.2 跑 `uv run pytest --cov=scripts/versions`
      加 `--cov-report=term-missing`（整条命令单行执行），把每个文件剩余
      未覆盖行号贴进本文件完成记录（日后阈值讨论的唯一数据），
      确认不设阈值、不加豁免；验证：命令退出 0
- [ ] 8.3 跑 `pnpm check`（含 `check:py` 与 `check:meta` 的
      `check_proposal.py` 闸门）全绿，确认新测试自动进既有闸门且
      `package.json`/`ci.yml` 零改动；验证：退出码 0

## Workflow follow-up

- apply 完成时删除 `Plan/软件升级.md` 中「versions 域补全单测」待办条目
  及「落地形态汇总」对应行（config.yaml apply 钩子），删后跑 `pnpm check:md`
- apply 完成前扫 `openspec/specs/` 做三态时效检查（本 change 预期：无 spec
  需改，`skip_specs`），结论留痕本文件
- retro：评估 `find_uv_projects` 排序坑是否新增 LL 至
  `openspec/specs/lessons-learned/python.md`
- 提交分组与标题由人工确认后执行（agent 不主动 commit）

## 完成记录

（apply 阶段填写：8.1 反向验证清单与结果、8.2 覆盖率剩余未覆盖行号、
8.3 闸门输出摘要、三态时效结论。）
