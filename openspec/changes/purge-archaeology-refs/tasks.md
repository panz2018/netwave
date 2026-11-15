# 任务：考古清理、堵源头、关缝隙与覆盖率统一

## 1. 门禁脚本（red 先于 green）

- [x] 1.1 新增 `scripts/tests/test_check_comments.py`（沿用
      `test_coverage_gate.py` 先例）：六项固定形态标记各一条命中用例
      （`LL-` 编号、`CI run` + 六位以上数字、`Re-enabled`/`重新启用` + 日期、
      `已标定`、`design decision`/`design D` + 数字、开发文档指针）；
      三类负例（裸日期夹具、`Deprecated: use X instead`、豁免路径
      `pnpm-lock.yaml`/`openspec/config.yaml`/archive `.openspec.yaml`）；
      `.yml`/`.yaml`/`.toml` 注释命中用例。夹具中的触发标记构造在字符串
      字面量或拼接中，不用注释行（`.py` 注释在扫描面上）。
      验证：`uv run pytest scripts/tests/test_check_comments.py` 失败
      （新后缀与新模式未实现，命中用例红）。
      完成记录：red 已取——实现前 11 failed / 21 passed，失败项恰为新行为
      （CI run 号、动词+日期、design 代号、`.yml`/`.toml` 后缀、在途
      manifest），既有行为 21 例全绿。
- [x] 1.2 改 `scripts/check_comments.py`：后缀集扩至
      `rs/py/ts/yml/yaml/toml`；新增模式（CI run 号、动词+日期、
      `design decision`/`design D` + 数字）；文件级豁免白名单
      （`pnpm-lock.yaml`、archive 下 `.openspec.yaml`、`openspec/config.yaml`、
      既有 `EXEMPT_DIRS`）；更新脚本 docstring 为当前契约表述。
      验证：1.1 测试全 PASS；`python3 scripts/check_comments.py`
      对当前仓库报出 ci.yml/rust-toolchain.toml 存量（门禁抓到存量的证据，
      退出码 1）。
      完成记录：32 passed；门禁 exit=1 报 6 处——`Cargo.toml:5`（开发文档指针，
      tasks 清单外新发现，归入 2.3 清理）、ci.yml L110/L208/L235/L342/L351。
      `rust-toolchain.toml` 与 ci.yml L288/L103 未被机械抓到（无固定形态，
      属语义层，由 AI 审查发现并清理）。实施中发现并修复两处既有缺陷：
      `glob` 不匹配点开头路径（`.github/`、`.openspec.yaml` 扫不到，改
      `os.walk`）；豁免目录子串匹配使 `.github/` 被 `.git` 误豁免（改按
      路径组件匹配）。

## 2. 配置存量清零

- [x] 2.1 改写 `.github/workflows/ci.yml` 全部考古注释：删 `LL-011`、
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
      完成记录：已清 12 处——除清单所列 8 处外，AI 全文审查另发现 4 处
      （L139 `dependency-upgrade spec` 指针、L162 `ironclad rule 8` 铁律编号、
      L358 `ci-matrix spec` 指针、L59-62 `Intel x64 dropped` / `meant an if`
      历史叙述）。`check_comments` 对 ci.yml 零命中，`check_ci.py` 绿
      （3 个 test 脚本接线字面全保留），Biome YAML 格式绿。
- [x] 2.2 改写 `rust-toolchain.toml` L3-4：删 `workspace-layout spec` 指针，
      保留"钉 stable，升级走 OpenSpec change"的当前契约表述。
      验证：`python3 scripts/check_comments.py` 零命中。
      完成记录：已改为"Pinned stable version floor; upgrades go through an
      OpenSpec change"，该文件零命中。
- [x] 2.3 改写 `Cargo.toml` L5（门禁扩面后新报）：删 `spec: zero-copy-roundtrip`
      指针，保留"LTO 为 wasm 体积"的当前契约表述。
      验证：`python3 scripts/check_comments.py` 全仓零命中（exit 0）。

## 3. 能力 spec 措辞改写（直接改主 spec，无行为变化）

- [x] 3.1 `openspec/specs/api-contract/spec.md` L63：`upload` 概念废止句
      改写为当前契约声明（"无 `upload` 概念"），归因删、结论留。
      完成记录：改为"公开面无 `upload` 概念（浏览器、node、Python 均无）"。
- [x] 3.2 `openspec/specs/ci-matrix/spec.md` L119-120：口径废止与被推翻句
      改写为只陈述当前采集口径；L230：`不再是` 改写为当前事实。
      完成记录：删"原口径废止…被推翻"叙述，改"绑定 crate 由
      show-env/report 外部驱动采集度量"；L230 改"YAML 格式有执法者，
      不靠散文约定"。
- [x] 3.3 `openspec/specs/memory-lifecycle/spec.md` L40：两表废止句
      改写为当前结构表述。
      完成记录：删"现有 `hosted`/`frequencies` 两表与逐动词 `cmds` 表
      废止"，保留"worker JS MUST NOT 存在任何句柄 `Map`…"当前契约。
- [x] 3.4 `openspec/specs/oracle-harness/spec.md` L39：命名废止句
      改写为当前命名契约。
      完成记录：改"产物命名恒为上述分层布局，不用平铺形态"，
      删平铺命名列举与"废止"。
- [x] 3.5 `openspec/specs/workspace-layout/spec.md` L19：`testdata/` 废止句
      改写为当前布局事实。
      完成记录：改"数值真值内容（manifest、样本、LICENSE-NOTES）居
      `oracle/`，仓库根无 `testdata/` 目录"。
- [x] 3.6 `openspec/specs/zero-copy-roundtrip/spec.md` L18/L22/L23/L85：
      四处废止叙述改写为当前契约（无分流、无 `_` 同步函数、基准文件
      命名现状）。
      完成记录：L18"浏览器端 `_` 同步计算函数废止"→"浏览器端无 `_`
      同步计算函数"；L22"分流废止"→"不分流"、L23"小数据主线程算
      废止"→"无小数据主线程算路径"；L85"不再以 node 模拟代替"→
      "验收 MUST 在真浏览器完成（不以 node 模拟替代）"、"scaffold 图案
      对拍…废止"→"…不存在"。
- [x] 3.7 保留判定（不改，留证据）：`touchstone-core/spec.md` L443
      "不再是合法选项行"为输入行为描述、`project-governance/spec.md`
      L701/L722 "契约废止"为规则生命周期判据的当前规则——均非考古；
      在 1.1 测试中落为负例锁定。
      验证：`pnpm check:md` 绿；改写前后逐条 diff 自查结论未丢。
      完成记录：三处原文未动；`test_check_comments.py` 新增
      `test_preserved_judgments_are_green` 负例锁定两句中文判定不被机械
      门禁误报。全仓 grep `废止|不再是` 余 4 处：本 change tasks.md 自身
      （开发文档，不在扫描面）与上述保留判定 3 处。`pnpm check:md` 绿。

## 4. 堵源头：AGENTS.md 出处措辞

- [x] 4.1 改 `AGENTS.md`「改动要有去向」条：出处改为"落 commit message 与
      lessons-learned 账本"，明确被门禁扫描的文件（代码/配置/spec 正文）
      注释内不写 LL 编号与 spec 指针；保留"删除/迁出须写明去向"与
      "Standards 轴打回"两句不变。验证：`pnpm check:md` 绿；
      该节读后不再要求往文件里写编号。
      完成记录：出处措辞已改为"出处落 commit message 与 lessons-learned
      账本，被门禁扫描的文件……注释内不写 LL 编号与 spec 指针，只留
      当前契约"；两句保留原文不动。`pnpm check:md` 绿。

## 5. 关缝隙：health-check 两态化与改名

- [x] 5.1 `git mv openspec/specs/archive-health-check openspec/specs/health-check`，
      同步 3 处引用：spec 标题行、`openspec/specs/README.md` 路由行
      （描述补"两态触发"）、`openspec/config.yaml` archive guidance 的
      spec 名指针；并把本 change 的 delta 目录同步改名为
      `specs/health-check/`（delta 目录名须与目标 spec 目录名一致，
      否则 archive 时 CLI 找不到目标）。
      验证：`openspec validate` 加 `--strict` 退出码 0；`pnpm check:md` 绿
      （BROKEN FILE/ARCHIVE PATH 门禁兜底）；全仓 grep `archive-health-check`
      仅剩账本与 Plan 的冻结引用。
      完成记录：两目录 `git mv` 完成；标题/Purpose 改两态表述，路由行
      改"两态只读体检（apply 被触碰文件全文 / archive 全项目存量）"，
      config.yaml archive guidance 指针改 `health-check`；delta 目录改名。
      `openspec validate --strict` 退出 0，`pnpm check:md` 绿；全仓 grep
      残留仅 archive/、账本、Plan/ 与本 change 工件自身。
- [x] 5.2 主 spec 正文按本 change 的 health-check delta 落地：Requirement
      改名两态、加 apply 态触发条款、`Plan/` 维标注仅 archive 态适用、
      新增语义考古维 Scenario、边界条款改准"diff 行归三轴、被触碰文件
      全文归 apply 态体检"。验证：delta 与主 spec 逐条一致。
      完成记录：主 spec `openspec/specs/health-check/spec.md` 首条
      Requirement 整块替换为 delta 版（两态触发、五维⑤标注仅 archive 态、
      新增「语义考古维（两态通用）」Scenario、边界条款含旧行归 apply 态）；
      其余 Requirement（三级去重/输出格式/硬伤标注/执行机制）delta 未改，
      主 spec 原样保留。delta 与主 spec 逐条对照一致。
- [x] 5.3 `openspec/config.yaml` 的 apply guidance 加一步：三轴 review 之后、
      `check:outdated` 之前 MUST 执行被触碰文件全文体检（只读，发现落
      `Plan/` 等点名，规则本体见 health-check spec，本条不复述）。
      验证：`pnpm check:md` 绿；YAML 经 Biome 格式化（`pnpm check:ts` 绿）。
      完成记录：apply guidance 在三轴 review 条与 check:outdated 条之间
      插入 apply 态体检一步；`pnpm check:md` 绿，Biome 对 config.yaml
      无修改（已合规）。

## 6. 覆盖率配置统一

- [x] 6.1 阅卷人补测 2 条（red 先于 green）：`scripts/tests/` 内为非数字键
      `continue` 分支与 `sys.exit(main())` 守卫各加一条用例（后者按 LL-079
      用 `runpy` 跑子进程钉退出码）。验证：先跑 `uv run pytest` 确认新用例
      在补测前对应行为无覆盖（覆盖率报告点名未覆盖行），补测后全 PASS。
      完成记录：red 已取——补测前 `coverage_gate.py` 93%（未覆盖
      L44/L46/L71/L110）、`check_comments.py` 97%（L99/L147）。实跑发现
      未覆盖行比 Plan 清单多 4 行（`_next_code_line` 跳行/EOF 分支、
      `is_exempt` 的 EXEMPT_FILES 分支、generated 路径过滤），一并补齐：
      `test_coverage_gate.py` 新增 `TestReportParsingBranches`（非数字键、
      跳空行/注释、EOF 不豁免）与 `TestMainGuard`（runpy 钉退出码），
      `test_check_comments.py` 新增 `test_is_exempt_matches_path_components`
      与 `test_generated_directory_is_skipped`；补测后 239 passed，两脚本
      均 100%。
- [x] 6.2 根 `pyproject.toml` 加 `[tool.coverage]`：`source` =
      `scripts/versions`、`scripts/coverage_gate.py`、
      `scripts/check_comments.py`，`fail_under` = 100；`[tool.pytest.ini_options]`
      加 `addopts` 使 `uv run pytest` 默认带覆盖率报告。
      验证：`uv run pytest` 退出码 0，终端覆盖率表含三目标且均 100%。
      完成记录：`[tool.coverage.run].source` = `scripts/versions` +
      `coverage_gate` + `check_comments`（后两者用裸模块名：两脚本经
      `pythonpath` 以顶层模块导入，写路径则 coverage 报
      module-not-imported 静默失效）；`[tool.coverage.report].fail_under`
      = 100；`addopts = ["--cov", "--cov-report=term"]`。`uv run pytest`
      退出 0，表含三目标全 100%，TOTAL 641/641。
- [x] 6.3 根 `package.json` 的 `check:py` 删 `--cov=scripts/versions` 与
      `--cov-fail-under=100`（范围与阈值只留 `pyproject.toml` 一处）。
      验证：`pnpm check:py` 退出码 0；红向验证——临时注释掉
      `test_check_comments.py` 任一命中用例，`pnpm check:py` 退出码 1
      （地板真生效），还原后复绿。
      完成记录：`check:py` 命令体简化为 ruff check + ruff format +
      `uv run pytest`（范围/阈值不再双写）；退出码 0。红向验证以
      `--deselect` 等价模拟用例失效（不临时改文件）：覆盖率 99.84%、
      pytest 退出码 1，地板真生效；不加 deselect 复绿。顺带修复两处
      E501 超长行（`check_comments.py` 日期模式、测试夹具行）。

## 7. 治理同步与时效

- [x] 7.1 确认三份 delta 与实现一致：跑 `openspec validate` 加 `--strict`
      对 `purge-archaeology-refs`，退出码 0。
      完成记录：`openspec validate purge-archaeology-refs --strict` 退出 0
      （改名后复验仍 valid）；三份 delta（project-governance /
      health-check / ci-matrix）均已按仓内先例在 apply 阶段落地主 spec，
      逐条与 delta 一致。
- [x] 7.2 删除 `Plan/考古文字清理-2026-11-14.md` 与
      `Plan/阅卷人覆盖率-2026-11-14.md`（结论已全部吸收进本 change 工件）。
      验证：`pnpm check:md` 绿。
      完成记录：两文件 `git rm`；`Plan/README.md` 路由表同步删
      阅卷人覆盖率行（否则 BROKEN FILE）；`pnpm check:md` 绿。
- [x] 7.3 三态时效检查（更新/新增/退役）：更新 `project-governance`、
      `ci-matrix`、`health-check`（改名+两态）；新增能力 0；退役 0；
      `scripts/README.md` 与 `Plan/测试规划.md` 覆盖率口径行同步。
      结论留痕本节完成记录。
      完成记录：更新 3（project-governance 两元规则、ci-matrix
      治理脚本单测进 CI、health-check 改名+两态，均已落地主 spec）；
      新增 0；退役 0。波及同步：`scripts/versions/README.md` 地板口径行
      从"`check:py` 的 `--cov-fail-under`（阈值定义在 `package.json`）"
      改为"根 `pyproject.toml` 的 `[tool.coverage]`（`check:py` 不带
      `--cov`）"——这是本次口径变更的真实旧事实残留。`scripts/README.md`
      的 `coverage_gate.py` 行描述 rust codecov 阅卷，与 python 地板无关，
      无需改；`Plan/测试规划.md` 无治理脚本覆盖率口径行（grep 零命中），
      无需改。`pnpm check:md` 绿。

## 8. 收尾闸门

- [x] 8.1 全量闸门：跑 `pnpm check`（含 check:md、check:ts、check:rs、
      check:py、check:meta），退出码 0。
      完成记录：`pnpm check` 退出码 0（五道闸门全绿，含 clippy
      --workspace -D warnings、pytest 239 passed 三目标 100%、
      check_comments 全仓零命中）。
- [x] 8.2 三轴 review：按 governance spec「元规则 review 三轴」
      （Standards/Spec/Lessons）对照本 change 工件审实现 diff，硬伤清零。
      完成记录：Standards 轴命中一处硬伤并修复——本 change 在
      `openspec/config.yaml` 的 apply guidance 三轴 review 与 check:outdated
      之间插入体检一步后，原三轴 review 条仍写"apply 倒数第二步"，
      锚点失效（现实为倒数第三步）——命中 LL-089（流程规则只写本步
      动作并核对步骤锚点，禁前移后置动作）。未遵守原因：加新步时
      只核对了新步自身的锚点（"三轴之后、check:outdated 之前"），
      未回扫相邻旧条的锚点是否因插入而失效。修复：三轴 review 条
      "apply 倒数第二步（check:outdated 之前）…才准入最后一项
      check:outdated"改为"apply 收尾（check:outdated 之前）…才准入
      后续步骤"，不再依赖序数锚点。Spec 轴：三份 delta 逐条已落地
      （见 7.1）。Lessons 轴：命中 LL-089（已上述修复）；LL-076
      （两份清单必漂移）已由 6.2/6.3 单一真相源落实；LL-094
      （改 pytest 全局配置须当轮全量跑并贴覆盖率清单）已贴三目标
      100% 证据。硬伤清零。
- [x] 8.3 专职全文体检（apply 态）：按 health-check spec 对本次 diff 触碰
      文件的全文做只读体检（语义考古维 + 四维），发现附文件+行号+证据
      落 `Plan/体检-<日期>.md`，不阻塞、修复等点名；无适用文件时记
      "已查，无适用文件"。
      完成记录：已查。语义考古维——对全部触碰文件全文扫历史归因/口径
      变更词，命中均为合法当前契约（governance spec 定义被禁词本身、
      `check_comments.py` 的 pattern 定义、`AGENTS.md` 对"实施"的释义、
      `scripts/versions/README.md` 的 node 迁移指令），非考古。四维：
      ①文档断言 vs 实测——覆盖率 100%、check_comments 全仓零命中、
      delta validate 退出 0，均已实证；②死代码/孤儿——改名残留已 grep
      清零、删 Plan 已同步路由、新测试文件被 pytest 收集，无孤儿；
      ③规则重复/冲突——唯一发现为 config.yaml 步骤锚点冲突，属本次
      diff 引入，已在 8.2 三轴当场修复，按「本次改动违规走三轴不进
      体检」不落 Plan/；④可门禁化 LL 未落闸门——新固定形态标记已落
      `check_comments.py`，LL-089 属流程软约束不可机械门禁。无新增
      发现需落 `Plan/体检-*.md`。
- [ ] 8.4 归档豁免留痕：经人工裁决（2026-11-15），本 change 归档时一次性
      跳过 health-check spec 的 archive 态体检——仅豁免本 change 这一次，
      规则本体（spec 与 `openspec/config.yaml` 的 archive guidance）不变。
- [x] 8.5 `pnpm check:outdated` 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化所报 LAG，复跑至退出码 0。
      完成记录：首跑报 1 LAG（cargo `rand 0.10.3 -> 0.10.4`，传递依赖
      patch 升级，属预授权）。`cargo update -p rand@0.10.3` 升级后
      `pnpm check` 退出 0、`pnpm check:cross` 四端对拍全绿
      （bit-exact + wasm within tol + 扰动自检 + vocab/verbs），
      复跑 `pnpm check:outdated` 退出 0（SUMMARY: 0 LAG）。
      Cargo.lock 升级改动归提交全景表单列一组，等人工点名。
