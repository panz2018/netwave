# Tasks

## 1. 前置验证（/tmp，不碰仓库）

- [x] 1.1 （2026-11-20 已跑通）在 /tmp 用真 `typescript/wasm`（wasm-bindgen 胶水 + core browser-gated + minicov `coverage` feature）以 wasi-sdk clang 编插桩 wasm、node 加载调 dump 倒出 187KB profraw、`llvm-profdata merge` + `llc --march=<宿主架构>` 编真 core `.ll`→5.5MB 宿主 `.o` + `llvm-cov report` 出含 `core/src/{frequency,resources,touchstone}.rs` 的报告（验证 `dump放setupFiles` + `独立target加feature门控` + `llvm-tools组件取工具` + `wasi-sdk编C` 成立）

## 2. wasm crate 插桩与 dump 导出

- [x] 2.1 `typescript/wasm/Cargo.toml` 加 minicov 依赖与默认关闭的 `coverage` feature（验证：`cargo metadata` 含该 feature，生产构建不含 minicov）
- [x] 2.2 `typescript/wasm/src/lib.rs` 加 `#[cfg(feature = "coverage")]` 门控的 `__cov_dump`/`__cov_ptr`/`__cov_len` 导出（验证 `独立target加feature门控`：不带 feature 的 `pnpm -C typescript build:wasm` 产物无这三个导出，带 feature 的插桩构建有）
- [x] 2.3 `typescript/src/netwave.worker.ts` 的 wasm 加载目录改为可被环境变量覆盖（未设=生产 `dist/wasm-web` 路径零变化），并把 init 返回的实例内存暴露给测试钩子读（验证 `worker环境变量切加载`：未设 env 时 worker 行为与现状一致）
- [x] 2.4 ~~先写一条失败测试：node 经 worker（env 指向插桩 wasm）跑 browser-gated
      函数、调 dump 得非空 profraw~~——被 `浏览器job采集` + `浏览器单采` 取代：
      profraw 改由真浏览器 worker 经控制消息 dump（见 8.1/8.3），node harness 的
      fakeSelf 走不到 fetch 臂故弃用；`RUSTC_BOOTSTRAP放行` 由 8.4 插桩构建实证

## 3. vitest dump 钩子（node 侧）

- [x] 3.1 新增 setup 文件，注册 worker 内 `afterAll`：调 `__cov_dump()`、读暴露的 wasm 内存、按 minicov module_signature 命名写 profraw（验证 `dump放setupFiles` + `profraw带签名合并`：跑测试后插桩 target dir 下出现 profraw）
- [x] 3.2 `typescript/vitest.wasm.config.ts` 加 `setupFiles`，插桩构建走独立 target dir（验证：生产 `build:wasm` 的 target-wasm 不受影响）
- [x] 3.3 `scripts/versions/lib/repository.py` 的 SKIP_DIRS 加插桩 target dir 名（验证 `插桩target加白名单`：插桩链产 profraw 不被 `clean_stray_profraw.py` 误判漏网删除）

## 4. test_ts.sh 覆盖率链

- [x] 4.1 探测段：从 `$(rustc --print sysroot)` 下 llvm-tools bin 目录解析
      `llc`/`llvm-profdata`/`llvm-cov`，并探测 wasi-sdk clang（缺失时提示跑
      `scripts/install_wasi_sdk.sh` 并以非零退出，不自动装）（验证
      `llvm-tools组件取工具` + `wasi-sdk编C`：任一缺失均报错指向对应安装位）
      ——被 `浏览器单采` 取代，探测段落 `test_wasm.sh`（见 8.4），非 test_ts.sh
- [x] 4.2 wasm rust 覆盖率段：`CC=<wasi-sdk>/bin/clang` + `RUSTC_BOOTSTRAP=1` +
      `-Cinstrument-coverage -Zno-profiler-runtime --emit=llvm-ir` 插桩构建（debug、
      独立 target dir）→ `wasm-bindgen --target web` 生成胶水 → env 驱动
      `test:browser` → `llvm-profdata merge -sparse` → `llc --march=<宿主架构>`
      `.ll`→`.o` → `llvm-cov export --format=lcov --ignore-filename-regex`
      （验证 `手动llvm链` + `度量core-browser`：出 lcov 含 core/src 路径行命中 > 0，
      LL-093）——被 `浏览器单采` 取代，链落 `test_wasm.sh`（见 8.4），非 test_ts.sh
- [x] 4.3 wasm 覆盖率链前后各加 `clean_stray_profraw.py`（验证 `前后双清理`：
      链外无残留 profraw）——被 `浏览器单采` 取代，落 `test_wasm.sh`（见 8.4）
- [x] 4.4 `scripts/coverage_gate.py coverage/coverage-wasm.lcov 99` 阅卷（验证
      `地板100先列清单` + `wasm地板99`：补完可驱动单测后剩 fetch「无
      fetch-capable scope」臂经人工确认属真不可达，地板降 99；其余链仍 100）
- [x] 4.5 ~~`仅node侧`：浏览器侧维持 TS-only、不采 rust 覆盖率~~——被
      `浏览器job采集` + `浏览器单采` 推翻：浏览器侧现为 rust 覆盖率唯一采集方
      （见 8.4），node 侧 `test:wasm` 退回纯 TS v8（见 8.5）

## 5. 工具链与 CI

- [x] 5.1 `rust-toolchain.toml` 的 `components` 加 `llvm-tools`（验证 `llvm-tools组件取工具`：rustup 激活钉版工具链后 `$(rustc --print sysroot)` 下 llvm-tools bin 目录含 `llc`/`llvm-profdata`/`llvm-cov`，本地与 CI 一致）
- [x] 5.2 新增 `scripts/install_wasi_sdk.sh`（仿 install_binaryen.sh：查 wasi-sdk 最新 release、下 arm64/x86_64 tarball 解压到 `~/.local/opt/wasi-sdk`、无 sudo）（验证 `wasi-sdk编C` + `编译阅卷工具分离`：脚本跑通后 `<dir>/bin/clang --target=wasm32-unknown-unknown` 可编 freestanding C）
- [x] 5.2b 新增 `scripts/install_wasm_bindgen_cli.sh`（仿 install_binaryen.sh：优先下 GitHub release 预编译 tarball 解压到 `~/.local`，平台无包时回退 `cargo install wasm-bindgen-cli --version <对齐 crate>`、无 sudo）（验证 `wasm-bindgen-cli生成胶水` + `wasm-bindgen-cli预编译优先`：脚本跑通后 `wasm-bindgen --version` 与 wasm-bindgen crate 对齐，可对插桩 `.wasm` 生成 `--target web` 胶水）
- [x] 5.3 `.github/workflows/ci.yml` node job 加 `scripts/install_wasi_sdk.sh` 与 `scripts/install_wasm_bindgen_cli.sh` 安装步（验证 `全矩阵采集` + `wasi-sdk编C`：5 格均装 wasi-sdk clang、均产 coverage-wasm.json）
- [x] 5.4 `scripts/versions/check_outdated.py` section 3 加 wasi-sdk 与 wasm-bindgen-cli 探测，追最新判 LAG（验证 `wasi-sdk编C` + `wasm-bindgen-cli预编译优先`：`pnpm check:outdated` 对落后两者报 LAG）

## 6. spec 同步与豁免清单

- [x] 6.1 `openspec/specs/ci-matrix/spec.md`「暂不采集」改为已采集并补 Scenario
      （验证 `spec同步改`：主 spec 与本 change delta 口径一致，`pnpm check:md`
      绿）——采集方随 `浏览器单采` 定为真浏览器 job，见 8.6
- [x] 6.2 跑真 core 后生成缺行清单，逐条标注文件+行号+不可达理由交人工确认
      （验证 `地板100先列清单` + `wasm地板99`：见 8.8，补完可驱动单测后仅剩
      fetch「无 fetch-capable scope」臂经人工确认属真不可达，地板降 99）

## 7. 收尾闸门（按 config.yaml operations.apply 六锚点）

- [x] 7.1 `pnpm test` 全绿（全量含四端对拍，先于 review）——FREQ/TOUCHSTONE
      ROUND-TRIP PASS、三端 tamper SELF-CHECK PASS、vocab/verbs/rule15 OK，
      TEST_EXIT=0（升级依赖后复跑仍绿）
- [x] 7.2 删除 `Plan/覆盖率统一-2026-11-12.md` 中本 change 已定案的 S5 章节，只留
      未执行项（S6），删后跑 `pnpm check:md`（锚点 `Plan/`）——S5 已删，
      Plan/README.md 索引同步，check:md 绿
- [x] 7.3 扫 `openspec/specs/` 全目录产出更新/新增/退役三态时效结论留痕本文件
      （锚点 `三态时效`）——**更新**：`ci-matrix`（wasm rust 覆盖率由「暂不采集」
      改为真浏览器 job 采集 + 99 地板）；**新增**：`ci-matrix` delta 的
      「wasm 覆盖率链的编译与阅卷工具均无需 sudo」Requirement；**退役**：无。
      其余 spec（api-contract/frequency-class/touchstone-core/memory-lifecycle 等）
      不受本 change 影响，时效不变
- [x] 7.4 按 governance spec「元规则 review 三轴」（Standards/Spec/Lessons）对照
      本 change 工件审实现 diff，diff 逐文件对上 tasks.md，硬伤清零（锚点 `三轴`）
      ——**Standards**：`pnpm check` 全绿（fmt/clippy -D warnings/biome/ruff/元闸门）；
      命名与注释符合当前契约（cov-drive 入口附一句职责）。**Spec**：实现逐条对上
      tasks.md（dump 出口/插桩链/99 地板/cov-drive 三类驱动）。**Lessons**：命中
      LL-092/LL-093（外部驱动胶水覆盖率、报告须验命中）已遵守；本会话新踩
      feature-union 死代码坑（cfg-gate 用 target_arch 非 feature）已记 repo 记忆。
      硬伤清零
- [x] 7.5 对触碰文件全文只读体检（health-check spec apply 态：语义考古维 + 四维，
      发现附文件+行号+证据落 Plan/ 等点名，不阻塞）（锚点 `体检`）——触碰的产码
      文件（core/{frequency,touchstone,resources}.rs、typescript/wasm/src/lib.rs、
      netwave.worker.ts、coverage-dump.ts、test_wasm.sh）已查：无遗留 phase-N 考古
      叙述、无孤儿 cfg 块、cov-drive 入口均 feature 门控生产零污染。发现一项
      架构级问题（wasm dispatch 放置违反自我完整）非本 change 范围，已落
      `Plan/绑定放置重构.md` 等点名。archive 态体检按裁决 `archive体检跳过` 一次性跳过
- [x] 7.6 apply 中途拍板的决定当场追加进 proposal.md `## 已定裁决` 段并补对应任务行，收尾复查每关键词载体任务已打勾（锚点 `迟到追加`）——`wasm地板99` 已记入 proposal 并落任务 4.4/6.2/8.8；`仅node侧` 关键词经任务 4.5 承载，check_proposal 闸门绿
- [x] 7.7 跑 `pnpm check:outdated` 并按 dependency-upgrade spec「apply 末尾体检与
      升级预授权」消化所报 LAG（锚点 `check:outdated`）——12 LAG 全消化：cargo
      lockfile 8 传递补丁、uv coverage→7.17.4（两项目）、CI setup-uv→v10.4.0、
      cargo-llvm-cov→0.9.2（install 脚本）；复跑 SUMMARY 0 LAG，全闸门 +
      四端对拍绿

## 8. 浏览器 job 采集迁移（裁决 `浏览器job采集` + `控制消息dump出口` + `浏览器单采`）

- [x] 8.1 `typescript/src/netwave.worker.ts` 加控制消息出口：收到 control 为
      dumpCoverage 的控制消息时调实例 `__cov_dump`/`__cov_ptr`/`__cov_len`、把
      profraw 字节 base64 后 postMessage 回主线程（验证 `控制消息dump出口`：
      worker.test.ts「固定模板不含动词名」仍绿——控制消息不进 core call 的 match、
      不算业务动词；dump 仅在插桩实例上非空）
- [x] 8.2 `typescript/vitest.browser.config.ts` 加 browser.commands.writeProfraw
      （node 端 base64 解码落 profraw，按 module_signature 命名）与插桩 wasm 加载：
      浏览器模式下 worker MUST 加载 `dist/wasm-cov` 插桩产物（验证 `浏览器job采集`：
      spike 已证 base64 经 commands 回传逐字节一致；Uint8Array 直传降级成 Object 已排除）
- [x] 8.3 浏览器测试末尾注册 dump：afterAll 经 worker 控制消息取 profraw，再经
      commands.writeProfraw 落盘（验证 `浏览器job采集`：跑 test:browser 后插桩 target
      dir 出现非空 profraw）
- [x] 8.4 `scripts/run/test_wasm.sh` 新增浏览器 rust 覆盖率链：插桩 cargo build 加
      wasm-bindgen 生成 web 胶水，env 驱动 test:browser，llvm-profdata merge 加 llc
      加 llvm-cov export lcov，`coverage_gate.py coverage/coverage-wasm.lcov 100`
      （验证 `浏览器job采集`：fetch Window/WorkerGlobalScope 臂命中 > 0，LL-093）
- [x] 8.5 `scripts/run/test_ts.sh` 删除 node 侧 wasm 插桩覆盖率链（验证 `浏览器单采`：
      test_ts.sh 不再含 wasm 插桩 build/dump/lcov，node test:wasm 退回纯 TS v8；native
      链与 python 链不动）
- [x] 8.6 `openspec/specs/ci-matrix/spec.md` 同步：wasm rust 覆盖率采集方从「node
      驱动 vitest」改为「真浏览器 job」，仅 node 侧旧 Scenario 改写（验证
      `spec同步改` + LL-034：主 spec 与本 change delta 口径一致，`pnpm check:md` 绿）
- [x] 8.7 `.github/workflows/ci.yml`：wasm job 产 coverage-wasm.lcov 并上传；node
      job 不再产 wasm lcov（验证 `浏览器单采`：上传路径与产出 job 一致）
- [x] 8.8 跑真浏览器覆盖率后生成缺行清单，逐条标注文件+行号+理由交人工确认（验证
      `地板100先列清单` + `wasm地板99`：实证补完 dropped guard、dispatch-violation、
      copy malformed-source（cov-drive 假资源）后，仅剩 `touchstone.rs` fetch「无
      fetch-capable scope」臂——读 `js_sys::global()` 真实全局、无注入点，mock/测试
      均不可达；人工确认属真不可达，地板降 99。write_file 等 native-only 已 cfg
      排除出分母，不属豁免）
