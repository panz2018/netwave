# Tasks

## 1. 改名（先做，后续任务基于新路径）

- [x] 1.1 `git mv scripts/version_pins.json scripts/versions.json`、
      `git mv scripts/check_version_pins.py scripts/check_versions.py`；
      改 `check_versions.py` 内 `REGISTRY` 常量指向 `scripts/versions.json`，
      更新 JSON `$comment` 措辞（内部键名 `pins`/`pin_location`/`categories` 不动）
- [x] 1.2 更新接线与活文档引用：根 `package.json` `check:meta`、`AGENTS.md`、
      `CONTRIBUTING.md`、`Plan/测试规划.md`（oracle uv 环境落地清单表）、
      活跃 change `upgrade-python-3-15` 的 `proposal.md` 与 `tasks.md`
- [x] 1.3 全仓 grep 确认无残留旧文件名（`version_pins`、`check_version_pins`），
      归档区 `openspec/changes/archive/` 命中属冻结历史保留不动；
      跑 `pnpm check:md` 退出 0

## 2. 登记表结构与闸门层（red 先于 green）

- [x] 2.1 red：临时给 `scripts/versions.json` 某条目挂非法 `blocked`
      （范围写法 `>=1.2`、缺 `reason`、非法类型），运行 `python3 scripts/check_versions.py`
      确认 FAIL 并报出具体条目与原因；另构造 `ci-actions` 挂 `blocked` 确认 FAIL
- [x] 2.2 green：`check_versions.py` 实现 `blocked` 结构校验——每项含精确版本号
      `version`（拒绝 `>=`/`<=`/`~`/`*`/`x` 等范围通配写法）、必填 `reason`、
      可选 `issue`；`ci-actions` 条目出现 `blocked` 即 FAIL；
      重跑 2.1 的非法输入确认全部 FAIL，删除非法输入后确认 PASS
- [x] 2.3 red：构造当前钉版命中黑名单的漂移输入（如给 `node` 相关条目挂
      `blocked` 且版本等于 `packageManager`/`.python-version`/workflow 全 pin tag
      之一的当前值），运行闸门确认 FAIL 并指出"停在已知坏版本"及原因
- [x] 2.4 green：`check_versions.py` 实现闸门层黑名单——读取仓库内可读当前值
      （`rust-toolchain.toml` channel、`packageManager`、各 `.python-version`、
      workflow 全 pin 的 action tag、`discovered:` 成员值、CI python 矩阵格），
      命中所属条目 `blocked` 即 FAIL；`machine:` 条目跳过黑名单检查；
      重跑 2.3 确认 FAIL，移除构造输入后 `pnpm check:meta` 全绿

## 3. 体检层黑名单过滤

- [x] 3.1 red：临时给某全局 CLI 条目挂 `blocked`（版本 = 其当前最新 release），
      运行 `python3 scripts/check_outdated.py` 确认该段不再推荐该版本，
      改报次新可用版为 target 并标注 blocked 原因
- [x] 3.2 green：`check_outdated.py` 读取 `scripts/versions.json`，
      在脚本内维护探测名↔条目名映射表（`node`→`node-global`、`npm`→`npm-global`、
      `pnpm`→`pnpm`、`uv`→`uv-global`、`rustup`→`rustup-global`、
      `openspec`→`openspec-global`、`markdownlint-cli2`→`markdownlint-cli2-global`、
      `wasm-pack`/`binaryen`/`cargo-llvm-cov` 同名；`rustc` 无条目不消费），
      对可枚举版本列表的段（全局 CLI、GitHub 直装工具、cargo 子命令、
      CI actions 的 semver tag、python 运行时 pin）过滤 blocked 并改报 target；
      lockfile 三段（pnpm / cargo / uv dry-run）不做过滤；重跑 3.1 确认通过
- [x] 3.3 全堵兜底：构造某条目全部候选版本均在 `blocked` 的输入，
      确认体检输出 `no known good target` 并保持落后标记、不推荐任何版本；
      无法映射到条目的 `blocked` 条目输出警告（防映射表漂移静默失效）；
      清理全部临时构造输入
- [x] 3.4 `check_outdated.py` 保持纯标准库、人工触发定位不变：
      确认 `ci.yml` 与 `pnpm check` 均不含该命令，`pnpm check:py` 全绿

## 4. Plan 收口与文档终检

- [x] 4.1 `Plan/测试规划.md`：删除问题二整节；待议节标题改为两问按内容命名
      （"过期检查门禁化"、"配对版本校验"），落地形态改"两问合并"；
      机器人安全阀（自动化提议升级 MUST NOT 推荐 blocked 版本）作为备查要求
      并入"过期检查门禁化"节
- [x] 4.2 跑 `pnpm check:md` 与 `openspec validate --specs`，
      修复锚点/链接问题（标题改名造成的断链当场修）
- [x] 4.3 全闸门验收：`pnpm check:meta`、`pnpm check:py` 全绿；
      `openspec status --change add-blocked-version-registry` 显示工件齐备
