# Tasks

## 1. 前置验证（/tmp，不碰仓库）

- [ ] 1.1 在 /tmp 用真 `typescript/wasm`（wasm-bindgen 胶水 + minicov `coverage` feature）+ vitest worker 跑最小 spike，确认 `__cov_dump` 导出与 wasm-bindgen 胶水共存可加载、worker 内 dump 成立；并验工具链 `llc` 加 `--march=<宿主架构>` 能把 wasm `.ll`（带 `target triple = "wasm32"`）编成宿主 `.o`（验证 `dump放setupFiles` + `独立target加feature门控` + `llvm-tools组件取工具` 成立；失败即停手回报，不进第 2 组）

## 2. wasm crate 插桩与 dump 导出

- [ ] 2.1 `typescript/wasm/Cargo.toml` 加 minicov 依赖与默认关闭的 `coverage` feature（验证：`cargo metadata` 含该 feature，生产构建不含 minicov）
- [ ] 2.2 `typescript/wasm/src/lib.rs` 加 `#[cfg(feature = "coverage")]` 门控的 `__cov_dump`/`__cov_ptr`/`__cov_len` 导出（验证 `独立target加feature门控`：不带 feature 的 `pnpm -C typescript build:wasm` 产物无这三个导出，带 feature 的插桩构建有）
- [ ] 2.3 先写一条失败测试：node 加载插桩 wasm、跑 browser-gated 函数、调 dump 得非空 profraw（red 先于 green，验证 `RUSTC_BOOTSTRAP放行`：stable + `RUSTC_BOOTSTRAP=1 -Zno-profiler-runtime` 编出的 wasm 可倒 profraw）

## 3. vitest dump 钩子（node 侧）

- [ ] 3.1 新增 setup 文件，注册 worker 内 `afterAll`：调 `__cov_dump()`、读 wasm 内存、按 minicov module_signature 命名写 profraw（验证 `dump放setupFiles` + `profraw带签名合并`：跑测试后 target-wasm-cov 下出现 profraw）
- [ ] 3.2 `typescript/vitest.wasm.config.ts` 加 `setupFiles`，插桩构建走独立 target dir（验证：生产 `build:wasm` 的 target-wasm 不受影响）

## 4. test_ts.sh 覆盖率链

- [ ] 4.1 `scripts/run/test_ts.sh` 从 `$(rustc --print sysroot)` 下 llvm-tools bin 目录解析 `llc`/`llvm-profdata`/`llvm-cov` 路径（验证 `llvm-tools组件取工具`：组件缺失时脚本报错指向 `rust-toolchain.toml` 的 components，不发起外部安装）
- [ ] 4.2 在 native 链后新增 wasm rust 覆盖率段：`RUSTC_BOOTSTRAP=1` + `-Cinstrument-coverage -Zno-profiler-runtime --emit=llvm-ir` 插桩构建（独立 target dir）→ `pnpm -C typescript test:wasm` → `llvm-profdata merge -sparse *.profraw` → `llc --march=<宿主架构>` 把 `.ll`→`.o` → `llvm-cov report --codecov --ignore-filename-regex` 剔 python/native（验证 `手动llvm链` + `度量core-browser`：出 `coverage/coverage-wasm.json` 且含 core/src 路径行命中 > 0，LL-093）
- [ ] 4.3 wasm 覆盖率链前后各加 `clean_stray_profraw.py` + `cargo llvm-cov clean --workspace`（验证 `前后双清理`：链外无残留 profraw）
- [ ] 4.4 `scripts/coverage_gate.py coverage/coverage-wasm.json 100` 阅卷（验证 `地板100先列清单`：未达行不直接豁免，先列「真不可达」候选清单交人工确认）
- [ ] 4.5 确认浏览器侧维持 TS-only、不采 rust 覆盖率（验证 `仅node侧`：`test_wasm.sh`/`vitest.browser.config.ts` 不含 rust profraw 倒出，rust 覆盖率仅由 node 驱动套件产 coverage-wasm.json）

## 5. 工具链配置

- [ ] 5.1 `rust-toolchain.toml` 的 `components` 加 `llvm-tools`（验证 `llvm-tools组件取工具` + `弃clang改llvm-tools`：rustup 激活钉版工具链后 `$(rustc --print sysroot)` 下 llvm-tools bin 目录含 `llc`/`llvm-profdata`/`llvm-cov`，本地与 CI 一致；不新增 ci.yml 安装步、不新增 check:outdated clang 探针）
- [ ] 5.2 确认 `test_ts.sh` 的 wasm rust 覆盖率段在全部 5 个 node matrix 格执行并各产 `coverage-wasm.json`（验证 `全矩阵采集`：ci.yml node job 不以 step 级 `if` 限定单格，5 格均出报告）

## 6. spec 同步与豁免清单

- [ ] 6.1 `openspec/specs/ci-matrix/spec.md`「暂不采集」改为已采集并补 Scenario（验证 `spec同步改`：主 spec 与本 change delta 口径一致，`pnpm check:md` 绿）
- [ ] 6.2 跑真 core 后生成 `coverage/coverage-wasm.json` 缺行清单，逐条标注文件+行号+不可达理由交人工确认（验证 `地板100先列清单`：确认前不豁免，未确认者补单测至 100）

## 7. 收尾闸门（按 config.yaml operations.apply 六锚点）

- [ ] 7.1 `pnpm test` 全绿（全量含四端对拍，先于 review）
- [ ] 7.2 删除 `Plan/覆盖率统一-2026-11-12.md` 中本 change 已定案的 S5 章节，只留未执行项，删后跑 `pnpm check:md`（锚点 `Plan/`）
- [ ] 7.3 扫 `openspec/specs/` 全目录产出更新/新增/退役三态时效结论留痕本文件（锚点 `三态时效`）
- [ ] 7.4 按 governance spec「元规则 review 三轴」（Standards/Spec/Lessons）对照本 change 工件审实现 diff，diff 逐文件对上 tasks.md，硬伤清零（锚点 `三轴`）
- [ ] 7.5 对触碰文件全文只读体检（health-check spec apply 态：语义考古维 + 四维，发现附文件+行号+证据落 Plan/ 等点名，不阻塞；全豁免记「已查，无适用文件」）（锚点 `体检`）。注：archive 态体检一次性跳过（2026-11-20，裁决 `archive体检跳过`），apply 态本项照常执行
- [ ] 7.6 apply 中途拍板的决定当场追加进 proposal.md `## 已定裁决` 段并补对应任务行，收尾复查每关键词载体任务已打勾（锚点 `迟到追加`）
- [ ] 7.7 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检与升级预授权」消化所报 LAG（含全局 CLI/直装工具的机器级升级；llvm-tools 随 `rust-toolchain.toml` 钉版走不单独报 LAG），复跑至退出码 0（SUMMARY 归零）才算完成（锚点 `check:outdated`）
