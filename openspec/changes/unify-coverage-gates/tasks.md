# Tasks

## 1. 事实 spike（未验证项先落地，结论写回 design.md）

- [ ] 1.1 本地验证 show-env 三步链能否让 napi build 吃到插桩参数：在仓库根跑
      `bash -c 'eval "$(cargo llvm-cov show-env --sh --no-cfg-coverage)" && cargo llvm-cov clean --workspace && pnpm -C typescript build:native:debug && pnpm -C typescript test:native && cargo llvm-cov report --codecov --output-path coverage/coverage-native.json --ignore-filename-regex "/core/"'`，验证 `coverage/coverage-native.json` 含 `typescript/native/src/` 的行且命中数 > 0（若全为 0 即未透传，改用 napi 配置注入 `RUSTFLAGS` 后复测）；结论（采用路径 + 证据数字）写回 design.md 决策 1
- [ ] 1.2 本地验证 profraw 多进程不互相覆盖：同 1.1 运行后 `ls target/llvm-cov/` 确认每个 pytest/vitest 进程各有一份 profraw（文件名含 `%p` 展开的 pid），`cargo llvm-cov report` 计数非零；若单文件覆盖则显式设 `LLVM_PROFILE_FILE` 含 `%p` 复测；结论写回 design.md 风险项
- [ ] 1.3 本地验证 maturin 侧透传：`bash -c 'eval "$(cargo llvm-cov show-env --sh --no-cfg-coverage)" && cargo llvm-cov clean --workspace && uv run --project python maturin develop && uv run --project python pytest python && cargo llvm-cov report --codecov --output-path coverage/coverage-python.json --ignore-filename-regex "/core/"'` 后报告含 `python/src/` 行且命中 > 0；结论写回 design.md

## 2. 阅卷脚本调用口径先测（red 先于 green）

- [ ] 2.1 在 `scripts/tests/` 新增 `coverage_gate` 多报告调用单测：构造两份最小 codecov.json fixture（一份 core 全命中、一份胶水含一行缺），断言分别以地板 100 调用时前者 exit 0、后者 exit 1，且缺行清单打印出缺的那一行；先跑 `uv run pytest scripts/tests -k coverage_gate` 确认新用例失败（脚本尚无该行为时 red），再确认现脚本已满足则记录"零改动即绿"的实证输出
- [ ] 2.2 同 2.1 补 `--ignore-filename-regex` 口径断言：fixture 含 `core/src/` 与 `python/src/` 两文件路径，断言胶水报告只计 `python/src/` 的行（core 行不出现在缺行清单），验证 core 与胶水不重复计分；验证命令同 2.1

## 3. rust job：合并命令 + 全平台

- [ ] 3.1 改 `.github/workflows/ci.yml` rust job：删除 `car go test` 步骤与覆盖率步骤的 `if: matrix.target == 'linux-x64'`，合并为单步 `cargo llvm-cov -p netwave --codecov --output-path coverage/coverage-core.json` + `cargo build --workspace --all-targets` + `python3 scripts/coverage_gate.py coverage/coverage-core.json 0`（首轮地板 0，见 6.3 翻回 100），`shell: bash`；验证：本地 `cargo llvm-cov -p netwave --codecov --output-path coverage/coverage-core.json` 与 `cargo build --workspace --all-targets` 各自 exit 0，且 core 测试仅执行一遍（日志中同一测试二进制名只出现一次）
- [ ] 3.2 rust job 加 upload-artifact 步骤留存 `coverage/coverage-core.json`（artifact 名含 matrix target）；验证：本地 push 后 CI 四格各出现该 artifact 且可下载

## 4. python job：胶水覆盖率扩面（地板 0 标定）

- [ ] 4.1 改 python job：加 `bash scripts/install_cargo_llvm_cov.sh` 步骤（复用现成脚本，不复制第二份），测试步骤改为单 step `shell: bash`：`eval "$(cargo llvm-cov show-env --sh --no-cfg-coverage)"` → `cargo llvm-cov clean --workspace` → `uv run maturin develop` → `uv run pytest --cov=netwave --cov-fail-under=100` → `cargo llvm-cov report --codecov --output-path coverage/coverage-python.json --ignore-filename-regex '/core/'`，随后 `python3 scripts/coverage_gate.py coverage/coverage-python.json 0`；pytest 命令与 `--cov-fail-under` 参数原样保留（python 层门槛不动）；show-env/report 与构建测试 MUST 同 step；验证：本地按 1.3 命令跑通且 pytest 全绿、报告含 `python/src/` 行
- [ ] 4.2 python job 加 upload-artifact 留存 `coverage/coverage-python.json`；验证：CI python 四格各出该 artifact

## 5. node job：胶水覆盖率扩面（地板 0 标定）

- [ ] 5.1 改 node job：加 `bash scripts/install_cargo_llvm_cov.sh` 步骤（并入现有 wasm toolchain 安装步之后，独立步骤保 PATH 生效），native 构建+测试改为单 step `shell: bash`：`eval "$(cargo llvm-cov show-env --sh --no-cfg-coverage)"` → `cargo llvm-cov clean --workspace` → `pnpm -C typescript build:native:debug` → `pnpm -C typescript test:native --coverage` → `cargo llvm-cov report --codecov --output-path coverage/coverage-native.json --ignore-filename-regex '/core/'`，随后 `python3 scripts/coverage_gate.py coverage/coverage-native.json 0`；show-env/report 与构建测试 MUST 同 step；vitest 阈值仍由 `vitest.native.config.ts` 单源；验证：本地按 1.1 命令跑通、vitest 全绿、报告含 `typescript/native/src/` 行
- [ ] 5.2 确认改造后 `pnpm check:meta` 仍绿（`scripts/check_ci.py` 要求 `typescript test:native` 字面出现在 ci.yml——`bash -c` 内保留该字面）；验证：`timeout 300 pnpm check:meta` 退出码 0
- [ ] 5.3 node job 加 upload-artifact 留存 `coverage/coverage-native.json`；验证：CI node 四格各出该 artifact
- [ ] 5.4 确认跨绑定对拍未被破坏：node job 的 `pnpm check:cross` 步骤位置与参数不变（在 maturin develop + stub_gen 之后），本地 `timeout 300 pnpm check:cross` 全绿（含内置反同义自检与跨端词汇类型闸门）

## 6. 标定轮收数字与地板启用（依赖 3/4/5 的 CI 首轮）

- [ ] 6.1 下载首轮 CI 的四格 core + 双胶水共六份报告，逐格记录行覆盖率与缺行清单到本 change 目录 `calibration.md`；验证：六份数字齐全，无格缺报
- [ ] 6.2 逐条定性缺行：真缺口 → 补测试（python 补 pytest 用例、native 补 vitest 用例、core 补 `core/tests/` 用例，先跑失败用例再让它通过）；结构性不可达 → 按铁律七逐条标注（`#[cfg(not(coverage))]` / `# pragma: no cover` / `/* v8 ignore start/stop */`）并在标注处附一句理由；验证：`timeout 300 pnpm check` 绿 + 本地重跑对应覆盖率命令缺行清零
- [ ] 6.3 把三处阅卷地板参数由 0 翻至 100（ci.yml：core、python、native 各一处，数值唯一定义处）；验证：CI 全绿且三域阅卷输出均为 `floor 100`

## 7. spec、账本与文档收口（LL-034）

- [ ] 7.1 本 change 的 `specs/ci-matrix/spec.md` delta 与主 spec 口径复核（五格矩阵、铁律七两处 MODIFIED + 三条 ADDED），确认命令字面与 ci.yml 实跑一致、无残留"绑定 crate 不进 llvm-cov job"旧表述；验证：`grep -rn "工具作用域分离" openspec/specs/` 无命中（archive 后）
- [ ] 7.2 登记 LL：口径漂移假绿类（`cargo test` 退役后 doctest 无人执行的前提、show-env 未透传致胶水假 0%）+ 本轮决策（合并/全平台/胶水扩面/命令内联不建根脚本），写入对应 scope 分片并同步 INDEX；验证：`pnpm check:md` 绿且 INDEX 与分片条目一致
- [ ] 7.3 波及文档同步：`Plan/覆盖率统一-2026-11-12.md`（已定案章节删除，S5/S1 延后项保留）、`Plan/闸门重排-2026-11-12.md`（T1/T2/T4 标延后、T1/T2 命令构成更新为内联口径）、CONTRIBUTING.md、scripts/README.md、`Plan/测试规划.md` 相关行；验证：`pnpm check:md` 退出码 0
- [ ] 7.4 `.gitignore` 复核：确认 `coverage/`、`*.profraw` 已在列（现成），旧名 `codecov.json` 行在主 spec 退役后清理；验证：`git status --porcelain` 在本地跑完覆盖率后无未忽略的 json/profraw

## 8. 终审闸门

- [ ] 8.1 三轴 review：按 governance spec「元规则 review 三轴」（Standards / Spec / Lessons）对照本 change 四件工件审实现 diff（ci.yml、scripts/tests、spec 修订、文档同步），硬伤清零；验证：review 结论留痕本 change 目录，无未决硬伤
- [ ] 8.2 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍，含全局 CLI/直装工具的机器级升级；上游 bug/不兼容登记回退不阻塞，设计级适配、restrictions.json 破损、流程走不通才停下报告；下限变更等人工发起）；消化后复跑 `pnpm check:outdated` 至退出码 0（SUMMARY 归零）才算完成

## Workflow follow-up

- 提交全景表（分组 → 文件 → commit 标题）在闸门绿后给出，等人工点名提交；禁止直推 main。
- 归档前按 archive guidance 执行 Plan/ 瘦身检查与 openspec/specs/ 三态时效检查。
- 本 change 经人工点名（2026-11-13）**跳过** archive guidance 中"归档完成后执行 archive-health-check 五维只读体检"一项，归档完成即收口。
- 延后项去向：根聚合入口 `test:*`（闸门重排档 T1/T2/T4）、wasm 胶水覆盖率 spike（S5）——各自独立点名立项，不在本 change。
