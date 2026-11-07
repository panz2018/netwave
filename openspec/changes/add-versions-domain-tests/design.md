# Design

## Context

动机见 proposal.md - Why。现状约束：

- 测试发现与执行已就位：根 `pyproject.toml` 配置 `testpaths`
  指向 `scripts/tests`、`pythonpath` 指向 `scripts/versions`，`pnpm check:py`
  已跑 `uv run pytest --cov=scripts/versions --cov-report=term`——新测试
  文件放进 `scripts/tests/` 即自动进闸门，无需改 `package.json`/`ci.yml`。
- `lib/repository.py` 的函数全部显式接收 `root` 参数（可注入是现成惯例）；
  但 `lib/latest.py` 的 `find_uv_projects`/`action_refs` 用模块级 `ROOT`。
- `check_outdated.py` 的探针集合（`PROBES`）与四段流程写在门面里；
  `check_versions.py` 的 `main()` 聚合 `all_laws` 结果并决定退出码。
- 全仓 `scripts/` 无任何 mock、无任何覆盖率豁免标注——本 change 立两种
  先例（依赖替换写法、离线防护）。

## Goals / Non-Goals

**Goals:**

- `lib/latest.py` 全函数、`lib/repository.py` 剩余发现函数、
  `lib/rules.py` 的 `summary`/`all_laws`、两个门面的 `main()` 有测试。
- "测试不联网"机器强制：忘做依赖替换的用例在本地和 CI 当场报错。
- 关键判定经反向验证证明测试有效（不是永远绿的摆设）。

**Non-Goals:**

- 设计层面排除：覆盖率阈值接入（`--cov-fail-under` 不加）、豁免标注、
  `fetch_json`/`run_cmd` 的真实网络/真实环境验证（测的是调用形状，
  不证真环境能跑）。

## Decisions

1. **门面测法：进程内调 `main()` + `capsys` 抓输出**，不起子进程。
   理由：`ROOT` 按文件位置算、不随 `cwd` 变，子进程方案注入不了假仓库；
   退出码经 `sys.exit(main())` 的契约用 `SystemExit`/返回值断言覆盖。
   备选（子进程真跑）否决：注入不可行。

2. **依赖替换统一 pytest `monkeypatch` + 手写假函数**，不用
   `unittest.mock`。理由：仓库零 mock 先例，选轻的一套；"断言 URL/命令串"
   用闭包收集调用参数到 list 即可；monkeypatch 自动还原不污染他例。

3. **`ROOT` 注入走测试侧**：用 monkeypatch 把 `lib.latest.ROOT`
   换成 tmp_path，不改生产签名。备选（给函数加 `root` 参数对齐
   `lib/rules.py` 风格）否决：改签名波及门面调用方，超出补测范围；
   若日后注入点变多再统一收编，另开 change。

4. **离线防护放 `scripts/tests/conftest.py`**（autouse fixture 替换
   `socket.socket`，真联网即抛错）。层级选 `scripts/tests/` 而非
   `scripts/tests/versions/`：一次立规矩覆盖未来所有闸门脚本测试域，
   且不误伤 `python/` 侧可能联网的测试。`run_cmd` 走子进程不受 socket
   影响，由依赖替换保证不真跑命令。

5. **门面测试文件位置**：`scripts/tests/versions/` 下的
   `test_check_versions.py`、`test_check_outdated.py`——与被测文件目录位置
   一一对应（`lib/` 下模块的测试对应放 `lib/` 子目录）。

6. **`run_cmd` 单独测三例**（人工裁决）：`echo hello` → rc 0 + 输出；
   `netwave-no-such-cmd` → rc 非 0 + 错误文字进返回值（验证 stdout+stderr
   拼接与失败不炸）；内部执行抛异常 → rc 125 不崩溃（"体检任何情况不崩"
   契约）。

7. **反向验证范围**（铁律二对"补测已存在代码"的落法）：挑判定逻辑——
   四律各一处、`is_version_tag`、`is_outdated` 相关、两门面退出码——
   故意改坏被测代码确认对应测试变红再改回，验证项逐条记入 tasks.md。
   备选（全量反向验证）否决：费时且边际收益低。

8. **覆盖率维持只报数**：完成时跑
   `uv run pytest --cov=scripts/versions --cov-report=term-missing`，
   剩余未覆盖行号贴 tasks.md 完成记录，作为日后阈值讨论的唯一数据。

## Risks / Trade-offs

- [依赖替换测出的"绿"不证明真环境能跑] → 接受：本次目标是防规则漏判与
  调用形状回归；真实联网行为由人工跑 `pnpm check:outdated` 时暴露，
  探针失败本身有降级 WARN 用例钉住。
- [socket 防护可能误伤未来确需联网的 scripts 测试] → 概率低（scripts
  闸门域设计上全离线）；真出现时在用例内显式恢复 socket 并注明理由。
- [约 43 例一次性落地 review 负担大] → tasks.md 按模块分节提交，
  每节独立可验证；反向验证放最后统一做。
- [monkeypatch `ROOT` 依赖模块属性可替换性] → `latest.py` 以
  `from lib.repository import ROOT` 导入，名字绑定在 `lib.latest` 模块上，
  patch `lib.latest.ROOT` 有效；用例内以一条 smoke 断言确认替换生效。

## Migration Plan

纯新增测试 + 一句 README 措辞，无部署/迁移；回滚 = git revert。

## Open Questions

（无——范围、测法、防护、覆盖率口径均已在 grilling 会话逐条拍板。）
