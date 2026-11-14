# Tasks

## 1. 事实 spike（未验证项先落地，结论写回 design.md）

- [x] 1.1 本地验证 show-env 三步链能否让 napi build 吃到插桩参数：在仓库根跑
      `bash -c 'eval "$(cargo llvm-cov show-env --sh --no-cfg-coverage)" && export NODE_OPTIONS=--expose-gc && cargo llvm-cov clean --workspace && pnpm -C typescript build:native:debug && pnpm -C typescript test:native --pool=threads --execArgv="" --no-file-parallelism && cargo llvm-cov report --target aarch64-unknown-linux-gnu --codecov --output-path coverage/coverage-native.json --ignore-filename-regex "/core/"'`，验证 `coverage/coverage-native.json` 含 `typescript/native/src/` 的行且命中数 > 0（若全为 0 即未透传，改用 napi 配置注入 `RUSTFLAGS` 后复测）；结论（采用路径 + 证据数字）写回 design.md 决策 1（实证通过：vitest 7/7、native 行命中 222/241=92.12%；report 须带 `--target`、vitest 须 threads 池串行 + `NODE_OPTIONS=--expose-gc`，详见决策 1 spike 结论）
- [x] 1.2 本地验证 profraw 多进程不互相覆盖：同 1.1 运行后 `ls target/llvm-cov/` 确认每个 pytest/vitest 进程各有一份 profraw（文件名含 `%p` 展开的 pid），`cargo llvm-cov report` 计数非零；若单文件覆盖则显式设 `LLVM_PROFILE_FILE` 含 `%p` 复测；结论写回 design.md 风险项（实证通过：show-env 默认模板 `netwave-%p-%18m.profraw` 已含 pid，native 侧 3 份 profraw、3 个唯一 pid 不互覆，report 计数 222/241 非零，无需显式补 `%p`）
- [x] 1.3 本地验证 maturin 侧透传：`bash -c 'eval "$(cargo llvm-cov show-env --sh --no-cfg-coverage)" && cargo llvm-cov clean --workspace && (cd python && uv run maturin develop) && (cd python && uv run pytest --cov=netwave --cov-fail-under=100) && cargo llvm-cov report --codecov --output-path coverage/coverage-python.json --ignore-filename-regex "/core/"'` 后报告含 `python/src/` 行且命中 > 0；结论写回 design.md（实证通过：pytest 全绿、profraw 17 份、`python/src/lib.rs` 行命中 326/351=92.88%。关键：maturin MUST 在 `python/` 目录跑（否则误读仓库根 `pyproject.toml`——根 pyproject 无 build-system 段直接报错），report 回仓库根出；maturin 不带 `--platform`/`--target`，对象落 host `target/debug`，report 无需 `--target`）

## 2. 阅卷脚本调用口径先测（red 先于 green）

- [x] 2.1 在 `scripts/tests/` 新增 `coverage_gate` 多报告调用单测：构造两份最小 codecov.json fixture（一份 core 全命中、一份胶水含一行缺），断言分别以地板 100 调用时前者 exit 0、后者 exit 1，且缺行清单打印出缺的那一行；先跑 `uv run pytest scripts/tests -k coverage_gate` 确认新用例失败（脚本尚无该行为时 red），再确认现脚本已满足则记录"零改动即绿"的实证输出（实证：现脚本已满足——首轮即 4 passed，零改动即绿；fixture 为 llvm-cov 真实 codecov 形状 `{"coverage": {path: {line: "hit/total"}}}`；`pyproject.toml` pythonpath 补 `scripts` 使顶层闸门可 import）
- [x] 2.2 同 2.1 补 `--ignore-filename-regex` 口径断言：fixture 含 `core/src/` 与 `python/src/` 两文件路径，断言胶水报告只计 `python/src/` 的行（core 行不出现在缺行清单），验证 core 与胶水不重复计分；验证命令同 2.1（实证：胶水报告输出不含 `core/src`，只计胶水行——regex 在 llvm-cov 导出层剔除，gate 层天然不重复计分）

## 3. rust job：合并命令 + 全平台

- [x] 3.1 改 `.github/workflows/ci.yml` rust job：删除 `cargo test --workspace` 步骤与覆盖率步骤的 `if: matrix.target == 'linux-x64'`，合并为单步 `cargo llvm-cov -p netwave --codecov --output-path coverage/coverage-core.json` + `cargo build --workspace --all-targets` + `python3 scripts/coverage_gate.py coverage/coverage-core.json 0`（首轮地板 0，见 6.3 翻回 100），`shell: bash`；验证：本地 `cargo llvm-cov -p netwave --codecov --output-path coverage/coverage-core.json` 与 `cargo build --workspace --all-targets` 各自 exit 0，且 core 测试仅执行一遍（日志中同一测试二进制名只出现一次）（实证：cov exit 0、959/959=100%；build exit 0；ci.yml YAML 合法）
- [ ] 3.2 rust job 加 upload-artifact 步骤留存 `coverage/coverage-core.json`（artifact 名含 matrix target）；验证：本地 push 后 CI 四格各出现该 artifact且可下载（步骤已加 `coverage-core-${{ matrix.target }}`，CI 验证待 push）

## 4. python job：胶水覆盖率扩面（地板 0 标定）

- [x] 4.1 改 python job：加 `bash scripts/install_cargo_llvm_cov.sh` 步骤（复用现成脚本，不复制第二份），测试步骤改为单 step `shell: bash`（`working-directory` 回仓库根，因 report 需访问根 `target/`）：`eval "$(cargo llvm-cov show-env --sh --no-cfg-coverage)"` → `cargo llvm-cov clean --workspace` → `(cd python && uv sync && uv run maturin develop)` → `(cd python && uv run pytest --cov=netwave --cov-fail-under=100)` → `cargo llvm-cov report --codecov --output-path coverage/coverage-python.json --ignore-filename-regex '/core/'`，随后 `python3 scripts/coverage_gate.py coverage/coverage-python.json 0`；pytest 命令与 `--cov-fail-under` 参数原样保留（python 层门槛不动）；maturin/pytest MUST 在 `python/` 子目录跑（见 task 1.3：根 pyproject 无 build-system）；show-env/report 与构建测试 MUST 同 step；验证：本地按 1.3 命令跑通且 pytest 全绿、报告含 `python/src/` 行（实证：见 1.3，326/351=92.88%）
- [ ] 4.2 python job 加 upload-artifact 留存 `coverage/coverage-python.json`；验证：CI python 四格各出该 artifact（步骤已加 `coverage-python-${{ matrix.os }}-${{ matrix.python-version }}`，CI 验证待 push）

## 5. node job：胶水覆盖率扩面（地板 0 标定）

- [x] 5.1 改 node job：加 `bash scripts/install_cargo_llvm_cov.sh` 步骤（并入现有 wasm toolchain 安装步之后，独立步骤保 PATH 生效），native 构建+测试改为单 step `shell: bash`：`eval "$(cargo llvm-cov show-env --sh --no-cfg-coverage)"` → `export NODE_OPTIONS=--expose-gc` → `cargo llvm-cov clean --workspace` → `pnpm -C typescript build:native:debug` → `pnpm -C typescript test:native --coverage --pool=threads --execArgv="" --no-file-parallelism` → `cargo llvm-cov report --target "$(rustc -vV | sed -n 's/^host: //p')" --codecov --output-path coverage/coverage-native.json --ignore-filename-regex '/core/'`，随后 `python3 scripts/coverage_gate.py coverage/coverage-native.json 0`；原独立 `vitest (native, coverage 100)` 步删除（已并入本步，`test:native` 字面保留在合并步内）；show-env/report 与构建测试 MUST 同 step；vitest 参数与 `--target` 为 task 1.1 实证必需（worker 线程不倒 profraw、napi 对象在 triple 子目录，见 design.md 决策 1）；vitest 阈值仍由 `vitest.native.config.ts` 单源；验证：本地按 1.1 命令跑通、vitest 全绿、报告含 `typescript/native/src/` 行（实证：threads 池下 v8 覆盖仍 100%（All files 四项全 100）、vitest 7/7、llvm 胶水 222/241=92.12%）
- [x] 5.2 确认改造后 `pnpm check:meta` 仍绿（`scripts/check_ci.py` 要求 `typescript test:native` 字面出现在 ci.yml——合并步内保留该字面）；验证：`timeout 300 pnpm check:meta` 退出码 0（实证：exit 0，CI gate check OK: 3 test scripts all wired）
- [ ] 5.3 node job 加 upload-artifact 留存 `coverage/coverage-native.json`；验证：CI node 四格各出该 artifact（步骤已加 `coverage-native-${{ matrix.os }}-${{ matrix.node-version }}`，CI 验证待 push）
- [x] 5.4 确认跨绑定对拍未被破坏：node job 的 `pnpm check:cross` 步骤位置与参数不变（在 maturin develop + stub_gen 之后），本地 `timeout 300 pnpm check:cross` 全绿（含内置反同义自检与跨端词汇类型闸门）（实证：exit 0，SELF-CHECK PASS ×3 + vocab types OK + verbs OK）

## 6. 标定轮收数字与地板启用（依赖 3/4/5 的 CI 首轮）

- [ ] 6.1 下载首轮 CI 的四格 core + 双胶水共六份报告，逐格记录行覆盖率与缺行清单到本 change 目录 `calibration.md`；验证：六份数字齐全，无格缺报
- [ ] 6.2 逐条定性缺行：真缺口 → 补测试（python 补 pytest 用例、native 补 vitest 用例、core 补 `core/tests/` 用例，先跑失败用例再让它通过）；结构性不可达 → 按铁律七逐条标注（`#[cfg(not(coverage))]` / `# pragma: no cover` / `/* v8 ignore start/stop */`）并在标注处附一句理由；验证：`timeout 300 pnpm check` 绿 + 本地重跑对应覆盖率命令缺行清零
- [ ] 6.3 把三处阅卷地板参数由 0 翻至 100（ci.yml：core、python、native 各一处，数值唯一定义处）；验证：CI 全绿且三域阅卷输出均为 `floor 100`

## 7. spec、账本与文档收口（LL-034）

- [x] 7.1 本 change 的 `specs/ci-matrix/spec.md` delta 与主 spec 口径复核（五格矩阵、铁律七两处 MODIFIED + 三条 ADDED），确认命令字面与 ci.yml 实跑一致、无残留"绑定 crate 不进 llvm-cov job"旧表述；验证：`grep -rn "工具作用域分离" openspec/specs/` 无命中（archive 后）（核对：delta 命令字面与 ci.yml 实跑一致——core `-p netwave --codecov`、show-env `--no-cfg-coverage`、python `report --codecov`、native `report --target`；主 spec 旧表述现存 1 处，archive 同步时清除）
- [x] 7.2 登记 LL：口径漂移假绿类（`cargo test` 退役后 doctest 无人执行的前提、show-env 未透传致胶水假 0%）+ 本轮决策（合并/全平台/胶水扩面/命令内联不建根脚本），写入对应 scope 分片并同步 INDEX；验证：`pnpm check:md` 绿且 INDEX 与分片条目一致（登记：LL-092 外部驱动胶水覆盖率三坑、LL-093 口径漂移假绿，均入 ci.md + INDEX；本轮决策已落 design.md 决策 1-7）
- [x] 7.3 波及文档同步：`Plan/覆盖率统一-2026-11-12.md`（已定案章节删除，S5/S1 延后项保留）、`Plan/闸门重排-2026-11-12.md`（T1/T2 标延后、决策一标已定选乙、命令构成更新为内联口径）、CONTRIBUTING.md（覆盖率口径 + quick start 命令）、scripts/README.md（补 coverage_gate.py 行）、`Plan/测试规划.md` 工具行（补胶水采集）；验证：`pnpm check:md` 退出码 0（实证：五文件已同步，check:md 绿）
- [x] 7.4 `.gitignore` 复核：确认 `coverage/`、`*.profraw` 已在列（现成），旧名 `codecov.json` 行在主 spec 退役后清理；验证：`git status --porcelain` 在本地跑完覆盖率后无未忽略的 json/profraw（实证：coverage/、*.profraw、codecov.json 均在 .gitignore；本地跑完覆盖率后 git status 无未忽略 json/profraw。codecov.json 行暂留——主 spec 退役随 archive，现删会破旧口径）

## 8. 终审闸门

- [x] 8.1 三轴 review：按 governance spec「元规则 review 三轴」（Standards / Spec / Lessons）对照本 change 四件工件审实现 diff（ci.yml、scripts/tests、spec 修订、文档同步），硬伤清零；验证：review 结论留痕本 change 目录，无未决硬伤（结论落 `review.md`；自查修正 spec/design 的 doctest 措辞与 tasks 裸版本代号两处；CI artifact 下载与标定轮数字属 push 后流程后置，非硬伤）
- [x] 8.2 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍，含全局 CLI/直装工具的机器级升级；上游 bug/不兼容登记回退不阻塞，设计级适配、restrictions.json 破损、流程走不通才停下报告；下限变更等人工发起）；消化后复跑 `pnpm check:outdated` 至退出码 0（SUMMARY 归零）才算完成（消化：cargo lockfile 5 patch——bumpalo 3.20.4/ctor 1.0.14/libloading 0.9.1/mio 1.2.5/target-lexicon 0.13.6 + 新增 link-section 0.19.4；CI action upload-artifact v5.0.0→v7.0.2（v6.0.0=node24 运行时、v7.0.0=新增可选 archive 参数+ESM，name/path 输入面兼容）。验收：`pnpm check` 绿、`cargo test -p netwave` 116 通过、`pnpm check:cross` 四端全绿；复跑体检 SUMMARY 0 LAG）

## Workflow follow-up

- 提交全景表（分组 → 文件 → commit 标题）在闸门绿后给出，等人工点名提交；禁止直推 main。
- 归档前按 archive guidance 执行 Plan/ 瘦身检查与 openspec/specs/ 三态时效检查。
- 本 change 经人工点名（2026-11-13）**跳过** archive guidance 中"归档完成后执行 archive-health-check 五维只读体检"一项，归档完成即收口。
- 延后项去向：根聚合入口 `test:*`（闸门重排档 T1/T2/T4）、wasm 胶水覆盖率 spike（S5）——各自独立点名立项，不在本 change。
