# 任务：考古清理、堵源头、关缝隙与覆盖率统一

## 1. 门禁脚本（red 先于 green）

- [ ] 1.1 新增 `scripts/tests/test_check_comments.py`（沿用
      `test_coverage_gate.py` 先例）：六项固定形态标记各一条命中用例
      （`LL-` 编号、`CI run` + 六位以上数字、`Re-enabled`/`重新启用` + 日期、
      `已标定`、`design decision`/`design D` + 数字、开发文档指针）；
      三类负例（裸日期夹具、`Deprecated: use X instead`、豁免路径
      `pnpm-lock.yaml`/`openspec/config.yaml`/archive `.openspec.yaml`）；
      `.yml`/`.yaml`/`.toml` 注释命中用例。夹具中的触发标记构造在字符串
      字面量或拼接中，不用注释行（`.py` 注释在扫描面上）。
      验证：`uv run pytest scripts/tests/test_check_comments.py` 失败
      （新后缀与新模式未实现，命中用例红）。
- [ ] 1.2 改 `scripts/check_comments.py`：后缀集扩至
      `rs/py/ts/yml/yaml/toml`；新增模式（CI run 号、动词+日期、
      `design decision`/`design D` + 数字）；文件级豁免白名单
      （`pnpm-lock.yaml`、archive 下 `.openspec.yaml`、`openspec/config.yaml`、
      既有 `EXEMPT_DIRS`）；更新脚本 docstring 为当前契约表述。
      验证：1.1 测试全 PASS；`python3 scripts/check_comments.py`
      对当前仓库报出 ci.yml/rust-toolchain.toml 存量（门禁抓到存量的证据，
      退出码 1）。

## 2. 配置存量清零

- [ ] 2.1 改写 `.github/workflows/ci.yml` 全部考古注释：删 `LL-011`、
      `LL-034`、`LL-047` 编号、`CI run 43603143333`、
      `Re-enabled 2026-09-26 after the typescript manual review landed`、
      `design decision 7` 等归因，保留结论性事实（为什么这么做、触发条件），
      只陈述当前契约。改写处含：L110（CI run 号）、L208（LL-011）、
      L327/L333（LL-034，含 `::error::` 文案）、L342（LL-011）、
      L351（LL-047）、L235（Re-enabled）、L288（design decision 7）、
      L103-105（`retired` 叙述）。
      验证：`python3 scripts/check_comments.py` 对 ci.yml 零命中；
      `pnpm check:ts` 绿（Biome YAML 格式执法）；`pnpm check:meta` 中
      `check_ci.py` 绿（`typescript test:native` 等字面仍在）。
- [ ] 2.2 改写 `rust-toolchain.toml` L3-4：删 `workspace-layout spec` 指针，
      保留"钉 stable，升级走 OpenSpec change"的当前契约表述。
      验证：`python3 scripts/check_comments.py` 零命中。

## 3. 能力 spec 措辞改写（直接改主 spec，无行为变化）

- [ ] 3.1 `openspec/specs/api-contract/spec.md` L63：`upload` 概念废止句
      改写为当前契约声明（"无 `upload` 概念"），归因删、结论留。
- [ ] 3.2 `openspec/specs/ci-matrix/spec.md` L119-120：口径废止与被推翻句
      改写为只陈述当前采集口径；L230：`不再是` 改写为当前事实。
- [ ] 3.3 `openspec/specs/memory-lifecycle/spec.md` L40：两表废止句
      改写为当前结构表述。
- [ ] 3.4 `openspec/specs/oracle-harness/spec.md` L39：命名废止句
      改写为当前命名契约。
- [ ] 3.5 `openspec/specs/workspace-layout/spec.md` L19：`testdata/` 废止句
      改写为当前布局事实。
- [ ] 3.6 `openspec/specs/zero-copy-roundtrip/spec.md` L18/L22/L23/L85：
      四处废止叙述改写为当前契约（无分流、无 `_` 同步函数、基准文件
      命名现状）。
- [ ] 3.7 保留判定（不改，留证据）：`touchstone-core/spec.md` L443
      "不再是合法选项行"为输入行为描述、`project-governance/spec.md`
      L701/L722 "契约废止"为规则生命周期判据的当前规则——均非考古；
      在 1.1 测试中落为负例锁定。
      验证：`pnpm check:md` 绿；改写前后逐条 diff 自查结论未丢。

## 4. 堵源头：AGENTS.md 出处措辞

- [ ] 4.1 改 `AGENTS.md`「改动要有去向」条：出处改为"落 commit message 与
      lessons-learned 账本"，明确被门禁扫描的文件（代码/配置/spec 正文）
      注释内不写 LL 编号与 spec 指针；保留"删除/迁出须写明去向"与
      "Standards 轴打回"两句不变。验证：`pnpm check:md` 绿；
      该节读后不再要求往文件里写编号。

## 5. 关缝隙：health-check 两态化与改名

- [ ] 5.1 `git mv openspec/specs/archive-health-check openspec/specs/health-check`，
      同步 3 处引用：spec 标题行、`openspec/specs/README.md` 路由行
      （描述补"两态触发"）、`openspec/config.yaml` archive guidance 的
      spec 名指针；并把本 change 的 delta 目录同步改名为
      `specs/health-check/`（delta 目录名须与目标 spec 目录名一致，
      否则 archive 时 CLI 找不到目标）。
      验证：`openspec validate` 加 `--strict` 退出码 0；`pnpm check:md` 绿
      （BROKEN FILE/ARCHIVE PATH 门禁兜底）；全仓 grep `archive-health-check`
      仅剩账本与 Plan 的冻结引用。
- [ ] 5.2 主 spec 正文按本 change 的 health-check delta 落地：Requirement
      改名两态、加 apply 态触发条款、`Plan/` 维标注仅 archive 态适用、
      新增语义考古维 Scenario、边界条款改准"diff 行归三轴、被触碰文件
      全文归 apply 态体检"。验证：delta 与主 spec 逐条一致。
- [ ] 5.3 `openspec/config.yaml` 的 apply guidance 加一步：三轴 review 之后、
      `check:outdated` 之前 MUST 执行被触碰文件全文体检（只读，发现落
      `Plan/` 等点名，规则本体见 health-check spec，本条不复述）。
      验证：`pnpm check:md` 绿；YAML 经 Biome 格式化（`pnpm check:ts` 绿）。

## 6. 覆盖率配置统一

- [ ] 6.1 阅卷人补测 2 条（red 先于 green）：`scripts/tests/` 内为非数字键
      `continue` 分支与 `sys.exit(main())` 守卫各加一条用例（后者按 LL-079
      用 `runpy` 跑子进程钉退出码）。验证：先跑 `uv run pytest` 确认新用例
      在补测前对应行为无覆盖（覆盖率报告点名未覆盖行），补测后全 PASS。
- [ ] 6.2 根 `pyproject.toml` 加 `[tool.coverage]`：`source` =
      `scripts/versions`、`scripts/coverage_gate.py`、
      `scripts/check_comments.py`，`fail_under` = 100；`[tool.pytest.ini_options]`
      加 `addopts` 使 `uv run pytest` 默认带覆盖率报告。
      验证：`uv run pytest` 退出码 0，终端覆盖率表含三目标且均 100%。
- [ ] 6.3 根 `package.json` 的 `check:py` 删 `--cov=scripts/versions` 与
      `--cov-fail-under=100`（范围与阈值只留 `pyproject.toml` 一处）。
      验证：`pnpm check:py` 退出码 0；红向验证——临时注释掉
      `test_check_comments.py` 任一命中用例，`pnpm check:py` 退出码 1
      （地板真生效），还原后复绿。

## 7. 治理同步与时效

- [ ] 7.1 确认三份 delta 与实现一致：跑 `openspec validate` 加 `--strict`
      对 `purge-archaeology-refs`，退出码 0。
- [ ] 7.2 删除 `Plan/考古文字清理-2026-11-14.md` 与
      `Plan/阅卷人覆盖率-2026-11-14.md`（结论已全部吸收进本 change 工件）。
      验证：`pnpm check:md` 绿。
- [ ] 7.3 三态时效检查（更新/新增/退役）：更新 `project-governance`、
      `ci-matrix`、`health-check`（改名+两态）；新增能力 0；退役 0；
      `scripts/README.md` 与 `Plan/测试规划.md` 覆盖率口径行同步。
      结论留痕本节完成记录。

## 8. 收尾闸门

- [ ] 8.1 全量闸门：跑 `pnpm check`（含 check:md、check:ts、check:rs、
      check:py、check:meta），退出码 0。
- [ ] 8.2 三轴 review：按 governance spec「元规则 review 三轴」
      （Standards/Spec/Lessons）对照本 change 工件审实现 diff，硬伤清零。
- [ ] 8.3 专职全文体检（apply 态）：按 health-check spec 对本次 diff 触碰
      文件的全文做只读体检（语义考古维 + 四维），发现附文件+行号+证据
      落 `Plan/体检-<日期>.md`，不阻塞、修复等点名；无适用文件时记
      "已查，无适用文件"。
- [ ] 8.4 归档豁免留痕：经人工裁决（2026-11-15），本 change 归档时一次性
      跳过 health-check spec 的 archive 态体检——仅豁免本 change 这一次，
      规则本体（spec 与 `openspec/config.yaml` 的 archive guidance）不变。
- [ ] 8.5 `pnpm check:outdated` 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化所报 LAG，复跑至退出码 0。
