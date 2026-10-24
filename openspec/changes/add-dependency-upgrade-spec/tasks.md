# Tasks

本 change 无 core 数值实现（铁律二 red/green 循环不适用）；闸门脚本按
"先构造已知漂移输入、看闸门变红，再让它变绿"的等价 red-first 执行。

## 1. 登记表与对账闸门

- [ ] 1.1 RED：临时把某 `Cargo.toml` 的 `rust-version` 改坏（如 1.97），
      验证 `check_version_pins.py` 尚不存在即失败（命令缺失/漂移未检出），
      明确闸门要抓的失败形态；改回原值。验证：记录失败输出为验收基线。
- [ ] 1.2 GREEN：创建 `scripts/version_pins.json`，按 design 的条目结构
      （name/category/pin_location/upgrade_method/paired_with）登记现状全部
      钉死点：Rust pin、四处 MSRV、`packageManager`、两份 lockfile、
      `.python-version`、`requires-python`、`engines.node`、CI 矩阵数字、
      CI actions、wasm-pack、binaryen、cargo-llvm-cov、Playwright Chromium、
      oracle 环境（预留）、全局 CLI 检查项（machine 类）。
- [ ] 1.3 GREEN：实现 `scripts/check_version_pins.py`（纯标准库）：条目
      结构校验、pin_location 存在性、四处 `rust-version` 一致性、
      `rust-version` ≤ pin major.minor、`packageManager` 精确版本、
      machine 类条目只查存在性。验证：1.1 的坏值输入变红、现状全绿。
- [ ] 1.4 根 `package.json` 的 `check:meta` 追加
      `python3 scripts/check_version_pins.py`。验证：`pnpm check:meta` 全绿；
      人为漂移时 `pnpm check` 变红。

## 2. 过期体检命令

- [ ] 2.1 实现 `scripts/check_outdated.py`（纯标准库）三段：项目依赖
      （subprocess 调 `pnpm outdated`、`cargo update --dry-run`、
      `uv lock --upgrade --dry-run`）、全局 CLI（`--version` 探测 vs
      endoflife.date/npm/crates.io 最新 LTS/稳定版）、GitHub 直装工具与
      cargo 子命令（已装版本 vs releases/latest，带 `GITHUB_TOKEN` 优先）。
      单段 API 失败降级为警告。验证：本机跑通、三段均有输出。
- [ ] 2.2 根 `package.json` 新增 `check:outdated` 脚本；确认 `check` 与
      `ci.yml` 均不含它。验证：`grep check:outdated .github/workflows/ci.yml`
      无结果。

## 3. Rust MSRV 收尾与 TS7 重测

- [ ] 3.1 `core/Cargo.toml`、`python/Cargo.toml`、`typescript/native/Cargo.toml`、
      `typescript/wasm/Cargo.toml` 的 `rust-version` 1.98→1.99。验证：
      `cargo test --workspace` 与 `pnpm check:rs` 全绿，1.3 闸门一致性通过。
- [ ] 3.2 TS7 重测：`pnpm -C typescript` 下 `build:shells` + `typecheck` +
      `test:native`/`test:wasm`/`test:browser` 全跑，确认 tsdown dts ×
      TypeScript 7 最新稳定版兼容。兼容则维持并在登记表 notes 记"已验证"；
      不兼容则钉 `typescript@6`、登记 LL（含 tsdown 配对约束）。
      验证：三端测试全绿且结论写入登记表。

## 4. 文档迁移与单源化

- [ ] 4.1 AGENTS.md「依赖版本策略」节删除，替换为一行指针
      （指向 `openspec/specs/dependency-upgrade/spec.md`，归档后路径）。
- [ ] 4.2 CONTRIBUTING.md「Toolchain freshness」节删除，替换为一行指针；
      「Toolchain (task → tool)」表保留（任务路由，非版本策略）。
- [ ] 4.3 按 delta 同步检查：workspace-layout 主 spec 的「版本底线」在归档
      sync 后移除、ci-matrix「语言版本矩阵」措辞去数字（delta 已写好，
      归档时自动生效；本任务核对 delta 与主 spec 无遗漏冲突）。
- [ ] 4.4 grep 全仓旧版本数字残留（`1\.98`、`3\.14`、写死的 Node 矩阵数字），
      确认散文文档无第二真相源。验证：`grep -rn` 仅命中清单文件/登记表/
      历史归档。
- [ ] 4.5 `pnpm check:md` 全绿（本次全部 Markdown 改动）。

## 5. 收尾验收

- [ ] 5.1 `pnpm check` 全绿 + `pnpm check:cross` 四端对拍通过。
- [ ] 5.2 `openspec validate` 通过；retro：本 change 踩坑回写 lessons-learned
      （如有）；Plan/测试规划.md「Rust 升版收尾」条目已完成，删除该条目并
      跑 `pnpm check:md`。

## Workflow follow-up

- 用户确认后走 apply；完成并 review 后 `/opsx:sync` + `/opsx:archive`。
- 归档后启动 `upgrade-python-3-15` change（按本 spec 流程执行）。
- 提交分组由人工确认后执行（agent 不主动 commit）。
