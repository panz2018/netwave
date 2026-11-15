# 任务：考古文字清理与门禁扩面

## 1. 门禁脚本（red 先于 green）

- [ ] 1.1 新增 `scripts/tests/test_check_comments.py`（沿用
      `test_coverage_gate.py` 先例）：六项固定形态标记各一条命中用例
      （`LL-` 编号、`CI run` + 六位以上数字、`Re-enabled`/`重新启用` + 日期、
      `已标定`、`design decision`/`design D` + 数字、开发文档指针）；
      三类负例（裸日期 `rustc 1.99.1 (abc1234 2026-10-13)`、
      `Deprecated: use X instead`、豁免路径 `pnpm-lock.yaml`/
      `openspec/config.yaml`/archive `.openspec.yaml`）；
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

- [ ] 2.1 改写 `.github/workflows/ci.yml` 全部考古注释：删 `LL-011`/
      `LL-034`/`LL-047` 编号、`CI run 43603143333`、
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

- [ ] 3.1 `openspec/specs/api-contract/spec.md` L63：`upload 概念全仓废止`
      改写为当前契约声明（"无 `upload` 概念"），归因删、结论留。
- [ ] 3.2 `openspec/specs/ci-matrix/spec.md` L119-120：`口径废止…被…推翻`
      改写为只陈述当前采集口径；L230：`不再是` 改写为当前事实。
- [ ] 3.3 `openspec/specs/memory-lifecycle/spec.md` L40：`两表…废止`
      改写为当前结构表述。
- [ ] 3.4 `openspec/specs/oracle-harness/spec.md` L39：`…废止`
      改写为当前命名契约。
- [ ] 3.5 `openspec/specs/workspace-layout/spec.md` L19：`testdata/ 废止`
      改写为当前布局事实。
- [ ] 3.6 `openspec/specs/zero-copy-roundtrip/spec.md` L18/L22/L23/L85：
      四处 `废止` 叙述改写为当前契约（无分流、无 `_` 同步函数、基准文件
      命名现状）。
- [ ] 3.7 保留判定（不改，留证据）：`touchstone-core/spec.md` L443
      `不再是合法选项行` 为输入行为描述、`project-governance/spec.md`
      L701/L722 `契约废止` 为规则生命周期判据的当前规则——均非考古；
      在 1.1 测试中落为负例锁定。
      验证：`pnpm check:md` 绿；改写前后逐条 diff 自查结论未丢。

## 4. 治理 spec 与文档同步

- [ ] 4.1 确认 specs delta 与实现一致：跑 `openspec validate` 加
      `--strict` 对 `purge-archaeology-refs`，退出码 0。
- [ ] 4.2 删除 `Plan/考古文字清理-2026-11-14.md`（结论已全部吸收进
      本 change 工件）。验证：`pnpm check:md` 绿。
- [ ] 4.3 三态时效检查（更新/新增/退役）：本 change 更新
      `project-governance`（delta）、改写 6 个能力 spec 措辞、无退役；
      结论留痕本节完成记录。

## 5. 收尾闸门

- [ ] 5.1 全量闸门：`pnpm check`（含 check:md/check:ts/check:rs/check:py/
      check:meta）退出码 0。
- [ ] 5.2 三轴 review：按 governance spec「元规则 review 三轴」
      （Standards/Spec/Lessons）对照本 change 工件审实现 diff，
      Standards 轴含语义考古 AI 全面审查（常驻文档+代码+配置注释，
      archive/账本/Plan 豁免），硬伤清零。
- [ ] 5.3 `pnpm check:outdated` 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化所报 LAG，复跑至退出码 0。
