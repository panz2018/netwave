# Tasks

## 1. 摘要行去黑话与四律计数（TDD 先 red）

- [ ] 1.1 red：改 `scripts/tests/versions/lib/test_rules.py` `TestSummary`
      逐字断言为 design 决策 1 的新措辞（夹具口径：rust 1 members、
      python 1 projects、pnpm 1 manifests、ci 1 python-version files，
      toolchain 替代 pin），并新增计数随夹具变化的断言（加第二个
      pyproject 后 python 计数变 2）。验证：跑 pytest 该用例 FAIL。
- [ ] 1.2 green：重写 `scripts/versions/lib/rules.py` `summary()`——四律计数从
      `lib/repository.py` 现成函数取（`rust_versions` / `find_files`+`is_python_project`
      / `find_package_managers` / `find_python_versions`），`pin`→`toolchain`，
      前缀 `version laws OK:` 保留。验证：1.1 用例 PASS。

## 2. 取数口径剥壳（段 2/3 标记的前置）

- [ ] 2.1 red：在 `scripts/tests/versions/lib/` 新增 `_clean_version` 用例，
      覆盖实测输出形状：uv 带括号架构后缀、rustc/rustup 带 hash+日期括号、
      wasm-pack 裸版本、wasm-opt 带 version 前缀、markdownlint-cli2 带
      markdownlint 括号、node 带 v 前缀，均剥成纯 semver；不可解析串返回
      None。验证：FAIL（函数不存在）。
- [ ] 2.2 green：在 `scripts/versions/lib/latest.py` 实现 `_clean_version`
      （剥工具名前缀、`v` 前缀、括号后缀；取首个 semver 形状 token）。验证：2.1
      PASS。

## 3. check_outdated 输出格式（TDD 先 red）

- [ ] 3.1 red：改 `scripts/tests/versions/test_check_outdated.py`——python 行
      断言改为 design 决策 2 的形状：行首字段名 python-version + 路径列、
      中段箭头 `-> latest stable`、尾部状态标记；段 2/3 断言每比较行尾部带
      OK/LAG/?；旧 WARN 行文案 python runtime pins 改为 python-version pins。
      验证：FAIL。
- [ ] 3.2 green：改 `scripts/versions/check_outdated.py`——python 行
      `python-version {path:24s} {cur:8s} -> latest stable {latest:8s} {mark}`；
      段 2/3 行尾补 `OK`/`LAG`（`is_outdated` 比较剥壳后版本，不可解析标 `?`）；
      WARN 行同步改名。验证：3.1 PASS 且全量 `uv run pytest scripts/tests` PASS。
- [ ] 3.3 实跑核对：`uv run python scripts/versions/check_versions.py` 输出新
      摘要行（四律计数、零 `pin`）；`uv run python scripts/versions/check_outdated.py`
      段 2/3 每行带标记、python 行无错位、退出码 0。

## 4. 文档与闸门同步

- [ ] 4.1 核对 `scripts/versions/README.md` 既有描述不变旧（`WARN` 降级、退出码
      段；不补示例输出行——人工裁决）。
- [ ] 4.2 全仓 grep `pin` 残留于 versions 域输出面（`print` 语句内），确认清零
      （注释/文档中"钉版"语义的 pin 用法不在本 change 范围）。
- [ ] 4.3 闸门：`uv run pytest scripts/tests` 全 PASS、`pnpm check:meta` 全绿、
      `pnpm check:md` 退出 0。
- [ ] 4.4 Plan/ 同步：删除 `Plan/软件升级.md`「摘要去黑话」已完成内容（待开
      change→已开并定案措辞），「落地形态汇总」对应行改为本 change 状态；删后
      `pnpm check:md`。

## Workflow follow-up

- apply 完成后按 openspec/config.yaml apply 钩子：Plan/ 对应章节当场删除 +
  `pnpm check:md`；扫 openspec/specs/ 三态时效留痕本文件完成记录。
- 归档时（`/opsx:archive`）：Plan/ 瘦身检查、specs/README.md 路由核对。
