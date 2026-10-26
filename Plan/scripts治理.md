# scripts/ 治理：独立 uv 项目、单元测试、命名与升级（待议）

`scripts/` 现在有 13 个 py 闸门 + 2 个 sh 安装脚本 + 登记表，黑名单落地后
复杂度又上一台阶。四个关联问题尚未拍板，将来专门讨论后按结论开 OpenSpec
change。本文件只存正反双方论点与待决点，不预设结论。

## 问题一：要不要独立成 uv 项目

**正方（划入独立 uv 项目）**：

- scripts 已有近 1500 行 Python，且闸门是"守门员"，守门员自己没测试体系
  （无 pytest、无覆盖率、无依赖声明），与 `python/` 工程的待遇不对等；
- 独立 `pyproject.toml` 后，pytest/ruff/coverage 依赖自己声明自己锁，
  不再寄居 `python/` 的 dev 组，`uv run --project scripts` 一条命令跑全套；
- 目录自治：scripts 的 lint、测试、覆盖率门槛可单独配置，不与绑定工程
  （maturin/pyo3）的构建关注点混在一起。

**反方（维持现状，寄居 `python/` 的 uv 环境）**：

- 这些脚本**零第三方依赖**（纯标准库），uv 最大的价值（锁依赖）用不上；
- `python/` 已在管它们：`check:py` 即
  `uv run --project python ruff check python/ scripts/`，测试环境（pytest、
  pytest-cov）也已在 `python/` dev 组，缺的只是测试文件本身；
- 新建 uv 项目 = 新增 `uv.lock` + `.python-version` 两个钉版点 → 登记表
  条目、CI job、体检覆盖、workspace-layout spec 全波及，属结构性升级；
  为"整齐"付这个代价不值；
- 仓库惯例是"一个子项目一个 README + 一个 uv 工程"，scripts 不是发布物
  （scripts/README 明说 "Not part of any published package"），
  工程化到发布级是过度设计。

**待决点**：若独立，CI 是否加 job、登记表加几条、`check:py` 拆不拆；
若不独立，测试放 `scripts/tests/` 还是 `python/tests/scripts/`。

## 问题二：要不要单元测试 + 覆盖率 100%

**正方（要，且 100%）**：

- 闸门 bug 的后果是**静默放行**（该 FAIL 的输入被放过），比业务代码 bug
  更隐蔽——业务代码错了测试会红，闸门错了没人知道它没拦；
- 铁律七本来就要求全端 100% 行覆盖 unit 层零豁免，闸门脚本是仓库代码，
  没有理由例外；
- 黑名单、发现式扫描、slug 规则、版本比较这些纯逻辑分支多，手工 red/green
  验证（本次黑名单实施即如此）不可回归，改一次闸门就得手测一轮。

**反方（要测试，但 100% 一刀切不对）**：

- 脚本里大量代码是**网络与子进程胶水**（`_req`、`run`、GitHub/npm/
  endoflife 三家 API、pnpm/cargo/uv 子进程），逐行覆盖它们只能靠打桩，
  桩测出来的"绿"不证明真环境能跑，反而制造虚假安全感；
- 覆盖率数字对这类工具意义有限：真正危险的是**规则漏判**（该拦没拦），
  这是用例设计问题，不是行覆盖率问题；
- 铁律七的豁免机制（结构性不可达逐条标注）本就为此设计，硬凑 100%
  会催生无断言的"刷覆盖"测试。

**折中（agent 建议，待人工确认）**：纯逻辑（登记表结构校验、精确版本
正则、blocked 匹配、发现式扫描、markdown 链接/slug 规则、`_semver`
比较、bench/coverage 阈值判定）100% 行覆盖 + 关键分支用例；网络/子进程
胶水段打桩测"调用形状"，异常分支按铁律七逐条 `# pragma: no cover` 标注
豁免，禁止整文件排除。

**待决点**：pytest 挂进哪条闸门（`check:py` 追加、还是新命令
`check:scripts`）；进不进 `check:meta`；覆盖率是否进 coverage_gate。

## 问题三：目录命名（scripts / manage / control）

**正方（改名 manage/ 或 control/）**：

- "scripts" 太泛，不表达"治理工具集"的身份；manage/control 更点题。

**反方（留 scripts/）**：

- `scripts/` 被钉死在：根 `package.json` 全部命令、`ci.yml`、登记表
  `pin_location`、AGENTS/CONTRIBUTING/scripts README、workspace-layout
  spec、install 脚本互引——改名波及面全仓，收益只有"好看"；
- "管理入口"职责已有归属：根 `package.json` 的 `check:*`/`fix:*` 就是
  门面，AGENTS.md 明文"对称命令以根 package.json 为唯一定义处"；
  再造 `manage.py` 调度器 = 第二个命令真相源，必漂移（违反登记表
  唯一真相源的同款理由）；
- 命名是名字不是契约，位置语义靠 README 表达即可。

**待决点**：无强烈改名动机，倾向维持；若改，必须与问题一合并成一次
结构性 change，禁止单独折腾。

## 问题四：脚本自身的升级管理

**现状（反方认为无需新机制）**：脚本升级 = 改代码本身，走现有闸门 + git
即可；脚本依赖的外部工具版本（ruff/pytest）由 `python/uv.lock` 管，
`check:outdated` 已覆盖；脚本调用的上游工具链由 dependency-upgrade spec
全套机制管。没有缺口。

**正方（仍有可议空间）**：闸门之间有无执行顺序依赖（如 check:meta 内
六闸门顺序）是否需要显式声明与对账；脚本内硬编码的 URL/正则（如
endoflife cycle、npm dist-tag）有无"过期"概念需要体检。

## 落地形态（四问合并）

改动触及 workspace-layout spec（目录结构）、ci-matrix spec（若加 CI job）、
dependency-upgrade spec（若加钉版点）、根 package.json 命令面——属结构性
升级，MUST 单独开 OpenSpec change（暂名 `add-scripts-test-harness`，
命名本身也是待议产物，不作数），待四问拍板后 propose。最小可执行切片：
先只做问题二（纯逻辑单测 + 豁免标注 + pytest 接线），不动目录、不建
uv 项目——测试体系立起来后，问题一/三的"要不要搬家"再议才有底气。
