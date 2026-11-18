# Proposal

## Why

根 `package.json` 只有 `test:rs` 一个测试入口，python 绑定的测试与 rust 胶水
覆盖率链只存在于 ci.yml python job 内联（`show-env → clean → maturin develop → pytest → report → coverage_gate` 加前后两道 profraw drain），本地无同口径聚合
命令；tasks.md 手抄 CI 参数即漂移不可见（`Plan/闸门重排-2026-11-12.md` §1 立项
根因在 python 侧的翻版）。`test:rs` 已由 change `add-test-rs-entry` 验证了
"脚本承载命令、本地与 CI 同一文件"的模式，本 change 把同一模式套到 python 链。

## What Changes

- 根 `package.json` 新增 `test:py` 薄调用入口：`bash scripts/run/test_py.sh`。
- 新建 `scripts/run/test_py.sh`：python 绑定全链（前后 profraw drain +
  `cargo llvm-cov show-env` + `clean --workspace` + `maturin develop` +
  `python/` pytest + rust 胶水阅卷 `coverage_gate.py coverage-python.json 100`）
  + 缺工具探测报错，本地与 CI 同一脚本。
- 后置清理顺序统一为 `drain → clean`：`test_py.sh` 后置块把带检测职责的
  `clean_stray_profraw.py` 顶到最前，`clean --workspace` 其后；`test_rs.sh`
  后置块同步换序（原 `rm -rf llvm-cov-target → drain` 改为 `drain → rm -rf`），
  防日后向后置块追加命令把 drain 挤后、削弱其"断链当轮即红"的检测职责。
- ci.yml：python job 的两道独立 drain 步骤删除、内联大步骤塌为
  `bash scripts/run/test_py.sh`（保留 `shell: bash`）；upload-artifact 留 CI。
- ci-matrix spec：python job 清扫归属从"独立清理步骤调 `clean_stray_profraw.py`"
  改为"内置于 `scripts/run/test_py.sh`"；补 `test_py.sh` 前后各一次
  `cargo llvm-cov clean --workspace` 与后置 `drain → clean` 顺序；"show-env、
  clean、build、test、report MUST 同一 step"补"或由 `test_py.sh` 单步承载"。
- 文档同步：`scripts/README.md`（补 `run/test_py.sh` 条目）、`CONTRIBUTING.md`
  （本地入口表补 `pnpm test:py` + 快循环出口）、`Plan/闸门重排-2026-11-12.md`
  已定裁决段。

## Capabilities

### New Capabilities

- 无（不新增能力域）。

### Modified Capabilities

- `ci-matrix`：python 测试入口从 ci.yml 内联改为根聚合入口 `test:py` 调
  `scripts/run/test_py.sh`；python job 的 profraw 清扫与插桩清理内置于该脚本
  （不再用独立 CI 步骤）；`test_rs.sh` / `test_py.sh` 后置清理统一 `drain → clean`
  顺序。

## Impact

- `package.json`（+1 行 `test:py`）
- `scripts/run/test_py.sh`（新建）
- `scripts/run/test_rs.sh`（后置块换序 `drain → rm -rf`）
- `.github/workflows/ci.yml`（python job 塌步 + 删两道 drain 步骤）
- `openspec/specs/ci-matrix/spec.md`（"覆盖率中间产物不跨轮残留" Requirement
  的 python 归属与单步承载措辞）
- `scripts/README.md`、`CONTRIBUTING.md`、`Plan/闸门重排-2026-11-12.md`
- 铁律七（覆盖率门槛）口径不变，仅执行载体从 CI 内联变为脚本；胶水阅卷豁免
  （`#[pymethods]` 宏属性行）不变。

## Non-goals

- 不建 `test:ts` / `test:wasm` / `test:cross` / `test` 总入口（归
  `Plan/闸门重排-2026-11-12.md` 其余任务，后续点名）。
- 不改覆盖率阈值、豁免规则与报告命名（铁律七口径不动）。
- 不改 python 版本矩阵格、不合并 CI job。
- 不动 `check:py`（根治理脚本 pytest，build-free，留 lint job）、不动 stub_gen
  （在 node job cross 步骤，属跨端一致性）。
- 不升级 `scripts/check_ci.py` 根级接线闸门（T4，另立任务）、不改 `check:cross`
  命名（决策二）。
- 不做 bench 相关改动（决策五：bench 未完工，本轮不动）。

## Prior art

- 仓库内既有模式：`scripts/run/test_rs.sh`（change `add-test-rs-entry` 落地）
  已是"脚本承载命令、`package.json` 与 CI 都只薄调用"的直接先例，本 change
  逐条对齐其结构（探测、前后清理、严格失败语义）。
- `scripts/install_cargo_llvm_cov.sh` 等 `install_*.sh` 是"命令细节收进脚本、
  调用方一行"的先例；uv 无对应安装脚本，CI 由 `astral-sh/setup-uv` 负责，故
  本地缺 uv 仅打印官方命令、不新建脚本。

## 专家增补

- 为 `test_py.sh` 补接线冒烟测：`scripts/tests/` 增用例断言根 `package.json`
  含 `test:py` 且 ci.yml python job 调用 `scripts/run/test_py.sh`，仿
  `scripts/tests/test_drain_profraw.py` 的 CLI 冒烟法——防"脚本写了没人接线"，
  弥补 `check_ci.py` 暂不扫根级 `test:*`（T4 未做）的执法缺口。
- `CONTRIBUTING.md` 注明快循环出口：`test:py` 含 maturin 编译首跑数分钟，日常
  快循环用 `(cd python && uv run pytest)`（Python 层地板仍生效），提交前跑
  `test:py` 全链——否则开发者绕开聚合入口，假绿问题换皮复发。
- 后置 `drain → clean` 换序的正确性依据：`drain_stray_profraw` 的 `SKIP_DIRS`
  含 `target`（`scripts/versions/lib/repository.py`），只删 `target/` 外散落
  profraw；`cargo llvm-cov clean --workspace` 只清 `target/` 内产物——两者作用集
  互斥，换序不互相破坏，且 drain 顶到最前保住检测职责。

## 已定裁决

- `范围只建test-py`：本次只建 `test:py` 一个入口，其余 `test:*` 留待后续点名。
- `脚本承载命令`：命令细节放 `scripts/run/test_py.sh`，`package.json` 只留薄调用，防参数抄漏。
- `清理用clean-workspace`：python 链插桩对象落 host `target/debug`，清理用
  `cargo llvm-cov clean --workspace`（非 `test_rs.sh` 的 `rm -rf llvm-cov-target`）。
- `前后各一次清理`：`test_py.sh` 在覆盖率链之前与之后各执行一次 `clean --workspace`。
- `后置drain先于clean`：`test_py.sh` 后置块顺序为 `drain → clean --workspace`，
  带检测职责的 drain 顶到最前，防日后追加命令把它挤后削弱检测。
- `rs同步换序`：`test_rs.sh` 后置块同步改为 `drain → rm -rf llvm-cov-target`，
  与 `test_py.sh` 后置结构一致。
- `缺工具报错不自动装`：`test_py.sh` 探测 `cargo-llvm-cov`（提示
  `bash scripts/install_cargo_llvm_cov.sh`）与 `uv`（打印官方安装命令），缺则
  非零退出，不自动安装、不新建 `install_uv.sh`。
- `uv子shell写法`：脚本内用 `(cd python && uv sync && uv run maturin develop)`
  与 `(cd python && uv run pytest)`，照抄 CI python job 现写法保同口径。
- `ci塌步调脚本`：ci.yml python job 内联大步骤塌为 `bash scripts/run/test_py.sh`
  （保留 `shell: bash`），upload-artifact 留 CI。
- `drain入脚本`：python job 前后两道独立 drain 步骤删除，清扫改由 `test_py.sh`
  内置（对齐 rust job 塌法）。
- `严格失败语义`：脚本 `set -euo pipefail`；清扫先删后报错 exit 1。
- `验收三判据`：①本地 `pnpm test:py` 全绿且产出 `coverage/coverage-python.json`
  经 `coverage_gate.py` 阅卷 100；②`python/src/` 人为加一行未测胶水产码 →
  `test:py` 报红；③人为放 `stray.profraw` → `test:py` 报红并删除。
- `文档spec同步`：ci-matrix spec、`scripts/README.md`、`CONTRIBUTING.md`、
  `Plan/闸门重排-2026-11-12.md` 随本 change 同步（LL-034）。
- `不扩范围`：`check_ci.py` 根级接线闸门升级（T4）、`check:cross` 改名（决策二）
  不在本 change，仅留痕。
