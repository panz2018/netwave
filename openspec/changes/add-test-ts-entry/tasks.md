# Tasks

## 1. typescript 级覆盖率下沉（red 先于 green）

- [x] 1.1 red：在 `scripts/tests/` 加断言 `typescript/package.json` 的
      `test:native`/`test:wasm`/`test:browser` 三条脚本各含 `--coverage` 的失败用例，
      落地前跑 `pnpm check:py` 确认该用例红
- [x] 1.2 green：把 `--coverage` 烤入 `typescript/package.json` 的 `test:native`、
      `test:wasm`、`test:browser` 三条脚本，使 `coverage 下沉` 生效（阈值数值仍只在
      `vitest.*.config.ts` 的 `thresholds`，本步不新增数值）
- [x] 1.3 验证 `coverage 下沉`：`pnpm -C typescript test:wasm`（不带 flag）即按
      阈值阅卷，人为造一处分支缺口能红

## 2. dts 防 any 闸门脚本化（T3）

- [x] 2.1 新建 `typescript/scripts/check_dts_any.mjs`：检查 `dist/index.browser.d.mts`
      与 `dist/index.node.d.mts` 含 `: any` 即非零退出并打印原因，落实 `dts 检查形态`
- [x] 2.2 验证 `dts 检查形态`：人为把某 dts 改出 `: any`，跑
      `node typescript/scripts/check_dts_any.mjs` 能红

## 3. typescript 测试根聚合入口脚本

- [x] 3.1 新建 `scripts/run/test_ts.sh`，`set -euo pipefail` + `cd` 仓库根，
      落实 `test_ts.sh 范围`：build:wasm → native 覆盖率链 → typecheck →
      dts 检查 → test:wasm（不含 browser、不含 cross）
- [x] 3.2 在 `test_ts.sh` 开头落实 `工具链探测`：探测 cargo-llvm-cov、wasm-pack、
      wasm-opt、wasm32-unknown-unknown 目标，缺则 stderr 打印对应安装命令并非零退出，
      不自动安装
- [x] 3.3 落实 `前后对称清理`：pre 块 `clean_stray_profraw.py` 先于
      `cargo llvm-cov clean --workspace`；post 块 `clean_stray_profraw.py` 在
      report/gate 之后再 `cargo llvm-cov clean --workspace`
- [x] 3.4 落实 `native 池参数留脚本`：native 链 show-env +
      `NODE_OPTIONS=--expose-gc` + build:native:debug +
      `test:native --pool=threads --execArgv="" --no-file-parallelism` +
      report（host triple）+ `coverage_gate.py 100`，池参数只在此处、不烤入包级脚本
- [x] 3.5 落实 `typecheck 无条件跑`：`test_ts.sh` 内调
      `pnpm -C typescript typecheck`，不带 node 版本条件
- [x] 3.6 落实 `不探测 node_modules`：脚本不检测依赖、不代跑 `pnpm install`，
      缺依赖由 pnpm/vitest 自报错
- [x] 3.7 验证 `test:ts`：仓库根 `pnpm test:ts` 全链绿；注入 `stray.profraw`
      能红且文件被删
- [x] 3.8 落实 `native report 排除 python`：`test_ts.sh` 的 native report
      `--ignore-filename-regex` 同时排除 `core` 与 `python`，修本地共享 `target/`
      被 maturin 插桩时 python 行以 0% 混入 native 报告（CI 端 no-op）

## 4. 根入口与 CI 接线

- [x] 4.1 根 `package.json` 加 `test:ts`：`bash scripts/run/test_ts.sh`，
      使 `test:ts` 入口生效
- [x] 4.2 `ci.yml` node job：测试步骤收敛为 `bash scripts/run/test_ts.sh`，
      删除内联的 native 链/typecheck/dts/test:wasm 步骤与独立 profraw drain 步骤，
      工具链安装步骤、coverage artifact 上传、cross 比对步骤留内联
- [x] 4.3 落实 `wasm job 只删 flag`：`ci.yml` wasm job 删两处 `--coverage`
      （`test:wasm`、`test:browser`），不拆独立脚本

## 5. CI 接线闸门升根级（T4）

- [x] 5.1 red：在 `scripts/tests/` 加 `check_ci.py` 根级口径失败用例——
      「根 `test:*` 对应 `scripts/run/test_<name>.sh` 不在 ci.yml 即红」与
      「`typescript test:native` 字面缺失不误报」两态，落地前 `pnpm check:py` 确认红
- [x] 5.2 green：`scripts/check_ci.py` 落实 `check_ci 根级口径`——以根
      `package.json` 每条 `test:*` 映射 `scripts/run/test_<name>.sh` 须出现在 ci.yml，
      typescript 级旧规则退役
- [x] 5.3 验证 `check_ci 根级口径`：从 ci.yml 删一条 `test_*.sh` 调用 →
      `pnpm check:meta` 红

## 6. 波及文档同步（LL-034）

- [x] 6.1 同步 `CONTRIBUTING.md`、`scripts/README.md`、`typescript/README.md`、
      `oracle/README.md` 中受影响的命令与口径描述
- [x] 6.2 同步 `openspec/specs/ci-matrix/spec.md`（归档时由 delta 合入，apply 阶段
      核对主 spec 与本 delta 口径一致）
- [x] 6.3 更新 `Plan/测试规划.md` 相关行；改写 `Plan/闸门重排-2026-11-12.md`
      的决策三（覆盖率下沉）与任务状态，并把 `延后项`（根 `pnpm test` 总聚合、
      T5 config.yaml 规则、`check:cross` 改名/接线）记回该档
- [x] 6.4 更新 `Plan/覆盖率统一-2026-11-12.md` 的 S1 延后项（"未建根脚本"已过时，
      改写去向）
- [x] 6.5 收尾对账：grep `Plan/` 中本 change 已完成/已定案章节，删除已落地内容，
      只留未执行任务；改后跑 `pnpm check:md`（锚点 `Plan/`）

## 7. 收尾闸门

- [x] 7.1 `三态时效`：扫 `openspec/specs/` 全目录，对照本 change 产出
      "更新/新增/退役"结论留痕本文件（哪些 spec 需改而未改、可退役），结构一致性由
      `check_md.py` SPECS ROUTER 兜底
      ——更新：`ci-matrix`（3 条 ADDED requirement 归档时由 delta 合入，apply 阶段
      主 spec 不动）；新增：无独立新 spec（均落 ci-matrix）；退役：无
      （grep 全 specs 无与本 change 冲突的旧口径——`memory-lifecycle` 不含
      profraw 清理条款，`health-check` 不含 `test:*` 命令事实）
- [x] 7.2 按 governance spec「元规则 review 三轴」（Standards/Spec/Lessons）
      对照本 change 工件审实现 diff，diff 文件集逐文件对上本 tasks.md，对不上即越权
      停手还原，硬伤清零才准入后续（锚点 `三轴`）
- [x] 7.3 对触碰文件全文只读体检（health-check spec apply 态：语义考古维 + 四维），
      发现附文件+行号+证据落 `Plan/` 等点名，不阻塞；全豁免记"已查，无适用文件"
      （锚点 `体检`）
- [x] 7.4 `迟到追加`：复查本 change 中途拍板的决定已当场追加进 `proposal.md` 的
      `## 已定裁决` 段并补对应任务行，每个关键词载体任务已打勾
- [x] 7.5 跑 `pnpm check`、`pnpm check:md`、`pnpm check:meta`、`pnpm test:ts`、
      `pnpm check:cross` 全绿（cross 对拍确认 CI 接线改动未破坏跨端一致性）
- [x] 7.6 最后一项：跑 `pnpm check:outdated` 并按 dependency-upgrade spec
      「apply 末尾体检与升级预授权」消化所报 LAG（升级 + 全闸门 + 四端对拍，含全局
      CLI/直装工具的机器级升级；上游 bug/不兼容登记回退不阻塞；下限变更等人工发起），
      消化后复跑 `pnpm check:outdated` 至退出码 0（SUMMARY 归零）才算完成
      （锚点 `check:outdated`）
- [x] 7.7 `归档体检一次性跳过`：本 change 归档时 archive 态只读体检跳过 跳过
      2026-11-18（仅本次一次性，config.yaml archive guidance 与 health-check spec
      规则本体不变）
